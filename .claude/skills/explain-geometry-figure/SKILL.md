---
name: explain-geometry-figure
description: >-
  Draw a dimensioned, annotated figure that explains a geometry finding — "show me
  that feature", "where exactly is the thin wall / the collision / the clearance",
  "make a picture of it", "send the vendor a drawing of what they measured", or any
  time a CAD/mesh answer is easier to see than to read. Produces a self-contained SVG
  (+ PNG) from a stdlib-only Python script, optionally with a headless OpenSCAD render
  of the real part embedded and annotated. Use for OpenSCAD parts, KiCad-derived
  outlines, STL analyses, layout/routing plans. NOT for UI mockups or charts of
  tabular data.
---

# Explain a geometry finding with a figure

A measurement in prose ("0.60 mm at x = 3.395") is unverifiable by the reader. The
same number drawn on the shape, next to the shape's own dimensions, settles the
question — and it settles it for a **vendor or collaborator** who can't run your
script. This skill is the recipe that produced the PolyKybd diffuser thin-wall
figures.

Two deliverables, usually both:

1. **A dimensioned drawing** — you compute the geometry, so you can draw it exactly
   and label the exact numbers. Best for anything sub-millimetre.
2. **A render of the real part** — OpenSCAD headless, then annotated in SVG. Best for
   "where on the part is this?".

## Procedure

1. **Compute first, draw second, in ONE script.** Put the analytic geometry at the
   top of the drawing script and `print()` the numbers it derives. The figure and the
   prose you write afterwards then come from the same source and cannot disagree —
   the alternative (numbers in your head, shape in the script) is how a figure ends
   up contradicting its own caption.

2. **Write the script in the scratchpad**, importing `figlib.py` from this skill
   directory. Resolve it from the repo root rather than hardcoding a checkout path
   (`git rev-parse --show-toplevel` if you need it in a shell):

   ```python
   import sys, math, subprocess
   REPO = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                         capture_output=True, text=True, check=True).stdout.strip()
   sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
   from figlib import Fig, C

   R, CH = 3.5, 0.25
   XTIP  = math.sqrt(R*R - CH*CH)          # derived, then printed AND drawn
   print(f'tip at x={XTIP:.4f}')

   f = Fig(1500, 960)
   f.title('The 0.15 mm feature the print service measured',
           'cap = circle(d=7) clipped at y = 0.25 — the chord sits ABOVE centre,')
   f.panel(40, 130, 660, 740, 'A — plan view', '⌀7.0 mm overall')
   A = f.frame(scale=88, ox=375, oy=660)   # mm -> px, y flipped
   f.poly([A(p) for p in cap_pts], C.AMB, C.AMB, op=0.45)
   f.save('/tmp/.../fig.svg'); f.png()
   ```

3. **Render the PNG and READ IT BACK with the Read tool. Every time.** Nothing in the
   SVG writer knows how wide your text is or where your panel ends, so the first
   layout is essentially always wrong — overflowing panels, labels on top of each
   other, a footer running off the canvas. Two or three look-and-fix rounds is normal
   and cheap. **Never send a figure you have not looked at.**

4. **Only then** deliver with `SendUserFile(display="render")`. Send the **`.svg`
   alongside the `.png`** — the SVG is editable, scales, and is what a vendor can drop
   into a document.

## Layout rules that survive contact

- **Two panels: the whole thing, and the zoom.** A sub-millimetre feature on a 7 mm
  part needs both, or the reader has no idea what they're looking at. Draw a coloured
  **zoom box** on panel A and run two dashed leaders to panel B's corners.
- **Size the zoom from the panel, not the feature.** Pick the zoom window in mm, then
  `scale = usable_panel_height / window_height_mm`, where *usable* already excludes
  the ~100 px you need under the shape for a dimension bar. Doing it the other way
  round is what pushes the drawing through the panel border.
- **Callouts closer than ~30 px collide.** Put the labels in a fixed **column** at a
  fixed x, fan their y positions apart (100 px steps), and join each to its point on
  the geometry with a dashed **leader**. Don't try to place text at the point.
- **Text width ≈ 0.6 × font-size per character** in monospace. Check a long line fits
  before rendering; break footers across two lines rather than shrinking the font.
- **Colour carries meaning, consistently:** amber = the subject, red = the problem,
  green = the proposed fix, blue = zoom/leaders, grey dashed = context geometry you
  are not talking about. `figlib.C` holds them.
- **Draw the fix too.** A dashed green line showing where you'd trim turns the figure
  from a complaint into a decision the reader can make.

## OpenSCAD renders (`scad_view.sh`)

```bash
SIZE=1000x700 CENTRE=0,0.9,0.6 DIST=18 ./scad_view.sh d_top.png model.scad top
SIZE=1000x700 CENTRE=0,0.9,0.6 DIST=32 ./scad_view.sh d_iso.png model.scad iso
```

Pull one module out of a big part file with `use <…>` — it imports the modules and
**ignores the file's top-level geometry**, so a `.scad` that renders a whole print
plate still gives you one part:

```openscad
use </home/user/PolyKybd/parts/diffuser.scad>
diffuser();
```

The traps, all of which cost a cycle:

- **No display ⇒ a 0-byte PNG and exit 0.** Always `xvfb-run -a`. The wrapper checks.
- **`--render` takes an argument** in OpenSCAD 2021.01: `--render=cgal`. A bare
  `--render` prints the usage block and exits 2 — which reads like a bad flag
  somewhere else entirely.
- **`--colorscheme="Tomorrow Night"`** must reach argv as one word.
- **`dist` is also the orthographic viewport scale**, so a top view that looks
  "zoomed in" is just `DIST` too small. Raise it until the part fits.
- **`$fn` set at your top level does NOT override a `$fn=` hard-coded inside the
  module's primitives** — the facets you see are the facets the STL has. Say so in
  the caption instead of fighting it.
- **Don't colour-highlight in preview mode.** OpenCSG preview tints `difference()`
  results itself and will happily paint your `color()` over the wrong region (it
  rendered an entire cap red once). Render one clean solid with `--render=cgal` and
  put the highlight on in **SVG**, on top — cheaper, and it can carry a label.

## Annotating a render

`Fig.image()` base64-embeds the PNG into the SVG. Do **not** use a relative `href` —
it breaks the moment the SVG moves. Scale and offset the image so the part fills the
frame, and pass `clip=` so the enlargement can't cover your title and footer:

```python
S  = 1.55                                    # part bbox centre (510,380) -> (480,400)
IX, IY = 480 - 510*S, 400 - 380*S
f.image('d_iso.png', IX, IY, 1000*S, 700*S, clip=(0, 66, 1000, 644))
f.ellipse(*M((690, 355)), 52, 150, C.RED)    # ring the feature
f.leader(...); f.txt(..., '0.15 mm tip', 20, C.RED, bold=True)
```

Ring the feature **on both sides if it's mirrored** — otherwise the reader assumes
it's a one-off defect rather than something inherent to the shape.

## Files

| File | Role |
|------|------|
| `figlib.py` | stdlib-only SVG builder: palette, panels, mm→px frames, dimension bars, leaders, PNG embed, `rsvg-convert` |
| `scad_view.sh` | headless OpenSCAD → PNG with the camera/render/display traps handled |

Requires `rsvg-convert` (librsvg2-bin), and for renders `openscad` + `xvfb-run`
(`xvfb`) — all present in the PolyKybd dev container.
