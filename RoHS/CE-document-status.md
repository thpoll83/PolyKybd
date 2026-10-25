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
6. ✅ **EMC tested 2026-10-06, report EMC-700 v1.0 received 2026-10-23** (§6)
7. 🔴 **Close the unrated ESD air discharge (§6e).** Design and fit the covers
   for the reset button, boot button and LED openings (§6e2), then **write the
   justification into the technical file** — decided 2026-10-23 to close this by
   justification rather than a re-test, since the DoC is ours to declare. A
   re-test stays the fallback if challenged.
8. 🔴 **Add the enclosure/screws/PCB bonding to the production assembly (§6f).**
   It was a lab modification, it is what turned a restart-every-discharge into
   criterion A, and it is in no BOM or assembly note.
9. **Request the pre-modification emission scan from KEBA** (§6h) — without it
   the replacement-core sizing in §7e cannot be done at all.
10. **Update the ferrite count everywhere to FOUR** (§6c): packaging BOM, cost
    model (`polykybd-costing/scripts/gen_ods.py`, which also has no bridge-cable
    line), manual, and the DoC's EUT description.
11. **Fill in the DoC** (§1) — the manufacturer name and address are now known
    from the report (§6a), so only the GmbH registration formalities and the
    final report version remain.
12. Optional, for margin rather than compliance: identify the 6.25 MHz source
    (§6i) and the shield-bonding experiment (§7f–h). The pass stands at 1.35 dB
    without them; neither is required to ship.

---

## 6. EMC test — report EMC-700 v1.0 (KEBA, test 2026-10-06)

Issued 2026-10-16 by **KEBA Industrial Automation GmbH**, Reindlstraße 51, 4040
Linz. Order 105860810010. Tested and released by Christian Leitner / Andreas
Reiter. **Preliminary version 1.0** — received 2026-10-23.

Standards: EN 61000-6-3:2007+A1:2011 and EN 55032:2015+A11:2020 **Class B**
(emission), EN 61000-6-1:2007 and EN 55035:2017+A11:2020 (immunity).
Environment declared: **residential**.

### a. EUT identification — as the report records it

| Field | Value in the report |
|---|---|
| Type designation | PolyKybd Split72 |
| **Serial number** | **`POLYKYBD-SPLIT72-01/3.3/EMC-001`** |
| **Hardware version** | **3.3** |
| Software version | `PolyKybd-fw-v1.7.3` |
| Manufacturer | **PolyTasten GmbH** |
| Customer address | **Zieglerstrasse 2, 4470 Enns, Austria** |
| Parts of the system | left and right keyboard, joined by a short USB-C cable |
| Power supply | 5 VDC USB |
| Port | 1 × USB-C, signal port, shielded, **2 m used / 5 m max** |

✅ **The hardware revision is recorded as 3.3.** The lab took it from the
paperwork and the marking plate, not from the USB descriptor, so the
`device_version "3.2.0"` defect did **not** contaminate the report and there is
nothing to correct with the lab. The fix is still right — a shipping product
should not misreport itself — but it is no longer on the critical path.

✅ **The DoC's manufacturer placeholders are answered by this report**: it names
PolyTasten GmbH at Zieglerstrasse 2, 4470 Enns. §1 can be filled in from here.

### b. Emission — passed, but on 1.35 dB

30 MHz – 1 GHz, Class B, quasi-peak, limit 30 dB(µV/m) below 230 MHz. Three
peaks, all vertical polarisation at 100–107 cm:

| Frequency | Level | Limit | **Margin** |
|---|---|---|---|
| 31.26 MHz | 27.39 dB(µV/m) | 30.00 | 2.61 dB |
| **43.74 MHz** | **28.65 dB(µV/m)** | 30.00 | **1.35 dB** |
| 56.25 MHz | 25.66 dB(µV/m) | 30.00 | 4.34 dB |

1 GHz – 6 GHz: passed with no listed peaks and **no modification**.

⚠️ **1.35 dB is not margin.** The report states compliance under **ILAC-G08
shared risk** (cover page: results lie in the confidence interval with
probability >50 % and <95 %), i.e. **measurement uncertainty is not subtracted**,
and it publishes no uncertainty figure. Typical U for CISPR radiated emission in
this band is ~5–6 dB, several times the margin. So this is a formal pass whose
result would not survive a different chamber, a different sample, or normal
production spread. **Treat headroom at 43.74 MHz as a design objective, not a
solved problem.**

### c. ⚠️ The modification is FOUR ferrites, not two

§4.1.1, verbatim: **two** snap ferrites (WE 742 711 11) on the cable **between
left and right keyboard**, and **two** on the cable **between keyboard and the
host**. Four `74271111` per keyboard, two per cable. §7 is corrected
accordingly — this doubles the accessory cost and changes the packaging BOM and
the fitting instruction.

### d. Two configuration facts that are easy to miss

- ⚠️ **The host was a mobile phone in flight mode, not a PC.** "USB isolator and
  laptop had too high emission for class B measurement from 30 MHz – 1 GHz.
  Therefore they were replaced with a cell phone in flight mode." Standard
  practice for removing the associated equipment's own emissions, and legitimate
  — the PC is not the EUT. But the measured configuration is not the user's, and
  the two host-side ferrites were what that configuration needed.
- **The emission mode was the screensaver**, chosen because "the constantly
  changing images caused higher emission" — i.e. the lab selected the worst case
  it could sustain, and display activity is what drives the emission. Final
  measurement time was raised to 5 s.

### e. ⚠️ OPEN: ESD air discharge ±8 kV is NOT RATED at five points

This is the real outstanding item, and it is not the ferrites.

| Point | Criterion target | Result |
|---|---|---|
| Reset button right, Boot button right | B | **NR** — right keyboard restarts at some air discharges |
| Reset button left, Boot button left | B | **NR** — left keyboard restarts at some air discharges |
| **LEDs left** | B | **NR** — "left keyboard side, **red LED got permanently dark** after air discharge" |

The report's resolution: *"According to customer a cover will be placed at these
enclosure openings to avoid air discharges and resolve this issues. The covers
were not available during the test, therefore these tests are not rated."*

⚠️ **A permanently dark LED is not criterion B and not even C** — nothing about
it is self-recoverable or operator-restorable; it is damage.

✅ **DECIDED 2026-10-23: closed by justification, not by re-test.** An earlier
draft of this section claimed "a declaration cannot rest on an unrated test" and
made this the critical path. **That was wrong about whose decision it is.** The
DoC is the *manufacturer's* declaration; KEBA supplies evidence, PolyTasten
declares. Whether an unrated point is covered is ours to decide and document.
The decision is: **fit the covers (§6e2), seal the cavities so the openings do
not exist in the shipped product, and justify it in the technical file.**

Three conditions on which it rests:
1. ⚠️ **"The opening does not exist" must be literally true** — a remaining seam
   an 8 kV discharge could jump leaves the test point in existence and the
   justification fails. This is why the seam is bonded rather than merely fitted.
2. ⚠️ **Confine the change to filling the openings.** The other ESD points passed
   on the as-tested case (keycaps top and front criterion A; enclosure, screws
   and USB-C plugs A on contact). Moving wall thickness, the plate mounting, or
   introducing a seam elsewhere would change more of the tested article than
   intended.
3. ⚠️ **The justification goes IN THE FILE, not just into the product.** An `NR`
   plus a product with covers is not self-explanatory to a later reader.

✅ **The report already carries the intent**, which makes the package coherent
rather than an unsupported assertion — §4.3.2: *"According to customer a cover
will be placed at these enclosure openings to avoid air discharges and resolve
this issues."*

**What the file needs:** the insert geometry (drawing or CAD view showing the
flush fill and inner overlap), a photo of a fitted production unit, a
one-paragraph justification referencing report §4.3.2, and the assembly/QC step
(insert seated, bead continuous).

