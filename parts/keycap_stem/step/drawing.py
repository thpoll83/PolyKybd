"""A dimensioned technical drawing of each keycap stem variant, on an A3 sheet.

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
import argparse, contextlib, math, os, re
from datetime import date

from build123d import Compound, GeomType, Plane, Pos, Rectangle, Rot, Vector
from build123d.exporters import Drawing

import stem_model as sm

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "export", "keycap_stem")

SCALE_MAIN, SCALE_DETAIL, SCALE_ISO = 2.0, 10.0, 2.4
SCALE_TOP = 3.0      # V3 alone: it carries the seat, the tabs, the cable
                     # relief, both cutting planes and the stamp
SCALE_SEC = 3.0      # V5 / V6 -- the sections carry the height dimensions
SCALE_STAMP = 3.0    # V8 / V9
DRAWING_REV = "A"          # revision of THIS SHEET; the part's stamp is
                           # stem_model.REVISION, and they are not the same thing
GENERAL_TOL = 0.10
MATERIAL = "ABS"

# A3 landscape.  A4 could not carry five views, three details, a section and the notes
# at a readable scale -- everything had to shrink until the 10:1 detail stopped being a
# detail.  A3 prints down to A4 at 71 % if a reader wants it that way.
PAGE_W, PAGE_H = 420.0, 297.0
FRAME_X, FRAME_Y = 200.0, 138.5      # drawing frame, centred on the origin
TITLE_W, TITLE_H = 150.0, 45.0

# ISO 128-20 line groups: thick : thin = 2 : 1.  Visible outlines thick, everything
# else (hidden, dimension, extension, leader, hatching, centre) thin or finer.
LOGO = os.path.join(HERE, "..", "..", "..", "poly_kybd", "logo.svg")

FONT = "DejaVu Sans, Arial, Helvetica, sans-serif"
CHAR_W = 0.58                        # advance / em, ample for placement decisions
NOTE_COLS = 3
NOTE_Y0 = -72.0                      # clear of V3, which at 3:1 reaches -52
NOTE_COL_W = 80.0                    # notes run in three columns this far apart
NOTE_INDENT = "     "                # continuation lines hang under the note number
# ⚠️ The wrap width has to leave room for that indent as well, or a continuation line
# runs into the next column -- which is exactly how the first two-column attempt read.
NOTE_CHARS = int(NOTE_COL_W / (2.1 * CHAR_W)) - len(NOTE_INDENT) - 3

# ISO 128-20 line groups are a fixed series (0.13 0.18 0.25 0.35 0.5 0.7 …) and you pick
# one GROUP, thick : thin = 2 : 1.  The 0.5/0.25 group was tried and reads heavy at this
# sheet's line density -- 0.35/0.18 is the group below it and is what the earlier sheets
# used.  Do not mix groups.
W_THICK, W_THIN, W_HAIR = 0.35, 0.18, 0.13
W_CUT = 0.5          # cutting-plane line, ISO 128-30: one step above the outline
ARROW_L, ARROW_W = 2.0, 0.7


# ------------------------------------------------------------------- svg plumbing
class Sheet:
    """An A3 sheet in millimetres, origin at the centre, +Y up."""

    def __init__(self):
        self.out = []
        self._groups = []
        self.texts = []          # (x0, y0, x1, y1, string) for the collision report
        self.thick = []          # visible outlines, ditto

    # -- extents ---------------------------------------------------------------
    # Every title used to sit at a hand-tuned offset from its view's centre, which is
    # a guess about how far the dimensions and leaders would reach.  The guesses were
    # wrong in both directions: V1's height dimension ran back over the part, and V2's
    # title ended up nearer the view below it than the view it names.  So the sheet
    # measures instead -- `group()` collects the extent of everything drawn inside it,
    # and the title is placed from that.  Anything added to a view later moves its
    # title automatically.
    @contextlib.contextmanager
    def group(self, box=None):
        box = [1e9, 1e9, -1e9, -1e9] if box is None else box
        self._groups.append(box)
        try:
            yield box
        finally:
            self._groups.pop()
            for g in self._groups:
                g[0], g[1] = min(g[0], box[0]), min(g[1], box[1])
                g[2], g[3] = max(g[2], box[2]), max(g[3], box[3])

    def _note(self, *pts):
        if not self._groups:
            return
        for x, y in pts:
            for g in self._groups:
                g[0], g[1] = min(g[0], x), min(g[1], y)
                g[2], g[3] = max(g[2], x), max(g[3], y)

    def _x(self, x):
        return x + PAGE_W / 2

    def _y(self, y):
        return PAGE_H / 2 - y

    def line(self, a, b, w=W_THIN, dash=None):
        self._note(a, b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(
            f'<line x1="{self._x(a[0]):.3f}" y1="{self._y(a[1]):.3f}" '
            f'x2="{self._x(b[0]):.3f}" y2="{self._y(b[1]):.3f}" '
            f'stroke="#000" stroke-width="{w}"{d}/>')

    def path(self, pts, w=W_THIN, dash=None, close=False):
        if len(pts) < 2:
            return
        self._note(*pts)
        if w >= W_THICK:
            self.thick.append(list(pts))
        d = "M " + " L ".join(f"{self._x(x):.3f},{self._y(y):.3f}" for x, y in pts)
        if close:
            d += " Z"
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<path d="{d}" fill="none" stroke="#000" '
                        f'stroke-width="{w}"{da}/>')

    def poly(self, pts, fill="#000"):
        self._note(*pts)
        d = " ".join(f"{self._x(x):.3f},{self._y(y):.3f}" for x, y in pts)
        self.out.append(f'<polygon points="{d}" fill="{fill}"/>')

    def rect(self, x0, y0, x1, y1, w=W_THIN):
        self.path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w, close=True)

    def text(self, s, at, size=2.6, anchor="middle", baseline="middle", bold=False,
             chrome=False):
        """`chrome=True` for sheet furniture that lives OUTSIDE the drawing frame -- the
        zone letters and numerals.  They are exempt from `check_inside_frame` (being
        outside is the point) and from the collision report (they sit in the margin
        band, where nothing else is drawn)."""
        w = len(s) * size * CHAR_W
        x0 = {"start": at[0], "middle": at[0] - w / 2, "end": at[0] - w}[anchor]
        if not chrome:
            self._note((x0, at[1] - size * 0.6), (x0 + w, at[1] + size * 0.6))
            self.texts.append((x0, at[1] - size * 0.52, x0 + w, at[1] + size * 0.52, s))
        s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        weight = ' font-weight="bold"' if bold else ""
        self.out.append(
            f'<text x="{self._x(at[0]):.3f}" y="{self._y(at[1]):.3f}" '
            f'font-family="{FONT}" font-size="{size}"{weight} xml:space="preserve" '
            f'text-anchor="{anchor}" dominant-baseline="{baseline}" '
            f'fill="#000">{s}</text>')

    def embed(self, svg_path, x, y, w, h):
        """Inline another SVG file, scaled into a w x h box with its top-left at (x, y).

        Nested `<svg>` with an overriding width/height/x/y, rather than parsing the
        file's own paths: the logo's squares carry a parent `<g transform=...>`, so
        lifting the `<path>` elements out of it would silently drop the transform and
        scatter them.  Keeping the root element keeps the transform and the namespaces.
        """
        try:
            src = open(svg_path, encoding="utf-8").read()
        except OSError:
            return
        self._note((x, y - h), (x + w, y))
        src = re.sub(r"<\?xml[^>]*\?>", "", src)
        src = re.sub(r"<!DOCTYPE[^>]*>", "", src)
        i = src.index("<svg")
        j = src.index(">", i)
        head = re.sub(r'\s(?:width|height|x|y)="[^"]*"', "", src[i:j])
        self.out.append(
            f'{head} x="{self._x(x):.3f}" y="{self._y(y):.3f}" '
            f'width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"'
            f'{src[j:]}')

    def centre_lines(self, at, half_x, half_y, w=W_HAIR):
        """ISO 128-24 centre line: long dash - short dash, crossing at the feature."""
        d = "5,1.2,1.2,1.2"
        self.line((at[0] - half_x, at[1]), (at[0] + half_x, at[1]), w, dash=d)
        self.line((at[0], at[1] - half_y), (at[0], at[1] + half_y), w, dash=d)

    def report_collisions(self, skip=()):
        """List labels that overlap another label or a visible outline.

        Same reasoning as `check_inside_frame`: a collision is invisible in the SVG
        source and obvious only in a render, so nothing in a code review catches it.
        This is a report rather than an exception -- a few overlaps are deliberate
        (a leader crossing a hidden line, the frame's own rules) -- but every one it
        prints was looked at.
        """
        def hit(a, b):
            return (a[0] < b[2] - 0.4 and b[0] < a[2] - 0.4
                    and a[1] < b[3] - 0.4 and b[1] < a[3] - 0.4)

        bad = []
        for i, a in enumerate(self.texts):
            if a[4] in skip:
                continue
            for b in self.texts[i + 1:]:
                if b[4] not in skip and hit(a, b):
                    bad.append(f"  text/text   {a[4][:34]!r} x {b[4][:34]!r}")
            for pl in self.thick:
                for (x1, y1), (x2, y2) in zip(pl, pl[1:]):
                    seg = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                    if hit(a, seg):
                        bad.append(f"  text/solid  {a[4][:44]!r} at "
                                   f"({a[0]:.0f}, {a[1]:.0f})")
                        break
                else:
                    continue
                break
        return bad

    def check_inside_frame(self):
        """Fail loudly on anything that runs off the drawing frame.

        A label that overshoots the border is invisible in the SVG source and obvious
        only in a render, so it survives every review that reads the code.  Reads the
        recorded text extents rather than re-parsing the emitted SVG, so `chrome=True`
        furniture (the zone letters, which live outside the frame by definition) is
        exempt for free instead of needing a second rule.
        """
        bad = [f"  {t[4][:52]!r} at ({t[0]:.1f}, {t[3]:.1f}) w={t[2] - t[0]:.1f}"
               for t in self.texts
               if t[0] < -FRAME_X + 1 or t[2] > FRAME_X - 1
               or t[1] < -FRAME_Y + 1 or t[3] > FRAME_Y - 1]
        if bad:
            raise ValueError("text outside the drawing frame:\n" + "\n".join(bad))

    def write(self, path):
        self.check_inside_frame()
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


def view(part, look_from, look_up=(0, 0, 1), hidden=True, scale=SCALE_MAIN, at=(0, 0),
         align=None):
    """Hidden-line-removed projection, plus a MAPPER from model coords onto the sheet.

    The mapper is what makes every dimension anchor on real geometry.  Without it a
    dimension has to be placed by guessing where the view's origin ended up, and the
    guess is wrong by a different amount in every view: `Drawing` projects about
    `shape.center()` -- the centre of MASS -- and the view is then re-centred on the
    projection's bounding box, so the model origin is nowhere near the middle of the
    view.  In the front view that error was 7.9 mm on the sheet, which is how the
    overall-height dimension came to start in mid-air.

    Frame, from build123d's own projector: screen-x = normalize(look_up) x
    normalize(look_from), screen-y = look_from x screen-x.
    """
    d = Drawing(part, look_from=look_from, look_up=look_up, with_hidden=hidden)
    zhat = Vector(*look_from).normalized()
    xhat = Vector(*look_up).normalized().cross(zhat)
    yhat = zhat.cross(xhat)
    if align is None:
        origin = part.center()
        layers = [d.visible_lines, d.hidden_lines if hidden else None]
        lo, hi = _bbox(layers)
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    else:
        # Overlay a SECOND shape on a view already laid out.  TWO separate re-centrings
        # have to be undone, and getting only one of them is worse than getting neither
        # -- the overlay lands plausibly, in the middle of the view, instead of visibly
        # nowhere.  `Drawing` projects about the shape's OWN centre of mass, so the
        # overlay's 2-D coordinates are already offset by the difference between the two
        # centres; and the first call then shifted by its own (cx, cy).  Correct both.
        origin, cx, cy = align
        delta = part.center() - origin
        cx -= delta.dot(xhat)
        cy -= delta.dot(yhat)
        layers = [d.visible_lines, d.hidden_lines if hidden else None]

    def to_sheet(p):
        v = Vector(*p) - origin
        return (at[0] + (v.dot(xhat) - cx) * scale,
                at[1] + (v.dot(yhat) - cy) * scale)

    out = []
    for sp in layers:
        out.append(None if sp is None else
                   _flatten(Pos(*at) * (Pos(-cx, -cy) * sp).scale(scale, about=(0, 0, 0))))
    return out[0], out[1], to_sheet, (origin, cx, cy)


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

    def put_pt(q):
        return (at[0] + (q[0] - cx) * scale, at[1] + (q[1] - cy) * scale)

    ux, uy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
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
            if hit is None or not hit.faces():
                continue
            for hf in hit.faces():
                # The sliver's OWN extreme vertices along the hatch direction, trimmed
                # 8 % at each end.  The bounding-box diagonal used before is bigger than
                # the sliver wherever the ruling is clipped at an angle, so the hatching
                # visibly ran outside the section outline.
                pts = [(v.X, v.Y) for v in hf.vertices()]
                if len(pts) < 2:
                    continue
                lo_p = min(pts, key=lambda q: q[0] * ux + q[1] * uy)
                hi_p = max(pts, key=lambda q: q[0] * ux + q[1] * uy)
                dx, dy = hi_p[0] - lo_p[0], hi_p[1] - lo_p[1]
                hatches.append([(lo_p[0] + dx * 0.08, lo_p[1] + dy * 0.08),
                                (lo_p[0] + dx * 0.92, lo_p[1] + dy * 0.92)])
    hatches = [[(put_pt(a)), (put_pt(b))] for a, b in hatches]
    # The vertices come back too, in the section's own local coordinates.  Dimensioning
    # a section from computed model values is what makes a dimension "float in the air":
    # the seat floor is 1.10 below a top face that is tilted -7°, so the point the
    # arithmetic names is not on the cut at all.  Snap to a real vertex instead.
    verts = sorted({(round(v.X, 4), round(v.Y, 4)) for f in faces for v in f.vertices()})
    return _flatten(put(outline)), hatches, put_pt, verts


def snap(verts, target, tol=0.6):
    """The section vertex nearest `target`, or raise if nothing is close enough.

    Raising is the point: a silent snap to the wrong corner is a wrong dimension on a
    fabrication drawing, which is worse than a build that stops.
    """
    best = min(verts, key=lambda v: math.hypot(v[0] - target[0], v[1] - target[1]))
    if math.hypot(best[0] - target[0], best[1] - target[1]) > tol:
        raise ValueError(f"no section vertex within {tol} of {target}; nearest {best}")
    return best


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


def projection_symbol(sh, at, d=7.0):
    """ISO 128 FIRST-ANGLE symbol: the end view (concentric circles) to the LEFT.

    Drawn from two independent sources that agree on the handedness, because getting it
    backwards is a serious drawing error.  The title block also says "FIRST ANGLE (ISO
    128)" in words and every view carries its own name, so the words remain the
    authority and the symbol is corroboration.
    """
    x, y = at
    r = d / 2
    for rr in (r, r * 0.55):
        sh.out.append(f'<circle cx="{sh._x(x - d * 0.75):.3f}" cy="{sh._y(y):.3f}" '
                      f'r="{rr:.3f}" fill="none" stroke="#000" stroke-width="{W_THIN}"/>')
    # the trapezoid, small end toward the circles
    sh.path([(x, y - r * 0.55), (x + d, y - r), (x + d, y + r), (x, y + r * 0.55)],
            W_THIN, close=True)


def axes_2d(sh, at, right, up, size=5.0):
    """A two-arrow indicator naming the MODEL axes in the plane of an orthographic view.

    OpenSCAD's frame, the one the .scad and this conversation use: +X right, +Y back,
    +Z up, origin at the bottom of the MX stem on the moulding face.  Without this the
    reader has to infer the handedness of each view from the part, which for a nearly
    symmetric stem is guesswork.
    """
    sh.line(at, (at[0] + size, at[1]), W_HAIR)
    arrow(sh, (at[0] + size + ARROW_L, at[1]), (-1, 0), W_HAIR)
    sh.text(right, (at[0] + size + ARROW_L + 2.2, at[1]), 2.4, "start")
    sh.line(at, (at[0], at[1] + size), W_HAIR)
    arrow(sh, (at[0], at[1] + size + ARROW_L), (0, -1), W_HAIR)
    sh.text(up, (at[0], at[1] + size + ARROW_L + 2.6), 2.4)


def axes_iso(sh, at, size=7.0):
    """An isometric XYZ triad, matching the isometric view's orientation."""
    dirs = {"X": (0.866, -0.5), "Y": (-0.866, -0.5), "Z": (0.0, 1.0)}
    for name, (dx, dy) in dirs.items():
        tip = (at[0] + dx * size, at[1] + dy * size)
        sh.line(at, tip, W_HAIR)
        arrow(sh, (at[0] + dx * (size + ARROW_L), at[1] + dy * (size + ARROW_L)),
              (-dx, -dy), W_HAIR)
        sh.text(name, (at[0] + dx * (size + ARROW_L + 3), at[1] + dy * (size + ARROW_L + 3)),
                2.4)


