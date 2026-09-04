# parts/

Every mechanical part of the PolyKybd: the OpenSCAD/Python sources, and the
meshes exported from them.

**The layout rule is one folder per part group, and everything generated under
`export/<the same folder name>/`.** A source folder holds the `.scad`/`.py` plus
the scripts that build and verify that part; nothing hand-edited ever lives in
`export/`, and nothing generated ever sits beside a source.

```
parts/
  <group>/          sources + that group's build/verify scripts
  export/<group>/   .stl / .step / .3mf  -- generated, do not hand-edit
  models/           reference meshes (not printed parts)
```

## What to print

| Part | Print this | Source |
|------|-----------|--------|
| Case, split72 (FDM) | `export/case/case_polykybd_split72_{left,right}_r7.stl` | `case/case_polykybd_split72_lr.scad` |
| Case, split72 (metal / CNC) | `export/case/case_polykybd_split72_metal*.stl`, `.3mf`; B-Rep STEP `export/case/metal-case-{left,right}.step` | `case/case_polykybd_split72_metal.scad`, re-authored by `case/step/` |
| Case, right side | `export/case/right_side_case.3mf`, `right_side_spacer.3mf` | `case/right_side.scad` |
| Spacer | `export/case/spacer.stl` — or `spacer_diffuser_frame.stl` when the LED diffuser frame is fitted (it is notched for the frame's web on **both** faces, so one part serves either half) | `right_spacer()` in `case/case_polykybd_split72_lr.scad` |
| LED diffuser frame | `export/diffuser/diffuser_frame_{left,right}.stl` (`_4x` = four stacked per plate) | `diffuser/` — **generated from the plate PCB**, see below |
| LED diffuser, old generation | `export/diffuser/diff_v2.stl` (4 rings × 19 caps, 97 × 97 × 6.2 mm) | `diffuser/led_caps.scad` |
| Keycap stems | `export/keycap_stem/keycap_stem_revAlpha_{1U,1U25}_{R1..R5,S1,S,S5}_10p.stl` | one file per plate in `keycap_stem/variants/`, over the shared `keycap_stem/keycap_stem.scad` |
| Keycap stems, **moulded** (not printed) | B-Rep STEP `export/keycap_stem/stem_S_{1U,1U25}.step` + the A3 drawing `stem_S_{1U,1U25}_drawing.svg` | the same `keycap_stem.scad`, re-authored by `keycap_stem/step/` |
| Status display holder | `export/display_holder/display_holder_r1.stl`, or `display_holder_dummy_r1.stl` to blank the cut-out | `display_holder/display_holder.scad` |
| Cirque trackpad insert | `export/cirque_insert/cirque23_slim_insert_r8.stl` (23 mm), `cirque23_insert_high_r1.stl` (raised); 35 mm is experimental | `cirque_insert/*.scad` |
| Cover insert | `export/cover_insert/cover_insert_r3_10p.stl` | `cover_insert/cover_insert.scad` |
| Rotary encoder insert | `export/rotary_enc_insert/rotary_enc_insert_r1.stl` | `rotary_enc_insert/rotary_enc_insert.scad` |
| Tenting legs | `export/legs/legs_r2_8p.stl` (8 legs, 4 mirrored pairs at 29 mm pitch, 119 × 39 × 3.8 mm) | `legs/legs.scad` (`connected_8p()`) |

`diffuser/led_caps.scad` is the **earlier generation** of the LED diffuser: one
cap is a ~7 × 4.2 × 3.2 mm D-shaped light pipe flanged on both faces, clipping
through a 5 mm hole in a 1.2 mm PCB, laid out 4 rings × 19 on a torus sprue. It
defines the same module names as `diffuser.scad`, so never `use <>` both from
one file. `diff_v2.stl` ("diffuser v2") is its committed plate: a fresh export
of `led_caps.scad` gives the same 210240 facets, the same 4062.9 mm³ and the
same bounding box, but only ~88 % of facets agree to the millimetre, so it came
from a slightly different revision of the source — `build_parts.sh led_caps`
therefore writes its own file rather than overwriting it.

The two leg meshes were committed as `case_ins_r2.stl` / `case_ins_leg_v0.stl`,
which read as "case insert" and hid what they were: `legs.scad` re-exports
`legs_r2_8p.stl` to within a micron (identical facet count, volume and bounding
box), and `legs_v0_1p.stl` is one older single leg. Their 3.8 mm thickness is
shared with the spacer, which is what makes them easy to mistake for one.

`models/` is **not** printable output — it holds what only ever existed to
visualise how a part fits: `display_glass.stl`, `keycap_display.stl`,
`keycap_display_cable.stl`, `display_holder_wdisplay.stl` (the holder shown with
its display in place), `right_side_model.wrl`, and `plate.scad`, which appears to
have been a 3D model of the switch plate rather than a printed part — it imports
SVGs from a `poly_kb_atom/` directory that is not in this repo, so it has not
built for a long time.

## Building

Three build scripts.  Run them rather than exporting by hand -- doing it by hand
is what let an export fall a revision behind, and what let a mesh sit in the tree
for years under a name that did not say which source made it.

```bash
parts/diffuser/build_frame.sh          # regenerate from the PCB, export, verify
parts/diffuser/build_frame.sh --check  # verify the committed meshes only

parts/keycap_stem/build_stems.sh            # every variant in variants/
parts/keycap_stem/build_stems.sh 1U_R2 S1   # only variants matching those
parts/keycap_stem/build_stems.sh --list

parts/build_parts.sh                   # the simple parts (top level IS the plate)
parts/build_parts.sh led_caps          # opt-in: the superseded diffuser
parts/build_parts.sh --list

parts/keycap_stem/render_profiles.sh   # the README profile pictures (not meshes)

make -C parts/case/step                # metal case -> clean B-Rep STEP
make -C parts/keycap_stem/step         # moulded stems -> STEP + A3 drawing
make -C parts/keycap_stem/step verify  # ...and diff the solid against the .scad
```

The two `step/` folders are a different pipeline from the exporters above: OpenSCAD has
no B-Rep kernel, so anything a fabricator's validator has to accept — the CNC case, the
injection-moulded stems — is **re-authored in build123d** rather than exported as a mesh.
They emit `.step` (and, for the stems, a dimensioned drawing) into the same `export/`
folders. See `case/openscad-to-step-recipe.md` and `openscad-to-step-recipe-stems.md`.

All three exporters re-export idempotently: OpenSCAD emits facets in an unstable order and
different builds of it disagree in the last float digits, so each script compares
the result against the committed mesh and puts the committed bytes back when only
that noise moved.  A clean re-run therefore prints `unchanged` and leaves the tree
untouched.

The keycap stems are **one `.scad` per plate** in `keycap_stem/variants/`, each
`include`-ing the shared `keycap_stem.scad` and making a single call, so a plate
renders on its own — open the variant in OpenSCAD and you are looking at exactly
what gets exported (`variants/<x>.scad` → `export/keycap_stem/<x>.stl`).  Adding a
plate means adding a file; `build_stems.sh` walks the directory and has no table
of its own.  ⚠️ On a machine that did not export them, some plates will report
`CHANGED` purely because the engraved revision tessellates differently under a
different Noto (see below) — check the bounding box and volume before believing
the geometry moved, and `git checkout` rather than committing the rewrite.

`keycap_stem/preview_stems.scad` holds the row-lineup arrangements — one stem per
row, front (row 1) nearest the viewer — behind a `view =` selector: `curved`
(R1..R5), `stepped` (sculpted: S1 front, S5 back, S between), `stepped_uniform`
(S everywhere), `flat` (R3 everywhere), plus the historic `r2_rows` set and a
`cutaway` with the display and its cable in place.  These are **pictures, not
plates**, so `build_stems.sh` ignores the file; `keycap_stem/render_profiles.sh`
renders the four profile views into `images/` for the top-level README.  Render
them with that script rather than framing them in the GUI: they only compare if
they share one camera, and the previous set did not — a difference in elevation
reads as a difference in profile.  (Rendering needs a display even though
exporting does not, hence the `xvfb-run` inside it.)

⚠️ **The renders draw the coordinate AXES on purpose, and `profile_row()` must
not rotate the row.**  The horizontal axis line is the reference a reader
measures each cap angle against, so it is the thing that makes the picture mean
anything — and any tilt applied to the row itself adds to every angle silently.
A row tilt of 8° was tried and made R3, which is flat by definition, sit 8°
nose-up on the axis.  Tilt the camera (the elevation in `render_profiles.sh`),
which moves the axes with it.

The diffuser frame is **generated from `poly_kybd/poly_kybd_split72_plate_*.kicad_pcb`**
— read hole positions and rotations from the board, never from the SVG exports.
`parts/diffuser/check_frame.py` gates it on watertightness, minimum wall,
left/right symmetry, the plate trap and spacer clearance in both flip
orientations.

Everything else is still exported from the OpenSCAD GUI by opening the `.scad`
and saving into the matching `export/` folder.

## Three things that will bite you

- **STL format is mixed and that is deliberate.** The diffuser frames are
  **ASCII** (`check_frame.py` parses them and refuses binary); every other part
  is **binary**. Match the sibling files already in the export folder.
- **The engraved revision needs Noto.** `keycap_stem.scad` asks for
  `Noto:style=Bold`; without it fontconfig silently substitutes another face and
  the plate exports looking fine. `build_stems.sh --fetch-font` downloads it to
  `~/.local/share/fonts/` (no root), the same source the firmware's `dl-fonts.sh`
  uses; `apt-get install fonts-noto-core` works too. ⚠️ Use `--fetch-font` to get
  a Noto when there is none, **not** on a machine that already has one: the
  downloaded variable font and a packaged static Bold tessellate the engraving
  differently (46192 vs 44912 facets on the same plate, identical volume and
  bounding box), so a re-export afterwards legitimately reports `CHANGED`.
- **Every case variant shares the imported KiCad SVG outlines**, and `import()`
  resolves relative to the .scad file — so they all have to stay in `case/`.
