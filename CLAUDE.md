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
`keycap_stem` (the printed plates, plus the moulded STEP + drawing pipeline
under `keycap_stem/step/`), `display_holder`, `cirque_insert`, `cover_insert`,
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
was search, not design.** Search the skills for a helper before writing one —
recursively, since each skill is its own directory:
`grep -RIn '<what you need>' .claude/skills/`.

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
  - **The axis you `translate()` the row along must match the camera's `rotz`** —
    the model's own layout, *not* the camera's `transx,y,z`. At `rotz=0` the
    model's X runs horizontally on screen, at `rotz=90` it is Y. Lay a row out
    along the wrong one and the parts stack in DEPTH — they overlap into a single
    blob, which looks like a geometry failure, not a viewpoint. Cost three renders
    before it was obvious.
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

## build123d / OpenCASCADE (the `step/` folders)

Anything a **fabricator's validator** has to accept — the CNC case, the injection-moulded
keycap stems — is **re-authored in build123d** rather than exported from OpenSCAD, because
OpenSCAD has no B-Rep kernel. `parts/case/step/` and `parts/keycap_stem/step/` are that
pipeline; each carries its own README and a `make` that builds, validates and (stems)
diffs the result back against the `.scad`. The traps that cost real time:

- ⚠️ **`Shape.scale()` scales about the SHAPE'S OWN LOCATION, not the origin** — and
  `linear_extrude(scale=)` scales the whole profile about the extrusion axis, so an
  off-centre sub-shape has to move inward as well as shrink. Left at the default the model
  still builds, still passes `BRepCheck_Analyzer`, and its tapered feature simply tapers at
  a third of the intended rate (measured: the stems' MX cross came out 4.074 instead of
  3.987 at the far end, +0.5 % volume). Nothing errors. Pass `about=(0, 0, 0)`, and check a
  tapered prism against its closed form — `A0·h·(1 − t + t²/3)` for a `1−t` taper — which is
  what caught it.
- **`loft` between two rectangles gives B-SPLINE sides; a convex hull of the 8 corners gives
  real planes.** Same solid, different surfaces: OCCT's ThruSections returns even a planar
  trapezoid as a degree-1 B-spline patch. Hulling the corners took the stem from 36 planar /
  62 free-form faces to 82 / 16. Worth doing wherever the flats are datums. ⚠️ **More
  ANALYTIC faces is not automatically better, and can be the tell of a bug**: a tapered
  off-centre arc is an *oblique* cone (its centre moves as its radius shrinks), so it must
  come back as a B-spline — the same model built with the `Shape.scale()` centre bug above
  reported 13 tidy `Geom_Cone` faces, because holding each centre fixed makes them right
  circular.
- **OpenSCAD `hull()` of polyhedra is exactly reproducible** — the convex hull of polyhedra
  is a polyhedron, so hull the vertices and merge the coplanar simplices back into n-gons
  (`parts/keycap_stem/step/hull3d.py`). Skipping the merge exports the ~60 triangles scipy
  hands back, which is the facet noise the whole exercise exists to remove.
- ⚠️ **`BRepBndLib.Add_s` on an un-meshed shape boxes the underlying SURFACES, not the
  trimmed faces**, so a cut whose prism runs past the solid inflates the bounding box — it
  reported z_max 11.30 for a stem that tops out at 7.91, and the metal case by up to 2.1 mm.
  Use `AddOptimal_s`. The printed bbox is what the recipes say to compare against the old
  mesh, so it has to be the real one.
- ⚠️ **build123d's drafting module cannot carry a full drawing sheet: OCCT's
  `Compound.make_text` SEGFAULTS.** Deterministically, on the 14th label, once the sheet
  holds the frame plus projections plus a section plus dimensions — with ~500 MB resident
  and 14 GB free, and with none of the ingredients crashing on its own. `drawing.py` takes
  geometry from build123d and **writes the SVG itself with real `<text>`** (the same shape
  as `parts/case/step/plate_svg.py`); the file is 200 KB instead of megabytes and the
  dimensions stay selectable. Related: `ExtensionLine` has no fallback for a label wider
  than its dimension line and dies with `Can't determine direction of empty Edge or Wire`
  several frames away.
