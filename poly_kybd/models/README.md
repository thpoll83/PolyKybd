# 3D models for the KiCad 3D view

Referenced from the split72 boards as `${KIPRJMOD}/models/<file>`.

| File | What | Source |
|------|------|--------|
| `keycap_display.wrl` | the 72x40 keycap OLED | PolyKybd |
| `keycap_flex_cable.wrl` | its flex cable at full length: display, down through plate and PCB slot, into the bottom-side FH34 connector | `flex_cable.py` |
| `keycap_display_cable.wrl` | the old, short cable (ended 5.7 mm above the PCB); no longer referenced | PolyKybd |
| `keycap_stem_r7.wrl`, `keycap_stem_r7_1u25.wrl` | keycap stem, 1U and 1.25U | PolyKybd |
| `outercap1u.wrl`, `outercap1u25.wrl` | clear outer keycap, 1U and 1.25U | PolyKybd |
| `display_w_holder.wrl`, `right_side_model.wrl` | display holder, right case | PolyKybd |
| `DHVQFN-16-1EP_2.5x3.5mm_P0.5mm_EP1x2mm.step` | 74HC595BQ shift register; KiCad's footprint names this file but the KiCad 9 3D library lacks it | `gen_models.py` |
| `FH34SRJ-14S-0.5SH_50_.step` | Hirose FH34SRJ 14-pos FFC connector (one per key display) | `gen_models.py` |
| `FH34SRJ-12S-0.5SH_50_.step` | the same in 12 positions, for J37 (the status display's connector) | `gen_models.py` |
| `screw_M3_pan_hex_2mm.step` | M3x10 pan head, 2 mm hex socket (1.0 mm deep, 118° drill-point floor, 0.15 mm mouth chamfer), 1.5 mm flat head with a rounded edge; on the 4 outer mounting holes per half (H2, H3, H6, H9), head on the plate top | `gen_models.py` |
| `case_polykybd_split72_{left,right}_r7.wrl` | the FDM case r7, on H5 | `stl_to_wrl.py` from `parts/export/case/case_polykybd_split72_{left,right}_r7.stl` |
| `plate_split72_{left,right}.wrz` | switch plate, flipped (Rosetta artwork up), on SW_K_1 at z 4.2, rotate 0 180 0 | `gen_plates.py` from the plate PCBs (see below) |
| `status_display_holder.wrl` | status OLED holder with the display, on J39 | `gen_inserts.py` from `display_holder_r1.stl` |
| `cover_insert.wrl` | lid for the expansion port, both halves, on J39 | `gen_inserts.py` from `cover_insert_r3_10p.stl` |
| `diffuser_frame_split72_{left,right}.wrl` | one-piece LED diffuser frame (36 diffusers and the web under the plate), attached like the plate: on SW_K_1 at z 4.2, rotate 0 180 0, scale 0.3937 | `gen_inserts.py` from `parts/export/diffuser/diffuser_frame_{left,right}.stl` |
| `SW_Cherry_MX_PCB.wrl`, `SW_Hotswap_Kailh.wrl` | MX switch and Kailh hotswap socket | [keyswitch-kicad-library](https://github.com/perigoso/keyswitch-kicad-library) release v2.0, `3dmodels/3d-library.3dshapes/`, CC-BY-SA 4.0 |

The two switch models used to be referenced as
`${KIPRJMOD}/ThirdParty/keyswitch-kicad-library/modules/packages3d/...`. That
folder was never committed, so they are vendored here.

Each key footprint (`SW_K_*`, `poly_kb:Kailh_socket_MX_Indicators`) carries six
models: switch, socket, stem, display, cable, outer cap. The 1.25U keys are the
outer column and three thumb keys on each half, mirrored between the halves:

- left: `SW_K_1, 8, 15, 22, 29, 34, 36`
- right: `SW_K_7, 14, 21, 28, 29, 30, 32`

Stock parts point at `${KICAD9_3DMODEL_DIR}/....step`, because the KiCad 9
library ships STEP only.

`gen_models.py` (build123d 0.12.0) writes the generated STEP files: the
DHVQFN-16, the FH34SRJ in 14 and 12 positions (`fh34srj(n)`) and the screw. They are
drawn in their footprint's frame, so the boards use zero offset and rotation.
They are approximations from the footprint outline, not vendor models.

### Stock models on custom footprints

Picked by fitting the stock footprint's pads onto ours, after undoing KiCad's
back-side flip (it negates pad Y in the file):

| Footprint | Model | Rotation | Pad fit |
|-----------|-------|----------|---------|
| `poly_kb:BY25Q64ES-LGA8-2x3` | `Package_SON:Winbond_USON-8-1EP_3x2mm...` | 270 | 0.07 mm |
| `poly_kb:Nexperia 74HC595BQ DHVQFN16` | `models/DHVQFN-16-...` | 0 | 0.12 mm |
| `poly_kb:USON-10` | `Package_SON:USON-10_2.5x1.0mm_P0.5mm` | 0 | 0.005 mm |
| `poly_kb:SMMS0420-2R2M` | `Inductor_SMD:L_Changjiang_FXL0420` | 0 | exact |
| `poly_kb:XL-3030RGBC-WS2812B` | `LED_SMD:LED_RGB_Wuerth-PLCC4_3.2x2.8mm` | 180 | stand-in, 3.2x2.8 for 3.0x3.0 |

### The case

The case rides on mounting hole H5 of each board, as the old `right_side_model.wrl`
did. Its STL frame is the board outline offset by 1.65 mm (wall + clearance), with
the PCB underside at z = 11.5 mm (floor 2 + ledge 9.5), so the offset is the
Edge.Cuts bbox centre minus the case bbox centre, and z = -(1.6062 + 11.5).
**Re-run `stl_to_wrl.py` after re-exporting the case STL.** KiCad does not read
STL, and its VRML2 parser drops a file silently if the layout differs from
`stl_to_wrl.py`'s output (no `creaseAngle`, one node per line).

Back-side footprints (all holes on the right board, H4 on the left) are flipped
by KiCad as 180 deg about X, after the footprint's own 180 deg rotation:

| Model on a B.Cu, 180 deg footprint | rotate | offset |
|---|---|---|
| screw | 180 0 0 | 0 0 -6.6062 (head on the plate top) |
| case (right) | 0 180 0 | 95.727 -131.7882 11.5 |

### Plate, status display, lid

`gen_plates.py` exports each plate PCB as gzipped VRML from a repaired temp
copy; the plate PCBs themselves are untouched. Each plate goes on the half its
name says, **flipped**: the Rosetta artwork is on the plate's B.SilkS and faces
up, the `< LEFT SIDE >` / `< RIGHT SIDE >` labels on F.SilkS face the switch
PCB. Unflipped, each plate also fits the other half (the halves are mirror
images), so outline matching alone cannot tell the two apart.

Both plate outlines have 36 zero-length Edge.Cuts segments, and the expansion-port
cut-out misses closing by 0.01 mm (58.1356 vs 58.1456 on plate_left, 220.4616 vs
220.4716 on plate_right). On plate_left KiCad rejects the whole outline
(DRC: not a closed shape, self-intersecting) and exports a bounding rectangle.

The inserts sit in the plate's cut-outs, flush with its top (5.0 mm above the
PCB top):

| Model | anchor | offset | rotate |
|---|---|---|---|
| status display, left | J39 | 13.438 30.877 2.5 | 0 0 180 |
| status display, right | J39 | 13.558 30.877 2.5 | 0 0 180 |
| cover lid, left | J39 | -4.422 -23.378 4.6 | 0 0 20 |
| cover lid, right | J39 | 4.4226 -23.378 4.6 | 0 0 -20 |

The lid angle was checked by eye: KiCad applies the model's z rotation
clockwise as seen from above, so +20 is the left cut-out's clockwise tilt.

The plate is an aluminium PCB: `gen_plates.py` recolours the export's mask and
board body to grey aluminium (0.58), dark enough that the white artwork reads.

Still without a model: `poly_kb:PolyJog` (rotary encoder option).
