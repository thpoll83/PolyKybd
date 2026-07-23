#!/usr/bin/env python3
"""Extract the per-key PCB cluster template from a PolyKybd board.

Every key on a PolyKybd board carries the same functional cluster: the MX
socket switch (SW_K_n), the display FPC socket (J*), and the per-key passives
(C1_n..C6_n, R1_n, D1_n). This tool expresses every cluster member in its
switch's local frame (translated to the switch center, rotated by the switch
angle) and reports, per member, the placements found across all keys:

  - one placement -> the member is RIGID (a true template, replayable at any
    key position/rotation);
  - several placements -> hand-nudged copies; the majority placement is the
    template candidate and the outliers are listed with their key numbers.

The JSON it can emit (--json) is the "golden cluster" input for a placement
generator: replay {member: (dx, dy, drot, layer)} at each key's position +
rotation from a KLE layout.

Measured on poly_corne_split42_left v1.0: the FPC socket is exactly rigid at
(0.00, -9.49) rot 0 across ALL 21 keys including the rotated thumbs; the
passives have one dominant placement (keys 8-20) with small hand-nudges on
keys 1-6; thumb clusters (keys 7/14/21) use ad-hoc refs (J25/J26/J27).

Usage:
    python3 tools/extract_key_cluster.py <board.kicad_pcb> [--json out.json]

Requires kiutils (pip install kiutils).
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict

from kiutils.board import Board

MEMBERS = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'R1', 'D1', 'J']


def load_footprints(path):
    b = Board.from_file(path)
    fps = {}
    for fp in b.footprints:
        ref = fp.properties.get('Reference') if isinstance(fp.properties, dict) else None
        if not ref:
            for p in fp.properties or []:
                if getattr(p, 'key', None) == 'Reference':
                    ref = p.value
        if ref:
            fps[ref] = (fp.position.X, fp.position.Y, fp.position.angle or 0,
                        fp.layer, fp.libId)
    return fps


def to_local(fps, member_ref, sw_ref):
    sx, sy, sa, _, _ = fps[sw_ref]
    x, y, a, lay, _ = fps[member_ref]
    th = math.radians(sa)
    dx, dy = x - sx, y - sy
    lx = dx * math.cos(th) - dy * math.sin(th)
    ly = dx * math.sin(th) + dy * math.cos(th)
    return (round(lx, 2), round(ly, 2), round((a - sa) % 360, 1), lay)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        sys.exit(1)
    json_out = None
    if '--json' in sys.argv:
        json_out = sys.argv[sys.argv.index('--json') + 1]

    fps = load_footprints(args[0])
    keys = sorted(int(m.group(1)) for r in fps
                  for m in [re.match(r'SW_K_(\d+)$', r)] if m)
    print(f'{args[0]}: {len(keys)} switches')

    placements = defaultdict(lambda: defaultdict(list))
    for n in keys:
        for m in MEMBERS:
            ref = f'J{n}' if m == 'J' else f'{m}_{n}'
            if ref not in fps:
                placements[m]['MISSING'].append(n)
            else:
                placements[m][to_local(fps, ref, f'SW_K_{n}')].append(n)

    template = {}
    for m in MEMBERS:
        vs = placements[m]
        real = {v: ns for v, ns in vs.items() if v != 'MISSING'}
        if not real:
            print(f'  {m:3s} no members matched (check ref naming)')
            continue
        best = max(real.items(), key=lambda kv: len(kv[1]))
        template[m] = {'dx': best[0][0], 'dy': best[0][1],
                       'drot': best[0][2], 'layer': best[0][3]}
        n_out = sum(len(ns) for v, ns in vs.items() if v != best[0])
        tag = 'RIGID ' if len(vs) == 1 else f'{n_out:2d} outliers'
        print(f'  {m:3s} template={best[0]}  ({len(best[1])} keys, {tag})')
        for v, ns in sorted(vs.items(), key=lambda kv: str(kv[0])):
            if v != best[0]:
                print(f'        deviates: {v} keys={ns}')

    if json_out:
        with open(json_out, 'w') as f:
            json.dump(template, f, indent=2)
        print(f'template written to {json_out}')


if __name__ == '__main__':
    main()
