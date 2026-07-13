# Task: Build the PolyKybd RoHS Compliance Appendix (single PDF)

## Goal
Produce **one** PDF — `RoHS/PolyKybd-RoHS-Appendix.pdf` — for the CE technical file. It bundles a
parts-to-certificate reference and a table of contents, followed by every RoHS certificate/report,
each introduced by a short headline page saying which part(s) it covers.

## Inputs (all already in `RoHS/`)
- `parts-to-pdf-reference.xls` — the BOM → certificate map. **Legacy `.xls`**, read with `xlrd`
  (openpyxl will not open it). Sheet `parts`, columns:
  `Reference | Part | Datasheet Appendix | Qty | Manufacturer | RoHS`.
  The `Datasheet Appendix` column holds the certificate **filename** in `RoHS/`.
- The certificate files themselves — mostly `.pdf`, plus two images:
  `winbond-W25Q64JV-rohs.png` and `rp2040-rohs.png`.
- `PolyKybd-RoHS-Compliance-Matrix.xlsx` — the reviewed status matrix (source for the reference
  table and the per-part notes; sheet `Compliance Matrix`, and `Findings & Actions`).
- `rohs-certificate-of-conformity.pdf` — JLCPCB bare-PCB DoC. **Not** in the .xls; add it as its
  own section (bare PCB substrate; also covers exposed copper of mounting holes & test points).

## Output structure
1. **Title page** — "PolyKybd — RoHS Compliance Appendix", subtitle "Directive 2011/65/EU (RoHS) as
   amended by (EU) 2015/863", date, and a one-line scope note.
2. **Parts reference table** — every BOM line: Designators, Part/Value, Qty, Manufacturer,
   Certificate file, Section #. (Pull straight from the .xls; Section # is assigned in step 4.)
3. **Table of contents** — Section N · part/designators · page number. Add real PDF bookmarks
   (outline) so it's navigable.
4. **Certificate sections** — **group each certificate once** (default). Order sections by first
   appearance in the BOM. For each unique certificate file:
   - a **divider/headline page**: `Section N — <Manufacturer> — <short part description>` and a line
     `Covers: <all designators that reference this file>`;
   - then the certificate itself: append PDF pages as-is, or place a PNG full-width on one page.
   - Add a bookmark at each divider page.

Notes:
- Several files are shared by many lines (e.g. the Samsung MLCC cert covers ~15 capacitor lines, the
  Yageo cert ~14 resistor lines) — that's why grouping once and listing all designators is the
  default. If per-part repetition is wanted instead, invert the grouping.
- Keep a fixed, professional look for generated pages (Helvetica/Arial, consistent margins).

## Suggested tooling
- `pypdf` (`PdfWriter`/`PdfReader`) to merge and to add the outline/bookmarks.
- `reportlab` to render the title, reference table, TOC and divider pages, then merge those with the
  source certs via `pypdf`. (Two-pass for the TOC: build sections first to learn page numbers, then
  render the TOC.)
- For the two PNGs, draw the image scaled to the page with `reportlab` before merging.
- LibreOffice (`soffice`) is available if any source needs normalising.

## Current project state (context)
- The `.xls` references were reconciled and all resolve to real files. Recent re-points:
  D5 → `C2297.pdf`; U3 → `ROHS-2024-SilergyCorp.pdf`; U12–U23 → `sn74lvc1g126.pdf`;
  J37 → `FH34SRJ-12S-0.5SH(99)_..._0000414526.pdf`; FB1/FB2 → `2310301640_Sunlord-GZ2012D601TF_C1017.pdf`.
- Matrix status: all 47 rows Documented. Two housekeeping notes only (not blockers): U12–U23 count is
  explained by two buffers per package; the FH34 filename's trailing (50)/(99) is packaging quantity,
  not a spec revision.
- D2 (1N5819WS, SOD-323) accepted via the Hottech/BST report + fab RoHS marking.

## Definition of done
- `RoHS/PolyKybd-RoHS-Appendix.pdf` exists, opens cleanly, every BOM line appears in the reference
  table, every referenced certificate is present exactly once with a correct headline, TOC page
  numbers match, and bookmarks jump to each section.
- Verify no referenced filename is missing before building (cross-check the .xls against `RoHS/`).
- `git add RoHS/PolyKybd-RoHS-Appendix.pdf RoHS/parts-to-pdf-reference.xls RoHS/PolyKybd-RoHS-Compliance-Matrix.xlsx`
  and commit (e.g. `RoHS: add compiled RoHS compliance appendix PDF`), then push.
