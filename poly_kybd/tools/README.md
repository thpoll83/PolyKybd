# PolyKybd hardware tools

Python tools that treat the KiCad files as data, so variant work (split42,
future layouts) is mechanical, auditable and verifiable instead of manual
copy-and-edit. Most of them need no KiCad installation: they read the
`.kicad_sch`/`.kicad_pcb` text (KiCad 9 format; `extract_key_cluster.py`
needs `pip install kiutils`). Two need KiCad 9 (`kicad_netlist.py`:
`kicad-cli`; `gen_split42_right_pcb.py`: `kicad-cli` and the `pcbnew` Python
module). The install recipe for a cloud container is in
[`render/README.md`](../../render/README.md) → *Setting up a fresh cloud
container*.

## Tools

| Tool | What it does |
|------|--------------|
| `kicad_sch_trace.py <board.kicad_sch>…` | Traces top-level connectivity and prints the **per-key wiring table** (Row / Col / SCLK / SDIN chain / shift-register CS output per `K_*` sheet). This is the electrical contract the firmware (`MATRIX_*_PINS`, `key_display[]`) must match — diff it between boards or against the firmware instead of eyeballing sheets. |
| `gen_split42_right_sch.py` | **Generates** `poly_corne_split42_right.kicad_sch` from the left schematic per the split72 L/R convention (nets walk the board in physical x-order, nothing mirrored): the grid is a straight net-copy of the left and only the thumb row is re-attached to the drawn-outer-left columns (`K_C=Col1`, `K_V=Col2`, `K_B=Col3`, CS unchanged), then **verifies** the result against the table derived from the firmware's `keyboard.json` + `split42.c key_display[]`. Non-zero exit on any mismatch. |
| `kicad_netlist.py <board.kicad_sch> [REF …]` | KiCad's own netlist through `kicad-cli sch export netlist`: the pad nets of every component, sub-sheets included. This is the authoritative answer to "which pad is on which net"; the text tracer above reads the top level only. `gen_split42_right_sch.py` uses it to check the generated schematic (exactly 9 thumb pads differ from the left, plus the 18 pads of the LTR-559 block), and `gen_split42_right_pcb.py` takes every pad's net from it. |
| `gen_split42_right_pcb.py [--no-verify]` | **Generates** `poly_corne_split42_right.kicad_pcb` from the routed LEFT board and the right schematic: outline and mechanical parts mirrored, the golden key cluster (placement and copper) on every key, the functional blocks moved as rigid groups with their copper, every pad's net from KiCad's netlist, GND zones refilled. It does not route between clusters and blocks. It ends with KiCad's DRC on both boards and exits non-zero when the right board has a finding the left board does not have. Run it with the Python that has `pcbnew` (`/usr/bin/python3.12` on Ubuntu 24.04). See *The generated split42 right board* below. |
| `extract_key_cluster.py <board.kicad_pcb> [--json out.json]` | Extracts the **per-key PCB cluster template** (switch + display FPC socket + passives, in switch-local coordinates) and reports which keys deviate from the majority placement. The JSON is the "golden cluster" input for automated placement. |
| `gen_variant_sch.py variants/<v>.yaml [--verify]` | **The universal-generator first cut** (the roadmap's `gen_schematic` stage): generates a top-level `.kicad_sch` per side from a KLE layout (`layouts/*.kle.json`, geometry + matrix position per key) + a variant YAML (`variants/*.yaml`, the complete electrical parameter set). Instantiates the hand-drawn sub-sheets (key cell, ni_buffer2, shift_registers, rp_pico) at KLE-derived positions with deterministic UUIDs and wires them by rule. `--verify` traces the generated file AND the hand-made reference and diffs the canonical contracts (per-key Row/Col/chain/CS/LED-chain + MCU pin map + buffers + SR wiring) — proven to reproduce **both hand-made split72 sides** with zero mismatches. Output in `tools/out/` (gitignored). |

### Variant YAML parameters (what it takes to describe a board)

Measured by reproducing split72 (`variants/split72.yaml`); this is the
parameter set a variant needs on top of its KLE geometry:

- `matrix`: `rows_per_side`, `cols` (KLE rows 0..N-1 = left, N..2N-1 = right).
- `matrix_only`: matrix positions with **no key/display cell** (the encoder
  push buttons — flat symbols on the board, per side).
- `key_cell`: which cell sheet (`SSD1306_TO_SPI` with RGB LED vs `_NO_LED`)
  and its fixed nets (D-C, RESET, GND, VDD, VSUP).
- `mcu`: `col_pins`/`row_pins` **in firmware MATRIX_*_PINS order**, all
  fixed-function GPIOs (LED array start, SR data/clock/latch, SPI raw
  clock/data, split link, I2C, encoder A/B, trackpad INT, D-C, RESET) and the
  power pins.
- `buffer` + `chains`: the display-chain partition per side — which matrix
  cols share which SCLKn/SDINn re-drive buffer (8 cols on 7 chains; the
  doubled pair is a per-side routing choice).
- `shift_registers`: count, control nets (MReset shares the display RESET
  net!) and the per-side `cs_bit` rule — `col_plus_1` (direct) or `col` for
  the split72-right upper-rows convention that firmware `invert_display()`
  compensates with its `c--`.
- `led_chain`: the WS2812 daisy-chain order rule (split72, both sides:
  `[row_asc, col_desc]` — rows top→bottom, decreasing matrix col).
- `reference`: the hand-made schematics `--verify` compares against.

⚠️ `layouts/split72.kle.json` is a copy of
`PolyKybdHost/polyhost/res/polykybd-split72.json` (one geometry source of
truth: firmware layout ↔ host anim geometry ↔ hardware). It carries all 74
matrix positions (72 keys + 2 encoder pushes) and matches the firmware
`keyboard.json` exactly. Keep the copies in sync (`cmp`).

## What the split72 / split42 schematics actually are (measured)

Analysis of the four top-level schematics (2026-07) — the facts the tools
are built on:

- Each board = **flat core symbols** (MCU support, USB-C ×2, ESD, power,
  connectors) + **hierarchical sheets**: one `SSD1306_TO_SPI[_NO_LED]` cell
  per key (switch + keycap OLED, 10-pin interface), `ni_buffer2` per display
  chain, `shift_registers`, `rp_pico`.
- **split72 left ↔ right differ ONLY in net assignment** — zero symbol or
  value differences. **The L/R convention (confirmed 2026-07-29 by review):
  nothing is mirrored electrically.** On both halves the drawn sheets keep
  their left-to-right order and the nets walk the PHYSICAL board in x-order
  — on the right half the drawn-left keys are physically the INNER column
  and get the LOW column nets (right K_B1/K_L1 sit at x=12.25/13.5, the
  inner edge, on Col2; the inner stacked thumb pair B8+B1 shares the
  doubled chain 1, mirroring the left's B7+B8 on chain 7). The split72
  `c--` in `invert_display()` exists only because the extra 8th key (B8)
  claims matrix col 0 on the right and shifts the grid by one.
- **split42 right** (generated here) applies the same convention. With no
  extra key and no stacked pair, the right GRID is a straight net-copy of
  the left and there is **no `c--` equivalent**; only the **thumb row**
  differs: the thumbs physically sit at the inner edge (x=7.5/8.5/9.5,
  matrix [7,0..2]), so they belong to the outer-left columns
  (K_C=Col1/SCLK1, K_V=Col2/SCLK2, K_B=Col3/SCLK3) with CS per sheet
  unchanged (Out1_7/Out2_7/Out3_7). Drawing-wise the thumb sheet blocks
  are MOVED under drawn columns 1–3 (inline with their SDIN/SCLK buses,
  which just extend straight down to them — no cross-sheet routing).
  The committed firmware (`keyboard.json` + `split42.c key_display[]`)
  matches this as-is — the schematic now encodes the previously
  "unverified symmetric guess" by design. (An earlier revision of the
  generator mirrored the columns/chains/CS instead — reviewed as wrong:
  it reproduced the left's local thumb-attachment pattern, which under
  the mirror lands the thumbs on the wrong columns.)
- All four top files share the **same root UUID** (they are copies; KiCad
  tolerates it), and sub-sheets carry per-project instance data for only
  one project — KiCad regenerates the rest on open.

On the PCB side (`poly_corne_split42_left` v1.0, measured with
`extract_key_cluster.py`):

- The per-key cluster is a real template: the display FPC socket sits at
  **(0, −9.49 mm) rot 0 relative to the switch on every key**, including
  the rotated thumbs. Passives share one dominant placement (keys 8–20)
  with small hand-nudges on keys 1–6 — copy-drift, not intent.
- Thumb clusters use ad-hoc refs (`J25/J26/J27` instead of `J7/J14/J21`),
  and **`J18` is missing entirely** (v1.0 defect, see
  `SPLIT42_REDESIGN_NOTES.md` item 3).
- The cluster's COPPER is a template too, on 7 of the 21 keys (see the next
  section). The other 14 differ in details of the routing.

## The generated split42 right board (2026-11-12)

`gen_split42_right_pcb.py` follows the method that the hand-made split72
pair shows. Measured on the split72 left and right boards:

| what | how the right board relates to the left |
|---|---|
| outline, mounting holes, switches | exact mirror, rotation −a |
| mechanical parts (USB, buttons, headers) | exact mirror position, rotation −a |
| ESD array at the link USB | moves with USB2, rotated 180° |
| chip blocks (MCU, regulators, crystal) | rigid translation, same rotation, to about the mirrored place |
| key clusters | the same UNMIRRORED cluster on both halves |

What the run produces today (the log prints these numbers):

- **Golden cluster**: 7 of the 21 left keys (`K_A K_D K_F K_G K_Q K_R K_S`)
  share placement and internal copper to 0.01 mm. `K_A` is the donor; the
  template is 70 tracks and vias. All 21 right keys get it, 1449 copper items
  in total. A right key with matrix position (row, col) sits at the mirrored
  place of the left key (row, 7 − col).
- **`J18`** (missing on the left board) is placed like the other 20 sockets.
- **Four passives** cannot take the golden place because a hole, a
  mechanical part or the outline is there on the mirrored board (`C1_6` and
  `C4_6` in cell `K_5`, `D1_25` in `K_C`, `D1_8` in `K_L2`). Each is moved by
  the smallest step that clears everything, and the copper that led to it is
  left out.
- **Blocks** (found by clustering: MCU with flash, regulators, crystal, both
  USB groups) are placed at the mirrored place and then moved by the smallest
  step that clears the parts already there. The regulator block fits only
  with a quarter turn. A block keeps only complete connections of its copper
  (pad to pad, or pad to a GND via).
- **U26** has pads 1–10 and 5–6 tied in copper (redesign note 1).
- **The LTR-559 block** (`U27 C27 C28 R26 R27 R28`, footprint
  `poly_kb:LTR-559ALS-01` drawn from the land pattern on page 38 of the
  Lite-On datasheet) is a group LEFT OF THE OUTLINE. Its place depends on
  the housing window, so it is not placed.
- **346 connections are open** and are the manual part: rows, columns, the
  SCLK/SDIN chains, CS, RESET and D-C, power.

The check at the end is KiCad's DRC with the schematic parity test, with the
left board as the baseline. The right board passes with 0 shorts, 0 courtyard
overlaps, no clearance below the left board's own 0.150 mm, and the same 12
parity items as the left (footprint names that the v3.3 sheet changed, and
`U9.9`).

### pcbnew traps this found

- ⚠️ **`import pcbnew` works only in the Python KiCad was built for.** On
  Ubuntu 24.04 that is `/usr/bin/python3.12`. Another `python3` on PATH
  fails at import.
- ⚠️ **Remove thousands of items with `board.Delete(item)`, not
  `board.Remove(item)`.** After about 5000 `Remove()` calls the SWIG proxies
  were corrupt, and an unrelated call failed with `'SwigPyObject' object has
  no attribute …`.
- ⚠️ **Fill zones on a board that was loaded again.** A fill done in the
  process that moved the zones used the old zone bounding boxes; DRC then
  reported `actual 0 mm` clearances against the fill. Save, `LoadBoard()`,
  `BuildConnectivity()`, `ZONE_FILLER(board).Fill(board.Zones())`, save.
- ⚠️ **`SaveBoard()` rewrites the `.kicad_pro` beside the board.** The
  generator writes the project file itself afterwards, from the left
  board's.
- **`pcbnew.KIID.SeedGenerator(n)`** makes the UUIDs, and with them the
  whole file, reproducible. Anything that iterates over a `set` of pcbnew
  objects must be sorted first, or two runs differ.
- ⚠️ **A placement check that looks at pads only is not enough.** The first
  placer did, and the board had 33 shorts and courtyard overlaps. The model
  needs courtyards, pads and tracks per layer, and holes.

## Where this is going: KLE + YAML → schematic + placed PCB

The measured facts above mean a variant generator is realistic. Target
pipeline (per variant, per side):

```
layout.kle.json      physical key positions + rotations (KLE, the same
                     format PolyKybdHost's startup_anim_demo.py --emit-geom
                     already consumes — one geometry source of truth for
                     hardware, firmware anim geometry and display maps)
variant.yaml         matrix size + Col/Row net map, chain partition,
                     SR chain order, options: encoder, expansion port,
                     status OLED, LTR-559, per-side net maps
        │
        ▼
gen_schematic  ──►  top-level .kicad_sch: N key-cell sheet instances +
                     option-block sheets, wires/labels generated from the
                     YAML (the hand-drawn cell/option sheets stay the
                     source of graphical truth; refs + UUIDs derived
                     deterministically from the KLE key id so regeneration
                     never orphans the PCB)
        │
        ▼
gen_pcb_place  ──►  place each key's golden cluster (extract_key_cluster
                     JSON) at the KLE position/rotation; option blocks
                     dropped as groups; inter-block routing stays manual
        │
        ▼
verify         ──►  kicad_sch_trace table == firmware-derived table;
                     cluster replay check; (ERC/DRC via kicad-cli where
                     KiCad is available)
```

Design rules learned from the split72→split42 history:

1. **Verify against the firmware, not against another schematic** — the
   firmware `keyboard.json` + `key_display[]` is the contract; both
   split72's `c--` and the split42 thumb guess show how easily schematic
   and firmware conventions drift apart silently.
2. **Deterministic refs/UUIDs keyed on the KLE key id.** Regenerating must
   change only what the layout change touched, or the PCB loses placement
   and routing. (The hand-made boards already violate this: `J25/J26/J27`.)
3. **Keep hand-drawn sheets as the unit of reuse.** The generator writes
   *instances and nets*, never symbol graphics — schematic quality stays
   human.
4. **The side difference is data, not a second design.** left/right = one
   key list, one YAML, a per-side net map. And it is smaller than it looks:
   nets walk the physical board in x-order on BOTH halves (nothing is
   mirrored electrically — see the split72 convention above), so the only
   per-side data is where the physical oddities land (split72: which end
   the stacked thumb pair/doubled chain sits; split42: which columns the
   thumb row joins). `variants/split72.yaml` + `gen_variant_sch.py`
   express exactly this today.
