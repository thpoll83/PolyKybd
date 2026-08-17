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

## OpenSCAD

The CLI is **2021.01** (CGAL backend only — there is no Manifold backend here, so
advice that starts "switch to Manifold" does not apply).

```bash
# export geometry -- no display needed
openscad -o out.stl --export-format asciistl part.scad
# render a PNG -- display IS needed
xvfb-run -a openscad -o view.png --imgsize=1000,700 --camera=… --render=cgal part.scad
```

⚠️ **To LOOK at a part, use the existing wrapper — don't hand-roll the flags.**
`.claude/skills/explain-geometry-figure/scad_view.sh` takes `out.png model.scad
[top|front|iso|<camera>]`, handles the missing-display and empty-PNG traps, and
documents both `--camera` forms (7 numbers = gimbal `transx,y,z, rotx,y,z, dist`;
6 = `eye, centre`). It was written for that skill's figures but is a general
viewer. This is worth stating because it did not get used: a session spent ~12
hand-built `--camera`/`--imgsize`/`--render` invocations, and five of those were
wasted purely on camera geometry, while the wrapper sat one directory away in
this repo (2026-08-17). Same lesson as the control-server deadlock in
`PolyKybdHost/CLAUDE.md` — **the remedy was already in the tree and the failure
was search, not design.** Grep `.claude/skills/*/` for a helper before writing one.

Four traps, each of which has cost real time:

- ⚠️ **`use <x.scad>` resolves relative to the .scad FILE, not the cwd.** A helper
  written in the wrong directory silently finds no modules, so the top-level
  object is empty — and for an intersection test that is **indistinguishable from
  "no collision"**. It is a false PASS, not an error. **Always pair a
  clearance/collision test with a positive control** that displaces the part a
  couple of mm and confirms the test still reports an overlap;
  `parts/diffuser/check_frame.py` does exactly this.
- ⚠️ **openscad exits `1` for an EMPTY result and `1` for a syntax error alike**
  (both verified). So the return code cannot classify the outcome: test for the
  `Current top level object is empty` marker **first**, then treat any remaining
  non-zero exit as a failure. Getting this backwards makes every clean
  no-collision result raise.
- **An empty top-level object writes no output file**, so a script that reuses one
  output path across several runs will silently re-read the *previous* run's mesh.
  Give each invocation its own output file.
- **`$fn` set at your top level does NOT override a `$fn=` hard-coded inside a
  module's primitives.** The facets you see are the facets the STL has.
- ⚠️ **Framing a render: `--viewall` is loose, and `rotz` decides which model axis
  runs across the screen.** Two separate camera traps, both of which read as a
  broken model rather than a bad camera:
  - **`--viewall --autocenter` fits the bounding SPHERE**, so a wide, shallow
    subject (a row of parts) comes out small in a sea of margin — ~60% dead space
    on a 5-stem lineup. Give an explicit `dist` instead and tune it; that is also
    the ortho scale in the 7-number form.
  - **The translate axis must match `rotz`.** At `rotz=0` the model's X runs
    horizontally, at `rotz=90` it is Y. Lay a row out along the wrong one and the
    parts stack in DEPTH — they overlap into a single blob, which looks like a
    geometry failure, not a viewpoint. Cost three renders before it was obvious.
  - Useful `rotx` values, gimbal form: `0` top, `90` pure side, `180` straight up
    at the underside (what "from the backside" usually means for a keycap),
    `70`–`80` a 3/4 that still shows the top face.
- **STL export is not byte-reproducible.** Facets come out in a different order
  run to run, so re-exporting an *unchanged* design still rewrites the whole file
  (23k lines of diff on one frame), burying any real change. Compare meshes as a
  **sorted facet multiset**, not with `cmp` — and when only the order moved, put
  the committed bytes back. `parts/diffuser/build_frame.sh` does this automatically;
  the same trick is what proves a refactor left the solid alone.

`use <>` imports a file's modules and **ignores its top-level geometry**, which is
how `parts/diffuser/diffuser.scad` can render a whole print plate on its own while
`diffuser_frame_*.scad` pulls just `diffuser()` out of it. ⚠️ `led_caps.scad`
(the superseded earlier generation, kept beside it) defines `diffuser()`,
`diffuser_cluster()` and `torus()` under the SAME names — so a file that
`use <>`s both silently gets one set of definitions.

## Verifying a printed part

**`parts/diffuser/build_frame.sh` is the whole loop** — regenerate the `.scad` from
the board, export every STL (both frames plus both stacked ones), then verify.
Run it after any edit to `diffuser.scad` or the generator; `--no-4x` skips the
slow stacked exports for a quick iteration, `--check` verifies without exporting.
Doing the steps by hand is where they get missed: a `diffuser.scad` change alters
the stacked pair too, and forgetting them leaves those a revision behind.

`parts/diffuser/check_frame.py` is the verifier it calls: watertight, minimum wall,
left/right symmetry, plate trap, and spacer clearance in both flip orientations.
It exits non-zero on failure. Extend it rather than re-deriving these by hand —
and note it deliberately reports FAIL rather than raising, because a gating script
that crashes on a malformed input tells you nothing about the design.

