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

## Why the stem is the *easy* case

The case needed re-authoring because `hull()` and `minkowski()` cannot survive as clean geometry. **The
stem uses neither.** Its whole shape is `linear_extrude(..., scale=)`, which is a **tapered extrude /
two-rectangle loft** — a native, exact operation in build123d. So this port is close to line-for-line,
with no approximation anywhere:

| `keycap_stem.scad` | build123d |
|---|---|
| `linear_extrude(h, scale=r)` | `extrude(..., taper=)` or `loft()` between two rects |
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

**The two variants.** Both are the `S` profile, which is `mx_stem(angle=-7, extra_len=1.5)`
(`keycap_stem.scad:325`). Only `u_size` differs:

| Variant | Call | Notes |
|---|---|---|
| **S 1U** | `mx_stem(u_size=1,    angle=-7, extra_len=1.5)` | 58 per keyboard |
| **S 1.25U** | `mx_stem(u_size=1.25, angle=-7, extra_len=1.5)` | 14 per keyboard |

⚠️ The `txt=` argument stamps the revision into the part. **Decide before tooling whether the moulded
part carries it** — an engraved character is a tool feature that cannot be changed later without a tool
edit, and `revision = "α"` will not stay α.

## Draft — already fine, with one exception

Measured from the SCAD (2026-08-17), against the 0.5–1° moulding minimum:

| Feature | Taper | Over | Draft |
|---|---|---|---|
| Outer body X / Y | `scale=0.85` | 5.65 mm | **11.6°** ✅ |
| Inside pocket | `scale=0.85` | 3.0 mm | **21.2°** ✅ |
| Shell (`keycap_stem.scad:163`) | `scale=0.97` | 11.3 mm | **1.18°** ✅ |
| **Display pocket** (`:116`) | **`scale=1`** | 1.1 mm | **0° ⚠️** |

⚠️ The **display seat is zero-draft** — `linear_extrude(height=disp_height, scale=1)` over
`DISP_X × DISP_Y`. At 1.1 mm deep a moulder may accept it as-is (shallow pockets often release,
especially textured), but **raise it explicitly in the quote** rather than letting them discover it.
Lines 58, 61 and 121 are the same `scale=1` pattern on smaller features. Everything else clears the
minimum by ~10×, so **draft is not a redesign item.**

## Build it

Mirror `case/step/` — same layout, same driver pattern:

```
parts/step/
  stem_model.py      # build123d model, both variants from one parametric function
  build.py           # emits stem_S_1U.step, stem_S_1U25.step
  validate_step.py   # reuse case/step/validate_step.py unchanged
  render_compare.py  # reuse the case's approach: render SCAD vs STEP, diff
  drawing.py         # NEW - the technical drawing, see below
```

```bash
pip install build123d
python parts/step/build.py            # -> parts/step/stem_S_1U.step, stem_S_1U25.step
python parts/step/validate_step.py parts/step/stem_S_1U.step
```

**Verify against the SCAD, do not assume.** `case/step/render_compare.py` exists precisely because a
re-authored model can drift from its source. The same standing rule from
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

## ⚠️ Status

**None of the above has been executed.** Neither OpenSCAD nor build123d/FreeCAD is available in the
session container where this was written, so every command and the draft-angle table were derived from
the SCAD source by inspection, not by running the toolchain. Treat the parameter list as verified
(read from the file) and the build steps as untested.
