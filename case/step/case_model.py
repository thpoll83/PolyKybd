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
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BOPAlgo import BOPAlgo_GlueEnum
from OCP.TopTools import TopTools_ListOfShape


def _glue_fuse(a, b):
    """Fuse two solids that share an EXACTLY coincident face (glue mode). A plain
    boolean fuse of coincident faces leaves free edges -> open shell; glue merges
    them. Used to weld the bottom lip prism (whose top face IS the part's bottom
    face) without the 0.5 mm overlap that would make the constant prism protrude
    past the tapering wall."""
    args = TopTools_ListOfShape(); args.Append(a.wrapped)
    tools = TopTools_ListOfShape(); tools.Append(b.wrapped)
    fu = BRepAlgoAPI_Fuse(); fu.SetArguments(args); fu.SetTools(tools)
    fu.SetGlue(BOPAlgo_GlueEnum.BOPAlgo_GlueShift); fu.Build()
    return Part(fu.Shape())

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

# ---- USB inner-wall chamfer (POST-PROCESSING, not in the .scad) ----------
# A 45 deg lead-in on the INTERIOR face of the wall around each USB window, so
# the connector/cable enters cleanly.  Modelled as a subtractive funnel (a boolean
# cut is robust to the internal ledge the window crosses, unlike an edge chamfer).
# The two windows are fixed by the committed SVGs (measured from the built solid,
# mine frame, right side): USB1 = the side window in the left/inner wall (normal
# +X); USB0 = the window in the back-left wall (normal -Y).
WITH_USB_CHAMFER = True
USB_CHAMFER = 3.0       # 45 deg lead-in depth/width on the inner face

# ---- interior wall-meets-floor chamfer (POST-PROCESSING, not in the .scad) ----
# A 45 deg chamfer along the interior seam where the inner wall meets the interior
# floor (the top-plate underside, z=13.65).  That corner is CONCAVE, so it is done
# the clean way the user asked for: apply the chamfer to the NEGATIVE VOLUME (the
# inner-hollow pocket) BEFORE the boolean subtraction -- chamfering the pocket's top
# edge leaves a 45 deg fillet-of-material transition that lands perfectly on the
# wall/floor corner after the cut.
#   NOTE: the interior ledge between the inner wall and the next pocket (the SCAD
#   "border") is only ~4 mm wide, so a 3 mm chamfer consumes it and degenerates the
#   boolean (verified: clean at <=2, broken at >=2.5).  2 mm is the clean maximum here.
WITH_WALLFLOOR_CHAMFER = True
WALLFLOOR_CHAMFER = 2.0

# ---- embossed branding on the convex-hull front-bezel flat top (not in .scad) --
# The SCAD `branding()` engraves "PolyKybd" (Arial Bold Italic, size 12, 0.35 deep)
# on the FDM case BOTTOM.  The metal case has no such bottom face, so we place the
# same engraving on the flat top area the CONVEX HULL created in front of the thumb
# cluster (the extra bezel the hull fills in vs the concave outline).  Engraved to
# match the SCAD (difference()); flip WITH_BRANDING/sign of depth for raised text.
WITH_BRANDING = True
BRAND_LINES  = ("Poly", "Kybd")   # two staggered lines (Kybd sits lower+right), logo-style
BRAND_SIZE   = 7.0      # smaller than the SCAD size-12 single line (top band is narrower)
BRAND_DEPTH  = 0.35     # SCAD text_height
BRAND_X      = 12.0     # centre of the block (mine frame, right side) - toward case centre
BRAND_Y      = -47.0
BRAND_STAG_X = 3.0      # 2nd line shifted +X (right) relative to the 1st
BRAND_STAG_Y = 3.6      # half the vertical gap: line1 up +STAG_Y, line2 down -STAG_Y
BRAND_TOP_Z  = 18.5     # flat top plateau z in the bezel region
BRAND_FONT   = "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"

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