**Picking a wall-thickness metric is itself the hard part** — three of them were
wrong before the fourth answered the question:

- **Inward-normal ray-cast on the STL** (what `min_wall()` does) is correct where
  two walls are parallel, which covers a plate-like part in z. It is **wrong near
  a corner**: the normal runs oblique to the far face and overestimates — it read
  3.0 mm across a wedge whose real wall was 1.55 mm.
- **Distance to the boundary is not thickness.** Every point near any edge scores
  low, so the "thin area" comes out enormous and meaningless.
- **For in-plane features, rasterise the profile and apply a morphological
  opening** (a disc of radius t/2 must fit). That is the test a print service
  runs, and it is what finally ranked an axis-aligned trim against a 45° one.
- **Report the AREA below a threshold, not the infimum.** Every polygon corner
  tapers to zero thickness at its apex, so the minimum is always ~0 and tells you
  nothing; how *much* material is thin is the number that decides anything.

⚠️ **Identify an orphan mesh by re-exporting the candidate source and comparing,
not by its filename.** Two meshes committed as `case_ins_r2.stl` /
`case_ins_leg_v0.stl` were grouped as a "case insert" on the strength of that
prefix, and separately guessed to be the plate-to-PCB spacer (they are 3.8 mm
thick, the same as `right_spacer()`, so the guess was reasonable). Re-exporting
`legs.scad` settled it in one command: same 32202 facets, same 5263.0 mm³, same
bounding box, 100 % of facets equal at 3 dp -- they are the **tenting legs**
(`connected_8p()`, 8 legs in 4 mirrored pairs). Now `export/legs/legs_r2_8p.stl`.
Float noise between OpenSCAD builds means an exact facet-set compare returns
False, so compare rounded, or on count+volume+bbox.

## Keycap stems

**One `.scad` per plate in `parts/keycap_stem/variants/`, over a library that has
NO top-level geometry** — `R1..R5` curved and `S1`/`S`/`S5` stepped, each in both
`1U` and `1U25`, sixteen files. Each `include`s `../keycap_stem.scad` and makes a
single call, so a variant renders on its own: what you open in the GUI is exactly
what gets exported, and `variants/<x>.scad` → `export/keycap_stem/<x>.stl` with no
name munging. `parts/keycap_stem/build_stems.sh` walks the directory and holds no
table of its own, so **adding a plate is adding a file**.

- **`include`, not `use`, in a variant.** `use` imports modules but *not*
  variables, and the engraved `revision` is a variable. That is also why the
  library must stay free of top-level geometry: `include` executes it, so
  anything left there would appear in all sixteen plates. The photo arrangements
  that used to sit at the bottom of the library live in `preview_stems.scad`
  (a `view=` selector), which the build script does not export.
- The profile set previously existed **only** as commented-out calls at the
  bottom of `keycap_stem.scad`, exported by uncommenting one line at a time —
  exactly how revAlpha shipped the stepped plates while the curved `R2..R5` were
  missing for a whole revision.
- ⚠️ **Verify a refactor here by re-exporting all sixteen — but expect only the
  plates YOUR machine last exported to report `unchanged`.** The library/variant
  split was checked this way and came back 8 `unchanged` / 8 `CHANGED`, split
  exactly along who exported what: the eight R2–R5 plates (exported in this
  container) were byte-identical, while R1 and the three S plates (exported by
  the author on their own machine) differed. That is **not** a refactor failure —
  each of the eight was confirmed to have an identical bounding box and a volume
  within 0.04%, i.e. only the engraving is tessellated differently, per the Noto
  note above. **Restore them (`git checkout`) rather than committing the
  rewrite**, or you trade ~16 MB of diff for a re-tessellated `α`. A single plate
  is not a sufficient check either way, since the two widths and the two profile
  families take different code paths.

- ⚠️ **The engraved revision silently renders in the WRONG FACE when Noto is
  absent.** `keycap_stem.scad` asks for `text_font = "Noto:style=Bold"`, and
  fontconfig substitutes (DejaVu Sans Bold in a bare container) rather than
  failing — the plate exports fine and nothing in the output mentions it. In a
  fresh container: `apt-get install fonts-noto-core`, or `build_stems.sh
  --fetch-font` (per-user, no root). `build_stems.sh` warns via `fc-match`,
  which is the only reason this is visible at all.
- ⚠️ **WHICH Noto also matters — `--fetch-font` on a machine that already has one
  will make every later re-export report `CHANGED`.** The engraving is tessellated
  from whatever file fontconfig resolves, and the downloaded *variable* NotoSans
  and a distro *static* NotoSans-Bold do not agree: measured 46192 vs 44912 facets
  on the same plate, at identical volume and bounding box. That is a real
  difference in the glyph outlines, well above what the settle rounding absorbs, so
  it is not a bug in the comparison — it is the comparison working. Use
  `--fetch-font` to acquire a Noto where there is none, not to "refresh" one.
