#!/usr/bin/env python3
"""Verify the reset/boot plunger against the hole it slides in.

    python3 parts/case/check_btn_plunger.py

Unlike the status-LED insert, this part MOVES, so "it fits" is not one question
but four, and three of them are about where it is allowed to go:

  it fits at rest          the nose in the wall, the ears behind the shoulder
  it can be pressed        still inside the cavity after btn_travel inward, so
                           the switch's own travel is what stops it, not the case
  it cannot come OUT       pushed outward it must foul - that is the ears doing
                           their job, and the only thing holding the part in
  it clears the switch     the body and the actuator are in that cavity too, and
                           the board goes in after the plunger

⚠️ The protection here is DIMENSIONAL, not structural: a sliding fit cannot be
bonded, so the remaining ESD path is just the gap. This script reports its
length and area rather than asserting a threshold, because no threshold we could
write down would be evidence.

Stdlib only.  Needs `openscad` on PATH (STL export only -- no display).
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_SCAD = 'case_polykybd_split72_lr.scad'
EPS = 1e-3          # mm^3; CGAL leaves zero-volume slivers on coincident faces

FAILURES = []


def check(ok, label, detail=''):
    print(f'  {"PASS" if ok else "FAIL"}  {label}{"   " + detail if detail else ""}')
    if not ok:
        FAILURES.append(label)
    return ok


def param(name):
    src = open(os.path.join(HERE, CASE_SCAD), encoding='utf-8').read()
    m = re.search(rf'^{name}\s*=\s*([-0-9.]+)\s*;', src, re.M)
    if not m:
        raise SystemExit(f'{name} not found in {CASE_SCAD}')
    return float(m.group(1))


def load_stl(path):
    tris, cur = [], []
    for ln in open(path, encoding='ascii', errors='replace'):
        ln = ln.strip()
        if ln.startswith('vertex'):
            cur.append(tuple(float(v) for v in ln.split()[1:4]))
            if len(cur) == 3:
                tris.append(tuple(cur))
                cur = []
    return tris


def volume(tris):
    return abs(sum((a[0] * (b[1] * c[2] - c[1] * b[2])
                    - a[1] * (b[0] * c[2] - c[0] * b[2])
                    + a[2] * (b[0] * c[1] - c[0] * b[1])) / 6.0
                   for a, b, c in tris))


def run_scad(body):
    """mm^3 of `body`, or 0.0 when it evaluates to nothing."""
    # ⚠️ `use <>` imports modules and functions but NOT variables, so anything
    # this body needs from the case file is passed in as a literal below.
    src = f'use <{CASE_SCAD}>\n{body}\n'
    fd, sf = tempfile.mkstemp(prefix='_check_tmp_', suffix='.scad', dir=HERE)
    with os.fdopen(fd, 'w') as fh:
        fh.write(src)
    ofd, of = tempfile.mkstemp(prefix='x_', suffix='.stl', dir=HERE)
    os.close(ofd)
    os.remove(of)                 # openscad writes it; absence IS the signal
    try:
        r = subprocess.run(['openscad', '-o', of, '--export-format', 'asciistl', sf],
                           capture_output=True, text=True, cwd=HERE, timeout=900)
        out = r.stderr + r.stdout
        # openscad exits 1 for an EMPTY result and for a syntax error alike.
        if 'Current top level object is empty' in out:
            return 0.0
        if r.returncode != 0:
            raise RuntimeError(f'openscad exited {r.returncode}:\n{out[-800:]}')
        if not os.path.exists(of) or os.path.getsize(of) == 0:
            raise RuntimeError(f'openscad produced nothing:\n{out[-800:]}')
        return volume(load_stl(of))
    finally:
        for p in (sf, of):
            try:
                os.remove(p)
            except FileNotFoundError:
                pass


# The cavity the plunger lives in, and the part, both from the case's own
# modules. `dx` slides the part along the travel axis: the wall's outer face is
# at the larger x, so pressing it is -x.
CAVITY = 'module _cavity() { btn_opening(); btn_counterbore(); }'


def outside(dx):
    return run_scad(CAVITY + f'difference() {{ translate([{dx},0,0]) btn_plunger(); _cavity(); }}')


def main():
    argparse.ArgumentParser().parse_args()
    travel = param('btn_travel')
    gap = param('btn_slide_gap')
    ear = param('btn_ear')
    print('Checking the reset/boot plunger\n')
    print(f'  6.0 x 3.0 mm opening, {gap} mm per face sliding fit, '
          f'{ear} mm ears, {travel} mm travel\n')

    at_rest = outside(0.0)
    check(at_rest <= EPS, 'it fits at rest',
          f'{at_rest:.6f} mm3 outside the cavity')

    pressed = outside(-travel)
    check(pressed <= EPS, f'it can be pressed {travel} mm',
          f'{pressed:.6f} mm3 outside the cavity — the switch stops it, not the case')

    # Pushed outward it MUST foul: that is the ears catching the shoulder, and
    # the only thing keeping the part in the case. A pass here is the control
    # for the two above as well -- if the boolean were broken, this would be 0.
    out = outside(+0.3)
    check(out > 0.5, 'it cannot be pushed OUT (the ears catch)',
          f'{out:.3f} mm3 outside the cavity when displaced 0.3 mm')

    # The switch body and actuator share the cavity. btn_plunger() already
    # subtracts them, so this measures whether that subtraction actually bites
    # at full travel, where the part is closest to the switch.
    clash = run_scad('difference() { translate([%f,0,0]) btn_plunger(); '
                     'btn_switch_clear(); }' % -travel)
    whole = run_scad('translate([%f,0,0]) btn_plunger();' % -travel)
    check(abs(clash - whole) <= EPS, 'it clears the switch body at full travel',
          f'{whole - clash:.6f} mm3 of the part is inside the switch envelope')

    # What is left as an ESD path, reported not asserted.
    print()
    print(f'  NOTE      the remaining path is the sliding gap: {gap} mm per face '
          f'round a 6.0 x 3.0 opening')
    print(f'            = {2 * (6.0 + 3.0) * gap:.2f} mm2 of slot against the '
          f'{6.0 * 3.0:.1f} mm2 the open window had, 2.9 mm deep,')
    print(f'            with a {ear} mm step and a corner on the two long sides. '
          f'DIMENSIONAL protection - see the')
    print(f'            note in the case file.')

    print()
    if FAILURES:
        print(f'{len(FAILURES)} check(s) FAILED: ' + '; '.join(FAILURES))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