- ⚠️ **A drawing sheet laid out by hand-tuned offsets WILL collide, and the SVG source
  never shows it — measure the sheet instead.** Two guards in `drawing.py`, both of which
  found real defects that had survived every code reading:
  - **`Sheet.group()`** collects the extent of everything drawn inside it, and view titles
    are placed from that rather than at a guessed `dy`. The guesses were wrong in both
    directions: V1's height dimension ran back across the part, and V2's title landed
    nearer the view *below* it than the view it names — which on a first-angle sheet is
    the part's own projection, so the label read as belonging to the wrong view. Titles go
    **above** all views for the same reason. Anything added to a view now moves its title.
  - **`Sheet.report_collisions()`** lists every label overlapping another label or a
    visible outline, and **`check_inside_frame()`** raises on anything off the border. Run
    them on every build; six overlaps and three overflows were live when they were added.
  - **Wrap the notes in CODE, and flow them into two columns.** Every note interpolates a
    measured value, so a hand-wrapped line overruns silently the moment a number gains a
    digit — the block had reached 2 mm off the frame. ⚠️ Two traps in the wrapper itself:
    the wrap width must allow for the hanging indent or a continuation line runs into the
    next column, and `text.split(" ")` eats the second space of a sentence gap, quietly
    reflowing the whole sheet's spacing.
  - **Line weight is an ISO 128 GROUP (0.35/0.18 or 0.5/0.25, thick : thin = 2 : 1), not a
    free choice per line.** 0.5/0.25 is right for a sparse sheet and reads as ink on a
    dense one; pick the group for the sheet and do not mix.
    ⚠️ The collision report only tracks **thick** (visible-outline) paths, so a label
    sitting on a dimension line or a thin isometric outline still passes — the 1.25U sheet
    (whose leaders reach 4.4 mm further out than 1U's) had exactly that, and only the
    render showed it. **Render both variants, not just the one you were editing.**
- ⚠️ **Get a cutting-plane arrow's direction from the section PLANE, not by eye.**
  build123d's `Plane.XZ` carries its normal on **-Y** and `Plane.YZ` on **+X**, so two
  sections of the same part are viewed from opposite senses and their arrows point
  opposite ways on the same plan view. Reason it out of the plane's `z_dir`; a guess is
  right half the time and a reversed arrow tells a fabricator to keep the wrong half.
- ⚠️ **A dimension's LABEL will outlive the geometry it was written from — check it
  against the model, not against the variable name.** The stem sheet carried "5.05 slot
  depth" through three revisions; the number is the height of the stem *boss*, and the
  slot is not bounded by it at all (the cross is cut clean through into the cap floor).
  The real bound has no closed form — the cap floor is tilted — so it is now bisected
  for. Same shape as the ink-measurement rule above: the source said `h_cyl` and the
  label said what someone assumed `h_cyl` meant.
- ⚠️ **Draw anything a reader could get backwards; do not describe it.** The stem sheet
  said the second stamp was "mirrored … reads correctly from below" for three revisions.
  It is `rotate([180, 0, 0])` — TURNED, not mirrored: it reads normally when the part is
  flipped front-to-back, and appears upside down in a projected view-from-below. Nobody
  caught it because an `S` is 180°-symmetric and only the `β` shows the difference. It
  was caught the moment the view was actually drawn and the picture disagreed with the
  caption.
- ⚠️ **A STEP re-export rewrites the file even when the solid is byte-identical** (the
  header carries a timestamp), so `make` always leaves both files "modified". Check
  below the header before committing —
  `diff <(git show HEAD:<path> | tail -n +12) <(tail -n +12 <path>)` — and `git checkout`
  when it is empty, or you commit 1.3 MB of clock. Same rule as the STL facet-order note
  above, different mechanism.
- ⚠️ **Hatch a section with thin RECTANGLES, not lines.** A line lying exactly in the
  section face's plane makes OCCT's edge-face common return **nothing at all**, silently —
  so an empty hatch reads as "no solid here" rather than as an error. Below ~0.05 mm the
  rectangle vanishes into the boolean tolerance too.
- **Diff the re-authored solid against the `.scad` both ways, and prove the diff can fail.**
  `parts/keycap_stem/step/verify.py` measures the critical feature off a section of the real
  solid, compares volume + bbox against an OpenSCAD export of the same call, and runs
  `A\B` and `B\A` through OpenSCAD; `--self-test` widens the MX cross by 0.10 mm and
  asserts the checks reject it. That self-test also shows why the cheap check is not enough:
  a 0.10 mm error on the one tolerance-critical feature is **+0.66 % volume**, i.e. it sails
  through a 1 % volume gate while the boolean diff and the direct measurement both catch it.
- ⚠️ **Engraved text is where three SILENT font traps live, and each one changes the glyph
  a toolmaker would cut.** (1) OCCT does **not** read fontconfig, so `font="Noto"` — what
  `keycap_stem.scad` asks for — prints *"unable to find font 'Noto'; 'FreeSans' is used
  instead"* and carries on; (2) the real family name `"Noto Sans"` finds the file but
  renders the **variable font's default instance**, not Bold; (3) OpenSCAD's `text(size=)`
  is a **point size at 100 DPI** while build123d's `font_size` is the em in mm, so the same
  nominal 3 comes out **100/72 = 1.389× larger** in OpenSCAD. Measured on one string: areas
  4.068 / 2.330 / 3.563 mm² for the three spellings, and cap height 3.058 vs 2.202 mm for
  the size convention. Pin the font to a FILE (`parts/keycap_stem/step/font.py`
  instantiates `wght=700` and passes `font_path=`) and convert the size. Trap (3) is the
  same shape as `fontconvert`'s `-s` being points at 141 DPI.
- ⚠️ **Noto Sans draws U+03B1 single-storey and TAILLESS, so the engraved `α` reads as a
  Latin `a`** — the printed plates have carried the ambiguous glyph all along, and it is a
  font-design fact, not a substitution bug (the cmap maps `alpha` and `a` to different
  glyphs; DejaVu's alpha has the usual right-hand tail, Noto's does not). Check a revision
  marker by RENDERING the glyph, not by confirming the codepoint. The **moulded** stems
  moved to `β` for this reason and a better one: they differ from the 3D-printed
  prototypes, so `parts/keycap_stem/step/stem_model.py` `REVISION` is deliberately **not**
  a mirror of `keycap_stem.scad:2` — the one constant there that isn't.
- ⚠️ **`build_stems.sh --fetch-font` FETCHES AND THEN RE-EXPORTS ALL SIXTEEN PLATES.** Its
  name and its help line both read as "install a font", and CLAUDE.md already warns that it
  changes which Noto resolves — but with no variant names it also runs the whole export
  loop, so committed meshes get rewritten against the new font. It rewrote three before
  being killed (2026-08-19). Use `make -C parts/keycap_stem/step font`, which shares the
  same cache path and stops after the download.
- ⚠️ **Find a feature by what it IS, not by "the smallest face".** A section-measuring check
  that took the smallest face in the plane silently started reporting the inside of an
  engraved `α` — 0.90 × 1.30 with r0.60/0.84, entirely plausible numbers for an MX cross —
  once the stamp was switched on, because the cap is tilted −7° and that sweeps the
  engraving through the section height. Select on identity (an inner wire centred on the
  stem axis, smaller than the stem OD), not on an ordering that happens to work today.
- **Read a constant's MEANING out of the `.scad`, not its name.** Two in `keycap_stem.scad`
  read as one thing and are another: `u_size = 1.22` is a half-width-extension dial fed to
  `(u_size − 1)·2·5`, not a keycap unit count; and `mx_cross` 4.35 / `mx_cross_width` 1.4
  describe the plus *before* `offset(r = −0.3)`, so the MX opening is **4.05 × 1.10**.
  Quoting either to a fabricator is a 0.3 mm error on the part's one critical fit.

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

⚠️ **That is the PRINTED part. The MOULDED one is a different pipeline** —
`parts/keycap_stem/step/` re-authors the same `mx_stem()` in build123d and emits
`export/keycap_stem/stem_S_{1U,1U25}.step` plus an A3 drawing, for the injection
moulder. Only the `S` profile is exported, and it carries the **same** geometry as
the printed plates with one deliberate difference: the revision stamp reads **β**,
not the plates' α, because a moulded part differs from the printed prototypes and
the two have to be tellable apart by eye (`stem_model.REVISION` is therefore the one
constant in that file that is *not* a mirror of `keycap_stem.scad`). A change to
`keycap_stem.scad` has to be re-exported on BOTH sides — `build_stems.sh` and
`make -C parts/keycap_stem/step`; `make verify` there is what tells you the two
still agree.

- ⚠️ **The three 0.4 × 3.0 × 0.3 tabs are a FUNCTIONAL click feature, not a print
  aid** — they stand 0.2 mm proud and are what makes the transparent relegendable
  cap click on. An earlier reading of `keycap_stem.scad` had them down as a
  sprued-plate artefact, and the first draft of the drawing invited the moulder to
  delete them; both were wrong. They are named (`CLICK_TAB_*`), dimensioned on the
  sheet, and note 10 says explicitly that they must not be removed. The general
  lesson: a small feature with no comment is not thereby decoration — ask before
  writing "optional" onto a fabrication drawing, because that is the one document
  the shop will act on without asking back.

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
