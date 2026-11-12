#!/usr/bin/env python3
"""Generate poly_corne_split42_right.kicad_pcb from the LEFT board.

The right board has never been designed; its file was a copy of the split72
right board. This script derives it from the routed left board and the right
schematic, following the method the hand-made split72 pair shows (measured
2026-11-12, left vs right board):

  outline, mounting holes, switches   exact mirror, rotation -a
  mechanical parts (USB, buttons,     exact mirror position, rotation -a
    headers)
  ESD array at the link USB           moves with USB2, rotated 180 degrees
  chip blocks (MCU, regulators)       rigid translation, same rotation, to
                                      about the mirrored place
  key clusters                        the SAME unmirrored cluster on every key

What it writes:

  1. Outline and drawings mirrored about the board's vertical centre line.
     Logo groups and texts are moved, not mirrored, so they stay readable.
  2. Every key cell as the golden cluster: the placement and the copper that
     the majority of the left keys share to 0.01 mm (switch, FPC socket, six
     capacitors, resistor, diode; 70 tracks and vias). A right key with
     matrix position (row, col) goes where the left key (row, 7 - col) is,
     mirrored. J18, which the left board lacks, is placed like the others.
     A passive whose golden place collides with a hole, a mechanical part or
     the outline is moved by the smallest step that clears them, and the
     copper that led to it is left out.
  3. Mechanical parts at their mirrored positions.
  4. Functional blocks (found by clustering the remaining parts) as rigid
     groups with their own copper, at the mirrored place, then moved by the
     smallest step that clears the parts already placed. A block may take a
     quarter turn. Of a block's copper only complete connections are kept
     (pad to pad, or pad to a GND via); a track that led to a neighbour on
     the left board is left out.
  5. Every pad's net from KiCad's netlist of the RIGHT schematic.
  6. The LTR-559 block as a group beside the board: where the sensor sits is
     a housing decision.
  7. GND zones mirrored and refilled. A local GND zone moves with the block
     it covers.
  8. The right board's .kicad_pro, with the left board's design rules.

What it does not do: route between clusters and blocks. The ratsnest that
remains is the manual part; the run ends with a count per net group.

The run ends with KiCad's DRC on both boards. Nothing may be wrong on the
right board that is not wrong on the left board too; open connections are
expected and counted. Exit code 1 on any failure.

The output is reproducible: the same inputs give the same file, byte for
byte (KIIDs are seeded).

Needs KiCad 9's Python module and `kicad-cli`. `pcbnew` belongs to the
system Python that KiCad was built for (Ubuntu 24.04: python3.12), which is
not always the `python3` on PATH.

Usage (from poly_kybd/):
    /usr/bin/python3.12 tools/gen_split42_right_pcb.py [--no-verify]
"""
import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
import kicad_netlist  # noqa: E402

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent / 'variations' / 'poly_corne'
SRC = BASE / 'poly_corne_split42_left.kicad_pcb'
DST = BASE / 'poly_corne_split42_right.kicad_pcb'
SCH = BASE / 'poly_corne_split42_right.kicad_sch'
PRETTY = TOOLS.parent / 'poly_kb.pretty'

# Parts whose place is fixed by the case: exact mirror, rotation -a.
MECH = ('USB1', 'USB2', 'Enc0', 'Exp0', 'Exp1', 'DBG1', 'DBG3', 'SW2', 'SW3')
# Parts that must stay with a mechanical part. rot180: the group faces the
# other way on the mirrored board (the link USB points at the other half).
ANCHORED = {
    'USB2': {'members': ('U26', 'FB2'), 'rot180': True},
    # FB1 is left out: the group is not mirrored, and with FB1 in it the
    # ferrite would stand 0.9 mm outside the mirrored outline.
    'USB1': {'members': ('R7', 'R9', 'TP1', 'TP14', 'U11'), 'rot180': False},
}
BLOCK_GAP_MM = 2.0          # parts closer than this belong to one block
WINDOW_MM = (-9.525, 9.525, -13.2, 7.0)   # key tile in switch-local mm
PARK_LTR_MM = (-22.0, 30.0)  # LTR-559 group: offset from the outline's left/top
N_COLS = 6

mm = pcbnew.ToMM
IU = pcbnew.FromMM


def deg(a):
    return pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T)


def role_of(ref):
    if ref.startswith('SW_K'):
        return 'SW'
    if re.fullmatch(r'J\d+', ref):
        return 'J'
    return ref.split('_')[0]


def to_local(sw_pos, sw_deg, p):
    th = math.radians(sw_deg)
    dx, dy = mm(p.x - sw_pos.x), mm(p.y - sw_pos.y)
    return (dx * math.cos(th) - dy * math.sin(th),
            dx * math.sin(th) + dy * math.cos(th))


def net_role(net, cell):
    """What a net is to one key cell; None for a net the cell has no pad on."""
    if net == f'/{cell}/CS':
        return 'CS'            # leaves the cell: routed differently per key
    if net.startswith(f'/{cell}/'):
        return 'cell:' + net.rsplit('/', 1)[1]
    if net.startswith('Net-(D1_'):
        return 'cell:SWD'
    for pat, role in ((r'/SCLK\d', 'SCLK'), (r'/SDIN\d', 'SDIN'),
                      (r'Col\d', 'COL'), (r'Row\d', 'ROW')):
        if re.fullmatch(pat, net):
            return role
    return net


