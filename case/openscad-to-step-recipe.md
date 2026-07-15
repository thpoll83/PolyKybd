# Recipe: recreating the PolyKybd case as a clean STEP with open-source Python CAD

**Goal.** Reproduce the OpenSCAD case (`case_polykybd_split72_metal.scad` and the `..._lr.scad`
variants) as closely as possible using an open-source, script-based **B-Rep** CAD toolchain, so the
exported STEP is a real solid model (true planar + cylindrical surfaces, tight tolerances) that a
fabricator's validator accepts — instead of the tessellated mesh you get from OpenSCAD → STL → STEP.

**Why this is needed.** OpenSCAD has no B-Rep kernel; it evaluates everything to a triangle mesh
(CGAL / Manifold). The current `metal-case-left/right.step` is that mesh written out as ~14,900 flat
facets with loose (~0.15 mm) stitching, and the rounded corners are sliver-facet strips — which is what
the fabricator flags. The outer shell in the SCAD is built with `hull()` of two profiles and rounded
with `offset(r=…)`, and `hull`/`minkowski` are precisely the operations that *cannot* survive as clean
geometry. So the fix is to re-author the model in a kernel that has real lofts and fillets.

## Toolchain (all open source)

- **build123d** — Python CAD library on top of OpenCASCADE (the recommended one; modern, Pythonic,
  clean STEP export). `pip install build123d`
- Alternatively **CadQuery** (same OCCT kernel, fluent API): `pip install cadquery`
- **OCP** (OpenCASCADE Python bindings) — pulled in by either; also used directly by the validation
  script below.
- Optional: **Inkscape** CLI (`inkscape --export-type=dxf`) to convert the SVG outlines to DXF, which
  imports more robustly than SVG.

There is **no reliable automatic SCAD → build123d translator** — this is a re-authoring job. But it
stays fully in code (parametric, diffable, CI-reproducible); no interactive CAD.

**Note on effort.** OpenSCAD is already close to what build123d does — same paradigm (describe the solid
in code, parametrically); the only real difference is the kernel underneath (OpenSCAD evaluates to a
mesh, build123d to a B-Rep). So most of the script translates almost line-for-line, and only the couple
of genuinely mesh-flavoured operations change (`hull`→`loft`, `minkowski`→`fillet`). If anything,
build123d lets you state design *intent* more directly — a rounded corner is a real `fillet(r)` instead
of an `offset(r)` that OpenSCAD then approximates into segments.

## Inputs already in the repo

2D profiles (in `case/`), all currently imported by the SCAD at **dpi = 300** (so
`mm = pixels * 25.4 / 300`; apply that scale on import):

| Purpose | File | SCAD var |
|---|---|---|
| Board outline | `poly_kb_wave_right2-OUTLINE.svg` | `pcb_outline` |
| Screw holes | `poly_kb_wave_right2-SCREW.svg` | `drill_holes` |
| Standoff positions | `poly_kb_wave_right2-STANDOFF.svg` | `standoffs_pos` |
| LED holes | `poly_kb_wave_right2-LED.svg` | `led_holes` |
| Switch holes | `poly_kb_wave_right2-SW.svg` | `switch_holes` |
| USB port / clearance | `poly_kb_wave_right2-USB.svg`, `…-USB-extra.svg` | `usb_port_holes`, `usb_clearance` |
| Wedge / tenting | `poly_kb_wave_right2-WD.svg` | `wedge_shape` |
| Nuts / inserts | `poly_kb_wave_right2-Nuts.svg`, `…-NutsInserts.svg` | `nuts`, `nuts_ins` |
| Misc cut-outs | `cut-outs.svg`, `poly_kybd_split72_plate_right-Edge_Cuts.svg` | `cutouts`, `cutouts2` |

Key parameters (from the SCAD header — keep them as Python constants so the port stays parametric):

