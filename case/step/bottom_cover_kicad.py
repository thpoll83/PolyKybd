"""Emit a KiCad .kicad_pcb for the metal-case BOTTOM COVER (ONE part fits both halves), ready to
order as an aluminium PCB. (This is the cover for the METAL case — unrelated to the
3D-printed-case plate in poly_kybd/poly_kybd_split72_plate_*.kicad_pcb.)

  python3 bottom_cover_kicad.py   # -> metal_case_bottom_cover.kicad_pcb

The two case halves are exact X-mirrors and the outline is left-right asymmetric, so
the SAME flat cover is used as-is on the right half and FLIPPED (180 deg about the
vertical axis) on the left. Flipping maps the hole pattern exactly; "PolyKybd" is on
both faces so it shows on whichever side ends up outward.

Geometry is taken from the built STEP in the same wedge-flattened, top-view frame as
plate_svg.py (the plane the plate lies in):
  * Cover OUTLINE (Edge.Cuts) = the recess opening (ledge outer wire, z ~ +0.64),
    the black solid line in the SVG, offset INWARD by PLATE_MARGIN (0.5 mm per side)
    so the cover drops into the recess with clearance.
  * 4x M2 clearance drill holes (Ø HOLE_CLEAR_D) at SCREW_HOLES, as non-plated
    through-holes (mounting-hole footprints).
  * "PolyKybd" on F.SilkS and B.SilkS, centred (bottom mirrored so it reads correctly).

Copper layers are intentionally empty — this is a cover, not a circuit.
"""
import numpy as np, uuid
from build123d import import_step, make_face, offset, Kind
import case_model as cm
from plate_svg import flatten, STEP, HOLE_CLEAR_D

PLATE_MARGIN = 0.15     # shrink outline inward per side for drop-in fit (CNC recess is precise;
                        # 0.15 = reliable no-bind clearance. Raise for a looser fit.)
EDGE_W       = 0.1      # Edge.Cuts stroke width
SILK_SIZE    = 10.0     # "PolyKybd" cap height on the silk (mm)
SILK_THICK   = 1.5
M            = 10.0     # border around the board in the KiCad sheet
SHEET_SHIFT  = 20.0     # nudge the whole board +X/+Y so it sits clear on the sheet
SILK_FONT    = "Arial Black"   # named TTF; KiCad fills the outline in the gerbers
_NS = uuid.UUID("0b0757a0-0000-4000-8000-000000000001")   # deterministic tstamp namespace


def _uid(tag):
    return str(uuid.uuid5(_NS, tag))


def seat_outline():
    """The recess-opening wire (flattened frame), offset inward PLATE_MARGIN; sampled pts."""
    pf = flatten(import_step(STEP))
    cand = []
    for f in pf.faces():
        n = cm._safe_normal(f)
        if n is not None and n.Z < -0.7 and abs(f.bounding_box().min.Z - 0.64) < 0.12:
            b = f.bounding_box(); cand.append((b.size.X * b.size.Y, f))
    cand.sort(key=lambda t: t[0])
    w = cand[-1][1].outer_wire()
    inner = offset(make_face(w), amount=-PLATE_MARGIN, kind=Kind.ARC)
    iw = inner.faces()[0].outer_wire()
    # ⚠️ Sample the WHOLE wire by arc length (ordered, connected traversal), NOT per
    # `iw.edges()` — edge order isn't guaranteed connected, which scrambled the polyline
    # into an OPEN outline (gaps/zero-length dupes) that KiCad won't close for 3D.
    # endpoint=False so the loop isn't duplicated; write_pcb closes last->first.
    N = max(400, int(iw.length / 0.3))
    pts = [(p.X, p.Y) for p in (iw.position_at(u) for u in np.linspace(0, 1, N, endpoint=False))]
    return np.array(pts)


LAYERS = """  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )"""


