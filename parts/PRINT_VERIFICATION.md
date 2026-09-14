# Verifying a printed part

Moved out of `CLAUDE.md` 2026-09-14. Verbatim.

## Verifying a printed part

**`parts/diffuser/build_frame.sh` is the whole loop** — regenerate the `.scad` from
the board, export every STL (both frames plus both stacked ones), then verify.
Run it after any edit to `diffuser.scad` or the generator; `--no-4x` skips the
slow stacked exports for a quick iteration, `--check` verifies without exporting.
Doing the steps by hand is where they get missed: a `diffuser.scad` change alters
the stacked pair too, and forgetting them leaves those a revision behind.

`parts/diffuser/check_frame.py` is the verifier it calls: watertight, minimum wall,
left/right symmetry, plate trap, and spacer clearance in both flip orientations.
It exits non-zero on failure. Extend it rather than re-deriving these by hand —
and note it deliberately reports FAIL rather than raising, because a gating script
that crashes on a malformed input tells you nothing about the design.

**Picking a wall-thickness metric is itself the hard part** — three of them were
wrong before the fourth answered the question:

- **Inward-normal ray-cast on the STL** (what `min_wall()` does) is correct where
  two walls are parallel, which covers a plate-like part in z. It is **wrong near
  a corner**: the normal runs oblique to the far face and overestimates — it read
  3.0 mm across a wedge whose real wall was 1.55 mm.
- **Distance to the boundary is not thickness.** Every point near any edge scores
  low, so the "thin area" comes out enormous and meaningless.
- **For in-plane features, rasterise the profile and apply a morphological
  opening** (a disc of radius t/2 must fit). That is the test a print service
  runs, and it is what finally ranked an axis-aligned trim against a 45° one.
- **Report the AREA below a threshold, not the infimum.** Every polygon corner
  tapers to zero thickness at its apex, so the minimum is always ~0 and tells you
  nothing; how *much* material is thin is the number that decides anything.

⚠️ **Identify an orphan mesh by re-exporting the candidate source and comparing,
not by its filename.** Two meshes committed as `case_ins_r2.stl` /
`case_ins_leg_v0.stl` were grouped as a "case insert" on the strength of that
prefix, and separately guessed to be the plate-to-PCB spacer (they are 3.8 mm
thick, the same as `right_spacer()`, so the guess was reasonable). Re-exporting
`legs.scad` settled it in one command: same 32202 facets, same 5263.0 mm³, same
bounding box, 100 % of facets equal at 3 dp -- they are the **tenting legs**
(`connected_8p()`, 8 legs in 4 mirrored pairs). Now `export/legs/legs_r2_8p.stl`.
Float noise between OpenSCAD builds means an exact facet-set compare returns
False, so compare rounded, or on count+volume+bbox.

## Design rules for resin-printed parts

A print service will quote a **0.8 mm minimum / 1.5 mm recommended** wall and
refuse the part if it measures below. Three ways this bit the diffuser frame:

- ⚠️ **A tapered rim beside passing geometry leaves a wafer.** A
  `linear_extrude(scale=)` rim sweeps its radius over its height, so *any*
  neighbouring wall whose edge lands anywhere in that band runs tangent to the
  slope at some height and leaves a near-zero-thickness sliver. On the frame this
  measured **0.043 mm** where a web stem passed a diffuser's bottom cap — an order
  of magnitude thinner than what the vendor complained about, and invisible until
  measured. **Use a vertical rim wherever other geometry passes close**: one
  radius means a neighbour can only clear it or merge with it.
- ⚠️ **`linear_extrude(scale=)` chamfers change ANGLE if you change their
  height.** The inward step is proportional to the *profile*, not the height, so
  thickening a flange by raising the chamfer layer lays the chamfer down (34.9° →
  21.8° when a flange went 1.0 → 1.5 mm). Keep the chamfer layer at its original
  height and put the extra thickness in the straight layer.
- ⚠️ **A minor circular segment ends in a knife edge.** `circle(d)` cut by a chord
  *above* centre runs out to nothing; the last fraction of a millimetre is what a
  vendor measures and rejects. Square the end off — and prefer a **cut that leans
  in plan** over an axis-aligned one: leaning opens the corner against the chord
  from 90° to 135° and spends the cut on the shallow strip, which measured **half
  the sub-0.8 mm area while keeping 4.4% more material**.

**Engraved text always leaves sub-0.8 mm relief** between glyph strokes — no pad
size fixes it, because legible text at any size that fits has strokes closer
together than the threshold. It is **surface relief, not a wall** (the full web
runs continuous underneath). Say so explicitly: exclude the engraving zone from a
wall check and assert the residual material separately, rather than reporting a
flattering number, and tell the vendor the same when they flag it.