- **`R1` and `S1` are deliberately identical geometry** (angle 5, extra_len 0.5)
  and differ only in the engraving. That is what the source says — don't "fix" it.
- **The engraved label matches the FILENAME's profile token, in a 5-character
  field.** `txt = str("R5   ", revision)` → the keycap reads `R5 α`. The field is
  padded to 5 so the profile sits at one corner of the top face and the revision
  at the other; keep that width when adding a profile (`"S    "`, `"R3   "`,
  `"S1   "` are all 5). It was not always so: the curved plates engraved a **bare
  digit** (`3 α`) while only the stepped ones carried a letter, so a printed stem
  could not be matched to the file that made it and "is the flat one R3?" was a
  question the part itself could not answer (2026-08-17). Note the consequence
  that survives: **flat IS R3** — same parameters, same mesh, same engraving — so
  a flat stem and a curved set's R3 are one interchangeable part, not two.
- ⚠️ **A full `build_stems.sh` run exceeds a two-minute tool timeout** (16 plates,
  CGAL each). Pass name filters (`build_stems.sh R1 R2 R3`) or run it in the
  background. A run killed part-way is not harmless: it leaves the plates it did
  reach re-exported, which then have to be told apart from a real change by bbox
  and volume before being reverted.
- ⚠️ **The README profile pictures draw the coordinate AXES on purpose — the
  horizontal axis line is the REFERENCE the cap angle is read against, and
  without it the images are five tilted caps with nothing to measure against.**
  The originals were GUI screenshots with the axes visible; a first scripted
  version dropped them as chrome and lost the one thing that made the pictures
  informative (field, 2026-08-17). Two rules follow, and they pull in opposite
  directions from the obvious instinct:
  - **Never rotate the row to make the profile read better.** A view tilt adds
    itself to every cap angle *without* moving the axes, so the picture reports
    the wrong profile: a `rotate([8,0,0])` in `profile_row()` made **R3, which is
    flat by definition, sit 8° nose-up on the axis**. Tilt the **camera** instead
    (`CAM` in `render_profiles.sh`) — that moves the axes with it, so the reading
    stays honest.
  - **Render with `--view=axes`** (2021.01 supports `axes`, `scales`,
    `crosshairs`, `edges`, `wireframe`). `scales` adds tick labels that render
    rotated and unreadable at this camera, so `axes` alone is the useful one.
  - The four views must share **one** camera or they cannot be compared —
    a difference in elevation reads as a difference in profile. That is the
    entire reason `render_profiles.sh` exists rather than a note about which
    camera to use.
- **Judge a regenerated plate by bbox + volume, not by facet count.** Text
  tessellation depends on the installed font *version*, so the triangle count
  moves between machines while the part is unchanged: regenerating the committed
  revAlpha R1 here reproduced its bounding box to 0.01 mm and its volume to
  0.01 % while the facet count differed by 2240. That comparison is what proved
  the commented "Curved Profile" parameters really are the alpha R-set.

## Design rules for resin-printed parts

A print service will quote a **0.8 mm minimum / 1.5 mm recommended** wall and
refuse the part if it measures below. Three ways this bit the diffuser frame:

- ⚠️ **A tapered rim beside passing geometry leaves a wafer.** A
  `linear_extrude(scale=)` rim sweeps its radius over its height, so *any*
  neighbouring wall whose edge lands anywhere in that band runs tangent to the
  slope at some height and leaves a near-zero-thickness sliver. On the frame this
  measured **0.043 mm** where a web stem passed a diffuser's bottom cap — an order
  of magnitude thinner than what the vendor complained about, and invisible until
  measured. **Use a vertical rim wherever other geometry passes close**: one
  radius means a neighbour can only clear it or merge with it.
- ⚠️ **`linear_extrude(scale=)` chamfers change ANGLE if you change their
  height.** The inward step is proportional to the *profile*, not the height, so
  thickening a flange by raising the chamfer layer lays the chamfer down (34.9° →
  21.8° when a flange went 1.0 → 1.5 mm). Keep the chamfer layer at its original
  height and put the extra thickness in the straight layer.
- ⚠️ **A minor circular segment ends in a knife edge.** `circle(d)` cut by a chord
  *above* centre runs out to nothing; the last fraction of a millimetre is what a
  vendor measures and rejects. Square the end off — and prefer a **cut that leans
  in plan** over an axis-aligned one: leaning opens the corner against the chord
  from 90° to 135° and spends the cut on the shallow strip, which measured **half
  the sub-0.8 mm area while keeping 4.4% more material**.

**Engraved text always leaves sub-0.8 mm relief** between glyph strokes — no pad
size fixes it, because legible text at any size that fits has strokes closer
together than the threshold. It is **surface relief, not a wall** (the full web
runs continuous underneath). Say so explicitly: exclude the engraving zone from a
wall check and assert the residual material separately, rather than reporting a
flattering number, and tell the vendor the same when they flag it.

## Drawing a finding

When a measurement needs to convince someone who cannot run the script — a print
service, most obviously — use the **`explain-geometry-figure`** skill. It produces
a dimensioned SVG/PNG with the numbers drawn on the shape.
