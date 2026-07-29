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
> | 1 | valid, **relocated** — two pad pairs at U26 are not tied together; the connector is fine | corrected by the board author; see that section |
> | 2 | valid | `I2C_SDA`/`I2C_SCL` reach only `U10` (RP2040) and the pull-ups `R3`/`R4` — no header, no connector |
> | 3 | **verified geometrically** | see the section |
> | 4 | valid | no LTR-559 footprint on the board |

## 0. Design the split42 RIGHT board (currently a split72 stub)

`poly_corne_split42_right.kicad_pcb` still IS split72-right verbatim. When deriving
the real right board, apply items 1–4 from the start — especially item 1, since the
orphaned link pads were evidently introduced during the left board's rework of the
(correct) split72 layout, i.e. exactly the step about to be repeated for the right.

## 1. ESD array U26: two pairs of pads are not tied together (v1.0 defect — the split-link bug)

> **Corrected 2026-07-29 by the board author**, twice — get this right before the
> redesign, because the earlier readings put the defect in the wrong place.
>
> **The rule: two pairs of pads must ALWAYS be connected.** The USB-C connector
> itself is **fine** — footprint and wiring are correct. The break is at **U26**
> (TPD4E05U06DQA ESD array), where those two pairs are not joined.

Each link signal reaches **four** U26 pads (verified from the netlist, and identical
on split72-left):

| net | MCU | U26 pads | connector |
|---|---|---|---|
| `SERIAL_COM1` | `U10.6` | 1, 4, 7, 10 | `USB2.6` (A-row), `USB2.8` (B-row) |
| `SERIAL_COM2` | `U10.7` | 2, 5, 6, 9 | `USB2.5` (B-row), `USB2.7` (A-row) |

Four pads per signal is two flow-through channels — one per plug orientation. Both
have to be connected for the signal to survive a flipped plug.

**On v1.0-left only the INNER two pairs are connected.** The pads sit in two columns
0.77 mm apart at 0.5 mm pitch, so the facing pairs and their distance from the package
centre (pads 3/8, GND — not on the COM nets) are:

| y (mm) | left | right | pair | from centre | state |
|---|---|---|---|---|---|
| 105.58 | 1 | 10 | **1 ↔ 10** | 1.00 | ❌ **not connected** |
| 105.08 | 2 | 9 | 2 ↔ 9 | 0.50 | ✅ connected |
| 104.58 | *3* | *8* | — | 0 | GND, not on a COM net |
| 104.08 | 4 | 7 | 4 ↔ 7 | 0.50 | ✅ connected |
| 103.58 | 5 | 6 | **5 ↔ 6** | 1.00 | ❌ **not connected** |

That is exactly one missing pair per signal — `1↔10` on `SERIAL_COM1`, `5↔6` on
`SERIAL_COM2` — hence **two pairs**. (The original version of this note named the same
two pairs as "U26's internal flow-through metal": right pads, wrong conclusion. They
are not a substitute for board copper.)

**Consequence (unchanged, and matches the bench):** the flipped-orientation path never
completes, so the link comes up in exactly one plug orientation. Power is unaffected
(VBUS/GND are hard-wired), so both halves always powered normally. With both halves
being left boards — no right board was ever fabbed — each cable end carries that same
coin flip, so only **1 of 4** plug-orientation combinations links. This is the root
cause of the whole "split link dead / transport_fail=100%" saga; full record in
`qmk_firmware/keyboards/polykybd/split42/SPLIT42_LINK_STATUS.md`.

**Fix in the redesign:** connect **`1↔10` and `5↔6`** at U26 in board copper, matching
the inner pairs, so neither orientation depends on the chip being present or
well-soldered. Apply it to the right
board from the start (item 0) — the fault was evidently introduced when the left board
was reworked from the correct split72 layout, which is exactly the step about to be
repeated.

⚠️ **Confirm on the bench before cutting the redesign, not from the `.kicad_pcb`.** The
pairing above is the board author's account plus the footprint geometry; two
independent geometric checks *of the copper* were written against the layout file and
both were discarded for reporting the same fault on the known-good split72 board (the
trap documented in `.claude/skills/investigate-kicad-pcb`). Use the B.Cu gerber or a
meter. Evidence renders:
[`images/split42_left_gerber_4layers.png`](../../../images/split42_left_gerber_4layers.png),
[`images/split42_link_copper_comparison.png`](../../../images/split42_link_copper_comparison.png).

**Bench fix for existing v1.0 boards:** bodge `U26.1↔U26.10` and `U26.5↔U26.6` — on BOTH halves.

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
