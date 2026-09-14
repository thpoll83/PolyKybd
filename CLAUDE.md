# CLAUDE.md — PolyKybd (hardware)

This file provides guidance to Claude Code (claude.ai/code) when working in the
**PolyKybd** repo: the KiCad boards under `poly_kybd/`, the OpenSCAD case and
printed parts under `parts/`.

For the firmware see [`../qmk_firmware/CLAUDE.md`](../qmk_firmware/CLAUDE.md);
for the host app [`../PolyKybdHost/CLAUDE.md`](../PolyKybdHost/CLAUDE.md). The
**code-review conventions** and **branching rules** in the qmk file apply to
every PolyKybd repo, this one included — in particular: start each piece of work
on a fresh branch cut from the updated default (**`master`** here), and never
keep committing to a branch whose PR has merged.

## Layout

**One folder per part group under `parts/`, and every generated mesh under
`parts/export/<same folder name>/`.** So a part's sources and its build/verify
scripts sit together, and nothing generated is ever mixed in with a source.

| Path | What |
|------|------|
| `poly_kybd/*.kicad_pcb` | the boards; the **authoritative** source for hole positions and rotations |
| `parts/<group>/` | the CAD sources for one part group, plus the scripts that build and verify it |
| `parts/export/<group>/` | everything generated: `.stl`, `.step`, `.3mf`. **Never hand-edited** |
| `parts/models/` | reference meshes (display glass, FFC cable) and `plate.scad` — visualisation only, never printed |
| `parts/README.md` | the index: which part, which source, what to print |

The groups are `case` (every case variant: the FDM split72 left/right, the
metal/CNC one, POM, right2 and the right-side case, plus the spacer they
share and the STEP pipeline under `case/step/`), `diffuser`,
`keycap_stem`, `display_holder`, `cirque_insert`, `cover_insert`,
`rotary_enc_insert`, `legs`.

⚠️ **Keep every case variant in `case/` — they SHARE the imported KiCad SVG
outlines.** `right_side.scad` and `case_polykybd_split72_lr.scad` both
`import("poly_kb_wave_right_case-*.svg")`, and an `import()` path resolves
relative to the .scad file just as `use <>` does, so splitting the variants
into sibling folders silently breaks whichever one loses the SVGs.

⚠️ **The two build scripts write a temporary driver `.scad` beside the sources
and `use <>` it**, because `use <>` resolves relative to the *.scad file*, not
the cwd (see the trap below). `parts/diffuser/check_frame.py` writes its temp
driver into `parts/case/` for the same reason — it needs
`case_polykybd_split72_lr.scad`'s `right_spacer()` and reaches the frame as
`use <../diffuser/diffuser_frame_left.scad>`. Both are gitignored as
`_build_*.scad` / `_check_tmp_*.scad`; moving either script to another folder
breaks the resolution **silently**, into an empty object.

**Read geometry from the `.kicad_pcb`, not from the SVG exports** — the SVGs
carry a DPI-scaling risk and lose the per-part rotations (the split72 thumb keys
run up to 20° off axis). `parts/diffuser/gen_diffuser_frame.py` is the worked
example; the `investigate-kicad-pcb` skill covers reading boards generally.

⚠️ **STL format is per part group, and the repo is genuinely mixed — check the
neighbours before exporting.** An earlier version of this file claimed "STLs in
this repo are ASCII"; that is true only of the **diffuser frames**. Everything
else — keycap stems, inserts, cases, spacers — is **binary** (the files start
`OpenSCAD Model`, not `solid`), because they were exported from the GUI, whose
default is binary. Neither format diffs usefully, so the rule is **match the
sibling files in the same export folder**, which is what the two build scripts
already do (`--export-format asciistl` for the frames, `binstl` for the stems).
It matters beyond taste: `check_frame.py`'s `load_stl()` parses ASCII only and
refuses a binary file outright, so an ASCII→binary slip on a frame turns a
verification into an error.

## KiCad boards (`poly_kybd/`)

The `investigate-kicad-pcb` skill is the entry point for reading a board with Python.
Board-level facts that outlive any one investigation — the shared-sheet consequences, the
`poly_kb.pretty` extractions, the land-pattern reasoning and the re-route cost method —
are [`docs/KICAD_BOARDS.md`](docs/KICAD_BOARDS.md). Four that will mislead you first:

- ⚠️ **`*.kicad_sch` is authoritative. `poly_kb.net`, `poly_kb.xml` and the KiCad-5
  `.sch` files are NOT** — they are generated artifacts last touched 2024-02-17,
  describing a design **two board revisions old**. Nothing labels them stale, so they
  read as current; an AI reviewer filed a confident finding off one.
- ⚠️ **Grep for the PART, not the reference designator.** Symbol *instances* store only
  `reference` and `unit`; `Value`/`Footprint`/`MPN` are symbol-level and shared by every
  instance of a hierarchical sheet, so `grep '"U24"'` finds nothing while U24 sits happily
  on the board. Search by value, `lib_id`, or footprint name.
- **A shared sheet cannot vary a part per board.** All four boards include
  `rp_pico.kicad_sch`, so a `Value`/`Footprint` change lands on split72 *and* split42.
  There is no per-instance override.
- ⚠️ **The JLC fab exporter builds the BOM from the BOARD's footprint properties, not the
  schematic — and *Update PCB from Schematic* does not refresh them by default.** A
  correct schematic still exports a wrong BOM; that ordered a DFN part onto an LGA-8 land
  once. Sweep board-vs-schematic `MPN`/`LCSC` after every export, and read
  `poly_kybd/Gerber/PCB/FABRICATION-NOTES.md` first.

## OpenSCAD

