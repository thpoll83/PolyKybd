# Fabrication export notes (PolyKybd split72)

Durable record of the things that keep being re-derived when regenerating gerbers,
BOM and CPL. Read this **before** re-exporting, and update it when a decision changes.

---

## ⚠️ 1. The fab exporter reads the BOARD, not the schematic

The JLC fabrication-toolkit plugin builds the BOM from **footprint properties on the
`.kicad_pcb`**. A correct schematic is *not* enough: *Update PCB from Schematic* changes
the footprint association and `Value` but leaves `MPN` / `LCSC` / `JLC` / `Manufacturer`
alone unless field updating is explicitly enabled.

**This has already shipped a wrong BOM once.** After the U9 flash swap the export read:

```
U9,BY25Q64ES-LGA8-2x3,1,BY25Q64ESCIG(R),C5440778
                                        ^^^^^^^^ Winbond -- the OLD part
```

Footprint and Value were right, and the `LCSC Part #` column — **the only column JLC
orders from** — still named the superseded Winbond `W25Q64JVXGIM` (DFN 4×4), which would
have been placed onto an LGA-8 land. Guaranteed assembly failure, invisible in the
footprint and invisible on the canvas.

**Check after every export**, comparing board fields against the schematic:

```python
# board footprint properties vs schematic symbol properties, per reference
# fields that matter: MPN, LCSC, JLC, Manufacturer
```

The 2026-08-24 sweep found 4 divergences out of 112 matched parts — see §3.

⚠️ Note the board's U9 fields were stale *independently* of this change: v3.2 was
fabricated with `C2940195` / `W25Q64JVXGIQ`, while the board file carried `C5440778`.
So "the board field" has never been a reliable record of what was ordered.

---

## ⚠️ 2. The 36 hot-swap sockets are BOTTOM mounted — every CPL export needs a manual flip

`SW_K_1` … `SW_K_36` (`poly_kb:Kailh_socket_MX_Indicators`) are placed on **`F.Cu`** in
the board file, but the sockets are physically mounted on the **bottom**. So a fresh
export writes `top` for all 36 and it must be corrected to `bottom` by hand before the
CPL goes to the fab.

This is not a one-off — it is required on **every** re-export, and it has been done
manually every time. The 2026-08-24 v3.3 export shipped with `top` still in place until
it was caught.

**The check:** the v3.2 CPL is the as-fabricated reference. A correct export agrees with
it on every common reference:

```bash
# expect: 0 side disagreements, 72 ',top' rows in both
```

The root cause is the board layer, so the permanent fix would be flipping those 36
footprints to `B.Cu` — deliberately not done, since that moves pads/mask/paste layers on
a working, fabricated design. The manual CPL fix is the cheaper risk.

---

## 3. Part decisions (2026-08-24)

| Ref | Decision | Availability | RoHS evidence |
|---|---|---|---|
| **U9** | **BOYAMICRO `BY25Q64ESCIG(R)` / `C50176394`** — everything points at the Boya part: schematic, board fields, and the v3.3 export | quoted $0.6012 × 400, 7 business days | ✅ `RoHS/2006180000_BOYAMICRO-BY25Q64ESCIG-R_C50176394.pdf` |
| **C3, C8** | **Samsung `CL05C270JB5NNNC` / `C86287`** (was FH `C1557`) | ✅ 69,800 in stock at LCSC | ✅ already filed — the Samsung series list in `RoHS/2304140030_Samsung-Electro-Mechanics-...C52923.pdf` includes `CL05C270 J B 5NNN`, and it is already in `PolyKybd-RoHS-Appendix.pdf` |
| **D2** | Guangdong Hottech `1N5819WS` / `C191023` — ⚠️ **RoHS evidence is OPEN**, see below | ✅ 5,636,800 in stock, SOD-323, not discontinued | ⚠️ **incomplete** |

⚠️ **C3/C8 value string reads `27pF 0402 16V` but both the old and new parts are 50V**
(`0402CG270J500NT` and `CL05C270JB5NNNC`). The label is inaccurate, the parts are not
under-rated. Left alone to avoid churn; fix it if the value strings are ever tidied.

### D2 — the last open RoHS row

`RoHS/schematics/parts.csv` records D2 as **`x Email sent`**, and it is the **only
populated part still without evidence** (the other open rows are test points, mounting
holes, headers and the DNP `SW1`). Closing it closes the appendix.

The problem is package coverage: `RoHS/ROHS3HOTTECH.pdf` is a genuine May-2020 BST test
report for Guangdong Hottech against RoHS 2 (EU) 2015/863, but its sample list is

> SOT-23, 323, 523, 723, 363, 223, 23-5, 23-6, 89, TO-92, 92L, 126, 252, 251, 220,
> SOP8, TSSOP8, SOP14, DIP8, DIP14, **SOD-123**

— **SOD-123, not SOD-323**, and the report states its results "refer only to the
sample(s) tested". D2 is SOD-323. (The `323` in that list is SOT-323, a different
package.)

Two ways to close it, undecided:

1. **Chase Hottech** for a declaration that names SOD-323 — this is the email that was
   sent and never came back.
2. **Switch to PAKER `B5819WS` / `C5278927`**, whose datasheet is already filed at
   `RoHS/2401041156_PAKER-B5819WS_C5278927.pdf`, explicitly covers **SOD-323**, and
   states "Halogen free and RoHS compliant". A datasheet claim is weaker than a test
   report, but it is package-correct where the Hottech report is not.

⚠️ Minor, no order impact: the board says `Manufacturer = Hottech Semi`, the schematic
says `Hottech`, and the real manufacturer is *Guangdong Hottech*. LCSC matches on both
sides, so nothing is mis-ordered.

---

## 4. Do NOT regenerate the v3.1 / v3.2 exports

They are the historical record of what was actually fabricated, and every board in
existence is v3.2. Only **v3.3** is regenerated — it has never been manufactured.
v3.2 doubles as the reference for the CPL check in §2.