**The downside is bounded**, which is what makes deciding now reasonable: if
challenged, the fallback is an ±8 kV air-discharge re-test with covers fitted —
a short session, bookable then rather than now.

**Free improvement:** v1.0 is preliminary, so a final version is coming anyway.
If KEBA will strengthen that §4.3.2 sentence when they issue it — from "a cover
*will* be placed" to language describing the production configuration — it costs
nothing and makes the file materially better.

Note the openings are the **reset button, boot button and the LEDs**, i.e. exactly
the service/debug features. Covering them in production is a case-design task, not
an electronics one.

### e2. ✅ DECIDED: how the ESD openings get closed (2026-10-23)

The case is the **resin-printed** shell, and **resin printing is the shipped
process** — so the EUT's case *is* the production case. That keeps the argument
simple: the only difference between tested and shipped is the **addition** of
inserts, which removes an exposure path rather than changing the product. KEBA
is being asked to rate points that are no longer accessible, not to accept a
different EUT.

**Geometry — a "top hat", fitted from the INSIDE** (`led_fit_from = "inside"`,
the default; the file argued itself round this twice — see the record below):

| Feature | Why |
|---|---|
| Boss **fills the hole flush** with the outer face | no recess for the gun's 8 mm tip to enter, no edge to approach; also removes the shadowed recess over the LEDs |
| **Flange sits in a pocket cut into the PCB ledge** | the outer surface keeps exactly the geometry that was tested — no pocket, no seam ring round the window, and nothing for a blade or a fingernail to engage |
| **Adhesive bead around the seam** | see the three reasons below. Fitted from the inside it is also the *only* thing resisting a push from outside, so it is not optional |
| ≥1 mm in the transparent window | PMMA/PC ≈ 16–20 kV/mm, so 1 mm ≫ the 8 kV test; 0.5 mm is only 8–10 kV, i.e. at the test level |

⚠️ **NOT one opening for all three, and not one piece spanning them** — that was
the first idea and the board rules it out. The
three status LEDs are **D1, D5 and D6** (0805, all on `B.Cu`), and mapping the
board to the case SVG through the `Edge.Cuts` bbox — offset exactly
(−28.0995, −26.395) — puts **D5 and D6 8.0 mm apart on one wall, and D1 round
the corner on the next**, 33.2 mm away along the wall with a 93.4° corner between
them.

✅ **ONE part, three per half, six per keyboard.** The first version made D5+D6 a
single piece and D1 a second, different one. It does not need to: both walls are
**flat over the flange's footprint** (the left wall is dead straight at x = 2.448
from y 56.4 to 129.8; the top wall runs straight from (3.75, 131.07) to
(70.54, 135.04)), the wall is 2.9 mm thick at all three, and the windows are the
same 2.8 × 2.2 mm. So the three differ only by a rigid transform and one geometry
serves all of them — six identical, interchangeable chips, nothing handed and
nothing position-specific.

⚠️ **That forced the flange to shrink, and the two overlaps to split.** D5 and D6
are only **5.2 mm apart edge to edge**, so two flanges grown by the cavity's
3.5 mm would have each other's material inside them. `led_flange_overlap` = 2.4
is the **part's** overlap (0.4 mm between neighbours) while `led_pocket_overlap`
= 3.5 stays the **cavity's**, so the two pockets still merge into one recess
rather than leaving a 0.4 mm rib of ledge between them to snap off. The leftover
room is bond gap.

⚠️ **D1's slot is 3.4° off square to its own wall**, so the shared part is not
exactly congruent there: at a 0.10 mm clearance it fouled that cavity by
**0.0062 mm³**, about 13 µm on one diagonal. `led_insert_gap` is **0.12** for
that reason — 20 µm of extra seam buys an exact fit at all six. (A 0.0001 mm³
residue survives at 0.13 and 0.15 too, so it is CGAL noise on the coincident
faces, not a fit problem. Don't chase it.)

✅ **Built and verified.** `parts/case/case_polykybd_split72_lr.scad` carries the
`led_*` parameters and modules, `parts/case/led_inserts.scad` selects the parts,
and `parts/build_parts.sh led_ins` exports them. The pocket and the insert come
from the **same modules**, so they cannot drift. Section drawing:
`RoHS/led-insert-section.svg` (regenerate with `led-insert-section.py`, which
derives it from those same parameters); `RoHS/led-insert-fitted.svg` for the
before/after view from outside the case; `RoHS/led-insert-views.svg` for the four
views in place; and `RoHS/led-insert-parts.svg` for the part on its own, the
chain, the V-score and where they ride on the frame.

| | |
|---|---|
| Window, on the outer face | **2.8 × 2.2 mm** |
| Wall there | 2.9 mm (only 1.5 mm above the PCB underside) |
| Pocket depth | 1.0 mm |
| Overlap — cavity / flange | 3.5 mm (`led_pocket_overlap`) / **2.4 mm** (`led_flange_overlap`) |
| Wall left under the pocket | 1.9 mm |
| PCB ledge left at full width above the pocket | **0.5 mm** (`led_ledge_keep`) |
| **Clearance where the seam SHOWS** | **0.12 mm** per face (`led_insert_gap`) — flange in its pocket, and the boss's outer lip |
| **Clearance, buried** | **0.25 mm** per face (`led_window_gap`), behind a `led_boss_lip` = 0.6 mm lip |
| The part | **7.4 × 4.0 × 2.9 mm, 29.8 mm³** |
| **Air path through the seam** | **5.3 mm**, before the bond closes it |

✅ **They ride on the diffuser frame — there is normally nothing to print
separately.** A 32 mm³ chip is small enough to lose and fiddly to place one at a
time, and the keyboard already prints **two** clear-resin diffuser frames, one
per half, with exactly **three** inserts needed on each. So from frame **r1.2**
each `diffuser_frame_{left,right}.stl` carries its half's three as **one chained
row** on V-scored webs, hung off the **lower tip of the thumb-side branch** and
running **inboard** across the empty pocket under the main grid — the only 25 mm
of free web this part has. The anchor is derived in `gen_diffuser_frame.py` from
the segments it already knows (the longest non-rail one reaching below the grid),
so it follows the web if the web moves.

Three things make it cost nothing:

- **The frame's bounding box does not change** (−75.347…78.015, −41.724…58.963,
  −1.0…2.7, both halves) — the inserts fit inside the envelope, so the print
  plate is no bigger.
- **The row sits flange-down with its flange face level with the web's
  underside**, which puts every V-score **in the web plane**. The tabs are a flat
  extension of the web rather than something standing off it.
- **Each frame still exports as ONE shell** — 18914 facets, 0 degenerate facets,
  0 non-manifold edges. It gains **96.24 mm³** against a row that measures
  **96.61 mm³** on its own; the **0.37 mm³** difference is the single weld, which
  is the whole overlap there is. An intersection of the row against the frame's
  web and diffusers is **empty** (and a 1.5 mm displacement finds a collision, so
  the test is not passing for the wrong reason).

⚠️ **The parts are laid out with `dir`, never mirrored.** The left frame is an
exact x-mirror of the right, but the insert is the **same part on both halves** —
a mirrored one fits nothing. `led_insert_strip(n, dir)` lays the row towards −x
by translating, so the geometry is never reflected. `check_mirror()` still passes
because it compares volume and bounding box, which are unaffected.

⚠️ **The breakaway features are deliberately under the frame's own minimum wall,
so `check_frame.py` had to be taught to skip them.** `MIN_WALL` is 0.99 mm; the
score leaves 1.0 mm of **height** but the web is only as thick as the flange
(0.88), and the flange itself is 0.88. Measuring those as frame walls is
measuring the wrong part, so `inserts_zone()` excludes the box — and it gets that
box by **exporting the module**, not by recomputing its arithmetic, because a
second copy of numbers that all come from the `led_*` parameters would drift the
first time one moved. Under `--quick` the min-wall check prints SKIP rather than
silently passing on an un-bounded zone.

