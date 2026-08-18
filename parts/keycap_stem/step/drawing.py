"""A dimensioned technical drawing of each keycap stem variant, on an A4 sheet.

    python drawing.py       # -> ../../export/keycap_stem/stem_S_1U{,25}_drawing.svg

⚠️ **The drawing governs; the STEP conveys shape.**  That is why both exist: a solid
model carries no tolerances, so a toolmaker handed only a STEP cuts to the model and the
tolerance question resurfaces at first article.  The block here states a general
tolerance and tightens only what decides fit -- the MX cross, and the interface to the
off-the-shelf transparent cap.

Every view is projected from the SAME solid `build.py` exports, so the drawing cannot
drift from the STEP.  Dimension VALUES are written explicitly because the views are at
2:1 and 10:1 and a measured-off-the-sheet label would read the scaled length.

⚠️ **Geometry comes from build123d; the SVG is written here by hand, and the text is
real `<text>`.**  build123d has a drafting module (`TechnicalDrawing`, `ExtensionLine`)
and it was used first -- but every label goes through OCCT's `Compound.make_text`, and
once a sheet carries the frame plus the projections, the section and the dimensions,
make_text **segfaults**.  Deterministically, on the 14th label, with ~500 MB resident
and 14 GB free, and none of the ingredients crashes on its own; only the combination
does.  Emitting the annotation as SVG text instead removes OCCT from that path
entirely, and pays twice over: the file is far smaller, and the dimensions are
selectable and searchable in the fabricator's viewer instead of being outlines.
`../../case/step/plate_svg.py` writes its SVG the same way.
"""
import argparse, math, os
from datetime import date

from build123d import Compound, GeomType, Plane, Pos, Rectangle, Rot
from build123d.exporters import Drawing

import stem_model as sm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "export", "keycap_stem")

SCALE_MAIN, SCALE_DETAIL, SCALE_ISO = 2.0, 10.0, 1.6
REVISION = "A"
GENERAL_TOL = 0.10

PAGE_W, PAGE_H = 297.0, 210.0        # A4 landscape
FRAME_X, FRAME_Y = 133.5, 89.0       # drawing frame, centred on the origin
TITLE_W, TITLE_H = 110.0, 32.0

FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"
CHAR_W = 0.58                        # advance / em, ample for placement decisions

W_THICK, W_THIN, W_HAIR = 0.4, 0.18, 0.13
ARROW_L, ARROW_W = 2.0, 0.7


# ------------------------------------------------------------------- svg plumbing
class Sheet:
    """An A4 sheet in millimetres, origin at the centre, +Y up."""

    def __init__(self):
        self.out = []

    def _x(self, x):
        return x + PAGE_W / 2

    def _y(self, y):
        return PAGE_H / 2 - y

    def line(self, a, b, w=W_THIN, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(
            f'<line x1="{self._x(a[0]):.3f}" y1="{self._y(a[1]):.3f}" '
            f'x2="{self._x(b[0]):.3f}" y2="{self._y(b[1]):.3f}" '
            f'stroke="#000" stroke-width="{w}"{d}/>')

    def path(self, pts, w=W_THIN, dash=None, close=False):
        if len(pts) < 2:
            return
        d = "M " + " L ".join(f"{self._x(x):.3f},{self._y(y):.3f}" for x, y in pts)
        if close:
            d += " Z"
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<path d="{d}" fill="none" stroke="#000" '
                        f'stroke-width="{w}"{da}/>')

    def poly(self, pts, fill="#000"):
        d = " ".join(f"{self._x(x):.3f},{self._y(y):.3f}" for x, y in pts)
        self.out.append(f'<polygon points="{d}" fill="{fill}"/>')

    def rect(self, x0, y0, x1, y1, w=W_THIN):
        self.path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w, close=True)

    def text(self, s, at, size=2.6, anchor="middle", baseline="middle", bold=False):
        s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        weight = ' font-weight="bold"' if bold else ""
        self.out.append(
            f'<text x="{self._x(at[0]):.3f}" y="{self._y(at[1]):.3f}" '
            f'font-family="{FONT}" font-size="{size}"{weight} xml:space="preserve" '
            f'text-anchor="{anchor}" dominant-baseline="{baseline}" '
            f'fill="#000">{s}</text>')

    def write(self, path):
        body = "\n".join(self.out)
        open(path, "w").write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{PAGE_W}mm" '
            f'height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}">\n'
            f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="#fff"/>\n'
            f'{body}\n</svg>\n')
        print("wrote", path)


