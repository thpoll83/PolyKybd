"""The PolyKybd keycap stem as a clean B-Rep solid (build123d / OpenCASCADE).

A line-for-line re-authoring of `mx_stem()` in `../keycap_stem.scad`, per
[`../../openscad-to-step-recipe-stems.md`](../../openscad-to-step-recipe-stems.md).
Every constant below is read from that file and kept under its SCAD name, so the two
stay diffable.  Nothing here is approximated: the tapered extrudes become real solids,
the MX cross fillet a real arc, the stem a real cylinder.

Why not STL -> STEP: OpenSCAD has no B-Rep kernel, so its export is a facet soup with
loose stitching -- and the feature that decides whether the keyboard works is a
~1.1 mm MX cross, which is not a datum anyone can cut to as facets.

Frame: origin at the bottom of the MX stem, stem axis +Z, so the part sits on the
plane it is moulded against.  Same frame as the SCAD module.
"""
import math
import numpy as np
from build123d import (Axis, BuildSketch, Circle, Cylinder, Cone, Face, Plane, Polyline,
                       Pos, Rectangle, Rot, Text, Wire, Align, FontStyle, extrude,
                       fillet, loft)

import font
from hull3d import hull_solid

# --------------------------------------------------------------------------------
# Parameters -- names and values from ../keycap_stem.scad (lines 2-28)
# --------------------------------------------------------------------------------
# ⚠️ DELIBERATELY NOT `keycap_stem.scad:2`, which stays "α".  The moulded part differs
# from the 3D-printed prototypes -- different process, different tolerances, different
# tooling -- so it carries its own revision letter and a part can be told apart by
# looking at it.  This is the one constant here that is NOT a mirror of the .scad; every
# other one keeps its .scad name and value so the two stay diffable.
#
# It also settles a legibility problem: Noto Sans draws U+03B1 single-storey and
# TAILLESS, so the printed set's "α" reads as a Latin "a" at stamp size (DejaVu's has the
# usual right-hand tail; Noto's does not).  "β" has no such twin.
REVISION                = "β"
PROFILE                 = "S"          # the profile token the printed plates engrave
# Gap between the two glyphs.  Wide on purpose -- the printed plates pad the profile
# token to 5 characters so the profile sits at one corner of the face and the revision at
# the other, and this keeps that.  ⚠️ Ceiling is 5.63 mm: the pocket ceiling is only
# 11.30 mm wide, so gap + 4.07 mm of glyph + 2 x STAMP_MARGIN has to fit inside it.
STAMP_GAP               = 5.2
STAMP_MARGIN            = 0.8          # min clear from the stamp to the edge of its face
TEXT_FONT               = "Noto"       # asked for by name in the .scad; see font.py
TEXT_SIZE               = 3.0          # OpenSCAD points -- see TEXT_EM below
# ⚠️ `text(size=)` in OpenSCAD is a POINT size rendered at 100 DPI (it calls
# FT_Set_Char_Size(..., 100, 100)), while build123d's `font_size` is the em in
# millimetres.  So the same nominal 3 comes out 100/72 = 1.389x larger in OpenSCAD --
# cap height 3.058 mm against 2.202 mm, measured both ways.  Without the conversion the
# moulded stamp is a third smaller than the one on the printed plates, which looks like
# a font-weight problem and is not.
TEXT_EM                 = TEXT_SIZE * 100 / 72
TEXT_HEIGHT             = 0.3

SURFACE_OFFSET          = 0.001             # SCAD's boolean-cleanliness nudge; kept
STEM_X, STEM_Y          = 15.5, 15.475
STEM_HEIGHT             = 5.65
STEM_TOP_BOTTOM_RATIO   = 0.85

# The three click tabs (keycap_stem.scad:88-100).  Named here because the drawing
# dimensions them: they are what makes the transparent cap click on, not a print aid.
CLICK_TAB_L             = 3.0               # along the edge it sits on
CLICK_TAB_W             = 0.4               # across it, so 0.20 stands proud
CLICK_TAB_H             = 0.3               # up from the moulding face, z = 0
CLICK_TAB_PROUD         = CLICK_TAB_W / 2

