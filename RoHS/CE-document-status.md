# CE technical file — document status

Where every compiled document and certificate stands after the v3.3 part changes
(PRs #23, #24, #25, #26). Written 2026-08-07.

**Read `RoHS-decisions-log.md` first** — it records *why* each certificate was chosen.
This file records *what is still outstanding*.

---

## 1. Compiled documents — regenerated from source

| Document | State | Notes |
|---|---|---|
| `PolyKybd-Schematics.pdf` | ✅ **current** | Re-exported with kicad-cli 9.0 and re-composed. Verified: buffer sheet shows `74AHC1G125`, RP2040 sheet shows `W25Q64JVXGIM` |
| `PolyKybd-RoHS-Appendix.pdf` | ✅ **current** | Rebuilt 2026-09-04: **119 pages**, 26 sections, no missing documents. ⚠️ It had been stale since 2026-08-24 — the D2 evidence swap edited the `.xls` without rebuilding, so the shipped appendix still carried the superseded `ROHS3HOTTECH.pdf` instead of the 2025 Hottech CTI report. **Rebuild the appendix in the same change as any `.xls` edit.** |
| `schematics/*.pdf` (7 per-sheet) | ✅ **current** | Re-exported; page counts unchanged, so composition is like-for-like |
| `parts-to-pdf-reference.xls` | ✅ **current** | Source of truth. 44×8 preserved; every referenced certificate exists on disk. Last edited 2026-09-04 (R18 → Yageo AC `C227547`; `R3,R4,R7,R9` onto the AC datasheet; `R5,R6,R16,R19,R21` corrected to Vishay) |
| `schematics/parts.csv` | ✅ **current** | |

### Still stale

| Document | Blocked on | What is needed |
|---|---|---|
| ~~`PolyKybd-RoHS-Compliance-Matrix.xlsx`~~ | — | ✅ **done 2026-08-13.** See §2 |
| **`PolyKybd-PCB-Layers.pdf`** | ~~A6~~ — **now unblocked**, v3.3 gerbers exist | `pcb_render.py` reads gerbers from `RoHS/pcb/<side>`; copy the v3.3 sets there, render, then `pcb_merge.py`. Needs `cairosvg` + `gerbonara`; note `cairosvg` needs a native cairo DLL that is **not present on this Windows box** — `gerbonara` + Pillow rasterising works as an alternative |
| **`EU-Declaration-of-Conformity.docx`** | **GmbH registration** + EMC report | Every field is still a `[TO CONFIRM]` placeholder: DoC number, revision, manufacturer name, address, contact. Must name **PolyTasten GmbH**, not Thomas Pollak |

---

## 2. `PolyKybd-RoHS-Compliance-Matrix.xlsx` — ✅ corrected 2026-08-13

*Kept for the record; all of the below is now applied.*

Sheet **Compliance Matrix**:

| Ref | Currently says | Should say |
|---|---|---|
| C4_1–C4_36, C33, C34 | Sunlord · `sunlord-rohs.pdf` | **Vishay** · `vishay-rohs-20250901.pdf` |
| C5, C11 | Samsung blanket | unchanged, but see the traceability caveat in §3 |
| U4–U8 | Nexperia statement | unchanged ✓ |
| U9 | `W25Q64JVXGIQ` · winbond | **`W25Q64JVXGIM`** · **Winbond** (capital W) |
| U9 | *"RoHS 2011/65/EU as amended by (EU) 2015/863"* | ❌ **wrong** — the document actually cites **2002/95/EU**. See §3 |
| U12–U23, U?, U? | `SN74LVC1G126DBVR` · TI · `sn74lvc1g126.pdf` | **U12–U25** · `74AHC1G125GW,125` · **Nexperia** · Nexperia RoHS statement |

Sheet **Findings & Actions**:

- Row 3 *"RESOLVED — U12-U23 (SN74LVC1G126DBVR) re-pointed to sn74lvc1g126.pdf"* is now
  obsolete twice over: that file is deleted, and the part is Nexperia. Rewrite to record the
  re-point to the Nexperia statement, and mark the `U?,U?` housekeeping **closed** (now `U12-U25`).

There is no build script for this workbook — it is maintained by hand. `openpyxl` reads and
writes it (installed).

---

## 3. Certificate evidence — open questions

### a. Winbond flash — cites a superseded directive ⚠️

`winbond-W25Q64JV-rohs.png` is page 59 of the W25Q64JV datasheet; the RoHS claim is Note 2
under Absolute Maximum Ratings. Two separate points:

- **Coverage is fine.** The page is titled `W25Q64JV` — the family — so it covers the new
  `XGIM` exactly as it covered `XGIQ`. No new document needed for the part change.
- **The directive is wrong.** It cites **RoHS `2002/95/EU`**, superseded by 2011/65/EU and
  amended by (EU) 2015/863. The compliance matrix currently *claims* the modern directive,
  which the document does not support.

**Action:** request a current RoHS/green declaration from Winbond for the W25Q64JV family. If
none is forthcoming, correct the matrix to state what the evidence actually says rather than
overstating it.

### b. Samsung 6.8 pF — part no longer named in its own certificate

The manufacturer is unchanged, so the blanket *"all our MLCCs"* declaration (page 2) still
applies and **no new document is required**. But part-level traceability got weaker:

- The Product Lineup lists `CL10C6R8DB8NNN` (±0.5 pF, the **old** part) on **page 14** — which
  the current page selection `1,2,13,19,25` does not even include.
- The new `CL10C6R8CB8NNNC` (±0.25 pF) does **not appear anywhere** in the 84-page document.

**Action (choose one):**
1. Add page 14 to the selection and accept blanket-only coverage for the new part — putting
   C5/C11 in the same category as Silergy/SY6280AAC, which the decisions log already accepts.
2. Request a part-specific Samsung declaration for `CL10C6R8CB8NNNC`.

Option 1 is consistent with existing practice and costs nothing.

### c. GigaDevice — evidence staged, **not** wired into the technical file

The Winbond flash pre-order for v3.3 (`C5440778`) **failed**, so GigaDevice `GD25Q64EQIGR`
(`C3202817`) is under evaluation as the second source for U9. Its RoHS evidence has been
collected in advance and is held in `RoHS/`, but **is deliberately not referenced from
`parts-to-pdf-reference.xls` or the compliance matrix** — the part is not on the board.

| File | What it is |
|---|---|
| `gigadevice-rohs-declaration-webcapture-20260814.pdf` | **Capture of a public web page**, not a manufacturer-issued certificate. GigaDevice publishes its RoHS 2.0 Declaration as a web page only |
| `gigadevice-iso14001-2015.pdf` | Genuine signed certificate — reg. 50050943 UM15, valid 2023-09-21 → 2026-09-20 |

**Content is good, form is weak.** The declaration cites the current directives
(2011/65/EU + (EU) 2015/863) — unlike Winbond's, which cites the superseded 2002/95/EU — and
lists all ten substances at the correct limits. But it carries no date, revision or
signatory. Part-level linkage comes from the datasheet ordering table, which decodes suffix
`G` as "Pb Free + Halogen Free Green Package"; the part is `GD25Q64E`**`Q`**`I`**`G`**`R`.

**Open action:** request a dated, signed RoHS declaration from GigaDevice naming the part,
as was obtained for Vishay. Ask at the same time as the pre-order. The capture is interim
evidence and should be replaced if a signed document is issued.

Full sourcing analysis, including the boot2 compatibility constraint that governs which
flash can be used at all: `notes/flash-second-sourcing.md` in the **polykybd-costing** repo.

### d. JUSHUO connectors J1–J36 — coverage still unverified

Three JUSHUO RoHS PDFs are on file (`Jushuo_SZXEC24000437502/504/505`). They are **encrypted,
image-only scans with no text layer**, so it could not be confirmed whether they cover the
fitted part — including the gold plating. Note also that `parts.csv` lists J1–J36 as **JUSHUO**
while the board ships **Hirose** `C324724` (row 16 of the .xls points at the Hirose spec sheet).

**Action:** resolve the manufacturer discrepancy first, then confirm certificate coverage.

### e. Unreferenced certificates — confirm intent

Now unreferenced but **deliberately kept**, as they document what the built **v3.2** boards
shipped with:

- `sunlord-rohs.pdf`, `sunlord-rohs-en-translated.pdf` — superseded by Vishay for the tantalum
  (Sunlord is still live for FB1/FB2 via its own part-specific document)
- `2410010304_Texas-Instruments-SN74AHC1G125DCKR_C151890.pdf` — the old buffer

Carried over from the decisions log and still open: Aerosemi MT9700, Fenghua RC-02W,
Prosperity MCS0530, Uniroyal 0603WAF are referenced by no BOM line. Confirm whether they are
alternates/DNPs or should be linked.

**Deleted:** `sn74lvc1g126.pdf` — a datasheet for a part that was never fitted.

---

## 4. Housekeeping

- ~~**`.gitattributes` — mark PDFs binary.**~~ ✅ **done 2026-08-13.** A repo-root
  `.gitattributes` now marks PDFs, Office documents, images, 3D files and archives binary.
  Verified: `PolyKybd-Schematics.pdf` reports `Bin 37253660 -> 37253659 bytes` instead of
  ~1.35 M lines of text. KiCad sources stay text on purpose — a readable diff on them is what
  caught the property-only scope of the recent part swaps.
- **Tool dependencies.** The appendix tools need `xlrd`, `pypdf`, `reportlab`, `pdfplumber`,
  `Pillow`, and — for writing the .xls — `xlutils` and `xlwt`. `openpyxl` for the matrix.
  `pcb_render.py` additionally needs `cairosvg` and `gerbonara`, which are **not installed**.
  Worth a `requirements.txt` next to the tools.
- **Paths.** All six tools were made repo-relative in #26 (they carried a hardcoded
  `/sessions/bold-festive-carson/...` from a cloud session). `POLYKYBD_ROHS` overrides.

---

## 5. Order of operations

1. Correct the compliance matrix (§2) — **can be done now**
2. Decide the Samsung page selection (§3b) and re-run `update_xls_pages.py`, then
   `build_appendix.py`
3. Ask Winbond for a current declaration (§3a); correct the matrix either way
4. Resolve JUSHUO vs Hirose for J1–J36 (§3c)
5. **After A6** (v3.3 gerbers): `pcb_render.py` → `pcb_merge.py` → `PolyKybd-PCB-Layers.pdf`
6. **After the GmbH exists** and the EMC report is issued: fill in the DoC (§1)
