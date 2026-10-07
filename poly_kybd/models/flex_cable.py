"""The keycap display's flex cable, at its real length: display -> PCB slot ->
the FH34SRJ connector on the bottom side.

    python poly_kybd/models/flex_cable.py        (numpy only)

writes keycap_flex_cable.wrl. The old keycap_display_cable.wrl stopped 5.7 mm
above the PCB, short of the plate, and never reached the connector.

Frame: the key footprint (poly_kb:Kailh_socket_MX_Indicators), mm, Y up, z = 0
on the PCB top. So the boards reference it with offset 0, rotate 0 and scale
0.3937 (KiCad reads VRML in 0.1 inch). From the board files:

- the display (keycap_display.wrl at offset z 12, scale 0.39) spans
  y -4.57..6.44 and z 16.51..17.45; the cable side is its front edge, -y;
- the footprint's plated slot (pad 3, oval 9.76 x 1.7) is at KiCad y +5.08,
  i.e. y = -5.08 here, through the 1.6062 mm PCB;
- the key's own FH34SRJ (on B.Cu) is the one BEHIND it, at KiCad y -9.49
  (y = +9.49 here): every one of the 36 keys has one at exactly that offset,
  the bottom-row thumb keys included. Its mouth faces away from the slot.
  So the cable curves BACK from the slot in one wide sweep, under the
  hotswap socket (bottom -3.60) and the switch's centre post (-3.16), runs
  past the connector, folds up and forward and enters the mouth: a -270 deg
  turn overall, as built (per the designer).

`strip()` is also imported by render/textured_parts.py, which builds the same
geometry with texture coordinates for Blender.
"""
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

WIDTH = 7.5            # mm; the 14 pins span 6.5, the slot is 9.76 long
THICK = 0.11           # mm
PCB = 1.6062
Y_SLOT = -5.08
Z_TOP = 16.45          # just under the display glass (its underside is 16.51)
Z_MOUTH = -(PCB + 0.35)  # the middle of the connector's 0.7 mm high mouth
Z_RUN = -3.95          # under the hotswap socket (-3.60) and centre post (-3.16)
R_TOP = 0.8
R_SWEEP = 2.0          # the wide bend from the slot back under the switch
R_LOOP = (Z_MOUTH - Z_RUN) / 2
Y_LOOP = 11.4          # loop centre, past the connector's far end (+11.0)
Y_START = -3.6         # bonded under the display's front edge
Y_END = 9.0            # inserted ~1.5 mm into the mouth (far side at +10.5)


def bezier(c, step):
    """Points along a cubic Bezier with control points c (4 x (y, z))."""
    c = np.array(c, dtype=float)
    approx = sum(np.linalg.norm(c[i + 1] - c[i]) for i in range(3))
    tt = np.linspace(0.0, 1.0, max(8, int(approx / step)), endpoint=False)[:, None]
    pts = ((1 - tt) ** 3 * c[0] + 3 * (1 - tt) ** 2 * tt * c[1]
           + 3 * (1 - tt) * tt ** 2 * c[2] + tt ** 3 * c[3])
    return [tuple(p) for p in pts]


def catmull_rom(ctrl, step, alpha=0.5):
    """Points along a centripetal Catmull-Rom spline through ctrl[1:-1]."""
    out = []
    c = [np.array(q, dtype=float) for q in ctrl]
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** alpha
        t2 = t1 + np.linalg.norm(p2 - p1) ** alpha
        t3 = t2 + np.linalg.norm(p3 - p2) ** alpha
        n = max(4, int(np.linalg.norm(p2 - p1) / step))
        for tt in np.linspace(t1, t2, n, endpoint=(i == len(c) - 3)):
            a1 = (t1 - tt) / (t1 - t0) * p0 + (tt - t0) / (t1 - t0) * p1
            a2 = (t2 - tt) / (t2 - t1) * p1 + (tt - t1) / (t2 - t1) * p2
            a3 = (t3 - tt) / (t3 - t2) * p2 + (tt - t2) / (t3 - t2) * p3
            b1 = (t2 - tt) / (t2 - t0) * a1 + (tt - t0) / (t2 - t0) * a2
            b2 = (t3 - tt) / (t3 - t1) * a2 + (tt - t1) / (t3 - t1) * a3
            out.append(tuple((t2 - tt) / (t2 - t1) * b1 + (tt - t1) / (t2 - t1) * b2))
    return out


