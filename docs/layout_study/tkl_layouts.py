#!/usr/bin/env python3
"""TKL layout study for a PolyKybd with 1, 1.25, 1.5 and 2U keys only.

Each row is a list of (width, label) or ("gap", width). The script checks that every
main-block row is 15U wide, counts keys per half for the split, and writes an SVG.
"""
import sys

ALLOWED = {1.0, 1.25, 1.5, 2.0}
U = 46          # px per unit
PAD = 0.4       # unit padding around a board

# main-block row y positions (U); nav cluster at x = 15.25
Y = {"f": 0, "n": 1.25, "t": 2.25, "c": 3.25, "s": 4.25, "b": 5.25}
NAV_X = 15.25

def nav(rows):
    """Standard TKL nav cluster, all 1U, all on the right half."""
    return [
        ("f", NAV_X, ["PrtSc", "ScrLk", "Pause"]),
        ("n", NAV_X, ["Ins", "Home", "PgUp"]),
        ("t", NAV_X, ["Del", "End", "PgDn"]),
        ("s", NAV_X + 1, ["↑"]),
        ("b", NAV_X, ["←", "↓", "→"]),
    ]

F_ROW = [(1, "Esc"), ("gap", 1), (1, "F1"), (1, "F2"), (1, "F3"), (1, "F4"), ("gap", .5),
         (1, "F5"), (1, "F6"), (1, "F7"), (1, "F8"), ("gap", .5),
         (1, "F9"), (1, "F10"), (1, "F11"), (1, "F12")]
NUM = [(1, "`"), (1, "1"), (1, "2"), (1, "3"), (1, "4"), (1, "5"), (1, "6"),
       (1, "7"), (1, "8"), (1, "9"), (1, "0"), (1, "-"), (1, "=")]
TAB = [(1, "Q"), (1, "W"), (1, "E"), (1, "R"), (1, "T"), (1, "Y"), (1, "U"), (1, "I"),
       (1, "O"), (1, "P"), (1, "["), (1, "]")]
CAPS = [(1, "A"), (1, "S"), (1, "D"), (1, "F"), (1, "G"), (1, "H"), (1, "J"), (1, "K"),
        (1, "L"), (1, ";"), (1, "'")]
SHIFT = [(1, "Z"), (1, "X"), (1, "C"), (1, "V"), (1, "B"), (1, "N"), (1, "M"), (1, ","),
         (1, "."), (1, "/")]

# cut: x position of the split in each row (left half is x < cut)
CUT = {"f": 7.5, "n": 7, "t": 6.5, "c": 6.75, "s": 7.25, "b": 7.25}

LAYOUTS = [
    {
        "name": "ANSI TKL reference (87 keys)",
        "note": "Red = width we cannot build (1.75, 2.25, 2.75, 6.25)",
        "rows": {
            "f": F_ROW,
            "n": NUM + [(2, "Bksp")],
            "t": [(1.5, "Tab")] + TAB + [(1.5, "\\")],
            "c": [(1.75, "Caps")] + CAPS + [(2.25, "Enter")],
            "s": [(2.25, "Shift")] + SHIFT + [(2.75, "Shift")],
            "b": [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (6.25, "Space"),
                  (1.25, "Alt"), (1.25, "Win"), (1.25, "Menu"), (1.25, "Ctrl")],
        },
        "split": False,
    },
    {
        "name": "ISO TKL reference (88 keys)",
        "note": "ISO Enter is L-shaped (1.5 top, 1.25 bottom) and cannot be built",
        "rows": {
            "f": F_ROW,
            "n": NUM + [(2, "Bksp")],
            "t": [(1.5, "Tab")] + TAB + [(1.5, "Enter*")],
            "c": [(1.75, "Caps")] + CAPS + [(1, "#"), (1.25, "Enter*")],
            "s": [(1.25, "Shift"), (1, "<")] + SHIFT + [(2.75, "Shift")],
            "b": [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (6.25, "Space"),
                  (1.25, "AltGr"), (1.25, "Win"), (1.25, "Menu"), (1.25, "Ctrl")],
        },
        "split": False,
    },
    {
        "name": "A: ANSI only, buildable (90 keys)",
        "note": "Gaps replace the 0.25/0.75 remainders; space bar becomes 2+1 thumb keys per side",
        "rows": {
            "f": F_ROW,
            "n": NUM + [(2, "Bksp")],
            "t": [(1.5, "Tab")] + TAB + [(1.5, "\\")],
            "c": [(1.5, "Caps"), ("gap", .25)] + CAPS + [("gap", .25), (2, "Enter")],
            "s": [(2, "Shift"), ("gap", .25)] + SHIFT + [(2, "Shift"), ("gap", .75)],
            "b": [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (1.5, "Fn"), (2, "Space"),
                  (1.5, "Space"), (1.25, "Fn"), (1.25, "AltGr"), (1.25, "Win"),
                  (1.25, "Menu"), (1.25, "Ctrl")],
        },
        "split": True,
    },
    {
        "name": "B: universal ANSI / ISO / JIS / ABNT2, buildable (94 keys), recommended",
        "note": "Blue = key whose legend or role changes with the language; no gaps in the main block",
        "rows": {
            "f": F_ROW,
            "n": NUM + [(1, "¥|Bksp"), (1, "Bksp")],
            "t": [(1.5, "Tab")] + TAB + [(1.5, "\\|Enter")],
            "c": [(1.5, "Caps"), ("gap", .25)] + CAPS + [(1, "#|Enter"), (1.25, "Enter")],
            "s": [(1.25, "Shift"), (1, "<|Shift")] + SHIFT + [(1.25, "ろ|/?|Fn"), (1.5, "Shift")],
            "b": [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (1.5, "無変換|Fn"), (2, "Space"),
                  (1.5, "Space"), (1.25, "変換|Fn"), (1.25, "AltGr"), (1.25, "Win"),
                  (1.25, "Menu"), (1.25, "Ctrl")],
        },
        "split": True,
    },
]

