# split42 (poly_corne) — board redesign notes for the next revision

Collected 2026-07-17. Applies to `poly_corne_split42_left` v1.0 (the only fabbed
layout — **all boards in hand are the LEFT layout**; the right layout exists only in
KiCad). Items 1 and 3 are confirmed defects of v1.0; 2 and 4 are feature additions.

## 1. Link USB-C: hard-wire BOTH plug orientations (v1.0 defect — the split-link bug)

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
its A-row partner), exactly as the (unbuilt) right layout and split72 already do.
Keep U26 for its actual ESD job, but never as a signal path.

**Bench fix for existing v1.0 boards:** reflow/populate U26, or bodge the two pad
pairs above — on BOTH halves.

## 2. Break out I2C0 with a header for the status OLED

The 128×32 status OLED (SSD1306, I2C) runs on `I2C0` = **GP0/GP1** (400 kHz). Add a
proper header/breakout for it on the board so the display connects via a header
instead of whatever ad-hoc wiring v1.0 required.

## 3. Missing keycap-display FPC socket at SW_K_18 (v1.0 defect)

v1.0 left has **21 key sockets but only 20 display FPC sockets**
(`FH34SRJ14S05SH50` / Hirose FH34SRJ-5). The gap is at **`SW_K_18`** — 3rd finger
row, 4th key column (board pos x=130.81 mm, y=93.19 mm; the column below SW_K_4 /
SW_K_11). The reference numbering shows it too: J17 and J19 exist, **J18 was never
placed**. Add J18 (same footprint + placement pattern as the other 20: FPC socket
9.5 mm from the key center) and its display routing.

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
