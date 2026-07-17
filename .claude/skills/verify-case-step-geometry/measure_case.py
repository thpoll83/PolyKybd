#!/usr/bin/env python3
"""Measure a built metal-case STEP feature — skin/wall thickness, hole span, or
screw-hole break-out — with hard numbers instead of eyeballing a render.

Run from case/step/ (so `import case_model` and the .step files resolve):
    measure_case.py skin  X Y                 # solid Z-spans of a +Z ray through (X,Y)
    measure_case.py hole  X Y                 # same, framed as bore + remaining solid
    measure_case.py screw [I]                 # break-out fill % for SCREW_HOLES[I] (all if omitted)

skin/hole: adjacent Z-hit pairs are solid spans (global frame). A recess floors low,
so the TOP span is the skin (e.g. [17.30, 18.50] => 1.20 mm). '[]' = outside footprint.

screw: ⚠️ holes are drilled in the WEDGE-FLATTENED frame (perpendicular to the tilted
bottom), so break-out MUST be measured there — this mode FLATTENS the part (same
flatten() as plate_svg.py), then fills a Ø2.2 (r=1.1) thread envelope of height
SCREW_HOLE_DEPTH over each SCREW_HOLES[I] along +Z. ~1.0 = buried; low = breaks out.
"""
import sys, os
from build123d import import_step, Cylinder, Location, Pos
from OCP.gp import gp_Pnt, gp_Dir, gp_Lin
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

sys.path.insert(0, os.getcwd())   # run from case/step/ so `import case_model`/`plate_svg` resolve
STEP = os.environ.get("CASE_STEP", "metal-case-right.step")
LEDGE_ZFLAT = 0.64   # flattened-frame ledge/plate-seat level (holes engage upward from here)


def zhits(part_w, x, y):
    it = BRepIntCurveSurface_Inter()
    it.Init(part_w, gp_Lin(gp_Pnt(x, y, -50), gp_Dir(0, 0, 1)), 1e-7)
    zs = []
    while it.More():
        zs.append(it.Pnt().Z())          # .Z() is a METHOD — call it
        it.Next()
    return sorted(zs)


def spans(zs):
    return [(zs[i], zs[i + 1]) for i in range(0, len(zs) - 1, 2)]


def _vol(shape):
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(shape.wrapped, g); return g.Mass()


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    mode = a[0]
    part = import_step(STEP)

    if mode in ("skin", "hole"):
        x, y = float(a[1]), float(a[2])
        zs = zhits(part.wrapped, x, y)
        print(f"{STEP}  ({x},{y})  z-hits: {['%.2f' % z for z in zs]}")
        for lo, hi in spans(zs):
            print(f"    solid {lo:.2f}..{hi:.2f}  = {hi - lo:.2f} mm")
        if mode == "skin" and spans(zs):
            lo, hi = spans(zs)[-1]
            print(f"  -> TOP-skin span = {hi - lo:.2f} mm")

    elif mode == "screw":
        # Holes are drilled in the wedge-flattened frame -> flatten before measuring.
        # The STEP already has the pilot bore subtracted, so measure the ANNULAR WALL
        # between the bore (SCREW_HOLE_D) and the Ø2.2 thread envelope: fraction of that
        # tube that is solid. ~1.0 = the thread is fully surrounded; low = it breaks out.
        import case_model as cm
        from plate_svg import flatten
        pf = flatten(part)
        h = cm.SCREW_HOLE_DEPTH
        r_env, r_bore = 1.1, cm.SCREW_HOLE_D / 2.0     # Ø2.2 thread env, Ø1.6 pilot bore
        zc = LEDGE_ZFLAT + h / 2.0                      # engage upward from the ledge seat
        idxs = [int(a[1])] if len(a) > 1 else range(len(cm.SCREW_HOLES))
        for i in idxs:
            x, y = cm.SCREW_HOLES[i]
            env = Cylinder(radius=r_env, height=h).moved(Location(Pos(x, y, zc)))
            bore = Cylinder(radius=r_bore, height=h + 2).moved(Location(Pos(x, y, zc)))
            tube = env - bore                          # the annular wall the thread cuts into
            vt = _vol(tube)
            frac = _vol(tube & pf) / vt if vt else 0.0
            verdict = "BURIED ✓" if frac > 0.97 else ("marginal" if frac > 0.9 else "BREAKS OUT ✗")
            print(f"screw #{i+1} ({x:.1f},{y:.1f}) flat  wall Ø{2*r_bore:.1f}->Ø{2*r_env:.1f} × {h}"
                  f"  -> solid {frac:.2f}  {verdict}")

    else:
        print(__doc__); sys.exit(2)


if __name__ == "__main__":
    main()