# Universal main block (layout B) without the F-row
B_ROWS = {k: v for k, v in LAYOUTS[3]["rows"].items() if k != "f"}
B_ROWS["n"] = [(1, "Esc|`")] + NUM[1:] + [(1, "¥|Bksp"), (1, "Bksp")]

# 65 %: main block plus one nav column = 16U; arrows tucked into shift/bottom rows
NAVC = [("gap", .25)]  # gap between the main block and the 1.25U nav column
R65_N = B_ROWS["n"][:13] + [(2, "Bksp")] + NAVC + [(1.25, "Del")]
R65_T = B_ROWS["t"] + NAVC + [(1.25, "PgUp")]
R65_C = ([(1.5, "Caps"), ("gap", .25)] + CAPS + [("gap", .25), (2, "Enter")]
         + NAVC + [(1.25, "PgDn")])
R65_S = ([(1.25, "Shift"), (1, "<|Shift")] + SHIFT + [(1, "#|ろ|/?"), (1, "Shift")]
         + [(1, "↑"), (1, "End")])
R65_B = [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (1.5, "無変換|Fn"), (2, "Space"),
         (2, "Space"), (1.25, "変換|Fn"), (1.25, "AltGr"), (1.25, "Ctrl"), ("gap", .25),
         (1, "←"), (1, "↓"), (1, "→")]
R65_W = {"n": 16.5, "t": 16.5, "c": 16.5, "s": 16.25, "b": 16.25}

COMPACT = [
    {
        "name": "C: universal, no F-row, full nav cluster (78 keys)",
        "note": "F1-F12 on a Fn layer over the number row; Esc shares the ` key; PrtSc/ScrLk/Pause on a layer",
        "rows": B_ROWS,
        "nav": [("n", NAV_X, ["Ins", "Home", "PgUp"]), ("t", NAV_X, ["Del", "End", "PgDn"]),
                ("s", NAV_X + 1, ["↑"]), ("b", NAV_X, ["←", "↓", "→"])],
        "split": True,
    },
    {
        "name": "D: universal, no F-row, nav as one column + floating arrows (74 keys)",
        "note": "Ins/Home/End on a layer; right Win dropped; 17.25U wide instead of 18.25U",
        "rows": {**B_ROWS,
                 "b": [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (1.5, "無変換|Fn"), (2, "Space"),
                       (1.5, "Space"), (1.25, "変換|Fn"), (1.25, "AltGr"), (1.25, "Menu"), (1.5, "Ctrl"),
                       ("gap", .25), (1, "←"), (1, "↓"), (1, "→")]},
        "main_w": {"b": 17.25},
        "nav": [("n", NAV_X, ["Del"]), ("t", NAV_X, ["PgUp"]), ("c", NAV_X, ["PgDn"]),
                ("s", NAV_X, ["↑"])],
        "split": True,
    },
    {
        "name": "E: universal 65 % (72 keys)",
        "note": "2U Enter and Backspace; # (ISO) / ろ (JIS) beside a 1U right Shift; 1.25U nav column and arrows set off by 0.25U; 16.5U wide",
        "rows": {"n": R65_N, "t": R65_T, "c": R65_C, "s": R65_S, "b": R65_B},
        "nav": [], "main_w": R65_W,
        "split": True,
    },
    {
        "name": "F: 65 % that fits the current 5x8 matrix (71 keys, 40 per half max)",
        "note": "As E, but End moves to a layer",
        "rows": {"n": R65_N, "t": R65_T, "c": R65_C,
                 "s": R65_S[:-1] + [("gap", 1)], "b": R65_B},
        "nav": [], "main_w": R65_W,
        "split": True,
    },
]

VARIABLE = {"Esc|`", "#|ろ|/?", "¥|Bksp", "\\|Enter", "#|Enter", "<|Shift", "ろ|/?|Fn", "無変換|Fn", "変換|Fn"}


