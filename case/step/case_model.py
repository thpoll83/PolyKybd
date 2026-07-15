"""
Clean B-Rep reproduction of the PolyKybd Split72 *metal* case
(OpenSCAD case_polykybd_split72_metal.scad -> build123d / OpenCASCADE).

Only the ACTIVE geometry of right_side_modular() is reproduced (the large
commented-out FDM block is not part of the metal case).  hull()->loft,
offset(r=)->real 2D offsets with arc joints (true cylinder corners).
"""
import contextlib, io
from build123d import *

# ---- parameters (from the SCAD header) ----------------------------------
CASE_H   = 17.5
WALL     = 1.5
FLOOR    = 2.0
CLEAR    = 0.15
PCB_EDGE_H = 9.5
X_SHIFT  = 5.0          # main(): translate([5,0,0]) right_case()

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

# ==========================================================================
def build_right():
    outline_c = centered_face("poly_kb_wave_right2-OUTLINE.svg")

    # ---- 1. outer shell : hull(camfer_top @ 17.5..18.5, bottom scaled 1.08 @ -5.94)
    #  SCAD pcb_shape_camfer_top: quarter-round rim, radius 1.65 -> 2.65 as z 18.5 -> 17.5.
    #  Reproduce as a 3-section loft: bottom(-5.94) -> widest(17.5,r2.65) -> cap(18.5,r1.65),
    #  then round the two rim circle edges so the rim is a true torus, not a chamfer.
    s_bot = scale(pcb_shape_face(0.0), by=1.08).moved(Location((0, 0, -6.21)))  # (-5.5-0.25)*1.08
    s_mid = pcb_shape_face(1.0).moved(Location((0, 0, CASE_H)))          # r 2.65 @ 17.5
    s_cap = pcb_shape_face(0.0).moved(Location((0, 0, CASE_H + 1.0)))    # r 1.65 @ 18.5
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

    return part.moved(Location((X_SHIFT, 0, 0)))   # main(): translate([5,0,0])

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
