# CLAUDE.md: PolyKybd (hardware)

KiCad boards in `poly_kybd/`; OpenSCAD and build123d case and printed parts in `parts/`.

**Rules for all PolyKybd repos** (review, branching, web session limits, including "fetch
your branch before concluding work is missing") are in `../polykybd-claude/CLAUDE.md`,
with the shared skills. If that repo is not attached, ask the user to attach
`thpoll83/polykybd-claude`. Default branch here: `master`. Local skills:
`investigate-kicad-pcb`, `explain-geometry-figure`, `render-variant-grid`. Search them for
a helper before writing one (`grep -RIn '<what>' .claude/skills/`).

## Layout

| Path | What |
|------|------|
| `poly_kybd/*.kicad_pcb` | the boards; the authoritative source for hole positions and rotations |
| `parts/<group>/` | CAD sources for one part group, plus its build and verify scripts |
| `parts/export/<group>/` | everything generated (`.stl`, `.step`, `.3mf`). Never hand-edited |
| `parts/models/` | reference meshes and `plate.scad`, for visualisation only |
| `parts/README.md` | the index: which part, which source, what to print |

Groups: `case` (all case variants, the shared spacer, and `case/step/`), `diffuser`,
`keycap_stem` (printed plates, and `keycap_stem/step/` for the moulded stem),
`display_holder`, `cirque_insert`, `cover_insert`, `rotary_enc_insert`, `legs`.

- ⚠️ **Keep every case variant in `case/`.** They `import()` the same KiCad SVG
  outlines, and `import()` resolves relative to the `.scad` file.
- ⚠️ **The build and check scripts write temporary driver `.scad` files beside the
  sources** (`_build_*.scad`, `_check_tmp_*.scad`; `check_frame.py` writes into
  `parts/case/`). Moving a script breaks resolution silently, into an empty object.
- **Read geometry from the `.kicad_pcb`, not the SVG exports**, which risk DPI scaling
  and lose per-part rotations (thumb keys up to 20°). Example:
  `parts/diffuser/gen_diffuser_frame.py`.
- ⚠️ **STL format is per group: match the sibling files.** The diffuser frames and the
  `case/spacer_diffuser_frame*.stl` files are ASCII; everything else is binary.
  `check_frame.py` parses ASCII only.

## KiCad boards

Board-level facts, extractions and re-route costs: [`docs/KICAD_BOARDS.md`](docs/KICAD_BOARDS.md).

- ⚠️ **`*.kicad_sch` is authoritative.** `poly_kb.net`, `poly_kb.xml` and the KiCad-5
  `.sch` files are generated, last touched 2024-02-17, two board revisions old.
- ⚠️ **Grep for the part (value, `lib_id`, footprint), not the reference designator.**
  Symbol instances store only `reference` and `unit`.
- **A shared sheet cannot vary a part per board.** All four boards include
  `rp_pico.kicad_sch`, so a change lands on split72 and split42 alike.
- ⚠️ **The JLC exporter builds the BOM from the board's footprint properties**, and
  *Update PCB from Schematic* does not refresh them by default. Sweep board vs schematic
  `MPN`/`LCSC` after every export; read `poly_kybd/Gerber/PCB/FABRICATION-NOTES.md` first.

## OpenSCAD

CLI 2021.01, CGAL only (no Manifold). Export needs no display
(`openscad -o out.stl --export-format asciistl|binstl part.scad`); a PNG render does
(`xvfb-run -a openscad -o view.png --render=cgal part.scad`). To look at a part:
`.claude/skills/explain-geometry-figure/scad_view.sh out.png model.scad [top|front|iso|<camera>]`.
Camera and framing traps: [`parts/OPENSCAD_NOTES.md`](parts/OPENSCAD_NOTES.md).

- ⚠️ **`use <x.scad>` resolves relative to the .scad file.** A helper in the wrong place
  yields an empty object, which a collision test reads as "no collision". Pair every
  clearance test with a positive control.
- ⚠️ **openscad exits 1 for an empty result and for a syntax error.** Test for
  `Current top level object is empty` first.
- **An empty result writes no file**, so give each invocation its own output path.
- **STL export is not byte-reproducible.** Compare a sorted facet multiset, and restore
  the committed bytes when only the order moved.

## build123d / OpenCASCADE (`step/` folders)

Parts a fabricator's validator must accept (the CNC case, the moulded stems) are
re-authored in build123d. Each `step/` folder has a README and a `make`.
Traps and the pin rationale: [`parts/STEP_PIPELINE.md`](parts/STEP_PIPELINE.md).

- ⚠️ **Both pipelines pin `BUILD123D_PIN` (0.12.0) and refuse another version**, on every
  target, even when nothing needs rebuilding. 0.13.0 changes the geometry. A case rebuild
  costs ~15 min.
- ⚠️ **Compare a re-export as an unordered point multiset, never byte-wise.** SVG path
  order shuffles run to run.
- ⚠️ **A STEP re-export rewrites the timestamped header.** Diff below the header
  (`tail -n +12`) and `git checkout` when nothing else changed.
- ⚠️ **Engraved text has three silent font traps**: OCCT ignores fontconfig, a family
  name renders the variable font's default instance, and OpenSCAD `text(size=)` differs
  from build123d `font_size` by 1.389×. Pin the font to a file and convert the size.
- **The drawing governs tolerance, material and finish; the STEP conveys shape.**
- ⚠️ **Measure the sheet layout** (`Sheet.report_collisions()`, `check_inside_frame()`);
  never eyeball offsets.

## Verifying a printed part

`parts/diffuser/build_frame.sh` regenerates, exports and verifies with `check_frame.py`.
Extend the verifier rather than checking by hand. Metrics and resin rules:
[`parts/PRINT_VERIFICATION.md`](parts/PRINT_VERIFICATION.md).

- **For in-plane wall thickness, rasterise and apply a morphological opening**, and
  report the area below the threshold, not the minimum.
- ⚠️ **A print service refuses walls below 0.8 mm.** Watch tapered rims,
  `linear_extrude(scale=)` chamfers and knife-edge circular segments. Engraved text is
  surface relief: exclude it from the wall check and tell the vendor.
- ⚠️ **Identify an orphan mesh by re-exporting the candidate source and comparing**
  (count + volume + bbox), never by filename.

## Keycap stems

Printed plates: one `.scad` per plate in `parts/keycap_stem/variants/` (R1–R5, S1, S, S5
× 1U/1U25), built by `build_stems.sh`; adding a plate is adding a file. The moulded stem
is `parts/keycap_stem/step/` (S profile only, revision stamp β instead of α). Notes:
[`parts/keycap_stem/NOTES.md`](parts/keycap_stem/NOTES.md).

- ⚠️ **A change to `keycap_stem.scad` must be re-exported on both sides**:
  `build_stems.sh` and `make -C parts/keycap_stem/step`; `make verify` checks they agree.
- **R1 and S1 are the same geometry; flat is R3.**
- ⚠️ **A missing Noto silently renders the engraving in the wrong face.**
  `build_stems.sh --fetch-font` acquires one; never use it to refresh one.
- **Judge a regenerated plate by bbox + volume, not facet count.**
- ⚠️ **Never rotate the profile row in the README pictures; tilt the camera.** The axes
  are the reference for the cap angle.
- ⚠️ **A full `build_stems.sh` run exceeds a 2-minute tool timeout.** Filter or
  background it.

To explain a measurement to someone who can't run the script (a print service), use the
`explain-geometry-figure` skill.
