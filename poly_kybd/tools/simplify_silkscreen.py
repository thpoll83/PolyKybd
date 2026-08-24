"""Douglas-Peucker simplification of SILKSCREEN gr_poly artwork in a .kicad_pcb.

Touches ONLY (gr_poly ...) whose (layer "...") contains 'SilkS'. Copper, mask,
paste, edge cuts, footprints, zones, tracks and vias are left byte-identical.
Closed-ring aware: anchors on the two farthest-apart vertices and simplifies
each chain, so the arbitrary start vertex is not pinned. Iterative, so a
2500-point polygon cannot blow the recursion limit.
"""
import re, math, sys

def blocks(t, tok, start=0, end=None):
    end = len(t) if end is None else end
    out = []
    for m in re.finditer(r'\(%s\b' % tok, t[start:end]):
        i = start + m.start(); d = 0; j = i; s = False
        while j < end:
            c = t[j]
            if s:
                if c == '\\': j += 2; continue
                if c == '"': s = False
            else:
                if c == '"': s = True
                elif c == '(': d += 1
                elif c == ')':
                    d -= 1
                    if d == 0: out.append((i, j + 1)); break
            j += 1
    return out

def _rdp_chain(pts, eps):
    """iterative Douglas-Peucker on an open chain"""
    n = len(pts)
    if n < 3: return list(range(n))
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1: continue
        ax, ay = pts[a]; bx, by = pts[b]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        dmax = -1.0; idx = -1
        for i in range(a + 1, b):
            px, py = pts[i]
            if L == 0.0:
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * px - dx * py + bx * ay - by * ax) / L
            if d > dmax: dmax = d; idx = i
        if dmax > eps:
            keep[idx] = True
            stack.append((a, idx)); stack.append((idx, b))
    return [i for i in range(n) if keep[i]]

def simplify_ring(pts, eps, min_pts=3):
    """closed ring: anchor on the two farthest-apart vertices"""
    n = len(pts)
    if n <= min_pts: return pts
    # farthest vertex from pts[0], then farthest from that -> two anchors
    def far_from(k):
        bi, bd = k, -1.0
        for i in range(n):
            d = math.dist(pts[k], pts[i])
            if d > bd: bd = d; bi = i
        return bi
    a = far_from(0); b = far_from(a)
    if a > b: a, b = b, a
    if a == b: return pts
    c1 = pts[a:b + 1]
    c2 = pts[b:] + pts[:a + 1]
    k1 = _rdp_chain(c1, eps)
    k2 = _rdp_chain(c2, eps)
    out = [c1[i] for i in k1] + [c2[i] for i in k2[1:-1]]
    return out if len(out) >= min_pts else pts

def fmt(v):
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'

def process(path, eps, layer_match='SilkS'):
    t = open(path).read()
    before_v = after_v = 0; touched = 0
    out = []; last = 0
    for a, b in blocks(t, 'gr_poly'):
        blk = t[a:b]
        lay = re.search(r'\(layer "([^"]+)"\)', blk)
        if not lay or layer_match not in lay.group(1):
            continue
        pb = blocks(blk, 'pts')
        if not pb: continue
        ps, pe = pb[0]
        pts = [(float(x), float(y)) for x, y in
               re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', blk[ps:pe])]
        if len(pts) < 4: continue
        new = simplify_ring(pts, eps)
        before_v += len(pts); after_v += len(new); touched += 1
        body = '\n'.join('\t\t\t\t(xy %s %s)' % (fmt(x), fmt(y)) for x, y in new)
        newpts = '(pts\n%s\n\t\t\t)' % body
        out.append(t[last:a + ps]); out.append(newpts); last = a + pe
    out.append(t[last:])
    return ''.join(out), touched, before_v, after_v

if __name__ == '__main__':
    src, dst, eps = sys.argv[1], sys.argv[2], float(sys.argv[3])
    res, n, bv, av = process(src, eps)
    open(dst, 'w').write(res)
    import os
    print("  %-46s polys %d  vertices %d -> %d (-%.1f%%)  %.1f MB -> %.1f MB" %
          (os.path.basename(src), n, bv, av, 100 * (1 - av / bv) if bv else 0,
           os.path.getsize(src) / 1048576, os.path.getsize(dst) / 1048576))
