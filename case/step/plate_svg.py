"""Emit a flat SVG of the bottom-plate outline (rim outer edge + plate seat) and the
4 M2 screw-hole positions, extracted from the built metal-case STEP in the wedge-
flattened frame (the plane the plate lies in).  Right + left halves.

  python3 plate_svg.py            # -> bottom_plate_right.svg, bottom_plate_left.svg

The plate drops INTO the recess and rests on the ledge, so the PLATE CUT LINE is the
recess opening.  Two outlines are emitted:
  * black solid  = plate cut line = recess opening (ledge outer edge).  Add your own
                   fit clearance (~0.1-0.2 mm inward) so it drops in without binding.
  * grey dashed  = OUTER edge of the rim (case outer boundary) -- reference only.
Red = the 4 screw holes: 2.2 mm M2-clearance circles + exact-centre cross-hairs.
SVG is in millimetres, top-view oriented (un-mirrored); the left file is the X-mirror.
"""
import numpy as np, math
from build123d import import_step, Axis
import case_model as cm

STEP = "metal-case-right.step"
HOLE_CLEAR_D = 2.2   # M2 clearance for the plate through-holes


def flatten(part):
    best = None
    for f in part.faces():
        n = cm._safe_normal(f)
        if n is not None and n.Z < -0.3:
            z = f.bounding_box().min.Z
            if best is None or z < best[0]:
                best = (z, f, n)
    bn = best[2]
    t = np.array([0, 0, -1.0]); n = np.array([bn.X, bn.Y, bn.Z]); n = n / np.linalg.norm(n)
    axv = np.cross(n, t); s = np.linalg.norm(axv); ang = math.degrees(math.atan2(s, n @ t))
    axv = axv / s if s > 1e-9 else np.array([1.0, 0, 0])
    return part.rotate(Axis((0, 0, 0), tuple(axv)), ang)


def outer_loop(pf, zlevel):
    fs = [f for f in pf.faces()
          if (cm._safe_normal(f) or type('', (), {'Z': 0})()).Z < -0.7
          and abs(f.bounding_box().min.Z - zlevel) < 0.12]
    bestw, besta = None, 0
    for f in fs:
        for w in [f.outer_wire()] + list(f.inner_wires()):
            b = w.bounding_box(); a = b.size.X * b.size.Y
            if a > besta:
                besta, bestw = a, w
    pts = []
    for e in bestw.edges():
        nseg = max(2, int(e.length / 0.4))
        for u in np.linspace(0, 1, nseg):
            p = e.position_at(u); pts.append((p.X, p.Y))
    return np.array(pts)


def write_svg(fn, rim, seat, holes):
    M = 6.0
    xmin, xmax = rim[:, 0].min(), rim[:, 0].max()
    ymin, ymax = rim[:, 1].min(), rim[:, 1].max()
    W, H = xmax - xmin + 2 * M, ymax - ymin + 2 * M
    tx = lambda x: x - (xmin - M)
    ty = lambda y: (ymax + M) - y            # flip Y for SVG (keeps top-view un-mirrored)

    def poly(pts, **kw):
        d = 'M ' + ' L '.join('%.3f,%.3f' % (tx(x), ty(y)) for x, y in pts) + ' Z'
        a = ' '.join('%s="%s"' % (k.replace('_', '-'), v) for k, v in kw.items())
        return '<path d="%s" %s/>' % (d, a)

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%.2fmm" height="%.2fmm" viewBox="0 0 %.3f %.3f">' % (W, H, W, H),
         '<g fill="none" stroke-width="0.25">',
         '<!-- PLATE CUT LINE = recess opening (ledge outer edge) -->', poly(seat, stroke='#000000'),
         '<!-- reference only: outer edge of the rim (case outer boundary) -->',
         poly(rim, stroke='#aaaaaa', stroke_dasharray='2,1.5'),
         '</g>',
         '<!-- 4x M2 screw holes: %.1fmm clearance circles + exact centres -->' % HOLE_CLEAR_D,
         '<g stroke="#ff0000" stroke-width="0.25" fill="none">']
    for x, y in holes:
        cx, cy = tx(x), ty(y)
        o.append('<circle cx="%.3f" cy="%.3f" r="%.3f"/>' % (cx, cy, HOLE_CLEAR_D / 2))
        o.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f"/>' % (cx - 1.6, cy, cx + 1.6, cy))
        o.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f"/>' % (cx, cy - 1.6, cx, cy + 1.6))
    o += ['</g>', '</svg>']
    open(fn, 'w').write('\n'.join(o))
    print('wrote %s  (%.1f x %.1f mm)' % (fn, W, H))


def main():
    pf = flatten(import_step(STEP))
    rim = outer_loop(pf, -0.86)     # outer rim edge (case outer at the bottom)
    seat = outer_loop(pf, 0.64)     # ledge outer edge (plate seat)
    holes = list(cm.SCREW_HOLES)
    write_svg('bottom_plate_right.svg', rim, seat, holes)
    rimL = rim.copy(); rimL[:, 0] *= -1
    seatL = seat.copy(); seatL[:, 0] *= -1
    write_svg('bottom_plate_left.svg', rimL, seatL, [(-x, y) for x, y in holes])


if __name__ == "__main__":
    main()
