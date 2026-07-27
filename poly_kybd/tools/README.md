# PolyKybd hardware tools

Python tools that treat the KiCad files as data, so variant work (split42,
future layouts) is mechanical, auditable and verifiable instead of manual
copy-and-edit. None of them need a KiCad installation — they operate on the
`.kicad_sch`/`.kicad_pcb` text (KiCad 9 format; `extract_key_cluster.py`
needs `pip install kiutils`).

## Tools

| Tool | What it does |
|------|--------------|
| `kicad_sch_trace.py <board.kicad_sch>…` | Traces top-level connectivity and prints the **per-key wiring table** (Row / Col / SCLK / SDIN chain / shift-register CS output per `K_*` sheet). This is the electrical contract the firmware (`MATRIX_*_PINS`, `key_display[]`) must match — diff it between boards or against the firmware instead of eyeballing sheets. |
| `gen_split42_right_sch.py` | **Generates** `poly_corne_split42_right.kicad_sch` from the left schematic by applying the right-half mirror (key-side `Col c → Col 7−c`, chain `n → 7−n`, per-register CS bit mirror + the thumb `Out1_7 ↔ Out3_7` pair), then **verifies** the result against the table derived from the firmware's `keyboard.json` + `split42.c key_display[]`. Non-zero exit on any mismatch. |
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
  value differences. The right side shifts the column↔chain assignment by
  one (with the doubled chain moving from cols 7+8 to cols 1+2) and rotates
  the bottom-row CS outputs. That mismatch between schematic pattern and
  matrix numbering is why `split72.c invert_display()` needs its `c--`
  shift on the right upper rows.
- **split42 right** (generated here) instead mirrors the CS wiring so the
  shared firmware `key_display[]` indexes directly — **no `c--`
  equivalent**, matching the committed `split42.c`.
- All four top files share the **same root UUID** (they are copies; KiCad
  tolerates it), and sub-sheets carry per-project instance data for only
  one project — KiCad regenerates the rest on open.
- The right-thumb CS order (`Out1_7/Out2_7/Out3_7` at matrix cols 0/1/2) is
  the firmware's **unverified symmetric guess** (`split42/split42.c`) —
  schematic and firmware agree by construction; if bench bring-up flips the
  firmware order, flip the pair swap in `gen_split42_right_sch.py` too.

On the PCB side (`poly_corne_split42_left` v1.0, measured with
`extract_key_cluster.py`):

- The per-key cluster is a real template: the display FPC socket sits at
  **(0, −9.49 mm) rot 0 relative to the switch on every key**, including
  the rotated thumbs. Passives share one dominant placement (keys 8–20)
  with small hand-nudges on keys 1–6 — copy-drift, not intent.
- Thumb clusters use ad-hoc refs (`J25/J26/J27` instead of `J7/J14/J21`),
  and **`J18` is missing entirely** (v1.0 defect, see
  `SPLIT42_REDESIGN_NOTES.md` item 3).

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
                     status OLED, LTR-559, per-side mirror rules
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
4. **The mirror is data, not a second design.** left/right = one key list,
   one YAML, a `side: right` flag flipping the Col/chain/CS assignment —
   exactly what `gen_split42_right_sch.py` does today as a special case.
