#!/usr/bin/env python3
"""Compose the distinct PolyKybd schematic sub-blocks into one PDF.
Repeated per-key (SSD1306_TO_SPI) and buffer (ni_buffer2) sheets are included once."""
import os, io, warnings
warnings.filterwarnings("ignore")
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pypdf import PdfReader, PdfWriter

SD  = "/sessions/bold-festive-carson/mnt/PolyKybd/RoHS/schematics"
OUT = "/sessions/bold-festive-carson/mnt/outputs/PolyKybd-Schematics.pdf"

# order requested: left, right, RP2040, key block, then other subsystems
BLOCKS = [
    ("Left half — PolyKybd Split L (root sheet)",        "poly_kybd_split72_left.pdf"),
    ("Right half — PolyKybd Split72 R (root sheet)",     "poly_kybd_split72_right.pdf"),
    ("RP2040 — microcontroller (rp_pico)",               "poly_kybd_split72_left-RpPico.pdf"),
    ("Key block — OLED key unit (SSD1306_TO_SPI, ×36/side, shown once)",
                                                         "poly_kybd_split72_left-K_L1.pdf"),
    ("Shift Registers (shift_registers)",                "poly_kybd_split72_left-ShiftRegisters.pdf"),
    ("Non-Inverting Buffer (ni_buffer2, repeated, shown once)",
                                                         "poly_kybd_split72_left-NonInvertingBuffer0.pdf"),
]

# ---- front matter (A4) : title + contents (page numbers computed below) ----
ss = getSampleStyleSheet()
H1  = ParagraphStyle("H1", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=22,
                     textColor=colors.HexColor("#1F4E78"), spaceAfter=6)
SUB = ParagraphStyle("SUB", parent=ss["Normal"], fontName="Helvetica", fontSize=11,
                     textColor=colors.HexColor("#404040"))
TOC = ParagraphStyle("TOC", parent=ss["Normal"], fontName="Helvetica", fontSize=11, leading=17)

# page count of each block (for contents numbering)
counts = [len(PdfReader(os.path.join(SD, f)).pages) for _, f in BLOCKS]
front_pages = 1
start = {}
run = front_pages
for (label, f), c in zip(BLOCKS, counts):
    start[f] = run + 1          # 1-based page in final PDF
    run += c

def esc(t): return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def front_bytes():
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=20*mm, bottomMargin=16*mm)
    st = [Paragraph("PolyKybd", H1),
          Paragraph("Schematics", ParagraphStyle("t2", parent=H1, fontSize=16)),
          Spacer(1, 4*mm),
          Paragraph("Complete hierarchical schematic set. Repeated per-key and buffer sheets "
                    "are shown once; every distinct sub-block is included.", SUB),
          Spacer(1, 6*mm),
          Paragraph("<b>Contents</b>", SUB), Spacer(1, 2*mm)]
    for (label, f) in BLOCKS:
        st.append(Paragraph(f'{esc(label)} &nbsp;&mdash;&nbsp; <b>p.{start[f]}</b>', TOC))
    doc.build(st)
    return buf.getvalue()

# ---- assemble ----
import argparse, ce_common
SECTION = "Schematics"
_ap = argparse.ArgumentParser(); _ap.add_argument("--start", type=int, default=1)
START = _ap.parse_args().start
writer = PdfWriter()
for p in PdfReader(io.BytesIO(front_bytes())).pages:
    writer.add_page(ce_common.a4_fit(p, rotate_landscape=False))
idx = {}
for label, f in BLOCKS:
    idx[f] = len(writer.pages)          # 0-based
    for p in PdfReader(os.path.join(SD, f)).pages:
        writer.add_page(ce_common.a4_fit(p))   # scale + rotate landscape into content band
for label, f in BLOCKS:
    writer.add_outline_item(label, idx[f])
ce_common.stamp(writer, SECTION, START)
writer.add_metadata({"/Title": "PolyKybd Schematics"})
with open(OUT, "wb") as fh:
    writer.write(fh)
print("saved", OUT, "| total pages:", len(writer.pages),
      "| start", START, "-> next section at page", START+len(writer.pages))
for label, f in BLOCKS:
    print(f"  p{start[f]:<3} {f}")