# -------------------------------------------------------------------- projections
def _flatten(shape, seg=0.35):
    """Every edge of a 2-D shape as a polyline, in sheet millimetres.

    Straight edges keep their two endpoints; curved ones are chorded at `seg` mm ON
    THE SHEET (the shapes are scaled before they get here), so a 10:1 detail's arcs
    stay smooth without flooding the 2:1 views with points.
    """
    paths = []
    for e in shape.edges():
        if e.geom_type == GeomType.LINE:
            n = 1
        else:
            n = max(4, int(math.ceil(e.length / seg)))
        paths.append([( (e @ (i / n)).X, (e @ (i / n)).Y ) for i in range(n + 1)])
    return paths


def _bbox(shapes):
    lo, hi = [1e9, 1e9], [-1e9, -1e9]
    for s in shapes:
        if s is None or not s.edges():
            continue
        b = s.bounding_box()
        lo = [min(lo[0], b.min.X), min(lo[1], b.min.Y)]
        hi = [max(hi[0], b.max.X), max(hi[1], b.max.Y)]
    return lo, hi


def view(part, look_from, look_up=(0, 0, 1), hidden=True, scale=SCALE_MAIN, at=(0, 0)):
    """Hidden-line-removed projection, centred on its own bbox and placed at `at`.

    Visible and hidden sets are centred TOGETHER; centring them separately shifts one
    against the other and the hidden lines stop lining up with the part.
    """
    d = Drawing(part, look_from=look_from, look_up=look_up, with_hidden=hidden)
    layers = [d.visible_lines, d.hidden_lines if hidden else None]
    lo, hi = _bbox(layers)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    out = []
    for s in layers:
        out.append(None if s is None else
                   _flatten(Pos(*at) * (Pos(-cx, -cy) * s).scale(scale, about=(0, 0, 0))))
    return out


def section(part, plane, scale, at, spacing=0.6, angle=45.0):
    """Cut `part` with `plane`; return (outline polylines, hatch polylines).

    Hatch rulings are thin RECTANGLES intersected with the face, not lines: a line
    lies exactly in the face's plane and OCCT's edge-face common then returns nothing
    at all -- silently, so an empty hatch reads as "no solid here" rather than an error.
    """
    sec = plane.to_local_coords(part & plane)
    faces = sec.faces()
    outline = Compound(children=[e for f in faces for e in f.edges()])
    lo, hi = _bbox([outline])
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2

    def put(s):
        return Pos(*at) * (Pos(-cx, -cy) * s).scale(scale, about=(0, 0, 0))

    hatches = []
    for f in faces:
        b = f.bounding_box()
        fx, fy = (b.min.X + b.max.X) / 2, (b.min.Y + b.max.Y) / 2
        reach = max(b.size.X, b.size.Y) * 1.6
        for i in range(-int(reach / spacing) - 1, int(reach / spacing) + 2):
            ruling = Pos(fx, fy) * Rot(0, 0, angle) * Pos(i * spacing, 0) * \
                Rectangle(0.12, reach * 2)
            try:
                hit = f & ruling
            except Exception:
                continue
            if hit is not None and hit.faces():
                for hf in hit.faces():
                    hb = put(hf).bounding_box()
                    hatches.append([(hb.min.X, hb.min.Y), (hb.max.X, hb.max.Y)]
                                   if angle > 0 else
                                   [(hb.min.X, hb.max.Y), (hb.max.X, hb.min.Y)])
    return _flatten(put(outline)), hatches


# --------------------------------------------------------------------- annotation
def arrow(sh, tip, along, w=W_THIN):
    ux, uy = along
    n = math.hypot(ux, uy) or 1.0
    ux, uy = ux / n, uy / n
    px, py = -uy, ux
    base = (tip[0] + ux * ARROW_L, tip[1] + uy * ARROW_L)
    sh.poly([tip, (base[0] + px * ARROW_W, base[1] + py * ARROW_W),
             (base[0] - px * ARROW_W, base[1] - py * ARROW_W)])


