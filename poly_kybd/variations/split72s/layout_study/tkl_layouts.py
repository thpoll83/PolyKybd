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
NAVC = []  # the 1.25U nav column touches the main block
R65_N = B_ROWS["n"][:13] + [(2, "Bksp")] + NAVC + [(1.25, "Del")]
R65_T = B_ROWS["t"] + NAVC + [(1.25, "PgUp")]
R65_C = ([(1.5, "Caps"), ("gap", .25)] + CAPS + [("gap", .25), (2, "Enter")]
         + NAVC + [(1.25, "PgDn")])
R65_S = ([(1.25, "Shift"), (1, "<|Shift")] + SHIFT + [(1, "#|ろ|/?"), (1, "Shift")]
         + [(1, "↑"), (1, "End")])
R65_B = [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (1.5, "無変換|Fn"), (2, "Space"),
         (2, "Space"), (1.5, "変換|Fn"), (1.25, "AltGr"), (1.25, "Ctrl"),
         (1, "←"), (1, "↓"), (1, "→")]
R65_W = {"n": 16.25, "t": 16.25, "c": 16.25, "s": 16.25, "b": 16.25}

REF65 = {
    "name": "Standard ANSI 65 % reference (68 keys)",
    "note": "Red = width we cannot build (1.75, 2.25, 6.25)",
    "rows": {
        "n": NUM + [(2, "Bksp"), (1, "Del")],
        "t": [(1.5, "Tab")] + TAB + [(1.5, "\\"), (1, "PgUp")],
        "c": [(1.75, "Caps")] + CAPS + [(2.25, "Enter"), (1, "PgDn")],
        "s": [(2.25, "Shift")] + SHIFT + [(1.75, "Shift"), (1, "↑"), (1, "End")],
        "b": [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (6.25, "Space"), (1, "Alt"),
              (1, "Fn"), (1, "Ctrl"), (1, "←"), (1, "↓"), (1, "→")],
    },
    "nav": [], "main_w": 16, "split": False,
}

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
        "note": "2U Enter and Backspace; # (ISO) / ろ (JIS) beside a 1U right Shift; 1.25U nav column; arrows and End right-aligned to it; 16.25U wide, no gaps",
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

# Number block: 5 rows like layout E, all 1U (a 4x5 grid that also works as a macro pad).
# The tall + and Enter and the 2U 0 become two 1U keys each.
NP4 = {"n": [(1, "Num"), (1, "/"), (1, "*"), (1, "-")],
       "t": [(1, "7"), (1, "8"), (1, "9"), (1, "+")],
       "c": [(1, "4"), (1, "5"), (1, "6"), (1, "+|=")],
       "s": [(1, "1"), (1, "2"), (1, "3"), (1, "Enter")],
       "b": [(1, "0"), (1, "0|00"), (1, "."), (1, "Enter")]}
NP5 = {"n": [(1, "Bksp")] + NP4["n"], "t": [(1, "(")] + NP4["t"], "c": [(1, ")")] + NP4["c"],
       "s": [(1, "=")] + NP4["s"], "b": [(1, "Tab")] + NP4["b"]}
NP_X = 16.25          # the number block docks to the right edge of layout E


def _docked(e_rows, pad):
    return {r: e_rows[r] + pad[r] for r in "ntcsb"}


NUMPAD = [
    {
        "name": "N1: number block, 4x5 grid of 1U keys (20 keys)",
        "note": "Tall + and Enter and the 2U 0 are two 1U keys each; blue keys can be =, 00; works as a macro pad",
        "rows": NP4, "nav": [], "main_w": 4, "split": False,
    },
    {
        "name": "N2: number block, 5x5 grid of 1U keys (25 keys)",
        "note": "Extra left column: Bksp, ( ) = Tab for calculator use",
        "rows": NP5, "nav": [], "main_w": 5, "split": False,
    },
    {
        "name": "E + N1 docked (92 keys)",
        "note": "The number block joins the right half flush, like the split; 20.25U wide",
        "rows": "E+N1", "nav": [], "main_w": NP_X + 4, "split": True, "pad_x": NP_X,
    },
]