ZONE_COLS, ZONE_ROWS = 8, 6          # ISO 5457 grid for A3: ~50 mm fields
ZONE_BAND = 8.0                      # band inside the trimmed margin


def zone_grid(sh):
    """ISO 5457 grid reference: 1..8 across, A..F down, on all four edges.

    Numerals run left to right and letters top to bottom, both starting at the
    top-left corner, so a feature can be called out as "the boss, D3" in an email
    without anyone counting views.  A3 takes 8 x 6 fields of ~50 x 46 mm.
    """
    x0, x1, y0, y1 = -FRAME_X, FRAME_X, -FRAME_Y, FRAME_Y
    sh.rect(x0 - ZONE_BAND, y0 - ZONE_BAND, x1 + ZONE_BAND, y1 + ZONE_BAND, W_THIN)
    for i in range(ZONE_COLS + 1):
        x = x0 + (x1 - x0) * i / ZONE_COLS
        for yy, dy in ((y1, ZONE_BAND), (y0, -ZONE_BAND)):
            sh.line((x, yy), (x, yy + dy), W_THIN)
    for j in range(ZONE_ROWS + 1):
        y = y1 - (y1 - y0) * j / ZONE_ROWS
        for xx, dx in ((x0, -ZONE_BAND), (x1, ZONE_BAND)):
            sh.line((xx, y), (xx + dx, y), W_THIN)
    for i in range(ZONE_COLS):
        x = x0 + (x1 - x0) * (i + 0.5) / ZONE_COLS
        for yy in (y1 + ZONE_BAND / 2, y0 - ZONE_BAND / 2):
            sh.text(str(i + 1), (x, yy), 3.0, bold=True, chrome=True)
    for j in range(ZONE_ROWS):
        y = y1 - (y1 - y0) * (j + 0.5) / ZONE_ROWS
        for xx in (x0 - ZONE_BAND / 2, x1 + ZONE_BAND / 2):
            sh.text(chr(ord("A") + j), (xx, y), 3.0, bold=True, chrome=True)


