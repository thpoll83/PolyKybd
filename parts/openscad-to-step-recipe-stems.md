# Recipe: keycap stems (S, 1U + 1.25U) as clean STEP + a technical drawing

**Goal.** Produce, for the two stem variants an injection moulder needs — **S 1U** and **S 1.25U** —
a real **B-Rep** STEP plus a dimensioned technical drawing, so a toolmaker can quote and cut without
guessing at facet noise.

**This follows the pattern already proven on the case** —
[`case/openscad-to-step-recipe.md`](../case/openscad-to-step-recipe.md) and the working toolchain in
[`case/step/`](../case/step/). Read that first; everything here is the same method on a much simpler
part. **Do not fall back to STL → STEP.** The case recipe records exactly why: OpenSCAD has no B-Rep
kernel, so the mesh export lands as ~14,900 flat facets with ~0.15 mm stitching, and the fabricator
flags it. A stem is worse in one respect — its critical feature is a **1.4 mm MX cross** whose fit
decides whether the keyboard works, and a faceted cross is not a datum anyone can cut to.

## Why the stem is the *easier* case

The case needed re-authoring because `hull()` and `minkowski()` cannot survive as clean geometry.
⚠️ **The stem does use `hull()`** — `keycap_stem.scad:83` hulls two tapered bodies (that is how the
1.25U gets its width) plus the three click tabs. But every member is a **polyhedron**, and the convex hull
of polyhedra is a polyhedron, so it comes back exactly from a hull of the vertices (`step/hull3d.py`);
there is no `minkowski()` anywhere. The rest is `linear_extrude(..., scale=)`, a tapered extrude that
is a native exact operation. So the port is close to line-for-line, with no approximation anywhere:

| `keycap_stem.scad` | build123d |
|---|---|
| `hull(bodyA, bodyB, tabs…)` | convex hull of the vertices → planar faces (`hull3d.py`) |
| `linear_extrude(h, scale=r)` | hull of the 8 corners — **not** `loft`, see below |
| `offset(r=-mx_cross_fillet)` on the cross | `fillet()` on the cross edges — a *real* fillet |
| `circle(d=…, $fn=64)` | `Circle(r)` — a true cylinder, not 64 facets |
| `square([x,y], center=true)` | `Rectangle(x, y)` |

## Parameters — copy these as Python constants

From `keycap_stem.scad` (keep them named so the port stays parametric):

```python
STEM_X, STEM_Y          = 15.5, 15.475
STEM_HEIGHT             = 5.65
STEM_TOP_BOTTOM_RATIO   = 0.85     # -> ~11.6 deg draft, see below
INSIDE_X, INSIDE_Y      = 13.3, 13.3
INSIDE_HEIGHT           = 3.0
MX_CYLINDER             = 5.5
MX_CROSS                = 4.35     # cross arm length
MX_CROSS_WIDTH          = 1.4      # cross arm width  <-- tolerance-critical
MX_CROSS_FILLET         = 0.3
DISP_X, DISP_Y          = 12.2, 12.1
DISP_HEIGHT             = 1.1
DISP_Y_CENTER_OFFSET    = 1.345
CABLE_STEM_X, CABLE_STEM_Y = 9.0, 2.12
CABLE_THICKNESS         = 0.5
```

**The two variants.** Both are the `S` profile — `angle=-7, extra_len=1.5`, from
`variants/keycap_stem_revAlpha_1U*_S_10p.scad`. Only `u_size` differs:

| Variant | Call | Body width |
|---|---|---|
| **S 1U** | `mx_stem(u_size=1,    angle=-7, extra_len=1.5)` | 15.50 |
| **S 1.25U** | `mx_stem(u_size=1.22, angle=-7, extra_len=1.5)` | 19.90 |

⚠️ **It is `u_size = 1.22`, not 1.25** — an earlier draft of this recipe read it as a keycap unit
count. It is not: `u_size` feeds `(u_size - 1) * 2 * 5`, i.e. it is a **half-width-extension dial**,
so 1.22 grows the body by 2 × 2.2 mm. The `.scad` is the authority.

⚠️ **`MX_CROSS` 4.35 and `MX_CROSS_WIDTH` 1.4 are NOT the cross size** either. They describe the plus
*before* `offset(r = -MX_CROSS_FILLET)`, so the opening the switch actually enters is **4.05 × 1.10**
with r0.30 corner fillets. Quoting the constants to a moulder overstates it by 0.3 mm on both.

