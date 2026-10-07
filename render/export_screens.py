"""Draw what the displays show on layer 0, for screens.py (PolyKybdHost's renderer).

    QT_QPA_PLATFORM=offscreen ../PolyKybdHost/.venv/bin/python render/export_screens.py [host checkout]

Writes render/textures/screens_layer0.png, an atlas of every key display's
72x40 legend (one cell per key, 10 columns), screens_layer0.json (matrix
"row,col" -> cell), and status_{left,right}.png, the two 128x64 status panels.
These are the RAW framebuffers, light pixels on pure black; the render does
the glow. ⚠️ The editor draws its panels on a dark ground (8, 10, 14), not
black, and screens.py makes every pixel emit, so that ground lit the whole
active area a metallic grey. `unlit()` maps it to black: an off OLED pixel
emits nothing. The legends come from the host layout editor's preview code over the
keymap in its shipped preview data (polyhost/res/preview/board.json, the
firmware's default keymap), so they are what the editor's Preview mode draws.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "PolyKybdHost"))
sys.path.insert(0, HOST)

from PyQt5.QtGui import QImage, QPainter  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

app = QApplication([])
from polyhost.gui.layout_dialog import kb_layout_dialog as kb  # noqa: E402

COLS, ROWS, LAYERS = 8, 10, 8           # the split72 matrix; the editor reads 8 layers
CELL_W, CELL_H, ATLAS_COLS = 72, 40, 10
# the export could not resolve this token to a number; HYPR(KC_NO) is QK_MODS | 0x0F << 8
UNRESOLVED = {"KC_HYPR": 0x0F00}

board = json.load(open(os.path.join(HOST, "polyhost", "res", "preview", "board.json"), encoding="utf-8"))
keys = []
for k in board["keys"]:
    code = k["keycode"] if k["keycode"] is not None else UNRESOLVED.get(k["token"], 0)
    keys.append((tuple(k["matrix"]), code))
buf = [0] * (COLS * ROWS * LAYERS)
for (r, c), code in keys:
    buf[r * COLS + c] = code


class Core:
    """Just enough of PolyCore for the dialog to open with this keymap."""
    def keymap_layer_names(self): return True, [f"L{i}" for i in range(LAYERS)]
    def keymap_layer_count(self): return True, LAYERS
    def keymap_buffer(self, *a, **k): return True, buf
    def keymap_default_layer(self): return True, 0
    def macro_list(self): return True, {"macros": [], "count": 0}
    def subscribe(self, cb): return lambda: None


class Settings:
    MATRIX_COLUMNS, MATRIX_ROWS = COLS, ROWS


def unlit(img):
    """The image with its darkest colour (the panel ground) set to pure black."""
    img = img.convertToFormat(QImage.Format_RGB32)
    ground = min(img.pixel(x, y) & 0xFFFFFF for y in range(img.height()) for x in range(img.width()))
    for y in range(img.height()):
        for x in range(img.width()):
            if img.pixel(x, y) & 0xFFFFFF == ground:
                img.setPixel(x, y, 0xFF000000)
    return img


d = kb.KbLayoutDialog(Core(), Settings())
names = d.keycode_browser.get_keycode_to_name_mapping()
n_rows = (len(keys) + ATLAS_COLS - 1) // ATLAS_COLS
atlas = QImage(ATLAS_COLS * CELL_W, n_rows * CELL_H, QImage.Format_RGB32)
atlas.fill(0)
cells, blank = {}, []
p = QPainter(atlas)
for i, ((r, c), code) in enumerate(keys):
    img = d._preview.render(code, names.get(code)) if code else None
    if img is None:
        blank.append(f"{r},{c}")
        continue
    x, y = (i % ATLAS_COLS) * CELL_W, (i // ATLAS_COLS) * CELL_H
    p.drawImage(x, y, unlit(img))
    cells[f"{r},{c}"] = [x, y]
p.end()
out = os.path.join(HERE, "textures")
atlas.save(os.path.join(out, "screens_layer0.png"))
with open(os.path.join(out, "screens_layer0.json"), "w", encoding="utf-8") as f:
    json.dump({"cell": [CELL_W, CELL_H], "size": [atlas.width(), atlas.height()],
               "fw_version": board.get("fw_version"), "keys": cells}, f, indent=1)
sr = kb.StatusScreenRenderer(d._preview.status_faces())
for side in ("left", "right"):
    unlit(sr.render(side, 0, d._layer_name(0))).save(os.path.join(out, f"status_{side}.png"))
print(f"{len(cells)} legends, blank: {blank}")