def frame_and_title(sh, cfg, name):
    zone_grid(sh)
    sh.rect(-FRAME_X, -FRAME_Y, FRAME_X, FRAME_Y, W_THICK)
    x0, y0 = FRAME_X - TITLE_W, -FRAME_Y
    x1, y1 = FRAME_X, -FRAME_Y + TITLE_H
    sh.rect(x0, y0, x1, y1, W_THICK)
    for yy in (y1 - 13, y1 - 23, y0 + 11):
        sh.line((x0, yy), (x1, yy), W_THIN)
    # 32, not 22: "PK-STEM-S-1U25" at 2.8 bold is 24 mm wide and a narrower cell
    # draws the rule straight through the part number.
    sh.line((x0 + 32, y1 - 23), (x0 + 32, y0 + 11), W_THIN)
    sh.line((x0 + 86, y1 - 23), (x0 + 86, y0), W_THIN)
    sh.line((x0 + 30, y0 + 11), (x0 + 30, y0), W_THIN)

    sh.embed(LOGO, x0 + 2.5, y1 - 2.0, 9.0, 9.0)
    sh.text("PolyTasten", (x0 + 14, y1 - 4.4), 3.4, "start", bold=True)
    sh.text("polykybd.org", (x0 + 14, y1 - 9.4), 2.2, "start")
    sh.text(f"Keycap stem  {cfg['label']}", (x0 + 46, y1 - 6.5), 5.0, "start", bold=True)

    sh.text("MX mount, injection moulded", (x0 + 2.5, y1 - 18), 2.8, "start")
    sh.text(f"MATERIAL   {MATERIAL}", (x0 + 60, y1 - 18), 2.8, "start", bold=True)
    sh.text("shrink 0.4-0.7 %", (x0 + 92, y1 - 18), 2.2, "start")

    rows = [(2.5, "DRAWING No.", f"PK-STEM-{name.replace('_', '-')}"),
            (2.5, "", ""),
            (60, "SHEET", "1 / 1"),
            (60, "", "")]
    sh.text("DRAWING No.", (x0 + 2.5, y1 - 26.5), 2.0, "start")
    sh.text(f"PK-STEM-{name.replace('_', '-')}", (x0 + 2.5, y1 - 31), 2.8, "start", bold=True)
    sh.text("SHEET REV.", (x0 + 35, y1 - 26.5), 2.0, "start")
    sh.text(DRAWING_REV, (x0 + 35, y1 - 31), 2.8, "start", bold=True)
    sh.text("PART REV.", (x0 + 51, y1 - 26.5), 2.0, "start")
    sh.text(sm.REVISION, (x0 + 51, y1 - 31), 2.8, "start", bold=True)
    sh.text("DATE", (x0 + 66, y1 - 26.5), 2.0, "start")
    sh.text(date.today().isoformat(), (x0 + 66, y1 - 31), 2.4, "start")
    sh.text("DRAWN", (x0 + 92, y1 - 26.5), 2.0, "start")
    sh.text("PolyTasten / PolyKybd", (x0 + 92, y1 - 31), 2.4, "start")
    sh.text("QTY / KEYBOARD", (x0 + 124, y1 - 26.5), 2.0, "start")
    sh.text(str(cfg["qty"]), (x0 + 124, y1 - 31), 2.4, "start")

    sh.text("UNITS  mm", (x0 + 2.5, y0 + 7.6), 2.4, "start")
    sh.text("FINISHED PART", (x0 + 2.5, y0 + 3.9), 2.0, "start")
    sh.text(f"GENERAL TOL.  ISO 2768-m  (±{GENERAL_TOL:.2f} here)",
            (x0 + 34, y0 + 7.6), 2.4, "start")
    sh.text("at 20 °C.  Shrink goes on the CAVITY, not here", (x0 + 34, y0 + 3.9), 2.0, "start")
    sh.text("SCALE  as noted", (x0 + 92, y0 + 7.6), 2.4, "start")
    sh.text("per view", (x0 + 92, y0 + 3.9), 2.0, "start")
    sh.text("FIRST ANGLE", (x0 + 140, y0 + 9.0), 2.0, "middle")
    projection_symbol(sh, (x0 + 137, y0 + 4.0), 4.2)


# --------------------------------------------------------------------- geometry aids
def silhouette_extreme(paths, axis, want_max):
    """The point of a flattened projection that is furthest along `axis` (0=x, 1=y).

    Used to anchor an overall dimension on the real outline.  The overall height used
    to be measured from (-half_width, 0) to (-half_width, z_max), and at z_max the part
    is 2 mm narrower than that, so the upper extension line started in mid-air.
    """
    best = None
    for pl in paths:
        for pt in pl:
            if best is None or ((pt[axis] > best[axis]) == want_max and pt[axis] != best[axis]):
                best = pt
    return best


