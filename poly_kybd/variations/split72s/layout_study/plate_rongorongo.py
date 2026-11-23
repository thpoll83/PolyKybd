#!/usr/bin/env python3
"""Plate artwork proposal for layout E: Rongorongo-style glyph lines on the plate,
with the switch cut-outs of the split72 plate.

    python3 plate_rongorongo.py

Writes plate_rongorongo.svg (1 unit = 1 mm). The glyphs are simplified drawings in
the Rongorongo manner (figures, birds, fish, turtle, plants, crescent), drawn for
this proposal. They are NOT copied from a tablet; a production version should trace
real glyphs from a source with a free licence. The glyph lines cover the whole plate regardless
of the keys (the holes cut through them), glyphs about 11 mm high, in reverse
boustrophedon: every second line is turned 180 degrees, as on the tablets. Bodies and
limbs are outlined strokes (two 0.35 mm lines), as the incised glyphs on the tablets.

Cut-out per key (from poly_kybd_split72_plate_left.kicad_pcb): a 14 x 14 mm hole,
0.8 mm wide slots on the left and right sides (12 mm long, for the switch clips) and a
5 x 0.66 mm notch on the back side. Wider keys keep the 1U cut-out at their centre.
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
U = 19.05
MARGIN = 5.0                 # plate border outside the keys, as render/layout_scene.py
LINE = 0.35                  # silkscreen line width, mm (JLC minimum 0.15)
OUTLINE_GAP = 0.45           # gap between the two lines of an outlined stroke
GLYPH_W, GLYPH_H = 6.0, 9.0  # glyph box in drawing units; stands on y = 9
SCALE = 1.22                 # drawing unit -> mm: glyphs about 11 mm high
PITCH_X = 6.6                # glyph spacing along a line, drawing units
PITCH_Y = 13.6               # target line spacing, mm (adjusted to fill the plate height)


def circle(cx, cy, r):
    return f"M{cx - r},{cy} a{r},{r} 0 1 0 {2 * r},0 a{r},{r} 0 1 0 {-2 * r},0"


def ellipse(cx, cy, rx, ry):
    return f"M{cx - rx},{cy} a{rx},{ry} 0 1 0 {2 * rx},0 a{rx},{ry} 0 1 0 {-2 * rx},0"


# Each glyph is a list of (kind, path) in a 6 x 9 box, y down:
#   "o" an outlined stroke (two parallel lines, as the incised bodies on the tablets),
#   "l" a single line, "f" a filled dot.
G = {}
G["figure arms up"] = [
    ("o", circle(3, 1.3, 0.9)), ("o", "M3 2.2C2.7 3.5 2.7 5 3 6.2"),
    ("o", "M2.9 3C1.6 3.2 0.9 2.4 0.8 0.9"), ("o", "M3.1 3C4.4 3.2 5.1 2.4 5.2 0.9"),
    ("o", "M3 6.2C2.2 7 1.6 7.8 1.3 9"), ("o", "M3 6.2C3.8 7 4.4 7.8 4.7 9"),
    ("l", "M0.8 0.9L0.3 0.3M0.8 0.9L0.8 0.1M0.8 0.9L1.3 0.3M5.2 0.9L4.7 0.3M5.2 0.9L5.2 0.1M5.2 0.9L5.7 0.3"),
    ("f", circle(2.7, 1.2, 0.17)), ("f", circle(3.3, 1.2, 0.17))]
G["figure with ears"] = [
    ("o", "M3 0.4C1.6 0.4 1.5 2.8 3 2.8C4.5 2.8 4.4 0.4 3 0.4"),
    ("l", "M1.7 1.2C0.9 0.8 0.8 2.2 1.6 2.1M4.3 1.2C5.1 0.8 5.2 2.2 4.4 2.1"),
    ("o", "M3 2.8C3.3 4.4 3.3 5.4 3 6.4"), ("o", "M3 3.6C1.6 4 1.2 5 1.6 6.2"), ("o", "M3 3.6C4.4 4 4.8 5 4.4 6.2"),
    ("o", "M3 6.4C2.4 7.4 2.2 8.2 2.4 9"), ("o", "M3 6.4C3.6 7.4 3.8 8.2 3.6 9"),
    ("f", circle(2.5, 1.4, 0.18)), ("f", circle(3.5, 1.4, 0.18))]
G["birdman"] = [
    ("o", circle(3.2, 1.4, 0.9)), ("l", "M3.9 1C5 1.2 5.6 2 5.4 2.6C4.9 2.1 4.3 1.9 3.9 1.9"),
    ("o", "M3 2.3C2.5 4 2.6 5.2 3 6.4"), ("o", "M2.8 3.2C1.4 3 0.8 3.8 0.9 5.2"),
    ("o", "M3 3.4C4.2 3.8 4.8 4.4 4.6 5.6"), ("o", "M3 6.4C2.2 7.2 2 8 2.2 9"),
    ("o", "M3 6.4C3.4 7.4 4 8 4.6 8.4"), ("l", "M0.9 5.2L0.5 5.9M0.9 5.2L1.2 5.9"), ("f", circle(3.4, 1.2, 0.18))]
G["frigatebird"] = [
    ("o", circle(3, 1.5, 0.8)), ("l", "M3.7 1.3C4.8 1.2 5.4 1.8 5 2.4"), ("l", "M3.4 2.2C3.9 2.9 3.4 3.3 3 3"),
    ("o", "M3 3C1.6 2.2 0.4 2.8 0.2 4.6"), ("o", "M3 3C4.4 2.2 5.6 2.8 5.8 4.6"),
    ("l", "M0.6 3.7L0.1 3.1M1.2 3.1L0.9 2.4M1.9 2.8L1.8 2.1M5.4 3.7L5.9 3.1M4.8 3.1L5.1 2.4M4.1 2.8L4.2 2.1"),
    ("o", "M3 3C2.7 4.6 2.7 5.6 3 6.6"), ("o", "M3 6.6C2.4 7.6 1.8 8.4 1.6 9"), ("o", "M3 6.6C3.6 7.6 4.2 8.4 4.4 9"),
    ("f", circle(3.2, 1.3, 0.17))]
G["tern"] = [
    ("o", "M2 2.2C3.6 1.4 4.6 2.6 4.2 3.8C3.8 5.2 4.6 6.2 3.8 7.1C3 7.9 1.8 7.5 1.6 6.3C1.4 5.1 2.2 4.1 2 2.2"),
    ("o", circle(2.2, 1.4, 0.8)), ("l", "M1.5 1.1L0.1 0.8L1.5 1.7"), ("l", "M2.4 3.8C3.2 4.4 3.4 5.4 3.2 6.4"),
    ("l", "M2.6 7.5L2.4 9M3.4 7.4L3.6 9M2.4 9L1.9 9M3.6 9L4.2 9"), ("f", circle(2, 1.3, 0.17))]
G["tern with fish"] = G["tern"] + [("o", "M0.2 1.6C0.6 2.6 0.6 3.6 0.3 4.4"), ("l", "M0.3 4.4L0 4.9M0.3 4.4L0.7 4.9")]
G["fish"] = [
    ("o", "M3 0.3C5 1.6 5 5 3 7C1 5 1 1.6 3 0.3Z"), ("o", "M3 7C2.2 7.8 1.6 8.4 1.2 9"), ("o", "M3 7C3.8 7.8 4.4 8.4 4.8 9"),
    ("l", "M1.6 3.4L0.6 4.4M4.4 3.4L5.4 4.4"), ("l", "M2 2.6C2.6 3.2 3.4 3.2 4 2.6"), ("l", "M3 3.6L3 6"),
    ("f", circle(3, 1.6, 0.25))]
G["turtle"] = [
    ("o", ellipse(3, 4.6, 2.1, 2.7)), ("o", circle(3, 1.1, 0.6)),
    ("o", "M1.3 3C0.6 2.6 0.2 2 0.2 1.4"), ("o", "M4.7 3C5.4 2.6 5.8 2 5.8 1.4"),
    ("o", "M1.3 6.3C0.6 6.8 0.3 7.4 0.3 8"), ("o", "M4.7 6.3C5.4 6.8 5.7 7.4 5.7 8"),
    ("l", "M3 2L3 7.3M1.3 3.8C2.2 4.2 3.8 4.2 4.7 3.8M1.3 5.5C2.2 5.1 3.8 5.1 4.7 5.5"), ("l", "M3 7.3L3 8.4")]
G["lizard"] = [
    ("o", circle(3, 0.9, 0.6)), ("o", "M3 1.5C2 3 4 4.4 3 6C2.4 7 3 8 3.6 9"),
    ("o", "M2.8 2.6C2 2.2 1.4 2.6 1 1.8"), ("o", "M3.4 2.8C4.2 2.4 4.8 2.8 5.2 2"),
    ("o", "M3.1 5.4C2.2 5.6 1.6 6.2 1.2 5.6"), ("o", "M3.2 5.6C4 6 4.6 6.4 5 6"),
    ("l", "M1 1.8L0.6 1.4M1 1.8L0.8 1.2M5.2 2L5.6 1.6M5.2 2L5.1 1.4M1.2 5.6L0.7 5.5M5 6L5.5 6.1")]
G["crescent"] = [("o", "M4.6 0.8C1.2 1.6 1 7.4 4.6 8.2"), ("l", "M4.6 0.8C3.2 2.6 3.2 6.4 4.6 8.2"),
                 ("f", circle(4.5, 4.5, 0.3)), ("l", "M4.8 4.5L5.8 4.5")]
G["plant"] = [
    ("o", "M3 9C2.6 6 3.4 3 3 0.4"),
    ("l", "M3 1.6C2 1.2 1.4 1.6 1 0.8M3 1.6C4 1.2 4.6 1.6 5 0.8M3 3.6C1.8 3.2 1.2 3.6 0.8 2.6M3 3.6C4.2 3.2 4.8 3.6 5.2 2.6"
          "M3 5.6C2 5.2 1.4 5.6 1 4.8M3 5.6C4 5.2 4.6 5.6 5 4.8M3 7.4C2.2 7.2 1.8 7.4 1.4 6.8M3 7.4C3.8 7.2 4.2 7.4 4.6 6.8")]
G["face with tears"] = [
    ("o", "M3 0.6C0.8 0.6 0.8 5 3 5C5.2 5 5.2 0.6 3 0.6"), ("f", circle(2.2, 2.2, 0.3)), ("f", circle(3.8, 2.2, 0.3)),
    ("l", "M2.2 2.8L2 4.4M3.8 2.8L4 4.4M2.4 3.9C2.8 4.2 3.2 4.2 3.6 3.9"),
    ("o", "M3 5L3 7.4"), ("o", "M3 7.4C2.4 8 2.2 8.6 2.2 9"), ("o", "M3 7.4C3.6 8 3.8 8.6 3.8 9")]
G["hand"] = [
    ("o", "M3 9C2.6 7 3.2 5 3 3.6"),
    ("l", "M3 3.6C2 2.8 1.4 1.8 1.2 0.8M3 3.6C2.6 2.4 2.4 1.2 2.4 0.2M3 3.6C3.4 2.4 3.6 1.2 3.6 0.2"
          "M3 3.6C4 2.8 4.6 1.8 4.8 0.8M3 4.4C4 4.4 5 3.8 5.4 3"), ("l", "M2.4 6L3.6 6M2.4 6.6L3.6 6.6")]
G["seated figure with staff"] = [
    ("o", circle(2.2, 1.3, 0.8)), ("o", "M2.2 2.1C2 3.6 2.2 4.6 2.6 5.4"),
    ("o", "M2.6 5.4C3.6 5.6 4.2 6.2 4 7C3.8 7.8 4 8.4 4.2 9"), ("o", "M2.6 5.4C1.6 6 1.2 7.2 1.6 9"),
    ("o", "M2.2 3C3.4 3.2 4 2.6 4.6 1.8"), ("l", "M4.9 0.2C4.5 3 4.7 6 5.1 9M4.4 0.5L5.4 0.1"), ("f", circle(2, 1.2, 0.17))]
G["figure leg raised"] = [
    ("o", circle(2.6, 1.3, 0.8)), ("o", "M2.6 2.1C2.4 3.6 2.6 4.8 2.8 6"),
    ("o", "M2.6 3C1.4 3.6 1 2.8 0.8 1.6"), ("o", "M2.7 3.2C3.8 3.8 4.6 3.6 5.2 2.6"),
    ("o", "M2.8 6C2.4 7 2 8 2.2 9"), ("o", "M2.8 6C3.8 6.2 4.8 5.6 5 4.4"), ("f", circle(2.8, 1.2, 0.17))]
G["oval"] = [("o", "M3 0.6C0.8 2 0.8 7 3 8.4C5.2 7 5.2 2 3 0.6"), ("l", "M3 2.2L3 6.8"),
             ("f", circle(3, 1.6, 0.22)), ("f", circle(3, 7.4, 0.22))]
G["coil"] = [("o", "M3 4.6C3.6 4.6 3.6 3.8 3 3.8C2 3.8 2 5.4 3 5.4C4.4 5.4 4.4 3 3 3C1.2 3 1.2 6.2 3 6.2"
                   "C5.2 6.2 5.2 2.2 3 2.2"), ("l", "M3 6.2L3 9M3 2.2L3 0.4")]
G["fishhook"] = [("o", "M4 0.6C4 3 4.4 6 3.6 7.6C2.8 9 1 8.6 1 7C1 6 1.6 5.6 2.2 6"), ("l", "M2.2 6L1.7 5.1"),
                 ("l", "M3.4 0.6L4.6 0.6M4 0.6L4 0")]
G["paddle"] = [("o", "M3 4C1.4 5 1.4 8 3 9C4.6 8 4.6 5 3 4"), ("o", "M3 4L3 0.8"), ("l", "M2 1.2L4 1.2"),
               ("l", "M3 5L3 8M2.3 6.4L3.7 6.4")]
G["star"] = [("o", "M3 0.4C3.4 3 3.6 3.6 6 4.5C3.6 5.4 3.4 6 3 8.6C2.6 6 2.4 5.4 0 4.5C2.4 3.6 2.6 3 3 0.4Z"),
             ("f", circle(3, 4.5, 0.3))]
G["egg with rays"] = [("o", ellipse(3, 4.8, 1.6, 2.2)), ("f", circle(3, 4.8, 0.35)),
                      ("l", "M3 2L3 0.4M1.6 3L0.6 1.8M4.4 3L5.4 1.8M1.4 6.4L0.4 7.4M4.6 6.4L5.6 7.4M3 7L3 9")]
G["two heads"] = [
    ("o", circle(1.7, 1.3, 0.8)), ("o", circle(4.3, 1.3, 0.8)), ("o", "M1.7 2.1C2 3 2.6 3.4 3 3.4C3.4 3.4 4 3 4.3 2.1"),
    ("o", "M3 3.4C2.8 4.8 2.8 5.6 3 6.6"), ("o", "M3 4.2C1.8 4.6 1.2 5.4 1 6.4"), ("o", "M3 4.2C4.2 4.6 4.8 5.4 5 6.4"),
    ("o", "M3 6.6C2.4 7.4 2.2 8.2 2.2 9"), ("o", "M3 6.6C3.6 7.4 3.8 8.2 3.8 9"),
    ("f", circle(1.7, 1.2, 0.16)), ("f", circle(4.3, 1.2, 0.16))]
G["figure with fan"] = [
    ("o", circle(2.4, 1.6, 0.8)), ("o", "M2.4 2.4C2.2 4 2.4 5 2.6 6.2"), ("o", "M2.4 3.4C3.4 3.2 4 2.6 4.2 1.8"),
    ("o", "M2.4 3.6C1.4 4.2 1 5 1.2 6"), ("o", "M2.6 6.2C2 7.2 1.8 8.2 2 9"), ("o", "M2.6 6.2C3.2 7.2 3.4 8.2 3.2 9"),
    ("l", "M4.2 1.8L3.6 0.2M4.2 1.8L4.4 0.1M4.2 1.8L5.2 0.4M4.2 1.8L5.8 1.2M3.6 0.2C4.4 -0.1 5.4 0.4 5.8 1.2"),
    ("f", circle(2.6, 1.5, 0.17))]
G["crab"] = [
    ("o", ellipse(3, 5, 1.8, 1.3)), ("o", "M1.6 4.2C1 3.4 1 2.4 1.6 1.6"), ("o", "M4.4 4.2C5 3.4 5 2.4 4.4 1.6"),
    ("l", "M1.6 1.6L1 1M1.6 1.6L2.2 1.1M4.4 1.6L5 1M4.4 1.6L3.8 1.1"),
    ("l", "M1.4 5.6L0.4 6.4L0.4 7.4M1.8 6.1L1.2 7.2L1.4 8.2M4.6 5.6L5.6 6.4L5.6 7.4M4.2 6.1L4.8 7.2L4.6 8.2"),
    ("f", circle(2.4, 4.8, 0.2)), ("f", circle(3.6, 4.8, 0.2))]
G["waves"] = [("o", "M0.4 2.4C1.4 0.8 2 4 3 2.4C4 0.8 4.6 4 5.6 2.4"),
              ("o", "M0.4 5C1.4 3.4 2 6.6 3 5C4 3.4 4.6 6.6 5.6 5"),
              ("l", "M0.4 7.6C1.4 6 2 9.2 3 7.6C4 6 4.6 9.2 5.6 7.6")]
G["feather wand"] = [
    ("o", "M3 9C3.2 6 2.8 3 3 0.6"),
    ("l", "M3 0.8C2 1 1.6 1.6 1.4 2.2M3 0.8C4 1 4.4 1.6 4.6 2.2M3 1.8C1.8 2 1.4 2.8 1.2 3.4M3 1.8C4.2 2 4.6 2.8 4.8 3.4"
          "M3 2.8C2 3 1.6 3.8 1.6 4.4M3 2.8C4 3 4.4 3.8 4.4 4.4"), ("f", circle(3, 6.4, 0.35))]
G["arch"] = [("o", "M0.6 9C0.6 2 5.4 2 5.4 9"), ("l", "M1.8 9C1.8 4.2 4.2 4.2 4.2 9"),
             ("f", circle(3, 3, 0.3)), ("f", circle(3, 6.6, 0.3))]
G["long-eared figure"] = [
    ("o", "M3 0.4C1.8 0.4 1.8 2.6 3 2.6C4.2 2.6 4.2 0.4 3 0.4"),
    ("o", "M2 1.4C1.2 1.6 1.2 3 1.4 4"), ("o", "M4 1.4C4.8 1.6 4.8 3 4.6 4"),
    ("o", "M3 2.6C3.2 4.2 3.2 5.4 3 6.4"), ("o", "M3 3.6C2.2 4.6 2.2 5.4 2.6 6"), ("o", "M3 3.6C3.8 4.6 3.8 5.4 3.4 6"),
    ("o", "M3 6.4C2.4 7.4 2.2 8.2 2.4 9"), ("o", "M3 6.4C3.6 7.4 3.8 8.2 3.6 9"),
    ("f", circle(2.6, 1.4, 0.16)), ("f", circle(3.4, 1.4, 0.16))]
G["shark"] = [
    ("o", "M0.6 4.6C1.6 2.6 4.4 2.6 5.6 4.2C4.4 5.8 1.6 6 0.6 4.6"), ("o", "M2.8 3C3 2 3.6 1.4 4.2 1.2"),
    ("o", "M0.6 4.6C0.2 3.6 0.2 3 0.4 2.4"), ("o", "M0.6 4.6C0.2 5.6 0.2 6.2 0.4 6.8"),
    ("l", "M4.4 4.8L5.2 4.6M3.6 4L3.6 5M3.2 4L3.2 5"), ("f", circle(4.8, 4, 0.18))]
G["rope"] = [("o", "M3 0.4C1.6 1.4 4.4 2.4 3 3.4C1.6 4.4 4.4 5.4 3 6.4C1.6 7.4 4.4 8.2 3 9"),
             ("l", "M2.2 1.4L3.8 1.4M2.2 3.4L3.8 3.4M2.2 5.4L3.8 5.4M2.2 7.4L3.8 7.4")]
GLYPHS = G


def glyph_svg(parts, fg, bg, scale):
    """Outlined strokes first (wide fg, then narrow bg on top), then lines and dots."""
    out_w = (2 * LINE + OUTLINE_GAP) / scale
    gap_w = OUTLINE_GAP / scale
    line_w = LINE / scale
    o = [d for k, d in parts if k == "o"]
    svg = "".join(f'<path d="{d}" stroke="{fg}" stroke-width="{out_w:.3f}"/>' for d in o)
    svg += "".join(f'<path d="{d}" stroke="{bg}" stroke-width="{gap_w:.3f}"/>' for d in o)
    svg += "".join(f'<path d="{d}" stroke="{fg}" stroke-width="{line_w:.3f}"/>' for k, d in parts if k == "l")
    svg += "".join(f'<path d="{d}" fill="{fg}" stroke="none"/>' for k, d in parts if k == "f")
    return svg


def load_keys():
    d = json.load(open(os.path.join(HERE, "layout_e_keys.json"), encoding="utf-8"))
    return d["keys"], d["cut"]


def half_outline(half, cut, width_u, rows=5, m=MARGIN):
    """Plate outline in mm, y down; the split line is a staircase with no margin."""
    stairs = []
    for i, r in enumerate("ntcsb"[:rows]):
        x = cut[r] * U
        y0 = i * U - (m if i == 0 else 0)
        y1 = (i + 1) * U + (m if i == rows - 1 else 0)
        stairs += [(x, y0), (x, y1)]
    if half == "left":
        return [(-m, -m)] + stairs + [(-m, rows * U + m)]
    xr = width_u * U + m
    return [(xr, -m), (xr, rows * U + m)] + stairs[::-1]


def cutout(cx, cy):
    """The split72 plate cut-out around a switch centre, y down (back = smaller y)."""
    h = 7.0
    pts = [(-h, -h), (-2.5, -h), (-2.5, -h - 0.66), (2.5, -h - 0.66), (2.5, -h), (h, -h),
           (h, -6), (h + 0.8, -6), (h + 0.8, 6), (h, 6), (h, h), (-h, h),
           (-h, 6), (-h - 0.8, 6), (-h - 0.8, -6), (-h, -6)]
    return [(cx + x, cy + y) for x, y in pts]


def path(poly):
    return "M" + "L".join(f"{x:.3f},{y:.3f}" for x, y in poly) + "Z"


def main():
    keys, cut = load_keys()
    width_u = max(k["x"] + k["w"] for k in keys)
    holes = {"left": [], "right": []}
    for k in keys:
        holes[k["half"]].append(cutout((k["x"] + k["w"] / 2) * U, (k["row"] + 0.5) * U))
    plate = {h: path(half_outline(h, cut, width_u)) + "".join(path(c) for c in holes[h])
             for h in ("left", "right")}

    # glyph lines over the whole plate, regardless of the keys: the holes cut through
    # them. The lines run across both halves: one tablet when the halves are joined.
    FG, BG = "#ece8dc", "#121314"
    rnd = random.Random(7)
    names = list(GLYPHS)
    gw, gh = GLYPH_W * SCALE, GLYPH_H * SCALE
    x0, x1 = -MARGIN + 0.6, width_u * U + MARGIN - 0.6
    top, bot = -MARGIN + 0.8, 5 * U + MARGIN - 0.8
    nlines = int(round((bot - top - gh) / PITCH_Y)) + 1      # spread evenly over the height
    pitch = (bot - top - gh) / (nlines - 1)
    y = top
    lines, n = [], 0
    while n < nlines:
        x = x0
        flip = n % 2 == 1                          # reverse boustrophedon
        while x + gw <= x1:
            g = names[rnd.randrange(len(names))]
            tr = f"translate({x:.2f},{y:.2f}) scale({SCALE})"
            if flip:
                tr += f" rotate(180 {GLYPH_W / 2} {GLYPH_H / 2})"
            lines.append(f'<g transform="{tr}">{glyph_svg(GLYPHS[g], FG, BG, SCALE)}</g>')
            x += PITCH_X * SCALE
        y += pitch
        n += 1

    vx, vy = -MARGIN - 6, -MARGIN - 14
    vw, vh = width_u * U + 2 * MARGIN + 12, 5 * U + 2 * MARGIN + 22
    clip = "".join(f'<clipPath id="c{h}"><path clip-rule="evenodd" d="{plate[h]}"/></clipPath>'
                   for h in plate)
    body = []
    for h in plate:
        body.append(f'<path fill="#121314" fill-rule="evenodd" d="{plate[h]}"/>')
        body.append(f'<g clip-path="url(#c{h})" fill="none" '
                    f'stroke-linecap="round" stroke-linejoin="round">{"".join(lines)}</g>')
        body.append(f'<path fill="none" stroke="#555" stroke-width="0.15" fill-rule="evenodd" d="{plate[h]}"/>')
    title = (f'<text x="{-MARGIN}" y="{-MARGIN - 6}" font-family="sans-serif" font-size="5" fill="#222">'
             f'Layout E plate, Rongorongo-style glyph lines (own simplified drawings, not from a tablet), '
             f'{len(GLYPHS)} glyphs, {n} lines, {LINE} mm silk lines</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw}mm" height="{vh}mm" '
           f'viewBox="{vx} {vy} {vw} {vh}"><defs>{clip}</defs>'
           f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="#d9d9d6"/>{title}{"".join(body)}</svg>')
    open(os.path.join(HERE, "plate_rongorongo.svg"), "w", encoding="utf-8").write(svg)

    # glyph sheet: each glyph large, for review
    cells, cols = [], 10
    for i, (name, parts) in enumerate(GLYPHS.items()):
        cx, cy = (i % cols) * 16, (i // cols) * 22
        cells.append(f'<g transform="translate({cx + 4.4},{cy + 2}) scale({SCALE})" fill="none" '
                     f'stroke-linecap="round" stroke-linejoin="round">{glyph_svg(parts, "#111", "#fff", SCALE)}</g>'
                     f'<text x="{cx + 8}" y="{cy + 16.5}" font-size="1.7" font-family="sans-serif" '
                     f'text-anchor="middle" fill="#444">{name}</text>')
    rows = (len(GLYPHS) + cols - 1) // cols
    sheet = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{cols * 160}" height="{rows * 220}" '
             f'viewBox="0 0 {cols * 16} {rows * 22}"><rect width="{cols * 16}" height="{rows * 22}" fill="#fff"/>'
             f'{"".join(cells)}</svg>')
    open(os.path.join(HERE, "rongorongo_glyphs.svg"), "w", encoding="utf-8").write(sheet)
    print(f"{n} lines, {len(lines)} glyphs placed, {sum(len(v) for v in holes.values())} cut-outs")


if __name__ == "__main__":
    main()