✅ **The connection is a full-height web V-SCORED ON ITS FACES — a PCB panel
score, not a waisted bar.** The web spans the height of the flange's end face
and the flange's thickness (3.26 × 0.78, held back by `led_tab_inset` — see
below), and the V is cut into its two **faces**, pinching the **thickness** to
**`led_score_t` = 0.3 mm** at mid-span. That is the axis you actually break
about: the two parts fold towards each other and the thin ligament fails in
tension, where a full-thickness waisted bar has to be twisted or cut. ⚠️ **1 mm
is not available in this direction** — the web is only as thick as the flange it
sits on, and the pocket has no room for more; at 0.3 the ligament is
3.26 × 0.3 = **0.98 mm²**, slightly *more* than the 0.78 the other axis left.

⚠️ **`led_tab_inset` = 0.05 is not cosmetic.** Flush with the flange's faces the
web's four planes are **coplanar** with the flange's, and the export comes out
with **8 degenerate facets and 8 non-manifold edges per joint** — 40 on the
six-up strip. The tell was indirect: OpenSCAD then refuses to boolean the
imported mesh at all (`Current top level object is empty` on an intersection
that plainly overlaps), which is what sent me looking. Held back 0.05 the strip
exports 0 degenerate, 0 non-manifold. Check it with an edge count, not with
`shells` — a welded-vertex shell count reports 1 either way.

⚠️ **`[0:n-2]` is NOT an empty range in OpenSCAD 2021.01.** At n = 1 it iterates
{0, −1}, so `led_insert_strip(1)` came out as a single insert with a web hanging
off **both** ends (x −5.285…5.285 instead of ±3.68). The loop is guarded with
`if (n > 1)`.

⚠️ **The anchor web is cut down to the frame stem's own width (2.0 mm), and
that is not a detail.** At the full 3.36 mm its root would overhang the 2.0 mm
stem by 0.68 a side — outside the notch the spacer already has for it — and foul
the spacer, which is the same mistake the insert row itself made before
`diffuser_frame_<side>_fitted()` existed. `led_v_tab(l, h)` takes the root height
for exactly this.

✅ **The three go on as ONE chained row, left of the thumb branch.** The branch
is the longest segment reaching below the grid — found in the generator by
vertical extent among the rungs and links, ⚠️ **deliberately excluding the
rails**, since the outermost rail drops 19 mm and would win on length while being
on the wrong side of the board entirely. The row hangs off that branch's **lower
tip** at y = −26.70 and runs inboard, x = −17.02…8.26 on the left half and
mirrored on the right. **0.83 mm clear** of everything else on the frame, against
the **0.75 mm** three separate inserts had — so chaining them costs nothing, and
it is one anchor to snap instead of three.

⚠️ **"A chained row does not fit here" was WRONG, and the way it was wrong is
the lesson.** The earlier sweep pinned the row's end to one rung and then moved
only `x`, which made the pocket look 0.17 mm too short. A free sweep over both
axes finds the row with room to spare. ⚠️ **A search that holds one degree of
freedom fixed reports the constraint it imposed, not the one the part has** —
and it reports it as a measurement, which is what made it believable. The sweep
that replaced it varies the row's `y` and its distance from the anchor together,
and lands where the two diffuser caps that bound the pocket — one at each end of
the row — come out **equal at 0.83 mm**, i.e. a true interior optimum: moving the
row either way along its own axis makes it worse.

⚠️ **The optimum is only 1.8 mm wide in `y`, so the generator MEASURES it rather
than trusting the two constants.** `INS_DY` (−0.70 mm below the tip) and
`INS_OVER` (0.50 mm of web root buried in it) place the row; the generator then
measures the row's rectangle against every stem capsule and every diffuser cap —
the same primitives it builds the frame from — prints the result, and **refuses
to emit a colliding frame**. Any change to the web topology that walks into the
row now fails the regeneration instead of printing a part fused to its carrier.

⚠️ **The anchor web is buried 0.5 mm in the branch's rounded tip, not butted
against it.** Butted, the root face is *tangent* to the stem — the singles got
away with the 5 µm overlap their 0.01 mm root section happened to give them, but
against a round tip there is no flat to sit on. Buried, the weld is a real
1.2 × 0.9 mm of material, and the score still sits at `led_tab_l()/2` = 0.8 mm
from the flange, which is **clear of the stem** — so it breaks at the score and
leaves 0.3 mm standing proud of the branch.

⚠️ **One anchor carries the whole 25.3 mm row, which is the one thing chaining
costs.** Three singles each had their own web, so a bad snap orphaned one part;
now a web that fails in the bag orphans all three. That is the trade accepted for
one snap instead of three, and it is why the root is buried rather than butted.

⚠️ **The free-space search that picked the first spot was wrong, and silently.**
It sampled the candidate box at a fixed 0.5 mm step with `range(int(w/0.5)+1)`,
which stops **0.36 mm short of the far edge** — so it never tested the corner
that was 0.24 mm inside a diffuser cup, and reported the placement as free.
Sample to both edges (`w*i/nx`), not by stepping from one.

`export/case/led_inserts.stl` remains as the standalone fallback: all six in a
row, 52.2 × 4.0 × 2.9 mm, one shell. The webs meet each part on the flange
**end** face, which is buried in the pocket, so no witness mark is ever on a
face that shows — and the part still seats with a stub at **each** end (the
difference against the cavity is a zero-volume coincident-face sliver, because
the web is exactly flush with the flange face).

⚠️ **The fit direction was argued round TWICE, and the objection that settled
it the first time was wrong.** Worth recording, because the wrong objection is
the kind that sounds decisive:

1. The first analysis said **inside**, and justified it with "seated harder by
   any pressure from outside". That is **backwards** — outside pressure pushes an
   inner flange *away* from the wall, into the cavity.