def _chamfered_pocket(face, height, amt):
    """Extruded pocket (negative volume) whose top `amt` is tapered inward by `amt`
    -- i.e. a 45 deg chamfer applied to the pocket's TOP edge.  Subtracting it leaves
    a clean 45 deg gusset at the concave interior wall/floor corner (the "apply the
    chamfer to the negative volume" approach).  Built as a loft (robust) rather than a
    build123d edge chamfer, which fails on the arc-cornered pocket outline.  Returns a
    Compound {main prism, top frustum} to subtract as one."""
    main = extrude(face, amount=height - amt)
    lo = face.moved(Location((0, 0, height - amt)))
    hi = offset(face, amount=-amt, kind=Kind.ARC).moved(Location((0, 0, height)))
    return Compound([main, loft([lo, hi])])


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
def build_right(with_branding=True):
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
    hull_face = convex_hull_face(outline_c, grow=hoff)
    pocket_h = CASE_H + 8.3 - 0.85
    # wall-meets-floor chamfer: taper the pocket's TOP edge (the negative volume) so
    # the concave inner wall/floor (z13.65) corner gets a clean 45 deg transition
    # after the cut -- the "apply the chamfer to the negative volume" approach.
    if WITH_WALLFLOOR_CHAMFER:
        hull_pocket = _chamfered_pocket(hull_face, pocket_h, WALLFLOOR_CHAMFER)
    else:
        hull_pocket = extrude(hull_face, amount=pocket_h)
    part = part - hull_pocket.moved(Location((0, 0, -10 - 1.3)))

    # ---- 4. inner border : outline offset (0.65-4) z -10..
    #  Same wall-floor chamfer on THIS negative too (the border pocket that makes the
    #  central region thinner): taper its top edge so its step corner is chamfered.
    border_face = offset(outline_c, amount=(hoff - 4.0), kind=Kind.ARC)
    if WITH_WALLFLOOR_CHAMFER:
        border = _chamfered_pocket(border_face, pocket_h, WALLFLOOR_CHAMFER)
    else:
        border = extrude(border_face, amount=pocket_h)
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

    # ---- 9. USB inner chamfer + branding (post-processing, see params) --------
    if WITH_USB_CHAMFER:
        part = add_usb_chamfer(part)
    if WITH_BRANDING and with_branding:
        part = add_branding(part)
    return part


def _usb_bottom_bevel(axis, sign, face_pos, v_bottom, C, uax, u0, u1):
    """A 45 deg lead-in on ONLY the BOTTOM edge of a USB window -- the edge toward the
    open bottom of the case, where nothing else is in the way (the top/sides hit the
    interior ceiling step, so we leave them square).  A triangular prism along the
    window bottom edge: at the inner wall surface the opening drops `C` below the
    window bottom, tapering back to the window bottom `C` deep into the wall.

    axis: wall-normal axis ('x'/'y'); sign: interior direction along it (+/-1);
    face_pos: the interior wall-surface coord on that axis; v_bottom: the window bottom
    z; uax/u0/u1: the window's long edge axis and span."""
    idx = {'x': 0, 'y': 1, 'z': 2}
    def pt(a_val, z_val):
        p = [0.0, 0.0, 0.0]; p[idx[axis]] = a_val; p[idx['z']] = z_val; p[idx[uax]] = u0
        return tuple(p)
    tri = make_face(Polyline(pt(face_pos, v_bottom),            # window bottom-inner corner
                             pt(face_pos, v_bottom - C),        # dropped down the inner face
                             pt(face_pos - sign * C, v_bottom),  # back to bottom, C into wall
                             close=True))
    d = [0.0, 0.0, 0.0]; d[idx[uax]] = 1.0
    return extrude(tri, amount=(u1 - u0), dir=tuple(d))


def add_usb_chamfer(part):
    """Bottom-only USB lead-ins (toward the open bottom) -- see _usb_bottom_bevel.
    No clip needed: below each window is clear wall down to the open bottom."""
    try:
        C = USB_CHAMFER
        b1 = _usb_bottom_bevel('x', +1, -86.7, 6.9, C, 'y', 1.0, 13.7)      # side wall
        b0 = _usb_bottom_bevel('y', -1, 61.1, 6.9, C, 'x', -71.1, -58.5)    # back wall
        return part - b1 - b0
    except Exception as e:
        print("add_usb_chamfer skipped:", e)
        return part


