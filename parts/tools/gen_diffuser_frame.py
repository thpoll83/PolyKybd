#!/usr/bin/env python3
"""Generate the one-piece LED diffuser frame for the PolyKybd split72.

Reads the plate PCB (poly_kybd/poly_kybd_split72_plate_<side>.kicad_pcb) — the
authoritative source for where every LED half-round hole is and how it is
rotated — and emits parts/diffuser_frame_<side>.scad.

The frame holds all 36 diffusers at their exact plate position/orientation and
ties them together with a web that lives UNDER the plate, routed through the
solid material between the switch openings.  The diffuser itself is NOT
re-modelled here: the generated file calls diffuser() from parts/diffuser.scad.

Topology (deliberately regular, not a router's spanning tree):
  * a straight vertical RAIL in each inter-column channel
  * a straight horizontal RUNG from every diffuser to the rail(s) beside it
  * the rotated thumb keys, which have no regular neighbour to line up with,
    are joined by links found with a free-space search
  * the two outermost rails stay unbroken as a backbone; the inner ones are
    thinned to 1-in-3 to save resin, every removal re-checked for connectivity

Usage:
    python3 gen_diffuser_frame.py            # both halves
    python3 gen_diffuser_frame.py left
"""
import sys, os, re, math, json, heapq, argparse, collections, datetime

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def plate_path(side):
    return os.path.join(REPO, "poly_kybd", f"poly_kybd_split72_plate_{side}.kicad_pcb")


REV  = "r1.0"
# Stamped into the generated header, so it must be the date this actually ran —
# a frozen constant silently claims the wrong day after the next regeneration.
DATE = datetime.date.today().isoformat()

# ======================================================================
# from sexp.py
# ======================================================================

def tokenize(s):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', s)

def parse(s):
    toks = tokenize(s)
    pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            out = []
            while toks[pos] != ')':
                out.append(rd())
            pos += 1
            return out
        if t.startswith('"'):
            return t[1:-1].replace('\\"','"')
        return t
    out=[]
    while pos < len(toks):
        out.append(rd())
    return out

def find(node, name):
    """direct children lists whose head == name"""
    return [c for c in node if isinstance(c, list) and c and c[0]==name]

def first(node, name):
    f = find(node, name)
    return f[0] if f else None


# ======================================================================
# from plate_geom.py
# ======================================================================

def load(path):
    with open(path, encoding='utf-8') as fh:
        return parse(fh.read())[0]

def arc_points(s,m,e,n=24):
    (sx,sy),(mx,my),(ex,ey)=s,m,e
    # circumcenter
    d=2*(sx*(my-ey)+mx*(ey-sy)+ex*(sy-my))
    ux=((sx**2+sy**2)*(my-ey)+(mx**2+my**2)*(ey-sy)+(ex**2+ey**2)*(sy-my))/d
    uy=((sx**2+sy**2)*(ex-mx)+(mx**2+my**2)*(sx-ex)+(ex**2+ey**2)*(mx-sx))/d
    r=math.hypot(sx-ux,sy-uy)
    a0=math.atan2(sy-uy,sx-ux); am=math.atan2(my-uy,mx-ux); a1=math.atan2(ey-uy,ex-ux)
    def norm(a): 
        while a<0: a+=2*math.pi
        while a>=2*math.pi: a-=2*math.pi
        return a
    # decide direction: go from a0 to a1 passing through am
    for sign in (1,-1):
        sweep=norm(sign*(a1-a0)); msw=norm(sign*(am-a0))
        if msw<=sweep+1e-9:
            pts=[(ux+r*math.cos(a0+sign*sweep*i/n), uy+r*math.sin(a0+sign*sweep*i/n)) for i in range(n+1)]
            return pts,(ux,uy),r
    return [ (sx,sy),(ex,ey) ],(ux,uy),r

