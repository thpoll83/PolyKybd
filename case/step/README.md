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

`add_bottom_rabbet()` reproduces it. The lip is a **perpendicular extrusion of the cut-off
*area***: flatten the wedge plane to horizontal, grab the real wedge-plane bottom face `bf`
(the actual section outline at that plane, following the taper), and extrude **that face**
as a *constant* prism straight down the plane normal (`dir=(0,0,-1)`, overlapping 0.5 mm up
into the wall so the fuse is a genuine overlap). Then recess the inner region so the ledge
sits `RABBET_UP` above the plane (pocket = `LIP_DROP+RABBET_UP` ≈ 2 mm =
`case_bottom_thickness`), and rotate back.

⚠️ Two wrong ways this went before:
- the **`scale(1.08)` loft-bottom silhouette** (the *straight-cut* section) extruded at the
  wedge angle — too wide on the tapered/back side, so the lip sticks out where the case gets
  thinner; and
- translating a thin **slice** of the wall down — the slice carries the wall's own taper, so
  the lip face tapers ("starts smaller then expands") instead of being perpendicular.

Extruding the single wedge-plane section as a constant prism is both perpendicular *and*
taper-free. Two more traps:
- `extrude(bf, negative)` extrudes UP along the face's downward normal — force `dir=(0,0,-1)`.
- Extruding **from z0 with no overlap** is what keeps the lip flush with the wall (a 0.5 mm
  overlap makes the constant prism poke ~0.1 mm past the tapering wall at the join). But the
  lip's top face is then exactly coincident with the part's bottom face, so a plain fuse
  opens the shell — weld it with a **glue-fuse** (`BOPAlgo_GlueShift`, see `_glue_fuse`).
- The recess footprint is a **uniform inward offset of the real section** (a clean convex
  polygon of `bf`'s own vertices, `offset(convex_hull_face(bf), −LIP_W)`). Using
  `scale(1.08)` there scales about the origin, pushing the far short-side ends out more, so
  the retained lip band comes out **wider on the short sides** — the plate recess must be a
  uniform band on every edge.

Parameters at the top of `case_model.py` — measured from the reference (mine frame): wedge
bottom −6.21, lip bottom **−7.19**, ledge **−5.1**:

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

## USB inner-wall chamfer (POST-PROCESSING feature — not in the .scad)

`add_usb_chamfer()` puts a 45° lead-in on the **interior** face of the wall around each
USB window, so the connector/cable enters cleanly. The two windows (fixed by the committed
SVGs) are **USB1**, the side window in the left/inner wall (normal +X), and **USB0**, the
window in the back-left wall (normal −Y).

It is applied on the **bottom edge only** — toward the **open bottom** of the case, where
nothing is in the way. The window's top/sides run into the interior ceiling step (which made
a full-perimeter lead-in awkward to contain), but below the window is clear wall all the way
to the open bottom, so a bottom lead-in is unobstructed. `_usb_bottom_bevel` subtracts a
**triangular prism** along the window's bottom edge: at the inner wall surface the opening
drops `USB_CHAMFER` below the window bottom, tapering back to the window bottom `USB_CHAMFER`
deep into the wall (a 45° ramp). No clip needed. The bevel's inner leg is started
`USB_BEVEL_OVERCUT` (0.4 mm) **interior of the measured inner wall face** (into the empty
cavity), so no thin wall sliver survives — a sub-0.1 mm error in the wall-face coordinate
otherwise left a ~0.05 mm wall between the bevel and the real inner face. Params:

```python
WITH_USB_CHAMFER = True
USB_CHAMFER = 3.0      # 45° lead-in depth/width on the inner face
```

Because the funnels live **inside `build_right()`** (before the YZ mirror), the left case
gets them for free.

## Interior wall-meets-floor chamfer (POST-PROCESSING feature — not in the .scad)

A 45° chamfer along the interior seam where the inner wall meets the interior floor (the
top-plate underside, z=13.65). That corner is **concave**, so a plain subtractive bevel
removes nothing — instead the chamfer is applied to the **negative volume**: `_chamfered_pocket`
tapers the inner-hollow pocket's **top edge** inward by `WALLFLOOR_CHAMFER` (a `loft`, since a
build123d edge `chamfer()` fails on the arc-cornered pocket), and subtracting that leaves a
clean 45° fillet-of-material transition exactly on the wall/floor corner. It is applied to
**both** inner negatives — the convex hull pocket (floor z=13.65) **and** the deeper "border"
pocket (floor z=14.95) — so the interior steps down through **two** chamfered transitions.

```python
WITH_WALLFLOOR_CHAMFER = True
WALLFLOOR_CHAMFER = 2.0   # 2 mm is the clean maximum here — see note
```

⚠️ **3 mm is not achievable at this corner.** The interior ledge between the inner wall and
the next pocket (the SCAD **"border"**, offset −3.35) is only ~4 mm wide, so a ≥2.5 mm chamfer
consumes it and **degenerates the boolean** (the border rises 1.3 mm above the ledge → a
sub-1 mm sliver). Verified: clean at ≤2 mm, broken at ≥2.5 mm — 2 mm is the clean maximum.

