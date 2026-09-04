# Keycap stem → clean STEP + a technical drawing (build123d)

Re-authors the **S-profile keycap stems** (`../keycap_stem.scad`, `mx_stem()`) as real
B-Rep solids with [build123d](https://build123d.readthedocs.io/) (OpenCASCADE), and
draws each one on an A3 sheet, so an injection moulder can quote and cut without
guessing at facet noise. Follows
[`../../openscad-to-step-recipe-stems.md`](../../openscad-to-step-recipe-stems.md),
which follows the case's [`../../case/openscad-to-step-recipe.md`](../../case/openscad-to-step-recipe.md).

**Why not STL → STEP.** OpenSCAD has no B-Rep kernel, so its export is a facet soup
with loose stitching. On a stem that matters more than on the case: the feature that
decides whether the keyboard works is a ~1.1 mm MX cross, and a faceted cross is not a
datum anyone can cut to.

## Build

```bash
pip install build123d scipy fonttools   # OCP comes with build123d; fontTools
                                        # instantiates the Bold font instance
sudo apt-get install -y openscad     # only for `make verify`

make                 # -> ../../export/keycap_stem/stem_S_1U{,25}.step + _drawing.svg, validated
make verify          # diff the solid against the .scad it was ported from
make selftest        # prove those checks can fail (see below)
```

| file | what |
|---|---|
| `stem_model.py` | the model. Every constant keeps its `keycap_stem.scad` name so the two stay diffable |
| `hull3d.py` | OpenSCAD `hull()` as an exact polyhedral convex hull |
| `font.py` | pins the engraving to one font FILE (`make font`) — see the font traps below |
| `build.py` | exports `stem_S_1U.step` / `stem_S_1U25.step` (+ an STL the checks use) |
| `drawing.py` | the A3 sheet: ISO 5457 zone frame, V1-V4 ortho (V3 at 3:1), V5/V6 sections at 3:1, V7 cross 10:1, V8/V9 stamps, V10 isometric, notes |
| `validate_step.py` | the case's acceptance test, reused (real solid, curved faces, tight tolerance) |
| `verify.py` | measures the cross, diffs volume/bbox and booleans against OpenSCAD |

## What the two deliverables are for

**The drawing governs; the STEP conveys shape.** A solid model carries no tolerances, so
a toolmaker handed only a STEP cuts to the model and the tolerance question resurfaces at
first article. The sheet states a general tolerance and tightens only the MX cross and the
interface to the off-the-shelf transparent cap.

## Results

```
faces 142   planar 108   curved 34   max edge tolerance 2.1e-07 mm
volume vs the OpenSCAD mesh   +0.111 % (1U)   +0.081 % (1.25U)
bounding box                  identical to 5 decimal places
STEP \ SCAD 0.62 mm3 (0.11 %)   SCAD \ STEP 0.011 mm3 (0.002 %)
```

The residual is entirely the `.scad`'s tessellation — a 128-gon stem and `$fn=64` cross
relief — against true analytic surfaces, which is the difference the exercise exists to
remove. The exported solid carries the stamp (142 faces, 556.98 mm³ at 1U); without it,
100 faces and 562.00 mm³.

⚠️ **The `.scad` diff runs with the stamp OFF, on purpose** (`verify.py` `engrave = False`).
The moulded stamp is β and the `.scad`'s is α, so an engraved diff would report the
*intended* difference as an error on every run — and the ~5 mm³ of glyph would drown the
0.6 mm³ of tessellation the diff exists to see. The stamp is checked separately and better:
its clearance to the seat edge is measured on **both** faces (0.80 mm all round against the
0.80 mm requirement), which a volume comparison could never tell you.

## Decisions taken

- **Material is ABS**, stated in the title block. Its 0.4–0.7 % shrink is what keeps the
  MX cross inside its ±0.03. ⚠️ **The model and the STEP are the FINISHED PART** — shrink
  compensation goes on the cavity and is the toolmaker's, and note 9 asks them to state
  the rate they used.
- **The profile + revision stamp is engraved**, `S    β` (`build.py --no-engrave` drops
  it). Marking the revision on the part is the *point* — so drawing note 10 asks for it on
  a **replaceable insert** in the cavity rather than cut into the block, which makes the
  next revision a plug swap instead of a tool edit. Both stamps are 0.30 mm deep with zero
  draft, in the display-seat floor and the pocket ceiling; neither is a fit surface.
- ⚠️ **The moulded revision is `β` where `keycap_stem.scad` stays `α`** — different
  process, different tolerances, different tooling, so the two are told apart by eye.
  `stem_model.REVISION` is therefore **the one constant here that is deliberately NOT a
  mirror of the `.scad`**; everything else keeps its `.scad` name *and* value.
- ⚠️ **The pocket-ceiling stamp is TURNED 180°, not mirrored** -- and the sheet said
  "mirrored ... reads correctly from below" until V10 was drawn and the picture
  disagreed with the caption. The `.scad` applies `rotate([180, 0, 0])`, a flip about
  X, so the stamp reads normally when the part is turned over front-to-back (how you
  actually turn one over) and appears upside down in a projected view-from-below. An
  `S` is 180°-symmetric, so only the `β` shows it at all. **Draw the thing a reader
  could get backwards; do not describe it.**
- ⚠️ **That change also fixed a legibility bug worth knowing about: Noto Sans draws
  U+03B1 single-storey and TAILLESS, so `α` reads as a Latin `a` at stamp size.** DejaVu's
  alpha has the usual right-hand tail; Noto's does not, and the printed plates have carried
  the ambiguous one all along. `β` has no such twin. The drawing spells the codepoint out
  (`revision_codepoint()`) regardless, because a Greek letter cut into steel from an
  outline alone is a chance to cut the wrong character.

## Things that are load-bearing

- ⚠️ **`MX_CROSS` 4.35 and `MX_CROSS_WIDTH` 1.4 are NOT the cross size.** They describe the
  plus *before* `offset(r = -MX_CROSS_FILLET)`, so the opening is **4.05 × 1.10**. Quoting
  the constants to a moulder overstates it by 0.3 mm on both. `cross_profile()` derives the
  real numbers, and `verify.py` measures them off the solid rather than trusting either.
- ⚠️ **`Shape.scale()` scales about the shape's own location, not the origin.**
  `linear_extrude(scale=)` scales the whole profile about the extrusion axis, so an
  off-centre sub-shape must move inward as well as shrink. Left at the default, the model
  still built, still validated, and its cross tapered at a third of the intended rate
  (+0.5 % volume). Pass `about=(0, 0, 0)`.
- **A tapered box is built as a convex hull of its 8 corners, not as a `loft`.** Same solid,
  different surfaces: OCCT's ThruSections returns the planar sides as degree-1 B-spline
  patches. Hulling the corners gives real `Geom_Plane` faces — 82 of them instead of 36.
- **The cross cut is a union of exact pieces** (two hulled bars + four fillet patches + four
  relief circles) rather than one lofted profile, so the eight arm flats — the surfaces the
  switch cross actually bears on — come out as planes. The fillet and relief walls stay
  free-form, and that is correct: tapering about the axis moves an off-centre arc's centre as
  well as its radius, so those walls are **oblique** cones and no analytic OCCT surface fits
  them. ⚠️ A build that reports them as `Geom_Cone` is a build whose taper is scaling each
  sub-shape about its own centre — the `Shape.scale()` bug above, which is exactly how it was
  first seen.
- ⚠️ **The `.scad` says `u_size = 1.22` for the 1.25U plate, not 1.25.** `u_size` feeds
  `(u_size - 1) * 2 * 5`, i.e. it is a half-width-extension dial (→ 19.90 mm body), not a
  keycap unit count. The recipe had read it as a unit size.
- ⚠️ **The engraving font is pinned to a FILE, and three plausible spellings give three
  different glyphs.** OCCT does not read fontconfig, so `font="Noto"` — what the `.scad`
  asks for — emits *"unable to find font 'Noto'; 'FreeSans' is used instead"* and carries
  on; the real family name `"Noto Sans"` finds the file but renders the **variable font's
  default instance**, not Bold. Measured areas for the same string: 4.068 (FreeSans) /
  2.330 (variable default) / 3.563 (a real Bold). `font.py` instantiates `wght=700` once
  and passes `font_path=`, so the tool is cut from the repo rather than from whatever the
  build machine had.
- ⚠️ **OpenSCAD's `text(size=)` is a POINT size at 100 DPI; build123d's `font_size` is the
  em in millimetres** — the same nominal 3 comes out **100/72 = 1.389× larger** in
  OpenSCAD (cap height 3.058 mm against 2.202 mm, measured both ways). Without
  `TEXT_EM = TEXT_SIZE * 100 / 72` the moulded stamp is a third smaller than the printed
  one, and it reads exactly like a font-weight problem. Same family of trap as
  `fontconvert`'s `-s` being points at 141 DPI (firmware `fonts/README`).
- ⚠️ **Do not run `../build_stems.sh --fetch-font` to get that font.** It fetches and then
  goes on to **re-export all sixteen printed plates** against the newly-installed font,
  rewriting committed meshes — it rewrote three here before it was killed. `make font`
  fetches and stops; the two share one cache path.
- ⚠️ **The three 0.4 × 3.0 × 0.3 tabs are a FUNCTIONAL click feature, not a print aid.**
  They stand 0.2 mm proud on +Y and ±X and are what makes the transparent relegendable
  cap click on. The first draft of this pipeline read them as a sprued-plate artefact,
  called them `print_tabs`, and had the drawing invite the moulder to delete them — on
  the one document a shop acts on without asking back. They are now `CLICK_TAB_*`,
  dimensioned in V3, and note 10 says they must not be removed. `--no-click-tabs` exists
  only to isolate them in a comparison; it is **not** a shipping option.

## Verification, and why there are three checks

`make verify` runs, per variant: the cross measured off a section of the real solid; the
tapered cross prism against its closed form; volume + bounding box against an OpenSCAD
export of the same call; and a **boolean difference both ways** through OpenSCAD.

⚠️ **Find a feature by what it IS, not by "the smallest face".** `measure_cross` used to
take the smallest face in the section; the cap is tilted −7°, which sweeps the seat
engraving through global z 5.1–5.5, so once the stamp was switched on a **glyph fragment**
became the smallest face and the check reported the inside of an `α` — 0.90 × 1.30,
r0.60/0.84, entirely plausible numbers for a cross. It now selects the inner wire that is
centred on the stem axis and smaller than the stem OD.

`make selftest` widens the cross by 0.10 mm and asserts the checks reject it. That run also
shows why the weakest check cannot stand alone:

```
cross measurement differs : True
SCAD \ STEP grew to 3.7767 mm3 (0.672 %) : True
volume delta +0.657 % (still inside the 1 % gate: True -- so volume ALONE would MISS this)
```

## Gotchas that cost real time

- ⚠️ **build123d's drafting module cannot be used for the annotation.** `TechnicalDrawing`
  and `ExtensionLine` were used first, and every label goes through OCCT's
  `Compound.make_text` — which **segfaults** once the sheet carries the frame plus the
  projections, the section and the dimensions. Deterministically, on the 14th label, with
  ~500 MB resident and 14 GB free; none of the ingredients crashes alone. `drawing.py`
  therefore takes geometry from build123d and writes the SVG itself, with real `<text>`.
  The file is 200 KB instead of megabytes and the dimensions are selectable in the
  fabricator's viewer. `../../case/step/plate_svg.py` writes its SVG the same way.
- ⚠️ **`ExtensionLine` has no fallback for a label wider than the dimension line**: the
  shaft between the arrowheads comes out empty and it raises `Can't determine direction of
  empty Edge or Wire` several frames away, which names nothing. Ø5.50 at 2:1 is enough to
  trigger it.
- ⚠️ **Hatch rulings must be thin RECTANGLES, not lines.** A line lying exactly in the
  section face's plane makes OCCT's edge-face common return nothing at all — silently, so
  an empty hatch reads as "no solid here" rather than as an error. Below ~0.05 mm the
  rectangle disappears into the boolean tolerance too.
- ⚠️ **The stamp details needed the MX slot in them, and `cap_body` has none.**
  `stamp_face()` takes its face from the untilted cap body, but `mx_stem` cuts the cross
  *after* tilting and raising the cap — so the detail was a rectangle with two letters
  in it and no datum to locate them from. Pull the cross back through that placement
  (`Rot(-angle) * Pos(0, 0, -extra_len) * cross_cut(...)`) and cut it into the cap body.
  ⚠️ Keep placing the STAMP against the uncut face, as `_engraving` does: centring it in
  a face that now has a hole in it moves it.
- ⚠️ **Zone letters live outside the frame, so `check_inside_frame` has to know.** It
  reads the recorded text extents now instead of re-parsing the emitted SVG, which makes
  `chrome=True` exempt from both that check and the collision report for free.
- ⚠️ **`snap` earns its keep by REFUSING.** It rejected the first attempt at V5's extra
  dimensions -- *"no section vertex within 0.6 of (-5.65, 4.52)"* on the 1.25U variant --
  and the pair I had confidently called "the flange" turned out to be the inside of the
  pocket, which moves with `u_size`. Silently snapping to the nearest corner would have
  shipped a wrong label on one variant and a wrong anchor on the other. **Name a
  dimension by what it MEASURES when you have not verified which feature it is.**
- ⚠️ **Derive the scale caption from the number that drew the view.** It was a literal
  beside each `titles[..]` entry; `SCALE_ISO` went 1.6 -> 2.4 and the isometric went on
  claiming 1.6:1 -- a caption a reader might measure against. `_ratio()` formats it.
- ⚠️ **Anchor every section dimension on a REAL VERTEX of the cut.** `section()` returns
  the vertices and `snap()` picks the nearest, raising past a tolerance rather than
  quietly taking the wrong corner. Dimensions computed from model constants are exactly
  what "floating in the air" looks like on a section: the display seat is 1.10 below a
  top face tilted −7°, so the height the arithmetic names is not a height anything on
  that cut has.
- ⚠️ **On a section, a leader often beats a dimension line.** A feature in the middle of
  the cut (the stem boss, behind the outer skirt) can only be dimensioned by dragging
  extension lines across hatched material. A leader touches the vertex the number came
  from and crosses nothing.
- ⚠️ **Overlaying a second shape on a laid-out view means undoing TWO re-centrings, and
  getting one of them is worse than getting neither.** `Drawing` projects about the
  shape's own centre of mass, *and* `view()` then shifts by the projection's bounding-box
  centre. Correcting only the second put the faint stamp overlay plausibly in the middle
  of V3/V4 instead of visibly nowhere, which is far harder to notice.
- ⚠️ **A dimension anchored by hand lands in mid-air.** `Drawing` projects about the
  shape's centre of **mass**, then `view()` re-centres the result on its bounding box — so
  a sheet point computed from the model's own coordinates is off by the difference between
  those two centres (7.9 mm on the front view: the "the 7.91 dimension starts from
  somewhere outside" report). `view()` returns a model→sheet mapper built from the same
  two transforms, and every dimension goes through it.
- ⚠️ **A sheet laid out by hand-tuned offsets WILL collide, and the SVG source never shows
  it.** Three guards, all of which found live defects on the first sheet:
  `Sheet.group()` measures what a view actually drew and the title is placed from that
  (a guessed `dy` put V2's title nearer the view *below* it — which on a first-angle sheet
  is another projection, so it read as labelling the wrong view); `report_collisions()`
  lists label-on-label and label-on-outline overlaps; `check_inside_frame()` raises on
  anything past the border. ⚠️ The collision report only tracks **thick** paths, so a label
  lying on a dimension line or a thin isometric outline still passes — **render both
  variants**: the 1.25U leaders reach 4.4 mm further out and one collision existed only
  there.
- ⚠️ **A self-test can pass for the wrong reason — assert the NEGATIVE control too.**
  `verify.py --self-test` widens the MX cross and asserts the checks catch it, and its
  cross-measurement half had its own copy of the expected span with the taper left out.
  That copy is 0.0033 mm off at z = 0.30 — above its own 2e-3 threshold — so it reported
  "caught" against a **correct** model and asserted nothing at all. The fix is both
  halves of the usual pair: one `cross_span()` shared with check 1 so the two cannot
  disagree, and an explicit assertion that the same comparison is *quiet* on the
  unmodified model. A harness that cannot tell "the check fired" from "my arithmetic is
  wrong" is the fail-open shape the self-test exists to rule out. (CodeRabbit, PR #38.)
- ⚠️ **Gate on the dependency the check actually needs.** Check 1b — the cross prism
  against its closed form, the one that caught the `Shape.scale()` centre bug — sat
  below `if not have_scad: continue`, so a machine without **openscad** silently skipped
  a check that is pure build123d and needs no openscad at all.
- ⚠️ **The engraving font is pinned by SHA-256, and the cache is SHARED.** The outlines
  cut into a steel cavity come from a `main` URL, so `font.py` verifies the bytes and
  stops with instructions if upstream moves. ⚠️ `../build_stems.sh` fetches the same URL
  into the same cache path with no verification, so a mismatched cache is re-downloaded
  rather than rejected — that heals the shared path instead of failing on a file the
  other script legitimately put there. Only a fresh download that still mismatches is
  fatal. Changing the digest means re-exporting both STEPs: the engraving moves with it.
- ⚠️ **A STEP re-export rewrites the file even when the solid is identical** -- the
  header carries a timestamp, so `make step` always shows both files as modified. Before
  committing one, check whether anything below the header actually moved:
  `diff <(git show HEAD:<path> | tail -n +12) <(tail -n +12 <path>)`. If it is empty,
  `git checkout` the file rather than committing 1.3 MB of timestamp. Same reasoning as
  the STL facet-order note in the repo CLAUDE.md.
- ⚠️ **`BRepBndLib.Add_s` on an un-meshed shape boxes the underlying SURFACES**, not the
  trimmed faces, so a cut whose prism runs past the solid inflates the answer: it reported
  z_max 11.30 for a part that tops out at 7.91. `validate_step.py` (shared with the case)
  now uses `AddOptimal_s`; the case's own bbox was off by up to 2.1 mm the same way.

## Still open

- **The cap interface is a hard datum we do not own** (the transparent relegendable caps are
  off-the-shelf POS parts). Confirm it against a real cap before cutting steel.
- **Whether the moulder will do the replaceable-revision insert** (note 10). If they cut
  the character into the block instead, every revision is a tool edit — ask before the
  quote is accepted, not after.
- Only the **S** profile is exported. `VARIANTS` in `stem_model.py` is where R1–R5/S1/S5
  would be added; they differ only in `angle` and `extra_len`.
