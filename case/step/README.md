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

`add_bottom_rabbet()` reproduces it. Flatten the wedge plane to horizontal, grab the real
wedge-plane bottom face `bf`, then — the recipe that is BOTH a uniform rim AND an
export-stable closed solid (this took several wrong tries, see below):
- **LIP** = a **full plate** from the real outer boundary `make_face(bf.outer_wire())`,
  extruded a constant `LIP_DROP` straight down the plane normal (`dir=(0,0,-1)`), glue-fused
  to the part (`BOPAlgo_GlueShift`, `_glue_fuse` — the plate top is coincident with the wall
  bottom).
- **LEDGE** = reopen the interior + recess it `RABBET_UP` above the plane using a
  **convex-hull** inset `offset(convex_hull_face(bf), −LIP_W)` — leaving the `LIP_W` rim band
  (pocket = `LIP_DROP+RABBET_UP` ≈ 2 mm = `case_bottom_thickness`). Then rotate back.

⚠️ **This is applied LAST in `build_right` (after the USB-chamfer + re-cut booleans), not at
step 7.** Running those later wall/keycap booleans on top of the remodelled rabbet bottom
turned the cut into a NO-OP that left an **open shell**.

⚠️ **Two shape choices are forced by what survives STEP export** — `validate_step.py` now
counts `solids` (must be **1**), because `BRepCheck_Analyzer.IsValid()` is topological only
and happily passes an **open shell** (`solids=0`) whose bottom faces read **inward** (you see
through the bottom). Both traps produce an in-memory `solids=1` that `export_step` →
re-import collapses to `solids=0`:
- **LIP must be the full plate, NOT a thin ring** (`of − offset(of,−LIP_W)`). The ring
  glue-fuses to a near-degenerate solid that STEP re-reads as an open shell; the full plate
  (single clean outer boundary) round-trips as `solids=1`. The plate still yields a uniform
  rim because the LEDGE cut reopens its centre.
- **LEDGE must be the convex hull, NOT a boolean-offset of the real outer wire**
  (`offset(make_face(bf.outer_wire()),−LIP_W)`). The real-wire offset subtracts to another
  export-unstable solid; `convex_hull_face(bf)` is a clean polygon that insets cleanly.
- ⚠️ **`LIP_W` must be SMALLER than the THIN front wall** (2.0, not 4.0). The ledge shelf is
  formed by the recess cut `offset(convex_hull_face(bf),−LIP_W)` landing **inside the wall**
  and removing material up to `z0+RABBET_UP`. On the back the wall is thick so any `LIP_W`
  lands in it; but the **front wall is thin** (the wedge grazes it), so at `LIP_W=4` the cut
  boundary falls **past** the wall into the already-open cavity — it removes nothing and **no
  front ledge forms** (the "rim missing on the thin front edge" report). At `LIP_W=2` the cut
  lands in the front wall and a uniform ledge appears, matching the reference (lip at
  zflat −0.9, ledge at zflat +0.65, both front and back — verified against
  `parts/metal-case-right.step` in the wedge-flattened frame).
- `extrude(bf, negative)` extrudes UP along the face's downward normal — force `dir=(0,0,-1)`.

Parameters at the top of `case_model.py`:

```python
WITH_BOTTOM_RABBET = True
LIP_DROP  = 0.9    # lip depth, perpendicular from the cut-off plane (ref: -0.9)
RABBET_UP = 0.6    # inner ledge recess above the cut-off plane (ref ledge ~+0.65)
LIP_W     = 2.0    # outer lip/ledge-cut inset (uniform); MUST be < the thin front wall (see above)
```

Set `WITH_BOTTOM_RABBET = False` for the pure SCAD reproduction.

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
from the convex-hull outer shell). It is drawn as a **single "PolyKybd" line** at a smaller
size than the SCAD's size-12 line (the top band is narrower), centred toward the case centre.
Engraved (subtracted) to match the SCAD's `difference()`. (`BRAND_LINES` as a 2-tuple staggers
onto two lines — **"Poly"** up/left, **"Kybd"** down/right — via `BRAND_STAG_X/Y`; the single
line was chosen as final. The separate raised-`hull()` **PolyKybd logo** that was tried earlier
was dropped entirely — "better without it".)

