"""Which board key is which: KLE matrix labels for the key displays, and where
on a display decal its 72x40 active area sits. Shared by topview.py (the host
editor's real view) and screens.py (lit displays)."""
import json
import math

import numpy as np

U = 19.05

# display active area inside the decal (gen_textures.display_front: 12.2 x 11.0 mm
# image; image bottom = key -y = the cable side). 9.2 x 5.1 mm (72 x 40 at the
# panel's 0.1277 mm pitch), centred in the dark panel area of the PHOTO the
# texture is made from (about 0.5..11.7 mm across, 0.6..6.4 mm down, measured
# on the texture). Was 1.35 mm down, from the old drawn texture; the photo
# puts it 0.35 mm higher.
A_U0, A_U1 = 1.5 / 12.2, 10.7 / 12.2
A_V0, A_V1 = 1 - 6.1 / 11.0, 1 - 1.0 / 11.0


def kle_keys(path):
    """[(label, cx, cy)] key centres in U, KLE frame (y down), rotations applied."""
    rows = json.load(open(path, encoding="utf-8"))
    keys = []
    r = rx = ry = 0.0
    x = y = 0.0
    for row in rows:
        if not isinstance(row, list):
            continue
        w = h = 1.0
        for item in row:
            if isinstance(item, dict):
                if "r" in item:
                    r = item["r"]
                if "rx" in item:
                    rx = item["rx"]
                    x, y = rx, ry
                if "ry" in item:
                    ry = item["ry"]
                    x, y = rx, ry
                x += item.get("x", 0)
                y += item.get("y", 0)
                w, h = item.get("w", w), item.get("h", h)
                continue
            cx, cy = x + w / 2, y + h / 2
            a = math.radians(r)
            dx, dy = cx - rx, cy - ry
            keys.append((item.split("\n")[0], rx + dx * math.cos(a) - dy * math.sin(a),
                         ry + dx * math.sin(a) + dy * math.cos(a)))
            x += w
            w = h = 1.0
        y += 1
        x = rx
    return keys


def match(board_xy, kle):
    """Board key centres (KiCad mm, y down) -> KLE labels, by translation fit."""
    pts = np.array([[k[1] * U, k[2] * U] for k in kle])
    t = board_xy.mean(0) - pts.mean(0)
    for _ in range(5):
        d = ((board_xy[:, None] - (pts + t)[None]) ** 2).sum(-1)
        near = d.argmin(1)
        t = (board_xy - pts[near]).mean(0)
    d = ((board_xy[:, None] - (pts + t)[None]) ** 2).sum(-1)
    near = d.argmin(1)
    resid = np.sqrt(d[np.arange(len(near)), near]).max()
    assert len(set(near)) == len(near), "two board keys matched one KLE key"
    return [kle[i][0] for i in near], resid
