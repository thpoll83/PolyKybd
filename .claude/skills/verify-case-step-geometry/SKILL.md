---
name: verify-case-step-geometry
description: Rebuild the build123d metal-case STEP (case/step/) and MEASURE a geometry feature to confirm it is right — skin/wall thickness over a recess, a hole's depth/perpendicularity, or a screw hole's break-out margin — rather than eyeballing a render. Use after editing case_model.py (recess depth, skin thickness, screw-hole position/depth, rabbet, wall) and whenever the user asks "how thick is the skin / wall there", "is the hole deep enough / perpendicular", "will the screw break out", "verify the recess", or before committing a case change. NOT for firmware or PCB work.
---

# Verify a metal-case STEP feature (build123d)

The case model (`case/step/case_model.py`, built by `build.py`) is measured, not
eyeballed — a render hides thin skins, shallow holes and break-out. This skill is
the loop used all through the case work: **build → validate → measure the specific
feature the change was about → report the number**. It answers three questions with
hard numbers:

1. **Skin / wall thickness** over a recess (display/encoder pocket, a wall).
2. **Hole depth + perpendicularity** — does a drill engage enough body, along the
   tilted-bottom normal.
3. **Screw break-out** — is the tapped-thread envelope fully buried in material.

Repo dir: `/home/user/PolyKybd/case/step`
Outputs: `metal-case-right.step`, `metal-case-left.step` (+ `.stl`).

## When to expect which question

| Change kind | Measure |
|---|---|
| Recess depth / "make the skin 1.2 mm" | skin thickness raycast over the pocket |
| Drill hole depth / "2 mm deeper" | hole-span raycast; solid remaining below |
| Screw-hole reposition / "might break out" | thread-envelope fill fraction |
| Rabbet / wall tweak | `validate_step` solids==1 + wall raycast |

Tell the user the number, not "looks fine".

## Procedure

1. **Build.** The full build is slow (~5–10 min) and memory-hungry — always via
   `build.py` (it sets the `RLIMIT_AS` OOM cap). Run it in the background and read
   the output file when it finishes; do not poll with a foreground `sleep`.
   ```bash
   cd /home/user/PolyKybd/case/step && python3 build.py
   ```
   A clean run prints `[right] … faces=… vol=… bbox=…` then `[left] …`.

2. **Validate — the closed-solid gate.** ⚠️ `BRepCheck_Analyzer.IsValid()` passes an
   OPEN SHELL; the real gate is **`solids == 1`** (a post-processing boolean that
   silently no-ops leaves `solids=0`, inward bottom normals, "see through the case").
   ```bash
   python3 validate_step.py metal-case-right.step metal-case-left.step   # want: PASS, solids: 1
   ```
   If `solids: 0` → an open shell; the last rabbet/wall/USB boolean no-op'd (see the
   README "Bottom-plate rabbet" traps) — fix before measuring anything else.

3. **Measure the feature** with the helper below (`measure_case.py`, sitting beside
   this SKILL.md). It raycasts and computes fill fractions on the built STEP:
   Run it **from `case/step/`** (so it can `import case_model` / `plate_svg` and find
   the `.step`). Reference it by its repo-root path:
   ```bash
   cd case/step
   S=../../.claude/skills/verify-case-step-geometry/measure_case.py
   python3 "$S" skin  -55 -5     # skin thickness over (x,y)
   python3 "$S" hole  -88 62     # solid span at a hole (global frame)
   python3 "$S" screw            # break-out fill % for every SCREW_HOLES entry (or pass an index)
   ```
   - **skin**: prints the sorted Z hits; a top-skin pair like `[17.30, 18.50]` = **1.20 mm**.
     A recess floors low and the top solid span IS the skin. Sample a few (x,y) across
     the pocket — the recess is not a point.
   - **hole**: the solid spans a +Z ray crosses; the gap where the drill removed material
     is the bore, the solid below it is what the screw bites into.
   - **screw**: **flattens the part first** (holes are drilled perpendicular to the tilted
     bottom, so break-out only reads right in the flattened frame), then measures the
     **annular wall** between the pilot bore (Ø`SCREW_HOLE_D`) and the Ø2.2 thread envelope
     over each `SCREW_HOLES` entry — the fraction of that tube that is solid. `~1.0` = the
     thread is fully surrounded; a low value = it breaks out through a wall, so move the
     hole outward until it's ~1.0. ⚠️ Measure the **annulus**, not a solid cylinder: the
     STEP already has the bore subtracted, so a plain Ø2.2 cylinder caps at ~0.5 even when
     perfectly buried (the hollow bore is half its volume).

4. **Report the number** and whether it meets the target (e.g. "skin 1.20 mm ✓,
   was 0.60"). Only then commit.

## Measuring by hand (if the helper isn't present)

Core recipe — a vertical ray, adjacent Z-hit pairs are solid spans:

```python
from build123d import import_step
from OCP.gp import gp_Pnt, gp_Dir, gp_Lin
from OCP.BRepIntCurveSurface import BRepIntCurveSurface_Inter
part = import_step("metal-case-right.step").wrapped
def zhits(x, y):
    it = BRepIntCurveSurface_Inter(); it.Init(part, gp_Lin(gp_Pnt(x,y,-50), gp_Dir(0,0,1)), 1e-7)
    zs=[]
    while it.More(): zs.append(it.Pnt().Z()); it.Next()   # .Z() is a METHOD — call it
    return sorted(zs)
```

Screw break-out — flatten first, then fraction of the annular wall (bore→envelope)
that is solid (build123d `-`/`&` + volume):

```python
from build123d import import_step, Cylinder, Location, Pos
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from plate_svg import flatten                       # reuses case_model.flatten
pf = flatten(import_step("metal-case-right.step"))  # holes -> perpendicular to +Z
def vol(s):
    g=GProp_GProps(); BRepGProp.VolumeProperties_s(s.wrapped, g); return g.Mass()
env  = Cylinder(radius=1.1, height=6.5).moved(Location(Pos(x, y, zc)))   # Ø2.2 thread env
bore = Cylinder(radius=0.8, height=8.5).moved(Location(Pos(x, y, zc)))   # Ø1.6 pilot bore
tube = env - bore
frac = vol(tube & pf) / vol(tube)      # ~1.0 buried; low = breaks out. (zc = ledge + h/2)
```

## Pitfalls

- **`.Z()` / `.X()` are METHODS on `gp_Pnt`** — `it.Pnt().Z` (no parens) is a bound
  method and `sorted()` throws `'<' not supported between … method and method`. Call them.
- **`solids == 1` is the acceptance, not `IsValid()`.** A topology-only valid check
  passes the open shell that a no-op'd boolean produces. Always run `validate_step.py`.
- **The bottom is TILTED (−5° wedge).** Screw holes are drilled in the wedge-flattened
  frame so their axes are perpendicular to the plate; when measuring hole *depth*, a
  global +Z ray is still fine for the span, but reason about "perpendicular to the
  bottom" in the flattened frame (see `plate_svg.py`/`case_model.py` `flatten`).
- **Sample a recess at several (x,y).** One ray can miss a rounded corner or land on a
  step; confirm the skin over the whole pocket, not one point. `[]` (no hits) = outside
  the part footprint — move inward.
- **Don't eyeball the STL/render for thickness or break-out.** That is exactly what
  hid the 0.6 mm skin and the 44%-buried front screws this loop was built to catch.
- **Build is slow + RAM-hungry — go through `build.py`** (it sets `RLIMIT_AS`); run it
  in the background and read the output file on completion instead of a foreground wait.
