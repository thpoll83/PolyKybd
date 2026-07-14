# PolyKybd — RoHS Documentation Decisions Log

Standard applied throughout: **Directive 2011/65/EU (RoHS) as amended by (EU) 2015/863.**
Last updated: 2026-07-13.

This file records the decisions made while assembling the RoHS evidence for the CE technical file,
so the results can be reviewed and reproduced.

## Files in `RoHS/`
- `parts-to-pdf-reference.xls` — BOM → certificate map. **Source of truth.** Columns:
  `Reference | Part | Datasheet Appendix (cert file) | Qty | Manufacturer | RoHS | (note) | Appendix Pages`.
- `PolyKybd-RoHS-Compliance-Matrix.xlsx` — reviewed status matrix (sheets: Compliance Matrix; Findings & Actions).
- `PolyKybd-RoHS-Appendix.pdf` — the compiled single-PDF appendix (title → parts reference → TOC → certificate sections).
- `appendix-tools/update_xls_pages.py` — recomputes the `Appendix Pages` selection and writes it into the .xls.
- `appendix-tools/build_appendix.py` — builds the appendix PDF, reading the page selection from the .xls.
- the individual certificate PDFs / PNGs (kept in full; the appendix uses excerpts only).

## Certificate reference fixes
1. **Filename mismatches corrected** in `parts-to-pdf-reference.xls`:
   - LED1–LED36 (XL-3030RGBC): `2301111010_…` → `2402181502_XINGLIGHT-XL-3030RGBC-WS2812B_C5349958.pdf` (date prefix).
   - U9 (W25Q64JV flash): `Winbond-W25Q64JV-rohs.png` → `winbond-W25Q64JV-rohs.png` (case).
2. **Re-points to better/correct evidence already on file:**
   - D5 (green 0805, C2297): was `KT-0805-B.pdf` (a **blue** LED spec) → `C2297.pdf` (KENTO 0805 green LED, RoHS stated).
   - U3 (SY6280AAC): was a Silergy **application note** → `ROHS-2024-SilergyCorp.pdf` (SGS RoHS test report, Jan 2024).
   - U12–U23 (SN74LVC1G126DBVR): was `…SN74AHC1G125DCKR…` (wrong part) → `sn74lvc1g126.pdf` (correct TI datasheet, RoHS stated).
   - J37 (FH34SRJ-12S): → `FH34SRJ-12S-0.5SH(99)_…_0000414526.pdf` (states "This product is RoHS compliant").
   - FB1, FB2 (GZ2012D601TF): → `2310301640_Sunlord-GZ2012D601TF_C1017.pdf` (part-specific Sunlord doc).

## Component-specific decisions
- **D2 (1N5819WS, SOD-323):** accepted via `ROHS3HOTTECH.pdf` (Hottech/BST RoHS 2 test report, which
  includes 323-series package testing) together with the assembly house (JLCPCB) marking the part
  RoHS-compliant.
- **Connectors J1–J36 / J37 / J39:** each references the Hirose spec sheet for its own part number,
  all stating RoHS compliance. J1–J36 = FH34SRJ-14S, J37 = FH34SRJ-12S, J39 = FH12-30S. The trailing
  `(50)`/`(99)` in the filenames is the **packaging quantity**, not a spec revision — so the
  part-matching sheet is correct regardless of that number. J1–J36 kept on the 14S sheet (no 14S(99)
  exists; not needed).
- **U12–U23 (SN74LVC1G126):** the designator/qty count reflects **two buffers per package**; not an error.
- **FB1/FB2:** now on the part-specific Sunlord document (was the generic company-wide DoC, which was
  also valid).
- **Scoped out (no separate certificate):** pin headers are **not populated**; mounting holes and test
  points are **bare PCB copper**, covered by the PCB substrate RoHS evidence.
- **Bare PCB:** `rohs-certificate-of-conformity.pdf` (JLCPCB DoC, Soar Testing 2025, ENIG + lead-free HASL).

## Appendix assembly rules
- **One section per certificate**, ordered by first appearance in the BOM; each section starts with a
  headline/divider page (manufacturer + a table of the designators/parts/qty it covers + the filename).
- **Table of contents** enumerates *every* part per section (no truncation; wraps across lines) with the
  section's page number.
- **Page trimming** (to keep the PDF manageable): the `Appendix Pages` column in the .xls controls which
  pages of each certificate are included.
  - `all` — include the whole document (used for short docs ≤3 pages and image-only scans that can't be
    text-analysed, e.g. `2310301640_Sunlord-GZ2012D601TF_C1017.pdf`).
  - `image` — a PNG certificate, rendered as one full page.
  - a page list (e.g. `1,2,13,19,25`) — those pages only. Auto-selection keeps page 1 (identity) plus the
    RoHS-relevant pages and a ±1-page neighbour for context. Trimmed sections state the kept pages on the
    divider and note the full document is retained in the repo.
- **Page size:** every page of every output PDF is normalised to **A4 portrait**. Certificate pages
  of other sizes (Letter, etc.) are scaled to fit and centred; landscape pages (and the schematic
  sheets) are rotated 90° so they read by turning the page clockwise (title block bottom-right).
- **Samsung MLCC (`…CL05A105KA5NQNC_C52923.pdf`):** this is a blanket "all our MLCCs" RoHS declaration
  (page 2) that does not name individual capacitances. To show the actual parts, the selection also
  includes the manufacturer's **Product Lineup** pages: `1,2,13,19,25` — page 19 lists the exact part
  `CL05A105KA5NQNC`; pages 13 (C0G) and 25 (X7R) cover the other used dielectrics. Part→certificate
  traceability is additionally provided by the reference table and the section divider.

## Part-reference verification (of trimmed certificates)
Each trimmed certificate was checked to confirm the specific part number appears on a **kept** page:
- Present on a kept page: NationStar NCD0805R1, C2297 (green LED), KENTO KT-0805Y, SXN SMMS0420-2R2M,
  XINGLIGHT XL-3030RGBC, Yageo RC0603, Kailh CPG151101S11-16, MSKSEMI TPD4E05U06DQAR, TI SN74LVC1G126,
  TXC 7M12000044, Samsung CL05A105 (page 19).
- **Blanket reports that do not name the part anywhere** (linkage via the reference table + divider):
  - Samsung `…CL05A105…` — addressed by adding Product Lineup pages (see above).
  - **Silergy `ROHS-2024-SilergyCorp.pdf`** — SGS report certifying Silergy's package families generally
    (coverage list includes "SOT", i.e. SY6280AAC's package). The part number SY6280 does not appear in the
    document, so no part-specific page can be added; U3 → SY6280AAC linkage is via the reference table/divider.

## Reproduce
From `RoHS/`:
1. `python3 appendix-tools/update_xls_pages.py` — (re)writes the `Appendix Pages` column from the certs.
   Edit that column by hand to include more/fewer pages for any certificate.
2. `python3 appendix-tools/build_appendix.py` — rebuilds `PolyKybd-RoHS-Appendix.pdf` from the .xls.
   Requires `xlrd`, `pypdf`, `reportlab`, `pdfplumber`, `Pillow`.

## Open housekeeping (not compliance blockers)
- The BOM row for U12–U23 still contains two unnamed designators (`U?,U?`); resolve when convenient.
- Some certificates in `RoHS/` are not referenced by any BOM line (e.g. Aerosemi MT9700, Fenghua RC-02W,
  Prosperity MCS0530, Uniroyal 0603WAF); confirm whether they are alternates/DNPs or should be linked.