def edge_segments(doc, layer='Edge.Cuts'):
    segs=[]
    for n in doc:
        if not isinstance(n,list): continue
        lay=first(n,'layer')
        if not lay or lay[1]!=layer: continue
        if n[0]=='gr_line':
            s=tuple(float(v) for v in first(n,'start')[1:3]); e=tuple(float(v) for v in first(n,'end')[1:3])
            segs.append(('line',[s,e]))
        elif n[0]=='gr_arc':
            s=tuple(float(v) for v in first(n,'start')[1:3]); m=tuple(float(v) for v in first(n,'mid')[1:3]); e=tuple(float(v) for v in first(n,'end')[1:3])
            pts,c,r=arc_points(s,m,e)
            segs.append(('arc',pts))
        elif n[0]=='gr_rect':
            s=tuple(float(v) for v in first(n,'start')[1:3]); e=tuple(float(v) for v in first(n,'end')[1:3])
            segs.append(('rect',[(s[0],s[1]),(e[0],s[1]),(e[0],e[1]),(s[0],e[1]),(s[0],s[1])]))
    return segs

def build_loops(segs, tol=1e-3):
    key=lambda p:(round(p[0]/tol),round(p[1]/tol))
    adj=collections.defaultdict(list)
    for i,(k,pts) in enumerate(segs):
        adj[key(pts[0])].append((i,0)); adj[key(pts[-1])].append((i,1))
    used=[False]*len(segs); loops=[]
    for i in range(len(segs)):
        if used[i]: continue
        used[i]=True
        pts=list(segs[i][1]); 
        # walk forward
        while True:
            k=key(pts[-1]); nxt=None
            for (j,end) in adj[k]:
                if not used[j]: nxt=(j,end); break
            if nxt is None: break
            j,end=nxt; used[j]=True
            p=segs[j][1] if end==0 else segs[j][1][::-1]
            pts.extend(p[1:])
        loops.append(pts)
    return loops

def bbox(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)

def area(pts):
    a=0
    for i in range(len(pts)-1):
        a+=pts[i][0]*pts[i+1][1]-pts[i+1][0]*pts[i][1]
    return abs(a)/2


# ======================================================================
# plate extraction
# ======================================================================

def extract(path):
    doc=load(path)
    # LED arcs
    leds=[]
    for n in doc:
        if isinstance(n,list) and n[0]=='gr_arc':
            lay=first(n,'layer')
            if not lay or lay[1]!='Edge.Cuts': continue
            sx,sy=[float(v) for v in first(n,'start')[1:3]]
            mx,my=[float(v) for v in first(n,'mid')[1:3]]
            ex,ey=[float(v) for v in first(n,'end')[1:3]]
            cx,cy=(sx+ex)/2,(sy+ey)/2
            r=math.hypot(sx-cx,sy-cy)
            ang=math.degrees(math.atan2(my-cy,mx-cx))   # kicad frame
            leds.append(dict(x=cx,y=cy,r=r,kang=ang))
    segs=edge_segments(doc)
    loops=build_loops(segs)
    cutouts=[l for l in loops if 200 < area(l) < 300]
    others=[l for l in loops if area(l)>=300]
    return leds, cutouts, others




# ======================================================================
# free-space field + routing
# ======================================================================


# ---------------------------------------------------------------- parameters
STEM_W   = 2.0    # stem width (mm) -- resin, so 2 mm is fine
CLEAR    = 0.40   # clearance from a switch cut-out edge (mm)
CAP_R    = 3.5    # diffuser cap radius (stems may start anywhere on the cap)
GRID     = 0.5    # router grid (mm)
TURN_PEN = 0.0    # cost added per direction change (keeps runs straight)
EDGE_MARGIN = 2.0 # keep the web this far inside the plate outline

SQ2 = math.sqrt(2)


# ---------------------------------------------------------------- geometry
def pt_seg_d(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def poly_dist(p, poly):
    """>0 outside, <0 inside."""
    x, y = p
    inside = False
    best = 1e9
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        best = min(best, pt_seg_d(p, a, b))
        if (a[1] > y) != (b[1] > y):
            if x < a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]):
                inside = not inside
    return -best if inside else best


def strip_led_bump(poly, leds, r=2.7):
    """Drop the LED half-round from a switch cut-out outline (closed with a chord),
    so the keep-out is just the switch opening."""
    keep = [p for p in poly[:-1]
            if not any(math.hypot(p[0] - l['x'], p[1] - l['y']) < r for l in leds)]
    return (keep + [keep[0]]) if keep else poly


