#!/usr/bin/env python3
"""Verify the one-piece LED diffuser frame against the things that have bitten it.

    python3 parts/tools/check_frame.py            # every check, both halves
    python3 parts/tools/check_frame.py --quick    # skip the OpenSCAD boolean checks

Exits non-zero if anything fails, so it can gate a change to diffuser.scad or to
the generator.  Every number it prints was, at some point in this part's history,
wrong in a way that only showed up as a print-service rejection or a bad fit:

  watertight        a frame that is not a closed solid is not printable at all
  minimum wall      the whole reason the part was redesigned; two separate knife
                    edges shipped before this check existed (a 0.60 mm cap horn
                    and a 0.043 mm wafer where a stem grazed a tapered rim)
  spacer clearance  the web crosses the spacer's ribs; the spacer is notched for
                    it on BOTH faces so one printed part serves either half, so
                    the frame has to clear it in both flip orientations
  plate trap        the cap must overhang the plug hole all the way round or the
                    frame falls back out of the plate

Stdlib only.  The boolean checks need `openscad` on PATH (and xvfb is NOT needed
-- these export STL, they do not render).
"""
import argparse
import collections
import math
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(REPO, 'case')
PARTS = os.path.join(REPO, 'parts')

MIN_WALL = 0.99          # mm; the web is 1.0, so anything under this is a defect
VENDOR_FLOOR = 0.80      # mm; what the print service quoted as its minimum
COLLISION_EPS = 0.01     # mm^3; a degenerate boolean can leave sliver facets
                         # with a tiny positive volume -- not a real interference
FRAME_XY = (92.19, 71.79)   # frame origin in spacer coordinates (right_spacer())
SPACER_Z = (23.8, -20.0)    # top-face and flipped placements

FAILURES = []


def check(ok, label, detail=''):
    print(f'  {"PASS" if ok else "FAIL"}  {label}{"   " + detail if detail else ""}')
    if not ok:
        FAILURES.append(label)
    return ok


# ---------------------------------------------------------------- mesh utils
def load_stl(path):
    """Parse an ASCII STL.  Validated at the source: every consumer here would
    otherwise inherit a silent truncation (min_wall dropping facets) or an
    unrelated-looking crash (min() on an empty sequence)."""
    try:
        with open(path, encoding='utf-8') as fh:
            txt = fh.read()
    except UnicodeDecodeError:
        raise RuntimeError(f'{path}: not ASCII -- this repo ships ASCII STLs, '
                           f'and a binary one cannot be parsed here') from None
    v = [tuple(map(float, m)) for m in
         re.findall(r'vertex\s+(\S+)\s+(\S+)\s+(\S+)', txt)]
    n = [tuple(map(float, m)) for m in
         re.findall(r'facet normal\s+(\S+)\s+(\S+)\s+(\S+)', txt)]
    if not v or len(v) % 3 or len(n) * 3 != len(v):
        raise RuntimeError(f'{path}: not a parseable ASCII STL '
                           f'({len(n)} normals, {len(v)} vertices)')
    return [(v[i], v[i + 1], v[i + 2]) for i in range(0, len(v), 3)], n


def watertight(tris):
    """Every edge used exactly twice <=> closed, orientable surface."""
    e = collections.Counter()
    k = lambda p: (round(p[0], 6), round(p[1], 6), round(p[2], 6))
    for a, b, c in tris:
        for p, q in ((a, b), (b, c), (c, a)):
            e[tuple(sorted((k(p), k(q))))] += 1
    return sum(1 for c in e.values() if c != 2)


def volume(tris):
    s = sum((a[0] * (b[1] * c[2] - c[1] * b[2])
             - a[1] * (b[0] * c[2] - c[0] * b[2])
             + a[2] * (b[0] * c[1] - c[0] * b[1])) / 6 for a, b, c in tris)
    return abs(s) / 1000.0          # cm^3


def _ray_tri(o, d, t):
    eps = 1e-9
    a, b, c = t
    e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    h = (d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0])
    det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2]
    if -eps < det < eps:
        return None
    f = 1.0 / det
    s = (o[0] - a[0], o[1] - a[1], o[2] - a[2])
    u = f * (s[0] * h[0] + s[1] * h[1] + s[2] * h[2])
    if u < 0 or u > 1:
        return None
    q = (s[1] * e1[2] - s[2] * e1[1], s[2] * e1[0] - s[0] * e1[2], s[0] * e1[1] - s[1] * e1[0])
    vv = f * (d[0] * q[0] + d[1] * q[1] + d[2] * q[2])
    if vv < 0 or u + vv > 1:
        return None
    tt = f * (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2])
    return tt if tt > eps else None


