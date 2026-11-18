#!/usr/bin/env python3
"""Plate artwork proposal for layout E: Rongorongo-style glyph lines on the plate,
with the switch cut-outs of the split72 plate.

    python3 plate_rongorongo.py

Writes plate_rongorongo.svg (1 unit = 1 mm). The glyphs are simplified drawings in
the Rongorongo manner (figures, birds, fish, turtle, plants, crescent), drawn for
this proposal. They are NOT copied from a tablet; a production version should trace
real glyphs from a source with a free licence. One line of glyphs runs in each visible strip of plate
(the border and the gaps between key rows; glyph height 3.7 to 5.6 mm), in reverse
boustrophedon: every second line is turned 180 degrees, as on the tablets.

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
STROKE = 0.25                # silkscreen line width, mm (JLC minimum 0.15)
GLYPH_W, GLYPH_H = 6.0, 8.0  # glyph box, mm
PITCH_X = 6.6                # glyph spacing along a line

# Each glyph: SVG path data in a 6 x 8 mm box, y down, standing on y = 8.
def circle(cx, cy, r):
    return f"M{cx - r},{cy} a{r},{r} 0 1 0 {2 * r},0 a{r},{r} 0 1 0 {-2 * r},0"


GLYPHS = {
    "figure arms up": circle(3, 1.4, 1.1) + "M3 2.5L3 5.5M3 3.2L1 2L0.8 0.6M3 3.2L5 2L5.2 0.6"
                      "M3 5.5L1.6 8M3 5.5L4.4 8",
    "figure with staff": circle(2.6, 1.4, 1.1) + "M2.6 2.5L2.8 5.6M2.7 3.3L5 3L5.6 1.8"
                         "M2.7 3.3L1 4.5M2.8 5.6L1.8 8M2.8 5.6L4 7.2L4.6 8",
    "frigatebird": circle(3, 1.6, 0.9) + "M3.8 1.4L5.4 2.2L3.9 2M3 2.6Q0.4 2.2 0.3 5M3 2.6Q5.6 2.2 5.7 5"
                   "M3 2.6L3 6.2M3 6.2L2 8M3 6.2L4 8",
    "seated bird": circle(2, 1.5, 0.9) + "M2.8 1.3L4.4 1.8L2.8 1.9M1.8 2.4Q0.6 5 2 6.4Q4.2 6.8 5.2 5.6"
                   "Q3.8 5 2.6 3M2.4 6.6L2 8M3.4 6.6L3.8 8",
    "fish": "M3 0.3Q5.4 3 3 6.6Q0.6 3 3 0.3ZM3 6.6L1.6 8L4.4 8ZM1.8 3.6L4.2 3.6" + circle(3, 1.8, 0.3),
    "turtle": "M0.8 4a2.2 2.8 0 1 0 4.4 0a2.2 2.8 0 1 0 -4.4 0" + circle(3, 0.7, 0.6)
              + "M1 2.6L0 1.6M5 2.6L6 1.6M1 5.6L0 6.6M5 5.6L6 6.6M3 1.5L3 6.5",
    "crescent": "M4.6 0.6A3.6 3.6 0 1 0 4.6 7.4A2.8 3.4 0 1 1 4.6 0.6Z",
    "plant": "M3 8L3 0.4M3 2L1.2 1M3 2L4.8 1M3 4L1 3M3 4L5 3M3 6L1.2 5M3 6L4.8 5",
    "seated figure": circle(2.4, 1.4, 1) + "M2.4 2.4L2.6 5.2M2.5 3.2L4.6 3.8L5 2.4"
                     "M2.6 5.2L4.4 5.6L4.2 8M2.6 5.2L1.4 6.6L1.8 8",
    "head with ears": "M1.6 3Q1.6 0.4 3 0.4Q4.4 0.4 4.4 3Q4.4 4.6 3 4.6Q1.6 4.6 1.6 3Z"
                      + circle(1.1, 2.4, 0.5) + circle(4.9, 2.4, 0.5) + "M3 4.6L3 8M3 5.6L1 6.8M3 5.6L5 6.8",
    "lizard": circle(3, 0.6, 0.5) + "M3 1.1Q2.2 3 3 4.4Q3.8 6 3 8M2.8 2.4L1.2 1.6M3 2.4L4.8 1.6"
              "M3.1 5.4L1.4 6.4M3.1 5.4L4.8 6.4",
    "star": "M3 0.6L3.7 3.3L6 4L3.7 4.7L3 7.4L2.3 4.7L0 4L2.3 3.3Z",
    "staff": circle(3, 1.4, 1) + "M3 8L3 2.4M1.6 4.6L4.4 4.6M1.6 6L4.4 6",
    "twin figures": circle(1.6, 1.4, 0.8) + circle(4.4, 1.4, 0.8) + "M1.6 2.2L1.6 5.4M4.4 2.2L4.4 5.4"
                    "M1.6 3.4L4.4 3.4M1.6 5.4L1 8M4.4 5.4L5 8M1.6 5.4L2.4 8M4.4 5.4L3.6 8",
    "hand": "M3 8L3 4M3 4L1.2 0.8M3 4L2.2 0.4M3 4L3.8 0.4M3 4L4.8 0.8M1.6 3Q3 5.6 4.4 3",
}


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

    # one glyph line per visible strip of plate: the border above the top row, the 5 mm
    # gaps between key rows (less the 0.66 mm notch of the row below) and the border
    # below the bottom row. The lines run across both halves: one tablet when joined.
    strips = [(-MARGIN, 0.5 * U - 7.66)]
    strips += [((i + 0.5) * U + 7.0, (i + 1.5) * U - 7.66) for i in range(4)]
    strips += [(4.5 * U + 7.0, 5 * U + MARGIN)]
    rnd = random.Random(7)
    names = list(GLYPHS)
    x0, x1 = -MARGIN + 0.8, width_u * U + MARGIN - 0.8
    lines, n = [], 0
    for top, bot in strips:
        h = min(bot - top - 0.7, 5.6)              # glyph height, 0.35 mm clear above and below
        sc = h / GLYPH_H
        y = (top + bot) / 2 - h / 2
        x = x0
        flip = n % 2 == 1                          # reverse boustrophedon
        while x + GLYPH_W * sc <= x1:
            g = names[rnd.randrange(len(names))]
            tr = f"translate({x:.2f},{y:.2f}) scale({sc:.4f})"
            if flip:
                tr += f" rotate(180 {GLYPH_W / 2} {GLYPH_H / 2})"
            lines.append(f'<path transform="{tr}" stroke-width="{STROKE / sc:.4f}" d="{GLYPHS[g]}"/>')
            x += PITCH_X * sc
        n += 1

    vx, vy = -MARGIN - 6, -MARGIN - 14
    vw, vh = width_u * U + 2 * MARGIN + 12, 5 * U + 2 * MARGIN + 22
    clip = "".join(f'<clipPath id="c{h}"><path clip-rule="evenodd" d="{plate[h]}"/></clipPath>'
                   for h in plate)
    body = []
    for h in plate:
        body.append(f'<path fill="#121314" fill-rule="evenodd" d="{plate[h]}"/>')
        body.append(f'<g clip-path="url(#c{h})" fill="none" stroke="#ece8dc" '
                    f'stroke-linecap="round" stroke-linejoin="round">{"".join(lines)}</g>')
        body.append(f'<path fill="none" stroke="#555" stroke-width="0.15" fill-rule="evenodd" d="{plate[h]}"/>')
    title = (f'<text x="{-MARGIN}" y="{-MARGIN - 6}" font-family="sans-serif" font-size="5" fill="#222">'
             f'Layout E plate, Rongorongo-style glyph lines (own simplified drawings, not from a tablet), '
             f'{len(GLYPHS)} glyphs, {n} lines, 0.25 mm silk</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw * 8:.0f}" height="{vh * 8:.0f}" '
           f'viewBox="{vx} {vy} {vw} {vh}"><defs>{clip}</defs>'
           f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="#d9d9d6"/>{title}{"".join(body)}</svg>')
    open(os.path.join(HERE, "plate_rongorongo.svg"), "w").write(svg)

    # glyph sheet: each glyph large, for review
    cells = []
    for i, (name, d) in enumerate(GLYPHS.items()):
        cx, cy = (i % 8) * 16, (i // 8) * 20
        cells.append(f'<g transform="translate({cx + 5},{cy + 2})"><path d="{d}" fill="none" stroke="#111" '
                     f'stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round"/></g>'
                     f'<text x="{cx + 8}" y="{cy + 14}" font-size="1.9" font-family="sans-serif" '
                     f'text-anchor="middle" fill="#444">{name}</text>')
    sheet = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="400" viewBox="0 0 128 40">'
             f'<rect width="128" height="40" fill="#fff"/>{"".join(cells)}</svg>')
    open(os.path.join(HERE, "rongorongo_glyphs.svg"), "w").write(sheet)
    print(f"{n} lines, {len(lines)} glyphs placed, {sum(len(v) for v in holes.values())} cut-outs")


if __name__ == "__main__":
    main()
