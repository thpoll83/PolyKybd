#!/usr/bin/env python3
"""Generate poly_corne_split42_right.kicad_sch from the LEFT schematic.

The right half of a PolyKybd split is the same circuit as the left with a
mirrored key↔net assignment. Instead of hand-editing the copy (the split72
right side was made that way), this script derives the right top-level sheet
from the left one mechanically:

  1. Key-side matrix columns mirror: global label instances Col c -> Col (7-c)
     — but ONLY on the key side. The MCU-side instances (nets that reach an
     RpPico sheet pin) keep their names: GP10 is Col1 on both halves, per
     split42/config.h MATRIX_COL_PINS. This matches the firmware's
     LAYOUT_lr_stacked42, where the right half's matrix col 0 is the INNER
     column (x=8) and col 5 the outer edge (x=13).
  2. Display chains mirror: ALL label instances SCLK/SDIN n -> 7-n (keys and
     NI-buffer outputs alike — every chain participant is chain-local, so a
     total swap is safe; the buffers are interchangeable, all fed from
     SCLK_RAW/SDIN_RAW). Chains stay aligned with their column: chain n
     serves the keys on Col n, like the left side and like split72 does.
  3. CS (shift-register output -> keycap display select) mirrors per
     register: the ShiftRegisters sheet-pin positions Out r_b <-> Out r_(7-b)
     are swapped for r=1..3, b=1..3 (pin-position swap reconnects the
     existing point-to-point wires — no wire geometry is touched). This makes
     the right half satisfy the SAME firmware key_display[] table with NO
     invert_display() column shift (split42.c indexes the table directly;
     split72 needed its infamous `c--` because its right board kept the
     name->CS pattern while shifting columns).
  4. Thumb row: firmware idx 18-20 (right thumbs, matrix cols 0-2) =
     BITMASK1(6)/BITMASK2(6)/BITMASK3(6) = Out1_7/Out2_7/Out3_7 left-to-right
     in matrix-col order. Under the mirror the C/B slots would land on
     Out1_7/Out3_7 swapped, so Out1_7 <-> Out3_7 is swapped as well.
     NOTE: the firmware right-thumb order is itself an unverified symmetric
     guess (see split42.c) — schematic and firmware agree by construction; if
     bench bring-up ever flips the firmware order, flip this pair too.
  5. Project instance name, title block and date are updated. Everything
     else — every symbol, value, wire, UUID — is byte-identical to the left
     sheet (the split72 L/R pair shares root UUIDs the same way).

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
DATE = '2026-07-23'

# Expected right-half table: firmware keyboard.json (LAYOUT_lr_stacked42 rows
# 4-7, matrix col c at x = 8 + c) x split42.c key_display[] (row r, col c ->
# SR r+1 bit c; right thumbs cols 0-2 -> bit 6 of SR 1/2/3). Sheet names name
# the mirrored physical position (split72 convention: same names both sides).
EXPECTED = {
    'K_L1': ('Row1', 'Col6', 'Out1_6'), 'K_1': ('Row1', 'Col5', 'Out1_5'),
    'K_2': ('Row1', 'Col4', 'Out1_4'), 'K_3': ('Row1', 'Col3', 'Out1_3'),
    'K_4': ('Row1', 'Col2', 'Out1_2'), 'K_5': ('Row1', 'Col1', 'Out1_1'),
    'K_L2': ('Row2', 'Col6', 'Out2_6'), 'K_Q': ('Row2', 'Col5', 'Out2_5'),
    'K_W': ('Row2', 'Col4', 'Out2_4'), 'K_E': ('Row2', 'Col3', 'Out2_3'),
    'K_R': ('Row2', 'Col2', 'Out2_2'), 'K_T': ('Row2', 'Col1', 'Out2_1'),
    'K_L3': ('Row3', 'Col6', 'Out3_6'), 'K_A': ('Row3', 'Col5', 'Out3_5'),
    'K_S': ('Row3', 'Col4', 'Out3_4'), 'K_D': ('Row3', 'Col3', 'Out3_3'),
    'K_F': ('Row3', 'Col2', 'Out3_2'), 'K_G': ('Row3', 'Col1', 'Out3_1'),
    'K_C': ('Row4', 'Col3', 'Out3_7'), 'K_V': ('Row4', 'Col2', 'Out2_7'),
    'K_B': ('Row4', 'Col1', 'Out1_7'),
}


def mirror(n):
    return 7 - n


def generate():
    t = SRC.read_text()
    nets = SchNets(t)

    mcu_nets = set()
    for sname, pins, _ in nets.sheets():
        if sname != 'RpPico':
            continue
        for _, x, y in pins:
            n = nets.net_of(x, y)
            if n is not None:
                mcu_nets.add(n)

    edits = []
    for m in re.finditer(r'\(global_label "(Col([1-6]))"', t):
        am = re.search(r'\(at ([\-\d.]+) ([\-\d.]+) [\d.]+\)', t[m.end():m.end() + 300])
        if nets.net_of(float(am.group(1)), float(am.group(2))) in mcu_nets:
            continue  # MCU pin naming is fixed by the firmware
        edits.append((m.start(1), m.end(1), f'Col{mirror(int(m.group(2)))}'))
    for m in re.finditer(r'\(label "((SCLK|SDIN)([1-6]))"', t):
        edits.append((m.start(1), m.end(1), f'{m.group(2)}{mirror(int(m.group(3)))}'))

    for sname, _, start in nets.sheets():
        if sname != 'ShiftRegisters':
            continue
        block = re.compile(r'\(sheet\n[\s\S]*?\n\t\)').search(t, start).group(0)
        pos = {}
        for p in re.finditer(r'\(pin "(Out\d_\d)" \w+\s*\(at ([^)]+)\)', block):
            pos[p.group(1)] = (start + p.start(2), start + p.end(2), p.group(2))
        pairs = [(f'Out{r}_{b}', f'Out{r}_{7 - b}') for r in (1, 2, 3) for b in (1, 2, 3)]
        pairs.append(('Out1_7', 'Out3_7'))  # thumb order, see module docstring
        for a, b in pairs:
            (sa, ea, ata), (sb, eb, atb) = pos[a], pos[b]
            edits.append((sa, ea, atb))
            edits.append((sb, eb, ata))

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
    print(f'wrote {DST.name}: {len(edits)} edits')


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
    print(f'verify: {len(EXPECTED)} keys + MCU pins checked, {fails} failures')
    return fails


if __name__ == '__main__':
    generate()
    sys.exit(1 if verify() else 0)