**The `txt=` stamp IS carried** (decided 2026-08-19): `S    β`, engraved 0.30 mm into the display-seat
floor and the pocket ceiling. Marking the revision is the point of it, so drawing note 10 asks for the
character on a **replaceable insert** in the cavity — the next revision is then a plug swap, not a tool
edit. Both stamps are zero-draft; neither sits on a fit surface. `build.py --no-engrave` drops it.

⚠️ **The moulded revision is `β` while `keycap_stem.scad` stays `α`** — the moulded part differs from
the 3D-printed prototypes, so it says so. `stem_model.REVISION` is the one constant that deliberately
does not mirror the `.scad`. It also sidesteps a legibility problem: **Noto Sans draws U+03B1
single-storey and tailless, so `α` reads as a Latin `a` at stamp size** (DejaVu's has the usual tail);
`β` has no twin. The sheet spells the codepoint out either way.

⚠️ **Getting the glyph right is the hard part, not adding it.** OCCT does not read fontconfig, so
`font="Noto"` — what the `.scad` asks for — falls back to FreeSans with a warning nobody reads, and the
family name resolves the *variable* font's default instance rather than Bold; and OpenSCAD's
`text(size=)` is a **point size at 100 DPI** while build123d's `font_size` is the em in mm, a 1.389×
difference. All three are silent. `step/font.py` pins the file and `TEXT_EM` does the conversion; the
step README has the measured numbers.

## Draft — computed, not eyeballed

`stem_model.draft_angles()` derives these from the model, and the drawing quotes it, so the sheet
cannot drift from the geometry. A `linear_extrude(scale=s)` over height `h` moves a wall that starts
`w` from the axis inward by `w·(1−s)`, so the draft is `atan(w·(1−s)/h)` — it depends on **how far out
the wall is**, which is why one number cannot describe a tapered profile:

| Feature | Wall at | Taper | Over | Draft |
|---|---|---|---|---|
| Outer body X / Y | 7.750 / 7.738 | `0.85` | 5.65 mm | **11.63° / 11.61°** ✅ |
| Inside pocket | 6.650 | `0.85` | 3.0 mm | **18.39°** ✅ |
| Centre pocket | 7.017 | `0.7225` | 3.0 mm | **32.99°** ✅ |
| Cross arm flats (`:163`) | 0.550 | `0.97` | 11.3 mm | **0.084° ⚠️** |
| Cross arm tips | 2.025 | `0.97` | 11.3 mm | **0.308° ⚠️** |
| **Display seat** (`:116`) | 6.100 | **`1`** | 1.1 mm | **0° ⚠️** |

⚠️ The earlier hand-derived version of this table was wrong in two places (21.2° for the inside pocket,
1.18° for the cross) — that is what "derived by inspection, not by running the toolchain" was worth.

Two things to raise in the quote rather than let a moulder discover them:
- The **display seat is zero-draft** (`linear_extrude(height=disp_height, scale=1)` over
  `DISP_X × DISP_Y`), as is its cable relief. At 1.1 mm deep it often releases as-is; say so anyway.
- The **cross has almost no draft** — 0.08° on the flats. It opens *downward*, so the core pin
  withdraws in the correct direction, but with very little relief, and the stem wall at the arm tip
  is only **0.67 mm**. Everything else clears the 0.5–1° minimum by 10× or more, so **draft is not a
  redesign item.**

## Build it

Mirror `case/step/` — same layout, same driver pattern:

Built as **`parts/keycap_stem/step/`**, not the `parts/step/` this recipe first suggested — the repo
rule is one folder per part group with its scripts beside its sources, and the case precedent is
`parts/case/step/`. Output goes to `parts/export/keycap_stem/` like every other generated mesh.

```
parts/keycap_stem/step/
  stem_model.py      # build123d model, both variants from one parametric function
  hull3d.py          # OpenSCAD hull() as an exact polyhedral convex hull
  build.py           # emits stem_S_1U.step, stem_S_1U25.step
  validate_step.py   # delegates to case/step/validate_step.py rather than copying it
  verify.py          # measures the cross + diffs against the .scad (with a self-test)
  drawing.py         # the technical drawing
  Makefile
```

```bash
pip install build123d scipy fonttools
make -C parts/keycap_stem/step            # step + drawing + validate
make -C parts/keycap_stem/step verify     # needs openscad
```

**Verify against the SCAD, do not assume.** `verify.py` does this, and `case/step/render_compare.py`
exists precisely because a re-authored model can drift from its source. The same standing rule from
[`CLAUDE.md`](../CLAUDE.md) applies: *compare meshes as a sorted facet multiset, and pair any
clearance test with a positive control.* For the stem the specific checks that matter:

1. **MX cross**: measure the **finished opening** on the STEP — flats **4.05 × 1.10**, corner
   fillets **R0.30**, and the four relief bulges that take the outer span to **4.11**. ⚠️ NOT
   4.35 × 1.4: those are the `MX_CROSS` / `MX_CROSS_WIDTH` source constants *before*
   `offset(r = -0.3)`, so measuring to them accepts an opening 0.30 mm oversized on both
   axes — the exact error the warning near the top of this file is about, written here as an
   instruction. `verify.py` check 1 measures the real values off a section of the solid.
2. **Volume delta** SCAD-mesh vs STEP solid: should agree to well under 1 % (only the facet
   approximation of the cylinders differs).
3. **The keycap cover interface** — the transparent relegendable caps are **off-the-shelf POS parts**,
   so that mating dimension is fixed by a supplier you do not control. Treat it as a hard datum.

## The technical drawing

build123d exports 2D projections through OCP; `case/step/plate_svg.py` is the closest existing
precedent for SVG output. `drawing.py` should emit, per variant, an **A3 sheet** carrying:

- **Four orthographic views** (right / front / above / **below**) + one isometric, projected from
  the STEP solid. ⚠️ A4 was the first target and it does not work: five views, three details, a
  section, the notes and a fit table all had to shrink until the 10:1 detail stopped being a
  detail. A3 prints down to A4 at 71 % if a reader wants it that way. The view from **below** is
  not optional either — the inner switch-clearance chamfer appears in no other view.
- **A section through the MX cross** — the feature that decides fit, so it needs its own view.
- **Number every view** and say the scale under each: a sheet with ten framings and five
  different scales is unreferenceable in an email otherwise. The shipped mapping is
  **V1–V4** ortho (right / front / above / below), **V5/V6** sections A-A and B-B,
  **V7** the MX cross at 10:1, **V8/V9** the two stamp details, **V10** isometric.
- **Dimensioned**: the MX opening **4.05 × 1.10 ±0.03** with **R0.30** corner fillets and the
  four relief bulges, `MX_CYLINDER` 5.5, overall 15.5 × 15.475, height 5.65, display seat
  12.2 × 12.1 × 1.1, draft angles called out. ⚠️ **Not 4.35 × 1.4** — those are the
  pre-`offset()` source constants, and the warning against quoting them to a moulder is
  eighty lines above this list. It said so and this line did it anyway.
- **A tolerance block.** ⚠️ This is the point of the whole exercise: **the drawing governs, the STEP
  conveys shape.** State a general tolerance (e.g. ±0.1) and tighten only the cross and the cover
  interface. Without it a toolmaker will cut to the model and the tolerance question resurfaces at
  first article.
- Material and finish, once chosen — see the material note below.
- Revision, date, part number, and the engraving — see below; it is present, and it is **β**.
- **The three click tabs, dimensioned.** ⚠️ They read like a 3D-printing sprue artefact and they
  are not: they are what makes the transparent cap click on. Say so on the sheet. A fabrication
  drawing is the one document a shop acts on without asking back, so "optional" written there is
  a decision, not a question.

## Material — **ABS** (decided 2026-08-19)

It is the standard keycap material and its low shrink (0.4–0.7 %) is what protects the MX cross
tolerance. POM was the alternative *if* the stem snap-retains the display or cover — better fatigue
under repeated engagement, but ~2 % shrink the cross geometry would have to compensate for; PBT and
nylon are both worse here (higher shrink, and nylon is hygroscopic).

⚠️ **Shrink compensation is NOT in the model.** The STEP and the drawing are the **finished part**;
the cavity is cut oversize by the toolmaker, who states the rate used (drawing note 9). That is the
normal division of labour and it keeps one model serving both the printed and the moulded part — do
not fold a shrink factor into `stem_model.py` without saying so on the drawing.

## ✅ Status — DONE (2026-08-18, reviewed and reworked 2026-08-20)

Executed end to end; `parts/keycap_stem/step/` is the working toolchain and
[its README](keycap_stem/step/README.md) carries the results and the traps. Both deliverables are in
`parts/export/keycap_stem/`: `stem_S_1U.step` / `stem_S_1U25.step` and their `*_drawing.svg`.

Both STEPs pass the acceptance test — one closed solid, **142 faces** (108 planar, 34 curved), max
edge tolerance **2.1e-07 mm**. Against an OpenSCAD export of the same call: bounding box identical
to 5 dp, volume **+0.111 % / +0.081 %**, and a two-way boolean difference of 0.62 mm³ one way and
0.011 mm³ the other — all of it the `.scad`'s tessellation (a 128-gon stem, `$fn=64` cross relief)
against true analytic surfaces, which is the difference this exercise exists to create.

⚠️ **That comparison runs with the stamp OFF, deliberately** (`verify.py` `engrave = False`): the
moulded stamp is **β** and the `.scad`'s is α, so an engraved diff would report the intended
difference as an error every run. The stamp is checked separately, and more usefully — `verify.py`
measures its clearance to the seat edge on both faces (0.80 mm all round, against the 0.80 mm
requirement) rather than folding it into a volume number where 5 mm³ of glyph would drown the
0.6 mm³ of tessellation the diff exists to see.

Three corrections this recipe needed once it was actually run, all now folded in above: the stem
**does** use `hull()`; `u_size` is 1.22 and is not a unit count; and the cross opening is 4.05 × 1.10,
not 4.35 × 1.4. The draft table was recomputed. Everything else held.

The build123d gotchas worth knowing before the next port are in the step README: `Shape.scale()`
defaults to scaling about the shape's own location (a silent 0.5 % geometry error); OCCT's text kernel
**segfaults** when a drawing sheet gets big enough, which is why `drawing.py` writes its own SVG; and
the three font traps above, each of which silently changes the glyph a toolmaker would cut.

### The 2026-08-20 review round

The first sheet was geometrically correct and typographically a mess, and none of it was visible
in the code. What the review changed, and the two guards that now stop it recurring:

- **A4 → A3**, four ortho views (the view from **below** was missing, and the switch-clearance
  chamfer shows in no other view), numbered views V1–V8, a **stamp proposal** view at 5:1, an axis
  triad on every view, a **fit table** against Cherry's published keycap slot, a fuller title block
  with the PolyTasten logo, and first-angle-projection marking.
- **The tabs were mis-documented as a print aid and the sheet invited their deletion** — corrected
  everywhere; they are a click feature and are now dimensioned.
- **The stamp** moved to β, `S` and `β` swapped so β's descender has room, gap widened from a
  measured 0.21 mm clearance to ≥ 0.80 mm all round.
- **Layout is now measured, not guessed** — `Sheet.group()` places each title from the extent of
  what the view actually drew, `report_collisions()` lists label-on-label and label-on-outline
  overlaps, and `check_inside_frame()` raises on anything past the border. Between them they found
  six collisions and three overflows that had shipped in the first sheet. ⚠️ **Render both variants**:
  the 1.25U leaders reach 4.4 mm further out, and one collision existed only there.
### The second review round (2026-08-20)

Seven more items, of which three were substantive:

- **Sections both ways.** A-A along X shows the slot; nothing in it said how the flex cable
  gets out, so **V9 section B-B** cuts the perpendicular plane and carries the cable route
  (2.12 relief, 1.10 deep, the FFC exit's 14.9° flare), with the 9.00 relief width on V3.
  ⚠️ Get the cutting-plane arrows from the section PLANE, not by eye: build123d's `Plane.XZ`
  has its normal on -Y and `Plane.YZ` on +X, so the two sections are viewed from opposite
  senses and their arrows point opposite ways on the same plan view.
- ⚠️ **The pocket stamp is TURNED 180°, not mirrored — and the sheet said "mirrored" until
  V10 was drawn.** The `.scad`'s `rotate([180, 0, 0])` is a flip about X: the stamp reads
  normally when the part is turned over front-to-back, and appears upside down in a
  projected view-from-below. The prose had been carried forward unchecked through three
  revisions because an `S` is 180°-symmetric and only the `β` shows the difference. **Draw
  anything a reader could get backwards.**
- ⚠️ **"5.05 slot depth" in A-A was wrong twice**: the number is the height of the stem
  BOSS, and the slot is not bounded by it at all — the cross is cut clean through into the
  cap floor. The real bound (z = 5.83) has no closed form, because the cap floor is tilted;
  `slot_top_z()` bisects for it. A dimension whose label was written from the variable name
  rather than from the geometry.
- Line weights dropped a full ISO 128 group (0.5/0.25 → 0.35/0.18): the heavier group is
  correct for a sparse sheet and reads as ink on a dense one.
- Notes that repeat a title-block cell were deleted, the rest are **wrapped in code** and
  flowed into two balanced columns — hand-wrapped lines silently overrun the moment an
  interpolated value gains a digit, which is how the block reached 2 mm off the frame.
- Axis triads are placed from each view's OUTLINE box, not a fixed offset, so a wider
  variant cannot push a dimension under one.

### The fifth review round (2026-08-20)

- **ISO 5457 grid reference** on all four edges — 1–8 across, A–F down, ~50 mm fields
  for A3 — so a feature can be called out as "the boss, D3" without anyone counting
  views. ⚠️ Those letters live OUTSIDE the drawing frame by definition, so
  `check_inside_frame` now reads the recorded text extents rather than re-parsing the
  SVG; a `chrome=True` flag is then exempt from both that check and the collision report
  for free.
- ⚠️ **A detail view of a face needs that face's own datum in it.** V8/V9 were a
  rectangle with two letters and nothing to locate them from, because `stamp_face()`
  takes its face from `cap_body` — which has no MX slot, since `mx_stem` cuts the cross
  after tilting and raising the cap. Pulling the cross back through that placement and
  cutting it into the cap body puts the slot in the detail. Both details also gained the
  stamp's own centre line and its offset from the stem axis.
- The notes lost the 3D-printing comparisons and the Cherry reference: reasoning for us,
  noise on a moulder's sheet.
- Views shifted down into the space the notes vacated; axis triads moved off the
  dimensions they had drifted onto.

### The fourth review round (2026-08-20)

Four items, all layout, and two general lessons fell out of them:

- ⚠️ **A snap helper earns its keep by REFUSING.** Adding dimensions to V5 tripped
  `snap` — *"no section vertex within 0.6 of (-5.65, 4.52)"*, and only on the 1.25U
  variant — and the vertex pair confidently labelled "the flange" turned out to be the
  inside of the pocket, which moves with `u_size`. Name a dimension by what it MEASURES
  when you have not verified which feature it is.
- ⚠️ **Derive the scale caption from the number that drew the view.** `SCALE_ISO` went
  1.6 → 2.4 and the isometric's caption went on saying 1.6:1 — the one label a reader
  might measure against.
- V5 and V6 to 3:1 and V10 to 2.4:1, with the height dimensions on the sections (the
  front view sees the boss and the skirt only as hidden lines). V6 now shows that the
  **pocket ceiling is not parallel to the moulding face** — 4.96 at the front, 4.17 at
  the back, which is the −7° cap tilt and decides which end of the core is thinnest.
- The notes moved to the bottom of the sheet, and V8's stamp-clearance callout became a
  real dimension instead of a leader long enough to run across the 10:1 detail.

### The third review round (2026-08-20)

Eleven items.  The ones with a general lesson in them:

- ⚠️ **Anchor every section dimension on a REAL VERTEX of the cut.** "Dimensions float in
  the air" was exactly right: they had been computed from model constants, and on a
  section that does not work — the display seat is 1.10 below a top face tilted −7°, so
  the height the arithmetic names is not a height anything on that cut has. `section()`
  now returns its vertices and `snap()` raises rather than taking the wrong corner.
- ⚠️ **On a section, a leader often beats a dimension line.** A feature in the middle of
  the cut (the stem boss, behind the outer skirt) can only be dimensioned by dragging
  extension lines across hatched material to reach the outside.
- ⚠️ **A cutting-plane mark is a SHORT stroke at each end** (ISO 128-30), not a line
  across the view — drawn full length it ran the height of the plan view and through
  every horizontal dimension on it.
- ⚠️ **Overlaying a second shape on a laid-out view means undoing TWO re-centrings**
  (`Drawing`'s own centre of mass, then the view's bounding-box shift), and correcting
  only one is worse than correcting neither: the faint stamp landed plausibly in the
  middle of the view rather than visibly nowhere.
- **What the drawing is FOR decides what goes on it.** The axis convention (drawn on
  every view anyway), the `.scad` provenance, and the whole Cherry fit table came off the
  sheet and into CLAUDE.md. They are reasoning for us, not instructions to a moulder.
  Notes went to three wrapped columns; V3 to 3:1 because it carries the most detail.
- View numbers were reassigned so the sections read together: V5/V6 sections, V7–V9
  details, V10 isometric.

- ⚠️ **A dimension anchored through `Drawing` lands in mid-air** unless you keep the projection's
  own mapper: `Drawing` projects about the shape's centre of **mass**, and the view is then
  re-centred on its bounding box, so a hand-computed sheet point is off by the difference (7.9 mm
  on the front view — the "7.91 dimension starts from somewhere outside" report). `view()` returns
  a model→sheet mapper for exactly this.
