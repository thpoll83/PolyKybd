# Keycap stem → clean STEP + a technical drawing (build123d)

Re-authors the **S-profile keycap stems** (`../keycap_stem.scad`, `mx_stem()`) as real
B-Rep solids with [build123d](https://build123d.readthedocs.io/) (OpenCASCADE), and
draws each one on an A4 sheet, so an injection moulder can quote and cut without
guessing at facet noise. Follows
[`../../openscad-to-step-recipe-stems.md`](../../openscad-to-step-recipe-stems.md),
which follows the case's [`../../case/openscad-to-step-recipe.md`](../../case/openscad-to-step-recipe.md).

**Why not STL → STEP.** OpenSCAD has no B-Rep kernel, so its export is a facet soup
with loose stitching. On a stem that matters more than on the case: the feature that
decides whether the keyboard works is a ~1.1 mm MX cross, and a faceted cross is not a
datum anyone can cut to.

## Build

```bash
pip install build123d scipy          # OCP comes with build123d
sudo apt-get install -y openscad     # only for `make verify`

make                 # -> ../../export/keycap_stem/stem_S_1U{,25}.step + _drawing.svg, validated
make verify          # diff the solid against the .scad it was ported from
make selftest        # prove those checks can fail (see below)
```

| file | what |
|---|---|
| `stem_model.py` | the model. Every constant keeps its `keycap_stem.scad` name so the two stay diffable |
| `hull3d.py` | OpenSCAD `hull()` as an exact polyhedral convex hull |
| `build.py` | exports `stem_S_1U.step` / `stem_S_1U25.step` (+ an STL the checks use) |
| `drawing.py` | the A4 sheet: 3 ortho views, isometric, section, 10:1 cross detail, tolerances, notes |
| `validate_step.py` | the case's acceptance test, reused (real solid, curved faces, tight tolerance) |
| `verify.py` | measures the cross, diffs volume/bbox and booleans against OpenSCAD |

## What the two deliverables are for

**The drawing governs; the STEP conveys shape.** A solid model carries no tolerances, so
a toolmaker handed only a STEP cuts to the model and the tolerance question resurfaces at
first article. The sheet states a general tolerance and tightens only the MX cross and the
interface to the off-the-shelf transparent cap.

## Results

```
faces 100   planar 82   B-spline 16   cone 1   cylinder 1   max edge tolerance 1.0e-07 mm
volume vs the OpenSCAD mesh   +0.111 % (1U)   +0.081 % (1.25U)
bounding box                  identical to 5 decimal places
STEP \ SCAD 0.62 mm3 (0.11 %)   SCAD \ STEP 0.011 mm3 (0.002 %)
```

The residual is entirely the `.scad`'s faceted cylinders (a 128-gon stem, `$fn=64` cross
relief) against true analytic surfaces — the difference the exercise exists to remove.

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
- **The engraved revision is OFF by default** (`build.py --engrave` turns it on): an engraved
  character is a tool feature that cannot be changed later without a tool edit, and it makes
  the model depend on which font fontconfig resolves — the trap `../build_stems.sh` already
  documents for the printed plates.
- **The three 0.4 × 3.0 × 0.3 print tabs are reproduced, not silently deleted.** They are in
  the source, so they are in the model (`--no-print-tabs` drops them) and note 10 of the
  drawing asks the moulder about them.

## Verification, and why there are three checks

`make verify` runs, per variant: the cross measured off a section of the real solid; the
tapered cross prism against its closed form; volume + bounding box against an OpenSCAD
export of the same call; and a **boolean difference both ways** through OpenSCAD.

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
- ⚠️ **`BRepBndLib.Add_s` on an un-meshed shape boxes the underlying SURFACES**, not the
  trimmed faces, so a cut whose prism runs past the solid inflates the answer: it reported
  z_max 11.30 for a part that tops out at 7.91. `validate_step.py` (shared with the case)
  now uses `AddOptimal_s`; the case's own bbox was off by up to 2.1 mm the same way.

## Still open

- **Material is not chosen.** ABS is assumed on the drawing (its 0.4–0.7 % shrink is what
  protects the cross); POM only if the stem must snap-retain, at ~2 % shrink the cross
  geometry then has to compensate for. **Shrink compensation belongs in the moulded model,
  not this one** — keep a printed and a moulded parameter set apart when it is applied.
- **The cap interface is a hard datum we do not own** (the transparent relegendable caps are
  off-the-shelf POS parts). Confirm it against a real cap before cutting steel.
- Only the **S** profile is exported. `VARIANTS` in `stem_model.py` is where R1–R5/S1/S5
  would be added; they differ only in `angle` and `extra_len`.