INSIDE_X, INSIDE_Y      = 13.3, 13.3
INSIDE_HEIGHT           = 3.0

MX_CYLINDER             = 5.5
MX_CROSS                = 4.35
MX_CROSS_WIDTH          = 1.4               # tolerance-critical -- see the drawing
MX_CROSS_FILLET         = 0.3

DISP_X, DISP_Y          = 12.2, 12.1
DISP_HEIGHT             = 1.1
DISP_Y_CENTER_OFFSET    = 1.345
CABLE_STEM_X            = 9.0
CABLE_STEM_Y            = 2.12
CABLE_THICKNESS         = 0.5

# The two variants a moulder is quoting.  Both are the `S` (stepped) profile,
# variants/keycap_stem_revAlpha_1U*_S_10p.scad -> angle -7, extra_len 1.5.
#
# NOTE the 1.25U plate calls mx_stem(u_size = 1.22), NOT 1.25 -- u_size feeds
# `(u_size - 1) * 2 * 5`, i.e. it is a HALF-WIDTH-EXTENSION dial (1.22 -> the body
# grows 2 x 2.2 mm to 19.9 mm), not the keycap unit count.  The .scad is the
# authority; the recipe's 1.25 was read as a unit size.
VARIANTS = {
    "S_1U":   dict(u_size=1.00, angle=-7.0, extra_len=1.5, label="S 1U", qty=58),
    "S_1U25": dict(u_size=1.22, angle=-7.0, extra_len=1.5, label="S 1.25U", qty=14),
}


def revision_codepoint():
    """Name the revision character explicitly, for the drawing.

    A Greek letter cut into steel from a glyph outline alone is a chance to cut the wrong
    character -- and the mark exists precisely to be read -- so the sheet spells the
    codepoint out rather than relying on the shape.  That is not hypothetical: the
    printed set's "α" is drawn single-storey and tailless by Noto and reads as a Latin
    "a" (see REVISION above).
    """
    import unicodedata
    c = REVISION
    if len(c) != 1:
        return f'"{c}"'
    return f"U+{ord(c):04X} {unicodedata.name(c).title()}"


def default_text():
    """The stamp the printed plates carry: `str("S    ", revision)`.

    Five characters wide, so the profile sits at one corner of the face and the
    revision at the other -- see the keycap-stem section of ../../../CLAUDE.md.  Keep
    the padding if a profile is added.
    """
    return f"{PROFILE:<5}{REVISION}"


# --------------------------------------------------------------------------------
# Primitives -- the SCAD operations that have exact build123d counterparts
# --------------------------------------------------------------------------------
def taper_box(sx, sy, h, scale, z0=0.0):
    """`linear_extrude(height=h, scale=s) square([sx,sy], center=true)`.

    `scale` may be a scalar or an (x, y) pair -- OpenSCAD accepts both, and the FFC
    cut-outs and the cross chamfers use the vector form.

    Built as the convex hull of the eight corners rather than as a `loft`, because the
    two give the SAME solid with DIFFERENT surfaces: the sides of a tapered box are
    planar (corresponding edges stay parallel, so each is a trapezoid), but OCCT's
    ThruSections returns them as degree-1 B-spline patches -- geometrically exact,
    typed as free-form.  Hulling the corners yields real `Geom_Plane` faces, which is
    what the fabricator's validator and the section views below want to see.
    """
    sxs, sys = (scale, scale) if np.isscalar(scale) else scale
    pts = []
    for z, kx, ky in ((z0, 1.0, 1.0), (z0 + h, sxs, sys)):
        for ex in (-1, 1):
            for ey in (-1, 1):
                pts.append([ex * sx / 2 * kx, ey * sy / 2 * ky, z])
    return hull_solid(pts)


