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
7. **When the report arrives**: check which hardware revision it names (§6b — the
   sample reported `HW0x3200` while the boards are v3.3), and extract the
   **pre- and post-mitigation emission scans** plus the declared measurement
   uncertainty — four numbers per peak. The peaks are still visible with the
   ferrites fitted, so the attenuation they deliver is measurable per frequency,
   which is what sizes any replacement core (§7e)
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

### f. ⚠️ Cable substitution, and the lead that would make the cable not matter

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

### h. Other board-revision options

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
