"""
Clean B-Rep reproduction of the PolyKybd Split72 *metal* case
(OpenSCAD case_polykybd_split72_metal.scad -> build123d / OpenCASCADE).

Only the ACTIVE geometry of right_side_modular() is reproduced (the large
commented-out FDM block is not part of the metal case).  hull()->loft,
offset(r=)->real 2D offsets with arc joints (true cylinder corners).
"""
import contextlib, io, math
import numpy as np
from build123d import *

# ---- parameters (from the SCAD header) ----------------------------------
CASE_H   = 17.5
WALL     = 1.5
FLOOR    = 2.0
CLEAR    = 0.15
PCB_EDGE_H = 9.5
X_SHIFT  = 5.0          # main(): translate([5,0,0]) right_case()

# ---- bottom-plate rabbet (POST-PROCESSING feature, NOT in the .scad) -----
# The reference parts/metal-case-*.step adds, around the wedge-cut bottom opening,
# a rabbet that seats a bottom plate: the outer wall extends LIP_DROP below the
# wedge plane (the "small extrusion perpendicular to the cut-off") and an inner
# ledge sits RABBET_UP above it (the "cut-out rim"), giving a LIP_DROP+RABBET_UP
# (~2 mm) pocket for the plate.  Measured from the reference (mine frame): wedge
# bottom -6.21, lip bottom -7.19, ledge -5.1.  All parametric — edit freely.
WITH_BOTTOM_RABBET = True
LIP_DROP  = 1.0         # how far the outer lip drops below the wedge plane
RABBET_UP = 1.0         # how far the inner ledge is recessed above the wedge plane
LIP_W     = 4.0         # width of the outer lip band

SVG = lambda n: "../" + n

# ---- SVG helpers ---------------------------------------------------------
def _wires(fn):
    with contextlib.redirect_stderr(io.StringIO()):
        return import_svg(SVG(fn)).wires()

def _outer_wire(fn):
    return max(_wires(fn), key=lambda w: (lambda b: b.size.X * b.size.Y)(w.bounding_box()))

def centered_face(fn):
    """OpenSCAD import(center=true): outer wire -> face, recentre on its bbox."""
    f = make_face(_outer_wire(fn))
    b = f.bounding_box()
    return f.moved(Location((-(b.min.X + b.max.X) / 2, -(b.min.Y + b.max.Y) / 2, 0)))

def centered_faces_all(fn):
    """All wires -> faces, recentred by the COMBINED bbox (multi-hole svgs)."""
    ws = _wires(fn)
    mnx = mny = 1e9; mxx = mxy = -1e9
    for w in ws:
        b = w.bounding_box()
        mnx = min(mnx, b.min.X); mny = min(mny, b.min.Y)
        mxx = max(mxx, b.max.X); mxy = max(mxy, b.max.Y)
    cx = (mnx + mxx) / 2; cy = (mny + mxy) / 2
    faces = []
    for w in ws:
        try:
            faces.append(make_face(w).moved(Location((-cx, -cy, 0))))
        except Exception:
            pass
    return faces

def raw_faces_all(fn):
    """import(...) without center: all wires -> faces in file coords."""
    faces = []
    for w in _wires(fn):
        try:
            faces.append(make_face(w))
        except Exception:
            pass
    return faces

# ---- 2D convex hull of a face's vertices (Andrew monotone chain) ---------
def convex_hull_face(face, grow=0.0):
    pts = sorted({(round(v.X, 4), round(v.Y, 4)) for v in face.vertices()})
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    hull = lo[:-1] + up[:-1]
    poly = make_face(Polyline(*[(x, y, 0) for x, y in hull], close=True))
    return offset(poly, amount=grow, kind=Kind.ARC) if grow else poly

def _cut_batched(part, solids, loc, batch=16):
    """Subtract many small solids in batches to keep peak memory low (112 key prisms)."""
    import gc
    for i in range(0, len(solids), batch):
        part = part - Compound(solids[i:i + batch]).moved(loc)
        gc.collect()
    return part

# ---- pcb_shape (rounded outline plate) -----------------------------------
def pcb_shape_face(extra_radius=0.0):
    """SCAD pcb_shape(): offset(-2) then offset(radius+2) on the centred outline."""
    radius = WALL + CLEAR + extra_radius
    f = centered_face("poly_kb_wave_right2-OUTLINE.svg")
    return offset(offset(f, amount=-2.0, kind=Kind.ARC), amount=radius + 2.0, kind=Kind.ARC)

