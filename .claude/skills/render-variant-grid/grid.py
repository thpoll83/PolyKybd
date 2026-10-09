"""Compose numbered, labelled crops into one comparison image.

    python3 grid.py out.jpg --crop x0,y0,x1,y1 [--cols 2] [--size 1400x788] \
        "photo=ref.jpg" "glow 15=g15.png" ...

Each cell is resized to --size, cropped to --crop, and labelled
"<n> <label>" in its top-left corner. Cells run row by row, left to right, so
"picture 4" means the same thing to everyone; say so in the caption too.
Needs Pillow (Blender's bundled Python has it).
"""
import argparse

from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("cells", nargs="+", help="label=path")
ap.add_argument("--crop", required=True)
ap.add_argument("--cols", type=int, default=2)
ap.add_argument("--size", default="1400x788")
a = ap.parse_args()
size = tuple(int(v) for v in a.size.split("x"))
box = tuple(int(v) for v in a.crop.split(","))
w, h = box[2] - box[0], box[3] - box[1]
rows = -(-len(a.cells) // a.cols)
sheet = Image.new("RGB", (w * a.cols, h * rows))
for k, cell in enumerate(a.cells):
    label, path = cell.split("=", 1)
    im = Image.open(path).convert("RGB").resize(size).crop(box)
    ImageDraw.Draw(im).text((10, 10), f"{k + 1} {label}", fill=(255, 255, 0))
    sheet.paste(im, ((k % a.cols) * w, (k // a.cols) * h))
sheet.save(a.out, quality=88)
print(a.out, sheet.size)
