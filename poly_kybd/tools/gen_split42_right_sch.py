#!/usr/bin/env python3
"""Generate poly_corne_split42_right.kicad_sch from the LEFT schematic.

CONVENTION (derived from the hand-made split72 pair, corrected 2026-07-29):
nothing is mirrored electrically. On both halves the drawn sheets keep their
left-to-right order and the nets walk the PHYSICAL board in x-order — on the
right half the drawn-left keys are physically the INNER column and get the
LOW column nets (split72-right: K_B1/K_L1 sit at x=12.25/13.5, the inner
edge, on Col2; the inner stacked pair B8+B1 shares doubled chain 1). The
split72 `c--` in invert_display() exists only because the extra 8th key
(B8) claims matrix col 0 and shifts the grid by one.

split42 has no extra key and no stacked pair, so the consequence is simple:

  1. The right GRID is a straight net-copy of the left (K_L1=Col1 ...
     K_5/K_T/K_G column = Col6, chains 1..6 per column, CS direct) — the
     matrix col->x order ascends on both halves, per keyboard.json.
  2. Only the THUMB ROW differs: physically the right thumbs sit at the
     INNER edge (x=7.5/8.5/9.5, keyboard.json [7,0..2]), so they belong to
     the drawn-outer-LEFT columns:
       K_C = Col1 / SCLK1 / SDIN1   (innermost, x=7.5, matrix [7,0])
       K_V = Col2 / SCLK2 / SDIN2   (x=8.5, matrix [7,1])
       K_B = Col3 / SCLK3 / SDIN3   (x=9.5, matrix [7,2])
     CS stays per-sheet as on the left (C=Out1_7, V=Out2_7, B=Out3_7):
     key_display[] row 3 cols 0..2 -> bit 6 of SR 1/2/3, so the firmware's
     split42.c table and keyboard.json need NO change — the schematic now
     encodes that order by design.

Drawing-wise the thumb sheet blocks are MOVED, not re-wired: each thumb
cell (sheet + pin stubs + labels + bus entries + its local bus cluster) is
translated 3 column pitches to the left so it sits directly under the
drawn column whose chain it uses, and the column's bus simply extends
straight down to it — the same plain feeder pattern every other column
uses, no cross-sheet routing. Consequences handled per thumb: the KeyCol
feeder into the old shared column trunk is deleted and a Col<n> global
label is placed directly ON the pin (the label-on-pin style the hand-made
boards use for the ShiftRegisters control pins); the per-pin SCLK/SDIN
chain labels are renamed; the CS wire keeps its point-to-point path (the
vertical drop moves with the cell and its horizontal run is stretched);
the Row4 trunk (which existed only to reach a far global label) is
replaced by a Row4 label on each moved KeyRow pin. Everything else is
byte-identical to the left sheet. Project name, title, date are updated.

RIGHT-ONLY addition: the LTR-559 light/proximity sensor block
(ltr559.kicad_sch — the Lite-On LTR-559ALS-01 application circuit from
DS86-2013-0003 p.4-5: sensor + 2x 1uF X7R + 10k pull-ups on SDA/SCL/INT,
LED_K tied to LDR for the internal emitter driver, LED_A/VLED = VDD;
I2C addr 0x23). Instantiated in the area the moved thumb blocks vacated
and wired to the existing top-level nets: VDD, GND, I2C_SDA, I2C_SCL
(the GP0/GP1 status-OLED bus); INT lands on a local LTR_INT net, unrouted
— the firmware polls (base/ltr559.c, side-agnostic). This implements
SPLIT42_REDESIGN_NOTES.md item 4 schematic-side; the PCB still needs the
8-pin ChipLED footprint (outline: datasheet p.3, 2.36x3.94x1.35 mm) and a
sensor window in the housing.

After writing, the result is verified: the per-key wiring table is traced
from the generated file and asserted against the table derived from
qmk_firmware split42 keyboard.json + split42.c key_display[]; a bus-aware
check asserts each thumb's bus cluster attaches to the target column's
bus and not the old one; the LTR559 sheet's pin nets are asserted.
Non-zero exit on any mismatch.

Usage (from poly_kybd/):
    python3 tools/gen_split42_right_sch.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kicad_sch_trace import SchNets, trace  # noqa: E402

BASE = Path(__file__).resolve().parent.parent / 'variations' / 'poly_corne'
SRC = BASE / 'poly_corne_split42_left.kicad_sch'
DST = BASE / 'poly_corne_split42_right.kicad_sch'
DATE = '2026-07-29'
ROOT_UUID = 'e63e39d7-6ac0-4ffd-8aa3-1841a4541b55'   # shared by all top files

# thumb sheet -> chain/column number it attaches to on the RIGHT
THUMBS = {'K_C': 1, 'K_V': 2, 'K_B': 3}

COL_BUS_PITCH = 36.83     # drawn column bus spacing (x = 104.14 + n*36.83)
BUS_GRID_END = 172.1      # all six column buses' grid portion ends at y=172.085
DX = -3 * COL_BUS_PITCH   # thumb block translation: 3 columns to the left

# RIGHT-ONLY addition: the LTR-559 light/proximity sensor block
# (variations/poly_corne/ltr559.kicad_sch — the Lite-On DS86-2013-0003
# application circuit; see SPLIT42_REDESIGN_NOTES.md item 4). Placed in the
# area the moved thumb blocks vacated; the sheet uuid must match the
# instance paths stored inside ltr559.kicad_sch.
LTR_SHEET_UUID = '00004a00-0000-4000-8000-0000a1755900'
LTR_SHEET_POS = (224.79, 190.5)
LTR_PINS = (('VDD', 'VDD', True), ('GND', 'GND', True),
            ('SDA', 'I2C_SDA', True), ('SCL', 'I2C_SCL', True),
            ('INT', 'LTR_INT', False))   # INT: local net, unrouted (fw polls)

# Expected right-half table: firmware keyboard.json (LAYOUT_lr_stacked42 rows
# 4-7, matrix col c at x = 8 + c, thumbs [7,0..2] at x = 7.5/8.5/9.5) x
# split42.c key_display[] (row r, col c -> SR r+1 bit c; thumb row cols 0..2
# -> bit 6 of SR 1/2/3). Grid identical to the left half; only the thumbs
# attach to the low columns.
EXPECTED = {
    'K_L1': ('Row1', 'Col1', 'Out1_1'), 'K_1': ('Row1', 'Col2', 'Out1_2'),
    'K_2': ('Row1', 'Col3', 'Out1_3'), 'K_3': ('Row1', 'Col4', 'Out1_4'),
    'K_4': ('Row1', 'Col5', 'Out1_5'), 'K_5': ('Row1', 'Col6', 'Out1_6'),
    'K_L2': ('Row2', 'Col1', 'Out2_1'), 'K_Q': ('Row2', 'Col2', 'Out2_2'),
    'K_W': ('Row2', 'Col3', 'Out2_3'), 'K_E': ('Row2', 'Col4', 'Out2_4'),
    'K_R': ('Row2', 'Col5', 'Out2_5'), 'K_T': ('Row2', 'Col6', 'Out2_6'),
    'K_L3': ('Row3', 'Col1', 'Out3_1'), 'K_A': ('Row3', 'Col2', 'Out3_2'),
    'K_S': ('Row3', 'Col3', 'Out3_3'), 'K_D': ('Row3', 'Col4', 'Out3_4'),
    'K_F': ('Row3', 'Col5', 'Out3_5'), 'K_G': ('Row3', 'Col6', 'Out3_6'),
    'K_C': ('Row4', 'Col1', 'Out1_7'), 'K_V': ('Row4', 'Col2', 'Out2_7'),
    'K_B': ('Row4', 'Col3', 'Out3_7'),
}


def sheet_block(text, sheet):
    i = text.find(f'"{sheet}"')
    s = text.rfind('(sheet\n', 0, i)
    e = text.find('\n\t)', s) + 4
    return s, e


def sheet_pin_pos(text, sheet, pin):
    s, e = sheet_block(text, sheet)
    m = re.search(r'\(pin "%s" \w+\s*\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)' % pin,
                  text[s:e])
    return float(m.group(1)), float(m.group(2)), int(m.group(3))


def elements(text, kind, coord_pat):
    """Yield (coords..., start, end) for every block of the given kind."""
    for m in re.finditer(r'\t\(%s\s*%s[\s\S]{0,320}?\n\t\)\n' % (kind, coord_pat), text):
        yield tuple(map(float, m.groups())) + (m.start(), m.end())


def wire_blocks(text, kind='wire'):
    return list(elements(
        text, kind,
        r'\(pts\s*\(xy ([\-\d.]+) ([\-\d.]+)\) \(xy ([\-\d.]+) ([\-\d.]+)\)\s*\)'))


def bus_entries(text):
    """(wire-side x, y, bus-side x, y) per bus_entry."""
    out = []
    for m in re.finditer(r'\(bus_entry\s*\(at ([\-\d.]+) ([\-\d.]+)\)\s*'
                         r'\(size ([\-\d.]+) ([\-\d.]+)\)', text):
        x, y, dx, dy = map(float, m.groups())
        out.append((x, y, x + dx, y + dy))
    return out


def branch_segments(nets, px, py):
    """Wire segments forming the dead-end branch from a pin up to the first
    junction (a point where the walk cannot continue uniquely)."""
    out = []
    cur = (px, py)
    while True:
        touching = [i for i, (x1, y1, x2, y2) in enumerate(nets.wires)
                    if i not in out
                    and ((abs(x1 - cur[0]) < 0.02 and abs(y1 - cur[1]) < 0.02)
                         or (abs(x2 - cur[0]) < 0.02 and abs(y2 - cur[1]) < 0.02))]
        if len(touching) != 1:
            break
        i = touching[0]
        out.append(i)
        x1, y1, x2, y2 = nets.wires[i]
        cur = (x2, y2) if (abs(x1 - cur[0]) < 0.02 and abs(y1 - cur[1]) < 0.02) else (x1, y1)
        others = [j for j, (a1, b1, a2, b2) in enumerate(nets.wires)
                  if j not in out
                  and min(a1, a2) - 0.02 <= cur[0] <= max(a1, a2) + 0.02
                  and min(b1, b2) - 0.02 <= cur[1] <= max(b1, b2) + 0.02]
        if len(others) != 1:
            break
    return out


def find_wire_span(text, x1, y1, x2, y2):
    for wx1, wy1, wx2, wy2, s, e in wire_blocks(text):
        if abs(wx1 - x1) < 0.02 and abs(wy1 - y1) < 0.02 \
                and abs(wx2 - x2) < 0.02 and abs(wy2 - y2) < 0.02:
            return s, e
    sys.exit(f'FATAL: wire ({x1},{y1})-({x2},{y2}) not found in source text')


def translate_x(chunk):
    """Shift every (at x ... / (xy x ... coordinate in a text chunk by DX."""
    return re.sub(r'(\((?:at|xy) )([\-\d.]+)',
                  lambda m: f'{m.group(1)}{round(float(m.group(2)) + DX, 3):g}',
                  chunk)


def generate():
    t = SRC.read_text()
    nets = SchNets(t)
    labels = list(re.finditer(
        r'\t\((?:label|global_label) "([^"]+)"[\s\S]{0,400}?\n\t\)\n', t))
    edits = []       # (start, end, replacement) — applied back-to-front
    anchor = t.find('\t(sheet_instances')
    moved = []

    for sheet, n in THUMBS.items():
        s, e = sheet_block(t, sheet)
        m = re.search(r'\(at ([\-\d.]+) ([\-\d.]+)\)\n\t\t\(size ([\-\d.]+) ([\-\d.]+)\)', t[s:e])
        sx, sy, w, h = map(float, m.groups())
        win = (sx - 0.1, sx + w + 3.85, sy - 0.1, sy + h + 0.1)

        def in_win(*pts):
            return all(win[0] <= x <= win[1] and win[2] <= y <= win[3]
                       for x, y in zip(pts[::2], pts[1::2]))

        # destination must be empty (except what we move there)
        dwin = (win[0] + DX, win[1] + DX, win[2], win[3])
        for x1, y1, x2, y2, _, _ in wire_blocks(t) + wire_blocks(t, 'bus'):
            if (dwin[0] <= x1 <= dwin[1] and dwin[2] <= y1 <= dwin[3]) or \
               (dwin[0] <= x2 <= dwin[1] and dwin[2] <= y2 <= dwin[3]):
                sys.exit(f'FATAL: destination of {sheet} not empty at ({x1},{y1})')

        # 1. the sheet block itself (project rename applied inside the chunk)
        edits.append((s, e, translate_x(t[s:e]).replace(
            'poly_corne_split42_left', 'poly_corne_split42_right')))

        # 2. pin stub wires + local bus cluster + bus entries in the window
        for x1, y1, x2, y2, ws, we in wire_blocks(t) + wire_blocks(t, 'bus'):
            if in_win(x1, y1, x2, y2):
                edits.append((ws, we, translate_x(t[ws:we])))
        for m2 in re.finditer(r'\t\(bus_entry\s*\(at ([\-\d.]+) ([\-\d.]+)\)'
                              r'[\s\S]{0,240}?\n\t\)\n', t):
            if in_win(float(m2.group(1)), float(m2.group(2))):
                edits.append((m2.start(), m2.end(), translate_x(m2.group(0))))

        # 3. the per-pin labels: translate; rename the SCLK/SDIN chain ones
        renamed = 0
        for lm in labels:
            am = re.search(r'\(at ([\-\d.]+) ([\-\d.]+)', lm.group(0))
            if not in_win(float(am.group(1)), float(am.group(2))):
                continue
            chunk = translate_x(lm.group(0))
            if re.fullmatch(r'(SCLK|SDIN)\d', lm.group(1)):
                chunk = chunk.replace(f'"{lm.group(1)}"', f'"{lm.group(1)[:4]}{n}"')
                renamed += 1
            edits.append((lm.start(), lm.end(), chunk))
        if renamed != 2:
            sys.exit(f'FATAL: {sheet}: renamed {renamed} chain labels (expected 2)')

        # 4. KeyCol: delete the old feeder branch, put Col<n> ON the moved pin
        px, py, _ = sheet_pin_pos(t, sheet, 'KeyCol')
        for i in branch_segments(nets, px, py):
            ws, we = find_wire_span(t, *nets.wires[i])
            edits.append((ws, we, ''))
        edits.append((anchor, anchor, label_block(
            'Col%d' % n, round(px + DX, 3), py, 270, 'c', n, sheet)))

        # 5. CS: move the vertical drop with the cell, stretch the horizontal
        px, py, _ = sheet_pin_pos(t, sheet, 'CS')
        drop = branch_segments(nets, px, py)[:1]
        x1, y1, x2, y2 = nets.wires[drop[0]]
        if abs(x1 - x2) > 0.02:
            sys.exit(f'FATAL: {sheet}: CS drop is not vertical')
        ws, we = find_wire_span(t, x1, y1, x2, y2)
        edits.append((ws, we, translate_x(t[ws:we])))
        turn_y = max(y1, y2)
        horiz = [(hx1, hy1, hx2, hy2, hs, he)
                 for hx1, hy1, hx2, hy2, hs, he in wire_blocks(t)
                 if abs(hy1 - turn_y) < 0.02 and abs(hy2 - turn_y) < 0.02
                 and (abs(hx1 - px) < 0.02 or abs(hx2 - px) < 0.02)]
        if len(horiz) != 1:
            sys.exit(f'FATAL: {sheet}: CS horizontal run: {len(horiz)} candidates')
        hx1, hy1, hx2, hy2, hs, he = horiz[0]
        chunk = t[hs:he].replace(f'(xy {px:g} {turn_y:g})',
                                 f'(xy {round(px + DX, 3):g} {turn_y:g})')
        edits.append((hs, he, chunk))

        # 6. bus: cut the old column's feeder, extend the target column's bus
        #    straight down to the moved cluster
        spx, spy, _ = sheet_pin_pos(t, sheet, 'SCLK')
        cluster = [(bx, by) for wx, wy, bx, by in bus_entries(t)
                   if abs(wx - (spx + 1.27)) < 0.03 and win[2] <= wy <= win[3]]
        if len(cluster) < 5:
            sys.exit(f'FATAL: {sheet}: found only {len(cluster)} bus entries')
        old_x = cluster[0][0]
        cluster_top = min(by for _, by in cluster)
        target_x = round(old_x + DX, 2)
        cut = 0
        target_bottom = None
        for x1, y1, x2, y2, ws, we in wire_blocks(t, 'bus'):
            if abs(x1 - old_x) < 0.03 and abs(x2 - old_x) < 0.03 \
                    and min(y1, y2) >= BUS_GRID_END - 0.05 \
                    and max(y1, y2) <= cluster_top + 0.02:
                edits.append((ws, we, ''))
                cut += 1
            if abs(x1 - target_x) < 0.03 and abs(x2 - target_x) < 0.03 \
                    and max(y1, y2) <= BUS_GRID_END:
                target_bottom = max(target_bottom or 0, y1, y2)
        if cut < 1 or target_bottom is None:
            sys.exit(f'FATAL: {sheet}: feeder cut={cut}, target bus bottom={target_bottom}')
        edits.append((anchor, anchor,
                      f'\t(bus\n\t\t(pts\n\t\t\t(xy {target_x:g} {target_bottom:g})'
                      f' (xy {target_x:g} {cluster_top:g})\n'
                      f'\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
                      f'\t\t(uuid "0000{n}b00-0000-4000-8000-'
                      f'{sheet.lower().replace("_", ""):0>12}")\n\t)\n'))
        moved.append(sheet)

    # 7. Row4: the trunk existed only to reach one far global label — delete
    #    it (wires, junctions, the far label) and label each moved pin.
    px, py, _ = sheet_pin_pos(t, 'K_C', 'KeyRow')
    row_net = nets.net_of(px, py)
    trunk_pts = set()
    for i, wseg in enumerate(nets.wires):
        if nets._find(('w', i)) == row_net:
            ws, we = find_wire_span(t, *wseg)
            edits.append((ws, we, ''))
            trunk_pts.update([(round(wseg[0], 2), round(wseg[1], 2)),
                              (round(wseg[2], 2), round(wseg[3], 2))])
    for jm in re.finditer(r'\t\(junction\s*\(at ([\-\d.]+) ([\-\d.]+)\)'
                          r'[\s\S]{0,160}?\n\t\)\n', t):
        if (round(float(jm.group(1)), 2), round(float(jm.group(2)), 2)) in trunk_pts:
            edits.append((jm.start(), jm.end(), ''))
    killed_label = 0
    for lm in labels:
        am = re.search(r'\(at ([\-\d.]+) ([\-\d.]+)', lm.group(0))
        if lm.group(1) == 'Row4' and nets.net_of(
                float(am.group(1)), float(am.group(2))) == row_net:
            edits.append((lm.start(), lm.end(), ''))
            killed_label += 1
    if killed_label != 1:
        sys.exit(f'FATAL: Row4 trunk label: {killed_label} matches (expected 1)')
    for sheet, n in THUMBS.items():
        px, py, _ = sheet_pin_pos(t, sheet, 'KeyRow')
        edits.append((anchor, anchor, label_block(
            'Row4', round(px + DX, 3), py, 180, 'r', n, sheet)))

    # 8. LTR-559 sensor block (right-only; redesign note 4). Sheet instance
    #    + pin stubs wired to the existing top-level nets.
    lx, ly = LTR_SHEET_POS
    w, h = 22.86, (len(LTR_PINS) + 1) * 2.54
    p = [f'\t(sheet\n\t\t(at {lx:g} {ly:g})\n\t\t(size {w:g} {h:g})\n'
         '\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type solid)\n\t\t)\n'
         '\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n'
         f'\t\t(uuid "{LTR_SHEET_UUID}")\n'
         f'\t\t(property "Sheetname" "LTR559"\n\t\t\t(at {lx:g} {ly - 0.7:g} 0)\n'
         '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
         '\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
         f'\t\t(property "Sheetfile" "ltr559.kicad_sch"\n\t\t\t(at {lx:g} {ly + h + 0.7:g} 0)\n'
         '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
         '\t\t\t\t(justify left top)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)']
    for i, (pname, _, _) in enumerate(LTR_PINS):
        py = round(ly + 2.54 * (i + 1), 3)
        p.append(f'\t\t(pin "{pname}" input\n\t\t\t(at {lx + w:g} {py:g} 0)\n'
                 '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                 '\t\t\t\t(justify right)\n\t\t\t)\n'
                 f'\t\t\t(uuid "00004a{i:02d}-0000-4000-8000-0000a17559{i:02d}")\n\t\t)')
    p.append('\t\t(instances\n\t\t\t(project "poly_corne_split42_right"\n'
             f'\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(page "30")\n'
             '\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    edits.append((anchor, anchor, '\n'.join(p)))
    for i, (pname, net, glob) in enumerate(LTR_PINS):
        py = round(ly + 2.54 * (i + 1), 3)
        sx = round(lx + w + 3.81, 3)
        edits.append((anchor, anchor,
                      f'\t(wire\n\t\t(pts\n\t\t\t(xy {lx + w:g} {py:g}) (xy {sx:g} {py:g})\n'
                      '\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
                      f'\t\t(uuid "00004a{i + 20:02x}-0000-4000-8000-0000a17559{i:02d}")\n\t)\n'))
        kind = 'global_label' if glob else 'label'
        shape = '\n\t\t(shape input)' if glob else ''
        edits.append((anchor, anchor,
                      f'\t({kind} "{net}"{shape}\n\t\t(at {sx:g} {py:g} 0)\n'
                      '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
                      '\t\t\t(justify left)\n\t\t)\n'
                      f'\t\t(uuid "00004a{i + 40:02x}-0000-4000-8000-0000a17559{i:02d}")\n\t)\n'))

    for m in re.finditer(r'\(project "(poly_corne_split42_left)"', t):
        if not any(sheet_block(t, sh)[0] < m.start() < sheet_block(t, sh)[1]
                   for sh in THUMBS):
            edits.append((m.start(1), m.end(1), 'poly_corne_split42_right'))
    m = re.search(r'\(title "(PolyCorne Split L)"', t)
    edits.append((m.start(1), m.end(1), 'PolyCorne Split R'))
    m = re.search(r'\(title_block[\s\S]{0,200}?\(date "([^"]+)"', t)
    edits.append((m.start(1), m.end(1), DATE))

    spans = sorted((s, e) for s, e, _ in edits if e > s)
    for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
        if s2 < e1:
            sys.exit(f'FATAL: overlapping edits at {s1}..{e1} / {s2}..{e2}')
    edits.sort(key=lambda ed: -ed[0])
    out = t
    for s, e, rep in edits:
        out = out[:s] + rep + out[e:]
    DST.write_text(out)
    print(f'wrote {DST.name}: {len(edits)} edits, thumb blocks moved: {moved}')


def label_block(name, x, y, ang, tag, n, sheet):
    return (f'\t(global_label "{name}"\n\t\t(shape input)\n'
            f'\t\t(at {x:g} {y:g} {ang})\n\t\t(effects\n'
            f'\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify right)\n\t\t)\n'
            f'\t\t(uuid "0000{n}{tag}01-0000-4000-8000-'
            f'{sheet.lower().replace("_", ""):0>12}")\n\t)\n')


def verify():
    r = trace(str(DST))
    fails = 0
    for s, (row, col, cs) in sorted(EXPECTED.items()):
        d = r[s]
        chain = col[-1]
        got = (d['KeyRow'], d['KeyCol'], d['SCLK'], d['SDIN'], d['CS'])
        exp = (row, col, f'SCLK{chain}', f'SDIN{chain}', f'ShiftRegisters.{cs}')
        if got != exp:
            fails += 1
            print(f'  FAIL {s}: got={got} exp={exp}')
    mcu = r['RpPico']
    for i in range(1, 7):
        if mcu.get(f'GP{9 + i}') != f'Col{i}':
            fails += 1
            print(f'  FAIL MCU GP{9 + i}: {mcu.get(f"GP{9 + i}")} != Col{i}')
    for i in range(1, 5):
        if mcu.get(f'GP{17 + i}') != f'Row{i}':
            fails += 1
            print(f'  FAIL MCU GP{17 + i}: {mcu.get(f"GP{17 + i}")} != Row{i}')
    # the thumbs' old feeder branches must be gone: Col4..6 nets must carry
    # exactly their three grid keys, no thumb
    for col, keys in (('Col4', {'K_3', 'K_E', 'K_D'}), ('Col5', {'K_4', 'K_R', 'K_F'}),
                      ('Col6', {'K_5', 'K_T', 'K_G'})):
        on_net = {s for s, d in r.items() if d.get('KeyCol') == col and s.startswith('K_')}
        if on_net != keys:
            fails += 1
            print(f'  FAIL {col} net keys: {sorted(on_net)} != {sorted(keys)}')
    ltr = r.get('LTR559')
    if ltr is None:
        fails += 1
        print('  FAIL LTR559 sheet missing')
    else:
        for pname, net, _ in LTR_PINS:
            if ltr.get(pname) != net:
                fails += 1
                print(f'  FAIL LTR559 {pname}: {ltr.get(pname)} != {net}')
    fails += verify_buses()
    print(f'verify: {len(EXPECTED)} keys + MCU pins + column membership + bus '
          f'attachment + LTR559 checked, {fails} failures')
    return fails


def verify_buses():
    """The DRAWN buses must tell the same story as the nets: each thumb's
    bus cluster reaches the target column's cells and not the old ones."""
    t = DST.read_text()
    segs = wire_blocks(t, 'bus')
    parent = {}

    def find(a):
        while parent.get(a, a) != a:
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    pts = {}
    for i, (x1, y1, x2, y2, _, _) in enumerate(segs):
        for p in ((round(x1, 2), round(y1, 2)), (round(x2, 2), round(y2, 2))):
            if p in pts:
                union(('b', i), pts[p])
            pts[p] = ('b', i) if p not in pts else pts[p]
            union(('b', i), pts[p])

    def comp_of(x, y):
        p = (round(x, 2), round(y, 2))
        if p in pts:
            return find(pts[p])
        for i, (x1, y1, x2, y2, _, _) in enumerate(segs):
            if min(x1, x2) - 0.02 <= x <= max(x1, x2) + 0.02 \
                    and min(y1, y2) - 0.02 <= y <= max(y1, y2) + 0.02:
                return find(('b', i))
        return None

    entries = bus_entries(t)

    def cell_bus_comps(sheet):
        px, py, _ = sheet_pin_pos(t, sheet, 'SCLK')
        stub_x = px + 1.27
        out = set()
        for wx, wy, bx, by in entries:
            if abs(wx - stub_x) < 0.03 and abs(wy - py) < 26:
                c = comp_of(bx, by)
                if c is not None:
                    out.add(c)
        return out

    fails = 0
    for thumb, good, bad in (('K_C', 'K_L2', 'K_E'), ('K_V', 'K_Q', 'K_R'),
                             ('K_B', 'K_W', 'K_T')):
        tc, gc, bc = cell_bus_comps(thumb), cell_bus_comps(good), cell_bus_comps(bad)
        if not tc or not tc <= gc:
            fails += 1
            print(f'  FAIL bus: {thumb} cluster not attached to {good}\'s column bus')
        if tc & bc:
            fails += 1
            print(f'  FAIL bus: {thumb} cluster still attached to {bad}\'s column bus')
    return fails


if __name__ == '__main__':
    generate()
    sys.exit(1 if verify() else 0)
