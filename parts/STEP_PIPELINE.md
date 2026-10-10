# The STEP pipeline (`parts/*/step/`)

Anything a **fabricator's validator** has to accept — the CNC case, the injection-moulded
keycap stems — is **re-authored in build123d** rather than exported from OpenSCAD, because
OpenSCAD has no B-Rep kernel. `parts/case/step/` and `parts/keycap_stem/step/` are that
pipeline; each carries its own README and a `make` that builds, validates and (stems)
diffs the result back against the `.scad`.

The rules that bind code *outside* these folders are in
[`../CLAUDE.md`](../CLAUDE.md); everything below is what you need once you are inside one.

## The traps that cost real time
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
- ⚠️ **The brand mark is the P, and it is `polyfabriq_logo.svg` at the repo root —
  NOT `poly_kybd/logo.svg`.** Both are a rounded key grid and they look alike in a
  file listing; only one spells a letter, as the white counter inside the grid.
  `poly_kybd/logo.svg` is the keycap mark (identical artwork to the docs site's
  `polykybd-keycap.svg`), and it sat in the stem sheet's title block for two rounds
  because its path says `poly_kybd/` and its name says `logo`. Check by content:
  the P is a SINGLE `<path>`, identical to the docs site's `polytasten-logo.svg` and
  its favicon, and 4 KB against the other's 26 KB.
  - ⚠️ **Generalises past logos: when something is reported missing but the code
    plainly draws it, test ASSET IDENTITY before rewriting the MECHANISM.** "Use the
    PolyKybd logo" was read as *the logo is not reaching the page*, and answered by
    rebuilding the whole embed path on a hypothesis — that some viewer had dropped the
    nested `<svg>` — which could not be tested here, since the only renderer in the
    container drew it correctly. That rewrite was worth having on its own merits and was
    **not the fix**; the next sentence from the user ("I wanted the P") was. The cheap
    check comes first: render the candidate assets side by side and ask *which* of them
    the page is showing. A mechanism you cannot reproduce failing is a weak hypothesis
    however plausible it reads.
- ⚠️ **Do not emit a nested `<svg>` into a deliverable, and PARSE what you write.** The
  title-block logo was inlined by keeping the source file's own `<svg>` root and
  overriding its width/height — valid SVG 1.1, which Chromium renders, and the one
  construct on an otherwise plain sheet that a conforming-enough consumer may legitimately
  drop or sanitise away. When it is dropped the sheet silently loses the only mark saying
  whose drawing it is, and everything else still renders. Keep the source's own
  `<g transform=…>` wrappers verbatim (a KiCad layer export's paths carry coordinates
  around 34…42 — lifting the `<path>`s out of the group scatters them off the sheet) and
  drop only the editor furniture: `<defs>`, `sodipodi:namedview`, and the ~570 empty `<g>`
  elements, which were 12 KB of every sheet.
  - ⚠️ **`<g … />` matches `<g[^>]*>`, so an "empty group" regex eats the next
    REAL closing tag.** The last of those 575 self-closing groups is immediately followed
    by the `</g>` that closes the group they all sit in; one pass deleted both, and the
    sheet became malformed XML. **Malformed SVG does not render partly — the browser
    gives up on the whole document and shows a blank page**, which reads as a path or a
    renderer problem, not as a defect in the sheet. `Sheet.write()` now parses the body
    before writing it, so the build fails instead.