VARIABLE = {"+|=", "0|00", "Esc|`", "#|ろ|/?", "¥|Bksp", "\\|Enter", "#|Enter", "<|Shift", "ろ|/?|Fn", "無変換|Fn", "変換|Fn"}


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
    left = right = pads = 0
    for r, x, w, lab in keys:
        px, py = (PAD + x) * U, by + (Y[r] + dy) * U
        bad = w not in ALLOWED
        side = "hl" if layout["split"] and x < CUT[r] else ("hr" if layout["split"] else "plain")
        if layout.get("pad_x") is not None and x >= layout["pad_x"]:
            side = "pad"
        pads += side == "pad"
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
        if layout.get("pad_x") is not None:
            px = (PAD + layout["pad_x"]) * U
            out.append(f'<path d="M {px:.1f},{by-0.125*U:.1f} L {px:.1f},{by+(5.125)*U:.1f}" class="cut"/>')
        out.append(f'<text x="{(PAD+width)*U}" y="{by+(6.75+dy)*U}" class="note" text-anchor="end">'
                   f'left {left} + right {right}' + (f' + number block {pads}' if pads else '')
                   + f' = {left+right+pads} keys</text>')
    else:
        out.append(f'<text x="{(PAD+width)*U}" y="{by+(6.75+dy)*U}" class="note" text-anchor="end">'
                   f'{count(keys)} keys</text>')
    for ax, ay, wmm, hmm, label in layout.get("areas", []):
        px, py = (PAD + ax) * U, by + (ay + Y["n"] + dy) * U     # ay counts from the top key row
        w, h = wmm / MM_U * U, hmm / MM_U * U
        out.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{w:.1f}" height="{h:.1f}" rx="3" class="area"/>')
        out.append(f'<text x="{px + w / 2:.1f}" y="{py + h / 2 - 2:.1f}" font-size="9" class="k">{esc(label)}</text>')
        out.append(f'<text x="{px + w / 2:.1f}" y="{py + h / 2 + 9:.1f}" font-size="8" class="k">{wmm:g} x {hmm:g} mm</text>')
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
    W = (max(18.25, *(max(x + w for _, x, w, _ in place(l)) for l in layouts)) + 2 * PAD) * U
    css = """
    .t{font:600 15px sans-serif;fill:#222}.note{font:12px sans-serif;fill:#555}
    .k{font-family:sans-serif;text-anchor:middle;fill:#222}.w{font:9px sans-serif;text-anchor:end;fill:#888}
    rect{stroke:#666;stroke-width:1}.plain{fill:#f2f2f2}.hl{fill:#e7f3e3}.hr{fill:#fbf0dc}.pad{fill:#efe6f7}.area{fill:#fff7d6;stroke:#b8860b;stroke-width:1.5;stroke-dasharray:4 3}
    .var{fill:#dbe8fb;stroke:#3c6fc4}.bad{fill:#fde0e0;stroke:#c33;stroke-width:2}
    .cut{fill:none;stroke:#c33;stroke-width:3;stroke-dasharray:7 4}"""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{oy:.0f}" '
           f'viewBox="0 0 {W:.0f} {oy:.0f}"><style>{css}</style>'
           f'<rect width="100%" height="100%" fill="#fff" stroke="none"/>'
           + "\n".join(parts) + "</svg>")
    open(path, "w", encoding="utf-8").write(svg)
    for n, t, l, r in summary:
        print(f"{t:3d} keys  L{l:3d} R{r:3d}  {n}")


NUMPAD[2]["rows"] = _docked(COMPACT[2]["rows"], NP4)