def centreline(step=0.15):
    """(y, z) points and unit tangents along the strip's centre."""
    pts = []

    def line(p0, p1):
        n = max(2, int(math.dist(p0, p1) / step))
        for i in range(n):
            t = i / n
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))

    def arc(c, r, a0, a1):
        n = max(4, int(abs(a1 - a0) * r / step))
        for i in range(n):
            a = a0 + (a1 - a0) * i / n
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))

    # under the display, heading -y
    line((Y_START, Z_TOP), (Y_SLOT + R_TOP, Z_TOP))
    # bend down
    arc((Y_SLOT + R_TOP, Z_TOP - R_TOP), R_TOP, math.pi / 2, math.pi)
    # straight down through the plate's switch hole and the PCB slot
    line((Y_SLOT, Z_TOP - R_TOP), (Y_SLOT, -0.4))
    # under the board: two cubic Beziers, no straight run. The first sags
    # from the slot under the switch, the hotswap socket and the connector
    # and comes up past the connector's far end; the second curls forward
    # into the mouth. A Bezier stays inside its control hull, so y never
    # passes 12.9 (the next key's slot starts at 13.1).
    pts.extend(bezier(((Y_SLOT, -0.4), (Y_SLOT, -7.2), (12.9, -7.4), (12.9, -2.9)), step))
    pts.extend(bezier(((12.9, -2.9), (12.9, -1.956), (11.6, -1.956), (10.4, Z_MOUTH)), step))
    line((10.4, Z_MOUTH), (Y_END, Z_MOUTH))
    pts.append((Y_END, Z_MOUTH))
    p = np.array(pts)
    t = np.gradient(p, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    return p, t


def strip():
    """Closed thin strip: vertices (N, 3), triangles (M, 3) and per-vertex
    uv (N, 2), u across the width, v = arc length / total length (0 at the
    display end). The top and bottom faces carry the uv; the edges reuse it."""
    p, t = centreline()
    nrm = np.stack([-t[:, 1], t[:, 0]], axis=1)      # left normal in the y-z plane
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))])
    v = s / s[-1]
    n = len(p)
    verts, uvs = [], []
    for side in (+1, -1):                            # the two faces of the strip
        off = p + nrm * (side * THICK / 2)
        for x, u in ((-WIDTH / 2, 0.0), (WIDTH / 2, 1.0)):
            for i in range(n):
                verts.append((x, off[i, 0], off[i, 1]))
                uvs.append((u, v[i]))
    verts, uvs = np.array(verts), np.array(uvs)
    a0, a1, b0, b1 = 0, n, 2 * n, 3 * n              # rows: face A left/right, face B left/right
    tris = []
    for i in range(n - 1):
        for r0, r1, flip in ((a0, a1, False), (b0, b1, True),   # faces
                             (a0, b0, True), (a1, b1, False)):  # long edges
            q = (r0 + i, r1 + i, r1 + i + 1, r0 + i + 1)
            tri = [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
            tris += [tuple(reversed(x)) for x in tri] if flip else tri
    for i in (0, n - 1):                             # end caps
        q = (a0 + i, a1 + i, b1 + i, b0 + i)
        tris += [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
    return verts, np.array(tris), uvs, s[-1]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    from stl_to_wrl import write_wrl
    verts, tris, _, length = strip()
    write_wrl(HERE / "keycap_flex_cable.wrl", [(verts[tris].reshape(-1, 3), (0.7, 0.3, 0.1))],
              f"flex_cable.py, {length:.1f} mm")
