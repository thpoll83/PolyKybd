# PolyKybd — RoHS Documentation Decisions Log

Standard applied throughout: **Directive 2011/65/EU (RoHS) as amended by (EU) 2015/863.**
Last updated: 2026-09-02.

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
- **D2 (1N5819WS, SOD-323):** ✅ closed 2026-08-24 via
  **`ROHS-2025-HottechElectronics-CTI-A225024736310100101.pdf`** — a Centre Testing International
  (CTI) report dated 17 Apr 2025, RoHS 2011/65/EU + (EU) 2015/863, full 10-substance scope
  (Pb, Cd, Hg, Cr(VI), PBBs, PBDEs and the four phthalates DBP/BBP/DEHP/DIBP), IEC 62321 methods,
  **all results N.D. — PASS**. Its Model No. list reads `SOD-123/323/523/723`, so **SOD-323 is
  explicitly covered**.
  - ⚠️ **This supersedes the previous rationale, which was wrong.** D2 was earlier accepted via
    `ROHS3HOTTECH.pdf` "which includes 323-series package testing" — but that 2020 BST report's
    sample list is `SOT-23, 323, 523, 723, … SOD-123`, where the `323` belongs to the **SOT** run.
    Its SOD coverage stops at **SOD-123**, and the report states its results "refer only to the
    sample(s) tested". D2 is SOD-323, so the package was never actually covered. `parts.csv` had
    recorded D2 as `x Email sent` throughout, which was the accurate status.
  - ✅ **DECIDED 2026-09-02 — Shenzhen and Guangdong Hottech are treated as ONE entity.** The
    applicant on the report is **Shenzhen Hottech Electronics**, while LCSC (and JLC's matched
    part on the v3.3 assembly order) lists the manufacturer as *Guangdong* Hottech. The report
    carries a remark that the two are "Group-subsidiary relations"; that linkage is **according
    to the client's statement**, not something CTI verified, but it is accepted here as
    sufficient — same group, same product line. This is a **stated position, not an open
    question**: do not re-raise it as a gap. If it is ever challenged and a firmer basis is
    wanted, the cheap ask is written confirmation from Hottech that the two are the same legal
    entity or a declared group, which converts a client statement into supplier correspondence.
  - ⚠️ **Two limitations remain, as disclosures rather than decisions** — both are inherent to
    the report and normal for an SMD part, but state them if the file is challenged: the sample
    was **tested as a whole** (not separated into homogeneous materials — the report says so
    explicitly, and RoHS limits formally apply per homogeneous material); and it is a
    **package-family report** (`SOD-123/323/523/723`), not MPN-specific to `1N5819WS`.
  - **Consequence:** no part change needed. The PAKER `B5819WS` / `C5278927` alternative
    (`2401041156_PAKER-B5819WS_C5278927.pdf`, SOD-323, "Halogen free and RoHS compliant") is no
    longer required — and is the weaker option anyway: 2,250 in stock against Hottech's 5.6M, and
    a 9A surge rating against 25A.
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

## v3.3 part changes — 2026-08-07

