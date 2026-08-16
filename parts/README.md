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
| LED diffuser, old generation | superseded, no mesh committed — export `diffuser/led_caps.scad` if you need it | `diffuser/led_caps.scad` |
| Keycap stems | `export/keycap_stem/keycap_stem_revAlpha_{1U,1U25}_{R1..R5,S1,S,S5}_10p.stl` | `keycap_stem/keycap_stem.scad` |
| Status display holder | `export/display_holder/display_holder_r1.stl`, or `display_holder_dummy_r1.stl` to blank the cut-out | `display_holder/display_holder.scad` |
| Cirque trackpad insert | `export/cirque_insert/cirque23_slim_insert_r8.stl` (23 mm), `cirque23_insert_high_r1.stl` (raised); 35 mm is experimental | `cirque_insert/*.scad` |
| Cover insert | `export/cover_insert/cover_insert_r3_10p.stl` | `cover_insert/cover_insert.scad` |
| Rotary encoder insert | `export/rotary_enc_insert/rotary_enc_insert_r1.stl` | `rotary_enc_insert/rotary_enc_nsert.scad` |
| Case insert | `export/case_insert/case_ins_r2.stl` (4 frames on a runner, 119 × 39 × 3.8 mm), `case_ins_leg_v0.stl` (25.5 × 18.35 × 3.8 mm) | ⚠️ no CAD source is committed for these |

`diffuser/led_caps.scad` is the **earlier generation** of the LED diffuser: one
cap is a ~7 × 4.2 × 3.2 mm D-shaped light pipe flanged on both faces, clipping
through a 5 mm hole in a 1.2 mm PCB, laid out 4 rings × 19 on a torus sprue. It
defines the same module names as `diffuser.scad`, so never `use <>` both from
one file. Both `case_ins_*` meshes are 3.8 mm thick — the same `spacer_height`
as `right_spacer()` — so they belong to the spacer layer.

`models/` is **not** printable output: `display_glass.stl`, `keycap_display.stl`,
`keycap_display_cable.stl`, `display_holder_wdisplay.stl` and
`right_side_model.wrl` exist to visualise how a part fits.

## Building

Two parts have a one-command build; run it rather than exporting by hand,
because in both cases doing it by hand is what let an export fall a revision
behind.

```bash
parts/diffuser/build_frame.sh          # regenerate from the PCB, export, verify
parts/diffuser/build_frame.sh --check  # verify the committed meshes only

parts/keycap_stem/build_stems.sh       # every profile, both widths
parts/keycap_stem/build_stems.sh R2 R3 # just those rows
parts/keycap_stem/build_stems.sh --list
```

The diffuser frame is **generated from `poly_kybd/poly_kybd_split72_plate_*.kicad_pcb`**
— read hole positions and rotations from the board, never from the SVG exports.
`parts/diffuser/check_frame.py` gates it on watertightness, minimum wall,
left/right symmetry, the plate trap and spacer clearance in both flip
orientations.

Everything else is still exported from the OpenSCAD GUI by opening the `.scad`
and saving into the matching `export/` folder.

## Two things that will bite you

- **STL format is mixed and that is deliberate.** The diffuser frames are
  **ASCII** (`check_frame.py` parses them and refuses binary); every other part
  is **binary**. Match the sibling files already in the export folder.
- **The engraved revision needs Noto.** `keycap_stem.scad` asks for
  `Noto:style=Bold`; without it fontconfig silently substitutes another face and
  the plate exports looking fine. `build_stems.sh --fetch-font` downloads it to
  `~/.local/share/fonts/` (no root), the same source the firmware's `dl-fonts.sh`
  uses; `apt-get install fonts-noto-core` works too.
- **Every case variant shares the imported KiCad SVG outlines**, and `import()`
  resolves relative to the .scad file — so they all have to stay in `case/`.

`plate/plate.scad` imports SVGs from a `poly_kb_atom/` directory that is
not in this repo, so it does not currently build.
