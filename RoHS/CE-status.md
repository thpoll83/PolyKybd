# PolyKybd Split72 — CE Certification Status Tracker

Living checklist. Update the boxes as items close. Manufacturer: **PolyTasten GmbH** (Austria).
Examiner: Clemens Mayer (GetSmandered), project R26_06. Last updated: 2026-07-17.

**Applicable:** EMC 2014/30/EU · RoHS 2011/65/EU · GPSR (EU) 2023/988 · WEEE 2012/19/EU · PPWR (packaging).
**Not applicable:** LVD (USB 5 V SELV), RED (no radio), battery, machinery. **Watch:** CRA (EU) 2024/2847.

Legend: `[x]` done · `[~]` drafted, needs your input · `[ ]` open · 🔴 external/critical-path.

## A. Done / drafted (in `RoHS/`)
- [x] RoHS technical documentation (EN IEC 63000) — `PolyKybd-RoHS-Compliance-Matrix.xlsx`, `PolyKybd-RoHS-Appendix.pdf`, `parts-to-pdf-reference.xls`, `RoHS-decisions-log.md`
- [x] Applicable standards identified — EN 55032, EN 55035 (+ EN 62368-1, EN IEC 63000)
- [x] Schematics — `PolyKybd-Schematics.pdf`, `schematics.md`
- [~] PCB construction files — `PolyKybd-PCB-Layers.pdf` (copper/mask/paste/outline). **Silkscreen + fab/stack-up + assembly drawing still to export via kicad-cli**
- [~] Risk analysis — `CE-Risk-Analysis.md` + filled consultant template `Riskanalysis_PolyKybd_EN.ods` (Image directory + edition years still to add)
- [~] Safety notice — `CE-Safety-Notice.md` (ISO 7010 pictograms to insert; translations)
- [~] User manual + quick start — `CE-User-Manual.md` (URL/QR, specs, translations)
- [~] Label / CE marking — generator `appendix-tools/generate_label.py` (official CE+WEEE artwork; address; origin)
- [~] EU Declaration of Conformity — `EU-Declaration-of-Conformity.docx` (final sign-off is the last step)

## B. Info you must supply (`[TO CONFIRM]` fields)
- [ ] PolyTasten GmbH full legal address + company/UID number
- [ ] EU Responsible Person (likely you — confirm)
- [ ] Standard edition years: EN 55032, EN 55035, EN 62368-1
- [ ] Firmware version covered by the file
- [ ] Electrical: typical/max current (mA), operating temperature range
- [ ] Country-of-origin decision ("Designed in Austria" preferred; confirm binding origin with WKO/customs if needed)
- [ ] Manual URL / QR target
- [ ] Consultant details in the risk template

## C. Documents still to author (no lab needed)
- [ ] Complete risk template **Image directory** (ISO 7010 pictograms, product photo, block diagram)
- [ ] **Technical-file compilation** — one indexed file; Git **release per hardware/firmware/supplier revision** (batch-level traceability)
- [ ] **Country-of-origin / sourcing** documentation (production procedure, where parts come from)
- [ ] **Post-market surveillance** plan
- [ ] **Translations** of manual + safety notice (machine translation OK; native proof-read + record it)
- [ ] Export **PCB silkscreen** + fabrication/stack-up + assembly drawings (kicad-cli); refresh `PolyKybd-PCB-Layers.pdf`
- [ ] **Firmware/source archival** — versioned zip incl. all libraries + their licenses; licenses of any open-source designs reused
- [ ] **PPWR packaging** — obtain a Declaration of Conformity from the packaging supplier for all packaging materials (mandatory from 12 Aug 2026)

## D. External / physical — critical path 🔴
- [ ] 🔴 **Pre-compliance EMC testing** (worst-case firmware, changing screen images) — build confidence first
- [ ] 🔴 **EMC lab test**: EN 55032 emissions + EN 55035 immunity, Class B (conducted emissions possibly excludable). **This gates the DoC and final sign-off.**

## E. Production & marking
- [ ] Swap placeholder **CE mark + WEEE** artwork for official versions (CE ≥ 5 mm, correct proportions)
- [ ] Non-removable marking in production (laser engraving — serial generator ready)
- [ ] Finalize label with real address/origin

## F. Final steps (after the test report)
- [ ] Finalize + sign the **EU Declaration of Conformity**
- [ ] Affix CE mark, place on market
- [ ] Retain technical file + DoC for **10 years**

---
**Critical path:** finish PCB silkscreen + technical-file compilation (quick), then **book the EMC lab** —
emissions/immunity results are the gate for the DoC and sign-off.