def cross_profile():
    """The MX cross opening: `offset(r = -MX_CROSS_FILLET)` of the raw plus, plus the
    four relief circles (keycap_stem.scad:163-177).

    Eroding a plus by a disc of radius f translates each edge inward by f and rounds
    the four REFLEX corners on an arc of radius f centred on the original corner --
    which is identical to a plus of (MX_CROSS - f) x (MX_CROSS_WIDTH - f) filleted
    r = f at those corners.  Stated that way it is a real arc instead of the segment
    fan `offset()` would leave, and the numbers are the ones to dimension:

        arm length  MX_CROSS       - MX_CROSS_FILLET = 4.05 mm   (NOT 4.35)
        arm width   MX_CROSS_WIDTH - MX_CROSS_FILLET = 1.10 mm   (NOT 1.40)

    The 4.35 / 1.4 constants are the pre-erosion plus, so quoting them as the cross
    size overstates the opening by 0.3 mm on both.
    """
    length = MX_CROSS - MX_CROSS_FILLET
    width = MX_CROSS_WIDTH - MX_CROSS_FILLET
    hw = width / 2

    with BuildSketch() as plus:
        Rectangle(length, width)
        Rectangle(width, length)
        reflex = plus.vertices().filter_by(
            lambda v: abs(abs(v.X) - hw) < 1e-9 and abs(abs(v.Y) - hw) < 1e-9)
        fillet(reflex, radius=MX_CROSS_FILLET)

    face = plus.sketch
    r = (MX_CROSS_WIDTH - MX_CROSS_FILLET) * 1.1 / 2
    for dx, dy in ((-MX_CROSS / 3, 0), (MX_CROSS / 3, 0),
                   (0, -MX_CROSS / 3), (0, MX_CROSS / 3)):
        face = face + Pos(dx, dy) * Circle(r)
    return face


# --------------------------------------------------------------------------------
# The part
# --------------------------------------------------------------------------------
def cross_cut(h, taper, z0=0.0):
    """The tapered MX cross opening as a solid -- keycap_stem.scad:162-178.

    Assembled from four exact pieces rather than lofted as one profile, and the reason
    is which SURFACES come out:  the eight arm flats are the datum the switch cross
    actually bears on, and lofting the whole plus-plus-circles outline turns every one
    of them into a free-form patch.  Built as a union of two hulled bars, the flats are
    real planes; only the fillet and relief walls stay free-form, which they must be --
    tapering about the origin moves an off-centre arc's centre as well as its radius,
    so those walls are oblique cones and no analytic OCCT surface fits them.

    `taper` scales about the ORIGIN, matching `linear_extrude(scale=)` applied to the
    whole profile (not to each sub-shape about its own centre).
    """
    length = MX_CROSS - MX_CROSS_FILLET
    width = MX_CROSS_WIDTH - MX_CROSS_FILLET
    part = taper_box(length, width, h, taper, z0)
    part += taper_box(width, length, h, taper, z0)

    # the four reflex-corner fillets: the square notch corner minus the arc disc
    f = MX_CROSS_FILLET
    hw = width / 2
    patch = (Pos(hw + f / 2, hw + f / 2) * Rectangle(f, f)) - (Pos(hw + f, hw + f) * Circle(f))
    for a in (0, 90, 180, 270):
        part += _taper_profile(Rot(0, 0, a) * patch, h, taper, z0)

    # the four relief circles (:174-177)
    r = (MX_CROSS_WIDTH - MX_CROSS_FILLET) * 1.1 / 2
    for dx, dy in ((-MX_CROSS / 3, 0), (MX_CROSS / 3, 0),
                   (0, -MX_CROSS / 3), (0, MX_CROSS / 3)):
        part += _taper_profile(Pos(dx, dy) * Circle(r), h, taper, z0)
    return part


def _taper_profile(face, h, taper, z0):
    """Loft a 2-D face to a copy scaled about the origin -- `linear_extrude(scale=)`.

    ⚠️ `about=(0, 0, 0)` is load-bearing.  `Shape.scale()` defaults to scaling about
    the SHAPE'S OWN LOCATION, so an off-centre sub-shape keeps its position and only
    shrinks -- while `linear_extrude(scale=)` scales the whole profile about the
    extrusion axis, moving it inward too.  Left at the default this builds a perfectly
    valid solid whose cross tapers at a third of the intended rate (span 4.074 instead
    of 3.987 at the far end, +0.5 % volume); nothing errors, and only measuring the
    section against the analytic value shows it.
    """
    return loft([Pos(0, 0, z0) * face,
                 Pos(0, 0, z0 + h) * face.scale(taper, about=(0, 0, 0))])