## Branding: engraved "PolyKybd" on the convex-hull front-bezel top (not in the .scad)

The SCAD `branding()` engraves **PolyKybd** (Arial Bold Italic, 0.35 mm deep) on the **FDM
case bottom**. The metal case has no such bottom face, so `add_branding()` places the same
engraving on the flat top area the **convex hull** created in front of the thumb cluster —
the extra bezel the hull fills in where the raw outline is concave (the "little extra area"
from the convex-hull outer shell). It is drawn as **two staggered lines** — **"Poly"** up/left,
**"Kybd"** down/right — at a smaller size than the SCAD's single size-12 line (the top band is
narrower), centred toward the case centre. Engraved (subtracted) to match the SCAD's `difference()`.

```python
WITH_BRANDING = True
BRAND_LINES = ("Poly", "Kybd"); BRAND_SIZE = 7.0; BRAND_DEPTH = 0.35   # two staggered lines
BRAND_X = 12.0; BRAND_Y = -47.0; BRAND_TOP_Z = 18.5                    # block centre on the bezel
BRAND_STAG_X = 3.0; BRAND_STAG_Y = 3.6                                 # 2nd line offset (+X, −Y)
BRAND_FONT = ".../LiberationSans-BoldItalic.ttf"                       # Arial Bold Italic metric clone
```

Text is built with build123d `Text` (**Liberation Sans Bold Italic** — the metric-compatible
Arial substitute present on Linux; there is no Arial), extruded and subtracted 0.35 mm into
the z=18.5 plateau. ⚠️ **Branding is applied AFTER the YZ mirror, per side**, so the logo
reads correctly (not mirror-backwards) on **both** halves: `build.py` does one heavy build
(`build_right(with_branding=False)`, which includes the USB + wall-floor chamfers), engraves
the right at `(BRAND_X, BRAND_Y)`, and engraves the mirrored left at `(−BRAND_X, BRAND_Y)`.
Set `WITH_BRANDING = False` (+ `WITH_USB_CHAMFER`/`WITH_WALLFLOOR_CHAMFER = False`) for the
pure SCAD reproduction.

## Display/encoder pocket — rounded corners (not in the .scad)

The SCAD's "extra space around display" is a square-cornered `cube([30,69,5])` @
(−75, 21.5, 15.4) that covers both the status display and the rotary-encoder area. Its
four **vertical corners are rounded** (`DISPLAY_CORNER_R`, default 2 mm) by filleting the
box's Z-parallel edges before subtracting.

```python
DISPLAY_CORNER_R = 2.0   # 0 = square corners (pure SCAD)
```

A **rotary-encoder blind pocket** is added on the pocket's **right edge**. It uses the
encoder's **own cutout shape** — the rotated-square `cut-outs.svg` face whose corner sits
at the pocket edge ≈(−55,−5), found by the vertex nearest `ENCODER_ANCHOR`. The **actual
encoder cutout stays** (that face is still cut through with the other switches — the real
through-hole is needed); on top of it an **enlarged BLIND body recess** is added: the same
face **enlarged** (offset `ENCODER_GROW`) to reach past the pocket edge, cut at the **same
z-depth as the display box** (z 12.9–17.9) so it stays under the top skin (z 17.9–18.5).
`ENCODER_ANCHOR` is a final-frame coord, converted to the pre-`X_SHIFT` frame where the
display Box + `cut_faces` live.

The recess is additionally **extended in Y only** by `ENCODER_GROW_Y` (the blind body is
unioned with two copies shifted ±`ENCODER_GROW_Y/2` in Y, so the X footprint is unchanged
and the Y span grows by `ENCODER_GROW_Y` total) — tuning the fit without widening X.

```python
WITH_ENCODER_POCKET = True
ENCODER_ANCHOR = (-55.0, -5.0)   # final-frame corner of the encoder cutout
ENCODER_GROW   = 3.5             # offset each side: widen the blind body recess
ENCODER_GROW_Y = 1.0             # extra Y-only span (X left as-is)
```

## Logo: engraved PolyTasten/PolyFabriq wordmark under the display (not in the .scad)

`add_logo()` engraves the stylised-keyboard wordmark from `polykybd.svg` on the **same top
plateau (z=18.5)** as the branding text, `LOGO_DEPTH` deep, on the front bezel **under the
display cutout**. `polykybd.svg` carries two side-by-side copies; only the left copy
(`bbox.min.X < 28`) is kept, scaled by `LOGO_SCALE`, and re-centred on `LOGO_CENTER` from the
**final** prism bbox (build123d's `scale()` is not about the origin, so recentring after
scale is required). Like the text it is applied **after the YZ mirror, per side** — the left
half passes `mirror_x=True` so the wordmark reads un-mirrored on both halves.

```python
WITH_LOGO   = True
LOGO_SVG    = "../../polykybd.svg"
LOGO_CENTER = (-70.0, -46.0)     # final-frame XY, front bezel under the display
LOGO_SCALE  = 0.45               # raw wordmark ≈25×24 mm → ≈11.4×11 mm
LOGO_DEPTH  = 0.35               # same engrave depth as the text
```

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