def cross_mouth(part):
    """The MX slot where it breaks the moulding face -- the lead-in the moulder cuts.

    Measured on the solid at z = 0 rather than derived: the two chamfer extrudes in the
    .scad use scale factors with hand-tuned fudge terms (-0.011, -0.07), so the closed
    form is not the number on the part.
    """
    sec = part & Plane.XY.offset(0.02)
    faces = [f for f in sec.faces() if f.bounding_box().size.X < sm.MX_CYLINDER * 1.2]
    best, wire = None, None
    for f in sec.faces():
        for w in f.inner_wires():
            b = w.bounding_box()
            if b.size.X < sm.MX_CYLINDER and abs(b.center().X) < 0.05:
                if best is None or b.size.X > best.size.X:
                    best, wire = b, w
    return best


# ---------------------------------------------------------------------- the sheet
def cutting_plane(sh, at, tag, direction, reach, half, stroke=6.0):
    """ISO 128-30 cutting-plane marks on the view the section is TAKEN FROM.

    `direction` is the LINE OF SIGHT in that view's sheet coordinates -- the way the
    reader looks through the cut.  Get it from the section plane rather than by eye:
    build123d's `Plane.XZ` has its normal on -Y, so A-A is viewed from the front and its
    arrows point +Y; `Plane.YZ` has its normal on +X, so B-B is viewed from the right and
    its arrows point -X.  The legs run back against the line of sight and the arrowheads
    point along it, which tells a reader which half is kept.

    ⚠️ **The mark is a SHORT stroke at each end, not a line across the view.** Drawn full
    length, the B-B mark ran the height of the plan view and straight through every
    horizontal dimension on it.  ISO 128-30 shows the plane only at its ends and at
    changes of direction; the thin long-dash-short-dash centre line does the joining.
    """
    dx, dy = direction
    ax, ay = -dy, dx                       # unit vector along the cut line
    for sgn in (-1, 1):
        p1 = (at[0] + ax * reach * sgn, at[1] + ay * reach * sgn)
        p0 = (p1[0] - ax * stroke * sgn, p1[1] - ay * stroke * sgn)
        sh.line(p0, p1, W_CUT)
        sh.line(p1, (p1[0] - dx * 5, p1[1] - dy * 5), W_CUT)
        arrow(sh, (p1[0] - dx * 8.5, p1[1] - dy * 8.5), direction, W_CUT)
        sh.text(tag, (p1[0] + ax * 4.5 * sgn - dx * 8, p1[1] + ay * 4.5 * sgn - dy * 8),
                3.4, bold=True)
    sh.line((at[0] - ax * half, at[1] - ay * half), (at[0] + ax * half, at[1] + ay * half),
            W_HAIR, dash="5,1.2,1.2,1.2")


def slot_top_z(part, lo=5.0, hi=6.5, steps=9):
    """The highest z at which the MX slot is still an ENCLOSED hole.

    Measured, not derived: the .scad cuts the cross over `2 * STEM_HEIGHT`, so the void
    runs past the top of the part -- what actually bounds the slot is where the material
    around it runs out and the void merges into the open cap interior.  There is no
    closed form for that (the cap floor is tilted -7°), and it is the number note 6 needs
    to be honest about how far a switch stem can go in.
    """
    for _ in range(steps):
        m = (lo + hi) / 2
        enclosed = any(f.inner_wires() for f in (part & Plane.XY.offset(m)).faces())
        lo, hi = (m, hi) if enclosed else (lo, m)
    return lo


def _ratio(scale):
    """"3:1" for 3.0, "1.6:1" for 1.6.

    Derived, not typed: the scale caption used to be a literal beside each view, and
    when SCALE_ISO went 1.6 -> 2.4 the isometric went on claiming 1.6:1.  A scale a
    reader might measure against must come from the number that drew the view.
    """
    return f"{scale:g}:1"