# ---------------------------------------------------------------- free-space grid
class Field:
    def __init__(self, keepouts, outline, pad, edge_margin=2.0):
        self.ko = keepouts
        self.kbb = [bbox(p) for p in keepouts]
        self.outline = outline
        self.pad = pad
        self.edge_margin = edge_margin
        x0, y0, x1, y1 = bbox(outline)
        self.ox, self.oy = x0 - 2, y0 - 2
        self.nx = int((x1 - x0 + 4) / GRID) + 1
        self.ny = int((y1 - y0 + 4) / GRID) + 1
        self.free = bytearray(self.nx * self.ny)
        for iy in range(self.ny):
            for ix in range(self.nx):
                self.free[iy * self.nx + ix] = 1 if self.point_free(self.xy(ix, iy)) else 0

    def xy(self, ix, iy):
        return (self.ox + ix * GRID, self.oy + iy * GRID)

    def ij(self, p):
        return (int(round((p[0] - self.ox) / GRID)), int(round((p[1] - self.oy) / GRID)))

    def point_free(self, p):
        if poly_dist(p, self.outline) > -self.edge_margin:
            return False                                  # outside / too near the rim
        for poly, (x0, y0, x1, y1) in zip(self.ko, self.kbb):
            if p[0] < x0 - 4 or p[0] > x1 + 4 or p[1] < y0 - 4 or p[1] > y1 + 4:
                continue
            if poly_dist(p, poly) < self.pad:
                return False
        return True

    def is_free(self, ix, iy):
        return 0 <= ix < self.nx and 0 <= iy < self.ny and self.free[iy * self.nx + ix]

    def seg_free(self, a, b, step=0.2):
        n = max(2, int(math.dist(a, b) / step) + 1)
        for i in range(n + 1):
            t = i / n
            if not self.point_free((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)):
                return False
        return True


NB = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]


def dijkstra(field, seeds):
    """seeds: list of (ix,iy).  Returns dist{}, prev{} keyed by (ix,iy,dir)."""
    dist, prev = {}, {}
    pq = []
    for s in seeds:
        if not field.is_free(*s):
            continue
        st = (s[0], s[1], -1 if TURN_PEN else 0)
        dist[st] = 0.0
        heapq.heappush(pq, (0.0, st))
    while pq:
        d, st = heapq.heappop(pq)
        if d > dist.get(st, 1e18) + 1e-9:
            continue
        ix, iy, pd = st
        for k, (dx, dy) in enumerate(NB):
            nx_, ny_ = ix + dx, iy + dy
            if not field.is_free(nx_, ny_):
                continue
            if dx and dy:                      # diagonal: both orthogonals must be free
                if not (field.is_free(ix + dx, iy) and field.is_free(ix, iy + dy)):
                    continue
            step = GRID * (SQ2 if dx and dy else 1.0)
            nd = d + step + (TURN_PEN if (pd != -1 and pd != k) else 0.0)
            nst = (nx_, ny_, k if TURN_PEN else 0)
            if nd < dist.get(nst, 1e18) - 1e-9:
                dist[nst] = nd
                prev[nst] = st
                heapq.heappush(pq, (nd, nst))
    return dist, prev


def best_at(dist, cells):
    best = None
    for c in cells:
        for k in (range(-1, 8) if TURN_PEN else (0,)):
            st = (c[0], c[1], k)
            if st in dist and (best is None or dist[st] < best[0]):
                best = (dist[st], st)
    return best


def trace(prev, st):
    pts = []
    while st is not None:
        pts.append((st[0], st[1]))
        st = prev.get(st)
    return pts[::-1]