def place(layout):
    keys = []  # (row, x, w, label)
    main_w = layout.get("main_w", 15)
    for r, items in layout["rows"].items():
        x = 0.0
        for it in items:
            if it[0] == "gap":
                x += it[1]
                continue
            w, lab = it
            keys.append((r, x, w, lab))
            x += w
        want = main_w.get(r, 15) if isinstance(main_w, dict) else main_w
        if abs(x - want) > 1e-9:
            sys.exit(f"{layout['name']}: row {r} is {x}U, not {want}U")
    for r, x0, labs in layout.get("nav", nav(None)):
        for i, lab in enumerate(labs):
            keys.append((r, x0 + i, 1, lab))
    return keys


def check_cuts(keys):
    for r, x, w, lab in keys:
        c = CUT[r]
        if x < c < x + w - 1e-9:
            sys.exit(f"key {lab} in row {r} straddles the cut at {c}")


def count(keys):
    # the ISO Enter is drawn as two rectangles but is one key
    n = sum(1 for k in keys if k[3] == "Enter*")
    return len(keys) - max(0, n - 1)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_board(layout, keys, oy):
    out = []
    title = layout["name"]
    out.append(f'<text x="{PAD*U}" y="{oy+22}" class="t">{esc(title)}</text>')
    out.append(f'<text x="{PAD*U}" y="{oy+40}" class="note">{esc(layout["note"])}</text>')
    by = oy + 52
    dy = 0 if "f" in layout["rows"] else -1.25
    width = max(x + w for _, x, w, _ in keys)
    nrows = 6 if dy == 0 else 5
    left = right = 0
    for r, x, w, lab in keys:
        px, py = (PAD + x) * U, by + (Y[r] + dy) * U
        bad = w not in ALLOWED
        side = "hl" if layout["split"] and x < CUT[r] else ("hr" if layout["split"] else "plain")
        left += side == "hl"
        right += side == "hr"
        cls = "bad" if bad else ("var" if lab in VARIABLE else side)
        out.append(f'<rect x="{px+2}" y="{py+2}" width="{w*U-4}" height="{U-4}" rx="5" class="{cls}"/>')
        txt = lab.replace("|", "/")
        fs = 11 if len(txt) <= 6 else 9
        out.append(f'<text x="{px+w*U/2}" y="{py+U/2+4}" font-size="{fs}" class="k">{esc(txt)}</text>')
        if w != 1:
            out.append(f'<text x="{px+w*U-6}" y="{py+U-7}" class="w">{w:g}</text>')
    if layout["split"]:
        pts = []
        for r in "fnt csb".replace(" ", ""):
            pass
        rows = [r for r in ["f", "n", "t", "c", "s", "b"] if r in layout["rows"]]
        tops = {"f": 0, "n": 1.25, "t": 2.25, "c": 3.25, "s": 4.25, "b": 5.25}
        path = []
        for r in rows:
            cx = (PAD + CUT[r]) * U
            y0 = by + (tops[r] + dy - (0.125 if r == "n" and dy == 0 else 0)) * U
            y1 = by + (tops[r] + dy + 1 + (0.125 if r == "f" else 0)) * U
            path += [(cx, y0), (cx, y1)]
        d = "M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in path)
        out.append(f'<path d="{d}" class="cut"/>')
        out.append(f'<text x="{(PAD+width)*U}" y="{by+(6.75+dy)*U}" class="note" text-anchor="end">'
                   f'left {left} + right {right} = {left+right} keys</text>')
    else:
        out.append(f'<text x="{(PAD+width)*U}" y="{by+(6.75+dy)*U}" class="note" text-anchor="end">'
                   f'{count(keys)} keys</text>')
    return "\n".join(out), by + (7.1 + dy) * U, left, right


def render(layouts, path):
    parts, oy = [], 0
    summary = []
    for lay in layouts:
        keys = place(lay)
        if lay["split"]:
            check_cuts(keys)
        s, oy, l, r = svg_board(lay, keys, oy)
        parts.append(s)
        summary.append((lay["name"], count(keys), l, r))
    W = (18.25 + 2 * PAD) * U
    css = """
    .t{font:600 15px sans-serif;fill:#222}.note{font:12px sans-serif;fill:#555}
    .k{font-family:sans-serif;text-anchor:middle;fill:#222}.w{font:9px sans-serif;text-anchor:end;fill:#888}
    rect{stroke:#666;stroke-width:1}.plain{fill:#f2f2f2}.hl{fill:#e7f3e3}.hr{fill:#fbf0dc}
    .var{fill:#dbe8fb;stroke:#3c6fc4}.bad{fill:#fde0e0;stroke:#c33;stroke-width:2}
    .cut{fill:none;stroke:#c33;stroke-width:3;stroke-dasharray:7 4}"""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{oy:.0f}" '
           f'viewBox="0 0 {W:.0f} {oy:.0f}"><style>{css}</style>'
           f'<rect width="100%" height="100%" fill="#fff" stroke="none"/>'
           + "\n".join(parts) + "</svg>")
    open(path, "w").write(svg)
    for n, t, l, r in summary:
        print(f"{t:3d} keys  L{l:3d} R{r:3d}  {n}")


if __name__ == "__main__":
    render(LAYOUTS, "tkl_layouts.svg")
    print()
    render(COMPACT, "compact_layouts.svg")