def build_sheet(name):
    cfg = sm.VARIANTS[name]
    part = sm.build(name)
    bb = part.bounding_box()
    dxo = (cfg["u_size"] - 1) * 2 * 5
    hx, hy = sm.STEM_X / 2 + dxo, sm.STEM_Y / 2
    S, D, D5 = SCALE_MAIN, SCALE_DETAIL, SCALE_STAMP

    plain = sm.build(name, engrave=False)
    # The stamp details are drawn in the CAP's own frame, where the seat floor and the
    # pocket ceiling are flat -- but `cap_body` has no MX slot in it, because `mx_stem`
    # cuts the cross after tilting and raising the cap.  Cut the same cross here, pulled
    # back through that placement, so the two detail views can show the one datum on
    # those faces that a toolmaker can register the stamp against.
    cap_cut = (sm.cap_body(cfg["u_size"], engrave=False)
               - (Rot(-cfg["angle"], 0, 0) * Pos(0, 0, -cfg["extra_len"])
                  * sm.cross_cut(sm.STEM_HEIGHT * 2, 0.97, -sm.SURFACE_OFFSET)))
    # `_engraving` works in the cap's OWN (untilted) frame, so it needs the same
    # placement `mx_stem` gives the cap before the two can be projected together.
    stamp_solid = (Pos(0, 0, cfg["extra_len"]) * Rot(cfg["angle"], 0, 0)
                   * sm._engraving(sm.cap_body(cfg["u_size"], engrave=False)))
    slot_top = slot_top_z(part)

    sh = Sheet()
    frame_and_title(sh, cfg, name)

    # First angle: the view from ABOVE goes below the front view, the view from BELOW
    # above it, and the view from the RIGHT to its left.
    right_at, front_at = (-178.0, 60.0), (-124.0, 60.0)
    top_at, bot_at = (-124.0, -10.0), (-124.0, 108.0)
    # The isometric goes in the gap the orthographic block leaves under the section,
    # not above it: at 1.25U the view-from-below leaders reach 4.4 mm further right
    # and ran straight over it there.
    sec_at, secb_at, iso_at = (-40.0, 76.0), (-32.0, 10.0), (66.0, -30.0)
    det_at, stamp_at, stamp2_at = (66.0, 70.0), (160.0, 90.0), (160.0, 2.0)

    def titled(n, text, at, dy, scale="2:1"):
        sh.text(f"{n}   {text}", (at[0], at[1] + dy), 3.2, bold=True)
        sh.text(scale, (at[0], at[1] + dy - 4.6), 2.4)

    def title_above(n, text, at, box, scale="2:1"):
        """Title above the view, clear of whatever the view actually drew.

        Above rather than below, for all four: a title under a view sits between it and
        the next one down, and on a first-angle sheet the view below is its own
        projection -- V2's label read as if it named V3.
        """
        sh.text(f"V{n}   {text}", (at[0], box[3] + 8.2), 3.2, bold=True)
        sh.text(scale, (at[0], box[3] + 3.6), 2.4)

    M, box, titles = {}, {}, {}
    # `corner` is which side of the OUTLINE the axis triad goes on -- chosen per view as
    # the quadrant that view's dimensions leave empty.  Placing it from the measured
    # outline rather than a fixed offset is what stops it landing on a dimension when a
    # wider variant pushes everything outward.
    for n, look, up, at, title, ax, corner in (
            (1, (1, 0, 0), (0, 0, 1), right_at, "VIEW FROM RIGHT", ("-Y", "Z"), (2, -22)),
            (2, (0, -1, 0), (0, 0, 1), front_at, "VIEW FROM FRONT", ("X", "Z"), (-14, -6)),
            (3, (0, 0, 1), (0, 1, 0), top_at, "VIEW FROM ABOVE", ("X", "Y"), (10, -26)),
            (4, (0, 0, -1), (0, 1, 0), bot_at, "VIEW FROM BELOW", ("-X", "Y"), (-14, -6))):
        box[n] = [1e9, 1e9, -1e9, -1e9]
        titles[n] = (title, at, _ratio(SCALE_TOP if n == 3 else S))
        with sh.group(box[n]):
            obox = [1e9, 1e9, -1e9, -1e9]
            with sh.group(obox):
                # V3 / V4 look straight at the two stamps, and at outline weight they
                # competed with the part.  There the body is projected WITHOUT them and
                # the stamp is overlaid hair-thin, just to place it -- its dimensions
                # live in V8 / V10.  `_engraving` returns the solid that was subtracted,
                # so the overlay is the stamp itself, not a re-derived outline.
                faint = n in (3, 4)
                sc = SCALE_TOP if n == 3 else S
                vis, hid, M[n], al = view(plain if faint else part, look, up,
                                          True, sc, at)
                for pl in hid:
                    sh.path(pl, W_HAIR, dash="2.2,1.4")
                for pl in vis:
                    sh.path(pl, W_THICK)
                if faint:
                    for pl in view(stamp_solid, look, up, False, sc, at, align=al)[0]:
                        sh.path(pl, W_HAIR)
            # Offsets are from the outline itself -- a POSITIVE x hangs the triad off
            # the right edge, a negative one off the left, and y is from the outline's
            # vertical centre.  Anchoring on the outline (not the view centre) is what
            # keeps it put when a wider variant grows the view.
            ox, oy = corner
            axes_2d(sh, (obox[2] + ox if ox > 0 else obox[0] + ox,
                         (obox[1] + obox[3]) / 2 + oy), *ax)

    box[10], titles[10] = [1e9, 1e9, -1e9, -1e9], ("ISOMETRIC", iso_at, _ratio(SCALE_ISO))
    with sh.group(box[10]):
        vis, _, _, _ = view(part, (1, -1, 0.75), hidden=False, scale=SCALE_ISO, at=iso_at)
        for pl in vis:
            sh.path(pl, W_THIN)
        axes_iso(sh, (iso_at[0] + 30, iso_at[1] - 16))

    # --- V5 section A-A, cut on the XZ plane straight through the cross ----------
    box[5], titles[5] = [1e9, 1e9, -1e9, -1e9], ("SECTION A-A", sec_at, _ratio(SCALE_SEC))
    with sh.group(box[5]):
        obox5 = [1e9, 1e9, -1e9, -1e9]
        with sh.group(obox5):
            out_p, hats, MS, va = section(part, Plane.XZ, SCALE_SEC, sec_at)
            for pl in hats:
                sh.path(pl, W_HAIR)
            for pl in out_p:
                sh.path(pl, W_THICK)
        # Plane.XZ local coords are (model X, model Z): the mapper takes them directly.
        # ⚠️ EVERY anchor here is a real vertex of the cut (`snap` raises if it is not).
        # Earlier drafts computed the anchors from model constants, and the arithmetic
        # named points that are not on the section at all -- a dimension floating beside
        # the part, or reaching into it from nowhere.  If a number cannot be anchored on
        # the cut, it does not belong in a section view.
        #
        # ⚠️ Both features here sit in the MIDDLE of the cut, behind the outer skirt, so
        # every dimension line for them has to drag extension lines across hatched
        # material to reach the outside.  Leaders instead: they touch the vertex the
        # number comes from and cross nothing.  A dimension line is not automatically
        # better than a leader -- on a section it is frequently worse.
        bot, top = snap(va, (2.32, 0.0)), snap(va, (2.02, 6.09))
        leader(sh, f"slot {top[1] - bot[1]:.2f} deep from z = 0",
               MS(top), (sec_at[0] - 20, sec_at[1] + 19), 2.2, True)
        b0, b1 = snap(va, (2.75, 0.0)), snap(va, (2.75, 4.0))
        leader(sh, f"Ø{sm.MX_CYLINDER:.2f} boss, {b1[1] - b0[1]:.2f} straight",
               MS(((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2)),
               (sec_at[0] - 26, sec_at[1] - 20), 2.2, True)
        # The height dimensions live here rather than on V2: the front view sees the boss
        # and the skirt only as hidden lines, and this is the cut that makes them
        # outlines.  Both ends of each are section vertices, or the z = 0 moulding face
        # -- which is the section's own bottom edge and the sheet's stated datum.
        #
        # ⚠️ These are named by what they MEASURE, not by which feature I think they
        # are.  `snap` refused the first attempt at this block ("no section vertex within
        # 0.6 of ..."), which is how the pair I had called the flange turned out to be
        # the inside of the pocket -- and to move with u_size, so the label would have
        # been wrong on one variant and the anchor wrong on the other.
        tab = sm.CLICK_TAB_PROUD
        sl, sr = snap(va, (-hx - tab, 1.5)), snap(va, (hx + tab, 1.5))
        dim(sh, MS(sl), MS(sr), -14, f"{sr[0] - sl[0]:.2f} over the click tabs")
        dim(sh, MS((sr[0], 0.0)), MS(sr), 3,
            f"{sr[1]:.2f} skirt above z = 0", vertical=True)
        axes_2d(sh, (obox5[2] + 4, obox5[3] - 4), "X", "Z")
        sh.text("cut on the cross centre-line, so the slot reads full depth",
                (sec_at[0], box[5][1] - 4.5), 2.2)
    with sh.group(box[3]):
        cutting_plane(sh, top_at, "A", (0, 1), hx * SCALE_TOP + 13, 26)

    # --- V6 section B-B, cut on the cable centre-line (the YZ plane) ---------------
    # The A-A cut runs along X and shows the slot; nothing in it says how the flex cable
    # gets out.  B-B is the plane at right angles to it, so it carries the whole cable
    # route: the seat, its 2.12 forward relief, and the flared FFC exit below.
    box[6] = [1e9, 1e9, -1e9, -1e9]
    titles[6] = ("SECTION B-B", secb_at, _ratio(SCALE_SEC))
    with sh.group(box[6]):
        obox9 = [1e9, 1e9, -1e9, -1e9]
        with sh.group(obox9):
            out_b, hats_b, MB, vb = section(part, Plane.YZ, SCALE_SEC, secb_at)
            for pl in hats_b:
                sh.path(pl, W_HAIR)
            for pl in out_b:
                sh.path(pl, W_THICK)
        # Plane.YZ local coords are (model Y, model Z).  Real vertices again -- and here
        # the arithmetic was demonstrably wrong: the seat floor is 1.10 below a top face
        # tilted -7°, so "z_seat" is not a height anything on this cut actually has.
        c0, c1 = snap(vb, (-3.57, 4.96)), snap(vb, (-5.71, 5.22))
        dim(sh, MB(c1), MB(c0), 14, f"{c0[0] - c1[0]:.2f} cable relief")
        # ⚠️ The POCKET CEILING IS NOT PARALLEL to the moulding face.  The cap is tilted
        # -7°, so the ceiling sits 0.79 higher at the front than at the back, and this is
        # the only view that shows it.  Both ends are section vertices, and the two cuts
        # agree: the plane through them meets x = 0 at 4.52, which is what A-A measures
        # there.  It decides which end of the core is thinnest, so it is dimensioned
        # rather than left to be worked out from "cap tilt 7°" on V1.
        sf = snap(vb, (2.89, 4.17))
        dim(sh, MB((c0[0], 0.0)), MB(c0), -16,
            f"{c0[1]:.2f} ceiling, front", vertical=True)
        dim(sh, MB((sf[0], 0.0)), MB(sf), 18,
            f"{sf[1]:.2f} ceiling, back", vertical=True)
        bs = snap(vb, (7.88, 0.53))
        dim(sh, MB((bs[0], 0.0)), MB(bs), 32,
            f"{bs[1]:.2f} skirt above z = 0", vertical=True)
        w_top, w_bot = sm.CABLE_THICKNESS, sm.CABLE_THICKNESS * 7
        axes_2d(sh, (obox9[0] - 13, obox9[1] - 9), "Y", "Z")
        leader(sh, f"{sm.ffc_flare_deg():.1f}° flare", MB(snap(vb, (-5.71, 5.22))),
               (secb_at[0] - 17, secb_at[1] - 15), 2.2, True)
        yb = box[6][1] - 4.5
        for t in ("cut on the cable centre-line.  The FFC exit is",
                  f"{w_top:.2f} wide at the seat floor and {w_bot:.2f} at z = 0;",
                  "the pocket ceiling is tilted 7° with the cap."):
            sh.text(t, (secb_at[0], yb), 2.2)
            yb -= 3.4
    with sh.group(box[3]):
        cutting_plane(sh, top_at, "B", (-1, 0), hy * SCALE_TOP + 17, 26)

    # --- V7 detail B: the cross opening, 10:1 -----------------------------------
    box[7], titles[7] = [1e9, 1e9, -1e9, -1e9], ("DETAIL B    MX CROSS", det_at, _ratio(D))
    g7 = sh.group(box[7]); g7.__enter__()
    z_det = sm.MX_CROSS_FILLET
    cross_sec = part & Plane.XY.offset(z_det)
    stem_face = min(cross_sec.faces(), key=lambda f: f.bounding_box().size.X)
    inner = [w for w in stem_face.wires() if w.bounding_box().size.X < sm.MX_CYLINDER]
    det = Compound(children=list(inner[0].edges()) + list(stem_face.outer_wire().edges()))
    lo, hi = _bbox([det])
    cx0, cy0 = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    for pl in _flatten(Pos(*det_at) * (Pos(-cx0, -cy0) * det).scale(D, about=(0, 0, 0))):
        sh.path(pl, W_THICK)
    sh.centre_lines(det_at, 33, 33)

    def dv(p, scale=D, at=None):
        at = at or det_at
        return (at[0] + p[0] * scale, at[1] + p[1] * scale)

    taper = 1 - 0.03 * z_det / (2 * sm.STEM_HEIGHT)
    c_len = (sm.MX_CROSS - sm.MX_CROSS_FILLET) * taper
    c_wid = (sm.MX_CROSS_WIDTH - sm.MX_CROSS_FILLET) * taper
    dim(sh, dv((-c_len / 2, c_wid / 2)), dv((c_len / 2, c_wid / 2)), 33, f"{c_len:.2f} ±0.03")
    dim(sh, dv((c_wid / 2, -c_len / 2)), dv((c_wid / 2, c_len / 2)), 35, f"{c_len:.2f} ±0.03")
    mouth = cross_mouth(part)
    reach = max(math.hypot(v.X, v.Y)
                for e in inner[0].edges() for v in (e @ (i / 8) for i in range(9)))
    for txt, tip, elbow, left in (
            (f"{c_wid:.2f} ±0.03 arm width", dv((-c_len / 2 + 0.4, c_wid / 2)),
             (det_at[0] - 24, det_at[1] + 28), True),
            (f"R{sm.MX_CROSS_FILLET:.2f}, 4x", dv((c_wid / 2 + 0.12, c_wid / 2 + 0.12)),
             (det_at[0] + 26, det_at[1] + 28), False),
            ("relief bulge 4x", dv((sm.MX_CROSS / 3, -c_wid / 2 - 0.16)),
             (det_at[0] + 27, det_at[1] - 26), False),
            (f"Ø{sm.MX_CYLINDER:.2f} stem",
             dv((-sm.MX_CYLINDER / 2 * 0.707, -sm.MX_CYLINDER / 2 * 0.707)),
             (det_at[0] - 32, det_at[1] - 26), True),
            (f"{sm.MX_CYLINDER / 2 - reach:.2f} min wall, stem to slot", dv((-2.4, 0)),
             (det_at[0] - 34, det_at[1] - 8), True),
                (f"lead-in {mouth.size.X:.2f} sq (note 8)",
             dv((c_len / 2 - 0.3, -c_wid / 2)),
             (det_at[0] + 26, det_at[1] - 34), False)):
        ln, dot, tx = leader_parts(txt, tip, elbow, 2.2, left)
        sh.path(ln, W_HAIR); sh.poly(dot); sh.text(*tx)

    sh.text(f"section at z = {z_det:.2f}, just above the lead-in chamfer",
            (det_at[0], box[7][1] - 4.5), 2.2)
    g7.__exit__(None, None, None)

    # --- V8 detail C: the stamp, as a proposal ----------------------------------
    box[8] = [1e9, 1e9, -1e9, -1e9]
    titles[8] = ("DETAIL C    SEAT-FLOOR STAMP", stamp_at, _ratio(D5))
    g8 = sh.group(box[8]); g8.__enter__()
    seat = sm.stamp_face(cap_cut, sm.STEM_HEIGHT - sm.DISP_HEIGHT)
    fb = seat.bounding_box()
    # ⚠️ The stamp is placed against the UNCUT face, as `_engraving` does -- placing it
    # against the slotted one would centre it in a face with a hole in it and move it.
    stamp = sm.place_stamp(sm.stamp_sketch(),
                           sm.stamp_face(sm.cap_body(cfg["u_size"], engrave=False),
                                         sm.STEM_HEIGHT - sm.DISP_HEIGHT),
                           sm.DISP_Y / 2 - sm.TEXT_SIZE / 2)
    sb = stamp.bounding_box()
    sx, sy = (fb.min.X + fb.max.X) / 2, (fb.min.Y + fb.max.Y) / 2

    def sv(p):
        return (stamp_at[0] + (p[0] - sx) * D5, stamp_at[1] + (p[1] - sy) * D5)

    # The MX slot breaks through this face too, and it is the only datum on it that a
    # toolmaker can register the stamp against -- without it the view is a rectangle
    # with two letters in it and nothing to locate them from.
    for w in seat.inner_wires():
        for pl in _flatten(Pos(*stamp_at) * (Pos(-sx, -sy) * w).scale(D5, about=(0, 0, 0))):
            sh.path(pl, W_THICK)
    for shape, w in ((seat.outer_wire(), W_THIN), (stamp, W_THICK)):
        for pl in _flatten(Pos(*stamp_at) * (Pos(-sx, -sy) * shape).scale(D5, about=(0, 0, 0))):
            sh.path(pl, w)
    # The stamp's own centre line, and where it sits relative to the stem axis (y = 0),
    # which is the origin every other view is dimensioned from.
    scy = (sb.min.Y + sb.max.Y) / 2
    sh.line(sv((fb.min.X - 0.4, scy)), sv((fb.max.X + 0.4, scy)), W_HAIR,
            dash="5,1.2,1.2,1.2")
    sh.line(sv((0, fb.min.Y - 0.4)), sv((0, fb.max.Y + 0.4)), W_HAIR,
            dash="5,1.2,1.2,1.2")
    dim(sh, sv((0, 0)), sv((0, scy)), -26, f"{scy:.2f} to the stamp CL",
        vertical=True)
    dim(sh, sv((fb.min.X, fb.max.Y)), sv((fb.max.X, fb.max.Y)), 8,
        f"{fb.size.X:.2f} seat floor")
    dim(sh, sv((fb.min.X, fb.min.Y)), sv((fb.min.X, fb.max.Y)), -8,
        f"{fb.size.Y:.2f}", vertical=True)
    dim(sh, sv((sb.min.X, sb.min.Y)), sv((sb.max.X, sb.min.Y)), -30, f"{sb.size.X:.2f}")
    dim(sh, sv((sb.max.X, sb.min.Y)), sv((sb.max.X, sb.max.Y)), 8, f"{sb.size.Y:.2f}")
    dim(sh, sv((sb.min.X, sb.max.Y)), sv((sb.min.X, fb.max.Y)), -20,
        f"{fb.max.Y - sb.max.Y:.2f} min to the edge", vertical=True)
    leader(sh, f"{sm.STAMP_GAP:.2f} gap, {sm.TEXT_HEIGHT:.2f} deep",
           sv((0, sb.min.Y + 0.3)), (stamp_at[0] - 24, stamp_at[1] - 8), 2.2, True)

    # ⚠️ Snapshot the box first: `sh.text` grows it, so reading box[8][1] again on the
    # second line puts that line 3.4 mm below where the first one just pushed the floor.
    y8 = box[8][1] - 4.5
    for k, t in enumerate(("looking down +Z, as V3.  Thin outline",
                           "= the face the stamp is cut into.")):
        sh.text(t, (stamp_at[0], y8 - k * 3.4), 2.2)
    g8.__exit__(None, None, None)

    # --- V10 detail D: the SECOND stamp, in the pocket ceiling -------------------
    # Drawn rather than described, and drawing it is what caught the description being
    # WRONG: the sheet used to say "the same, mirrored ... reads correctly from below".
    # The .scad applies `rotate([180, 0, 0])`, which is a flip about X -- so the stamp
    # is TURNED 180°, and in a projected view-from-below it appears upside down, not
    # mirrored.  (An S is 180°-symmetric, so only the β shows it.)  That is the one
    # instruction here a toolmaker could satisfy the wrong way round, and the cost is a
    # cavity insert that reads backwards on every part.  No dimensions: they are V8's,
    # and repeating them would invite the two to drift.
    #
    # ⚠️ The face and the stamp do NOT get the same transform, which is the whole point.
    # `_engraving` places the pocket stamp with `Rot(180, 0, 0)`, so its footprint is
    # (x, -y) of the sketch, while the face it sits in is untouched.  Looking from below
    # maps model (x, y) to screen (-x, y).  Compose the two and the face MIRRORS while
    # the stamp ROTATES -- do both the same way and V10 becomes a drawing of a part we
    # are not making.
    box[9] = [1e9, 1e9, -1e9, -1e9]
    titles[9] = ("DETAIL D    POCKET-CEILING STAMP", stamp2_at, _ratio(D5))
    with sh.group(box[9]):
        ceil = sm.stamp_face(cap_cut, sm.INSIDE_HEIGHT)
        under = sm.place_stamp(sm.stamp_sketch(),
                               sm.stamp_face(sm.cap_body(cfg["u_size"], engrave=False),
                                             sm.INSIDE_HEIGHT), -sm.DISP_Y / 3)
        cbb = ceil.bounding_box()
        ccx, ccy = (cbb.min.X + cbb.max.X) / 2, (cbb.min.Y + cbb.max.Y) / 2

        def pv(pl, sx, sy):
            return [(stamp2_at[0] + (sx * x - sx * ccx) * D5,
                     stamp2_at[1] + (sy * y - sy * ccy) * D5) for x, y in pl]

        def cv(x, y, sy=1):
            return pv([(x, y)], -1, sy)[0]

        for shape, w, sy in ((ceil.outer_wire(), W_THIN, 1), (under, W_THICK, -1)):
            for pl in _flatten(shape):
                sh.path(pv(pl, -1, sy), w)
        for w in ceil.inner_wires():                 # the MX slot, same reason as V8
            for pl in _flatten(w):
                sh.path(pv(pl, -1, 1), W_THICK)
        ub = under.bounding_box()
        ucy = (ub.min.Y + ub.max.Y) / 2              # in `under`; the drawn stamp is -y
        sh.line(cv(cbb.min.X - 0.4, -ucy), cv(cbb.max.X + 0.4, -ucy), W_HAIR,
                dash="5,1.2,1.2,1.2")
        sh.line(cv(0, cbb.min.Y - 0.4), cv(0, cbb.max.Y + 0.4), W_HAIR,
                dash="5,1.2,1.2,1.2")
        dim(sh, cv(0, 0), cv(0, -ucy), -26, f"{abs(ucy):.2f} to the stamp CL",
            vertical=True)
        dim(sh, cv(cbb.min.X, cbb.max.Y), cv(cbb.max.X, cbb.max.Y), 13,
            f"{cbb.size.X:.2f} pocket ceiling")
        dim(sh, cv(cbb.max.X, cbb.min.Y), cv(cbb.max.X, cbb.max.Y), -13,
            f"{cbb.size.Y:.2f}", vertical=True)
        dim(sh, cv(ub.min.X, ub.max.Y, -1), cv(ub.max.X, ub.max.Y, -1), -30,
            f"{ub.size.X:.2f}")
        y10 = box[9][1] - 4.5
        for t in ("looking up -Z, as V4.  Same stamp, same depth,",
                  "TURNED 180° -- not mirrored.  It reads normally",
                  "when the part is flipped over front-to-back."):
            sh.text(t, (stamp2_at[0], y10), 2.2)
            y10 -= 3.4

    # --- dimensions --------------------------------------------------------------
    # Each block goes into its view's own extent box, so the title placed afterwards
    # clears the dimensions as well as the outline.
    # V3 from above: plan envelope, display seat, click tabs
    with sh.group(box[3]):
        dim(sh, M[3]((-hx, hy, 0)), M[3]((hx, hy, 0)), 12, f"{2 * hx:.2f}")
        dim(sh, M[3]((hx, -hy, 0)), M[3]((hx, hy, 0)), 13, f"{2 * hy:.3f}")
        y_seat = sm.DISP_Y_CENTER_OFFSET - sm.DISP_Y / 2
        dim(sh, M[3]((-sm.DISP_X / 2, -hy, 0)), M[3]((sm.DISP_X / 2, -hy, 0)), -7,
            f"{sm.DISP_X:.2f} display seat")
        dim(sh, M[3]((-hx, y_seat, 0)), M[3]((-hx, y_seat + sm.DISP_Y, 0)), -8,
            f"{sm.DISP_Y:.2f}", vertical=True)
        # The click tabs are a functional feature (note 10), so V3 dimensions the one
        # length that is legible at 2:1 and the leader carries the three that are not.
        tl, tp = sm.CLICK_TAB_L, sm.CLICK_TAB_PROUD
        dim(sh, M[3]((-tl / 2, hy + tp, 0)), M[3]((tl / 2, hy + tp, 0)), 6,
            f"{tl:.2f} click tab")
        y_cab = sm.DISP_Y_CENTER_OFFSET - sm.DISP_Y / 2 - sm.CABLE_STEM_Y
        dim(sh, M[3]((-sm.CABLE_STEM_X / 2, y_cab, 0)),
            M[3]((sm.CABLE_STEM_X / 2, y_cab, 0)), -13,
            f"{sm.CABLE_STEM_X:.2f} cable relief (V6)")
        leader(sh, "click tab 3x (note 6)", M[3]((-hx - tp, tl / 4, 0)),
               (top_at[0] - 32 - dxo * SCALE_TOP, top_at[1] + 18), 2.2, True)

    # V2 from front: overall height and the top face, both on the real outline
    with sh.group(box[2]):
        dim(sh, M[2]((hx, 0, 0)), M[2]((hx, 0, bb.max.Z)), 12,
            f"{bb.max.Z:.2f} overall", vertical=True)
        w_top = sm.STEM_X * sm.STEM_TOP_BOTTOM_RATIO + 2 * dxo
        z_top = cfg["extra_len"] + sm.STEM_HEIGHT * math.cos(math.radians(cfg["angle"]))
        dim(sh, M[2]((-w_top / 2, 0, z_top)), M[2]((w_top / 2, 0, z_top)), 8,
            f"{w_top:.2f} top face")

    # V1 from right: the cap tilt, which is the whole point of the profile.  A note
    # under the view, not a leader: a leader long enough to carry this sentence runs
    # straight into the front view beside it.
    with sh.group(box[1]):
        sh.text(f"cap tilt {abs(cfg['angle']):.0f}° (the S profile)",
                (right_at[0], box[1][1] - 4.5), 2.2)

    # V4 from below: the switch-clearance chamfer, which only this view shows
    px, py = (sm.INSIDE_X + sm.INSIDE_X + sm.STEM_X) / 6, (sm.INSIDE_Y + sm.STEM_Y) / 4
    with sh.group(box[4]):
        leader(sh, f"switch clearance {2 * px:.2f} x {2 * py:.2f} at z = 0",
               M[4]((-px * 0.97, py * 0.55, 0)),
               (bot_at[0] + 24 + dxo * S, bot_at[1] + 11), 2.2)
        leader(sh, f"{sm.draft_angles()[3][4]:.1f}° inner chamfer (note 5)",
               M[4]((-px * 0.86, py * 0.05, 0)),
               (bot_at[0] + 24 + dxo * S, bot_at[1] + 4), 2.2)
        leader(sh, f"pocket {sm.INSIDE_HEIGHT:.2f} deep from z = 0",
               M[4]((-px * 0.55, -py * 0.75, 0)),
               (bot_at[0] + 24 + dxo * S, bot_at[1] - 8), 2.2)

    for n, (title, at, *sc) in sorted(titles.items()):
        title_above(n, title, at, box[n], *sc)

    notes_block(sh, c_len, c_wid, mouth, slot_top)
    for line in sh.report_collisions():
        print("  ! overlap:", line.strip())
    return sh


def leader_parts(text, tip, elbow, size=2.2, left=False):
    """`leader` split into its pieces, so a caller can batch them onto layers."""
    tail = (elbow[0] + (-3.5 if left else 3.5), elbow[1])
    dot = [(tip[0] - 0.4, tip[1]), (tip[0], tip[1] + 0.4),
           (tip[0] + 0.4, tip[1]), (tip[0], tip[1] - 0.4)]
    txt = (text, (tail[0] + (-0.8 if left else 0.8), tail[1]), size,
           "end" if left else "start")
    return [tip, elbow, tail], dot, txt


def _wrap(text, width):
    """Greedy word wrap that KEEPS the double space after a full stop.

    `text.split(" ")` yields an empty token for the second space of a pair, so the naive
    version silently reflows the whole sheet's sentence spacing to single -- against the
    house style every hand-written line here uses.  An empty token just widens the gap.
    """
    out, line = [], ""
    for word in text.split(" "):
        if not word:
            line += " "
            continue
        cand = (line + " " + word) if line and not line.endswith(" ") else line + word
        if line.strip() and len(cand.rstrip()) > width:
            out.append(line.rstrip())
            line = word
        else:
            line = cand
    if line.strip():
        out.append(line.rstrip())
    return out


def notes_block(sh, c_len, c_wid, mouth, slot_top):
    """The notes block.

    ⚠️ **Anything the title block already states does NOT get a note.**  The first draft
    opened with "dimensions in mm", "general tolerance ISO 2768-m" and "material ABS" --
    all three of which are cells in the block a reader looks at first, so they cost four
    lines of the sheet's scarcest space to repeat something.  Keep the notes for what a
    cell cannot hold: the axis convention, the two CRITICAL items, and the things a
    moulder would otherwise decide for us.

    ⚠️ **The text is wrapped HERE, not typed pre-wrapped.**  Every one of these notes
    interpolates a measured value, so a hand-wrapped line silently overruns the moment a
    number gains a digit -- and at one column the block reached to 2 mm off the frame.
    Two wrapped columns halve the height and the wrapping follows the content.
    """
    dr = {n: a for n, *_, a in sm.draft_angles()}
    notes = [
        f"1.  CRITICAL  MX slot {c_len:.2f} x {c_wid:.2f} ±0.03, R{sm.MX_CROSS_FILLET:.2f} "
        "corner fillets (V7).  Gauge against a real MX switch stem, not by CMM alone.  "
        "Our slot is deliberately TIGHTER than Cherry's published keycap slot; the four "
        "relief bulges are what make that work.  Verify on a moulded first article.",
        "2.  CRITICAL  The transparent relegendable cap is an off-the-shelf POS part, so "
        "that mating dimension is a hard datum set by a supplier we do not control.  "
        "Confirm before cutting steel.",
        f"3.  Draft, measured off the model: outer body {dr['outer body X']:.1f}°, inside "
        f"pocket {dr['inside pocket']:.1f}°.  ZERO DRAFT on the display seat "
        f"({sm.DISP_X} x {sm.DISP_Y} x {sm.DISP_HEIGHT} deep) and on its cable relief (V6) "
        "-- confirm release at first article rather than meeting it there.",
        f"4.  Slot draft {dr['cross arm flat']:.2f}° on the flats, "
        f"{dr['cross arm tip']:.2f}° at the arm tips, opening downward: the core pin "
        "withdraws the right way, but with very little relief.  Polish along the arms.  "
        f"The slot runs from the moulding face to z = {slot_top:.2f} -- through the boss "
        "and on into the cap floor (V5).",
        f"5.  The inner chamfer in V4 ({dr['centre pocket']:.1f}°) is switch-body "
        "clearance, not cosmetic -- it is what stops the cap fouling a bulky switch.  Do "
        "not flatten it to simplify the core.",
        f"6.  The three {sm.CLICK_TAB_W:.2f} x {sm.CLICK_TAB_L:.2f} x "
        f"{sm.CLICK_TAB_H:.2f} tabs standing {sm.CLICK_TAB_PROUD:.2f} proud (+Y and ±X, "
        "V3) are FUNCTIONAL: they are what makes the clear keycap click on properly.  "
        "They must NOT be removed.",
        f"7.  Stamp \"{sm.REVISION} {sm.PROFILE}\" = revision + profile, "
        f"{sm.TEXT_HEIGHT:.2f} deep, zero draft, in TWO places: the display-seat floor "
        "(V8) and the pocket ceiling (V9).  The second is TURNED 180°, not mirrored -- "
        "it reads normally when the part is flipped over front-to-back.  Drawn in V9; do "
        f"not infer it.  Revision character is {sm.revision_codepoint().upper()}.  Carry "
        "it on a REPLACEABLE INSERT in the cavity rather than cut into the block: a "
        "revision change is then a plug swap, not a tool edit.  Font Noto Sans Bold, "
        "outlines in the STEP.",
        f"8.  The slot lead-in opens to {mouth.size.X:.2f} x {mouth.size.Y:.2f} at z = 0 "
        f"over {sm.MX_CROSS_FILLET:.2f} mm (~46°).  Keep it -- it is what lets the cap "
        "start on the stem.",
        "9.  GATE AND EJECTORS are the moulder's choice, but they must NOT land on the MX "
        "slot or its lead-in, the display seat floor or cable relief, the three click "
        "tabs, or the moulding face (z = 0).  A side wall (±X) clear of the tabs is the "
        "obvious place, feeding toward the stem boss -- the thickest section, and a wall "
        "that already tolerates a witness mark.  Mark the positions chosen on the tooling "
        "drawing and send it back.",
        "10.  Surface: tool polish on the slot and the stem bore; the outer faces may "
        "carry the standard texture.  No flash permitted on the slot, the tabs or the "
        "seat floor.",
    ]
    lines = [("NOTES", True)]
    for note in notes:
        for k, ln in enumerate(_wrap(note, NOTE_CHARS)):
            lines.append(((NOTE_INDENT if k else "") + ln, False))
    # Break only at note boundaries, and choose the breaks that make the TALLEST column
    # as short as possible.  Filling each column to a fixed height is the obvious version
    # and it is wrong: one long note after the fill line dumps most of the block into
    # column 1, which then runs off the bottom of the frame.
    starts = [i for i, (t, _) in enumerate(lines) if not t.startswith(NOTE_INDENT)]
    best, cuts = None, None
    for a in range(1, len(starts) - 1):
        for b in range(a + 1, len(starts)):
            i, j = starts[a], starts[b]
            tall = max(i, j - i, len(lines) - j)
            if best is None or tall < best:
                best, cuts = tall, (i, j)
    chunks = [lines[:cuts[0]], lines[cuts[0]:cuts[1]], lines[cuts[1]:]]
    for col, chunk in enumerate(chunks):
        y = NOTE_Y0
        for i, (t, bold) in enumerate(chunk):
            sh.text(t, (-198.0 + col * NOTE_COL_W, y), 2.1, "start", bold=bold)
            y -= 2.1 * 1.42 if i or col else 3.4


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