class Left:
    """Everything read from the left board before anything is changed."""

    def __init__(self, board):
        self.board = board
        self.cells = defaultdict(dict)          # 'K_F' -> {role: footprint}
        self.others = {}                        # ref -> footprint (non-key)
        for fp in board.GetFootprints():
            sheet = fp.GetSheetname()
            if sheet.startswith('/K_'):
                self.cells[sheet.strip('/')][role_of(fp.GetReference())] = fp
            elif not fp.GetReference().startswith(('kibuzzard', 'REF')):
                self.others[fp.GetReference()] = fp
        self.rc = {}                            # cell -> (row, col), 1-based
        for cell, m in self.cells.items():
            row = col = None
            for p in m['SW'].Pads():
                r = re.fullmatch(r'Row(\d)', p.GetNetname())
                row = int(r.group(1)) if r else row
            for p in m['D1'].Pads():
                c = re.fullmatch(r'Col(\d)', p.GetNetname())
                col = int(c.group(1)) if c else col
            self.rc[cell] = (row, col)

    def cell_roles(self, cell):
        roles = {}
        for fp in self.cells[cell].values():
            for p in fp.Pads():
                n = p.GetNetname()
                if n and p.GetNumber():
                    roles[n] = net_role(n, cell)
        return roles

    def pose_sig(self, cell):
        m = self.cells[cell]
        sw = m['SW']
        sig = {}
        for role, fp in m.items():
            lx, ly = to_local(sw.GetPosition(), sw.GetOrientationDegrees(), fp.GetPosition())
            sig[role] = (round(lx, 2), round(ly, 2),
                         round((fp.GetOrientationDegrees() - sw.GetOrientationDegrees()) % 360, 1),
                         fp.GetLayerName())
        return sig

    def copper(self, cell):
        """{signature: track} for copper inside the key's tile on the cell's nets."""
        m = self.cells[cell]
        sw = m['SW']
        pos, ang = sw.GetPosition(), sw.GetOrientationDegrees()
        roles = self.cell_roles(cell)
        x0, x1, y0, y1 = WINDOW_MM
        out = {}
        for t in self.board.GetTracks():
            role = roles.get(t.GetNetname())
            if role is None:
                continue
            s = to_local(pos, ang, t.GetStart())
            e = to_local(pos, ang, t.GetEnd())
            if not all(x0 <= q[0] <= x1 and y0 <= q[1] <= y1 for q in (s, e)):
                continue
            if isinstance(t, pcbnew.PCB_VIA):
                sig = ('via', role, round(s[0], 2), round(s[1], 2))
            else:
                a, b = sorted([(round(s[0], 2), round(s[1], 2)), (round(e[0], 2), round(e[1], 2))])
                sig = ('seg', role, t.GetLayerName(), a, b, t.GetWidth())
            out[sig] = t
        return out

    def golden(self):
        """The cells that share the majority placement and internal copper,
        and the copper common to all of them."""
        poses = {c: self.pose_sig(c) for c in self.cells}
        majority = {}
        for role in ('SW', 'J', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'R1', 'D1'):
            majority[role] = Counter(p[role] for p in poses.values() if role in p).most_common(1)[0][0]
        copper = {c: self.copper(c) for c in self.cells}

        def internal(c):
            return frozenset(s for s in copper[c] if s[1].startswith('cell:'))
        maj_int = Counter(internal(c) for c in self.cells).most_common(1)[0][0]
        gold = sorted(c for c in self.cells
                      if all(poses[c].get(r, majority[r]) == majority[r] for r in majority)
                      and internal(c) == maj_int)
        common = set.intersection(*[set(copper[c]) for c in gold])
        donor = next(c for c in gold if 'J' in self.cells[c])
        return gold, donor, {sig: copper[donor][sig] for sig in common}


def right_matrix(comps, pad_nets):
    """cell -> (row, col) on the right board, from KiCad's netlist."""
    rc = {}
    for ref, c in comps.items():
        sheet = (c['sheet'] or '').strip('/')
        if not sheet.startswith('K_'):
            continue
        if ref.startswith('SW_K'):
            r = re.fullmatch(r'Row(\d)', pad_nets[(ref, '1')])
            rc.setdefault(sheet, [None, None])[0] = int(r.group(1))
        elif ref.startswith('D1_'):
            col = re.fullmatch(r'Col(\d)', pad_nets[(ref, '1')])
            rc.setdefault(sheet, [None, None])[1] = int(col.group(1))
    return {k: tuple(v) for k, v in rc.items()}


# ------------------------------------------------------------ geometry helpers

def pad_rects(fp, margin=0):
    """[(x0, y0, x1, y1, side)] for the footprint's pads. side is 'F', 'B',
    or '*' for a drilled pad, which occupies both sides."""
    out = []
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        drilled = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
        side = '*' if drilled else ('F' if p.IsOnLayer(pcbnew.F_Cu) else 'B')
        out.append((bb.GetLeft() - margin, bb.GetTop() - margin,
                    bb.GetRight() + margin, bb.GetBottom() + margin, side))
    return out


def body_rect(fp):
    """The courtyard's bounding box, or None for a footprint without one."""
    front = fp.GetLayer() == pcbnew.F_Cu
    lay = pcbnew.F_CrtYd if front else pcbnew.B_CrtYd
    box = None
    for g in fp.GraphicalItems():
        if g.GetLayer() == lay:
            bb = g.GetBoundingBox()
            b = (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]),
                                         max(box[2], b[2]), max(box[3], b[3]))
    return None if box is None else box + ('F' if front else 'B',)


