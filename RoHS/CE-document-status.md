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
| `schematics/parts.csv` | ✅ **current** | The technical file's BOM (per `CE-Technical-File-Checklist.md`) — **not** a generator input; no script reads it. Corrected 2026-09-04: R18 → C227547, and three rows that disagreed with the board (`R5,R6,R16,R19,R21` were listed as Yageo but are Vishay; `R10,R11,R30` and `D5` carried another part's datasheet URL) |

### Still stale

| Document | Blocked on | What is needed |
|---|---|---|
| ~~`PolyKybd-RoHS-Compliance-Matrix.xlsx`~~ | — | ✅ **done 2026-08-13.** See §2 |
| **`PolyKybd-PCB-Layers.pdf`** | ~~A6~~ — **now unblocked**, v3.3 gerbers exist | `pcb_render.py` reads gerbers from `RoHS/pcb/<side>`; copy the v3.3 sets there, render, then `pcb_merge.py`. Needs `cairosvg` + `gerbonara`; note `cairosvg` needs a native cairo DLL that is **not present on this Windows box** — `gerbonara` + Pillow rasterising works as an alternative |
| **`EU-Declaration-of-Conformity.docx`** | **GmbH registration** (the EMC test has passed — §6) | Every field is still a `[TO CONFIRM]` placeholder: DoC number, revision, manufacturer name, address, contact. Must name **PolyTasten GmbH**, not Thomas Pollak. Its EUT description must name the two required ferrites (§7) |

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

Carried over from the decisions log and still open: Aerosemi MT9700, Fenghua RC-02W and
Prosperity MCS0530 are referenced by no BOM line. Confirm whether they are alternates/DNPs or
should be linked.

**Uniroyal 0603WAF is no longer one of them** — answered 2026-09-04: evaluated as the `R18`
replacement and rejected (its datasheet carries no RoHS statement), so
`2206010216_UNI-ROYAL-…_C7250.pdf` stays unreferenced **deliberately**. See the decisions log.

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
2. Decide the Samsung page selection (§3b), then `build_appendix.py`. ⚠️ **Edit
   the `Appendix Pages` cell by hand — do NOT re-run `update_xls_pages.py`**: §3b
   option 1 *is* a hand-curated selection, and that script recomputes every row
   and destroys them (it has done so once; see `RoHS-decisions-log.md`)
3. Ask Winbond for a current declaration (§3a); correct the matrix either way
4. Resolve JUSHUO vs Hirose for J1–J36 (§3c)
5. **After A6** (v3.3 gerbers): `pcb_render.py` → `pcb_merge.py` → `PolyKybd-PCB-Layers.pdf`
6. ✅ **EMC test done 2026-10-13** — passed with two snap ferrites added (§7)
7. **When the report arrives** (§6b): check which hardware revision it names; the
   sample reported `HW0x3200` while the boards are v3.3
8. **Record the ferrite placement** from the report before it is needed for a
   production fitting instruction (§7c) — unrecoverable later
9. **Wire the ferrite datasheet into the appendix** (§7d.3) — add the `.xls` row
   and rebuild in the same change; do not re-run `update_xls_pages.py`
10. **After the GmbH exists**: fill in the DoC (§1), naming the ferrites in the
    EUT description

---

## 6. EMC test — done, passed with added ferrites (2026-10-13)

The lab test ran on **Tuesday 2026-10-13** and the product **passed**, but only
with two snap ferrites fitted to the cables — see §7, which is now a shipping
requirement, not a test-bench detail. Confirm the exact test date and the EUT
table against the issued report when it arrives; everything below is what was
submitted, recorded here so the DoC and the report can be checked against each
other.

### a. EUT identification as submitted

| Field | Value |
|---|---|
| Manufacturer | PolyTasten GmbH — address `[TO CONFIRM]` (same placeholder as the DoC) |
| Product | PolyKybd Split72 |
| Model / type designation | `POLYKYBD-SPLIT72-01` |
| Hardware revision | **v3.3** |
| Firmware | `PolyKybd-fw-v1.7.3` (tagged 2026-10-05, `PROTOCOL_VERSION 22`) |
| USB VID / PID | `0x2021` / `0x2007` |
| USB descriptor strings | Manufacturer `PolyTasten`, Product `PolyKybd Split72` |
| Sample serial | `POLYKYBD-SPLIT72-01/3.3/EMC-001` |
| Required accessory | 2 × Würth Elektronik `74271111` snap ferrite (§7) |

The EUT is **both halves plus the interconnect**, not one device: the bridge
cable carries a 460800-baud full-duplex UART and radiates, which is precisely
why it needed a ferrite. **Both cable lengths belong in the report's EUT
description** — a radiated result is not reproducible without them.

### b. ⚠️ The tested sample reported hardware revision 3.2, not 3.3

`keyboards/polykybd/split72/keyboard.json` carried `"device_version": "3.2.0"`
at the time of the test, so QMK generated `DEVICE_VER 0x3200` and the sample
stated v3.2 in two places: the USB `bcdDevice` field, and the HID `GET_ID`
reply (`"Split72 1.7.3 P22 HW0x3200 "`, from `hid_com.c`'s
`POLY_GET_ID_STR`).