# Room for the status display holder (27 x 26 mm cut-out, parts/display_holder) and the
# expansion port lid (17 x 14 mm cut-out plus a 1 mm flange, parts/cover_insert) above the
# arrow keys. The nav column goes; the arrows sit 0.25U right of the modifiers.
DISPLAY_MM, EXPANSION_MM = (27.0, 26.0), (19.0, 16.0)
MM_U = 19.05          # mm per key unit (U above is pixels per unit)
_E2_TOP = {"n": B_ROWS["n"][:13] + [(2, "Bksp")],
           "t": B_ROWS["t"],
           "c": [(1.5, "Caps"), ("gap", .25)] + CAPS + [("gap", .25), (2, "Enter")]}
_E2_SHIFT = [(1.25, "Shift"), (1, "<|Shift")] + SHIFT + [(1, "#|ろ|/?"), (1, "Shift"), ("gap", .25)]
_E2_BOTTOM = [(1.25, "Ctrl"), (1.25, "Win"), (1.25, "Alt"), (1.5, "無変換|Fn"), (2, "Space"),
              (2, "Space"), (1.5, "変換|Fn"), (1.25, "AltGr"), (1.25, "Ctrl")]


def _area(x_u, y_u, size_mm, label):
    return (x_u, y_u, size_mm[0], size_mm[1], label)


STATUS = [
    {
        "name": "E (current): no room above the arrows (72 keys)",
        "note": "Nav column Del/PgUp/PgDn/End fills the strip above the arrows",
        "rows": {"n": R65_N, "t": R65_T, "c": R65_C, "s": R65_S, "b": R65_B},
        "nav": [], "main_w": R65_W, "split": True,
    },
    {
        "name": "E2: display and expansion port above the arrows, Del beside the up arrow (69 keys)",
        "note": "PgUp/PgDn/Home/End on Fn + arrows; arrows 0.25U from the modifiers; right half 38 keys, fits the current 5x8 matrix",
        "rows": {**{r: v + [("gap", 1.5)] for r, v in _E2_TOP.items()},
                 "s": _E2_SHIFT + [(1, "↑"), (1, "Del")],
                 "b": _E2_BOTTOM + [("gap", .25), (1, "←"), (1, "↓"), (1, "→")]},
        "nav": [], "main_w": 16.5, "split": True,
        # stacked in the 1.5U x 3U strip
        "areas": [_area(15.0 + (1.5 - DISPLAY_MM[0] / MM_U) / 2, 0.15, DISPLAY_MM, "status display"),
                  _area(15.0 + (1.5 - EXPANSION_MM[0] / MM_U) / 2, 1.85, EXPANSION_MM, "expansion port")],
    },
    {
        "name": "E3: display and expansion port above the arrows, PgUp and PgDn beside the up arrow (71 keys)",
        "note": "Home/End/Del on Fn; Menu key added left of the arrows; 17.5U wide; right half 40 keys, fits the current 5x8 matrix",
        "rows": {**{r: v + [("gap", 2.5)] for r, v in _E2_TOP.items()},
                 "s": _E2_SHIFT + [(1, "PgUp"), (1, "↑"), (1, "PgDn")],
                 "b": _E2_BOTTOM + [(1, "Menu"), ("gap", .25), (1, "←"), (1, "↓"), (1, "→")]},
        "nav": [], "main_w": 17.5, "split": True,
        # side by side: 27 + 1.6 + 19 mm = 47.6 mm = the 2.5U strip
        "areas": [_area(15.0, (3 - DISPLAY_MM[1] / MM_U) / 2, DISPLAY_MM, "status display"),
                  _area(15.0 + (DISPLAY_MM[0] + 1.6) / MM_U, (3 - EXPANSION_MM[1] / MM_U) / 2, EXPANSION_MM, "expansion port")],
    },
]


if __name__ == "__main__":
    render(LAYOUTS, "tkl_layouts.svg")
    print()
    render(COMPACT, "compact_layouts.svg")
    print()
    render([REF65, COMPACT[2]], "e_vs_65.svg")
    print()
    render(NUMPAD, "numpad_layouts.svg")
    print()
    render(STATUS, "status_layouts.svg")