def write_pcb(fn, title, outline, holes):
    xmin, xmax = outline[:, 0].min(), outline[:, 0].max()
    ymin, ymax = outline[:, 1].min(), outline[:, 1].max()
    tx = lambda x: x - (xmin - M) + SHEET_SHIFT
    ty = lambda y: (ymax + M) - y + SHEET_SHIFT   # flip Y -> KiCad (Y down), keep top-view
    cx, cy = tx((xmin + xmax) / 2), ty((ymin + ymax) / 2)

    o = ['(kicad_pcb (version 20221018) (generator pcbnew)',
         '  (general (thickness 1.6))',
         '  (paper "A4")',
         '  (title_block (title "%s") (rev "1") (company "thpoll"))' % title,
         LAYERS,
         '  (setup (pad_to_mask_clearance 0))',
         '  (net 0 "")',
         '']
    # closed polyline on Edge.Cuts
    N = len(outline)
    for i in range(N):
        x0, y0 = outline[i]; x1, y1 = outline[(i + 1) % N]
        o.append('  (gr_line (start %.3f %.3f) (end %.3f %.3f) '
                 '(stroke (width %.3f) (type solid)) (layer "Edge.Cuts") (tstamp %s))'
                 % (tx(x0), ty(y0), tx(x1), ty(y1), EDGE_W, _uid('%s-edge-%d' % (fn, i))))

    o.append('')
    o.append('  (gr_text "PolyKybd" (at %.3f %.3f) (layer "F.SilkS")' % (cx, cy))
    o.append('    (effects (font (face "%s") (size %.2f %.2f) (thickness %.2f) italic))'
             % (SILK_FONT, SILK_SIZE, SILK_SIZE, SILK_THICK))
    o.append('    (tstamp %s))' % _uid(fn + '-silkF'))
    o.append('  (gr_text "PolyKybd" (at %.3f %.3f) (layer "B.SilkS")' % (cx, cy))
    o.append('    (effects (font (face "%s") (size %.2f %.2f) (thickness %.2f) italic) (justify mirror))'
             % (SILK_FONT, SILK_SIZE, SILK_SIZE, SILK_THICK))
    o.append('    (tstamp %s))' % _uid(fn + '-silkB'))

    o.append('')
    for i, (hx, hy) in enumerate(holes):
        kx, ky = tx(hx), ty(hy)
        o.append('  (footprint "MountingHole" (layer "F.Cu") (tstamp %s)' % _uid('%s-fp-%d' % (fn, i)))
        o.append('    (at %.3f %.3f)' % (kx, ky))
        o.append('    (attr exclude_from_pos_files exclude_from_bom)')
        o.append('    (pad "" np_thru_hole circle (at 0 0) (size %.2f %.2f) (drill %.2f) '
                 '(layers "F&B.Cu" "*.Mask") (tstamp %s))'
                 % (HOLE_CLEAR_D, HOLE_CLEAR_D, HOLE_CLEAR_D, _uid('%s-pad-%d' % (fn, i))))
        o.append('  )')

    o.append(')')
    open(fn, 'w').write('\n'.join(o) + '\n')
    W, H = tx(xmax) + M, ty(ymin) + M
    print('wrote %s  board %.1f x %.1f mm, %d edge segs, %d holes'
          % (fn, xmax - xmin, ymax - ymin, N, len(holes)))


def main():
    # ONE part fits BOTH halves: the two case halves are exact X-mirrors, and the
    # outline is left-right asymmetric, so the same flat cover is used as-is on the
    # right and FLIPPED (180 deg about the vertical axis) on the left. Flipping maps
    # the right hole pattern exactly onto the left, and the wordmark is on both faces
    # so it shows on whichever side ends up outward.
    out = seat_outline()
    holes = list(cm.SCREW_HOLES)
    write_pcb('metal_case_bottom_cover.kicad_pcb',
              'PolyKybd Metal-Case Bottom Cover (fits both halves - flip for the left)', out, holes)


if __name__ == "__main__":
    main()