def outer_hull(u_size, click_tabs=True):
    """`hull()` of the two tapered bodies and the three click tabs (:83-100).

    OpenSCAD's hull is CONVEX, and every member here is a polyhedron, so the result is
    a polyhedron -- reproduced exactly by hulling the vertices (see hull3d.py).

    ⚠️ **The three 0.40 x 3.00 x 0.30 mm tabs on +Y and +/-X are a FUNCTIONAL feature,
    not a print aid.**  They stand 0.20 mm proud of the body and are what makes the clear
    keycap click on properly, so `click_tabs=False` exists only to isolate them in a
    comparison -- it is not an option for a shipped part.  (An earlier reading of this
    file had them down as a sprued-plate artefact and the drawing invited the moulder to
    delete them; both were wrong.)
    """
    dx = (u_size - 1) * 2 * 5
    s = STEM_TOP_BOTTOM_RATIO
    pts = []
    for sx in (dx, -dx):                                   # the two hulled bodies
        for z, k in ((0.0, 1.0), (STEM_HEIGHT, s)):
            for ex in (-1, 1):
                for ey in (-1, 1):
                    pts.append([sx + ex * STEM_X / 2 * k, ey * STEM_Y / 2 * k, z])
    if click_tabs:
        L, W = CLICK_TAB_L, CLICK_TAB_W
        tabs = [((0.0, STEM_Y / 2), (L, W)),
                ((STEM_X / 2 + dx, 0.0), (W, L)),
                ((-STEM_X / 2 - dx, 0.0), (W, L))]
        for (cx, cy), (tx, ty) in tabs:
            for z in (0.0, CLICK_TAB_H):
                for ex in (-1, 1):
                    for ey in (-1, 1):
                        pts.append([cx + ex * tx / 2, cy + ey * ty / 2, z])
    return hull_solid(pts)


def cap_body(u_size, click_tabs=True, engrave=True, txt=None):
    """The hollow cap, in its own (untilted) frame -- keycap_stem.scad:80-152."""
    dx = (u_size - 1) * 2 * 5
    s = STEM_TOP_BOTTOM_RATIO
    part = outer_hull(u_size, click_tabs)

    # inside pockets (:101-113) -- two under the hulled bodies, one wider-but-steeper
    # in the middle "for the bulky switches"
    part -= Pos(dx, 0) * taper_box(INSIDE_X, INSIDE_Y, INSIDE_HEIGHT, s, -SURFACE_OFFSET)
    part -= Pos(-dx, 0) * taper_box(INSIDE_X, INSIDE_Y, INSIDE_HEIGHT, s, -SURFACE_OFFSET)
    part -= taper_box((INSIDE_X + INSIDE_X + STEM_X) / 3, (INSIDE_Y + STEM_Y) / 2,
                      INSIDE_HEIGHT, s * 0.85, -SURFACE_OFFSET)

    # display seat + its cable relief (:114-122).  Both are scale = 1, i.e. ZERO
    # DRAFT -- called out on the drawing.
    z_disp = STEM_HEIGHT - DISP_HEIGHT + SURFACE_OFFSET
    part -= Pos(0, DISP_Y_CENTER_OFFSET) * taper_box(DISP_X, DISP_Y, DISP_HEIGHT, 1.0, z_disp)
    y_cable = DISP_Y_CENTER_OFFSET - DISP_Y / 2 - CABLE_STEM_Y / 2 + SURFACE_OFFSET
    part -= Pos(0, y_cable) * taper_box(CABLE_STEM_X, CABLE_STEM_Y, DISP_HEIGHT, 1.0, z_disp)

    # FFC exit (:124-136).  The first is `rotate([0,180,0])` in the SCAD, so it flares
    # DOWNWARD: 0.5 mm at the top face opening out to 3.5 mm at the base.
    y_ffc = (DISP_Y_CENTER_OFFSET - DISP_Y / 2 - CABLE_STEM_Y - CABLE_THICKNESS / 2
             + SURFACE_OFFSET * 2)
    h_ffc = STEM_HEIGHT + SURFACE_OFFSET * 2
    part -= Pos(0, y_ffc) * taper_box(
        CABLE_STEM_X, CABLE_THICKNESS * 7, h_ffc, (1, 1 / 7),
        STEM_HEIGHT + SURFACE_OFFSET - h_ffc)
    y_ffc2 = DISP_Y_CENTER_OFFSET - DISP_Y / 2 - CABLE_STEM_Y - 0.05
    part -= Pos(0, y_ffc2) * taper_box(
        CABLE_STEM_X, 0.2, 1.0, (1, 10),
        STEM_HEIGHT - DISP_HEIGHT + SURFACE_OFFSET * 2 - 1)
    part -= Pos(0, -CABLE_STEM_X / 2) * taper_box(
        CABLE_STEM_X, CABLE_STEM_X, INSIDE_HEIGHT, 1.0, -SURFACE_OFFSET)

    if engrave:
        part -= _engraving(part, txt)
    return part


