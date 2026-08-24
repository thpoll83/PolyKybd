---
name: investigate-kicad-pcb
description: >-
  Investigate a PolyKybd KiCad PCB with Python — trace what sits on a net, compare
  two board variants or revisions, hunt a suspected design fault (short/open/routing/
  BOM/passive difference), or run DRC. Use when asked to "check the PCB traces/nets",
  "is this a design fault", "compare split42 vs split72 layout", "what's on
  SERIAL_COM/net X", "did the plane short the line", or during hardware bring-up when
  deciding whether a symptom is firmware vs board. Operates on this repo's KiCad
  files (poly_kybd/*.kicad_pcb). Knows which Python libs work and which mislead, and
  that KiCad 9 / pcbnew is unavailable here. NOT for firmware config (that lives in
  the qmk_firmware repo) or gerber/fab output.
---

# Investigate a KiCad PCB (PolyKybd) with Python

This repo (**thpoll83/PolyKybd**) holds the PolyKybd hardware — KiCad 9 boards under
`poly_kybd/`. This skill is the tool-aware way to answer "what is on this net?", "do
these two boards differ?", and "is the symptom a board fault or firmware?" — without
the KiCad GUI, which is **not installable here**.

The recurring high-value move is a **variant diff**: compare the same net (by NAME)
between a *failing* board and a *known-good* one (e.g. split42 vs split72). Identical
routing exonerates the design and points at build/assembly; a real difference is a
concrete lead.

## Tools — what to reach for (and what to avoid)

| Tool | Use for | Notes |
|------|---------|-------|
| **plain regex over the `.kicad_pcb` text** | nets, pads, track len/width/layer, vias | Most robust. The bundled `kicad_net_diff.py` does exactly this. |
| **kiutils** | structured parse (footprints, pads, positions) | Correct pad world-position needs rotation **sign = −1**; validate against a known-good board. |
| **kicad-tools** (`rjwalters` PyPI, `import kicad_tools as kt`) | pure-Python **DRC** | `IncrementalDRC(pcb, DesignRules(track_w, clearance, via_d, via_drill, hole))` then `.full_check()`; `kt.PCB.load(path)`; `.get_ratsnest()`. `net_count` is an **attribute**, not a method. `DRCReport.load` only *parses* a report — it does not run DRC. |
| **kicad-skip** | alt structured parse | installed; interchangeable with kiutils for most reads. |
| ~~pcbnew / KiCad GUI~~ | — | **UNAVAILABLE** (see Pitfalls). Don't try to install it. |

## Procedure

1. **Locate the boards.** `find . -iname '*.kicad_pcb'`. The real PolyKybd boards are
   `<variant>_left.kicad_pcb` / `<variant>_right.kicad_pcb`; `*_left2`/`*_right2` are
   stubs (no `U26`/`USB2`) and `*_plate_*` are mechanical.
2. **Work by net NAME, not number** (numbers are per-file — see Pitfalls). For a
   quick look: `grep -nE '\(net [0-9]+ "<NAME>"\)' board.kicad_pcb`.
3. **Extract / diff** with the helper (schematic side is a separate check — parse
   `.kicad_sch` for the components on the net + their values):
   ```bash
   python3 .claude/skills/investigate-kicad-pcb/kicad_net_diff.py SERIAL_COM1 SERIAL_COM2 -- \
       poly_kybd/variations/poly_corne/poly_corne_split42_left.kicad_pcb \
       poly_kybd/poly_kybd_split72_left.kicad_pcb
   ```
   It prints, per net: the pads on it (footprint.pad), total track length, segment
   count, via count, widths, and layers — so a variant diff is a glance.
4. **Reason about the electrical path** from the pad list, e.g. COM is
   `U10.6/7 (MCU GP4/GP5) → U26 (shunt ESD array) → USB2 (bridge connector)`, no
   series element (the 22 Ω `R1/R2` are on USB D±, not COM). Same-length, same-pad,
   same-layer between variants ⇒ design equivalent.
5. **DRC** (shorts/clearance) via kicad-tools when a short is suspected — do **not**
   hand-roll a zone-overlap check (see Pitfalls).
6. **Report** what's identical vs different, and state the conclusion at the
   confidence the files support — "design equivalent to the known-good board, so the
   fault is not in the layout" is a valid, valuable result. Do **not** upgrade a
   layout delta into a claimed physical mechanism (joint/cap) the files can't show.

## Pitfalls (the expensive lessons)

- **Net numbers are PER-FILE.** `SERIAL_COM1` is net **226** on `split42_left` but
  net **400** on `split42_right` and `split72`. Resolve name→number **in each file**
  (the helper does). Reusing a number across files silently analyzes the *wrong* net
  (once made `split42_right` COM look like it hung off a stray cap + connector).
- **Validate every custom geometry check against a KNOWN-GOOD board first.** A
  hand-rolled pad-position check falsely reported "USB2 unrouted (15.9 mm no copper)"
  from a **rotation-sign bug** — caught only by running it on the *working* split72
  and seeing the identical bogus number. If your check flags the good board too, the
  check is wrong, not the board.
- **shapely+kiutils zone-short checks are UNRELIABLE — but the fault is KIUTILS, not
  hand-rolling.** kiutils drops zone-fill clearance holes, so a pad inside a plane's
  *clearance pocket* reads as overlapping copper — 289/1230 known-good pads flagged as
  GND-shorted. ⚠️ **This does NOT mean "never hand-roll a zone check".** Parse
  `(filled_polygon (layer "…") (pts …))` **straight out of the s-expression** and the
  clearance holes survive: KiCad makes each fill simply-connected with cut lines, so a
  hole's boundary is already part of the same point list, and a plain
  point-to-segment distance measures it correctly. A whole 2026-08 zone investigation
  ran that way and every number held up — 744 of 746 foreign vias at *exactly* the
  zone's 0.200 mm local clearance, cross-checked against KiCad's own DRC report.
  Three traps to respect when you do:
  - **Measure BOTH tails.** A via with *no* knockout shows a **large** distance to the
    nearest fill edge, not a small one. Only checking the minimum misses it entirely
    (cost several rounds before the maximum was looked at).
  - **Pair the rule to the item.** Plated `thru_hole` is copper-to-copper
    (`min_clearance`, 0.15 here); `np_thru_hole` is hole-to-copper
    (`min_hole_clearance`, 0.13) and its "pad" is the drill, not the size. Applying
    0.15 to both inflated a real count of 10 into 123.
  - **Check `filled_areas_thickness`.** `no` means the stored polygons *are* the copper
    edge. If it is absent (legacy files), polygons are stroked by `min_thickness` and
    every measured gap needs correcting by half that.
- ⚠️ **If the SAVED FILL is correct and DRC still reports `actual 0,0000 mm`, check the
  zone OUTLINE for self-intersection — check it FIRST, before any of the fill settings.**
  A self-intersecting outline has an **ambiguous interior** (a spliced-in excursion has
  winding number 2, so even-odd and non-zero rules disagree), and KiCad's filler and its
  DRC resolve that ambiguity **differently** — the filler writes correct polygons while
  DRC measures against a different shape. 2026-08 cost a very long session to this: 88
  violations, every named via measuring a clean **+0.2005 mm** in the file against DRC's
  0.0000, root-caused to one pour whose outline stored vertices 4 and 19 as the identical
  point with a keyhole excursion between them. Replacing it with a plain rectangle cleared
  all 88.
  ```python
  # duplicate vertices + self-intersecting edge pairs, per zone
  dupes = [(a,b) for a in range(n) for b in range(a+1,n) if pts[a]==pts[b]]
  ```
  ⚠️ **The failures need not be near the malformed corner** — here the keyhole was at
  y 56–68 and every violation at y 89–97, which is exactly why "what is special about
  that row?" was the wrong question for hours. And two symptoms actively mislead:
  assigning the zone **a different net or no net "fixes" it** (it only changes which
  regions fill, so the ambiguity stops mattering — it is not a clue about nets), and the
  errors **look confined to one row** when nothing about that row is unusual.
  ⚠️ Tested and **not** the cause, so do not spend time there: `island_removal_mode` /
  `island_area_min` (all settings), and zone priority.
- ⚠️ **KiCad does NOT persist DRC markers to disk.** There is no marker data in a
  `.kicad_pcb` — zero `(marker` tokens, and `drc_exclusions` lives in the `.kicad_pro`.
  You cannot read someone's markers from a commit; a session was spent trying. Ask for
  **DRC dialog → Save Report to File…** and have the `.rpt` committed. That report is
  what located the 2026-08 zone problem after every inference-based theory had failed —
  its `actual 0,0000 mm` lines disagreed with the saved fill, which is what proved DRC
  was refilling in memory rather than checking the file.
- **KiCad 9 / pcbnew is UNAVAILABLE.** `add-apt-repository` breaks (`ModuleNotFoundError:
  apt_pkg`), the KiCad PPA is proxy-blocked, and the distro **KiCad 7 cannot open v9
  `.kicad_pcb`** (or run its DRC). Don't burn time installing it — the Python-only
  path above is the whole toolkit.
- **A layout diff is a lead, not a verdict.** Identical files exonerate the design;
  a delta (trace layer, GND-pour clearance) is worth flagging but is rarely, on its
  own, proof of a fault. Keep hardware-mechanism claims (joints, coupling) as
  hypotheses until a bench measurement confirms them.
