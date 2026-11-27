"""Write the emoji layer's screens as a legend atlas for the render scripts.

    QT_QPA_PLATFORM=offscreen ../PolyKybdHost/.venv/bin/python render/emoji_atlas.py <name> [category] [page]

Writes textures/<name>.png/.json in export_screens.py's format (72x40 cells, 10
columns, matrix "row,col" -> cell), from tutorial_screens.Screens().emoji_menu(),
which draws the emoji layer as the firmware does on the default split72 keymap.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tutorial_screens as ts  # noqa: E402

name = sys.argv[1]
cat = int(sys.argv[2]) if len(sys.argv) > 2 else 0
page = int(sys.argv[3]) if len(sys.argv) > 3 else 0
fr = ts.Screens().emoji_menu(cat, page)
keys = sorted(fr.keys, key=lambda mp: tuple(map(int, mp.split(","))))
W, H, C = 72, 40, 10
rows = (len(keys) + C - 1) // C
atlas = np.zeros((rows * H, C * W), np.uint8)
cells = {}
for n, mp in enumerate(keys):
    x, y = n % C * W, n // C * H
    a = np.asarray(fr.keys[mp], np.float32)
    atlas[y:y + H, x:x + W] = np.clip(a * (255 if a.max() <= 1 else 1), 0, 255).astype(np.uint8)
    cells[mp] = [x, y]
out = os.path.join(HERE, "textures", name)
Image.fromarray(atlas).convert("RGB").save(out + ".png")
json.dump({"cell": [W, H], "size": [C * W, rows * H], "keys": cells}, open(out + ".json", "w"), indent=1)
print(f"{len(keys)} keys -> {out}.png")