def _glyph(ch):
    """One glyph with its BASELINE at y = 0 and its left edge at x = 0."""
    from fontTools import ttLib
    from fontTools.pens.boundsPen import BoundsPen
    f = ttLib.TTFont(font.bold_path())
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    pen = BoundsPen(gs)
    gs[cmap[ord(ch)]].draw(pen)
    x0, y0, x1, y1 = pen.bounds
    k = TEXT_EM / f["head"].unitsPerEm
    shape = Text(ch, TEXT_EM, font_path=font.bold_path(), font_style=FontStyle.BOLD,
                 align=(Align.MIN, Align.MIN))
    # align=(MIN, MIN) puts the glyph's yMin at 0; shift by yMin to land the baseline there
    return Pos(0, y0 * k) * shape, (x1 - x0) * k


def stamp_sketch():
    """The stamp: revision then profile, side by side on a COMMON BASELINE.

    Two glyphs placed explicitly rather than one string, for three reasons the string
    could not give: the gap between them is a millimetre value (`STAMP_GAP`) instead of
    however wide the font draws a run of spaces; the order is chosen (β leads, S
    follows); and both sit on one baseline, so β's descender hangs below S rather than
    dragging the pair's bounding box down and pushing the whole stamp off-centre.

    ⚠️ β is 4.19 mm tall against S's 3.06 -- it has both an ascender and a descender.
    That is what broke the SCAD's hard-coded stamp positions when the moulded revision
    moved from α: they were tuned for a 3.06 mm glyph set, and at 4.19 the stamp reached
    the edge of the face it is cut into (0.21 mm clear on the seat floor, and flush with
    the edge on the pocket ceiling).  Hence `place_stamp` below.
    """
    lead, tail = REVISION, PROFILE
    a, wa = _glyph(lead)
    b, wb = _glyph(tail)
    return (Pos(-STAMP_GAP / 2 - wa, 0) * a) + (Pos(STAMP_GAP / 2, 0) * b)


def stamp_face(body, z):
    """The largest planar face of `body` lying at height `z` -- what the stamp cuts into."""
    best = None
    for f in body.faces():
        b = f.bounding_box()
        if abs(b.min.Z - z) < 0.02 and abs(b.max.Z - z) < 0.02:
            if best is None or f.area > best.area:
                best = f
    if best is None:
        raise RuntimeError(f"no planar face at z={z}")
    return best