def pcb_shape_convex(extra_radius=0.0):
    """CONVEX version of pcb_shape: OpenSCAD hull() convexifies, so the outer shell
    (SCAD `hull(...)`) is the convex hull of the outline, rounded. Convex-hull the
    outline first, then apply the same offset(-2)/offset(radius+2) rounding."""
    radius = WALL + CLEAR + extra_radius
    hull = convex_hull_face(centered_face("poly_kb_wave_right2-OUTLINE.svg"))
    return offset(offset(hull, amount=-2.0, kind=Kind.ARC), amount=radius + 2.0, kind=Kind.ARC)

# ==========================================================================
def build_right():
    outline_c = centered_face("poly_kb_wave_right2-OUTLINE.svg")

    # ---- 1. outer shell : hull(camfer_top @ 17.5..18.5, bottom scaled 1.08 @ -5.94)
    #  SCAD `hull(...)` is a CONVEX hull -> the outer shell is the CONVEX hull of the
    #  outline (concavities like the front wave are filled). Using the concave outline
    #  here (plain loft) let the convex inner-hollow pocket poke through the wall in the
    #  front concavity = a hole. So the sections are convex (pcb_shape_convex).
    #  pcb_shape_camfer_top: quarter-round rim, radius 1.65 -> 2.65 as z 18.5 -> 17.5;
    #  reproduce as a 3-section loft + rounded rim edges.
    s_bot = scale(pcb_shape_convex(0.0), by=1.08).moved(Location((0, 0, -6.21)))  # (-5.5-0.25)*1.08
    s_mid = pcb_shape_convex(1.0).moved(Location((0, 0, CASE_H)))         # r 2.65 @ 17.5
    s_cap = pcb_shape_convex(0.0).moved(Location((0, 0, CASE_H + 1.0)))   # r 1.65 @ 18.5
    with BuildPart() as shell:
        add(s_bot); add(s_mid); add(s_cap); loft(ruled=True)
        rim = shell.edges().filter_by(Plane.XY).group_by(Axis.Z)
        try:
            fillet(rim[-1] + rim[-2], radius=0.7)   # round cap edge + widest edge
        except Exception:
            pass
    part = shell.part

    # ---- 2. wedge cut-off : translate z=-10, rotate x=-5, cube 300 centred
    wedge = Box(300, 300, 20).rotate(Axis.X, -5).moved(Location((0, 0, -10)))
    part = part - wedge

    # ---- 3. inner hollow : convex-hull(outline offset 0.65) z -11.3..
    hoff = CLEAR + 0.5
    hull_pocket = extrude(convex_hull_face(outline_c, grow=hoff), amount=(CASE_H + 8.3 - 0.85))
    part = part - hull_pocket.moved(Location((0, 0, -10 - 1.3)))

    # ---- 4. inner border : outline offset (0.65-4) z -10..
    border = extrude(offset(outline_c, amount=(hoff - 4.0), kind=Kind.ARC), amount=(CASE_H + 8.3 - 0.85))
    part = part - border.moved(Location((0, 0, -10)))

    # ---- 5. switch cut-outs + clearance (cut-outs.svg)
    #  SCAD: translate(T) linear_extrude(h) rotate([0,180,0]) <2D>.  The rotate acts on the
    #  FLAT z=0 profile -> pure X-mirror; the extrude then goes UP.  (Rotating the solid would
    #  send it to z<0, below the case.)  So: X-mirror faces, extrude up, translate.
    cut_faces = [f.mirror(Plane.YZ) for f in centered_faces_all("cut-outs.svg")]
    T = Location((-4.215, 0.779, 0))
    clr = [extrude(offset(f, amount=1.2, kind=Kind.ARC), amount=5) for f in cut_faces]
    part = _cut_batched(part, clr, T * Location((0, 0, CASE_H + 6.3 - 1.5 - 10)))
    # extrude tall enough to clear the top plate (top rim z<=18.5); start below 0 for safety
    sw = [extrude(f.moved(Location((0, 0, -2))), amount=28) for f in cut_faces]
    part = _cut_batched(part, sw, T)

    # ---- 6. extra space around display : cube([30,69,5]) centred @ (-75,21.5,15.4)
    part = part - Box(30, 69, 5).moved(Location((-75, 21.5, 15.4)))

    # ---- 7. LED / switch / USB holes : raw file coords, translate([-92,-72,1])
    led = [extrude(offset(f, amount=0.9, kind=Kind.ARC), amount=2.20).moved(Location((0, 0, PCB_EDGE_H - 0.1 - 0.5)))
           for f in raw_faces_all("poly_kb_wave_right2-LED.svg")]
    swf = [extrude(offset(f, amount=2.5, kind=Kind.ARC), amount=3.0).moved(Location((0, 0, PCB_EDGE_H - 0.4 - 1)))
           for f in raw_faces_all("poly_kb_wave_right2-SW.svg")]
    usb = [extrude(offset(f, amount=1.1, kind=Kind.ARC), amount=8.0).moved(Location((0, 0, PCB_EDGE_H - 1.6 - 2)))
           for f in raw_faces_all("poly_kb_wave_right2-USB.svg")]
    holes = Compound(led + swf + usb).moved(Location((-92, -72, 1)))
    part = part - holes

    part = part.moved(Location((X_SHIFT, 0, 0)))   # main(): translate([5,0,0])
    if WITH_BOTTOM_RABBET:
        part = add_bottom_rabbet(part)

    # ---- 8. re-cut the switch/LED openings on the FINAL geometry.
    #  OCCT's boolean occasionally NO-OPs a cut against the complex intermediate part
    #  (the "Boolean operation unable to clean" warnings): here it silently left two
    #  keycap LED round holes (wires 9 & 95) capped at the top plate (z 17.3-18.5) while
    #  the other 34 cut through. Re-cutting the same prisms on the final part removes
    #  those caps (verified 2->0 crossings) and is idempotent for the openings already
    #  cut. Prisms are re-placed at T shifted by X_SHIFT to match the moved part.
    part = _cut_batched(part, sw, T * Location((X_SHIFT, 0, 0)))
    return part