def add_branding(part, x=None, y=None):
    """Engrave the two-line staggered PolyKybd logo on the convex-hull bezel top.

    "Poly" sits up/left, "Kybd" down/right (BRAND_STAG_X/Y) at BRAND_SIZE, engraved
    BRAND_DEPTH deep into the flat top area the convex hull fills in front of the
    thumb cluster (the concavity the raw outline had) - like the SCAD `branding()`
    bottom text (difference), relocated to the top.  x/y override the block centre
    (build_left brands the mirrored part at -x, with fresh (un-mirrored) text so the
    logo reads correctly on the left half too)."""
    try:
        cx = BRAND_X if x is None else x
        cy = BRAND_Y if y is None else y
        placed = [(BRAND_LINES[0], cx - BRAND_STAG_X, cy + BRAND_STAG_Y),
                  (BRAND_LINES[1], cx + BRAND_STAG_X, cy - BRAND_STAG_Y)]
        prisms = []
        for word, wx, wy in placed:
            with contextlib.redirect_stderr(io.StringIO()):
                txt = Text(word, font_size=BRAND_SIZE, font_path=BRAND_FONT,
                           align=(Align.CENTER, Align.CENTER))
            # text prism straddling the top plateau, subtracted BRAND_DEPTH deep
            prisms.append(extrude(txt, amount=BRAND_DEPTH + 0.15)
                          .moved(Location((wx, wy, BRAND_TOP_Z - BRAND_DEPTH))))
        return part - Compound(prisms)
    except Exception as e:
        print("add_branding skipped:", e)
        return part


def add_bottom_rabbet(part):
    """Add the bottom-plate rabbet (lip + inner ledge) around the wedge-cut opening.

    The lip must be a PERPENDICULAR extrusion of the cut-off AREA -- take the wedge-plane
    section's outline (a single, constant cross-section) and extrude it straight along the
    plane normal. Two wrong ways it went before:
      * the `scale(1.08)` loft-bottom silhouette (the *straight-cut* section) extruded at
        the wedge angle -> too wide on the tapered/back side, lip sticks out; and
      * translating a thin *slice* of the wall down -> the slice carries the wall's own
        taper, so the lip face tapers ("starts smaller then expands"), not perpendicular.
    Right way: flatten the wedge plane to horizontal, grab the real wedge-plane bottom
    face `bf` (the actual section, following the taper at that plane), and extrude THAT
    face as a constant prism straight down from z0 (glue-fused so the coincident top face
    welds without an overlap that would make the prism protrude past the tapering wall).
    Constant section + straight extrude = a true perpendicular lip that hugs the wall.
    Then recess the inner region up so the ledge sits RABBET_UP above the plane, using a
    UNIFORM inward offset of the real section (so the retained lip band is the same width
    on every side -- scale(1.08) scales about the origin and makes it non-uniform).

    (Never offset the boolean-messy extracted bottom wire -> free edges/open shell; a
    clean convex polygon of bf's own vertices offsets fine.) Returns part on any failure.
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

        # the real wedge-plane bottom face (flattened, lowest downward face)
        bf = None
        for f in p.faces():
            nn = _safe_normal(f)
            if nn is not None and nn.Z < -0.3:
                if bf is None or f.bounding_box().min.Z < bf.bounding_box().min.Z:
                    bf = f
        z0 = bf.bounding_box().min.Z

        # LIP: extrude the section face as a CONSTANT prism straight down (perpendicular),
        # from z0 EXACTLY (no overlap -> no protrusion where a wider constant prism would
        # otherwise stick out past the tapering wall). Its top face is the part's own
        # bottom face, so weld with a glue-fuse (a plain fuse of coincident faces opens
        # the shell). Force dir=-Z: bf's normal points down, so a negative amount would
        # extrude UP into the part.
        lip = extrude(bf, amount=LIP_DROP, dir=(0, 0, -1))
        p = _glue_fuse(p, lip)
        # LEDGE: recess the inner region up. Footprint = a UNIFORM inward offset of the
        # real wedge-plane section (clean convex polygon of bf's own vertices), so the
        # retained lip band is the same width on every side. (scale(1.08) scales about
        # the origin, pushing the far short-side ends out more -> non-uniform band.)
        inner = offset(convex_hull_face(bf), amount=-LIP_W,
                       kind=Kind.ARC).moved(Location((0, 0, z0)))
        rab = extrude(inner.moved(Location((0, 0, -LIP_DROP - 0.05))),
                      amount=LIP_DROP + RABBET_UP + 0.05)
        p = p - rab
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
    # mirror the UN-branded base, then engrave so the logo reads correctly (not
    # backwards) on the left half; -BRAND_X puts it on the mirrored bezel.
    base = build_right(with_branding=False).mirror(Plane.YZ)
    return add_branding(base, x=-BRAND_X, y=BRAND_Y) if WITH_BRANDING else base

if __name__ == "__main__":
    import time
    t = time.time()
    p = build_right()
    print("RIGHT built in %.1fs" % (time.time() - t))
    print("bbox:", p.bounding_box())
    print("volume:", round(p.volume, 1))
    print("faces:", len(p.faces()))