```python
WITH_BRANDING = True
BRAND_LINES = ("PolyKybd",); BRAND_SIZE = 7.0; BRAND_DEPTH = 0.35      # single line (2-tuple = staggered)
BRAND_X = 16.0; BRAND_Y = -47.0; BRAND_TOP_Z = 18.5                    # block centre on the bezel
BRAND_STAG_X = 3.0; BRAND_STAG_Y = 3.6                                 # 2nd-line offset if 2 lines
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
z-depth as the display box** so it stays under the top skin.
`ENCODER_ANCHOR` is a final-frame coord, converted to the pre-`X_SHIFT` frame where the
display Box + `cut_faces` live.

⚠️ **Top skin over BOTH recesses is 1.2 mm, not 0.6 mm (thickened for the metal case).** The
display + encoder recesses originally floored at **z17.9**, leaving only a **0.6 mm** skin under
the z18.5 top plateau — too thin for a *metal* case. Both were dropped to floor at **z17.3**
(skin = 18.5 − 17.3 = **1.2 mm**) by shortening the two pockets: the display `Box` height and
the encoder blind-recess `extrude(enc_face, amount=…)` were each reduced by 0.6 mm (encoder
`5 → 4.4`). ⚠️ **Only the BLIND recess depths changed — the encoder *through-cut* (`enc_src` in
`cut_faces`) is untouched.** Verify the skin with a vertical raycast over each pocket (see
"Measuring the solid" below): a hit pair of `[17.30, 18.50]` is the correct 1.2 mm skin.

The recess Y-extent is additionally grown by `ENCODER_GROW_Y` (X unchanged): the enlarged
`enc_face` is **scaled in Y about its centre** so the bbox height grows by `ENCODER_GROW_Y`
mm — one clean pocket (not a doubled/lumpy body). build123d's `scale()` is not about the
origin, so the face is re-centred on its original Y centre afterwards.

```python
WITH_ENCODER_POCKET = True
ENCODER_ANCHOR = (-55.0, -5.0)   # final-frame corner of the encoder cutout
ENCODER_GROW   = 3.5             # offset each side: widen the blind body recess
ENCODER_GROW_Y = 1.0             # extra Y-only span (single Y-scale of the face)
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

⚠️ **The LED SVG holds OPEN strokes, not filled regions** — `poly_kb_wave_right2-LED.svg`
is line segments (each wire is a single edge). OpenSCAD's `offset(r=0.9) import(...)`
implicitly closes each degenerate path and inflates it into a rounded **slot** of width
`2·0.9`. build123d's `make_face` rejects an open wire, so `raw_faces_all` returned `[]` and
the **LED light-pipe slots silently vanished**. `raw_slot_faces(fn, r)` reproduces OpenSCAD:
it offsets each open wire by `r` (`Kind.ARC`) into the closed stadium outline, then faces it
(extrude directly — the `r` offset already IS the slot, so no second offset). ⚠️ **The switch
SVG `poly_kb_wave_right2-SW.svg` is the SAME open-stroke case** (2 slots on the wall *opposite*
the LED slots) — it also went through `raw_faces_all` → `[]`, so the **switch openings were
missing too**; it now uses `raw_slot_faces(..., 2.5)`. Only the **USB** SVG is filled regions,
keeping the `raw_faces_all` + `offset` path.

## Bottom-plate screw holes (POST-PROCESSING — not in the .scad)

4 pilot holes for **M2×4 self-tapping** screws that fix the bottom plate (aluminium → no
thread; the screw cuts its own on first use, so `SCREW_HOLE_D = 1.6` is a tight thread-cutting
pilot). Drilled in `add_bottom_rabbet` in the **wedge-flattened frame** — so the hole **axes
run perpendicular to the odd, tilted bottom plane**, not to global Z (this was an explicit
design check). Each engages `SCREW_HOLE_DEPTH` (**6.5 mm** = the M2×4 screw + ~2 mm slack) of
body above the ledge. `WITH_SCREW_HOLES` toggles them; positions are `SCREW_HOLES` (flattened XY).

⚠️ The case walls are thin, so the holes sit in the thicker **corner L-junctions** (outer shell
solid, any opening faces the interior). The two **front** corners are useless — the wedge makes
the front shallow, with no material at the ledge — so the front holes are **moved north to the
side "knees"** (where the diagonal front wall meets the vertical side wall).