def simplify(field, pts):
    """Greedy line-of-sight shortcutting -> few long straight stems."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        j = len(pts) - 1
        while j > i + 1 and not field.seg_free(pts[i], pts[j]):
            j -= 1
        out.append(pts[j])
        i = j
    return out




# ======================================================================
# regular topology
# ======================================================================



# ------------------------------------------------- parameters (topology only;
# the shared ones -- STEM_W, CLEAR, CAP_R, EDGE_MARGIN -- live in the router
# parameter block above and are NOT repeated here)
RUNG_OFF  = 1.90   # rung offset from the LED centre, toward the round side (mm)
COL_TOL   = 0.6    # x tolerance when grouping LEDs into columns (mm)
BAND_MERGE = 12.0  # columns closer than this are one band (no rail fits between)
CAP_WELD_Y = 0.80  # min local-y of a stem anchor (cap starts at 0.25)
CAP_WELD_R = 3.00  # max radius of a stem anchor (cap radius is 3.5)
THIN_VERTICALS = True  # drop every second long row-to-row run to save resin
OUTER_RAILS_FULL = True  # leave the two outermost channels fully connected
INNER_KEEP_EVERY = 3     # inner channels: keep 1 long run in N (2 in a row may go)
SHORT_RAIL = 5.0   # rail runs below this join two columns at one row: always keep

PAD = STEM_W / 2 + CLEAR


def seg_len(s):
    return sum(math.dist(s['pts'][k], s['pts'][k + 1]) for k in range(len(s['pts']) - 1))


def _key(p):
    return (round(p[0] * 1000), round(p[1] * 1000))


def _cap_nodes(leds):
    """Node keys that land on a diffuser cap — these must stay connected."""
    out = {}
    for i, l in enumerate(leds):
        a = math.radians(l['kang'])
        out[_key((l['x'] + RUNG_OFF * math.cos(a), l['y'] + RUNG_OFF * math.sin(a)))] = i
    return out


def _adjacency(segs):
    adj = {}
    for s in segs:
        for a, b in zip(s['pts'], s['pts'][1:]):
            ka, kb = _key(a), _key(b)
            adj.setdefault(ka, set()).add(kb)
            adj.setdefault(kb, set()).add(ka)
    return adj


def _reachable(segs, leds):
    """Set of cap nodes reachable from the first one, plus the cap-node map."""
    adj = _adjacency(segs)
    caps = _cap_nodes(leds)          # one boss key per LED
    start = next((k for k in caps if k in adj), None)
    if start is None:
        return caps, adj, set()
    seen, stack = {start}, [start]
    while stack:
        for nb in adj.get(stack.pop(), ()):
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return caps, adj, seen


def count_components(segs, leds):
    """How many separate pieces the diffusers fall into (1 = one part)."""
    adj = _adjacency(segs)
    caps = _cap_nodes(leds)
    if len(caps) != len(leds):
        return len(leds)             # boss keys collided — treat as broken
    seen, comps = set(), 0
    for k in caps:
        if k in seen:
            continue
        if k not in adj:
            comps += 1               # a diffuser with no stem is its own piece
            seen.add(k)
            continue
        comps += 1
        stack = [k]
        seen.add(k)
        while stack:
            for nb in adj.get(stack.pop(), ()):
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return comps


def graph_connected(segs, leds):
    """Is every diffuser joined to every other through `segs`?

    Each LED contributes exactly one node — its boss key, the point every stem
    that serves it is welded to.  A diffuser with no stem at all has no node in
    the adjacency map, and must fail here rather than be skipped: this is the
    only safety gate the thinning loop has.
    """
    caps, adj, seen = _reachable(segs, leds)
    if len(caps) != len(leds):
        return False
    return all(k in adj and k in seen for k in caps)


def prune_dead_ends(segs, leds):
    """Drop stubs that lead nowhere after thinning (they cost resin, do nothing)."""
    caps = _cap_nodes(leds)
    changed = True
    while changed:
        changed = False
        adj = _adjacency(segs)
        dead = {k for k, nb in adj.items() if len(nb) <= 1 and k not in caps}
        if not dead:
            break
        keep = []
        for s in segs:
            if any(_key(p) in dead for p in (s['pts'][0], s['pts'][-1])):
                changed = True
            else:
                keep.append(s)
        segs = keep
    return segs


def group_columns(leds, idx):
    cols = []
    for i in sorted(idx, key=lambda k: (leds[k]['x'], leds[k]['y'])):
        for c in cols:
            if abs(leds[c[0]]['x'] - leds[i]['x']) < COL_TOL:
                c.append(i); break
        else:
            cols.append([i])
    for c in cols:
        c.sort(key=lambda k: leds[k]['y'])
    return sorted(cols, key=lambda c: leds[c[0]]['x'])


def build(side='left'):
    leds, cutouts, other = extract(
        plate_path(side))
    outline = max(other, key=lambda l: abs(sum(
        l[k][0] * l[k + 1][1] - l[k + 1][0] * l[k][1] for k in range(len(l) - 1))))
    keep = [strip_led_bump(l, leds) for l in cutouts if len(l) > 10]
    keep += [l for l in cutouts if len(l) <= 10]
    keep += [l for l in other if l is not outline]
    field = Field(keep, outline, PAD, EDGE_MARGIN)

    n = len(leds)
    regular = [i for i, l in enumerate(leds) if abs(l['kang'] + 90.0) < 0.5]
    odd     = [i for i in range(n) if i not in regular]
    cols = group_columns(leds, regular)
    print(f'  {n} LEDs: {len(regular)} on-grid in {len(cols)} columns, {len(odd)} rotated')

    segs = []          # list of dicts: kind, pts

    # Columns whose x differ by less than BAND_MERGE are one physical column of
    # the matrix (e.g. a bottom key nudged sideways) — no rail fits between them.
    bands = [list(cols[0])]
    bandx = [[leds[cols[0][0]]['x']] * 2]
    for c in cols[1:]:
        x = leds[c[0]]['x']
        if x - bandx[-1][1] < BAND_MERGE:
            bands[-1] += c; bandx[-1][1] = x
        else:
            bands.append(list(c)); bandx.append([x, x])
    cols = bands
    print(f'  -> {len(cols)} column bands at x = '
          + ', '.join(f'{a:.1f}' if a == b else f'{a:.1f}/{b:.1f}' for a, b in bandx))

    # ---- rungs: LED -> the rail x on each side ------------------------------
    railx = [(bandx[k][1] + bandx[k + 1][0]) / 2 for k in range(len(bandx) - 1)]

    def rung(i, x_to):
        cy = leds[i]['y'] - RUNG_OFF
        a = (leds[i]['x'], cy); b = (x_to, cy)
        return a, b

    for ci, col in enumerate(cols):
        for i in col:
            for xr in (railx[ci - 1] if ci > 0 else None,
                       railx[ci] if ci < len(railx) else None):
                if xr is None:
                    continue
                a, b = rung(i, xr)
                if field.seg_free(a, b):
                    segs.append(dict(kind='rung', pts=[list(a), list(b)]))

    # ---- rails: vertical runs joining the rungs they serve -------------------
    for ci, xr in enumerate(railx):
        ys = sorted(leds[i]['y'] - RUNG_OFF
                    for i in cols[ci] + cols[ci + 1])
        # walk consecutive rung heights, emit the free portions
        for y0, y1 in zip(ys, ys[1:]):
            if y1 - y0 < 1e-6:
                continue
            if field.seg_free((xr, y0), (xr, y1)):
                segs.append(dict(kind='rail', pts=[[xr, y0], [xr, y1]],
                                 chan=ci, gap=len([s for s in segs
                                                   if s['kind'] == 'rail'
                                                   and s.get('chan') == ci])))
            else:
                print(f'  !! rail x={xr:.2f} blocked between y={y0:.1f}..{y1:.1f}')

    # ---- connectivity bookkeeping ------------------------------------------
    parent = list(range(n))
    def uf_find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = uf_find(a), uf_find(b)
        if ra != rb:
            parent[ra] = rb

    # a rung ties its LED to everything else on that rail
    rail_members = {i: [] for i in range(len(railx))}
    for ci, col in enumerate(cols):
        for i in col:
            for ri in (ci - 1, ci):
                if 0 <= ri < len(railx):
                    a, b = rung(i, railx[ri])
                    if field.seg_free(a, b):
                        rail_members[ri].append(i)
    for ri, mem in rail_members.items():
        for i in mem[1:]:
            union(mem[0], i)

    # ---- routed links for the rotated thumb keys ----------------------------
    # A stem may only meet a diffuser where the diffuser actually HAS a bottom
    # cap.  parts/diffuser.scad builds that cap as
    #     circle(d = cutout_diameter + 2*cap_overlap)  minus  {local y <= 0.25}
    # i.e. a minor segment on the round side only — NOT a half disc.  Anchoring
    # a stem outside it would leave it floating in mid-air.
    def local(l, p):
        """point -> diffuser-local frame (+y = the round/bulge side)."""
        a = math.radians(l['kang'])
        dx, dy = p[0] - l['x'], p[1] - l['y']
        return (-math.sin(a) * dx + math.cos(a) * dy,      # local x
                 math.cos(a) * dx + math.sin(a) * dy)      # local y

    def on_cap(l, p, min_y=CAP_WELD_Y, max_r=CAP_WELD_R):
        lx, ly = local(l, p)
        return ly >= min_y and math.hypot(lx, ly) <= max_r

    def boss(l):
        """the canonical weld point: RUNG_OFF out along the round side."""
        a = math.radians(l['kang'])
        return (l['x'] + RUNG_OFF * math.cos(a), l['y'] + RUNG_OFF * math.sin(a))

    ports = {}
    for i, l in enumerate(leds):
        cs = []
        i0, j0 = field.ij((l['x'], l['y']))
        rad = int(CAP_R / 0.5) + 1
        for di in range(-rad, rad + 1):
            for dj in range(-rad, rad + 1):
                p = field.xy(i0 + di, j0 + dj)
                if on_cap(l, p) and field.is_free(i0 + di, j0 + dj):
                    cs.append((i0 + di, j0 + dj))
        ports[i] = cs
        if not cs:
            print(f'  !! LED {i} has no weldable cap cell')

    guard = 0
    while len({uf_find(i) for i in range(n)}) > 1 and guard < 60:
        guard += 1
        root = uf_find(0)
        src = [c for i in range(n) if uf_find(i) == root for c in ports[i]]
        dist, prev = dijkstra(field, src)
        best = None
        for j in range(n):
            if uf_find(j) == root:
                continue
            r = best_at(dist, ports[j])
            if r and (best is None or r[0] < best[0]):
                best = (r[0], r[1], j)
        if best is None:
            print('  !! cannot reach', [i for i in range(n) if uf_find(i) != root])
            break
        L, st, j = best
        path = simplify(field, [field.xy(*c) for c in trace(prev, st)])
        # weld both ends to the boss of the diffuser they land on, so the stem
        # is guaranteed to reach solid cap material rather than its rim
        src_led = min(range(n), key=lambda k: math.dist(boss(leds[k]), path[0]))
        path = [boss(leds[src_led])] + path + [boss(leds[j])]
        segs.append(dict(kind='link', pts=[list(p) for p in path]))
        union(j, root)

    # ---- thin out every second long vertical run ---------------------------
    # Each row is already connected right across the matrix (adjacent columns
    # meet at a shared rail point, or a ~2.4 mm stub where the columns are
    # staggered), so the long row-to-row runs are roughly twice as many as
    # connectivity needs.  Drop them in a brick pattern, but only ever accept a
    # removal that leaves every diffuser still joined to the rest of the part.
    if THIN_VERTICALS:
        before = sum(seg_len(s) for s in segs)
        nrails = len(railx)

        def droppable(s):
            # the two outermost channels are the frame's backbone — never thin
            if OUTER_RAILS_FULL and s['chan'] in (0, nrails - 1):
                return False
            # inner channels: keep 1 in INNER_KEEP_EVERY, staggered per channel,
            # so consecutive gaps may both be empty
            return (s['chan'] + s['gap']) % INNER_KEEP_EVERY != 0

        cand = [k for k, s in enumerate(segs)
                if s['kind'] == 'rail' and seg_len(s) > SHORT_RAIL and droppable(s)]
        dropped = []
        for k in cand:
            trial = [s for idx, s in enumerate(segs) if idx not in dropped + [k]]
            if graph_connected(trial, leds):
                dropped.append(k)
        segs = [s for idx, s in enumerate(segs) if idx not in dropped]
        segs = prune_dead_ends(segs, leds)
        after = sum(seg_len(s) for s in segs)
        pct = 100 * (before - after) / before if before else 0.0
        print(f'  thinned {len(dropped)}/{len(cand)} long vertical runs: '
              f'{before:.0f} -> {after:.0f} mm ({pct:.0f}% less stem)')

    # NOT from `parent`: that only tracks the rung/link phases, so it would
    # under-report after thinning and dead-end pruning removed rails.
    comps = count_components(segs, leds)
    total = sum(sum(math.dist(s['pts'][k], s['pts'][k + 1])
                    for k in range(len(s['pts']) - 1)) for s in segs)
    print(f'  segments {len(segs)} ({sum(1 for s in segs if s["kind"]=="rung")} rungs, '
          f'{sum(1 for s in segs if s["kind"]=="rail")} rails, '
          f'{sum(1 for s in segs if s["kind"]=="link")} routed links), '
          f'components {comps}, stem {total:.0f} mm')

    return dict(leds=leds, sw=[[list(p) for p in l] for l in keep],
                outline=[list(p) for p in outline], segs=segs,
                comps=comps, stem_w=STEM_W, total=total)





# ======================================================================
# OpenSCAD emitter
# ======================================================================
def emit_scad(side, D, path):
    outline = D['outline']
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    def S(p):
        """plate KiCad coords (y down) -> OpenSCAD coords (y up), recentred."""
        return (p[0] - ox, -(p[1] - oy))

    nrail = sum(1 for x in D['segs'] if x['kind'] == 'rail')
    nrung = sum(1 for x in D['segs'] if x['kind'] == 'rung')
    nlink = sum(1 for x in D['segs'] if x['kind'] == 'link')

    L = []
    L.append(f"""// ===========================================================================
