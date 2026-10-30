#!/usr/bin/env python3
"""Verify the reset/boot plunger against the hole it slides in.

    python3 parts/case/check_btn_plunger.py

Unlike the status-LED insert, this part MOVES, so "it fits" is not one question
but five, and four of them are about where it is allowed to go:

  it fits at rest          the nose in the wall, the ears behind the shoulder
  it can be pressed        still inside the cavity after btn_travel inward, so
                           the switch's own travel is what stops it, not the case
  it cannot come OUT       pushed outward it must foul - that is the ears doing
                           their job, and the only thing holding the part in
  it clears the switch     the body and the actuator are in that cavity too, and
                           the board goes in after the plunger
  it clears the BOARD      which fitting its own cavity does NOT imply: the
                           cavity stops at the ledge top because there is no
                           case material above it to cut, so a part built to
                           the opening's full height fits perfectly and still
                           stands in the board's seat

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


def pair(name):
    """A two-element list parameter, e.g. btn_c = [ 83.69, 91.49 ];"""
    src = open(os.path.join(HERE, CASE_SCAD), encoding='utf-8').read()
    m = re.search(rf'^{name}\s*=\s*\[\s*([-0-9.]+)\s*,\s*([-0-9.]+)\s*\]\s*;', src, re.M)
    if not m:
        raise SystemExit(f'{name} not found in {CASE_SCAD}')
    return float(m.group(1)), float(m.group(2))


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
# ⚠️ every cut the case makes, or the part reads as not fitting its own hole.
# The chamfer was added to the case and not to this line, and the two fit
# checks below went red by exactly the chamfer's volume - which is the
# check doing its job, but it looks like a geometry bug for a minute.
CAVITY = ('module _cavity() { btn_opening(); btn_counterbore(); '
          'btn_nose_chamfer(); }')


def outside(dx, dz=0.0):
    return run_scad(CAVITY + f'difference() {{ translate([{dx},0,{dz}]) btn_plunger(); '
                             f'_cavity(); }}')


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

    c0, c1 = pair('btn_c')
    # ⚠️ btn_z0 is an EXPRESSION in the scad (pcb_edge_height - 0.4), so it is
    # recomputed here rather than read; param() only sees numeric literals.
    z0, h = param('pcb_edge_height') - 0.4, param('btn_h')
    post, half = param('btn_post'), 0.5 + param('btn_r') + param('btn_ear')
    mid = (c0 + c1) / 2

    # The bar's slot. ⚠️ This is NOT testable by lifting the part: the noses are
    # already located in their holes to +-0.12, so they foul first whatever the
    # pocket does, and a lift test passes just as happily with no slot at all.
    # What the slot adds is a SECOND bearing 2.5 mm lower, which is what stops
    # the part rocking while two noses are lined up with two holes from inside.
    # So measure the pocket's own z profile instead: along the middle there must
    # be solid case between the slot's top and the opening.
    bar_gap, bh = param('btn_bar_gap'), param('btn_bridge_h')
    slot_top = z0 - param('btn_under') + bh + 2 * bar_gap
    mid_band = (f'translate([0,0,{slot_top + 0.05}]) '
                f'linear_extrude({z0 - slot_top - 0.1}) '
                f'translate([0,{mid}]) square([600,2], center=true)')
    waist = run_scad(CAVITY + f'intersection() {{ _cavity(); {mid_band}; }}')
    check(waist <= EPS, 'the pocket narrows to a slot along the middle',
          f'{waist:.6f} mm3 of cavity between the slot top and the opening')
    # control: at the ends the same band MUST be open, or the posts could not
    # reach down to the bar and this check would be passing on a solid block.
    end_band = mid_band.replace(f'translate([0,{mid}])',
                                f'translate([0,{c0 - half + post / 2}])')
    ends = run_scad(CAVITY + f'intersection() {{ _cavity(); {end_band}; }}')
    check(ends > 0.5, 'control: and stays full height at the ends, for the posts',
          f'{ends:.3f} mm3 of cavity there')

    # The switch body and actuator share the cavity. btn_plunger() already
    # subtracts them, so this measures whether that subtraction actually bites
    # where the part is closest to the switch.
    # ⚠️ btn_switch_clear() defaults to the TOLERANCED envelope, which is what
    # the part is built against. Testing against that is testing the part
    # against itself, so these pass tol = 0 and move the envelope by hand.
    tol = param('btn_switch_tol')

    def clears(dx, env_dx, label):
        c = run_scad(f'difference() {{ translate([{dx},0,0]) btn_plunger(); '
                     f'translate([{env_dx},0,0]) btn_switch_clear(0, 0); }}')
        w = run_scad(f'translate([{dx},0,0]) btn_plunger();')
        check(abs(c - w) <= EPS, label,
              f'{w - c:.6f} mm3 of the part is inside the switch envelope')

    clears(-travel, 0.0, 'it clears the switch at nominal, at full travel')
    # The two extremes. Out: the actuator meets the pocket floor, so the press is
    # just the switch's own travel, against a body that is tol nearer. In: the
    # press is travel + 2 tol through the slack, against a body tol further.
    clears(-travel, +tol, f'... and with the switch {tol} mm toward the wall')
    clears(-(travel + 2 * tol), -tol, f'... and {tol} mm away, through the slack')

    # At the recessed extreme the plunger has to travel travel + 2 tol, which is
    # more than the counterbore is deep - it pushes past the ledge's inner face
    # and into the case. That is free space, not a wall, but _cavity() does not
    # know about it, so the deep-travel test needs it added or it fails for the
    # wrong reason.
    deep = run_scad(CAVITY + f'difference() {{ '
                             f'translate([{-(travel + 2 * tol)},0,0]) btn_plunger(); '
                             f'_cavity(); led_band_r(led_in_r(), led_in_r() - 20); }}')
    check(deep <= EPS,
          f'it has room for the full {travel + 2 * tol:.2f} mm of travel',
          f'{deep:.6f} mm3 outside the cavity and the case interior together')

    # --- the board ---------------------------------------------------------
    # The board goes in AFTER the plunger and rests on the ledge, whose top face
    # sits BELOW the top of the opening (btn_ledge_top() 11.5 against 12.1). So
    # anything built to the opening's full height that also reaches inboard of
    # the wall stands in the board's seat - the ears did, by 0.48 mm, and no
    # check above could have caught it: a part is measured against the cavity,
    # and the cavity simply stops there because the case has no material up
    # there to remove. Hence a check against the BOARD, not against the hole.
    pcb_gap = param('btn_pcb_gap')
    foul = run_scad('intersection() { btn_plunger(); btn_board_stub(); }')
    check(foul <= EPS, 'it clears the board on its ledge',
          f'{foul:.6f} mm3 of the part inside the board')
    # ⚠️ control. Raised by the gap it MUST foul - and note the nose cannot:
    # it is in the wall, outboard of the board's edge, so whatever this finds
    # is the ears and the posts, which is exactly what is capped.
    lift = pcb_gap + 0.2
    ctl = run_scad(f'intersection() {{ translate([0,0,{lift}]) btn_plunger(); '
                   f'btn_board_stub(); }}')
    check(ctl > 0.1, f'control: raised {lift:.1f} mm it does foul the board',
          f'{ctl:.3f} mm3')

    # --- the bridge and its slot -------------------------------------------------------
    # The two plungers ship as ONE part so they fit in a single go, which only
    # works if the thing joining them is a FLEXURE and not a weld: reset and
    # boot have to work independently (pressing both at once is the RP2040
    # bootloader gesture). Two things make it one, and both are measured here
    # rather than argued - the plungers must be cut apart above the bridge, and
    # the bridge must touch them only at its two ends.
    # a thin slab on the separation plane, over the plungers' own height
    sep = param('btn_sep')
    slab = (f'translate([0,0,{z0 - 0.2}]) linear_extrude({h + 0.4}) '
            f'translate([0,{mid}]) square([600,{sep - 0.01}], center=true)')
    joined = run_scad(f'intersection() {{ btn_plunger(); {slab}; }}')
    check(joined <= EPS,
          f'the two plungers are cut apart above the bridge ({sep} mm)',
          f'{joined:.6f} mm3 bridging them at the separation plane')
    # ⚠️ control for BOTH slab checks: the counterbore is continuous across that
    # plane, so if the slab were mislaid or the boolean broken this reads 0 too.
    ctrl = run_scad(f'intersection() {{ btn_counterbore(); {slab}; }}')
    check(ctrl > 1.0, 'control: the slab does find the counterbore there',
          f'{ctrl:.3f} mm3')

    # and a slab between the bridge's top and the plungers' bottom, in the span
    # between the posts: anything here is the bridge touching what it must not.
    bz = z0 - param('btn_under') + 0.4 + param('btn_bridge_h')
    span_lo, span_hi = c0 - half + post, c1 + half - post
    free = run_scad(f'intersection() {{ btn_plunger(); '
                    f'translate([0,0,{bz + 0.05}]) linear_extrude({z0 - bz - 0.1}) '
                    f'translate([0,{mid}]) square([600,{span_hi - span_lo}], center=true); }}')
    check(free <= EPS, 'the bridge is free of them between its posts',
          f'{free:.6f} mm3 of contact along the span')

    # The flexure, from the geometry rather than from intent. E and the flexural
    # strength are material properties this cannot measure, so the numbers are
    # REPORTED with the assumption named, not asserted.
    span = span_hi - span_lo
    t, bh = param('btn_bridge_t'), param('btn_bridge_h')
    E = 2500.0            # MPa, a typical SLA resin
    F = 12 * E * (bh * t ** 3 / 12.0) * travel / span ** 3
    sig = 6 * E * (t / 2) * travel / span ** 2
    print()
    print(f'  NOTE      bridge: {span:.2f} mm free span, {t} x {bh} mm section, '
          f'{travel} mm deflection.')
    print(f'            At E = {E:.0f} MPa that is {F:.2f} N of extra force and '
          f'{sig:.1f} MPa of bending stress,')
    print(f'            against ~2.5 N to actuate the other switch and ~65 MPa '
          f'flexural strength.')

    print()
    print(f'  NOTE      switch tolerance +-{tol} mm in the actuation axis. The pocket is cut to')
    print(f'            the furthest-OUT position, so at the other extreme the press runs '
          f'through')
    print(f'            up to {2 * tol:.2f} mm of slack first: {travel:.2f}..{travel + 2 * tol:.2f} mm '
          f'of plunger travel, not a flat {travel:.2f}.')

    # What is left as an ESD path, reported not asserted.
    print()
    print(f'  NOTE      the remaining path is the sliding gap: {gap} mm per face '
          f'round a 6.0 x 3.0 opening')
    print(f'            = {2 * (6.0 + 3.0) * gap:.2f} mm2 of slot against the '
          f'{6.0 * 3.0:.1f} mm2 the open window had, 2.9 mm deep,')
    print(f'            with a {ear} mm counterbore step and a corner on the two '
          f'long sides. DIMENSIONAL protection -')
    print(f'            see the note in the case file.')
    cham = param('btn_chamfer')
    print(f'            The {cham} mm chamfer at the nose root shortens the tight '
          f'section on the two')
    print(f'            SHORT faces from 1.5 to {1.5 - cham:.1f} mm. The long faces '
          f'keep their full run:')
    print(f'            it flares the hole in width only, never in height.')

    print()
    if FAILURES:
        print(f'{len(FAILURES)} check(s) FAILED: ' + '; '.join(FAILURES))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