def dim(sh, p1, p2, offset, text, size=2.4, vertical=None, gap=1.0, ext=1.5):
    """A linear dimension between two SHEET points, offset perpendicular to the run.

    Places the value outside the arrows when it will not fit between them -- the case
    build123d's `ExtensionLine` cannot handle (it produces an empty shaft and raises
    `Can't determine direction of empty Edge or Wire` several frames away).
    """
    if vertical is None:
        vertical = abs(p2[1] - p1[1]) > abs(p2[0] - p1[0])
    if vertical:
        x = (p1[0] + p2[0]) / 2 + offset
        a, b = (x, p1[1]), (x, p2[1])
        for p, q in ((p1, a), (p2, b)):
            s = math.copysign(gap, q[0] - p[0])
            sh.line((p[0] + s, p[1]), (q[0] + math.copysign(ext, offset), q[1]), W_HAIR)
        run = abs(b[1] - a[1])
    else:
        y = (p1[1] + p2[1]) / 2 + offset
        a, b = (p1[0], y), (p2[0], y)
        for p, q in ((p1, a), (p2, b)):
            s = math.copysign(gap, q[1] - p[1])
            sh.line((p[0], p[1] + s), (q[0], q[1] + math.copysign(ext, offset)), W_HAIR)
        run = abs(b[0] - a[0])

    need = len(text) * size * CHAR_W + 2 * ARROW_L
    inside = run >= need
    if inside:
        sh.line(a, b, W_THIN)
        arrow(sh, a, (b[0] - a[0], b[1] - a[1]))
        arrow(sh, b, (a[0] - b[0], a[1] - b[1]))
    else:                                   # arrows outside, pointing in
        d = 3.0
        u = ((b[0] - a[0]) / (run or 1), (b[1] - a[1]) / (run or 1))
        sh.line((a[0] - u[0] * d, a[1] - u[1] * d), (b[0] + u[0] * d, b[1] + u[1] * d),
                W_THIN)
        arrow(sh, a, (-u[0], -u[1]))
        arrow(sh, b, u)

    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    if vertical:
        sh.text(text, (mid[0] + (1.0 if offset > 0 else -1.0), mid[1]), size,
                "start" if offset > 0 else "end")
    else:
        sh.text(text, (mid[0], mid[1] + (inside and 0.9 or 0.9) + size * 0.35), size)


def leader(sh, text, tip, elbow, size=2.2, left=False):
    """A leader note -- for a feature too small to dimension between extension lines."""
    tail = (elbow[0] + (-3.5 if left else 3.5), elbow[1])
    sh.path([tip, elbow, tail], W_HAIR)
    sh.poly([(tip[0] - 0.4, tip[1]), (tip[0], tip[1] + 0.4),
             (tip[0] + 0.4, tip[1]), (tip[0], tip[1] - 0.4)])
    sh.text(text, (tail[0] + (-0.8 if left else 0.8), tail[1]), size,
            "end" if left else "start")


def frame_and_title(sh, cfg, name):
    sh.rect(-FRAME_X, -FRAME_Y, FRAME_X, FRAME_Y, W_THICK)
    x0, y0 = FRAME_X - TITLE_W, -FRAME_Y
    x1, y1 = FRAME_X, -FRAME_Y + TITLE_H
    sh.rect(x0, y0, x1, y1, W_THICK)
    sh.line((x0, y1 - 11), (x1, y1 - 11), W_THIN)
    sh.line((x0, y0 + 10), (x1, y0 + 10), W_THIN)
    sh.line((x0 + 62, y0 + 10), (x0 + 62, y1 - 11), W_THIN)

    sh.text(f"Keycap stem  {cfg['label']}", (x0 + 3, y1 - 5.5), 4.4, "start", bold=True)
    sh.text("MX mount, injection moulded", (x0 + 3, y1 - 15.5), 2.6, "start")
    sh.text("PolyTasten / PolyKybd", (x0 + 3, y1 - 19.5), 2.2, "start")
    sh.text(f"DRAWING  PK-STEM-{name.replace('_', '-')}-{REVISION}",
            (x0 + 65, y1 - 15.0), 2.4, "start")
    sh.text(f"DATE  {date.today().isoformat()}", (x0 + 65, y1 - 19.5), 2.2, "start")
    sh.text("SCALE  as noted", (x0 + 3, y0 + 5.5), 2.4, "start")
    sh.text("FIRST ANGLE (ISO 128)", (x0 + 40, y0 + 5.5), 2.4, "start")
    sh.text("UNITS  mm", (x0 + 90, y0 + 5.5), 2.4, "start")