Five parts were retargeted because the ordered ones went **EOL at JLCPCB** ("no longer
manufactured", 0 stock). Certificate consequences:

| Ref | Was | Now | Certificate |
|---|---|---|---|
| C4_1-C4_36, C33, C34 | Sunlord `C118249` | **Vishay** 293D475X9025A2TE3 `C5380411` | **changed** → `vishay-rohs-20250901.pdf` |
| C5, C11 | Samsung `C170128` | Samsung CL10C6R8CB8NNNC `C318672` | unchanged — same blanket declaration |
| U4-U8 | Nexperia `C3303719` | Nexperia 74HC595BQ,115 `C730243` | unchanged — same MPN, same statement |
| U9 | Winbond `C2940195` XGIQ | Winbond W25Q64JVXGIM `C5440778` | unchanged — family-level evidence |
| U12-U25 | TI SN74LVC1G126DBVR | **Nexperia** 74AHC1G125GW,125 `C85397` | **changed** → Nexperia statement |

### New evidence
- **`vishay-rohs-20250901.pdf`** — Vishay ROHS Compliance Statement, 1 September 2025, signed by
  Roy Shoshani (COO Semiconductors / CTO). Header cites *"Directives 2002/95/EG, 2011/65/EU,
  2015/863/EU (RoHS I – III)"*. Company-wide: certifies that all products *identified as
  RoHS-compliant* meet those directives. Our part is `293D475X9025A2TE3` — the **`E3` termination
  suffix is Vishay's lead-free code**, and the 293D datasheet states "Terminations: 100 % matte tin
  standard" and warns that parts with lead (Pb) terminations are *not* RoHS-compliant. Source:
  `vishay.com/doc?49157`. One page, so `Appendix Pages = all`.
- **`nexperia-74AHC1G125-datasheet.pdf`** — Nexperia 74AHC1G125/74AHCT1G125 data sheet, Rev 15.1,
  28 August 2024. Supporting documentation for the new buffer; not itself the RoHS evidence.

### U12–U25 buffer — re-pointed to the Nexperia statement
The fitted part is now Nexperia `74AHC1G125GW,125` (SOT-353), so the TI datasheet no longer
applies. The existing **`Nexperia - Statement on RoHS 20241008.pdf`** covers it: it is company-wide
across all Nexperia semiconductor products and cites the correct directives.

**Checked the exemption appendix (page 3):** it lists 37 packages that exceed the 0.1 % lead limit
and rely on RoHS exemptions 7(a) / 7(c)-I. **Neither SOT-353 (U12–U25) nor DHVQFN-16 (U4–U8) is on
that list**, so both Nexperia parts are compliant outright, with no exemption claimed. Rows 37 and
41 now share one certificate and therefore one appendix section.

The reference also fixes the old `U12-U23,U?,U?` designator string → **`U12-U25`**, closing the
housekeeping item below. Qty stays 14 (one buffer per package; the earlier "two per package" note
was based on the wrong part).

- `sn74lvc1g126.pdf` **deleted** — datasheet for a part that was never fitted.
- `sunlord-rohs.pdf` / `sunlord-rohs-en-translated.pdf` and
  `2410010304_Texas-Instruments-SN74AHC1G125DCKR_C151890.pdf` are now unreferenced but **kept**:
  they document what the built **v3.2** boards actually shipped with.

### Samsung 6.8 pF — traceability note
The manufacturer is unchanged, so the blanket "all our MLCCs" declaration (page 2) still applies
and no new document is needed. But part-level traceability is now weaker, and the page selection
is stale:
- The Product Lineup lists `CL10C6R8**D**B8NNN` (±0.5 pF, the **old** part) on **page 14** — which
  the current selection `1,2,13,19,25` does not even include.
- The new `CL10C6R8**C**B8NNNC` (±0.25 pF) does **not appear anywhere** in the document.

So C5/C11 now sit in the same category as Silergy below: covered by a blanket report that does not
name the part, with linkage via the reference table and section divider. Consider adding page 14.

### Winbond flash — directive version caveat
`winbond-W25Q64JV-rohs.png` is page 59 of the W25Q64JV datasheet; the RoHS claim is Note 2 under
Absolute Maximum Ratings. It is titled **W25Q64JV** (the family), so it covers `XGIM` exactly as it
covered `XGIQ` — no new document needed. **However it cites RoHS `2002/95/EU`**, the superseded
directive, not 2011/65/EU + 2015/863. Worth requesting a current Winbond declaration before the
technical file is finalised.

## Reproduce
From `RoHS/`:
1. `python3 appendix-tools/update_xls_pages.py` — (re)writes the `Appendix Pages` column from the certs.
   Edit that column by hand to include more/fewer pages for any certificate.
2. `python3 appendix-tools/build_appendix.py` — rebuilds `PolyKybd-RoHS-Appendix.pdf` from the .xls.
   Requires `xlrd`, `pypdf`, `reportlab`, `pdfplumber`, `Pillow`.

## Open housekeeping (not compliance blockers)
- ~~The BOM row for U12–U23 still contains two unnamed designators (`U?,U?`)~~ — **resolved
  2026-08-07**, now `U12-U25`.
- ~~`PolyKybd-RoHS-Appendix.pdf` and `PolyKybd-Schematics.pdf` are stale~~ — **both regenerated
  2026-08-07** from the v3.3 sources.
- ~~Both appendix tools carry a hardcoded sandbox path~~ — **fixed 2026-08-07**; all six tools now
  resolve paths relative to the checkout, overridable with `POLYKYBD_ROHS`.
- Some certificates in `RoHS/` are referenced by no BOM line (Aerosemi MT9700, Fenghua RC-02W,
  Prosperity MCS0530, Uniroyal 0603WAF); confirm whether they are alternates/DNPs or should be
  linked. Since 2026-08-07 this also covers `sunlord-rohs.pdf` and the TI buffer datasheet, which
  are **deliberately** kept as the record of what the built v3.2 boards shipped with.

**→ See `CE-document-status.md`** for the full state of every compiled document and the remaining
certificate questions (compliance matrix, PCB layers, Declaration of Conformity, the Winbond
directive version, the Samsung page selection, and JUSHUO vs Hirose on J1–J36).
- Some certificates in `RoHS/` are not referenced by any BOM line (e.g. Aerosemi MT9700, Fenghua RC-02W,
  Prosperity MCS0530, Uniroyal 0603WAF); confirm whether they are alternates/DNPs or should be linked.
