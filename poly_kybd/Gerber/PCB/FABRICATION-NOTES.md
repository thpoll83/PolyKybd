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
| **D2** | Guangdong Hottech `1N5819WS` / `C191023` — kept, no change | ✅ 5,636,800 in stock, SOD-323, not discontinued | ✅ closed 2026-08-24, see below |

⚠️ **C3/C8 value string reads `27pF 0402 16V` but both the old and new parts are 50V**
(`0402CG270J500NT` and `CL05C270JB5NNNC`). The label is inaccurate, the parts are not
under-rated. Left alone to avoid churn; fix it if the value strings are ever tidied.

### D2 — RoHS closed (2026-08-24)

Evidence: **`RoHS/ROHS-2025-HottechElectronics-CTI-A225024736310100101.pdf`** — Centre Testing
International report dated 17 Apr 2025, RoHS 2011/65/EU + (EU) 2015/863, full 10-substance scope
(Pb, Cd, Hg, Cr(VI), PBBs, PBDEs, and the phthalates DBP/BBP/DEHP/DIBP), IEC 62321 methods, all
results **N.D. — PASS**. Its Model No. list reads `SOD-123/323/523/723`, so **SOD-323 is
explicitly covered**. `parts.csv` updated `x Email sent` → `x`; **no part change needed**.

⚠️ **The earlier acceptance was based on a misreading — don't reinstate it.** D2 had been
accepted via `ROHS3HOTTECH.pdf` on the grounds that it "includes 323-series package testing".
That 2020 report's sample list is `SOT-23, 323, 523, 723, … SOD-123`, where the `323` belongs to
the **SOT** run — its SOD coverage stops at **SOD-123**, and it states its results "refer only to
the sample(s) tested". The package was never actually covered, which is why `parts.csv` carried
`x Email sent` the whole time.

⚠️ Two limitations of the new report, both normal for an SMD part but worth being able to answer
if the technical file is challenged: the sample was **tested as a whole** rather than separated
into homogeneous materials (the report says so, and RoHS limits formally apply per homogeneous
material), and the applicant is **Shenzhen Hottech Electronics** while LCSC lists the part's
manufacturer as *Guangdong* Hottech — the report remarks the two are "Group-subsidiary relations",
but that is *according to the client's statement*, not verified by CTI. It is also a
package-family report, not MPN-specific.

The PAKER `B5819WS` / `C5278927` alternative is **no longer needed**, and was the weaker option
regardless: 2,250 in stock against 5.6M, and a 9A surge rating against 25A.

⚠️ Minor, no order impact: the board says `Manufacturer = Hottech Semi`, the schematic says
`Hottech`, and the real manufacturer is *Guangdong Hottech*. LCSC matches on both sides.

---

## 4. Do NOT regenerate the v3.1 / v3.2 exports

They are the historical record of what was actually fabricated, and every board in
existence is v3.2. Only **v3.3** is regenerated — it has never been manufactured.
v3.2 doubles as the reference for the CPL check in §2.

---

## 5. Silkscreen artwork is simplified — do not re-import at full trace fidelity

The Rosetta Stone artwork on the silk layers was imported as traced vector outlines at
full curve fidelity: **5.5 million `gr_poly` vertices** across the boards, which was ~80%
of every board file and pushed three of them past GitHub's 50 MB warning.

⚠️ **That detail cannot be printed.** Measured on the left board, the median edge in the
artwork was **0.017 mm** and **98.6% of edges were under 0.10 mm** — silkscreen resolves
about 0.1 mm and JLC's minimum silk line width is 0.15 mm.

A Douglas–Peucker pass at **0.01 mm** (a tenth of print resolution) is applied by
`poly_kybd/tools/simplify_silkscreen.py`:

| | before | after |
|---|---|---|
| silk vertices | 5,532,117 | 884,434 (−84%) |
| split72 left / right | 51.6 / 52.6 MB | 18.5 / 18.6 MB |
| split42 right / plate_left | 52.9 / 17.1 MB | 18.8 / 3.2 MB |
| **total** | **180.5 MB** | **65.3 MB** |

**Verified visually, not just by vertex count.** Rendering the artwork at 4× print
resolution before and after, of 411,805 differing pixels exactly **4** fall inside an
eroded core — everything else is a 1–2 px (~0.025 mm) edge shift along an outline. No
feature is lost. The one real effect is a uniform **−3.1% ink area**, because RDP cuts
corners inward; the art reads very slightly lighter, undistorted.

The tool touches **only `gr_poly` on layers whose name contains `SilkS`**. After each run,
everything else in the file is byte-identical — copper, mask, paste, edge cuts, footprints,
zones, tracks, vias and the non-silk `gr_poly` blocks (there are 25 on the split72 boards,
including some on `B.Cu` and `B.Mask`). That is asserted per board, not assumed.

⚠️ **Keep the original artwork source** (SVG or whatever it was traced from) outside the
board files. The boards now carry a print-resolution version; if the art is ever needed at
higher fidelity — a larger panel, a poster, a different process — it has to come from the
source, not from the board.

⚠️ **Git LFS was considered and rejected.** It treats the symptom: converting existing files
means rewriting history across every branch, everyone re-clones, and GitHub stops rendering
`.kicad_pcb` diffs. That diffability is load-bearing here — the copper comparisons, CPL
checks and footprint verification in this repo all depend on the boards being diffable text.