2. So it was flipped to **outside**, on the grounds that an inner flange "does
   not fit: the PCB underside is at z = 11.5 and the window top at 11.6, so it
   would foul the PCB ledge". That is **overstated**. Only the window's top
   **0.1 mm** is above the ledge top. An inner flange does not have to reach it,
   and it is not in the cavity at all — the pocket is cut *into* the ledge, so
   the flange lives inside the wall and never gets near the LED (which stands
   1.1 mm clear of the ledge's inner face in any case).
3. Back to **inside**, which is what was wanted, with the real constraint found
   by measuring instead of assuming: the pocket must stop **below the ledge top**,
   because that ledge is what the board rests on and it is only 1.25 mm wide.
   `led_ledge_keep` = 0.5 mm holds it back; slices of the built case confirm the
   wall still runs x −0.452…2.448 at z 11.1 and 11.44, i.e. full support, and
   −0.452…1.448 through the pocket, i.e. **the outer face is untouched**.

⚠️ **The retention trade is real and does not go away.** Fitted from the inside,
pressure from outside — a finger, an ESD gun tip — pushes the part *into* the
cavity and only the bond resists it. Fitted from the outside the flange would
bear on the pocket floor and the part would be captive against exactly that load
(and only the bond would resist a *pull*). The outside arrangement is still in
the file, one parameter away (`led_fit_from = "outside"`), and panel B of
`led-insert-section.svg` draws it. It was not chosen because the visible seam and
the untouched outer surface won; the price is that the bond is load-bearing, which
is why "insert seated, bead continuous" is a QC check rather than a design note.

✅ **The air path is NOT load-bearing — the report already shows why.** Table 14
records the tenting-kit breakout holes as **n.d., "no discharge possible"**, and
those are open 1 mm holes straight into the cavity. So a small opening is not by
itself a path; what made the LED and button openings rateable was a **conductive
target close behind them** (the LED sits 2.1 mm back, the switches are at the
opening). Once the window is filled with solid dielectric there is no such target,
and a hairline seam is far less of a path than the 1 mm hole that already failed
to conduct.

**Consequence worth recording so the geometry is not re-justified wrongly:** the
3.5 mm overlap and the bond stay, but **for mechanical reasons, not electrical
ones** — the overlap because below ~3.1 mm the two flanges stop merging into one
part (below), and the bond for retention. Anyone shrinking the pocket later
should know the ESD margin was never what sized it.

✅ **Two clearances, split by whether the seam can be SEEN — not by which
feature it is.** Once the seam stopped being the ESD argument, the fit could be
loosened to whatever makes the part go in. The first attempt split it by feature
(flange 0.10, boss 0.25) and that was right *for the outside fit*, where the
flange covers the window. **Fitted from the inside it is wrong, and the render
is what showed it**: with no flange on the outer face, the boss *is* the visible
seam, so a 0.25 mm clearance meant a 0.25 mm adhesive line round a 2.8 mm
window. The split is therefore:

- **`led_insert_gap` = 0.10 mm** — **every seam anybody can see**: the flange in
  its pocket, and the boss's outer lip. ⚠️ This is also the number to raise if a
  printed part will not push home; it is the only one that costs anything visible.
- **`led_window_gap` = 0.25 mm** — the **buried** remainder of the boss, behind a
  `led_boss_lip` = 0.6 mm lip. The boss has to travel the full 2.9 mm of wall and
  is the only feature that can bind on the way, so everything except the lip is
  relieved. The step also acts as a lead-in.

With `led_fit_from = "outside"` the flange covers the lip region entirely, so the
lip is a no-op there — one geometry, correct either way.

Two defects disappeared along the way, neither of which was the point:

- The boss used to end **exactly at the PCB underside** (z = 11.5) and could bear
  on the board. The buried part now stops at 11.35.
- The part had an **odd stepped top**, the boss standing 0.1 mm proud of the
  flange, because the flange carried the gap and the boss did not.

⚠️ The **visible face gets no clearance in the insertion direction** — the bands
take the gap off the far side only, so the part is flush with the case and the
slack ends up behind it. Do not add a gap there to "make it easier": it would
sink the insert below the surface.

✅ **The boss is RELIEVED under the ledge, and the distinction is the whole
point** (`led_ledge_relief`). The boss stood 0.47 mm above the flange's
shoulders across the full wall thickness, which put it **0.15 mm** under the
ledge the PCB rests on. The slice inboard of the wall-above-the-board (offset
`led_hi_r()`, case x 1.048 → 2.448) is now cut back to the flange top, so:

- the part clears the board by **0.62 mm** instead of 0.15, and its inner face
  is flat — no tab standing proud of the flange;
- the window is still plugged **1.50 mm deep from the OUTER face**, so what is
  left is a blind recess on the inside, not a path;
- it costs 1.5 mm³, 5% of the part.

⚠️ **Do NOT extend that relief outboard and shave the top flat.** The remaining
0.47 mm on the outer 1.5 mm is the **only thing closing the top of the window**:
taken off, it leaves **0.72 × 2.8 mm open** straight through 2.9 mm of wall to
the LED behind. Nor can it be met from the other side — raising the flange to
the boss needs the pocket top at 11.47, leaving **0.25 mm** of PCB ledge under
the board, a standing rib well under the 0.8 mm the print service allows. Flange
0.88 in a 1.0 mm pocket and a 1.25 mm ledge cannot both clear 0.8, and that is
what fixes the pocket top at 11.0. Figure: `RoHS/led-insert-top.svg`
(`led-insert-top.py`) draws both.

⚠️ **`led_hi_r()` is +`pcb_clearance`, not −.** `offset()` grows **outward**, and
above the board the wall stops 0.15 mm *outboard* of the outline (measured: the
wall is x −0.452…1.048 above z 11.5 against −0.452…2.448 below it). With the sign
wrong the band lands 0.3 mm inboard and the relief silently does nothing — which
is exactly what the first attempt did, and the only tell was that the measured
top of the ledge slab did not move.

✅ **The witness stub is why the cavity stays wider than the flange — verified,
not assumed.** Breaking a V-score leaves half the tab (0.8 mm) on the insert, and
on a middle insert there is one at **each** end. With the cavity grown by 3.5 mm
and the flange by 2.4 there is 1.22 mm of tangential room beyond the flange, so
the part still seats with both stubs on: `led_insert()` plus two
`led_v_tab_root()`s, placed at D5 and differenced against that cavity, exports as
**empty**. ⚠️ Widen the region box when re-running that test — with the default
±4 mm box the stubs poke out of the *test region* and it reports a false 0.49 mm³
protrusion.

⚠️ **The two overlaps pull in OPPOSITE directions — don't collapse them back
into one.** `led_pocket_overlap` (3.5, the cavity) wants to be **above** ~3.1 mm
so the D5 and D6 recesses merge; below that they separate and leave a thin rib of
ledge standing between them. `led_flange_overlap` (2.4, the part) wants to be
**below** 2.6 so two neighbouring flanges do not overlap each other, which is what
lets all six parts be the same. One number cannot satisfy both.

⚠️ **The pocket must not reach above the PCB underside** (z = 11.5): the wall is
only `case_wall_thickness` there, so a pocket would leave it too thin to print.

Verified rather than eyeballed. The ONE part was placed at each of the three
windows (`led_place_d5/d6/d1`) and differenced against that window's cavity:
**D5 and D6 export as empty, D1 leaves only the 0.0001 mm³ coincident-face
residue**. Four positive controls — 0.2 mm in ±y and ±z, and 1.4 mm tangentially
at D1 (where the flange has 1.1 mm of room by design, so a small shift proves
nothing) — all collide, so the test can still fail. Measured per face, by slicing
the part and the cavity in the same slab:

| slab | part | cavity | per face |
|---|---|---|---|
| boss lip (outer 0.5 mm of wall) | y 88.61–91.17, z 9.52–11.48 | y 88.49–91.29, z 9.4–11.6 | **0.12** |
| boss body (x 0.4–0.9) | y 88.74–91.04, z 9.65–11.35 | y 88.49–91.29, z 9.4–11.6 | **0.25** |
| flange (between the slots) | z 7.52–10.88 | z 7.4–11.0 | **0.12** |

The flange reading is the one that shows the fit is not over-constrained: it is
flush at the ledge's inner face (2.448) with the 0.10 mm standing at the pocket
floor, so the part is positioned by pushing it until the boss is flush from
outside and the print tolerance lands in the bond gap.

**The buttons need a different part from the LEDs, because they must move.** Any
clearance is an air path unless it is long or sealed, so the protection should be
a **flexible membrane or boot** (silicone/TPU) with the same inner flange: you
press *through* it and there is no gap at all. A rigid plunger with an inside
flange also works, but its protection is the length of the annular clearance —
a dimensional argument that degrades with tolerance, where the membrane is a
structural one. These points made the board **restart**, so prefer structural.
If the LEDs and buttons share a face, one moulded piece can do both regions with
no seam between them.

⚠️ **Three independent reasons the seam is bonded rather than merely fitted:**
1. **Resin is brittle** — an interference fit in the thin wall around an opening
   is exactly where an SLA part cracks.
2. **Printed dimensions vary** (resin batch, parameters, post-cure), so a
   tolerance-based gap argument is weak at the design stage.
3. ⚠️ **It fails silently in production.** A shell that prints slightly oversized
   leaves an insert loose; the keyboard works perfectly and the ESD margin is
   simply gone, with no functional symptom to catch it. Hence "insert seated,
   bead continuous" is a **QC check**, not a design note.

✅ **The top-hat pocket is free in resin** — a stepped recess for an inner flange
would need a side action or a split line in an injection tool. It also prints
same-day, so the geometry can be iterated before the re-test is booked.

**Rejected, with the number:** leaving a thin resin membrane over the LEDs
instead of a hole. Resin is ~15–20 kV/mm, so 0.4 mm gives ~6–8 kV — at the test
level, and fragile. 1 mm would be comfortable but will not pass useful light
through opaque resin. (A translucent shell resin would change this.)

**Close-out:** fit all five NR points, then **one re-test session** covering them
together, and get the rated result into the **final** report — v1.0 is
preliminary, which is the natural opening.

Already fine, so do not chase them: the lab worked round the whole case —
breakout holes returned "no discharge possible", and keycaps from top and front
were both criterion A. The five NR points are the whole exposure.

### f. A second modification was needed for contact discharge

±4 kV contact on *Enclosure left* and *Screws left* initially gave *"left keyboard
restarts at the every discharge"*. The report records: **"With modified EUT,
electrical connection established between metal enclosure, screws and PCB, the
test was passed with criterion A."**

✅ **"Metal enclosure" means the ALUMINIUM SWITCH PLATE** — and the test method
proves it rather than it being a guess: contact discharge is applied only to
*conductive* surfaces (insulating ones get air discharge), so with a resin shell
the "Enclosure right/left" rows in the ±4 kV **contact** table cannot be the
case. The only exposed metal is the plate and the screws.

⚠️ **That bonding is now a production requirement, not a lab fix**, and it is in
no BOM or assembly note. Make it a **deliberate feature** — a dedicated grounding
screw into a plated pad, or a spring contact — rather than a connection that
happens because a screw incidentally touches a pad. A bond that depends on
assembly variation passes the re-test and then varies per unit, which is the same
silent-failure shape as the loose insert in §6e2.

**C and F are complementary, not alternatives:** the bonded plate drains a
*contact* discharge safely, and the filled openings stop an *air* discharge
bypassing the plate to reach the PCB directly. Both are needed. The left half was
the one restarting at every discharge, so check whether the two halves currently
differ in how the plate is bonded — that asymmetry is a clue, not noise.

### g. Everything else passed

Radiated RF immunity 80 MHz–6 GHz (criterion A), EFT ±0.5 kV (B), conducted RF
150 kHz–80 MHz at 3 V (A), contact discharge indirect HCP/VCP (A). Surge: NA
(cable < 30 m, not leaving the building). Power-frequency magnetic field: not
performed, EUT has no magnetically sensitive component — informative only.

### h. ⚠️ The pre-modification scan is NOT in the report

Only the final, post-ferrite scan is published. So the per-peak pre/post delta
the §7e arithmetic needs — and the whole "which peaks does the cable own, how
much attenuation can be given back" method — **cannot be run from this
document.** Ask KEBA whether the pre-modification sweep was retained as a working
measurement; they ran it, since that is what prompted the ferrites.

### i. What the peaks are: odd harmonics of 6.25 MHz

31.25, 43.75 and 56.25 MHz are the **5th, 7th and 9th harmonics of 6.25 MHz** —
odd orders only, which is the signature of a **symmetric (50 % duty) square
wave**. The spacing is a clean 12.5 MHz. 6.25 MHz is `clk_sys`/32 (200/32) and
equally XIP/8 (50/8).

⚠️ **The per-key display SPI is ruled out**: `SPI_DIVISOR (CPU_CLOCK / 10000000)`
in `keyboards/polykybd/config.h` gives 200/20, i.e. a **10 MHz** SPI clock, whose
harmonics are 10/30/50/70 — not this comb. That is worth stating because display
activity *is* what the lab observed driving the emission, so the SPI clock is the
assumption everyone will make first. **The 6.25 MHz source is not yet
identified**; nothing in `keyboards/polykybd/` declares a 6.25 or 12.5 MHz clock.
Finding it with a near-field probe over the board is exactly what such a probe is
good for, and it would be the most direct route to real margin at 43.74 MHz.

---

## 7. Required accessory: FOUR snap ferrites (EMC pass condition)

The product passed **with two ferrite cores on the host cable and two on the
bridge cable — four in total** (report §4.1.1). That makes them part of the
tested configuration, so they are a shipping requirement — see the obligations below, which are the part of this
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

1. **Ship FOUR per keyboard** and include them in the packaging BOM and cost
   model — two on the host cable, two on the bridge cable, as tested.
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

### e. Open decision: a cable with the core built in

Preferred direction as of 2026-10-15, **not yet decided**. A clip-on the user
must fit, on the right cable, in the right place, is a compliance dependency on
the user performing a step correctly. A cable supplied with the core integrated
removes that. It also removes the 3.5–5.0 mm clamping window in §7b entirely,
since there is nothing to clamp.

**The two cables are not the same case.** Each half has two USB-C receptacles
(`poly_kybd_split72_{left,right}.kicad_sch`): the **host** port on net `USB`
(real D+/D−) and the **bridge** port on `USB2`, which carries `SERIAL_COM1` /
`SERIAL_COM2` — the 460800-baud UART, not USB at all.

- **Bridge cable: integrate it.** We supply this cable, the link is not USB (two
  signal pins plus ground, no USB-IF cable requirement to satisfy), and it is
  the cable whose UART made the ferrite necessary. A custom assembly with a
  moulded core is straightforward here.
- **Host cable: integration does not close the substitution hole.** Users bring
  their own USB-C cables, and a core moulded into ours does not travel to
  theirs. It closes the *forgot-to-fit-it* hole, which is a different and also
  real one. That is acceptable — a DoC covers the product as placed on the
  market with its supplied accessories — but do not buy it believing otherwise.

#### The equivalence criterion is narrow, and that is what makes it buyable

The suppression only has to hold **at the frequencies where this product is
actually marginal**, which the report's emission scans name. So the purchase
specification is a floor at two (or a few) stated frequencies, not a matched
curve — a specification a vendor can actually meet and evidence.

⚠️ **Needs BOTH scans — the pre-mitigation one as well as the final one.** The
peaks that are *close to the limit now* are the ones the Würth did not fully
fix; the peaks that are *comfortable now* may be comfortable **because** the
Würth is suppressing them hard. Matching only where the final scan is marginal
can re-expose a peak the core was quietly holding down, and the first evidence
of that is a failed retest.

✅ **The peaks are still visible with the mitigation fitted** (reported
2026-10-15, before the written report arrived). That is the good case: a level
at both ends means the attenuation the Würth delivered is *measurable* per
frequency, rather than something to be assumed. Had a peak been pushed under the
noise floor, its margin would have been unknowable and the only safe
substitution would have been an identical core.

#### When the report arrives: deriving the impedance floor from the measured dB

Pull four numbers **per peak**: pre-mitigation level, post-mitigation level, the
limit, and the lab's **declared measurement uncertainty**. They answer three
questions in order.

**1. Which peaks does the cable even own?** The per-peak delta says so. A peak
that dropped ~10 dB when the ferrites went on is common-mode current on the
cable. A peak that dropped ~1 dB is not — it is board or enclosure radiation,
no core will improve it, and equally **no core change can make it worse**. Those
drop out of the vendor specification entirely, which usually shrinks the problem
a long way.

**2. How much attenuation can be given back?** The post-mitigation margin to the
limit, *after* accounting for uncertainty. ⚠️ **Check whether the report's
margin is quoted before or after the declared uncertainty** (radiated at 3 m is
typically ~5–6 dB). If the pass was achieved on a margin smaller than the
uncertainty, there is effectively nothing to trade and the answer is to keep the
tested core.

**3. What impedance does that require?** Common-mode current is `V_cm / Z_cm`,
so adding a series core impedance `Z_f` attenuates by
`A = 20·log₁₀(|Z_cm + Z_f| / |Z_cm|)`, and radiated field tracks the current.
Measuring `A` with a known `Z_f` therefore **backs out the cable's own
common-mode impedance** — the term that is otherwise unknown:

```
k      = 10^(A/20)                    # measured, from the two scan levels
Z_cm   = Z_würth / (k - 1)            # the cable's common-mode impedance at f
Z_req  = Z_cm · (10^(A'/20) - 1)      # for the attenuation A' you must keep

  i.e.   Z_req = Z_würth · (10^(A'/20) - 1) / (10^(A/20) - 1)
```

Worked, with plausible numbers at 100 MHz (`Z_würth` = 316 Ω): a measured
`A` = 12 dB gives `k` = 3.98 and `Z_cm` ≈ 106 Ω. If 4 dB of the margin can be
spent, `A'` = 8 dB, and `Z_req` ≈ **160 Ω** — about half the Würth's impedance
is enough. That is the difference between a specialised core and an ordinary
one.

⚠️ **This is a sizing estimate, not an exact answer.** It adds magnitudes as if
both terms were in phase (fair where the core is lossy, which is the point of
4W620 at these frequencies, but not exact), and `Z_cm` is itself strongly
frequency-dependent — it is a resonant antenna impedance, not a constant. Apply
it with margin, and keep the floor expressed as a minimum over tolerance.

**The non-obvious consequence, worth knowing before negotiating with a vendor:**
attenuation saturates in `Z_f`, so **the peaks where the ferrite helped most are
the ones where there is most freedom to substitute a weaker core.** Where it
barely helped, `k − 1` is small and almost all of the original impedance is
needed to hold even a little attenuation — but those are also the peaks the
cable does not own, so they are not a core-selection problem in the first place.

⚠️ **Specify a floor from Würth's MINIMUM, not its typical.** The datasheet
figures carry ±25 %, so its guaranteed floor is 131 Ω @ 25 MHz and 237 Ω
@ 100 MHz. Worse, the *tested* unit could have been anywhere in that band: a
part at +25 % (219 Ω @ 25 MHz) against a replacement at −25 % (131 Ω) is a 40 %
unit-to-unit shortfall while both datasheets read "175 Ω typ". Write the
requirement as "≥ *Z* Ω at *f*, minimum over tolerance", and set *Z* from what
was tested rather than from a typical figure.

Two smaller points: equal **|Z|** is not equal attenuation if one core is
inductive at *f* and the other past resonance — ask for the R and X split, or at
least the curve, since dissipation is what suppresses; and the important
frequencies may **differ between the two cables**, because different sources
dominate each, so expect two acceptance criteria rather than one.

⚠️ **Ask the vendor for the core's PART NUMBER, not its description.** Cable
makers write "with ferrite core / EMI suppression" and publish nothing
measurable. Assembly houses commonly use Würth, Fair-Rite or Laird cores and
will name them if asked, and the core's own datasheet is where the curve lives.
**A vendor who will not name the core makes equivalence undocumentable**, and an
equivalence that cannot be documented is worth nothing in a technical file.

⚠️ **The cable is part of the EUT, not just the core.** Shield construction,
shield termination (360° vs pigtail vs none), length and geometry all change the
radiating structure. Matching the core while changing the cable holds one
variable and moves several.

#### The zero-EMC-risk version of the same idea

Have the **cable assembly house fit the Würth `74271111` itself**, in a position
given on the drawing. The suppressor is then literally the tested part: no
equivalence argument, no new uncertainty, nothing to retest, and the safety-key
fixation means the user cannot remove it. That buys nearly everything
integration is for — cannot be forgotten, lost or misfitted, no packaging item,
no manual step — and costs only the cosmetics of a clip-on lump instead of a
moulded bulge. Weigh it honestly against a delta retest.

#### Sequence this before the DoC is issued

The DoC is blocked on the GmbH anyway (§1), so the window is free, the report is
fresh and the lab still holds the setup data. Changing the supplied cable after
declaring means amending the declaration. **The question that decides it is one
for the lab**: what they would accept as an equivalence assessment for a
cable-plus-core change, and what a delta retest would cost (radiated only,
worst-case mode) rather than a full repeat.

### f. ⚠️ Cable substitution, and a LEAD — unverified — that would make the cable not matter

> ✅ **Gate answered by report EMC-700 (§6): the peaks ARE cable common-mode.**
> The lab's own fix was ferrites on the two cables, and it is what brought
> 30 MHz – 1 GHz inside Class B — so the emission is carried on the cables and
> these sections apply. Two qualifications: the **pre-modification scan is not in
> the report** (§6h), so the per-peak dB delta the §7e arithmetic needs is still
> missing and must be requested from KEBA; and the peaks are at **31–56 MHz**,
> lower than this analysis assumed, where the Würth core gives roughly 175–200 Ω
> rather than its 100 MHz figure. The shield-bonding lead is now worth pursuing
> on its merits, with the worst margin at 43.74 MHz being only **1.35 dB** (§6b).


**The user-substitution problem does not have a cable-side answer, so this is
where it has to be solved.** Three layers, because the first two bound the
problem and only the third removes it.

**1. The obligation is narrower than it looks.** 2014/30/EU requires the
apparatus to comply when properly installed and used for its intended purpose,
*per the instructions supplied*, and the DoC covers the product as placed on the
market with its own accessories. "Use the supplied cable" is a standard,
long-established clause. Three conditions make it legitimate rather than a
figleaf: a conforming cable is actually supplied, the requirement is stated
plainly in the instructions rather than buried, and it is reasonable to follow.
A user fitting their own non-conforming cable is operating outside the
documented configuration, which is their deviation. **This is the normal
situation for every USB peripheral on the market** — it is not a gap to feel bad
about.

**2. The two cables differ, and the bridge one is closable by construction.**
- **Bridge (`USB2`).** The user has no reason to own a spare, and the link is
  **not USB** — a UART on USB-C pins. So the decisive fix is **not to use USB-C
  for the bridge**: a keyed or locking 4-pin connector means no generic
  substitute exists, the supplied cable is the only cable, the core can be
  moulded in permanently, and it also removes the "bridge port plugged into a
  charger or a PC" class of problem. The cost is that a lost cable becomes a
  support ticket instead of a trip to any drawer. A v3.4 decision, but it is the
  real answer for this cable.
- **Host (`USB1`).** Cannot be closed. It is a USB-C peripheral and people use
  their own cables; that is the point of the connector. Only layer 3 helps here.

**3. The lead: BOTH cable shields are RF-floating.** Traced from the
schematics — `USB1` pin 13 (`SHIELD`) → **FB1** → GND, and `USB2` pin 13 →
**FB2** → GND, on every half of both boards. Both beads are
`GZ2012D601TF`, **600 Ω @ 100 MHz ±25 %**, and **nothing else sits on either
net — there is no parallel capacitor.** So at the frequencies in question each
cable shield is tied to board ground through roughly 600 Ω, i.e. not grounded at
RF at all. A shield that cannot carry common-mode return current back to the
board does not shield; it floats and is driven as an antenna. That is consistent
with a cable needing a clip-on core to pass.

⚠️ **The bead is deliberate, and the fix is not simply to remove it.** Grounding
a USB shield through a bead breaks ground loops and keeps host-side noise out —
it is in many reference designs. But the usual form of that trade-off carries a
**parallel capacitor** (typically 1–10 nF) exactly so the shield is isolated at
DC and audio while still bonded at RF. That capacitor is what is missing here.

**This is testable on existing v3.3 hardware for the price of a rework.** FB1 and
FB2 are 0805. In increasing aggression:
1. Tack **1–10 nF across the bead** — restores the RF bond, keeps the DC
   isolation. Try this first, and try it on the **bridge** first: that shield
   joins two halves of one product, so there is no third-party chassis in the
   loop and it is the cable whose UART made the ferrite necessary.
2. Replace the bead with a **0 Ω link** — a hard bond. ⚠️ On the **host** side
   this ties the PC chassis to keyboard ground and, with two cables, can form a
   host → left → bridge → right loop; it may trade radiated emissions for
   conducted emissions or susceptibility. That is presumably why the bead is
   there, so this is the second experiment, not the first.

Measuring the change needs only *relative* evidence to decide whether to pursue
it: a near-field sniffer probe and a spectrum analyser will show it, or ask the
lab for a short pre-compliance session, which is far cheaper than a retest.

⚠️ **This is a hypothesis to test, not a diagnosis.** The report's per-peak
deltas (§7e) decide it first: a peak that barely moved when the ferrites went on
is not cable common-mode, so the shield bond is not its lever either.

**If it holds, the dependency on a user-fitted part largely goes away**, which
is the only outcome that actually answers the substitution question. For v3.4,
pair it with **common-mode choke footprints on both pairs** — the host D+/D−
(full-speed USB at 12 Mbit/s has ample margin for one) and the bridge UART
(460800 baud, trivial) — fitted or linked out as the measurements dictate. A
footprint carried and not populated costs nothing.

### g. Should a cable shield float? — why the advice conflicts, and the rule

Searching this returns both answers with equal confidence, which is not because
the topic is unsettled but because **three different questions all get called
"should the shield float"**, and almost no source says which one it is
answering.

| The real question | Regime it assumes | Its answer |
|---|---|---|
| Ground loops, hum, chassis potential difference | DC to audio; cable electrically *short* | float one end |
| Radiated emissions and immunity | RF; cable electrically *long* | bond both ends, **locally** |
| Both at once | — | bond at RF, isolate at DC → **a capacitor** |

**What decides which regime you are in is cable length against wavelength**, and
that is arithmetic rather than opinion. λ/4 is 1.5 m at 50 MHz, 75 cm at
100 MHz, 37.5 cm at 200 MHz. A ~1 m cable is therefore electrically **long**
from roughly 50 MHz upward, and a shield bonded at one end only presents a
high-impedance open at the other: a resonant monopole, fed by whatever
common-mode voltage sits on the board. The "float one end" rule comes from audio
and instrumentation, where the frequencies of concern are tens of kHz and the
same 1 m cable is a ten-thousandth of a wavelength — electrically a lump, with no
antenna to speak of, so the loop genuinely is the only problem. **Repeating that
rule into a 30–300 MHz emissions problem applies the right answer to the wrong
regime, and that is the whole source of the disagreement.**

A second resolver is specific to this connector: in USB the shield is *intended*
as the common-mode return path, terminated to the plug shell at the cable end.
The differential pair returns on GND; containing the common mode is the shield's
job. Bonded is the designed-in state and floating is the deviation.

#### ⚠️ Our network is the INVERSE of the usual compromise

This is the part worth internalising, because it is not a question of camps:

| Network | At DC | At 100 MHz | Effect |
|---|---|---|---|
| Classic 1 MΩ ∥ 4.7 nF | ~1 MΩ | ~0.3 Ω | blocks the loop, **bonds** the RF |
| **Ours: `GZ2012D601TF` bead** | **~0.3 Ω** | **~600 Ω** | **permits the loop, blocks the RF** |

So the board is not using the float camp's answer or the bond camp's answer — it
is using the opposite of the compromise. It does have a coherent purpose: a bead
treats the shield as an *incoming* noise source and keeps the host's cable-borne
RF out of our ground. That is an **immunity**-oriented choice, and we have an
**emissions** problem. Same part, opposite direction. That reframes the question
from "which camp is right" into "which direction am I optimising", which is
answerable.

#### The bridge port is unambiguous — decide it without measuring

Every ground-loop argument needs **two independently grounded chassis**. The
bridge joins two halves of one product, from one supply, with no third chassis
anywhere. **There is no loop to break, so the float argument has no premise at
all there.** Bond `USB2`'s shield directly and locally. That one needs no
experiment.

The host port (`USB1`) is the genuinely two-sided case, because a PC chassis is
involved — so that is the one to settle by measurement, and the cap is the
compromise that serves both directions.

#### ⚠️ Position matters as much as value

From the layout: both shield nets run **~19–20 mm of 0.3–0.6 mm trace** from the
shell to the bead, with **no via on either net** (the shell's through-hole pads
are the only layer transition), and the nearest GND via is 2.5–3.5 mm beyond the
bead. That is roughly 6–8 nH, about 5 Ω at 100 MHz — **negligible against
600 Ω, so it is not a confounder for the measurement now.** But it becomes the
limiting term the moment the bead is addressed: a perfect bond 19 mm away down a
0.3 mm trace is not a bond.

So the two are different jobs:
- **The rework is an experiment.** Tack the cap straight across the bead; it
  answers the question. ⚠️ But expect it to under-read the available
  improvement, and do not conclude "the cap did not help" from a weak result.
- **The production fix is placement.** Bond the shell to the ground plane with
  multiple vias **at the shell pads**, and if DC isolation is wanted, put the
  capacitor there too — not 19 mm downstream.

#### Stop deciding, measure — three variants on one board

Consistent with the project's own rule that when the clever theories conflict
you do the mechanical, auditable thing and let the hardware decide:

| Variant | FB1 / FB2 | Tests |
|---|---|---|
| **A** | as built (bead only) | the baseline, already measured |
| **B** | bead ∥ 4.7 nF | RF bond with DC isolation kept |
| **C** | 0 Ω link | hard bond, the upper bound on what bonding buys |

Relative measurements are enough to choose (near-field probe and a spectrum
analyser, or a short pre-compliance slot). Run the bridge side first — it is
the unambiguous case and the cable whose UART made the ferrite necessary.
Whatever wins, **the answer is then a property of this board rather than of an
internet argument**, and it can be written into the v3.4 schematic with a
reason attached.

### h. How to measure the A/B/C comparison without owning a lab

The comparison above needs only **relative** evidence at two already-known
frequencies, which is a far weaker requirement than pre-compliance and opens up
options that would be useless for an absolute measurement. In rough order of
value, not cost:

1. **Ask the lab for a short engineering / open-chamber slot — this is the one
   to try first.** They already hold our configuration and the baseline scan, so
   their A/B/C is apples-to-apples in a way no bench measurement can be, the
   result is *citable* toward an equivalence argument, and the same conversation
   answers what they would accept for a cable change (§7e). One or two hours of
   engineering time competes directly with buying and learning an instrument,
   and it ends with an answer rather than an indication.
2. **Ask Würth's application engineering.** Free, expert, squarely their
   territory (they publish the *Trilogy of Magnetics*), and we are buying their
   part. Shield-termination and suppression-component selection is exactly what
   they support customers on. Costs an email.
3. **A tinySA.** ⚠️ **The basic model at ~$70 covers the entire band of
   interest** (100 kHz–960 MHz); our peaks are in 30–300 MHz, so the Ultra+ at
   ~$187 and the 7.3 GHz ZS407 at ~$279 are buying headroom we will never use.
   The Ultra's better dynamic range, noise floor and 4″ screen are real, so it is
   the better buy *if* one instrument is wanted for future bring-up — but not for
   this measurement.
   ⚠️ **Clones are rampant and indistinguishable** ("How to recognize a cloned
   tinySA — simple answer is: you can't"), so buy from the project wiki's own
   list. For Austria the EU entries avoid import and warranty friction:
   **Eleshop** (Europe), **GOTRONIK** (Poland), **Neven** (Central/Eastern
   Europe), **astroradio** (Spain). AURSINC is authorised, but the wiki names
   specifically **"Aursinc on Amazon"** rather than their own webshop.
   ⚠️ **TinyRFEquip and TinyRFLab are named on that page as claiming
   authorisation without having it** — a search summary asserted the opposite,
   i.e. that those two *were* the official sources. Read the wiki, not a summary
   of it.

   **⚠️ None of the bundles contain what this job needs, and one item would make
   the measurement worse:**
   - **An LNA is harmful here.** A current or near-field probe on an emitting
     cable delivers a strong signal; a 20 dB preamp in front of it drives the
     input into compression, and a compressed reading corrupts the *dB delta* —
     the only quantity we care about. LNAs are for weak distant signals.
   - **The "50 W DC–3 GHz 50 dB N-type attenuator" is the wrong part** — a
     transmitter power attenuator. What is wanted is a set of small **SMA step
     attenuators** (3 / 6 / 10 / 20 dB, ~€10–15 anywhere).
   - **The 400 MHz–8 GHz log-periodic antenna is the wrong band** and the wrong
     method (far-field).
   - A protective case is a few dollars and harmless.

   So: instrument + SMA step attenuators + an SMA pigtail for the home-made
   current probe below. ✅ **The step attenuators also buy the linearity check:**
   insert 10 dB and the reading must drop by exactly 10 dB. If it does not, the
   front end is compressing and every delta measured is understated. Run that
   once before trusting any A/B/C number.
4. **RTL-SDR dongle, ~€30** — ~24 MHz–1.7 GHz. 8-bit, limited dynamic range,
   overloads easily (add attenuation), but it will show a 10 dB change in a
   known peak perfectly well. Enough to decide whether the lead is worth
   pursuing at all.
5. **A university EMC lab.** The Austrian and German FH/TU labs do industry
   cooperation cheaply, sometimes free for an interesting project.

#### The self-measured procedure — PREPARED, NOT STARTED

⚠️ **Nothing below is committed, and none of it should begin before the report
is read.** Preference as of 2026-10-15 is to measure in-house rather than book a
lab slot, so the method is written down ready — but the report decides whether
there is anything here worth measuring at all (see the gate at the head of §7f).
If the peaks turn out not to be cable common-mode, this whole subsection is moot
and no instrument needs buying.

The intent, if it goes ahead: measure in-house to **decide**, and spend the lab
on the **chosen** design once rather than on exploring three. What this setup can answer: which variant
reduces common-mode current at the named frequencies, and roughly by how much —
enough to commit a v3.4 schematic. What it cannot answer: an absolute level, a
margin, or anything citable. Keep that line clear and the DIY result is sound.

**Shopping list** (beyond a spare `74271111`, which we have):

| Item | ~Cost | Why |
|---|---|---|
| tinySA basic (or Ultra) | $70 / $187 | 100 kHz–960 MHz covers 30–300 MHz |
| SMA step attenuators 3/6/10/20 dB | €12 | input protection **and** the linearity check |
| SMA pigtail + thin enamelled wire | €5 | the current probe |

⚠️ **Leave an attenuator permanently in line as a sacrificial part** — the tinySA
input is easy to destroy with static or overload.

**Build the current probe.** Wind **10 turns** of thin insulated wire through one
half of a spare snap core, spread evenly; solder the ends to an SMA pigtail
(centre and shield). Clamp it round the cable under test — the snap core makes it
genuinely clamp-on.

⚠️ **Why this does not disturb what it measures, which is counter-intuitive and
worth understanding before trusting it:** the same core bolted on a cable with
*no* winding is a suppressor presenting its full ~316 Ω. Wound and **terminated
in 50 Ω**, the secondary current opposes the flux and it reflects only
`50/N²` = **0.5 Ω** into the cable — negligible. Transfer impedance is
`50/N` = 5 Ω, so 10 µA of common-mode current reads ≈ −73 dBm, comfortably above
even the basic unit's floor.
⚠️ **Therefore never take a reading with the SMA disconnected**: an open winding
turns the probe back into a suppressor, and the measurement silently becomes a
measurement of the probe.

**Stimulus — it must be repeatable, or nothing else matters.** Emissions depend
on what the firmware is doing, so use a deterministic, continuous, hands-off
activity:
- **`KC_DEMO`** (settings layer, behind More) plays a 15-minute showroom loop
  until Esc — self-driving and identical every run. Good general case.
- For the **bridge** cable specifically, hammer the split link: a shell loop
  around `polyctl overlay send <files>` drives USB, the 460800-baud UART and 72
  SPI display writes together. That is the worst case and the one a bench test
  will not reach by itself.

**Procedure.** Tape the probe down, tape the cable route down, do not hold
anything, and do not disturb the geometry between variants — rework in place
rather than swapping boards.

1. **A** (as built) — record both peak levels.
2. **A again** — must reproduce within ~1 dB, or stop and fix the setup.
3. **B** (bead ∥ 4.7 nF) — record.
4. **A again** — the strongest form of the check: if A no longer reproduces, B's
   number is worthless.
5. **C** (0 Ω link) — record.

**Four validity checks, each of which has to pass:**

| Check | How | What a failure means |
|---|---|---|
| Linearity | insert 10 dB; reading must fall **exactly** 10 dB | front end compressing — every delta understated |
| Noise floor | unclamp the probe, keep it terminated | the measurement is instrument noise |
| It is ours | power the keyboard **off** | any peak that survives is ambient, not emission |
| Repeatability | the A → B → A sequence above | geometry drift; the deltas are noise |

⚠️ **The ambient check is not optional here, because FM broadcast occupies
88–108 MHz** and is strong in any city — right where a 50 MHz XIP-clock second
harmonic would sit. A probe on a cable will happily pick up a local transmitter
and present it as a beautiful stable peak. Power-off is the one-command
discriminator.

#### Measure CURRENT, not field — and the probe can be made from a spare ferrite

Common-mode current on the cable is what drives the radiated field (that is the
basis of the arithmetic in §7e), so measuring the current is both more directly
relevant and **far less geometry-sensitive** than a near-field field probe.

A clamp-on RF current probe is the standard tool and costs four figures new —
but a relative one can be made from **a spare `74271111`**: pass ~10 turns of
wire through the snap core, terminate in 50 Ω, feed the analyser, and clamp it
round the cable. Transfer impedance is roughly `50/N` ≈ 5 Ω, so ~10 µA of
common-mode current gives about −73 dBm, comfortably inside a tinySA's floor and
workable on an SDR.
⚠️ **Valid for relative comparison at a fixed frequency only** — the core's
permeability rolls off, so the response is not flat and the reading is not a
calibrated current. Leave the probe clamped in the same place for all three
variants so its own added impedance is a constant rather than a variable.

#### ⚠️ The dominant error source is geometry, not the instrument

A near-field reading moves many dB if the probe shifts a millimetre or the cable
is coiled differently, which is larger than the difference between a $30 dongle
and a real analyser. So:

- Tape the probe down and tape the cable route down. Do not hold either.
- **Measure A, then B, then A again.** If the second A does not reproduce the
  first, the measurement is worthless and no amount of instrument quality saves
  it. That single check is what makes a cheap setup trustworthy, and skipping it
  is how a cheap setup produces a confident wrong answer.
- Rework in place and re-measure rather than comparing two different boards;
  board-to-board variation is its own confounder.

### i. Other board-revision options

**Sanity-check the report's frequencies against the plausible sources** before
assuming the cable is the only lever — several are firmware-side:

| Source | Expect |
|---|---|
| `clk_sys` | 200 MHz and harmonics (400, 600 …) |
| XIP flash clock | `clk_sys / PICO_FLASH_SPI_CLKDIV` = **50 MHz** and harmonics (100, 150 …) |
| Per-key OLED SPI | derived from `clk_sys` via `SPI_DIVISOR` |
| Split UART | 460800 baud, broadband at low MHz |
| TLV62569 bucks | 1.5 MHz nominal and harmonics; **spreads and drops in Power Save Mode** |
| USB full-speed | 12 MHz |
| WS2812 data | ~800 kHz |

⚠️ If the marginal peaks turn out to be `clk_sys`-related, note that
**`-e POLYKYBD_SYS_CLK=125` is a documented, verified build-time lever** — it
produces an image byte-identical to the pre-200 MHz builds (see the firmware
repo's CLAUDE.md). It moves every derived clock with it, costs performance, and
would itself be a change to the tested configuration, so it is a last resort
rather than a free one. But it is worth knowing it exists before redesigning a
board.
