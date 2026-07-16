# Metal case → clean STEP (build123d)

Re-authors the OpenSCAD **metal** case (`../case_polykybd_split72_metal.scad`,
module `right_side_modular`) as a real B-Rep solid using
[build123d](https://build123d.readthedocs.io/) (OpenCASCADE), so the exported
STEP has true planar/cylindrical surfaces and tight tolerances — instead of the
~15 000-facet mesh a fabricator's validator rejects. Follows
[`../openscad-to-step-recipe.md`](../openscad-to-step-recipe.md).

## Build

```bash
pip install build123d          # pulls in OCP (OpenCASCADE bindings)
pip install matplotlib         # only for `make preview`
make                           # -> metal-case-right.step, metal-case-left.step + validate
make preview                   # -> compare.png : this model vs the original mesh
```

`build.py` builds both sides (left = right mirrored across YZ) and writes STEP + a
coarse STL for preview. `validate_step.py` is the acceptance test; `render_compare.py`
renders this model beside `../case_polykybd_split72_metal.stl`.

## What is reproduced

Only the **active** geometry of `right_side_modular()` — the large commented-out
FDM block (standoffs, tenting, branding, flip-stand bays, nut pockets) is **not**
part of the metal case and is not reproduced.

| SCAD op | here | notes |
|---|---|---|
| `hull(camfer_top, scale(1.08) pcb_shape)` | 3-section `loft` of the **convex-hull** sections (bottom @−6.21, widest r2.65 @17.5, cap r1.65 @18.5) + rim `fillet` | outer shell; **`hull()` is convex** so the shell is the convex hull of the outline (see below) |
| `offset(r=…)` corner rounding | `offset(..., kind=Kind.ARC)` | real cylindrical corner faces |
| wedge cut-off (`rotate([-5,0,0]) cube`) | `Box` rotated −5° about X, subtracted | tented underside |
| inner hollow (`hull() offset(outline)`) | 2-D convex hull of the outline, extruded & subtracted | `hull()` of one profile = its convex hull |
| inner border (`offset(outline, −3.35)`) | `offset(…, −3.35)` extruded & subtracted | wave-following inner ledge |
| switch/key cut-outs (`cut-outs.svg`) | X-mirrored faces extruded up, subtracted | 112 key openings |
| LED / SW / USB holes | per-file faces `offset`+extrude, subtracted | side/edge holes |
| left case | `right.mirror(Plane.YZ)` | one source of truth |

## ⚠️ OCCT can silently NO-OP a boolean cut → re-cut on the final part

OpenCASCADE's boolean occasionally leaves a cut **unapplied** against a complex
intermediate solid (it emits `Boolean operation unable to clean`): here the
switch/LED cut of `cut-outs.svg` left **two** keycap LED round holes (wires 9 & 95)
**capped** by the top plate (a solid layer at z 17.3–18.5) while the other 34 cut
through — the "two keys whose round LED space isn't open" bug. The same prisms cut
fine on a simple plate *and* re-cut fine on the final part, so the failure is
intermediate-state-specific. Fix: **re-run the switch cut on the final geometry**
(`build_right` step 8) — idempotent for the openings already cut, and it removes the
caps (verified by vertical raycast: all 36 circles go to 0 crossings). If you add
cut features and something doesn't open, raycast the suspect XY through the model and
check for stray crossings before assuming the profile is wrong.

## ⚠️ The outer shell is CONVEX (`hull()`), not the raw outline

OpenSCAD `hull()` returns a **convex** hull. The SCAD builds the outer shell as
`hull(camfer_top, pcb_shape)`, so the shell is the **convex hull** of the outline —
concavities (the front wave, thumb notch) are filled. The inner hollow is *also*
`hull(...)` → convex. A plain `loft` of the raw (concave) outline instead of its convex
hull leaves the wall concave in the front while the convex inner pocket stays put, so the
pocket **pokes through the wall = a hole in the front**. Fix: the loft sections are the
**convex hull** of the outline (`pcb_shape_convex`), so outer ⊇ inner everywhere.
(The concave, wave-following outline is what the *3-D-printed* case uses — a different model.)

## Bottom-plate rabbet (POST-PROCESSING feature — not in the .scad)

The reference `parts/metal-case-*.step` adds, around the wedge-cut bottom opening, a
**rabbet that seats a bottom plate** — this was a manual post-processing step, so it is
**not** in `case_polykybd_split72_metal.scad`. It shows up as the two things you described:
the *"small extrusion perpendicular to the cut-off"* (an outer **lip** dropping below the
wedge plane) plus the *"inner cut-out rim"* (a recessed **ledge** the plate rests on).

`add_bottom_rabbet()` reproduces it. The lip must be the **actual wall cross-section at
the wedge plane**, extended perpendicular to that plane. It flattens the wedge plane to
horizontal, takes a thin slice of the **real wall** just above it (`part & slab` — the true
wedge-plane section, which follows the taper), translates that slice **down** `LIP_DROP` for
the lip, then recesses the inner region so the ledge sits `RABBET_UP` above the plane
(pocket = `LIP_DROP+RABBET_UP` ≈ 2 mm = `case_bottom_thickness`), and rotates back.

⚠️ **Do not build the lip from the `scale(1.08)` loft-bottom silhouette (the straight-cut
cross-section).** The wall tapers, so the wedge plane meets a *narrower* wall on the raised
(back) side; the wide straight-cut footprint then makes the lip **stick out past the wall
exactly where the case gets thinner**. Slicing the real wall (`part & slab`) hugs it on
every edge. (The recess *cut* can still use the clean `scale(1.08)` footprint — a slightly
off cut only changes the ledge width; only the added *lip* must match the wall.) Parameters
at the top of `case_model.py` — measured from the reference (mine frame): wedge bottom
−6.21, lip bottom **−7.19**, ledge **−5.1**:

```python
WITH_BOTTOM_RABBET = True
LIP_DROP  = 1.0    # lip depth, perpendicular from the cut-off plane
RABBET_UP = 1.0    # inner ledge recess above the cut-off plane
LIP_W     = 4.0    # outer lip band width
```

Set `WITH_BOTTOM_RABBET = False` for the pure SCAD reproduction.

⚠️ **Use CLEAN convex tools, never the boolean-extracted bottom wire.** Offsetting the
messy extracted `bf.outer_wire()` leaves free edges, and the STEP then exports as an **open
shell** (`solids=0`) whose bottom faces read **inward** in a viewer (you see through the
bottom). The clean convex footprint booleans into a **single closed solid** — verify with
`solids=1, shell closed=True` (both sides pass). Verified vs the reference: lip bottom −7.18
(ref −7.19), overall height 25.71 mm (ref 26.05).

## ⚠️ Two corrections vs. the recipe (learned from the geometry)

1. **Do NOT apply the `25.4/300` (dpi) scale.** The KiCad SVGs already declare their
   size in **millimetres** (`width="195.3006mm"`, matching viewBox units), and
   build123d's `import_svg` reads real mm. OpenSCAD's `dpi=300` is ignored here for the
   same reason (it only scales *unit-less* px). Applying the recipe's `scale(25.4/300)`
   would shrink the case ~12× (to ~16 mm). Verified: the exported bbox
   (≈200 × 141 × 25 mm) matches the original STL to <0.3 mm on every axis.

2. **`rotate([0,180,0])` in `linear_extrude(h) rotate([0,180,0]) <2D>` acts on the flat
   2-D profile, i.e. it is a pure X-mirror — then the extrude goes up.** Rotating the
   *solid* 180° about Y instead sends the prisms to z < 0, below the case, and no holes
   are cut. Mirror the faces (`Plane.YZ`), then extrude upward.

`center=true` imports are reproduced by recentring each face on its own bounding-box
centre; non-centred imports (LED/SW/USB) keep file coordinates and are placed by the
same `translate([-92,-72,1])` as the SCAD. build123d and OpenSCAD both flip SVG Y about
the document height, so the coordinates line up.

## Acceptance (validate_step.py)

Both sides pass:

- `valid B-Rep = True`
- **curved faces > 0** (519 — real corner cylinders + rim tori)
- **max edge tolerance ≈ 1e-5 mm** (vs 0.148 in the mesh export)
- ~1359 faces (vs ~15 000 facets), bbox 200.1 × 142.9 × **25.7** mm (with the bottom
  rabbet; ~24.7 mm without it, i.e. the pure SCAD reproduction)

## Memory note

OpenCASCADE's allocator over-reserves address space during the 112-key-hole
booleans and can trip the container/OS OOM killer even with plenty of free RAM.
`build.py` sets a soft `RLIMIT_AS` (~6.5 GB) at startup, which keeps the allocator
conservative and makes the build reliable (it just runs a bit slower). If you drive
the model directly instead of via `build.py`, cap it yourself first:
`ulimit -v 6000000` (Linux) before `python case_model.py`.