//  PolyKybd split72 — one-piece LED diffuser frame ({side} half)
//
//  GENERATED — do not edit the coordinates by hand.
//  Re-run:  python3 parts/tools/gen_diffuser_frame.py {side}
//
//  All 36 diffusers sit at their exact plate position and orientation, tied
//  together by a web UNDER the plate that routes through the solid material
//  between the switch openings.  The diffuser itself is parts/diffuser.scad's
//  diffuser() module, used unmodified — this file adds only the web.
//
//  ---------------------------------------------------------------------
//  revision   {REV}          generated {DATE}
//  source     poly_kybd/poly_kybd_split72_plate_{side}.kicad_pcb
//  diffusers  {len(D['leds'])}
//  web        {nrung} rungs + {nrail} rails + {nlink} routed links,
//             {D['total']:.0f} mm of {D['stem_w']} mm stem
//  clearance  >= {CLEAR:.2f} mm from every switch opening (checked per segment)
//
//  ASSEMBLY   Offer the frame up to the plate FROM BELOW so each diffuser
//             passes through its own switch opening, then slide it ~5.5 mm
//             away from the round side until every plug seats in its
//             half-round.  The top and bottom caps then trap the plate and
//             the switches block it sliding back, so no glue or snap fit is
//             needed.  4.5 mm is the minimum that clears (the 20-degree
//             rotated thumb key is the limiting one); below 4.0 mm it binds.
//             Do this BEFORE the plate meets the spacer — the slide needs the
//             space under the plate to be clear.
//
//  The spacer is notched for this web: see right_spacer() in
//  case/case_polykybd_split72_lr.scad.  One spacer serves both halves —
//  flip it over for the other one.
//  ---------------------------------------------------------------------
// ===========================================================================