def place_stamp(sketch, face, nominal_y):
    """Centre the stamp in `face` in x, and clamp it in y to keep STAMP_MARGIN clear.

    Derived from the REAL face rather than hard-coded, so it re-solves itself if a
    pocket changes or the revision character grows a descender.  ⚠️ The face is not the
    rectangle the parameters suggest: the display seat breaks out through the tapered
    wall at +Y, so its floor ends at y +6.86, not at the seat's nominal +7.40.
    """
    b = sketch.bounding_box()
    fb = face.bounding_box()
    cx = (fb.min.X + fb.max.X) / 2 - (b.min.X + b.max.X) / 2
    lo = fb.min.Y + STAMP_MARGIN - b.min.Y
    hi = fb.max.Y - STAMP_MARGIN - b.max.Y
    if lo > hi:
        raise ValueError(f"stamp {b.size.Y:.2f} mm tall does not fit the "
                         f"{fb.size.Y:.2f} mm face with {STAMP_MARGIN} mm margins")
    cy = min(max(nominal_y - (b.min.Y + b.max.Y) / 2, lo), hi)
    return Pos(cx, cy) * sketch


def _engraving(body, txt=None):
    """The two stamps (:138-151): one in the display-seat floor, one under the pocket.

    ⚠️ Both are 0.30 mm deep with **zero draft**, and on a moulded part they are steel:
    the seat stamp stands proud of the core, the pocket stamp likewise.  At 0.30 mm that
    normally releases, but it is called out on the drawing rather than left to be
    discovered.

    ⚠️ **The font is pinned to a file** (`font.bold_path()`), not named.  OCCT does not
    read fontconfig, so `font="Noto"` -- what the .scad asks for -- falls back to
    FreeSans with a warning nobody reads, and the family name finds the VARIABLE file's
    default instance rather than Bold.  The three spellings give three different glyphs
    (areas 4.068 / 2.330 / 3.563 mm² for this string), and the tool is cut from whichever
    one the build happened to produce.  See font.py.
    """
    sk = stamp_sketch() if txt is None else _text_sketch(txt)
    z_top = STEM_HEIGHT - DISP_HEIGHT
    top = place_stamp(sk, stamp_face(body, z_top), DISP_Y / 2 - TEXT_SIZE / 2)
    under = place_stamp(sk, stamp_face(body, INSIDE_HEIGHT), -DISP_Y / 3)
    return (Pos(0, 0, z_top - TEXT_HEIGHT + SURFACE_OFFSET * 2)
            * extrude(top, amount=TEXT_HEIGHT)) + \
           (Pos(0, 0, INSIDE_HEIGHT + TEXT_HEIGHT - 0.01) * Rot(180, 0, 0)
            * extrude(under, amount=TEXT_HEIGHT))


def stamp_report(u_size=1.00):
    """Measured clearance from each stamp to the edge of the face it is cut into.

    Reported rather than assumed: the numbers this replaced were 0.21 mm on the seat
    floor and 0.00 mm on the pocket ceiling, i.e. the stamp was ON the edge.
    """
    body = cap_body(u_size, engrave=False)
    sk = stamp_sketch()
    out = []
    for label, z, nominal in (("display-seat floor", STEM_HEIGHT - DISP_HEIGHT,
                               DISP_Y / 2 - TEXT_SIZE / 2),
                              ("pocket ceiling", INSIDE_HEIGHT, -DISP_Y / 3)):
        face = stamp_face(body, z)
        placed = place_stamp(sk, face, nominal)
        b, fb = placed.bounding_box(), face.bounding_box()
        out.append(dict(where=label, size=(b.size.X, b.size.Y),
                        clear=dict(x_min=b.min.X - fb.min.X, x_max=fb.max.X - b.max.X,
                                   y_min=b.min.Y - fb.min.Y, y_max=fb.max.Y - b.max.Y)))
    return out


def _text_sketch(txt):
    """Escape hatch: an arbitrary string, for comparing against the .scad's own stamp."""
    return Text(txt, TEXT_EM, font_path=font.bold_path(), font_style=FontStyle.BOLD,
                align=(Align.CENTER, Align.CENTER))