```
case_height          = 17.5
case_wall_thickness  = 1.5
case_bottom_thickness= 2.0
pcb_clearance        = 0.15
pcb_edge_height      = 9.5
pcb_edge_width       = 1.4
stand_off_extra_radius = 2.3
text_font = "Arial", style bold italic;  text_size = 12;  text_height = 0.35
revision  = "r1.7"
```

## Operation mapping (OpenSCAD → build123d)

| OpenSCAD | build123d equivalent | Notes |
|---|---|---|
| `hull(topProfile, bottomProfile)` | **`loft([bottom_section, top_section])`** | This is the whole outer shell. Loft between the two chamfer sections at z=0 and z=`case_height`. |
| `offset(r=R)` corner rounding | real **`fillet(edges, radius=R)`** | Apply to the vertical corner edges after the loft/extrude → true cylinder surfaces, not segments. |
| `minkowski(cube, cylinder(r))` | `fillet(box.edges(), radius=r)` | The two flip-stand bays: just fillet the cube by the cylinder radius. |
| `linear_extrude(h) <2D>` | `extrude(sketch, amount=h)` | |
| `import(file=svg, dpi=300)` | `import_svg(path)` then `scale(25.4/300)` | Or convert to DXF first (`import_dxf`). Ensure closed paths. |
| `difference()` / `union()` / `intersection()` | `-` / `+` / `&` (boolean ops) | |
| `translate` / `rotate` / `mirror` | `Location`, `Rotation`, `mirror()` | Left case = `right case` mirrored. |
| `text(font,size)` | `Text(...)` → `extrude` | Real font outlines; keep as shallow engrave (`text_height`). Expect many faces. |
| `cylinder` / `cube` / `sphere` | `Cylinder` / `Box` / `Sphere` | |

## Step-by-step recipe

Port module by module — the SCAD already isolates the pieces:

1. **Load the 2D profiles once** into a helper: `import_svg(path)` → take the face(s), scale by
   `25.4/300`, recenter to match the SCAD's `center=true` imports. Cache them in a dict keyed by the
   table above.
2. **Outer shell** (SCAD `pcb_shape_camfer_top` / `_bottom` + the `hull` at line 277):
   - Build the **bottom section** = board outline offset outward by wall thickness/clearance.
   - Build the **top section** = the chamfer offset (the `extra_offet` used in `pcb_shape_camfer_top`).
   - `loft([bottom_section@z0, top_section@z=case_height])` → solid shell blank.
   - `fillet` the vertical corner edges by the corner radius (was the `offset(r=…)`), and chamfer the
     top edge if the SCAD does (`camfer_top`).
3. **Hollow it** (SCAD `inner_walls` / the `linear_extrude … offset(r=pcb_clearance+0.5) import(outline)`):
   extrude the inner (clearance) outline up to `case_height - case_bottom_thickness` and boolean-subtract
   → wall thickness `case_wall_thickness`, floor `case_bottom_thickness`.
4. **Board ledge** (`pcb_edge_height`, `pcb_edge_width`): an inward lip at the board rest height — a thin
   extruded ring subtracted/added per the SCAD.
5. **Standoffs & nut pockets** (`standoffs`, `pcb_standoffs`, `nuts_inserts`, `standoffs_holes`): extrude
   the STANDOFF profile up as bosses (with `stand_off_extra_radius`), drill the SCREW holes through, and
   subtract the Nuts/NutsInserts pockets.
6. **Feature cut-outs**: extrude-cut the LED, SW, USB (+ USB-extra), WD/tenting, `cut-outs.svg` and
   `…Edge_Cuts.svg` profiles through the relevant faces. These are all plain extrude + boolean, so they
   port directly.
7. **Branding** (`branding`): `Text` with the real font, extruded `text_height` and engraved (subtract)
   or embossed (add) on the chosen face; mirror for the left case.
8. **Left / right**: define the right case, then `mirror` across the appropriate plane for the left case
   (SCAD `left_case()` / `right_case()`).
9. **Export**: `export_step(part, "metal-case-right.step")` (and left). build123d writes a clean B-Rep.

## Skeleton (build123d)

