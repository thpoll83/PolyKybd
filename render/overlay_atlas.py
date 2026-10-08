"""An app's overlay icons on a legend atlas, as the keyboard shows them.

    python render/overlay_atlas.py board.json <app>.mods.png screens_layer1 screens_<app>_l1

update_displays() draws a key's normal legend and then ORs the app's overlay
image for that keycode over it (copy_overlay_to_buffer()). This does the same on
textures/<atlas>.png with the overlay's NO_MOD variant (alpha channel), and writes
textures/<out>.png and .json. Overlay sheets are 10 x 9 slots of 72 x 40 in
keycode order from KC_A, jumping past the keypad and media ranges
(PolyKybdHost res/overlay_specification.md).
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageChops

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")


def slot(kc):
    """The overlay sheet slot of a basic keycode, or None."""
    if 0x04 <= kc <= 0x53:
        return kc - 0x04
    if kc in (0x64, 0x65):
        return 80 + kc - 0x64
    if 0xE0 <= kc <= 0xE7:
        return 82 + kc - 0xE0
    return None


board_path, sheet, base, out = sys.argv[1:5]
atlas = Image.open(os.path.join(TEX, base + ".png")).convert("L")
cells = json.load(open(os.path.join(TEX, base + ".json"), encoding="utf-8"))["keys"]
board = json.load(open(board_path, encoding="utf-8"))
icons = Image.open(sheet).getchannel("A").point(lambda v: 255 if v > 127 else 0)
n = 0
for k in board["keys"]:
    cell = cells.get("{},{}".format(*k["matrix"]))
    s = slot(k["keycode"]) if isinstance(k["keycode"], int) else None
    if cell is None or s is None:
        continue
    icon = icons.crop(((s % 10) * 72, (s // 10) * 40, (s % 10) * 72 + 72, (s // 10) * 40 + 40))
    if icon.getextrema()[1] == 0:
        continue
    x, y = cell
    atlas.paste(ImageChops.lighter(atlas.crop((x, y, x + 72, y + 40)), icon), (x, y))
    n += 1
atlas.save(os.path.join(TEX, out + ".png"))
shutil.copy(os.path.join(TEX, base + ".json"), os.path.join(TEX, out + ".json"))
print(f"{n} keys carry an overlay icon")