def track_rects(t, margin=0):
    """Squares that cover a track or via, on its copper layer ('*' = all)."""
    if isinstance(t, pcbnew.PCB_VIA):
        p, w = t.GetPosition(), t.GetWidth(pcbnew.F_Cu) // 2 + margin
        return [(p.x - w, p.y - w, p.x + w, p.y + w, '*')]
    s, e = t.GetStart(), t.GetEnd()
    w = t.GetWidth() // 2 + margin
    lay = {'F.Cu': 'F', 'B.Cu': 'B'}.get(t.GetLayerName(), t.GetLayerName())
    n = max(1, int(math.hypot(e.x - s.x, e.y - s.y) // max(w, IU(0.1))))
    out = []
    for i in range(n + 1):
        x, y = s.x + (e.x - s.x) * i // n, s.y + (e.y - s.y) * i // n
        out.append((x - w, y - w, x + w, y + w, lay))
    return out


class Occupied:
    """What is already on the board, as rectangles in a grid of 2 mm cells.
    Bodies (courtyards) collide with bodies on the same side; copper (pads,
    tracks, vias, holes) collides with copper on the same layer."""
    CELL = IU(2.0)

    def __init__(self):
        self.grid = {'body': defaultdict(list), 'cu': defaultdict(list)}

    def _cells(self, r):
        for i in range(r[0] // self.CELL, r[2] // self.CELL + 1):
            for j in range(r[1] // self.CELL, r[3] // self.CELL + 1):
                yield (i, j)

    def add(self, kind, rects):
        for r in rects:
            for c in self._cells(r):
                self.grid[kind][c].append(r)

    def hit(self, kind, rects, dx=0, dy=0):
        g = self.grid[kind]
        for x0, y0, x1, y1, lay in rects:
            r = (x0 + dx, y0 + dy, x1 + dx, y1 + dy)
            for c in self._cells(r):
                for q in g.get(c, ()):
                    if (lay == q[4] or '*' in (lay, q[4])) \
                            and r[0] < q[2] and q[0] < r[2] and r[1] < q[3] and q[1] < r[3]:
                        return True
        return False


def bbox_of(rects):
    return (min(r[0] for r in rects), min(r[1] for r in rects),
            max(r[2] for r in rects), max(r[3] for r in rects))


def connected_to_pads(tracks, fps):
    """The tracks that reach one of the footprints' pads through copper of
    the same net inside the candidate set."""
    tracks = list(tracks)
    parent = list(range(len(tracks)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def ends(t):
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            return [(p.x, p.y)]
        return [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]

    at = defaultdict(list)
    for i, t in enumerate(tracks):
        for e in ends(t):
            at[(t.GetNetCode(), e)].append(i)
    for idx in at.values():
        # at one point: a via joins everything; without one, each layer joins
        # only itself. (Joining with the first item of the list only made the
        # result depend on the list's order.)
        vias = [i for i in idx if isinstance(tracks[i], pcbnew.PCB_VIA)]
        by_layer = defaultdict(list)
        for i in idx:
            by_layer['*' if vias else tracks[i].GetLayer()].append(i)
        for same in by_layer.values():
            for j in same[1:]:
                parent[find(same[0])] = find(j)
    pads = [p for fp in fps for p in fp.Pads() if p.GetNetCode() > 0]
    live = set()
    for i, t in enumerate(tracks):
        for x, y in ends(t):
            pt = pcbnew.VECTOR2I(x, y)
            for p in pads:
                if p.GetNetCode() != t.GetNetCode() or not p.HitTest(pt):
                    continue
                if isinstance(t, pcbnew.PCB_VIA) or p.IsOnLayer(t.GetLayer()):
                    live.add(find(i))
    return [t for i, t in enumerate(tracks) if find(i) in live]


def prune_dangling(tracks, fps):
    """Drop copper that ends in the air: a block keeps only complete
    connections (pad to pad, or pad to the ground plane). The stubs that led
    to a neighbour on the left board point at nothing on the right."""
    tracks = list(tracks)
    pads = [p for fp in fps for p in fp.Pads() if p.GetNetCode() > 0]

    def on_pad(t, pt, layer=None):
        v = pcbnew.VECTOR2I(*pt)
        return any(p.GetNetCode() == t.GetNetCode() and p.HitTest(v)
                   and (layer is None or p.IsOnLayer(layer)) for p in pads)
    while True:
        at = defaultdict(list)
        for t in tracks:
            if isinstance(t, pcbnew.PCB_VIA):
                at[(t.GetNetCode(), t.GetPosition().x, t.GetPosition().y)].append(t)
            else:
                for e in (t.GetStart(), t.GetEnd()):
                    at[(t.GetNetCode(), e.x, e.y)].append(t)
        keep = []
        for t in tracks:
            code = t.GetNetCode()
            if isinstance(t, pcbnew.PCB_VIA):
                pt = (t.GetPosition().x, t.GetPosition().y)
                segs = [o for o in at[(code,) + pt] if not isinstance(o, pcbnew.PCB_VIA)]
                ok = (t.GetNetname() == 'GND' and (segs or on_pad(t, pt))) \
                    or len({o.GetLayer() for o in segs}) >= 2 or (segs and on_pad(t, pt))
            else:
                ok = True
                for e in (t.GetStart(), t.GetEnd()):
                    pt = (e.x, e.y)
                    joined = any(o is not t and (isinstance(o, pcbnew.PCB_VIA) or o.GetLayer() == t.GetLayer())
                                 for o in at[(code,) + pt])
                    ok = ok and (joined or on_pad(t, pt, t.GetLayer()))
            if ok:
                keep.append(t)
        if len(keep) == len(tracks):
            return keep
        tracks = keep


class Unit:
    """Footprints and copper that move as one rigid piece."""

    def __init__(self, name, fps, tracks=()):
        self.name, self.fps, self.tracks = name, list(fps), list(tracks)
        self.zones = []          # local zones that belong to this block
        self.shift = (0, 0)

    def move(self, dx, dy):
        v = pcbnew.VECTOR2I(int(dx), int(dy))
        for it in self.fps + self.tracks + self.zones:
            it.Move(v)

    def rotate(self, centre, degrees):
        for it in self.fps + self.tracks + self.zones:
            it.Rotate(centre, deg(degrees))

    def rects(self, margin=0):
        return [r for fp in self.fps for r in pad_rects(fp, margin)]

    def bodies(self):
        return [b for b in (body_rect(fp) for fp in self.fps) if b]

    def copper(self, margin=0):
        return self.rects(margin) + [r for t in self.tracks for r in track_rects(t, margin)]


def find_blocks(left, exclude):
    """Cluster the remaining parts of the left board into blocks."""
    free = [fp for ref, fp in sorted(left.others.items()) if ref not in exclude]
    boxes = [bbox_of(pad_rects(fp)) for fp in free]
    parent = list(range(len(free)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    gap = IU(BLOCK_GAP_MM)
    for i in range(len(free)):
        for j in range(i + 1, len(free)):
            a, b = boxes[i], boxes[j]
            dx = max(a[0] - b[2], b[0] - a[2], 0)
            dy = max(a[1] - b[3], b[1] - a[3], 0)
            if math.hypot(dx, dy) <= gap:
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i, fp in enumerate(free):
        groups[find(i)].append(fp)
    return sorted(groups.values(), key=lambda g: (-len(g), g[0].GetReference()))


def block_copper(board, fps):
    """Copper of the block: on the block's nets, inside its bounding box,
    and reaching one of its pads."""
    x0, y0, x1, y1 = bbox_of([r for fp in fps for r in pad_rects(fp, IU(0.4))])
    codes = {p.GetNetCode() for fp in fps for p in fp.Pads() if p.GetNetCode() > 0}

    def inside(pt):
        return x0 <= pt.x <= x1 and y0 <= pt.y <= y1
    cand = [t for t in board.GetTracks()
            if t.GetNetCode() in codes and inside(t.GetStart()) and inside(t.GetEnd())]
    return prune_dangling(connected_to_pads(cand, fps), fps)


# -------------------------------------------------------------------- build

def build():
    pcbnew.KIID.SeedGenerator(20261112)     # same UUIDs on every run
    comps, _, pad_nets, messages = kicad_netlist.export(SCH)
    if messages:
        sys.exit('kicad-cli reported: ' + '; '.join(messages))
    board = pcbnew.LoadBoard(str(SRC))
    left = Left(board)
    gold, donor, common = left.golden()
    rrc = right_matrix(comps, pad_nets)
    by_left_rc = {v: k for k, v in left.rc.items()}
    log = []

    edge = board.GetBoardEdgesBoundingBox()
    cx = (edge.GetLeft() + edge.GetRight()) // 2
    centre = pcbnew.VECTOR2I(cx, 0)

    def mx(x):
        return 2 * cx - x

    # ---- snapshot of the left board: poses, template copper, blocks
    left_pose = {c: (pcbnew.VECTOR2I(m['SW'].GetPosition()), m['SW'].GetOrientationDegrees())
                 for c, m in left.cells.items()}
    dm = left.cells[donor]
    donor_pose = {role: (pcbnew.VECTOR2I(fp.GetPosition()), fp.GetOrientationDegrees())
                  for role, fp in dm.items()}
    donor_pos, donor_deg = left_pose[donor]
    if donor_deg:
        sys.exit('the donor key is rotated; the local frame below assumes it is not')
    gold_pose = {r: s[:3] for r, s in left.pose_sig(donor).items()}

    def net(name):
        ni = board.FindNet(name)
        if ni is None:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
        return ni
    kept = []

    def set_pad_nets(fp):
        ref = fp.GetReference()
        for p in fp.Pads():
            want = pad_nets.get((ref, p.GetNumber()))
            if want is None or want.startswith('unconnected-') and p.GetNetCode() > 0 \
                    and (ref, p.GetNumber()) in BOARD_TIES:
                if want is not None:
                    kept.append(f'{ref}.{p.GetNumber()} stays on {p.GetNetname()} (schematic: unconnected)')
                elif p.GetNetCode() > 0:
                    p.SetNetCode(0)
                continue
            p.SetNet(net(want))
    keep = {id(t) for t in connected_to_pads(list(common.values()), dm.values())}
    template = [(sig[1], t.Duplicate()) for sig, t in sorted(common.items(), key=str)
                if id(t) in keep]
    log.append(f'golden cluster: {len(gold)} of {len(left.cells)} left keys share it '
               f'({" ".join(gold)}); donor {donor}; {len(template)} copper items '
               f'({len(common) - len(template)} common items reach no pad of the cell and are left out)')

    buffers = {r: fp for r, fp in left.others.items() if fp.GetSheetname().startswith('/NonInvertingBuffer')}
    regs = {r: fp for r, fp in left.others.items() if fp.GetSheetname() == '/ShiftRegisters/'}
    anchored_refs = set(ANCHORED) | {m for a in ANCHORED.values() for m in a['members']}
    exclude = set(MECH) | anchored_refs | set(buffers) | set(regs)
    units = []
    for anchor, spec in ANCHORED.items():
        fps = [left.others[anchor]] + [left.others[m] for m in spec['members']]
        u = Unit(f'{anchor} group', fps, [t.Duplicate() for t in block_copper(board, fps)])
        u.anchor, u.rot180, u.fixed = pcbnew.VECTOR2I(left.others[anchor].GetPosition()), spec['rot180'], True
        units.append(u)
    for fps in find_blocks(left, exclude):
        big = max(fps, key=lambda f: len(list(f.Pads())))
        u = Unit(f'{big.GetReference()} block' if len(fps) > 1 else big.GetReference(),
                 fps, [t.Duplicate() for t in block_copper(board, fps)] if len(fps) > 1 else [])
        b = bbox_of(u.rects())
        u.anchor, u.rot180, u.fixed = pcbnew.VECTOR2I((b[0] + b[2]) // 2, (b[1] + b[3]) // 2), False, False
        units.append(u)
    buf_pos = {(int(fp.GetSheetname().strip('/')[-1]), fp.GetPath().AsString().rsplit('/', 1)[1]):
               pcbnew.VECTOR2I(fp.GetPosition()) for fp in buffers.values()}

    # zones: the largest is the board's ground fill and is mirrored. A small
    # zone was drawn around one block and moves with the block it covers most.
    zones = sorted(board.Zones(), key=lambda z: -z.GetBoundingBox().GetWidth() * z.GetBoundingBox().GetHeight())
    main_zone = zones[0]
    for z in zones[1:]:
        zb = z.GetBoundingBox()

        def cover(u):
            n = 0
            for x0, y0, x1, y1, _ in u.rects():
                n += zb.GetLeft() <= (x0 + x1) // 2 <= zb.GetRight() \
                    and zb.GetTop() <= (y0 + y1) // 2 <= zb.GetBottom()
            return n
        best = max(units, key=cover)
        if cover(best):
            best.zones.append(z)
            log.append(f'local GND zone ({mm(zb.GetWidth()):.0f} x {mm(zb.GetHeight()):.0f} mm) moves with the {best.name}')
        else:
            log.append(f'local GND zone ({mm(zb.GetWidth()):.0f} x {mm(zb.GetHeight()):.0f} mm) covers no block: mirrored')
    local_zones = {z.m_Uuid.AsString() for u in units for z in u.zones}

    # texts: remember the pad each one sits next to
    texts = []
    all_pads = [(fp, i, p) for fp in board.GetFootprints() for i, p in enumerate(fp.Pads())]
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetParentGroup() is None:
            c = d.GetBoundingBox().Centre()
            fp, i, p = min(all_pads, key=lambda q: (q[2].GetPosition() - c).EuclideanNorm())
            off = c - p.GetPosition()
            texts.append((d, (fp, i, off) if off.EuclideanNorm() < IU(6) else None))

    # ---- remove all copper; the template and block copper are duplicates
    n_tracks = len(board.GetTracks())
    for t in list(board.GetTracks()):
        board.Delete(t)      # Remove() hands the item to Python; thousands of those break the bindings
    for z in board.Zones():
        z.UnFill()

    # ---- drawings
    for g in board.Groups():
        if g.GetParentGroup() is None:
            c = g.GetBoundingBox().Centre()
            g.Move(pcbnew.VECTOR2I(mx(c.x) - c.x, 0))
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_SHAPE) and d.GetParentGroup() is None:
            d.Mirror(centre, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    for fp in board.GetFootprints():
        if fp.GetReference().startswith(('kibuzzard', 'REF')):
            p = fp.GetPosition()
            a = fp.GetOrientationDegrees()
            fp.SetPosition(pcbnew.VECTOR2I(mx(p.x), p.y))
            fp.SetOrientationDegrees(-a)

    # ---- key cells: the golden cluster at the mirrored key places
    sheetfile = dm['SW'].GetSheetfile()
    cell_copper = []
    key_fps = []
    cell_frame = {}
    for cell in sorted(rrc, key=lambda c: rrc[c]):
        r, c = rrc[cell]
        src = by_left_rc[(r, N_COLS + 1 - c)]
        spos, sdeg = left_pose[src]
        tpos, tdeg = pcbnew.VECTOR2I(mx(spos.x), spos.y), -sdeg
        members = left.cells[cell]
        if 'J' not in members:
            ref = next(rf for rf, cm in comps.items()
                       if (cm['sheet'] or '').strip('/') == cell and role_of(rf) == 'J')
            j = dm['J'].Duplicate()
            j.SetReference(ref)
            j.SetPath(pcbnew.KIID_PATH(comps[ref]['path']))
            j.SetSheetname(f'/{cell}/')
            j.SetSheetfile(sheetfile)
            board.Add(j)
            members['J'] = j
            log.append(f'{ref} added in cell {cell} (missing on the left board)')
        rot, delta = deg(tdeg - donor_deg), tpos - donor_pos
        for role, fp in members.items():
            pos, ang = donor_pose[role]
            if fp.GetLayer() != dm[role].GetLayer():
                sys.exit(f'{fp.GetReference()} is on another side than the donor part')
            fp.SetOrientationDegrees(ang)
            fp.SetPosition(pos)
            fp.Rotate(donor_pos, rot)
            fp.Move(delta)
            set_pad_nets(fp)
            key_fps.append(fp)
        cell_frame[cell] = (rot, delta)
        names = {net_role(p.GetNetname(), cell): p.GetNetname()
                 for fp in members.values() for p in fp.Pads() if p.GetNetCode() > 0}
        for role, tmpl in template:
            t = tmpl.Duplicate()
            t.Rotate(donor_pos, rot)
            t.Move(delta)
            t.SetNet(net(names[role]))
            cell_copper.append((t, cell, role))

    # ---- mechanical parts and the groups tied to them
    for ref in MECH:
        if ref in ANCHORED:
            continue
        fp = left.others[ref]
        p, a = fp.GetPosition(), fp.GetOrientationDegrees()
        fp.SetPosition(pcbnew.VECTOR2I(mx(p.x), p.y))
        fp.SetOrientationDegrees(-a)
    for u in units:
        if u.rot180:
            u.rotate(u.anchor, 180)
        u.move(mx(u.anchor.x) - u.anchor.x, 0)

    # ---- cluster members that collide with a hole, a mechanical part or the
    # outline. The left board moved such parts by hand too (its corner key
    # avoids a mounting hole). The part is moved by the smallest step that
    # clears everything; its copper is left out, because it led to the place
    # the part no longer has.
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline)
    clear = IU(0.2)
    holes = [fp for fp in board.GetFootprints() if fp.GetReference().startswith('REF')]
    hard_fps = holes + [left.others[r] for r in MECH if r not in ANCHORED] \
        + [fp for u in units if u.fixed for fp in u.fps]
    hard = Occupied()
    hard.add('body', [b for b in (body_rect(fp) for fp in hard_fps) if b])
    hard.add('body', [r[:4] + ('*',) for fp in holes for r in pad_rects(fp)])
    hard.add('cu', [r for fp in hard_fps for r in pad_rects(fp)])
    hard.add('cu', [r for u in units if u.fixed for t in u.tracks for r in track_rects(t)])

    def clear_of_hard(fp):
        b = body_rect(fp)
        if (b and hard.hit('body', [b])) or hard.hit('cu', pad_rects(fp, clear)):
            return False
        return all(outline.Contains(pcbnew.VECTOR2I(x, y)) for r in pad_rects(fp, IU(0.45))
                   for x, y in ((r[0], r[1]), (r[2], r[1]), (r[0], r[3]), (r[2], r[3])))

    def place_local(fp, cell, pose):
        rot, delta = cell_frame[cell]
        fp.SetOrientationDegrees(pose[2])
        fp.SetPosition(donor_pos + pcbnew.VECTOR2I(IU(pose[0]), IU(pose[1])))
        fp.Rotate(donor_pos, rot)
        fp.Move(delta)

    passive = ('C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'R1', 'D1')
    for cell in sorted(cell_frame):
        members = left.cells[cell]
        for role in passive:
            fp = members[role]
            if clear_of_hard(fp):
                continue
            mine = [t for t, c, _ in cell_copper if c == cell]
            drop = {id(t) for t in connected_to_pads(mine, [fp])}
            rest = Occupied()
            others = [f for f in key_fps if f is not fp and f.GetReference() != fp.GetReference()]
            rest.add('body', [b for b in (body_rect(f) for f in others) if b])
            rest.add('cu', [r for f in others for r in pad_rects(f)])
            rest.add('cu', [r for t, _, _ in cell_copper if id(t) not in drop for r in track_rects(t)])
            g = gold_pose[role]
            # nearest first: steps of 0.25 mm up to 8 mm, each in four rotations
            steps = sorted(((0.25 * i, 0.25 * j) for i in range(-32, 33) for j in range(-32, 33)),
                           key=lambda s: math.hypot(*s))
            tries = [(g[0] + sx, g[1] + sy, (g[2] + turn) % 360)
                     for sx, sy in steps if math.hypot(sx, sy) <= 8 for turn in (0, 90, 180, 270)]
            for pose in tries:
                place_local(fp, cell, pose)
                b = body_rect(fp)
                if clear_of_hard(fp) and not (b and rest.hit('body', [b])) \
                        and not rest.hit('cu', pad_rects(fp, clear)):
                    cell_copper[:] = [x for x in cell_copper if id(x[0]) not in drop]
                    log.append(f'{fp.GetReference()} (cell {cell}): the golden place collides with a hole, '
                               f'a mechanical part or the outline; moved to ({pose[0]:+.2f}, {pose[1]:+.2f}) mm '
                               f'from the switch, rotation {pose[2]:.0f}; {len(drop)} copper items of it left out')
                    break
            else:
                place_local(fp, cell, g)
                log.append(f'{fp.GetReference()} (cell {cell}): COLLIDES at the golden place and no other '
                           'placement fits: place it by hand')
    # cluster copper that still crosses a hole or a mechanical part
    bad = {(c, t.GetNetCode()) for t, c, _ in cell_copper if hard.hit('cu', track_rects(t, clear))}
    if bad:
        n0 = len(cell_copper)
        cell_copper[:] = [x for x in cell_copper if (x[1], x[0].GetNetCode()) not in bad]
        log.append(f'{n0 - len(cell_copper)} cluster copper items left out: their net crosses a hole or a '
                   f'mechanical part in cells {" ".join(sorted({c for c, _ in bad}))}')

    # ---- shift registers and buffers: single parts at mirrored places
    singles = []
    for ref, fp in sorted(regs.items()):
        p = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(mx(p.x), p.y))
        singles.append(Unit(ref, [fp]))
    for ref, fp in sorted(buffers.items()):
        idx = int(fp.GetSheetname().strip('/')[-1])
        src = buf_pos[(N_COLS - 1 - idx, fp.GetPath().AsString().rsplit('/', 1)[1])]
        fp.SetPosition(pcbnew.VECTOR2I(mx(src.x), src.y))
        singles.append(Unit(ref, [fp]))

    # ---- move blocks and singles off anything already placed
    occ = Occupied()
    fixed_fps = key_fps + [left.others[r] for r in MECH if r not in ANCHORED] \
        + [fp for fp in board.GetFootprints() if fp.GetReference().startswith('REF')] \
        + [fp for u in units if u.fixed for fp in u.fps]
    occ.add('body', [b for b in (body_rect(fp) for fp in fixed_fps) if b])
    occ.add('cu', [r for fp in fixed_fps for r in pad_rects(fp)])
    occ.add('cu', [r for t, _, _ in cell_copper for r in track_rects(t)])
    occ.add('cu', [r for u in units if u.fixed for t in u.tracks for r in track_rects(t)])
    offsets = [(0, 0)] + [(int(IU(0.5 * k) * math.cos(a * math.pi / 12)), int(IU(0.5 * k) * math.sin(a * math.pi / 12)))
                          for k in range(1, 61) for a in range(24)]
    movable = [u for u in units if not u.fixed] + singles

    def inside(points, dx, dy):
        return all(outline.Contains(pcbnew.VECTOR2I(x + dx, y + dy)) for x, y in points)
    for u in movable:
        u.shift = u.turn = None
        u.bare = False
        attempts = [(turn, False) for turn in ((0, 90, 270, 180) if len(u.fps) > 1 else (0,))]
        if u.tracks:        # last resort: the parts alone, without the block's copper
            attempts += [(turn, True) for turn in (0, 90, 270, 180)]
        # a block is tried as it is first; a quarter turn can fit a place
        # whose shape is the mirror image of the one it came from
        for turn, bare in attempts:
            if bare and not u.bare:
                u.bare, u.dropped, u.tracks = True, len(u.tracks), []
            box = bbox_of(u.rects())
            mid = pcbnew.VECTOR2I((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
            if turn:
                u.rotate(mid, turn)
            bodies, copper = u.bodies(), u.copper(clear)
            margin = IU(0.5)
            corners = [(x, y) for r in bodies + u.rects(margin)
                       for x, y in ((r[0], r[1]), (r[2], r[1]), (r[0], r[3]), (r[2], r[3]))]
            for dx, dy in offsets:
                if not occ.hit('body', bodies, dx, dy) and not occ.hit('cu', copper, dx, dy) \
                        and inside(corners, dx, dy):
                    u.move(dx, dy)
                    u.shift, u.turn = (dx, dy), turn
                    break
            if u.shift is not None:
                break
            if turn:
                u.rotate(mid, -turn)
        occ.add('body', u.bodies())
        occ.add('cu', u.copper())
    for u in movable:
        if u.shift is None:
            log.append(f'NO FREE PLACE within 30 mm for {u.name}: left at the mirrored place, overlapping')
        elif u.shift != (0, 0) or u.turn or u.bare:
            log.append(f'{u.name}: moved ({mm(u.shift[0]):+.1f}, {mm(u.shift[1]):+.1f}) mm '
                       + (f'and turned {u.turn} degrees ' if u.turn else '')
                       + 'from the mirrored place to clear other parts'
                       + (f'; it fits only without its own copper ({u.dropped} items left out)' if u.bare else ''))

    # ---- LTR-559 block, parked beside the board
    park = pcbnew.VECTOR2I(edge.GetLeft() + IU(PARK_LTR_MM[0]), edge.GetTop() + IU(PARK_LTR_MM[1]))
    layout = {'U27': (0, 0, 0), 'C27': (-3.0, -1.0, 90), 'C28': (-3.0, 1.2, 90),
              'R26': (3.0, -1.6, 0), 'R27': (3.0, 0, 0), 'R28': (3.0, 1.6, 0)}
    ltr = []
    for ref, (lx, ly, ang) in layout.items():
        c = comps[ref]
        if ref == 'U27':
            fp = pcbnew.FootprintLoad(str(PRETTY), 'LTR-559ALS-01')
            fp.SetFPID(pcbnew.LIB_ID('poly_kb', 'LTR-559ALS-01'))
            # the BOM is read from the board's footprint properties
            for name, text in sorted(c['fields'].items()):
                if name in ('Footprint', 'Description') or not text:
                    continue
                fp.SetField(name, text)
                fp.GetFieldByName(name).SetVisible(False)
        else:
            fp = left.others['C24' if ref.startswith('C') else 'R25'].Duplicate()
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)   # to the top side
        fp.SetReference(ref)
        fp.SetValue(c['value'])
        fp.SetPath(pcbnew.KIID_PATH(c['path']))
        fp.SetSheetname(c['sheet'])
        fp.SetSheetfile('../../ltr559.kicad_sch')
        fp.SetOrientationDegrees(ang)
        fp.SetPosition(park + pcbnew.VECTOR2I(IU(lx), IU(ly)))
        board.Add(fp)
        ltr.append(fp)
    log.append('LTR-559 block (U27 C27 C28 R26 R27 R28) parked left of the outline: '
               'its place is a housing decision')

    # ---- nets: every pad from the right schematic's netlist
    keyed = {fp.GetReference() for fp in key_fps}
    for fp in board.GetFootprints():
        if fp.GetReference() in comps and fp.GetReference() not in keyed:
            set_pad_nets(fp)
    log += sorted(set(kept))

    # ---- copper
    added = Counter()
    for t, cell, role in cell_copper:
        board.Add(t)
        added['key clusters'] += 1
    for u in units:
        codes = {p.GetNetCode() for fp in u.fps for p in fp.Pads()}
        for t in u.tracks:
            if t.GetNetCode() in codes:
                board.Add(t)
                added[u.name] += 1
        if len(u.fps) > 1:
            g = pcbnew.PCB_GROUP(board)
            g.SetName(u.name)
            board.Add(g)
            for it in u.fps + [t for t in u.tracks if t.GetNetCode() in codes]:
                g.AddItem(it)
    g = pcbnew.PCB_GROUP(board)
    g.SetName('LTR-559 block (to be placed)')
    board.Add(g)
    for fp in ltr:
        g.AddItem(fp)
    # redesign note 1: tie the two outer pad pairs of the link ESD array
    u26 = left.others['U26']
    pads = {p.GetNumber(): p for p in u26.Pads()}
    for a, b in (('1', '10'), ('5', '6')):
        if pads[a].GetNetCode() != pads[b].GetNetCode():
            sys.exit(f'U26 pads {a} and {b} are not on one net')
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pads[a].GetPosition())
        t.SetEnd(pads[b].GetPosition())
        t.SetWidth(IU(0.2))
        t.SetLayer(u26.GetLayer())
        t.SetNet(pads[a].GetNet())
        board.Add(t)
        added['U26 pad ties'] += 1
    log.append('U26: pads 1-10 and 5-6 tied in copper (redesign note 1)')

    # ---- texts
    for d, attach in texts:
        c = d.GetBoundingBox().Centre()
        if attach:
            fp, i, off = attach
            pad = list(fp.Pads())[i]
            target = pad.GetPosition() + pcbnew.VECTOR2I(-off.x, off.y)
        else:
            target = pcbnew.VECTOR2I(mx(c.x), c.y)
        d.Move(target - c)
        if 'Left Side' in d.GetText():
            d.SetText(d.GetText().replace('Left Side', 'Right Side'))
    tb = board.GetTitleBlock()
    tb.SetTitle(tb.GetTitle().replace('Split L', 'Split R').replace('Left', 'Right'))

    # ---- zones
    for z in board.Zones():
        if z.m_Uuid.AsString() not in local_zones:
            z.Mirror(centre, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    # Fill on a freshly loaded board. Filling in this process leaves the
    # moved zones lying over foreign copper (KiCad caches each zone's
    # bounding box on the board, from before the zone moved); DRC then
    # reports 'actual 0 mm' against them.
    pcbnew.SaveBoard(str(DST), board)
    board = pcbnew.LoadBoard(str(DST))
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(DST), board)
    # The design rules are in the project file. SaveBoard writes one as a
    # side effect; write it on purpose: the left board's, renamed. The right
    # project file was derived from split72 and had other rules.
    DST.with_suffix('.kicad_pro').write_text(
        SRC.with_suffix('.kicad_pro').read_text().replace(SRC.stem, DST.stem))
    log.append(f'{DST.stem}.kicad_pro: design rules taken from the left board\'s project file')
    log.append(f'copper: {n_tracks} tracks and vias on the left board; written to the right: '
               + ', '.join(f'{v} {k}' for k, v in sorted(added.items())))
    log.append(f'unrouted connections left for manual routing: '
               f'{board.GetConnectivity().GetUnconnectedCount(False)}')
    print(f'wrote {DST.name}')
    for line in log:
        print('  ' + line)


# The left board ties these pads to a net although the schematic leaves the
# pin unconnected. The right board keeps that, so the copied copper fits.
BOARD_TIES = {('U9', '9')}   # flash exposed pad on GND


# ------------------------------------------------------------------- verify

def drc(pcb):
    """KiCad's DRC with the schematic parity test, as parsed JSON."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'drc.json'
        # nosemgrep: dangerous-subprocess-use-audit -- fixed argv, no shell
        subprocess.run(['kicad-cli', 'pcb', 'drc', '--format', 'json', '--schematic-parity',
                        '--severity-all', '--units', 'mm', '-o', str(out), Path(pcb).name],
                       cwd=Path(pcb).parent, capture_output=True, text=True, check=False)
        return json.loads(out.read_text())


def verify():
    """Judge the generated board by KiCad's DRC, with the left board as the
    baseline: nothing may be wrong on the right that is not wrong on the
    left too. Open connections are expected and counted."""
    left, right = drc(SRC), drc(DST)
    fails = 0

    def parity(d):
        return Counter((v['type'], re.sub(r'\s+', ' ', v['description']),
                        tuple(sorted(i['description'] for i in v['items'])))
                       for v in d.get('schematic_parity', []))
    extra = parity(right) - parity(left)
    for (typ, desc, items), n in sorted(extra.items()):
        fails += n
        print(f'  FAIL schematic parity, not on the left board: {typ}: {desc} {"; ".join(items)}')

    def errors(d):
        return Counter(v['type'] for v in d['violations'] if v['severity'] == 'error')
    le, re_ = errors(left), errors(right)
    for typ in sorted(re_):
        if typ == 'clearance':
            continue
        if re_[typ] > le[typ]:
            fails += re_[typ] - le[typ]
            print(f'  FAIL {typ}: {re_[typ]} on the right, {le[typ]} on the left')
    # warnings: a cut-off track end is expected (the copper between blocks is
    # not carried over); any other kind must not grow
    lw = Counter(v['type'] for v in left['violations'] if v['severity'] == 'warning')
    rw = Counter(v['type'] for v in right['violations'] if v['severity'] == 'warning')
    for typ in sorted(rw):
        if typ != 'track_dangling' and rw[typ] > lw[typ]:
            fails += rw[typ] - lw[typ]
            print(f'  FAIL warning {typ}: {rw[typ]} on the right, {lw[typ]} on the left')
    # clearance: the left board's own findings are all between 0.150 and
    # 0.1524 mm (pads inside one footprint, one track pair in a cluster)
    worst = 1.0
    for v in right['violations']:
        if v['type'] == 'clearance':
            m = re.search(r'actual ([\d.]+)', v['description'])
            actual = float(m.group(1)) if m else 0.0
            worst = min(worst, actual)
            if actual < 0.15:
                fails += 1
                print('  FAIL clearance: ' + v['description'].strip() + ' | '
                      + ' | '.join(i['description'] for i in v['items']))
    open_nets = Counter()
    for v in right.get('unconnected_items', []):
        m = re.search(r'\[([^\]]+)\]', v['items'][0]['description'])
        name = m.group(1) if m else '?'
        for pat, group in ((r'Row\d', 'Row'), (r'Col\d', 'Col'), (r'/SCLK\d', 'SCLK'), (r'/SDIN\d', 'SDIN'),
                           (r'/K_\w+/CS', 'CS'), (r'GND', 'GND'), (r'VDD|VSUP|VBUS|VSYS|\+\dV\d', 'power'),
                           (r'RESET|D-C', 'RESET, D-C')):
            if re.fullmatch(pat, name):
                name = group
                break
        else:
            name = 'other'
        open_nets[name] += 1
    dangling = sum(1 for v in right['violations'] if v['type'] == 'track_dangling')
    print(f'verify (KiCad DRC, left board as baseline): {fails} failures')
    print(f'  errors on the right: {dict(sorted(re_.items()))}; on the left: {dict(sorted(le.items()))}')
    print(f'  smallest clearance on the right: {worst:.4f} mm (rule 0.1524, left board 0.1500)')
    print(f'  schematic parity: {sum(parity(right).values())} items, all present on the left board as well'
          if not extra else f'  schematic parity: {sum(extra.values())} items not on the left board')
    print(f'  open connections: {sum(open_nets.values())} ('
          + ', '.join(f'{n} {k}' for k, n in open_nets.most_common()) + f'); track ends without a connection: {dangling}')
    return fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--no-verify', action='store_true', help='skip the DRC comparison')
    args = ap.parse_args()
    build()
    if not args.no_verify:
        sys.exit(1 if verify() else 0)


if __name__ == '__main__':
    main()
