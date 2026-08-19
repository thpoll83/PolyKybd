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
    "S_1U":   dict(u_size=1.00, angle=-7.0, extra_len=1.5, label="S 1U"),
    "S_1U25": dict(u_size=1.22, angle=-7.0, extra_len=1.5, label="S 1.25U"),
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


def outer_hull(u_size, print_tabs=True):
    """`hull()` of the two tapered bodies and the three print tabs (:83-100).

    OpenSCAD's hull is CONVEX, and every member here is a polyhedron, so the result is
    a polyhedron -- reproduced exactly by hulling the vertices (see hull3d.py).

    `print_tabs` covers the three 0.4 x 3 x 0.3 mm tabs on +Y and +/-X.  They stand
    0.2 mm proud of the body and are an ADDITIVE-MANUFACTURING aid on a sprued plate,
    not a functional feature -- but they are in the source, so they are on by default
    and the moulder is asked about them in the drawing rather than being deleted here.
    """
    dx = (u_size - 1) * 2 * 5
    s = STEM_TOP_BOTTOM_RATIO
    pts = []
    for sx in (dx, -dx):                                   # the two hulled bodies
        for z, k in ((0.0, 1.0), (STEM_HEIGHT, s)):
            for ex in (-1, 1):
                for ey in (-1, 1):
                    pts.append([sx + ex * STEM_X / 2 * k, ey * STEM_Y / 2 * k, z])
    if print_tabs:
        tabs = [((0.0, STEM_Y / 2), (3.0, 0.4)),
                ((STEM_X / 2 + dx, 0.0), (0.4, 3.0)),
                ((-STEM_X / 2 - dx, 0.0), (0.4, 3.0))]
        for (cx, cy), (tx, ty) in tabs:
            for z in (0.0, 0.3):
                for ex in (-1, 1):
                    for ey in (-1, 1):
                        pts.append([cx + ex * tx / 2, cy + ey * ty / 2, z])
    return hull_solid(pts)


def cap_body(u_size, print_tabs=True, engrave=True, txt=None):
    """The hollow cap, in its own (untilted) frame -- keycap_stem.scad:80-152."""
    dx = (u_size - 1) * 2 * 5
    s = STEM_TOP_BOTTOM_RATIO
    part = outer_hull(u_size, print_tabs)

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
        part -= _engraving(txt if txt is not None else default_text())
    return part


def _engraving(txt):
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
    top = Pos(0, DISP_Y / 2 - TEXT_SIZE / 2,
              STEM_HEIGHT - DISP_HEIGHT - TEXT_HEIGHT + SURFACE_OFFSET * 2) * extrude(
        Text(txt, TEXT_EM, font_path=font.bold_path(), font_style=FontStyle.BOLD,
             align=(Align.CENTER, Align.CENTER)), amount=TEXT_HEIGHT)
    under = Pos(0, -DISP_Y / 3, INSIDE_HEIGHT + TEXT_HEIGHT - 0.01) * Rot(180, 0, 0) * extrude(
        Text(txt, TEXT_EM, font_path=font.bold_path(), font_style=FontStyle.BOLD,
             align=(Align.CENTER, Align.CENTER)), amount=TEXT_HEIGHT)
    return top + under


def mx_stem(u_size, angle=0.0, extra_len=0.0, print_tabs=True, engrave=True, txt=None):
    """`mx_stem()` -- the whole part.  keycap_stem.scad:74-189."""
    cap = Pos(0, 0, extra_len) * Rot(angle, 0, 0) * cap_body(u_size, print_tabs, engrave, txt)

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
    cfg.pop("label")
    cfg.update(overrides)
    return mx_stem(**cfg)


# --------------------------------------------------------------------------------
# Draft angles -- computed, because the numbers get guessed wrong by hand
# --------------------------------------------------------------------------------
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