def mx_stem(u_size, angle=0.0, extra_len=0.0, click_tabs=True, engrave=True, txt=None):
    """`mx_stem()` -- the whole part.  keycap_stem.scad:74-189."""
    cap = Pos(0, 0, extra_len) * Rot(angle, 0, 0) * cap_body(u_size, click_tabs, engrave, txt)

    # the MX stem itself (:153-160): a true cylinder + the flange cone, not 128 facets
    h_cyl = STEM_HEIGHT - DISP_HEIGHT - 1 + extra_len
    stem = Pos(0, 0, h_cyl / 2) * Cylinder(MX_CYLINDER / 2, h_cyl)
    stem += Pos(0, 0, 2.5 + extra_len + 0.7) * Cone(MX_CYLINDER / 2, MX_CYLINDER / 2 + 1.2, 1.4)

    part = cap + stem

    # the cross, tapered 0.97 over 2 x STEM_HEIGHT (:162-178)
    part -= cross_cut(STEM_HEIGHT * 2, 0.97, -SURFACE_OFFSET)

    # the lead-in chamfer at the bottom of the cross (:179-187)
    f = MX_CROSS_FILLET
    sl = MX_CROSS / (MX_CROSS + 2 * f) - 0.011
    sw = MX_CROSS_WIDTH / (MX_CROSS_WIDTH + 2 * f) - 0.07
    part -= taper_box(MX_CROSS + f, MX_CROSS_WIDTH + f, f, (sl, sw), -SURFACE_OFFSET)
    part -= taper_box(MX_CROSS_WIDTH + f, MX_CROSS + f, f, (sw, sl), -SURFACE_OFFSET)
    return part


def build(name, **overrides):
    """Build one entry of VARIANTS by name."""
    cfg = dict(VARIANTS[name])
    for k in ("label", "qty"):
        cfg.pop(k)
    cfg.update(overrides)
    return mx_stem(**cfg)


# --------------------------------------------------------------------------------
# Draft angles -- computed, because the numbers get guessed wrong by hand
# --------------------------------------------------------------------------------
def ffc_flare_deg():
    """Half-angle of the FFC exit's flare, per side.

    The exit is a `taper_box` 7 x CABLE_THICKNESS wide at the moulding face scaling to
    1/7 of that at the top of the boss, so it opens downward -- that is the chamfer the
    flex cable runs out through, and it has no number anywhere in the .scad.
    """
    wide, narrow = CABLE_THICKNESS * 7, CABLE_THICKNESS
    return math.degrees(math.atan((wide - narrow) / 2 / STEM_HEIGHT))


def draft_angles():
    """Per-feature draft, as (feature, half-width mm, taper scale, depth mm, degrees).

    A `linear_extrude(scale=s)` over height h moves a wall that starts `w` from the
    extrusion axis inward by `w * (1 - s)`, so the draft is `atan(w * (1 - s) / h)` --
    it depends on HOW FAR OUT the wall is, which is why one number cannot describe a
    tapered profile and why the cross flats (0.55 mm out) and the cross arm tips
    (2.055 mm out) differ by 4x on the same extrude.
    """
    import math

    def row(name, w, scale, h):
        return (name, w, scale, h, math.degrees(math.atan2(w * (1 - scale), h)))

    s = STEM_TOP_BOTTOM_RATIO
    cross_l = (MX_CROSS - MX_CROSS_FILLET) / 2
    cross_w = (MX_CROSS_WIDTH - MX_CROSS_FILLET) / 2
    return [
        row("outer body X", STEM_X / 2, s, STEM_HEIGHT),
        row("outer body Y", STEM_Y / 2, s, STEM_HEIGHT),
        row("inside pocket", INSIDE_X / 2, s, INSIDE_HEIGHT),
        row("centre pocket", (INSIDE_X + INSIDE_X + STEM_X) / 6, s * 0.85, INSIDE_HEIGHT),
        row("cross arm flat", cross_w, 0.97, 2 * STEM_HEIGHT),
        row("cross arm tip", cross_l, 0.97, 2 * STEM_HEIGHT),
        row("display seat", DISP_X / 2, 1.0, DISP_HEIGHT),
        row("cable relief", CABLE_STEM_X / 2, 1.0, DISP_HEIGHT),
    ]
