"""Build the VRML models for the plate inserts from their printable STLs.

    python poly_kybd/models/gen_inserts.py

- status_display_holder.wrl  parts/export/display_holder/display_holder_r1.stl
  plus the display it carries (glass and active area, sized from
  display_holder.scad's show_display branch). Frame: holder.scad's, so the
  cut-out is x 0..27, y 0..26 and the plate top is z = 2.5.
- cover_insert.wrl  one upright piece cut out of the 10-piece print sheet
  parts/export/cover_insert/cover_insert_r3_10p.stl (the piece at x = -26,
  sprues dropped), recentred. Frame: cover_insert.scad's, the 17 x 14 cut-out
  centred on the origin, flange underside (= plate top) at z = 0.4.
- diffuser_frame_split72_{left,right}.wrl  parts/export/diffuser/
  diffuser_frame_<side>.stl, the one-piece LED diffuser frame, moved into the
  plate model's frame so it attaches exactly like the plate (see below).

All are in mm, so the boards reference them with scale 0.3937.

The diffuser frame is generated in plate coordinates (gen_diffuser_frame.py):
x = plate x - 139.3036, y = -(plate y - 93.701), plate underside at z = 0 and
z up through the plate. Both offsets were fitted from the 36 LED holes of each
plate (worst residual 0.0006 mm). The plate VRML (gen_plates.py) puts plate
point PLATE_ORIGIN at its origin with the plate mid-plane at z = 0, and the
board turns it over (rotate 0 180 0, offset z 4.2). So the frame is written in
that same frame with z mirrored: plate underside z = 0 -> +0.8, the face that
ends up at the bottom. That makes it a reflection, so the faces are rewound.
"""
from pathlib import Path

import numpy as np

from stl_to_wrl import load_stl, write_wrl

HERE = Path(__file__).resolve().parent
PARTS = HERE.parent.parent / "parts" / "export"
CASE_GREY = (0.35, 0.35, 0.37)
DIFFUSER = (0.85, 0.86, 0.88)           # a colour no other model uses: render/materials.py's role
FRAME_TO_PLATE = (139.3036, 93.701)     # plate (x, y) = (fx + 139.3036, 93.701 - fy)
PLATE_ORIGIN = {"left": (259.7096 - 48.4915, 50.6615),       # gen_plates.PLATES
                "right": (259.6016 - 73.152, 50.66025)}
PLATE_HALF_T = 0.8


def box(x0, y0, z0, sx, sy, sz):
    """Triangles of an axis-aligned box, as an (N*3, 3) vertex array."""
    x1, y1, z1 = x0 + sx, y0 + sy, z0 + sz
    c = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return np.array([c[i] for a, b, cc, d in quads for i in (a, b, cc, a, cc, d)])


def display_holder():
    holder = load_stl(PARTS / "display_holder" / "display_holder_r1.stl")
    disp_x, disp_y, disp_t, emboss, cut_t = 27 - 0.05, 19.5 - 0.35, 1.6, 0.3, 2.5
    lcd_x, lcd_y = 21.7, 10.9
    glass = box(0, 2 - 0.2, cut_t - disp_t - emboss, disp_x, disp_y, disp_t)
    lcd = box((disp_x - lcd_x) / 2, 5, 2.15, lcd_x, lcd_y, 0.1)
    write_wrl(HERE / "status_display_holder.wrl", [
        (holder, CASE_GREY), (glass, (0.06, 0.06, 0.07)), (lcd, (0.01, 0.01, 0.015))],
        "display_holder_r1.stl + display")


def cover_insert():
    tris = load_stl(PARTS / "cover_insert" / "cover_insert_r3_10p.stl").reshape(-1, 3, 3)
    c = tris.mean(1)
    piece = tris[(np.abs(c[:, 0] + 26) < 12) & (tris[:, :, 2].min(1) > -2.0)]
    piece = piece.reshape(-1, 3) + np.array([26.0, 0, 0])
    write_wrl(HERE / "cover_insert.wrl", [(piece, CASE_GREY)], "cover_insert_r3_10p.stl, one piece")


def load_ascii_stl(path):
    """Vertices (N*3, 3) of an ASCII STL, the format the diffuser frames are kept in."""
    v = [line.split()[1:4] for line in open(path, encoding="ascii") if line.lstrip().startswith("vertex")]
    return np.array(v, dtype=np.float64)


def diffuser_frames():
    for side in ("left", "right"):
        v = load_ascii_stl(PARTS / "diffuser" / f"diffuser_frame_{side}.stl")
        ox, oy = PLATE_ORIGIN[side]
        out = np.column_stack([v[:, 0] + FRAME_TO_PLATE[0] - ox,
                               v[:, 1] - FRAME_TO_PLATE[1] + oy,
                               PLATE_HALF_T - v[:, 2]])
        out = out.reshape(-1, 3, 3)[:, ::-1].reshape(-1, 3)     # z mirrored: rewind
        write_wrl(HERE / f"diffuser_frame_split72_{side}.wrl", [(out, DIFFUSER)],
                  f"diffuser_frame_{side}.stl, in the plate model's frame")


if __name__ == "__main__":
    display_holder()
    cover_insert()
    diffuser_frames()
