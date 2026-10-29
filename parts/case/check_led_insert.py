#!/usr/bin/env python3
"""Verify the transparent ESD status-LED insert against its own pocket.

    python3 parts/case/check_led_insert.py            # every check
    python3 parts/case/check_led_insert.py --quick    # skip the headroom sweep

The insert and the cavity come from the same `led_*` modules, so the part can
never drift from the pocket -- but two things are NOT covered by that:

  the broken webs   the inserts ship chained on V-scored webs.  Once the row is
                    snapped off the frame and folded apart, every insert keeps
                    the ROOT half of each web it was joined by, standing
                    led_tab_l()/2 proud of its flange end face.  Nothing in the
                    pocket's own arithmetic knows about them, and the part is
                    bonded in -- a stub that fouls the cavity is found with the
                    glue already on it.
  D1's skew         D1's slot sits 3.4 deg off square to its wall, so the shared
                    part reaches further into that cavity's corner than into
                    D5's or D6's.  D1 is where both margins run out first.

Stdlib only.  Needs `openscad` on PATH (STL export only -- no display, no xvfb).
"""
import argparse
import math
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_SCAD = 'case_polykybd_split72_lr.scad'
COLLISION_EPS = 1e-4     # mm^3; CGAL leaves zero-volume slivers on the
                         # coincident faces at ANY gap -- see led_insert_gap

FAILURES = []


def check(ok, label, detail=''):
    print(f'  {"PASS" if ok else "FAIL"}  {label}{"   " + detail if detail else ""}')
    if not ok:
        FAILURES.append(label)
    return ok


def case_param(name):
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
    # ⚠️ `use <>` imports modules and FUNCTIONS but NOT variables, so the body
    # must say led_tab_l(), never led_tab_len -- the variable comes back undef,
    # led_v_tab_root() silently collapses to a 0.01 mm sliver, and the fit test
    # then passes because the stub it was meant to check is not there.
    src = f'use <{CASE_SCAD}>\n{body}\n'
    # Must live beside the case file: `use <>` resolves relative to the .scad.
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
        # openscad exits 1 for an EMPTY result and for a syntax error alike, so
        # the marker has to be tested before the return code.
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


STUBBED = """
module _stubbed(grow = 0, stubs = true) {
    led_insert();
    if (stubs) {
        translate([  led_insert_half(), led_tab_y(), led_tab_z() ])
            led_v_tab_root(led_tab_l() + 2 * grow);
        translate([ -led_insert_half(), led_tab_y(), led_tab_z() ])
            rotate([ 0, 0, 180 ]) led_v_tab_root(led_tab_l() + 2 * grow);
    }
}
module _cavity() { led_window_cut(); led_pocket_cut(); }
module _all(grow = 0, stubs = true) {
    led_place_d5() _stubbed(grow, stubs);
    led_place_d6() _stubbed(grow, stubs);
    led_place_d1() _stubbed(grow, stubs);
}
"""


def protruding(grow):
    """mm^3 of part that is NOT inside the case cavity."""
    return run_scad(STUBBED + f'difference() {{ _all({grow}); _cavity(); }}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true',
                    help='skip the headroom sweep (4 extra OpenSCAD runs)')
    a = ap.parse_args()

    tab = case_param('led_tab_len')
    stub = tab / 2
    margin = (case_param('led_pocket_overlap') - case_param('led_flange_overlap')
              + case_param('led_insert_gap'))
    print('Checking the transparent ESD status-LED insert\n')
    print(f'  web {tab:.2f} mm root to root, so each break leaves a {stub:.2f} mm stub;')
    print(f'  the cavity is {margin:.2f} mm longer than the flange at each end '
          f'(square to the wall)\n')

    # The part on its own must seat -- if this fails, nothing below means
    # anything, because the stubs would just be inheriting the flange's problem.
    bare = run_scad(STUBBED + 'difference() { _all(0, false); _cavity(); }')
    check(bare <= COLLISION_EPS, 'the insert alone seats in its pocket',
          f'{bare:.6f} mm3 outside the cavity')

    out = protruding(0)
    check(out <= COLLISION_EPS,
          'it STILL seats with the broken-off V-web stubs attached',
          f'{out:.6f} mm3 outside the cavity (two stubs, worst case)')

    ctrl = protruding(1.2)
    check(ctrl > 0.5,
          'control: a stub 1.2 mm too long IS detected',
          f'{ctrl:.3f} mm3 outside the cavity')

    if a.quick:
        print('  SKIP      headroom (--quick)')
    else:
        # What the stub could grow to before it fouls.  Reported rather than
        # asserted: it is the budget led_tab_len has, and D1's skew means it is
        # NOT simply the square margin printed above.
        hi = None
        for g in (0.1, 0.2, 0.3, 0.4):
            if protruding(g) > COLLISION_EPS:
                hi = g
                break
        if hi is None:
            print(f'  NOTE      stub headroom > {stub + 0.4:.2f} mm '
                  f'(nothing fouled up to the end of the sweep)')
        else:
            print(f'  NOTE      stub headroom {stub + hi - 0.1:.2f}..{stub + hi:.2f} mm, '
                  f'against the {stub:.2f} mm the part has — i.e. led_tab_len has about '
                  f'{2 * (hi - 0.1):.1f} mm of room left')

    print()
    if FAILURES:
        print(f'{len(FAILURES)} check(s) FAILED: ' + '; '.join(FAILURES))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