# ---------------------------------------------------------------------- the sheet
def build_sheet(name):
    cfg = sm.VARIANTS[name]
    part = sm.build(name)
    bb = part.bounding_box()
    dxo = (cfg["u_size"] - 1) * 2 * 5
    hx, hy = sm.STEM_X / 2 + dxo, sm.STEM_Y / 2
    S, D = SCALE_MAIN, SCALE_DETAIL

    sh = Sheet()
    frame_and_title(sh, cfg, name)

    right_at, front_at, top_at = (-110.0, 62.0), (-56.0, 62.0), (-56.0, 16.0)
    sec_at, iso_at, det_at = (14.0, 62.0), (66.0, 60.0), (90.0, 12.0)

    for look, up, at, title in (
            ((1, 0, 0), (0, 0, 1), right_at, "VIEW FROM RIGHT  2:1"),
            ((0, -1, 0), (0, 0, 1), front_at, "VIEW FROM FRONT  2:1"),
            ((0, 0, 1), (0, 1, 0), top_at, "VIEW FROM ABOVE  2:1")):
        vis, hid = view(part, look, up, True, S, at)
        for p in hid:
            sh.path(p, W_HAIR, dash="1.1,0.9")
        for p in vis:
            sh.path(p, W_THICK)
        sh.text(title, (at[0], at[1] + (16 if at is not top_at else -21)), 2.8,
                bold=True)

    vis, _ = view(part, (1, -1, 0.75), hidden=False, scale=SCALE_ISO, at=iso_at)
    for p in vis:
        sh.path(p, W_THIN)
    sh.text("ISOMETRIC  1.6:1", (iso_at[0], iso_at[1] + 17), 2.8, bold=True)

    # --- section A-A, cut on the XZ plane straight through the cross --------------
    out_p, hats = section(part, Plane.XZ, S, sec_at)
    for p in hats:
        sh.path(p, W_HAIR)
    for p in out_p:
        sh.path(p, W_THICK)
    sh.text("SECTION A-A  2:1", (sec_at[0], sec_at[1] + 19), 2.8, bold=True)
    sh.text("on the cross centre-line", (sec_at[0], sec_at[1] + 15), 2.1)
    # the cutting plane, marked on the view from above
    sh.line((top_at[0] - 34, top_at[1]), (top_at[0] + 34, top_at[1]), W_THIN,
            dash="6,1.5,1.5,1.5")
    for lbl, x in (("A", -36.5), ("A", 36.5)):
        sh.text(lbl, (top_at[0] + x, top_at[1] + 4.0), 3.2, bold=True)

    # --- detail B: the cross opening at the moulding face, 10:1 ------------------
    z_det = sm.MX_CROSS_FILLET
    cross_sec = part & Plane.XY.offset(z_det)
    stem_face = min(cross_sec.faces(), key=lambda f: f.bounding_box().size.X)
    inner = [w for w in stem_face.wires()
             if w.bounding_box().size.X < sm.MX_CYLINDER]
    det = Compound(children=list(inner[0].edges())
                   + list(stem_face.outer_wire().edges()))
    lo, hi = _bbox([det])
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    for p in _flatten(Pos(*det_at) * (Pos(-cx, -cy) * det).scale(D, about=(0, 0, 0))):
        sh.path(p, W_THICK)
    sh.text("DETAIL B  10:1", (det_at[0], det_at[1] + 34), 2.8, bold=True)
    sh.text(f"cross opening at z = {z_det:.2f}, above the lead-in chamfer",
            (det_at[0], det_at[1] - 34), 2.1)
    sh.text("B", (det_at[0] - 30, det_at[1] + 34), 3.2, bold=True)
    # detail marker on the view that contains the feature
    sh.out.append(f'<circle cx="{sh._x(top_at[0])}" cy="{sh._y(top_at[1])}" '
                  f'r="7.5" fill="none" stroke="#000" stroke-width="{W_HAIR}" '
                  f'stroke-dasharray="1.5,1.2"/>')
    sh.text("B", (top_at[0] + 13.0, top_at[1] - 12.5), 3.0, bold=True)

    # --- dimensions ---------------------------------------------------------------
    def at_view(at, p, scale=S):
        return (at[0] + p[0] * scale, at[1] + p[1] * scale)

    dim(sh, at_view(top_at, (-hx, -hy)), at_view(top_at, (hx, -hy)), -13,
        f"{2 * hx:.2f}")
    dim(sh, at_view(top_at, (hx, -hy)), at_view(top_at, (hx, hy)), 12, f"{2 * hy:.3f}")
    y_seat = sm.DISP_Y_CENTER_OFFSET - sm.DISP_Y / 2
    dim(sh, at_view(top_at, (-sm.DISP_X / 2, hy)),
        at_view(top_at, (sm.DISP_X / 2, hy)), 8.0, f"{sm.DISP_X:.2f} display seat")
    dim(sh, at_view(top_at, (-sm.DISP_X / 2, y_seat)),
        at_view(top_at, (-sm.DISP_X / 2, y_seat + sm.DISP_Y)), -12, f"{sm.DISP_Y:.2f}")

    dim(sh, at_view(front_at, (-hx, 0)), at_view(front_at, (-hx, bb.max.Z)), -9,
        f"{bb.max.Z:.2f}")
    dim(sh, at_view(front_at, (-hx, 0)), at_view(front_at, (hx, 0)), -18,
        f"{2 * hx:.2f}")

    h_cyl = sm.STEM_HEIGHT - sm.DISP_HEIGHT - 1 + cfg["extra_len"]
    dim(sh, at_view(sec_at, (hx, 0)), at_view(sec_at, (hx, sm.STEM_HEIGHT)), 8,
        f"{sm.STEM_HEIGHT:.2f} cap")
    dim(sh, at_view(sec_at, (-hx, 0)), at_view(sec_at, (-hx, h_cyl)), -8,
        f"{h_cyl:.2f} stem")

    taper = 1 - 0.03 * z_det / (2 * sm.STEM_HEIGHT)
    c_len = (sm.MX_CROSS - sm.MX_CROSS_FILLET) * taper
    c_wid = (sm.MX_CROSS_WIDTH - sm.MX_CROSS_FILLET) * taper
    dim(sh, at_view(det_at, (-c_len / 2, c_wid / 2), D),
        at_view(det_at, (c_len / 2, c_wid / 2), D), 16, f"{c_len:.2f} ±0.03")
    dim(sh, at_view(det_at, (c_wid / 2, -c_len / 2), D),
        at_view(det_at, (c_wid / 2, c_len / 2), D), 18, f"{c_len:.2f} ±0.03")

    leader(sh, f"{c_wid:.2f} ±0.03 arm width",
           at_view(det_at, (-c_len / 2 + 0.4, c_wid / 2), D),
           (det_at[0] - 26, det_at[1] + 24), 2.1, True)
    leader(sh, f"R{sm.MX_CROSS_FILLET:.2f}, 4x",
           at_view(det_at, (c_wid / 2 + 0.12, c_wid / 2 + 0.12), D),
           (det_at[0] + 20, det_at[1] + 24), 2.1)
    leader(sh, "relief bulge 4x",
           at_view(det_at, (sm.MX_CROSS / 3, -c_wid / 2 - 0.16), D),
           (det_at[0] + 21, det_at[1] - 22), 2.1)
    leader(sh, f"Ø{sm.MX_CYLINDER:.2f} stem",
           at_view(det_at, (-sm.MX_CYLINDER / 2 * 0.707, -sm.MX_CYLINDER / 2 * 0.707), D),
           (det_at[0] - 24, det_at[1] - 26), 2.1, True)
    # The thinnest stem wall -- MEASURED off the section, not derived.  Two derivations
    # were tried and both were wrong, in opposite directions: the widest point of the
    # opening is neither the arm tip (2.025) nor the relief bulge (1.45 + 0.605 = 2.055)
    # but the arm tip's CORNER, hypot(2.025, 0.55) = 2.098 -- so the wall is 0.65, not
    # the 0.67 or 0.70 the two closed forms give.  Sample the wire.
    reach = max(math.hypot(v.X, v.Y)
                for e in inner[0].edges() for v in (e @ (i / 8) for i in range(9)))
    wall = sm.MX_CYLINDER / 2 - reach
    leader(sh, f"{wall:.2f} min wall, stem to cross", at_view(det_at, (-2.4, 0), D),
           (det_at[0] - 26, det_at[1] - 8), 2.1, True)
    leader(sh, "print tab, 3x (note 10)", at_view(top_at, (hx, 0)),
           (top_at[0] + 30, top_at[1] + 12), 2.1)
    leader(sh, f"display seat {sm.DISP_HEIGHT:.2f} deep, zero draft (note 7)",
           at_view(sec_at, (-hx + 1.2, sm.STEM_HEIGHT - sm.DISP_HEIGHT / 2 + 1.3)),
           (sec_at[0] - 24, sec_at[1] + 20), 2.1, True)

    # --- notes ---------------------------------------------------------------------
    dr = {n: a for n, *_, a in sm.draft_angles()}
    notes = [
        ("NOTES", True),
        (f" 1.  Dimensions in mm.  First-angle projection (ISO 128).  Scale as marked per view.", False),
        (f" 2.  General tolerance ±{GENERAL_TOL:.2f} unless stated otherwise.", False),
        (" 3.  Geometry re-authored from keycap_stem.scad in build123d.  The STEP is the shape reference;", False),
        ("       THIS DRAWING governs tolerance, material and finish.  No revision character is moulded.", False),
        (f" 4.  CRITICAL  MX cross {c_len:.2f} x {c_wid:.2f} ±0.03, R{sm.MX_CROSS_FILLET:.2f} corner fillets.  Gauge against a reference MX", False),
        ("       switch stem, not by CMM alone.  Polish the core pin to draw along the arms.", False),
        (" 5.  CRITICAL  The transparent relegendable cap is an off-the-shelf POS part, so that mating", False),
        ("       dimension is a hard datum set by a supplier we do not control.  Confirm before cutting steel.", False),
        (f" 6.  Draft, measured off the model: outer body {dr['outer body X']:.1f}°, inside pocket {dr['inside pocket']:.1f}°, centre pocket {dr['centre pocket']:.1f}°.", False),
        (f" 7.  ZERO DRAFT on the display seat ({sm.DISP_X} x {sm.DISP_Y} x {sm.DISP_HEIGHT} deep) and on its cable relief.  Shallow enough", False),
        ("       that it often releases as-is, but confirm it rather than discover it at first article.", False),
        (f" 8.  Cross draft {dr['cross arm flat']:.2f}° on the flats and {dr['cross arm tip']:.2f}° at the arm tips, opening downward -- the core pin", False),
        ("       withdraws in the correct direction, but with very little relief.", False),
        (" 9.  MATERIAL NOT FIXED.  ABS assumed: its 0.4-0.7% shrink is what protects the cross.  POM only if", False),
        ("       the stem must snap-retain, at ~2% shrink for the cross to compensate.  Shrink compensation", False),
        ("       belongs in the moulded model, not this one -- ask before applying it.", False),
        ("10.  Three 0.40 x 3.00 x 0.30 tabs stand 0.20 proud of the body (+Y and ±X).  They are a print-plate", False),
        ("       aid carried over from the 3D-printed part -- delete them for tooling unless you want them.", False),
    ]
    y = -19.0
    for i, (t, bold) in enumerate(notes):
        sh.text(t, (-131.0, y), 2.0, "start", bold=bold)
        y -= 2.0 * 1.55 if i else 3.4
    return sh


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for name in sm.VARIANTS:
        if args.only and name != args.only:
            continue
        build_sheet(name).write(os.path.join(OUT, f"stem_{name}_drawing.svg"))


if __name__ == "__main__":
    main()