- ⚠️ **A drawing sheet laid out by hand-tuned offsets WILL collide, and the SVG source
  never shows it — measure the sheet instead.** Two guards in `drawing.py`, both of which
  found real defects that had survived every code reading:
  - **`Sheet.group()`** collects the extent of everything drawn inside it, and view titles
    are placed from that rather than at a guessed `dy`. The guesses were wrong in both
    directions: V1's height dimension ran back across the part, and V2's title landed
    nearer the view *below* it than the view it names — which on a first-angle sheet is
    the part's own projection, so the label read as belonging to the wrong view. Titles go
    **above** all views for the same reason. Anything added to a view now moves its title.
  - ⚠️ **Sheet furniture that lives OUTSIDE the frame needs an exemption, and the
    cheapest one is to record it separately.** The ISO 5457 zone letters (1–8 / A–F on
    all four edges) sit in the margin by definition, so `check_inside_frame` failed
    them all. It now reads the recorded text extents rather than re-parsing the emitted
    SVG, which makes a `chrome=True` flag exempt from both the frame check and the
    collision report for free instead of needing a second rule in each.
  - ⚠️ **A cutting-plane mark is a SHORT stroke at each end, not a line across the
    view** (ISO 128-30 shows the plane only at its ends and at changes of direction).
    Drawn full length, the B-B mark ran the height of the plan view and through every
    horizontal dimension on it; the thin long-dash-short-dash centre line is what joins
    the two ends.
  - ⚠️ **Anything drawn outside a view's `group()` is invisible to its title.** The
    cutting-plane marks were, so the title was placed as though they were not there and
    landed exactly on the "B" tag — a collision the report found and the code reading
    would not.
  - ⚠️ **A box moves as you draw into it**, so a multi-line caption must snapshot
    `box[..][1]` before the loop; reading it again on line 2 puts that line below the
    floor line 1 just pushed down.
  - **`Sheet.report_collisions()`** lists every label overlapping another label or a
    visible outline, and **`check_inside_frame()`** raises on anything off the border. Run
    them on every build; six overlaps and three overflows were live when they were added.
  - **To LOOK at the result, use
    `.claude/skills/explain-geometry-figure/svg_view.sh`** — it crops a region in the
    FILE's own units (`svg_view.sh out.png sheet.svg x y w h [px_per_unit]`), so
    inspecting one view costs a line instead of a hand-built HTML wrapper and px/mm
    arithmetic. One session spent ~8 of those on a single drawing and got two of the
    crops wrong, while this repo had already written the same lesson about `scad_view.sh`
    and models. ⚠️ `drawing.py` works in SHEET coordinates (origin at the page centre,
    **+y up**), so a BOX needs both y bounds converted **and they swap** — the crop's
    top comes from the sheet's HIGHER y: `x = x0 + PAGE_W/2`, `y = PAGE_H/2 - y1`,
    `w = x1 - x0`, `h = y1 - y0`. Converting the lower y puts the crop one box-height
    too far down.
  - **Wrap the notes in CODE, and flow them into two columns.** Every note interpolates a
    measured value, so a hand-wrapped line overruns silently the moment a number gains a
    digit — the block had reached 2 mm off the frame. ⚠️ Two traps in the wrapper itself:
    the wrap width must allow for the hanging indent or a continuation line runs into the
    next column, and `text.split(" ")` eats the second space of a sentence gap, quietly
    reflowing the whole sheet's spacing.
  - **Line weight is an ISO 128 GROUP (0.35/0.18 or 0.5/0.25, thick : thin = 2 : 1), not a
    free choice per line.** 0.5/0.25 is right for a sparse sheet and reads as ink on a
    dense one; pick the group for the sheet and do not mix.
    ⚠️ **"Wide" in ISO means the GROUP'S wide width, not a step above it** — so the
    cutting-plane line is 0.35 in a 0.35/0.18 sheet, the same as the visible outline.
    It was 0.5, under a comment asserting ISO 128-30 required that and three lines under
    another comment saying not to mix groups. What makes a cut mark read is the 2 : 1
    contrast against the thin centre line joining its ends, which the group already
    gives you.
    ⚠️ The collision report only tracks **thick** (visible-outline) paths, so a label
    sitting on a dimension line or a thin isometric outline still passes — the 1.25U sheet
    (whose leaders reach 4.4 mm further out than 1U's) had exactly that, and only the
    render showed it. **Render both variants, not just the one you were editing.**
- ⚠️ **A detail view of a face needs the face's own DATUM in it, and `cap_body` has
  none.** The two stamp details drew a rectangle with two letters in it and nothing to
  locate them from, because `stamp_face()` takes its face from `cap_body`, which has no
  MX slot — `mx_stem` cuts the cross *after* tilting and raising the cap. Pull the same
  cross back through that placement (`Rot(-angle) * Pos(0,0,-extra_len) * cross_cut(…)`)
  and cut it into the cap body, and the slot appears in the detail. ⚠️ Keep placing the
  stamp against the UNCUT face, as `_engraving` does — centring it in a face with a hole
  in it moves it.
- ⚠️ **A snap helper earns its keep by REFUSING.** The stem sheet's `snap` rejected a
  dimension anchor — *"no section vertex within 0.6 of (-5.65, 4.52)"*, and only on the
  wider variant — and the vertex pair confidently labelled "the flange" turned out to be
  the inside of the pocket, which moves with `u_size`. Taking the nearest corner quietly
  would have shipped a wrong label on one variant and a wrong anchor on the other.
  Corollary: **name a dimension by what it MEASURES when you have not verified which
  feature it is.**
- ⚠️ **Derive a scale caption from the number that drew the view.** It was a literal
  beside each view's title; the isometric's scale went 1.6 → 2.4 and the caption went on
  saying 1.6:1 — on the one label a reader might actually measure against.
- ⚠️ **Anchor every section dimension on a REAL VERTEX of the cut, and make the helper
  raise when it cannot.** Dimensions computed from model constants are what "floating in
  the air" looks like: the display seat is 1.10 below a top face tilted −7°, so the
  height the arithmetic names is not a height anything on that cut actually has. `snap()`
  takes the nearest section vertex and raises past a tolerance — a silent snap to the
  wrong corner is a wrong number on a fabrication drawing, which is worse than a build
  that stops.
- ⚠️ **A dimension line is not automatically better than a leader — on a section it is
  frequently worse.** A feature in the middle of a cut (the stem boss behind the outer
  skirt) can only be dimensioned by dragging extension lines across hatched material to
  reach the outside. A leader touches the vertex the number comes from and crosses
  nothing.
  - **Anchor it on the wall NEAREST the note.** Both walls of a Ø5.50 boss are the same
    feature, so either is geometrically correct and nothing in the model says which to
    pick — but a leader to the far wall crosses the whole cut, and the reader has to work
    out that it means the cylinder rather than whatever it passed over on the way. The
    short reach is also what keeps the note out of the neighbouring view.
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
  - ⚠️ **Three separate things then decide whether it reads as hatching or as scribble,
    and the first draft had all three wrong.** They generalise to any ruled fill.
    **(1) Order the sliver along the RULING.** The rulings ran along `(-sin a, cos a)`
    while their two ends were picked along `(cos a, sin a)` — the perpendicular, on which
    a sliver's projection is near-constant, so "the ends" were two arbitrary corners of
    it. That alone produced the ragged, unequal, randomly-short rulings.
    **(2) ONE lattice for the whole cut, not one per face.** Each face was ruled from its
    own bounding-box centre, so two faces of one cut carried the same spacing at
    different *phases* — and on a section, hatching out of step means two materials.
    **(3) Clamp the sliver to the ruling's CENTRE LINE, not to its own corners.** A strip
    has width, so at an angled boundary its furthest corner lies past the centre line's
    true crossing: that is hatching running outside the outline. Trimming a fixed
    percentage off each end (the first fix) cures it by leaving *every* ruling short of
    the outline instead, and takes as much off a 1 mm ruling as off a 10 mm one. Project
    the corners onto the centre line and both ends land exactly on the boundary — which
    also makes the strip width free above the floor above (counted on both cuts: 0.02,
    0.04, 0.06 and 0.10 mm return the same rulings).
- ⚠️ **A positive control needs its NEGATIVE half, or it passes for the wrong reason.**
  `verify.py --self-test` widens the MX cross and asserts the checks catch it — the
  discipline this file already preaches. Its cross-measurement half kept its own copy of
  the expected span with the taper omitted, which is 0.0033 mm at z = 0.30, i.e. above
  its own 2e-3 threshold: it therefore reported "caught" against a **correct** model and
  asserted nothing. Two fixes, both general: give the two call sites **one** shared
  definition so they cannot drift (`cross_span()`), and assert the comparison is
  **quiet on the unmodified model** as well as loud on the broken one. Same family as
  the gtest-ANSI and never-applied-mutation traps in `qmk_firmware/CLAUDE.md`: every one
  of them is a harness reporting the answer that means "your checks are worthless" and
  reading as success.
- ⚠️ **A verification that never opens the SHIPPED file verifies the code, not the
  deliverable.** Checks 0-3 all ran on a solid built in memory, so `make verify` was
  green against a stale export, a half-written one, or one built by another build123d —
  the three ways the committed STEP can actually be wrong. Check 4 re-imports the
  artifact and compares it back. The general form: when a target's whole purpose is to
  bless a file, it has to read that file.
- ⚠️ **A check that cannot run must FAIL, not skip.** Missing openscad made checks 2 and
  3 — the entire `.scad` parity argument — quietly vanish while the run still printed
  `PASS`, i.e. it reported success having compared the stem against nothing. Same family
  as the fail-open self-test above: the dangerous outcome is never the loud one. The
  escape hatch (`--allow-no-openscad`) exists, names itself in the output, and is not
  the default.
- ⚠️ **Gate a check on the dependency IT needs, not on the one the block around it
  needs.** The closed-form cross-prism check — the one that caught `Shape.scale()`
  above — sat under `if not have_scad: continue`, so a machine without **openscad**
  silently dropped the most valuable check in the file for an unrelated missing tool.
- ⚠️ **Pin the engraving font by DIGEST, and remember the cache is shared.** The β/S
  outlines cut into a steel cavity come from a `main` URL, so an upstream change
  silently alters tool geometry; `font.py` verifies SHA-256 and stops with instructions.
  ⚠️ `build_stems.sh` fetches the same URL into the same cache with no verification, so
  a mismatched cache is **re-downloaded, not rejected** — rejecting would fail on a file
  the sibling script legitimately put there. Only a fresh download that still mismatches
  is fatal, and changing the digest means re-exporting both STEPs.
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


## The moulded keycap stem specifically
- **The MX slot is deliberately TIGHTER than Cherry's published keycap slot — this
  table is the reasoning, and it lives here rather than on the drawing.** It was a
  block on the sheet for two revisions; it is background for us, not an instruction to
  a moulder, so the drawing now carries only the conclusion (note 1: gauge against a
  real switch stem, and the relief bulges are what make the fit work).

  | | this part | Cherry keycap spec | real switch stem |
  |---|---|---|---|
  | slot across | 4.05 (bulges 4.11) | 4.10 +0.05 | — |
  | arm width | 1.10 (bulges 1.21) | 1.17 ±0.02 | N/S 1.05–1.10, E/W 1.25–1.30 |
  | corner fillet | R0.30 | not published | — |
  | lead-in | 4.61 sq × 0.30 | not published | — |

  Cherry's keycap slot spec via deskthority / telcontar.net. The switch stem's own cross
  is **asymmetric** and Cherry's uniform 1.17 slot already interferes ~0.07 on two sides;
  ours is tighter still, so the fit rests on the four relief bulges. Verify on a moulded
  first article, not by CMM.
- **Provenance, also deliberately off the sheet:** the moulded geometry is re-authored
  from `keycap_stem.scad` in build123d, and `verify.py` is what keeps the two agreeing.
  The STEP is the shape reference and the drawing governs tolerance, material and
  finish — that division is worth stating to a fabricator, and *is* on the sheet; where
  the shape came from is ours.
- ⚠️ **The three 0.4 × 3.0 × 0.3 tabs are a FUNCTIONAL click feature, not a print
  aid** — they stand 0.2 mm proud and are what makes the transparent relegendable
  cap click on. An earlier reading of `keycap_stem.scad` had them down as a
  sprued-plate artefact, and the first draft of the drawing invited the moulder to
  delete them; both were wrong. They are named (`CLICK_TAB_*`), dimensioned on the
  sheet, and note 4 says explicitly that they must not be removed. The general
  lesson: a small feature with no comment is not thereby decoration — ask before
  writing "optional" onto a fabrication drawing, because that is the one document
  the shop will act on without asking back.

## Why the build123d pin exists

_Moved verbatim from `CLAUDE.md` on 2026-10-10._

- ⚠️ **BOTH pipelines pin their toolchain (`BUILD123D_PIN`, currently 0.12.0) and
  refuse to run on another version.** The geometry is version-sensitive: 0.13.0 projects
  the stem sheet
  materially differently (111 of 2087 paths, 8 of them structural, a 43 mm coordinate
  delta) and rewrites the STEP below its header too, so an unpinned `pip install`
  silently rewrites a fabrication deliverable. The check is an ORDER-ONLY prerequisite
  of the outputs, which means it runs on `make`, `make step`, `make drawing` and
  `make verify` alike, **including when every output is already up to date** (verified:
  a wrong pin exits 2 on all four with nothing to rebuild) — an order-only prerequisite
  is still updated, it just does not drag the target with it. That property matters more
  in `case/step/`, where a needless rebuild costs ~15 minutes (903.7 s for the right side
  alone). The case pin is **verified, not assumed**: rebuilding on 0.12.0 reproduces the
  committed `metal-case-left.step` byte for byte below the header, and
  `metal-case-right.step` to one DIRECTION written `(-0.,-0.,-1.)` rather than
  `(0.,0.,-1.)` — the same direction, since `-0.0 == 0.0`.
  **Compare a re-export as an unordered POINT MULTISET, never byte-wise** — even on the
  right version the SVG path order is not stable RUN TO RUN on one machine (18-55
  segments reshuffle, geometry and text identical), the SVG analogue of the STL
  facet-order rule below. So a byte diff is noise by default, and it cannot tell that
  noise apart from a real geometry change.
