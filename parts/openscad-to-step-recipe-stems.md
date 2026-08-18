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
1.25U gets its width) plus three print tabs. But every member is a **polyhedron**, and the convex hull
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

⚠️ The `txt=` argument stamps the revision into the part. **Decide before tooling whether the moulded
part carries it** — an engraved character is a tool feature that cannot be changed later without a tool
edit, and `revision = "α"` will not stay α.

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
pip install build123d scipy
make -C parts/keycap_stem/step            # step + drawing + validate
make -C parts/keycap_stem/step verify     # needs openscad
```

**Verify against the SCAD, do not assume.** `verify.py` does this, and `case/step/render_compare.py`
exists precisely because a re-authored model can drift from its source. The same standing rule from
[`CLAUDE.md`](../CLAUDE.md) applies: *compare meshes as a sorted facet multiset, and pair any
clearance test with a positive control.* For the stem the specific checks that matter:

1. **MX cross**: arm length 4.35, width **1.4**, fillet 0.3 — measure these on the STEP, not by eye.
2. **Volume delta** SCAD-mesh vs STEP solid: should agree to well under 1 % (only the facet
   approximation of the cylinders differs).
3. **The keycap cover interface** — the transparent relegendable caps are **off-the-shelf POS parts**,
   so that mating dimension is fixed by a supplier you do not control. Treat it as a hard datum.

## The technical drawing

build123d exports 2D projections through OCP; `case/step/plate_svg.py` is the closest existing
precedent for SVG output. `drawing.py` should emit, per variant, an **A4 sheet** carrying:

- **Three orthographic views** (top / front / side) + one isometric, projected from the STEP solid.
- **A section through the MX cross** — the feature that decides fit, so it needs its own view.
- **Dimensioned**: cross arm 4.35 and width **1.4 ±?**, `MX_CYLINDER` 5.5, overall 15.5 × 15.475,
  height 5.65, display seat 12.2 × 12.1 × 1.1, draft angles called out.
- **A tolerance block.** ⚠️ This is the point of the whole exercise: **the drawing governs, the STEP
  conveys shape.** State a general tolerance (e.g. ±0.1) and tighten only the cross and the cover
  interface. Without it a toolmaker will cut to the model and the tolerance question resurfaces at
  first article.
- Material and finish, once chosen — see the material note below.
- Revision, date, part number, and whether the `txt` engraving is present.

## Material (for the drawing's title block)

Not yet decided. **ABS** is the default: it is the standard keycap material and its low shrink
(0.4–0.7 %) is what protects the MX cross tolerance. **POM** is the alternative *if* the stem
snap-retains the display or cover — better fatigue under repeated engagement, at ~2 % shrink that the
cross geometry must then compensate for. PBT and nylon are both worse here (higher shrink; nylon is
hygroscopic). Whichever is chosen, **shrink compensation belongs in the moulded model, not the printed
one** — so keep the printed stem and the moulded stem as separate parameter sets in `stem_model.py`.

## ✅ Status — DONE (2026-08-18)

Executed end to end; `parts/keycap_stem/step/` is the working toolchain and
[its README](keycap_stem/step/README.md) carries the results and the traps. Both deliverables are in
`parts/export/keycap_stem/`: `stem_S_1U.step` / `stem_S_1U25.step` and their `*_drawing.svg`.

Both STEPs pass the acceptance test — one closed solid, 100 faces (82 planar, 16 B-spline, 1 conical,
1 cylindrical), max edge tolerance **1.0e-07 mm**. Against an OpenSCAD export of the same call: bounding
box identical to 5 dp, volume **+0.111 % / +0.081 %**, and a two-way boolean difference of 0.62 mm³
one way and 0.011 mm³ the other — all of it the `.scad`'s faceted cylinders against true analytic
surfaces, which is the difference this exercise exists to create.

Three corrections this recipe needed once it was actually run, all now folded in above: the stem
**does** use `hull()`; `u_size` is 1.22 and is not a unit count; and the cross opening is 4.05 × 1.10,
not 4.35 × 1.4. The draft table was recomputed. Everything else held.

Both build123d gotchas worth knowing before the next port are in the step README: `Shape.scale()`
defaults to scaling about the shape's own location (a silent 0.5 % geometry error), and OCCT's text
kernel **segfaults** when a drawing sheet gets big enough, which is why `drawing.py` writes its own
SVG.