```python
from build123d import *

MM_PER_PX = 25.4 / 300            # SCAD imported at dpi=300
CASE_H, WALL, FLOOR = 17.5, 1.5, 2.0
CLEAR, CORNER_R = 0.15, 3.0       # CORNER_R = the offset(r=) you used on the outline

def load(path):                    # SVG -> scaled, centered face
    f = import_svg(path)           # returns wires/edges; make_face if needed
    return scale(f, MM_PER_PX)

with BuildPart() as case:
    bottom = load("poly_kb_wave_right2-OUTLINE.svg")   # + outward offset for wall
    top    = offset(bottom, amount=+0.0)               # the camfer_top offset
    # outer shell as a loft between the two sections (replaces hull())
    with BuildSketch(Plane.XY):        add(bottom)
    with BuildSketch(Plane.XY.offset(CASE_H)): add(top)
    loft()
    # real rounded corners (replaces offset(r=)):
    fillet(case.edges().filter_by(Axis.Z).group_by(SortBy.LENGTH)[-1], radius=CORNER_R)
    # hollow, ledge, standoffs, cut-outs, text ... (boolean cuts/fuses as above)

export_step(case.part, "metal-case-right.step")
```

Treat the API calls above as representative — check them against the installed **build123d** version;
the *structure* (load → loft → fillet → boolean features → export) is what matters.

## Validate the result (open source, OpenCASCADE)

After export, confirm it is a real solid (this is the acceptance test the mesh version failed):

```python
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
from OCP.BRep import BRep_Tool

r = STEPControl_Reader(); r.ReadFile("metal-case-right.step"); r.TransferRoots()
s = r.OneShape()
print("valid B-Rep:", BRepCheck_Analyzer(s).IsValid())

ex = TopExp_Explorer(s, TopAbs_FACE); planar = curved = 0
while ex.More():
    curved += BRepAdaptor_Surface(TopoDS.Face_s(ex.Current())).GetType() != GeomAbs_Plane
    planar += BRepAdaptor_Surface(TopoDS.Face_s(ex.Current())).GetType() == GeomAbs_Plane
    ex.Next()
print("planar/curved faces:", planar, curved, "(curved > 0 means real fillets exist)")

ex = TopExp_Explorer(s, TopAbs_EDGE); mt = 0
while ex.More():
    mt = max(mt, BRep_Tool.Tolerance_s(TopoDS.Edge_s(ex.Current()))); ex.Next()
print("max edge tolerance:", mt, "(want ~1e-6..1e-4, not 0.1)")
```

Pass criteria: `valid B-Rep = True`, **curved faces > 0** (the corner fillets are real cylinders),
**max edge tolerance ≤ ~1e-4 mm** (vs 0.148 in the mesh), and a face count in the hundreds — not ~15,000.
Also compare the bounding box against the old mesh to confirm nothing shifted.

## Automate

Keep it a one-command build, e.g. a `Makefile`:

```
step: case_right.py case_left.py
	python case_right.py   # -> metal-case-right.step
	python case_left.py    # -> metal-case-left.step
	python validate_step.py metal-case-right.step metal-case-left.step
```

so the pipeline is `SVG outlines + params → build123d → clean STEP`, fully open source and reproducible.

## Gotchas

- **SVG import**: build123d needs closed paths; if `import_svg` is fussy, pre-convert with Inkscape to
  DXF and use `import_dxf`. Watch units — apply the `25.4/300` scale and match the SCAD's `center=true`.
- **Corner roundness**: use real `fillet(radius=…)` for true cylinders. If you instead extrude an
  `offset`-rounded polygon you're back to many flat faces (clean, but not arcs).
- **`hull` / `minkowski`**: always map `hull(sectionA, sectionB)` → `loft`, and `minkowski(shape, ball)`
  → `fillet`/`chamfer`. Never try to pass these through a mesh.
- **Text**: real font engraving adds many faces and can slow booleans; do it last, keep it shallow, or
  leave engraving to the fab as a 2D layer.
- **Left vs right**: build the right case, then `mirror` — don't maintain two copies.
