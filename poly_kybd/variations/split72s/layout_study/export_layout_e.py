#!/usr/bin/env python3
"""Save layout E (universal 65 %, 72 keys) in formats other tools read.

    python3 export_layout_e.py

Writes, next to this script:
- layout_e.kle.json   raw data for keyboard-layout-editor.com (Raw data tab)
- layout_e.qmk.json   a QMK `layouts` entry with a 6x7 matrix per half
                      (rows 0-5 left, 6-11 right)
- layout_e_keys.json  every key with position, width, half, legend, for the renderer
- layout_e_legends.png  one 72x40 legend cell per key (white on black), for the renderer
- numpad_n1.kle.json, numpad_n1.qmk.json  the 20-key number block N1, 5x4 matrix
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

import tkl_layouts as t

HERE = os.path.dirname(os.path.abspath(__file__))
E = next(l for l in t.COMPACT if l["name"].startswith("E:"))
ROWS_PER_SIDE, COLS = 6, 7

# what the render shows on a key whose role depends on the language (US English)
RENDER_LEGEND = {"Esc|`": "Esc", "\\|Enter": "\\", "#|Enter": "#", "<|Shift": "<",
                 "#|ろ|/?": "#", "無変換|Fn": "Fn", "変換|Fn": "Fn", "←": "◀", "↓": "▼",
                 "→": "▶", "↑": "▲"}


def keys():
    out = []
    order = "ntcsb"
    for r, x, w, lab in t.place(E):
        out.append({"row": order.index(r), "x": x, "w": w, "label": lab,
                    "half": "left" if x < t.CUT[r] else "right",
                    "legend": RENDER_LEGEND.get(lab, lab.split("|")[0])})
    out.sort(key=lambda k: (k["row"], k["x"]))
    return out


def assign_matrix(ks):
    """Matrix rows follow the physical rows; keys past column 7 go to matrix row 5."""
    for half, base in (("left", 0), ("right", ROWS_PER_SIDE)):
        spill = []
        for row in range(5):
            rk = [k for k in ks if k["half"] == half and k["row"] == row]
            for c, k in enumerate(rk[:COLS]):
                k["matrix"] = [base + row, c]
            spill += rk[COLS:]
        if len(spill) > COLS:
            raise SystemExit(f"{half}: {len(spill)} keys do not fit matrix row 5")
        for c, k in enumerate(spill):
            k["matrix"] = [base + 5, c]
    used = [tuple(k["matrix"]) for k in ks]
    assert len(used) == len(set(used)), "matrix position used twice"


def kle(ks, name="PolyKybd layout E (universal 65 %)"):
    rows = []
    for row in range(5):
        rk = [k for k in ks if k["row"] == row]
        line, x = [], 0.0
        for k in rk:
            props = {}
            if abs(k["x"] - x) > 1e-9:
                props["x"] = round(k["x"] - x, 4)
            if k["w"] != 1:
                props["w"] = k["w"]
            if props:
                line.append(props)
            line.append(k["label"].replace("|", "\n"))
            x = k["x"] + k["w"]
        rows.append(line)
    return [{"name": name}] + rows


def legends(ks, path):
    cw, ch = 72, 40
    img = Image.new("L", (cw * len(ks), ch), 0)
    d = ImageDraw.Draw(img)
    for i, k in enumerate(ks):
        txt = k["legend"]
        size = 26 if len(txt) == 1 else (17 if len(txt) <= 4 else 13)
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        bx = d.textbbox((0, 0), txt, font=f)
        d.text((i * cw + (cw - bx[2] - bx[0]) / 2, (ch - bx[3] - bx[1]) / 2), txt, fill=255, font=f)
        k["cell"] = i
    img.save(path)


def export_numpad():
    n1 = next(l for l in t.NUMPAD if l["name"].startswith("N1:"))
    order = "ntcsb"
    ks = [{"row": order.index(r), "x": x, "w": w, "label": lab}
          for r, x, w, lab in t.place(n1)]
    ks.sort(key=lambda k: (k["row"], k["x"]))
    for row in range(5):
        for c, k in enumerate([k for k in ks if k["row"] == row]):
            k["matrix"] = [row, c]
    json.dump(kle(ks, "PolyKybd number block N1"), open(os.path.join(HERE, "numpad_n1.kle.json"), "w"), ensure_ascii=False, indent=1)
    qmk = {"matrix_size": {"rows": 5, "cols": 4},
           "layouts": {"LAYOUT_numpad20": {"layout": [
               {"label": k["label"], "matrix": k["matrix"], "x": k["x"], "y": k["row"],
                **({"w": k["w"]} if k["w"] != 1 else {})} for k in ks]}}}
    json.dump(qmk, open(os.path.join(HERE, "numpad_n1.qmk.json"), "w"), ensure_ascii=False, indent=1)
    print("numpad", len(ks), "keys")


def main():
    ks = keys()
    assign_matrix(ks)
    legends(ks, os.path.join(HERE, "layout_e_legends.png"))
    json.dump(kle(ks), open(os.path.join(HERE, "layout_e.kle.json"), "w"), ensure_ascii=False, indent=1)
    qmk = {"matrix_size": {"rows": 2 * ROWS_PER_SIDE, "cols": COLS},
           "layouts": {"LAYOUT_universal65": {"layout": [
               {"label": k["label"], "matrix": k["matrix"], "x": k["x"], "y": k["row"],
                **({"w": k["w"]} if k["w"] != 1 else {})} for k in ks]}}}
    json.dump(qmk, open(os.path.join(HERE, "layout_e.qmk.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({"cut": t.CUT, "pitch_mm": 19.05, "cell": [72, 40], "keys": ks},
              open(os.path.join(HERE, "layout_e_keys.json"), "w"), ensure_ascii=False, indent=1)
    for half in ("left", "right"):
        hk = [k for k in ks if k["half"] == half]
        print(half, len(hk), "keys; matrix rows used:", sorted({k["matrix"][0] for k in hk}))
    export_numpad()


if __name__ == "__main__":
    main()
