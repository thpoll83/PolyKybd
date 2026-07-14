#!/usr/bin/env python3
"""Fast merge: place rasterised PCB layer PNGs onto A4 pages with headers, contents,
summary and bookmarks."""
import os, warnings; warnings.filterwarnings("ignore")
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import colors
from PIL import Image

BASE = "/sessions/bold-festive-carson/mnt/outputs"
PAGES = os.path.join(BASE, "pcb_pages")
OUT = os.path.join(BASE, "PolyKybd-PCB-Layers.pdf")
A4W, A4H = 595.275591, 841.889764
BLUE = (0x1F/255, 0x4E/255, 0x78/255)

import argparse, ce_common
SECTION = "PCB Layer Documentation"
_ap = argparse.ArgumentParser(); _ap.add_argument("--start", type=int, default=1)
START = _ap.parse_args().start
_pageno = [START]

BOARDS = [("Left board", "L"), ("Right board", "R")]
LAYER_TITLES = [
    "Top Copper — F.Cu", "Inner Layer 1 — In1.Cu", "Inner Layer 2 — In2.Cu",
    "Bottom Copper — B.Cu", "Top Solder Mask — F.Mask", "Bottom Solder Mask — B.Mask",
    "Top Paste — F.Paste", "Bottom Paste — B.Paste", "Board Outline — Edge.Cuts",
]
N = len(LAYER_TITLES)

# board dims from outline gerber (fast parse)
dims = {}
try:
    from gerbonara import LayerStack
    for _, sub in BOARDS:
        (x0,y0),(x1,y1) = LayerStack.open_dir(os.path.join(BASE,"pcb",sub)).graphic_layers[('mechanical','outline')].bounding_box()
        dims[sub] = (round(x1-x0,1), round(y1-y0,1))
except Exception:
    dims = {"L":None,"R":None}

c = rl_canvas.Canvas(OUT, pagesize=(A4W, A4H))

def text_page(lines, title=None):
    y = A4H-70
    if title:
        c.setFillColorRGB(*BLUE); c.setFont("Helvetica-Bold", 18); c.drawString(30, y, title); y -= 26
    for txt, size, bold in lines:
        c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(30, y, txt); y -= size+6
    ce_common.draw_frame(c, SECTION, _pageno[0]); _pageno[0]+=1
    c.showPage()

# title
text_page([
    ("PolyKybd Split72", 20, True),
    ("PCB Layer Documentation — Rev 3.2", 13, False),
    ("", 6, False),
    ("Fabrication layer plots for the left and right boards (4-layer PCB),", 10, False),
    ("generated from the released production Gerber set.", 10, False),
    ("Prepared: 2026-07-13", 10, False),
])
# contents
page_of = {}
p = 3
for _, sub in BOARDS:
    for i in range(N): p += 1; page_of[(sub,i)] = p
clines = [("Contents", 15, True), ("", 4, False)]
for name, sub in BOARDS:
    d = dims.get(sub); dtxt = f"   ({d[0]} x {d[1]} mm)" if d else ""
    clines.append((f"{name}{dtxt}", 12, True))
    for i in range(N):
        clines.append((f"   {LAYER_TITLES[i]}   p.{page_of[(sub,i)]}", 9.5, False))
    clines.append(("", 4, False))
text_page(clines)
# summary
text_page([
    ("PCB construction summary", 14, True),
    ("", 4, False),
    ("Layer count: 4 (2 outer + 2 inner copper).  Stack order top->bottom: F.Cu, In1.Cu, In2.Cu, B.Cu.", 10, False),
    ("Base material: FR-4.  Surface finish: ENIG or lead-free HASL (per PCB fabricator RoHS certificate).", 10, False),
    (f"Left board outline: {dims['L'][0]} x {dims['L'][1]} mm." if dims.get('L') else "", 10, False),
    (f"Right board outline: {dims['R'][0]} x {dims['R'][1]} mm." if dims.get('R') else "", 10, False),
    ("", 6, False),
    ("Layers shown: copper (x4), solder mask (top/bottom), solder paste (top/bottom), board outline.", 10, False),
    ("Silkscreen layers are part of the released Gerber set; export from KiCad (kicad-cli) if required.", 9, False),
    ("Confirm exact dielectric thicknesses / copper weights with the PCB fabricator.", 9, False),
])

def layer_page(title, sub_txt, png):
    c.setFillColorRGB(*BLUE); c.setFont("Helvetica-Bold", 15); c.drawString(28, A4H-42, title)
    c.setFillColorRGB(0.25,0.25,0.25); c.setFont("Helvetica", 10); c.drawString(28, A4H-58, sub_txt)
    c.setStrokeColorRGB(0.75,0.75,0.75); c.setLineWidth(0.5); c.line(28, A4H-64, A4W-28, A4H-64)
    iw, ih = Image.open(png).size
    box_w = A4W-52; box_h = (A4H-74)-34
    landscape = iw >= ih
    c.saveState(); c.translate(28+box_w/2, 34+box_h/2)
    if landscape:
        c.rotate(90); s = min(box_w/ih, box_h/iw)
    else:
        s = min(box_w/iw, box_h/ih)
    w, h = iw*s, ih*s
    c.drawImage(png, -w/2, -h/2, width=w, height=h)
    c.restoreState()
    ce_common.draw_frame(c, SECTION, _pageno[0]); _pageno[0]+=1
    c.showPage()

for name, sub in BOARDS:
    for i in range(N):
        layer_page(f"{name} — {LAYER_TITLES[i]}", "PolyKybd Split72 Rev 3.2",
                   os.path.join(PAGES, f"{sub}_{i}.png"))

c.save()
from pypdf import PdfReader
print("saved", OUT, "| pages", len(PdfReader(OUT).pages), "| dims", dims)
