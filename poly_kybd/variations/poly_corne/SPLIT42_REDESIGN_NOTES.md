# split42 (poly_corne) — board redesign notes for the next revision

Collected 2026-07-17. Applies to `poly_corne_split42_left` v1.0 (the only fabbed
layout — **all boards in hand are the LEFT layout**). Note:
`poly_corne_split42_right.kicad_pcb` is a **byte-identical copy of
`poly_kybd_split72_right.kicad_pcb`** (an untouched stub — the split42 right side has
not been designed yet; that design work is item 0 below). Items 1 and 3 are confirmed
defects of v1.0-left; 2 and 4 are feature additions.

> **Re-validated 2026-07-29 against the board files on `master`.** All five points
> still stand — `git log` shows the `poly_corne` boards untouched since these notes
> were written, so nothing here has been addressed in the interim. What each claim
> now rests on:
>
> | item | status | evidence |
> |---|---|---|
> | right board is a split72 stub | **verified** | `cmp` says byte-identical to `poly_kybd_split72_right.kicad_pcb` |
> | 0 | valid | follows from the above |
> | 1 | valid, but **relocated** — defect is at U26, not the connector | corrected by the board author; see that section |
> | 2 | valid | `I2C_SDA`/`I2C_SCL` reach only `U10` (RP2040) and the pull-ups `R3`/`R4` — no header, no connector |
> | 3 | **verified geometrically** | see the section |
> | 4 | valid | no LTR-559 footprint on the board |

## 0. Design the split42 RIGHT board (currently a split72 stub)

`poly_corne_split42_right.kicad_pcb` still IS split72-right verbatim. When deriving
the real right board, apply items 1–4 from the start — especially item 1, since the
orphaned link pads were evidently introduced during the left board's rework of the
(correct) split72 layout, i.e. exactly the step about to be repeated for the right.

## 1. ESD array U26: two unconnected traces (v1.0 defect — the split-link bug)

> **CORRECTED 2026-07-29 by the board author.** The defect is at **U26, the ESD
> protection chip: two of its traces are not connected.** The **USB-C connector
> itself is fine** — its footprint and wiring are correct.
>
> Everything below this note was written from the opposite reading (that the *`USB2`
> pads* were copper-orphaned and the fix was to tie the A-row and B-row pads together,
> keeping U26 out of the signal path). **That framing is wrong and its prescribed fix
> should not be actioned as written** — it would add traces at the connector to work
> around a break that is actually at U26. The observable symptom and its consequences
> are unaffected: two of the four flow-through paths do not complete, so the link comes
> up in only one plug orientation, and with both halves being left boards that is 1 of
> 4 plug combinations.
>
> Still to pin down before the redesign: **which two** U26 traces are open, and hence
> whether the fix is completing them in copper or re-routing the channel. ⚠️ Do not try
> to settle this from the `.kicad_pcb` — two independent geometric checks were written
> for it and both were discarded for reporting the same fault on the known-good
> split72 board (the trap documented in `.claude/skills/investigate-kicad-pcb`). Use
> the B.Cu gerber or a meter.

### Superseded framing (kept for context — see the correction above)

On the v1.0 **left** layout the flipped-orientation data pads of the link USB-C
(`USB2` pad 5 = B7/COM2, pad 8 = B6/COM1) are **copper-orphaned**: they reach U26
(TPD4E05U06DQA ESD array) but nothing continues on the other side — the only bridge
to the RP2040 is U26's *internal* flow-through metal (pads 1↔10, 5↔6). B.Cu shows it
directly: 4 data stubs enter U26, only 2 leave. If U26 is absent or has a cold joint,
the link works in exactly ONE plug orientation (power flows either way — VBUS/GND are
all hard-wired). With both halves being left boards, both cable ends carry that coin
flip → only 1 of 4 plug-orientation combos links up. This is the root cause of the
entire split42 "split link dead / transport_fail=100%" saga (full record:
`qmk_firmware/keyboards/polykybd/split42/SPLIT42_LINK_STATUS.md`).

**Fix in the redesign:** route both orientation pads to the MCU in board copper —
`USB2.8 → USB2.6` and `USB2.5 → USB2.7` (two short traces joining each B-row pad to
its A-row partner), exactly as split72 already does. Keep U26 for its actual ESD
job, but never as a signal path.