**Check what the issued report says.** If the lab took the revision from the
paperwork and the label it reads v3.3 and there is nothing to do. If they read
it off the USB descriptor, the report names a revision that does not exist, and
a DoC for v3.3 cannot cleanly reference it — that needs a correction from the
lab, or a dated note in the technical file explaining the discrepancy.

A fix is on `claude/polykybd-costing-handover-6iwoes` in the firmware repo
(`device_version` → `3.3.0`). It is worth stating explicitly, so nobody later
reads it as invalidating the test: **this changes only a descriptor string and
has no effect on emissions.** Nothing reads the value for a decision — the host
keeps it as a display string, the rig does not check it, and no test pins
`0x3200`.

### c. The USB serial number is not this serial

`SERIAL_NUMBER_USE_HARDWARE_ID` defaults on for ChibiOS, and RP2040's
`get_hardware_id()` returns `flash_get_unique_id()` — the external QSPI flash
chip's 0x4B unique id, since the RP2040 has none of its own. So the serial
string in the USB descriptor is a 16-hex-digit flash id unrelated to
`POLYKYBD-SPLIT72-01/3.3/EMC-001`, which is a chassis/label serial. If the
report carries both, say which is which, or it reads as two unexplained
serials for one sample.

---

## 7. Required accessory: two snap ferrites (EMC pass condition)

The product passed **with ferrite cores added to the host cable and the bridge
cable**. That makes them part of the tested configuration, so they are a
shipping requirement — see the obligations below, which are the part of this
easiest to get wrong.

### a. The part

**Würth Elektronik `74271111`** — WE-STAR-TEC snap ferrite with safety-key
technology (series 74271). Datasheet rev `010.000` (2025-09-10) is in this
folder as `Wurth-Elektronik-74271111_WE-STAR-TEC-snap-ferrite.pdf`
(8 pages, md5 `2ba11d6d4219e269ac0c007a03f8b618`). Sourced from Mouser.

| Property | Value |
|---|---|
| Material | 4W620, µi 620 typ., Curie temperature 150 °C typ. |
| Impedance | **175 Ω @ 25 MHz**, **316 Ω @ 100 MHz** (±25 %; test cable AWG26 / 100 mm, **1 turn**) |
| Applicable cable diameter | **3.5 – 5.0 mm** |
| Dimensions | 41.0 × 23.4 × 18.0 mm (±1.0) |
| Housing | grey plastic, flammability **UL94 V-0** |
| Operating temperature | −50 °C to +105 °C |
| RoHS | Compliant [2011/65/EU & 2015/863] |
| REACh | Conform or declared [(EC) 1907/2006] |
| Halogen free | Conform [JEDEC JS709B], [IEC 61249-2-21] |
| Automotive | AEC-Q200 qualified [Rev. E] |

The safety-key / STAR-CLIP fixation is the right choice for a compliance
accessory and worth keeping: it needs a tool to reopen, so it is not a snap-on
the user removes and loses. Say so in the manual rather than treating it as an
inconvenience.

### b. ⚠️ The 3.5–5.0 mm cable window is the real constraint

**Measure both shipped cables before ordering in quantity.** The datasheet's
impedance figures are for a cable filling the bore (AWG26, 1 turn). Below
3.5 mm the core does not clamp onto the jacket, the coupling drops and the
realised impedance is *not* the figure above; above 5.0 mm it will not close at
all. Many thin USB-C cables sit at 3.0–3.5 mm, so this is not a safe
assumption — and if a cable is out of range, the fix is to change the cable or
the ferrite, not to fit it loosely.

The user-substitution case is worse, because it fails silently: someone using
their own USB-C cable can land outside the window, or simply not fit the
ferrite, and the product is then in a configuration that was never tested with
nothing to indicate it.

### c. ⚠️ Where the lab put them is part of the result

Record the **placement** from the test report (and its photographs): which
cable, which end, the distance from the connector, and the number of turns —
the datasheet figures are for 1 turn. A production fitting instruction that
differs from the tested placement does not reproduce the pass. This is the
detail that is cheapest to capture now and impossible to recover later.

### d. Obligations that follow

1. **Ship two per keyboard** and include them in the packaging BOM and cost
   model — one for the host cable, one for the bridge cable.
2. **Document fitting in the user manual**: which cable, where, and that it is
   required for compliance rather than optional.
3. **Add to the RoHS appendix.** The ferrite is now a component placed on the
   market with the product, so its RoHS evidence belongs in the technical file.
   ⚠️ **Not yet wired up** — the PDF is in this folder but has no row in
   `parts-to-pdf-reference.xls`, so `PolyKybd-RoHS-Appendix.pdf` does not carry
   it. Adding the row means rebuilding the appendix in the same change (§1),
   and ⚠️ **do not re-run `update_xls_pages.py` to do it** — it recomputes every
   row and destroys the hand-curated page selections (it has done so once).
4. **Name it in the DoC's EUT description**, so the declaration covers the
   configuration that was actually tested.

### e. For a future board revision

A common-mode choke at the split connector, on the board, would remove the
dependency on a part the user has to fit correctly. The ferrite is a fix at the
cable, not at the source. Recording that as an option for a later revision, not
as a decision — the shipped v3.3 answer is the ferrites, and they work.