def min_wall(tris, norms, maxt=4.0, cell=3.0):
    """Local thickness: step just inside each facet and shoot along -normal.

    The first surface the ray meets is the opposite wall, so the distance is the
    wall thickness there.  Bucketed into a spatial hash or it is O(n^2)."""
    grid = collections.defaultdict(list)
    for i, t in enumerate(tris):
        lo = [min(p[j] for p in t) for j in range(3)]
        hi = [max(p[j] for p in t) for j in range(3)]
        for cx in range(int(lo[0] // cell), int(hi[0] // cell) + 1):
            for cy in range(int(lo[1] // cell), int(hi[1] // cell) + 1):
                for cz in range(int(lo[2] // cell), int(hi[2] // cell) + 1):
                    grid[(cx, cy, cz)].append(i)
    out = []
    for i, (t, n) in enumerate(zip(tris, norms, strict=True)):
        ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if ln == 0:
            continue
        n = (n[0] / ln, n[1] / ln, n[2] / ln)
        c = tuple(sum(p[j] for p in t) / 3 for j in range(3))
        d = (-n[0], -n[1], -n[2])
        o = tuple(c[j] + d[j] * 1e-4 for j in range(3))
        best, seen = None, set()
        for s in range(int(maxt / cell) + 2):
            p = tuple(o[j] + d[j] * s * cell for j in range(3))
            key = tuple(int(p[j] // cell) for j in range(3))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for j in grid.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                            if j == i or j in seen:
                                continue
                            seen.add(j)
                            hit = _ray_tri(o, d, tris[j])
                            if hit is not None and hit < maxt and (best is None or hit < best):
                                best = hit
            if best is not None and best < (s + 1) * cell:
                break
        if best is not None:
            out.append((best, c))
    return out


# ------------------------------------------------------------ openscad utils
def intersect_volume(placement, workdir):
    """mm^3 of overlap between the notched spacer and the frame."""
    src = ('use <case_polykybd_split72_lr.scad>\n'
           'use <../parts/diffuser_frame_left.scad>\n'
           f'intersection() {{ right_spacer(); {placement} diffuser_frame_left(); }}\n')
    # Must live in CASE: `use <case_polykybd_split72_lr.scad>` resolves relative
    # to the scad file, not the cwd.  Unique name so two runs cannot delete each
    # other's input.
    fd, sf = tempfile.mkstemp(prefix='_check_tmp_', suffix='.scad', dir=CASE)
    with os.fdopen(fd, 'w') as fh:
        fh.write(src)
    # Its own output file per call.  Sharing one path across the three
    # placements means a failed export silently re-reads the PREVIOUS
    # placement's mesh and reports its volume as this one's clearance.
    ofd, of = tempfile.mkstemp(prefix='x_', suffix='.stl', dir=workdir)
    os.close(ofd)
    os.remove(of)                    # openscad writes it; absence is the signal
    try:
        r = subprocess.run(['openscad', '-o', of, '--export-format', 'asciistl', sf],
                           capture_output=True, text=True, cwd=CASE, timeout=900)
        out = r.stderr + r.stdout
        # Order matters: openscad exits 1 for an EMPTY result and 1 for a syntax
        # error alike (verified), so the marker has to be tested before the code.
        if 'Current top level object is empty' in out:
            return 0.0
        if r.returncode != 0:
            raise RuntimeError(f'openscad exited {r.returncode}:\n{out[-800:]}')
        if not os.path.exists(of) or os.path.getsize(of) == 0:
            raise RuntimeError(f'openscad produced nothing:\n{out[-800:]}')
        tris, _ = load_stl(of)
        return volume(tris) * 1000.0
    finally:
        try:
            os.remove(sf)
        except FileNotFoundError:
            pass


# -------------------------------------------------------------------- checks
def revision_zone(side):
    """Where the revision is engraved, so wall checks can exclude it.

    The engraved glyphs are SURFACE RELIEF, not walls: the gaps between letter
    strokes are ~0.2 mm in plan, but there is a full (web_t - depth) of solid
    web continuous underneath every one of them.  A ray-cast thickness measure
    cannot tell the two apart, so the zone is excluded here and the residual
    web under it is asserted separately."""
    p = os.path.join(PARTS, f'diffuser_frame_{side}.scad')
    with open(p) as fh:
        src = fh.read()
    wt = re.search(r'^web_t\s*=\s*([\d.]+)', src, re.M)
    m = re.search(r'translate\(\[(-?[\d.]+), (-?[\d.]+)\]\) square\(\[([\d.]+), ([\d.]+)\]'
                  r', center = true\);\s*// pad for the revision', src)
    d = re.search(r'_revision\(\).*?linear_extrude\(([\d.]+)\)', src, re.S)
    if not (wt and m and d):
        return None
    web_t = float(wt.group(1))
    cx, cy, w, h = (float(m.group(i)) for i in range(1, 5))
    depth = float(d.group(1))
    return dict(x=(cx - w / 2, cx + w / 2), y=(cy - h / 2, cy + h / 2),
                z=(-web_t, -web_t + depth), depth=depth, web_t=web_t)


def check_meshes():
    print('\nmesh integrity and wall thickness')
    for side in ('left', 'right'):
        p = os.path.join(PARTS, f'diffuser_frame_{side}.stl')
        if not os.path.exists(p):
            check(False, f'{side}: STL present')
            continue
        tris, norms = load_stl(p)
        nm = watertight(tris)
        check(nm == 0, f'{side}: watertight',
              f'{len(tris)} facets, {volume(tris):.3f} cm3'
              + (f', {nm} bad edges' if nm else ''))

        zone = revision_zone(side)
        check(zone is not None, f'{side}: revision zone found in the scad source',
              '' if zone else 'min wall below would measure the engraving as a wall')
        def in_zone(c):
            return zone and all(zone[k][0] - 0.05 <= c[i] <= zone[k][1] + 0.05
                                for i, k in enumerate('xyz'))

        res = min_wall(tris, norms)
        struct = [(d, c) for d, c in res if not in_zone(c)]
        mn = min(d for d, _ in struct)
        thin = [(d, c) for d, c in struct if d < MIN_WALL]
        ok = check(not thin, f'{side}: min wall >= {MIN_WALL} mm (excl. engraving)',
                   f'measured {mn:.3f} mm over {len(struct)} facets')
        if not ok:
            for d, c in sorted(thin)[:5]:
                print(f'          {d:.3f} mm at ({c[0]:+8.2f}, {c[1]:+8.2f}, {c[2]:+6.2f})')
            below = [d for d, _ in thin if d < VENDOR_FLOOR]
            if below:
                print(f'          {len(below)} of those are under the '
                      f'{VENDOR_FLOOR} mm the print service allows')
        if zone:
            left = zone['web_t'] - zone['depth']
            check(left >= VENDOR_FLOOR, f'{side}: web under the engraving',
                  f'{left:.2f} mm continuous ({zone["web_t"]:.2f} web - '
                  f'{zone["depth"]:.2f} engraved)')


def check_mirror():
    print('\nleft/right symmetry (one spacer must serve both halves)')
    ps = [os.path.join(PARTS, f'diffuser_frame_{s}.stl') for s in ('left', 'right')]
    if not all(map(os.path.exists, ps)):
        return check(False, 'both STLs present')
    a, _ = load_stl(ps[0])
    b, _ = load_stl(ps[1])
    # The engraved side letter is deliberately NOT mirrored -- "L r1.1" and
    # "R r1.1" are different glyphs -- so facet counts legitimately differ and
    # comparing them is wrong.  Compare what must match: volume, and the
    # x-mirrored bounding box.
    va, vb = volume(a), volume(b)
    check(abs(va - vb) < 5e-3, 'volumes match', f'{va:.3f} vs {vb:.3f} cm3')
    def bb(t, mirror_x):
        s = (-1 if mirror_x else 1, 1, 1)          # x only -- the halves mirror in x
        return [tuple(sorted((min(s[i] * p[i] for tr in t for p in tr),
                              max(s[i] * p[i] for tr in t for p in tr))))
                for i in range(3)]
    ba, bx = bb(a, False), bb(b, True)
    worst = max(abs(u - v) for pa, pb in zip(ba, bx) for u, v in zip(pa, pb))
    check(worst < 0.01, 'bounding boxes mirror', f'worst corner differs by {worst:.4f} mm')


def check_plate_trap():
    """The cap must stay outside the plug hole all the way round, or the frame
    drops back out of the plate once slid home."""
    print('\nplate trap (cap overhang past the d=5 plug)')
    with open(os.path.join(PARTS, 'diffuser.scad')) as fh:
        src = fh.read()

    missing = []

    def g(n):
        """A renamed constant must FAIL the check, not raise AttributeError."""
        m = re.search(rf'^{n}\s*=\s*([\d.]+)', src, re.M)
        if not m:
            missing.append(n)
            return 0.0
        return float(m.group(1))

    W = g('cutout_diameter') + g('cap_overlap') * 2       # cap circle diameter
    R, PR = W / 2, g('cutout_diameter') / 2
    CH = W / 2 - 2.25 - g('cap_overlap')                  # chord, from the clip square
    trim, ang = g('cap_trim'), math.radians(g('cap_trim_angle'))
    if missing:
        return check(False, 'cap overhangs the plug everywhere',
                     'cannot read ' + ', '.join(missing) + ' from diffuser.scad')

    def in_cap(x, y):
        if y < CH or x * x + y * y > R * R:
            return False
        for s in (1, -1):                                 # the two leaning trim cuts
            if (x - s * trim) * (s * math.cos(ang)) + (y - CH) * (-math.sin(ang)) > 0:
                return False
        return True

    worst, wx = 1e9, None
    for i in range(1, 1800):                              # bisect the boundary per bearing
        ux, uy = math.cos(math.pi * i / 1800.0), math.sin(math.pi * i / 1800.0)
        lo = next((t for t in (r/200 for r in range(1, 201)) if in_cap(ux*t*R, uy*t*R)), None)
        if lo is None:                          # bearing never enters the cap
            continue
        lo, hi = lo * R, R
        for _ in range(50):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if in_cap(ux * mid, uy * mid) else (lo, mid)
        if lo < 1e-6:
            continue
        if lo - PR < worst:
            worst, wx = lo - PR, (ux * lo, uy * lo)
    if wx is None:
        # Reachable exactly when a diffuser.scad edit leaves no cap above the
        # chord -- e.g. a smaller cap_overlap or a larger cap_trim.  That is the
        # change this check exists to catch, so it must FAIL, not crash.
        check(False, 'cap overhangs the plug everywhere',
              'no cap boundary found -- check cap_overlap / cap_trim in diffuser.scad')
    else:
        check(worst > 0.05, 'cap overhangs the plug everywhere',
              f'worst {worst:+.3f} mm at ({wx[0]:+.2f}, {wx[1]:+.2f})')


def check_spacer(workdir):
    print('\nspacer clearance (notched on both faces, so check both flips)')
    for name, placement in (
            ('as fitted', f'translate([{FRAME_XY[0]},{FRAME_XY[1]},{SPACER_Z[0]}])'),
            ('spacer flipped',
             f'mirror([0,0,1]) translate([{FRAME_XY[0]},{FRAME_XY[1]},{SPACER_Z[1]}])')):
        v = intersect_volume(placement, workdir)
        check(v <= COLLISION_EPS, f'no collision, {name}',
              f'{v:.3f} mm3 overlap (tolerance {COLLISION_EPS} mm3)')
    # positive control: displace the frame and the same test must SEE a collision
    v = intersect_volume(
        f'translate([{FRAME_XY[0]},{FRAME_XY[1]},{SPACER_Z[0] - 2}])', workdir)
    check(v > COLLISION_EPS * 100, 'control: a 2 mm displacement is detected',
          f'{v:.1f} mm3 overlap')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quick', action='store_true',
                    help='skip the checks that shell out to openscad')
    a = ap.parse_args()

    print('Checking the one-piece LED diffuser frame')
    # A gating script reports FAIL; it does not hand back a traceback.  Anything
    # raised here (unparseable STL, openscad missing or hung) becomes a failure
    # line naming the stage, and still exits non-zero.
    for name, fn in (('mesh checks', check_meshes),
                     ('symmetry', check_mirror),
                     ('plate trap', check_plate_trap)):
        try:
            fn()
        except Exception as exc:                      # noqa: BLE001 - report, don't crash
            check(False, f'{name} could not run', f'{type(exc).__name__}: {exc}')
    if a.quick:
        print('\nspacer clearance    SKIPPED (--quick)')
    else:
        try:
            with tempfile.TemporaryDirectory() as wd:
                check_spacer(wd)
        except Exception as exc:                      # noqa: BLE001
            check(False, 'spacer clearance could not run',
                  f'{type(exc).__name__}: {exc}')

    print()
    if FAILURES:
        print(f'{len(FAILURES)} check(s) FAILED: ' + '; '.join(FAILURES))
        return 1
    print('all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
