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
     INNER edge (x=7.5/8.5/9.5, keyboard.json [7,0..2]), so they attach to
     the drawn-outer-LEFT columns instead of the columns drawn above them:
       K_C = Col1 / SCLK1 / SDIN1   (innermost, x=7.5, matrix [7,0])
       K_V = Col2 / SCLK2 / SDIN2   (x=8.5, matrix [7,1])
       K_B = Col3 / SCLK3 / SDIN3   (x=9.5, matrix [7,2])
     CS stays per-sheet as on the left (C=Out1_7, V=Out2_7, B=Out3_7):
     key_display[] row 3 cols 0..2 -> bit 6 of SR 1/2/3, so the firmware's
     split42.c table and keyboard.json need NO change — the schematic now
     encodes that order by design.

Mechanically, per thumb cell: the KeyCol branch wires (stub + feeder into
the shared column trunk) are deleted and a global label Col<n> is placed
directly ON the pin (the same label-on-pin style the hand-made boards use
for the ShiftRegisters control pins); the per-pin SCLK/SDIN chain labels
are renamed. Everything else — every symbol, value, wire, UUID — is
byte-identical to the left sheet. Project name, title and date are updated.

After writing, the result is verified: the per-key wiring table is traced
from the generated file and asserted against the table derived from
qmk_firmware split42 keyboard.json + split42.c key_display[]. Non-zero exit
on any mismatch.

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

# thumb sheet -> chain/column number it attaches to on the RIGHT
THUMBS = {'K_C': 1, 'K_V': 2, 'K_B': 3}

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


def sheet_pin_pos(text, sheet, pin):
    i = text.find(f'"{sheet}"')
    s = text.rfind('(sheet\n', 0, i)
    blk = text[s:text.find('\n\t)', s) + 3]
    m = re.search(r'\(pin "%s" \w+\s*\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)' % pin, blk)
    return float(m.group(1)), float(m.group(2)), int(m.group(3))


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
        # stop at a junction: other segments meet or pass through cur
        others = [j for j, (a1, b1, a2, b2) in enumerate(nets.wires)
                  if j not in out
                  and min(a1, a2) - 0.02 <= cur[0] <= max(a1, a2) + 0.02
                  and min(b1, b2) - 0.02 <= cur[1] <= max(b1, b2) + 0.02]
        if len(others) != 1:
            break
    return out


def wire_pattern(x1, y1, x2, y2):
    def num(v):
        return re.escape(f'{v:g}')
    return (r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy %s %s\) \(xy %s %s\)\n\t\t\)'
            r'[\s\S]{0,220}?\n\t\)\n' % (num(x1), num(y1), num(x2), num(y2)))


def generate():
    t = SRC.read_text()
    nets = SchNets(t)
    edits = []       # (start, end, replacement) — applied back-to-front
    removed = 0

    for sheet, n in THUMBS.items():
        # 1. KeyCol: delete the branch into the shared column trunk, then
        #    attach Col<n> as a label directly on the pin.
        px, py, _ = sheet_pin_pos(t, sheet, 'KeyCol')
        for i in branch_segments(nets, px, py):
            x1, y1, x2, y2 = nets.wires[i]
            m = re.search(wire_pattern(x1, y1, x2, y2), t)
            if not m:
                sys.exit(f'FATAL: wire ({x1},{y1})-({x2},{y2}) not found in source text')
            edits.append((m.start(), m.end(), ''))
            removed += 1
        lbl = (f'\t(global_label "Col{n}"\n\t\t(shape input)\n'
               f'\t\t(at {px:g} {py:g} 270)\n\t\t(effects\n'
               f'\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
               f'\t\t\t(justify right)\n\t\t)\n'
               f'\t\t(uuid "0000{n}c01-0000-4000-8000-{sheet.lower().replace("_", ""):0>12}")\n\t)\n')
        anchor = t.find('\t(sheet_instances')
        edits.append((anchor, anchor, lbl))

        # 2. SCLK/SDIN: rename the per-pin chain label instances.
        for base in ('SCLK', 'SDIN'):
            px, py, _ = sheet_pin_pos(t, sheet, base)
            hits = 0
            for lm in re.finditer(r'\(label "(%s(\d))"[\s\S]{0,120}?\(at ([\-\d.]+) ([\-\d.]+) [\d.]+\)' % base, t):
                if abs(float(lm.group(3)) - px) < 3 and abs(float(lm.group(4)) - py) < 1:
                    edits.append((lm.start(1), lm.end(1), f'{base}{n}'))
                    hits += 1
            if hits != 1:
                sys.exit(f'FATAL: {sheet} {base} label instance: {hits} matches (expected 1)')

    for m in re.finditer(r'\(project "(poly_corne_split42_left)"', t):
        edits.append((m.start(1), m.end(1), 'poly_corne_split42_right'))
    m = re.search(r'\(title "(PolyCorne Split L)"', t)
    edits.append((m.start(1), m.end(1), 'PolyCorne Split R'))
    m = re.search(r'\(title_block[\s\S]{0,200}?\(date "([^"]+)"', t)
    edits.append((m.start(1), m.end(1), DATE))

    edits.sort(key=lambda e: -e[0])
    out = t
    for s, e, rep in edits:
        out = out[:s] + rep + out[e:]
    DST.write_text(out)
    print(f'wrote {DST.name}: {len(edits)} edits ({removed} thumb feeder wires removed)')


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
    print(f'verify: {len(EXPECTED)} keys + MCU pins + column membership checked, {fails} failures')
    return fails


if __name__ == '__main__':
    generate()
    sys.exit(1 if verify() else 0)
