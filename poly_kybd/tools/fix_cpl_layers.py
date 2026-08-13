#!/usr/bin/env python3
"""Correct the Layer column of a JLCPCB CPL (positions.csv) after export.

Why this is needed
------------------
KiCad writes the footprint's *placement* layer into the position file. For most
parts that is also the side the part is soldered to, but not for the Kailh
hotswap sockets: `poly_kb:Kailh_socket_MX_Indicators` is placed on F.Cu while
its only paste apertures are on B.Cu, so the socket is physically soldered on
the bottom. Exported as-is, the CPL tells JLC "top" for all 36 sockets.

Rather than hardcoding SW_K, this derives the assembly side from the board: a
footprint's true side is wherever its solder paste is. Anything whose paste side
disagrees with its placement layer gets corrected.

Usage
-----
    python tools/fix_cpl_layers.py <positions.csv> [--pcb <board.kicad_pcb>]
    python tools/fix_cpl_layers.py <export_dir>    [--pcb <board.kicad_pcb>]
    python tools/fix_cpl_layers.py <positions.csv> --check    # report only

The board is guessed from the CPL filename when --pcb is omitted. Safe to run
twice: a corrected file is left untouched the second time.
"""
import argparse, csv, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKDIR = os.path.dirname(HERE)


def footprint_blocks(s):
    for m in re.finditer(r'\(footprint "', s):
        j = m.start(); d = 0; k = j
        while k < len(s):
            if s[k] == '(':
                d += 1
            elif s[k] == ')':
                d -= 1
                if d == 0:
                    yield s[j:k + 1]
                    break
            k += 1


def assembly_sides(pcb_path):
    """reference -> ('top'|'bottom' placement, 'top'|'bottom'|None paste side)"""
    s = io.open(pcb_path, encoding='utf-8', errors='replace').read()
    out = {}
    for fp in footprint_blocks(s):
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp)
        lay = re.search(r'\(layer "([^"]+)"\)', fp)
        if not ref or not lay:
            continue
        placement = 'top' if lay.group(1) == 'F.Cu' else 'bottom'
        f = len(re.findall(r'"F\.Paste"', fp))
        b = len(re.findall(r'"B\.Paste"', fp))
        paste = None if (f == 0 and b == 0) else ('top' if f > b else 'bottom')
        out[ref.group(1)] = (placement, paste)
    return out


def guess_pcb(cpl_path):
    name = os.path.basename(cpl_path).lower()
    parent = os.path.basename(os.path.dirname(os.path.abspath(cpl_path))).lower()
    hay = name + ' ' + parent
    if re.search(r'(^|[_\-])r([_\-.]|ight)', hay) or 'right' in hay:
        cand = 'poly_kybd_split72_right.kicad_pcb'
    elif re.search(r'(^|[_\-])l([_\-.]|eft)', hay) or 'left' in hay:
        cand = 'poly_kybd_split72_left.kicad_pcb'
    else:
        return None
    p = os.path.join(PKDIR, cand)
    return p if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', help='positions .csv, or the export directory')
    ap.add_argument('--pcb', help='board file (guessed from the name if omitted)')
    ap.add_argument('--check', action='store_true', help='report only, do not write')
    a = ap.parse_args()

    cpl = a.target
    if os.path.isdir(cpl):
        hits = [f for f in os.listdir(cpl) if f.lower().endswith('.csv')
                and 'position' in f.lower()]
        if len(hits) != 1:
            sys.exit('expected exactly one *position*.csv in %s, found %d' % (cpl, len(hits)))
        cpl = os.path.join(cpl, hits[0])
    if not os.path.exists(cpl):
        sys.exit('no such file: %s' % cpl)

    pcb = a.pcb or guess_pcb(cpl)
    if not pcb or not os.path.exists(pcb):
        sys.exit('could not determine the board file - pass --pcb')

    sides = assembly_sides(pcb)
    print('CPL   %s' % cpl)
    print('board %s' % pcb)

    raw = io.open(cpl, encoding='utf-8-sig', newline='').read()
    rows = list(csv.DictReader(io.StringIO(raw)))
    if not rows:
        sys.exit('empty CPL')
    fields = list(rows[0].keys())
    lay_col = next((c for c in fields if c.strip().lower() == 'layer'), None)
    des_col = next((c for c in fields if c.strip().lower() == 'designator'), None)
    if not lay_col or not des_col:
        sys.exit('CPL is missing a Designator/Layer column: %s' % fields)

    changed, unknown = [], []
    for r in rows:
        ref = (r[des_col] or '').strip()
        if ref not in sides:
            unknown.append(ref)
            continue
        placement, paste = sides[ref]
        if paste is None or paste == placement:
            continue                                  # THT, or already consistent
        if (r[lay_col] or '').strip().lower() != paste:
            changed.append((ref, r[lay_col], paste))
            r[lay_col] = paste

    if unknown:
        print('  note: %d CPL rows not found on the board (%s%s)'
              % (len(unknown), ', '.join(unknown[:5]), ' ...' if len(unknown) > 5 else ''))

    if not changed:
        print('  nothing to correct - every row already matches its paste side')
        return

    byref = {}
    for ref, old, new in changed:
        byref.setdefault((re.sub(r'[0-9_]+$', '', ref), old.strip(), new), []).append(ref)
    for (kind, old, new), refs in sorted(byref.items()):
        print('  %-8s %-6s -> %-6s  x%-3d  %s%s'
              % (kind, old, new, len(refs), ', '.join(sorted(refs)[:3]),
                 ' ...' if len(refs) > 3 else ''))

    if a.check:
        print('  --check: %d row(s) would change, nothing written' % len(changed))
        sys.exit(1)

    nl = '\r\n' if '\r\n' in raw else '\n'
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator=nl)
    w.writeheader()
    w.writerows(rows)
    io.open(cpl, 'w', encoding='utf-8-sig', newline='').write(buf.getvalue())
    print('  corrected %d row(s) and saved' % len(changed))


if __name__ == '__main__':
    main()
