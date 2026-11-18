# Layout study: TKL, 65 % and number block with 1, 1.25, 1.5 and 2U keys

The study looks for physical layouts that use only 1, 1.25, 1.5 and 2U keys and that
split into two halves at the standard split line (6/T/G/B on the left). In the
connected position the halves touch along that line.

## Files

| File | What |
|---|---|
| `tkl_layouts.py` | Generator: every layout as rows of key widths and gaps. Checks the row widths and that no key crosses the split line, then writes the SVGs |
| `tkl_layouts.svg/.png` | ANSI and ISO TKL references, A (ANSI only, 90 keys), B (universal TKL, 94 keys) |
| `compact_layouts.svg/.png` | No F-row: C (full nav, 78), D (one nav column, 74), E (65 %, 72), F (E without End, 71) |
| `e_vs_65.svg/.png` | Layout E next to a standard ANSI 65 % board |
| `numpad_layouts.svg/.png` | Number blocks N1 (4x5, 20 keys) and N2 (5x5, 25 keys), all 1U, and E with N1 docked on the right |
| `export_layout_e.py` | Writes the JSON files below from `tkl_layouts.py` |
| `layout_e.kle.json` | Layout E for keyboard-layout-editor.com (paste into the Raw data tab) |
| `layout_e.qmk.json` | Layout E as a QMK `layouts` entry, 6x7 matrix per half (rows 0-5 left, 6-11 right) |
| `layout_e_keys.json`, `layout_e_legends.png` | Input for `render/layout_scene.py` |
| `numpad_n1.kle.json`, `numpad_n1.qmk.json` | Number block N1, 5x4 matrix |
| `plate_rongorongo.py` | Plate artwork proposal: the layout E plate with the split72 switch cut-outs and Rongorongo-style glyph lines in the visible strips. Writes the two SVGs below |
| `plate_rongorongo.svg/.png`, `rongorongo_glyphs.svg/.png` | The plate proposal and the 15 glyphs. The glyphs are own simplified drawings, not copied from a tablet |

Regenerate:

```bash
python3 tkl_layouts.py
python3 export_layout_e.py
```

## Layout E

72 keys, 16.25U wide, 5 rows. Left half 31 keys (rows 7, 6, 6, 7, 5), right half 41 keys
(rows 8, 9, 8, 9, 7). A blue key in the drawings changes its role with the language,
for example `\` on ANSI is the top half of the ISO Enter.

- Matrix: 6x7 per half (42 positions, 13 GPIOs, as today). Keys past column 7 of a
  physical row are wired into matrix row 5.
- Display chip selects: 41 on the right half, so 6 shift registers per half instead of 5.

## Test render

`render/layout_scene.py` builds the layout from the real 1U key model. Wider caps and
display carriers are stretched in x, so they are an approximation of a real 1.5U or 2U
part. The case and plate are plain extrusions of each half's outline, without screw
holes, USB ports or switch cut-outs.

```bash
blender -b --python render/layout_scene.py -- docs/layout_study/layout_e_keys.json \
    docs/layout_study/layout_e_legends.png render/out/layout_e.png 64 1600 joined 34
```

Arguments after the output: Cycles samples, width in pixels, `joined` or `apart`,
camera elevation in degrees. One render at 64 samples and 1600 px takes about 2 minutes
on 4 CPUs. Blender 4.1.1 is required (see `render/README.md`).