use <diffuser.scad>

// The web hangs below the plate (plate underside is z = 0), co-planar with
// diffuser()'s bottom cap stack, which occupies z = -2*cap_thickness .. 0.
web_t  = 1.0;
stem_w = {D['stem_w']};

$fn = 64;

module _stem_{side}(a, b) {{
    hull() {{
        translate(a) circle(d = stem_w);
        translate(b) circle(d = stem_w);
    }}
}}

// Grown, open-topped copy of the web — the spacer subtracts this so its ribs
// are notched exactly where the web crosses them and keep full height elsewhere.
//
// lat and deep are SEPARATE on purpose.  `deep` sets how far into the spacer
// the notch reaches, so it must stay small or the ribs get cut clean through.
// `lat` sets how wide the notch is, and wants to be big enough that a rib the
// notch only partly overlaps is removed rather than left as a fragile fin.
module diffuser_frame_{side}_clearance(lat = 0.3, deep = 0.3, up = 6) {{
    translate([0, 0, -web_t - deep])
        linear_extrude(web_t + deep + up)
            offset(r = lat) diffuser_frame_{side}_web_2d();
}}

module diffuser_frame_{side}_web_2d() {{
    union() {{""")

    for seg in D['segs']:
        pts = [S(p) for p in seg['pts']]
        for a, b in zip(pts, pts[1:]):
            L.append(f"        _stem_{side}([{a[0]:.3f}, {a[1]:.3f}], "
                     f"[{b[0]:.3f}, {b[1]:.3f}]);  // {seg['kind']}")
    L.append("    }\n}\n")
    L.append(f"module diffuser_frame_{side}_web() {{ translate([0, 0, -web_t]) "
             f"linear_extrude(web_t) diffuser_frame_{side}_web_2d(); }}\n")

    L.append(f"module diffuser_frame_{side}_diffusers() {{")
    for i, l in enumerate(D['leds']):
        x, y = S((l['x'], l['y']))
        rot = -l['kang'] - 90.0
        rot = 0.0 if abs(rot) < 1e-9 else rot
        L.append(f"    translate([{x:.3f}, {y:.3f}, 0]) rotate([0, 0, {rot:.2f}]) "
                 f"diffuser();  // LED {i}")
    L.append("}\n")

    L.append(f"""module diffuser_frame_{side}() {{
    union() {{
        diffuser_frame_{side}_diffusers();
        diffuser_frame_{side}_web();
    }}
}}

diffuser_frame_{side}();
""")
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(L))
    return path


def mirror_x(D):
    """Exact x-mirror of a built frame.