The CLI is **2021.01** (CGAL backend only — there is no Manifold backend here, so advice
that starts "switch to Manifold" does not apply).

```bash
openscad -o out.stl --export-format asciistl part.scad          # no display needed
xvfb-run -a openscad -o view.png --render=cgal part.scad        # display IS needed
```

⚠️ **To LOOK at a part, use the existing wrapper** —
`.claude/skills/explain-geometry-figure/scad_view.sh` takes
`out.png model.scad [top|front|iso|<camera>]` and handles both camera forms. It did not
get used once: a session spent ~12 hand-built invocations while the wrapper sat one
directory away. **Search the skills for a helper before writing one** —
`grep -RIn '<what you need>' .claude/skills/`.

The camera traps, the render-framing rules and the full write-up are
[`parts/OPENSCAD_NOTES.md`](parts/OPENSCAD_NOTES.md). Four that cost real time:

- ⚠️ **`use <x.scad>` resolves relative to the .scad FILE, not the cwd.** A helper in the
  wrong directory finds no modules, so the top-level object is empty — and for a
  collision test that is **indistinguishable from "no collision"**. It is a false PASS.
  **Always pair a clearance test with a positive control** that displaces the part and
  confirms the test still reports an overlap.
- ⚠️ **openscad exits `1` for an EMPTY result and `1` for a syntax error alike.** Test for
  the `Current top level object is empty` marker FIRST, then treat any remaining non-zero
  exit as a failure — backwards, and every clean no-collision result raises.
- **An empty top-level object writes no output file**, so a script reusing one output path
  silently re-reads the previous run's mesh. Give each invocation its own file.
- **STL export is not byte-reproducible** — facets come out in a different order run to
  run. Compare meshes as a **sorted facet multiset**, never with `cmp`, and put the
  committed bytes back when only the order moved.

## Verifying a printed part, and designing for resin

`parts/diffuser/build_frame.sh` is the whole loop — regenerate the `.scad` from the
board, export every STL, then verify with `check_frame.py` (watertight, minimum wall,
symmetry, plate trap, spacer clearance). Extend the verifier rather than re-deriving
these by hand; it reports FAIL rather than raising, because a gating script that crashes
on a malformed input tells you nothing about the design. The wall-thickness metric
comparison, the three resin design rules and their measurements are
[`parts/PRINT_VERIFICATION.md`](parts/PRINT_VERIFICATION.md). Four rules:

- **Picking a wall-thickness metric is itself the hard part.** An inward-normal ray-cast
  is wrong near a corner (read 3.0 mm across a wall that was really 1.55); distance to
  the boundary is not thickness. For in-plane features, **rasterise the profile and apply
  a morphological opening** — the test a print service actually runs.
- **Report the AREA below a threshold, not the infimum.** Every polygon corner tapers to
  zero, so the minimum is always ~0 and tells you nothing.
- ⚠️ **A print service refuses below 0.8 mm**, and three shapes generate a wafer without
  looking like it: a tapered rim beside passing geometry, a `linear_extrude(scale=)`
  chamfer whose ANGLE changes when you change its height, and a minor circular segment
  ending in a knife edge.
- **Engraved text always leaves sub-0.8 mm relief** between strokes — it is surface
  relief, not a wall. Exclude the engraving zone from a wall check and assert the
  residual separately, and tell the vendor the same.
- ⚠️ **Identify an orphan mesh by RE-EXPORTING the candidate source and comparing**, not
  by its filename. Two meshes were grouped as a "case insert" on a filename prefix and
  turned out to be the tenting legs. Float noise means an exact facet compare returns
  False — compare rounded, or on count+volume+bbox.

## Keycap stems

**One `.scad` per plate in `parts/keycap_stem/variants/`** — `R1..R5` curved and
`S1`/`S`/`S5` stepped, each in `1U` and `1U25`, sixteen files over a library with **no
top-level geometry**. `build_stems.sh` walks the directory and holds no table, so
**adding a plate is adding a file**. The full notes — why `include` and not `use`, the
engraving field width, the font traps and the re-export comparison method — are
[`parts/keycap_stem/NOTES.md`](parts/keycap_stem/NOTES.md). Four things to know first:

- **`R1` and `S1` are deliberately identical geometry**, differing only in the engraving;
  and **flat IS R3** — same parameters, same mesh, so a flat stem and a curved set's R3
  are one interchangeable part.
- ⚠️ **The engraved revision silently renders in the WRONG FACE when Noto is absent** —
  fontconfig substitutes rather than failing, and nothing in the output mentions it.
  `build_stems.sh --fetch-font`, but ⚠️ **use it to acquire a Noto where there is none,
  never to "refresh" one**: a variable NotoSans and a static NotoSans-Bold disagree, and
  every later re-export then reports CHANGED.
- **Judge a regenerated plate by bbox + volume, not by facet count** — text tessellation
  depends on the installed font version, so the triangle count moves between machines
  while the part is unchanged.
- ⚠️ **The README profile pictures draw the coordinate AXES on purpose** — the horizontal
  axis is the REFERENCE the cap angle is read against. **Never rotate the row to make the
  profile read better**: a view tilt adds itself to every cap angle without moving the
  axes, which made R3, flat by definition, sit 8° nose-up. Tilt the **camera** instead.
- ⚠️ **A full `build_stems.sh` run exceeds a two-minute tool timeout.** Pass name filters
  or background it; a run killed part-way leaves the plates it reached re-exported.

## Drawing a finding

When a measurement needs to convince someone who cannot run the script — a print
service, most obviously — use the **`explain-geometry-figure`** skill. It produces
a dimensioned SVG/PNG with the numbers drawn on the shape.