**Placement + break-out verification (how the positions were chosen):**
- **On the ledge shelf, not the wall.** A good spot is the **centroid of the ledge-shelf face**
  ("middle of the ledge") — hole #1 landed there naturally; #2/#3/#4 were moved onto their own
  shelf centroids, then nudged by hand (#2 → x99).
- **Break-out is checked, not eyeballed.** For a candidate `(x,y)`, build the **thread envelope**
  as a `Cylinder(radius≈1.1, Ø2.2)` (the tapped/expanded ⌀, wider than the 1.6 pilot) at the
  hole depth and compute the **volume-fill fraction** `vol(cyl ∩ part) / vol(cyl)`. ~1.0 = fully
  buried; a low fraction (the front holes were only ~44 % enclosed when too far inboard) means
  the thread would break out through a wall. The front holes were pushed **1.5 mm outward** until
  the envelope was fully enclosed (edge distance ≈ 2.3 mm).
- The **bottom-plate SVG** (`plate_svg.py`, below) emits these same `SCREW_HOLES` as Ø2.2 M2
  clearance circles so the plate matches the tapped case.

## Bottom-plate SVG (`plate_svg.py`)

Emits a flat, dimensioned SVG of the bottom plate for **both** halves
(`bottom_plate_right.svg`, `bottom_plate_left.svg`), extracted from the built STEP:

```bash
python3 plate_svg.py        # -> bottom_plate_{right,left}.svg
```

The plate **drops into the recess and rests on the ledge**, so the cut line is the **recess
opening**, not the rim. Everything is measured in the **wedge-flattened frame** (the plane the
plate lies in — same `flatten()` as the rabbet/holes) and drawn top-view (Y flipped for SVG,
un-mirrored; the left file is the pure X-mirror). Two outlines + the holes:
- **black solid = plate cut line = recess opening** — the **ledge outer wire** at flattened
  `z ≈ +0.64` (`outer_loop(pf, 0.64)`). Add your own ~0.1–0.2 mm inward fit clearance.
- **grey dashed = outer rim edge** (case outer boundary) at flattened `z ≈ −0.86` — reference only.
- **red = the 4 `SCREW_HOLES`** as **Ø2.2 mm M2-clearance** circles + centre cross-hairs.

`outer_loop(pf, zlevel)` grabs the largest downward face (`normal.Z < −0.7`) whose `bbox.min.Z`
matches the level and samples its biggest wire at 0.4 mm steps. ⚠️ The two z-levels (`+0.64`
ledge, `−0.86` rim) are the flattened-frame rabbet levels — if `LIP_DROP`/`RABBET_UP` change,
re-check them (they are literals in `main()`).

## Measuring the solid (raycast + fill fraction)

The reusable way to *measure* a built solid (skin thickness, wall thickness, hole depth) without
eyeballing — used to verify the 1.2 mm skins and the screw break-out above:

```python
from build123d import import_step
from OCP.gp import gp_Pnt, gp_Dir, gp_Lin
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
part = import_step("metal-case-right.step").wrapped
def zhits(x, y):                       # sorted Z of every surface a +Z ray through (x,y) crosses
    it = BRepIntCurveSurface_Inter(); it.Init(part, gp_Lin(gp_Pnt(x, y, -50), gp_Dir(0, 0, 1)), 1e-7)
    zs = []
    while it.More(): zs.append(it.Pnt().Z()); it.Next()   # note: .Z() is a METHOD, call it
    return sorted(zs)
# adjacent pairs = solid spans. Over a recess: [17.30, 18.50] => 1.20 mm top skin.
```

- **Skin / wall thickness** = the gap of a solid span (`zhits` pair) over the feature.
- **Screw break-out** = volume-fill fraction of the thread envelope:
  `Cylinder(radius=1.1, height=h)` at the hole, then `vol(cyl & part) / vol(cyl)` (build123d
  `&` + `GProp_GProps`/`BRepGProp.VolumeProperties_s`). ~1.0 = buried; low = breaks out.

The **`verify-case-step-geometry` skill** wraps both of these + the build/validate loop.

## Acceptance (validate_step.py)

Both sides pass:

- `valid B-Rep = True`
- **exactly one solid** with positive volume (`solids == 1`) — the check that catches the
  open-shell/inward-normal failure `BRepCheck_Analyzer.IsValid()` passes (see the rabbet notes)
- **curved faces > 0** (~700 — real corner cylinders + rim tori)
- **max edge tolerance ≈ 1e-5 mm** (vs 0.148 in the mesh export)
- ~1643 faces (vs ~15 000 facets), bbox 200.1 × 142.9 × **25.6** mm (with the bottom
  rabbet; ~24.7 mm without it, i.e. the pure SCAD reproduction)

## Memory note

OpenCASCADE's allocator over-reserves address space during the 112-key-hole
booleans and can trip the container/OS OOM killer even with plenty of free RAM.
`build.py` sets a soft `RLIMIT_AS` (~6.5 GB) at startup, which keeps the allocator
conservative and makes the build reliable (it just runs a bit slower). If you drive
the model directly instead of via `build.py`, cap it yourself first:
`ulimit -v 6000000` (Linux) before `python case_model.py`.