    The two plates are mirror images to within KiCad's own rounding (worst LED
    position error 0.0072 mm, worst angle error 0.000008 deg), so the right
    frame is produced by negating the left one rather than running the search
    again.  That search is grid-based, so building the two halves independently
    gave frames that differed by a fraction of a millimetre — enough that one
    spacer could not serve both.  Mirroring makes them exactly symmetric.

    diffuser() is itself symmetric about its local YZ plane, so mirroring a
    diffuser is the same as negating its rotation.
    """
    xs = [p[0] for p in D['outline']]
    cx = (min(xs) + max(xs)) / 2

    def mx(x):
        return 2 * cx - x

    def ang(a):
        return ((180.0 - a + 180.0) % 360.0) - 180.0

    return dict(
        leds=[dict(l, x=mx(l['x']), kang=ang(l['kang'])) for l in D['leds']],
        sw=[[[mx(p[0]), p[1]] for p in poly] for poly in D['sw']],
        outline=[[mx(p[0]), p[1]] for p in D['outline']],
        segs=[dict(s, pts=[[mx(p[0]), p[1]] for p in s['pts']]) for s in D['segs']],
        comps=D['comps'], stem_w=D['stem_w'], total=D['total'])


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sides', nargs='*', help="'left', 'right', or omit for both")
    ap.add_argument('--out-dir', default=os.path.join(REPO, 'parts'))
    args = ap.parse_args()
    left = None
    for side in (args.sides or ['left', 'right']):
        # not an assert: `python -O` strips those
        if side not in ('left', 'right'):
            sys.exit(f"error: unknown side {side!r} (expected 'left' or 'right')")
        print(side)
        if side == 'right':
            # exact mirror of the left half — see mirror_x()
            D = mirror_x(left if left is not None else build('left'))
            print('  mirrored from the left half (exact)')
        else:
            D = build(side)
            left = D
        if D['comps'] != 1:
            sys.exit(f"error: the {side} frame falls into {D['comps']} separate "
                     f"pieces — refusing to write it")
        p = emit_scad(side, D, os.path.join(args.out_dir, f'diffuser_frame_{side}.scad'))
        print('  wrote', os.path.relpath(p, REPO))