**Bench fix for existing v1.0 boards:** reflow/populate U26, or bodge the two pad
pairs above — on BOTH halves.

> ⚠️ **This item rests on the gerbers and the bench, NOT on the `.kicad_pcb`.** A
> re-check on 2026-07-29 found the *netlist* identical to split72-left: on both
> boards `USB2.5/.7` are one net (`SERIAL_COM2`) and `USB2.6/.8` another
> (`SERIAL_COM1`), each also touching `U10` and four `U26` pads. So the schematic
> intent is the same and the defect can only live in the copper. Aggregate copper is
> near-equivalent too (`SERIAL_COM1` 48.09mm/24 seg vs split72's 48.93mm/29 seg; the
> one real delta is that split42's COM1 has **0 vias and is B.Cu-only** where
> split72's has 2 vias across B.Cu+In1.Cu).
>
> A pad-to-pad copper-connectivity check was attempted and **discarded**: it reported
> "not connected" for the *known-good* split72 board as well, which per
> `.claude/skills/investigate-kicad-pcb` means the check is wrong, not the board.
> Do not treat that as evidence either way.
>
> The claim stands on what actually produced it — the B.Cu gerber (4 data stubs into
> U26, only 2 out) and the reproducible bench behaviour (1 of 4 plug-orientation
> combos links, across 5 boards). Both renders are in this repo:
> [`images/split42_left_gerber_4layers.png`](../../../images/split42_left_gerber_4layers.png)
> and [`images/split42_link_copper_comparison.png`](../../../images/split42_link_copper_comparison.png).
> **To close this out properly, verify on the fabbed gerbers or with a meter — not
> from the layout file.**

## 2. Break out I2C0 with a header for the status OLED

The 128×32 status OLED (SSD1306, I2C) runs on `I2C0` = **GP0/GP1** (400 kHz). Add a
proper header/breakout for it on the board so the display connects via a header
instead of whatever ad-hoc wiring v1.0 required.

## 3. Missing keycap-display FPC socket at SW_K_18 (v1.0 defect)

v1.0 left has **21 key sockets but only 20 display FPC sockets**
(`FH34SRJ14S05SH50` / Hirose FH34SRJ-5). The gap is at **`SW_K_18`** — 3rd finger
row, 4th key column (board pos x=130.81 mm, y=93.19 mm; the column below SW_K_4 /
SW_K_11). Add J18 (same footprint + placement pattern as the other 20: FPC socket
9.5 mm from the key center) and its display routing.

> **Verified geometrically 2026-07-29** — the board has 21 `SW_K_*` and 20 `FH34SRJ`
> sockets, and measuring each key centre to its nearest socket identifies the orphan
> without relying on reference numbers: every key but one has a socket at exactly
> **9.49 mm**, while `SW_K_18` (130.81, 93.19) has none nearer than **17.20 mm**
> (J25, which belongs to the thumb cluster). That confirms both the count and *which*
> key is affected.
>
> ⚠️ The original argument here — "J17 and J19 exist, so J18 was never placed" — is
> **not sound on its own**: J7, J14 and J21–J24 are also unplaced, and J25/J26/J27 are
> ordinary FPC sockets, so the reference numbering is simply sparse by design. The
> conclusion was right; the reasoning wasn't. Use the distance check above.

## 4. LTR-559 light+proximity sensor as a permanent part

The Pimoroni LTR-559 (ambient light + proximity, I2C addr `0x23`) has proven its
worth on split72 (auto-brightness + proximity wake) — place it permanently on the
split42 board. Notes:

- It lives on **I2C0** — same bus as the status OLED (item 2), no extra pins. No
  address conflict (SSD1306 is 0x3C/0x3D).
- Firmware support already exists and is **side-agnostic** (`base/ltr559.c`; the
  master pulls slave-side readings over `USER_SYNC_SLAVE_DATA`). It is a clean no-op
  when the part is absent (bounded probe retries), so it can be enabled
  unconditionally: once the hardware exists, add `-DPOLYKYBD_LTR559
  -DPOLYKYBD_LTR559_DRIVE` + `base/ltr559.c` to `split42/rules.mk` (mirroring
  split72).
- Mind the optics: the sensor needs a window/hole in the housing, and the proximity
  resting baseline is housing-dependent (split72 measured ~129 open bench vs ~325
  mounted) — re-check `LTR559_NEAR_THRESHOLD` for the split42 enclosure.
