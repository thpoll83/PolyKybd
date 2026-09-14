# KiCad boards — reading them, and what misleads

Moved out of `CLAUDE.md` 2026-09-14. Verbatim.

## KiCad boards (`poly_kybd/`)

The `investigate-kicad-pcb` skill is the entry point for reading a board with Python —
it carries the tool choices and the geometry pitfalls. What follows is board-level fact
that outlives any one investigation.

- ⚠️ **`*.kicad_sch` is authoritative. `poly_kb.net`, `poly_kb.xml` and the KiCad-5
  `.sch` files are NOT.** Those are generated artifacts last touched **2024-02-17**
  and they describe a design **two board revisions old** — they still name the LED as
  `WS2812B-Mini` / `C527089`, which the BOM history shows was replaced by
  `XL-3030RGBC` / `C5349958` between v3 and v3.2. Nothing labels them stale, so they
  read as current: an AI reviewer read one in 2026-08 and filed a confident finding
  that the live LED was the 2024 part. Either regenerate them or delete them; until
  then, treat any answer sourced from them as two revisions out of date.

- ⚠️ **Grep for the PART, not the reference designator.** Symbol *instances* store only
  `reference` and `unit`; `Value`, `Footprint` and `MPN` are **symbol-level**, shared by
  every instance of a hierarchical sheet. So `grep '"U24"' *.kicad_sch` finds nothing
  while `U24` sits happily on the board — it is one of 14 instances of
  `ni_buffer2.kicad_sch` (2 symbols → 28 SOT-353 buffers). This produced a false
  "orphan footprints declared by no schematic" alarm in 2026-08, and it is the **same
  mistake shape** as the `Nexperia595` one already recorded in
  `PolyKybdHost/CLAUDE.md` — searching a designator instead of the thing itself. Once
  was evidently not enough; search by value, `lib_id`, or footprint name.

- **`MPN` here usually holds an LCSC CATALOG ID, not a manufacturer part number — that is
  the convention, not a defect.** 39 of the 46 `MPN` properties in `rp_pico.kicad_sch` are
  `C\d+` values identical to the part's own `LCSC` property; only five carry a real part
  number, and the true manufacturer p/n normally lives in `Value` (e.g. `USB1` is
  `MPN C165948` / `Value TYPE-C-31-M-12`). An AI reviewer flagged this as a fault introduced
  by a PR that had only changed that symbol's `Footprint` (2026-08). Before filing it as a
  finding, check whether the symbol's MPN differs from the merge base at all — and note the
  fix, if one is ever wanted, is a board-wide sweep of ~39 symbols, not a one-part edit.

- **A shared sheet cannot vary a part per board.** All four boards include
  `rp_pico.kicad_sch`, so a `Value`/`Footprint` change to U9 lands on split72 *and*
  split42 whether you want it or not. There is no per-instance override. If a variant
  genuinely needs a different part, extract just that part into its own small
  sub-sheet and fork **that** — forking `rp_pico.kicad_sch` duplicates 45 unrelated
  symbols (46 placed symbols, 14.5k lines) to vary one, and they will drift.

- ⚠️ **The JLC fab exporter builds the BOM from the BOARD's footprint properties, not the
  schematic — and *Update PCB from Schematic* does not refresh them by default.** So a
  correct schematic still exports a wrong BOM: after the U9 flash swap the `LCSC Part #`
  column (the only column JLC orders from) still named the superseded Winbond
  `C5440778` while the footprint and `Value` were the new Boya part — a DFN 4x4 ordered
  onto an LGA-8 land. Sweep board-vs-schematic `MPN`/`LCSC`/`JLC`/`Manufacturer` after
  every export. ⚠️ Also: the **36 hot-swap sockets sit on `F.Cu` in the board but mount
  physically on the BOTTOM**, so every CPL export writes `top` for them and has to be
  flipped by hand; the as-fabricated v3.2 CPL is the reference to diff against. Full
  detail, plus the per-part decisions and the open D2 RoHS row, in
  `poly_kybd/Gerber/PCB/FABRICATION-NOTES.md` — read it before re-exporting.

- **A footprint the boards use but no library provides gets EXTRACTED from the board, not
  hunted upstream.** Three now live in `poly_kb.pretty` this way: the USB-C connector
  (`HRO-TYPE-C-31-M-12-Assembly`, upstream `EnvUSB` absent), `RP2040-QFN-56` (upstream
  `keebio` absent) and `CP_EIA-3216-18_Kemet-A` — the last for a different reason worth
  remembering: **the stock KiCad tantalum footprint has since grown ~0.05 mm**, enough to
  produce clearance violations against routing already on the boards, so the as-built copy
  is kept deliberately and must not be "updated" from the stock library without re-running
  DRC. All three stay on **B.Cu**: every instance of each, on every board, is bottom-mounted,
  so there is no front-side instance to copy and converting would need a front/back mirror
  with nothing to verify against. The mechanics (local x,y but absolute pad angles, which
  instance junk to strip, and comparing pad layers as a set) are in the
  `investigate-kicad-pcb` skill.

- **Land-pattern changes: the target is solder THICKNESS, not solder volume.** When
  extending a pad (e.g. the LED toe, 0.9 → 1.25 mm in 2026-08), **paste must scale
  with the copper** to hold the same ~0.050 mm³ of solder per mm² of pad. Insetting the
  paste to "limit added solder" spreads roughly the same solder over more copper and
  yields a joint **thinner than the one you started with** — the opposite of the
  intent. A long *bare* copper toe with paste held well back is worse still: bare
  copper adjacent to a joint **robs solder** outward and thins the fillet. Two
  corollaries worth keeping:
  - **Tombstoning is not a mechanism on a 4-pad part.** Drawbridging needs a
    two-terminal component able to rotate about one end; four symmetric corner pads
    constrain both axes, and extending all four equally preserves self-centering. The
    real volume risk is float/tilt, which scales with how much you added (+39 % was
    accepted, +111 % was not).
  - **Extend the toe only, never the heel.** Keeping the heel fixed means nothing under
    the package moves, so the paste over the terminal is unchanged and the addition
    lands on bare toe copper where the fillet forms.

- **Measure the re-route cost before picking a pad size.** Rectangle-to-segment against
  every `F.Cu` track and via, own-net excluded, per board. For the 2026-08 LED toe that
  turned "1 mm each?" into a table (1.40 → 21 pads/15 overlaps on the right board;
  1.25 → 19/9) and picked the size. ⚠️ A 0.15 mm threshold is **stricter than the
  board's own rule** — the **negative-clearance overlaps are the real count**, not the
  flagged total. Field-confirmed: 5 flagged on the left board, 0 overlaps, and exactly
  1 trace actually needed moving.

