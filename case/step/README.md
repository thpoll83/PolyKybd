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
| `hull(camfer_top, scale(1.08) pcb_shape)` | 3-section `loft` (bottom @−6.21, widest r2.65 @17.5, cap r1.65 @18.5) + rim `fillet` | outer shell; flares to ~200 mm at the wedge-cut bottom |
| `offset(r=…)` corner rounding | `offset(..., kind=Kind.ARC)` | real cylindrical corner faces |
| wedge cut-off (`rotate([-5,0,0]) cube`) | `Box` rotated −5° about X, subtracted | tented underside |
| inner hollow (`hull() offset(outline)`) | 2-D convex hull of the outline, extruded & subtracted | `hull()` of one profile = its convex hull |
| inner border (`offset(outline, −3.35)`) | `offset(…, −3.35)` extruded & subtracted | wave-following inner ledge |
| switch/key cut-outs (`cut-outs.svg`) | X-mirrored faces extruded up, subtracted | 112 key openings |
| LED / SW / USB holes | per-file faces `offset`+extrude, subtracted | side/edge holes |
| left case | `right.mirror(Plane.YZ)` | one source of truth |

## Bottom-plate rabbet (POST-PROCESSING feature — not in the .scad)

The reference `parts/metal-case-*.step` adds, around the wedge-cut bottom opening, a
**rabbet that seats a bottom plate** — this was a manual post-processing step, so it is
**not** in `case_polykybd_split72_metal.scad`. It shows up as the two things you described:
the *"small extrusion perpendicular to the cut-off"* (an outer **lip** dropping below the
wedge plane) plus the *"inner cut-out rim"* (a recessed **ledge** the plate rests on).

`add_bottom_rabbet()` reproduces it: it flattens the slanted wedge face (rotate about X by
the wedge angle), extrudes the outer wall silhouette band **down** `LIP_DROP` for the lip
and recesses the inner region **up** `RABBET_UP` for the ledge (pocket = `LIP_DROP+RABBET_UP`
≈ 2 mm = `case_bottom_thickness`), then rotates back. Parameters at the top of
`case_model.py` — measured from the reference (mine frame): wedge bottom −6.21, lip bottom
**−7.19**, ledge **−5.1**:

```python
WITH_BOTTOM_RABBET = True
LIP_DROP  = 1.0    # outer lip drop below the wedge plane
RABBET_UP = 1.0    # inner ledge recess above the wedge plane
LIP_W     = 4.0    # outer lip band width
```

Set `WITH_BOTTOM_RABBET = False` to get the pure SCAD reproduction. **Known limitation:**
the lip footprint uses the clean `scale(1.08)` outer silhouette, which tracks the real
opening on the low/front edge (the primary seat) but can sit up to ~a few mm proud on the
high/back edge where the outer wall tapers inward — tune `LIP_W`/the silhouette scale if the
back seat matters. Verified against the reference: lip bottom −7.18 (ref −7.19), overall
height 25.68 mm (ref 26.05).

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
- **curved faces > 0** (458 — real corner cylinders + rim tori)
- **max edge tolerance ≈ 3e-7 mm** (vs 0.148 in the mesh export)
- ~1324 faces (vs ~15 000 facets), bbox 200.1 × 142.9 × **25.7** mm (with the bottom
  rabbet; **24.7** mm without it, i.e. the pure SCAD reproduction)

## Memory note

OpenCASCADE's allocator over-reserves address space during the 112-key-hole
booleans and can trip the container/OS OOM killer even with plenty of free RAM.
`build.py` sets a soft `RLIMIT_AS` (~6.5 GB) at startup, which keeps the allocator
conservative and makes the build reliable (it just runs a bit slower). If you drive
the model directly instead of via `build.py`, cap it yourself first:
`ulimit -v 6000000` (Linux) before `python case_model.py`.