def add_bottom_rabbet(part):
    """Add the bottom-plate rabbet (lip + inner ledge) around the wedge-cut opening.

    The lip is an EXTRUSION FROM THE CUT-OFF PLANE, perpendicular to it -- not a
    vertical silhouette that would stick out past the tapered wall. We rotate the part
    so the slanted wedge bottom is horizontal, build the outer-wall band from the
    **clean convex** outer footprint (scale(1.08) of pcb_shape_convex, i.e. the loft's
    bottom silhouette), extrude that band DOWN by LIP_DROP (the lip, perpendicular to
    the cut plane) and recess the inner region so the ledge sits RABBET_UP above the
    plane, then rotate back.

    Clean convex tools are essential: offsetting the boolean-messy extracted bottom
    wire leaves free edges, and the STEP then exports as an OPEN SHELL (0 solids) whose
    bottom faces read inward in a viewer. The convex footprint booleans cleanly into a
    single closed solid. Returns the part unchanged on any failure.
    """
    try:
        # locate the wedge bottom face (lowest downward-facing face) -> flatten rotation
        best = None
        for f in part.faces():
            n = _safe_normal(f)
            if n is not None and n.Z < -0.3:
                z = f.bounding_box().min.Z
                if best is None or z < best[0]:
                    best = (z, f, n)
        if best is None:
            return part
        _, _, bn = best
        t = np.array([0, 0, -1.0]); n = np.array([bn.X, bn.Y, bn.Z]); n = n / np.linalg.norm(n)
        axv = np.cross(n, t); s = np.linalg.norm(axv)
        ang = math.degrees(math.atan2(s, n @ t))
        axv = axv / s if s > 1e-9 else np.array([1.0, 0, 0])
        Rax = Axis((0, 0, 0), tuple(axv))
        p = part.rotate(Rax, ang)                    # flatten the wedge plane -> horizontal
        z0 = min(f.bounding_box().min.Z for f in p.faces()
                 if (_safe_normal(f) is not None and _safe_normal(f).Z < -0.3))

        # clean convex outer footprint at the cut plane (= the loft bottom silhouette)
        outer = scale(pcb_shape_convex(0.0), by=1.08).moved(Location((X_SHIFT, 0, z0)))
        inner = offset(outer, amount=-LIP_W, kind=Kind.ARC)
        band = outer - inner
        lip = extrude(band, amount=-LIP_DROP)                        # lip: from the plane, down
        # recess the inner region: from below the lip up to the ledge (z0 + RABBET_UP)
        rab = extrude(inner.moved(Location((0, 0, -LIP_DROP - 0.05))),
                      amount=LIP_DROP + RABBET_UP + 0.05)
        p = (p + lip) - rab
        return p.rotate(Rax, -ang)                    # rotate back
    except Exception as e:
        print("add_bottom_rabbet skipped:", e)
        return part


def _safe_normal(f):
    try:
        return f.normal_at()
    except Exception:
        return None

def build_left():
    return build_right().mirror(Plane.YZ)

if __name__ == "__main__":
    import time
    t = time.time()
    p = build_right()
    print("RIGHT built in %.1fs" % (time.time() - t))
    print("bbox:", p.bounding_box())
    print("volume:", round(p.volume, 1))
    print("faces:", len(p.faces()))
