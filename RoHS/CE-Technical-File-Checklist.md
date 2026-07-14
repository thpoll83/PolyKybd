# PolyKybd — CE Technical File Checklist

Scope note: this covers the **whole CE technical file**, not only RoHS. It assumes PolyKybd is a
**wired USB (5 V) mechanical keyboard with no radio/wireless function**. If that is wrong, see the two
"depends" items in the directive table — they change the required documents.
Last updated: 2026-07-13. (Regulatory summary; not legal advice — an EMC test lab or notified/assessment
body can confirm the exact standards list for your build.)

## 1. Which EU legislation applies

| Legislation | Applies to PolyKybd? | Why |
|---|---|---|
| **EMC Directive 2014/30/EU** | **Yes** | Any electronic apparatus that can emit or be affected by disturbance. Self-declared (no notified body needed) using harmonised standards. |
| **RoHS Directive 2011/65/EU** | **Yes** | Category 3 electronic equipment. Restricted-substance compliance. (This is the part already built.) |
| **General Product Safety Regulation (EU) 2023/988 (GPSR)** | **Yes** | Applies to consumer products since **13 Dec 2024**. Requires risk analysis, technical documentation, safety instructions and an **EU Responsible Person**. |
| **WEEE Directive 2012/19/EU** | **Yes** | Waste-electronics marking (crossed-out wheelie-bin) + national registration. |
| **REACH (EC) 1907/2006** | **Yes (light)** | SVHC substance obligation; a short statement usually suffices. |
| **Low Voltage Directive 2014/35/EU** | **No** (as assumed) | Only covers equipment powered at 50–1000 V AC / 75–1500 V DC. USB 5 V is below scope — **unless you ship or specify a mains USB power adapter**, which then needs its own LVD compliance (normally the adapter maker's). |
| **Radio Equipment Directive 2014/53/EU** | **No** (as assumed) | Only if the product has wireless (Bluetooth/RF). **If any wireless is added, RED replaces the EMC route and adds radio + health/safety testing.** |

## 2. Technical file contents (what an assessor expects)

Legend: ✅ have it · ⬜ still to produce.

- ✅ **Bill of materials** — `schematics/parts.csv` and `RoHS/parts-to-pdf-reference.xls` (designators, values, manufacturer part numbers, quantities).
- ✅ **Circuit schematics** — `RoHS/PolyKybd-Schematics.pdf` (all distinct sub-blocks, both halves).
- ✅ **RoHS technical documentation** per **EN IEC 63000:2018** — `RoHS/PolyKybd-RoHS-Compliance-Matrix.xlsx` + `RoHS/PolyKybd-RoHS-Appendix.pdf` (supplier declarations/test reports mapped to the BOM) + `RoHS/RoHS-decisions-log.md`. This is exactly what EN IEC 63000 asks for.
- ⬜ **PCB layout / fabrication drawings** — *yes, these are required* (see §3).
- ⬜ **General description & product identification** — one page: product name, model/type, photos, intended use/environment, electrical ratings (USB 5 V, current draw), interfaces, firmware version.
- ⬜ **Theory of operation / functional description** — a short text explaining how the schematic works (MCU, key matrix, LED chain, OLED per key, power path), enough to understand the drawings.
- ⬜ **List of harmonised standards applied** — with justification, e.g.:
  - EMC emissions: **EN 55032** (multimedia equipment, Class B for home/office).
  - EMC immunity: **EN 55035**.
  - (EN IEC 61000-3-2/3-3 harmonics/flicker normally **not** applicable — USB-powered, not mains-connected.)
  - RoHS: **EN IEC 63000:2018**.
- ⬜ **EMC test report** — emissions + immunity, from an (ideally accredited) EMC lab. *This is the main external item still missing* — see §4.
- ⬜ **Risk assessment** — (a) EMC risk/standards-selection rationale, and (b) a **GPSR safety risk analysis** (hazards: electrical, thermal, mechanical/sharp edges, small parts/choking, materials, foreseeable misuse).
- ⬜ **EU Declaration of Conformity (DoC)** — a single declaration listing all applicable directives (EMC + RoHS + GPSR reference) and the standards used; model text in EMC Annex IV and RoHS Annex VI. See §5.
- ⬜ **User instructions & safety information** — in the language(s) of each country of sale; include intended use, warnings, and disposal (WEEE) info.
- ⬜ **Marking & label artwork** — see §6.
- ⬜ **EU Responsible Person / traceability** — GPSR requires an EU-established responsible person (manufacturer, authorised rep, or importer) named on the product/packaging/docs. Needed if you are outside the EU or selling cross-border.

## 3. PCB layers — yes, include them
The technical file's "design and manufacturing drawings and schemes of components, sub-assemblies and
circuits" is understood to include the **PCB artwork**, so add, for each board (left and right):

- **Copper layer plots** — every layer (top, any inner layers, bottom).
- **Silkscreen** (top/bottom) and **solder-mask** layers.
- **Fabrication/drill drawing** — board outline, dimensions, drill map, and **layer stack-up** (materials, thicknesses, finish — ENIG / lead-free HASL, matching your PCB RoHS certs).
- **Assembly drawing** — component placement with reference designators (top/bottom), which ties the BOM to physical positions.

These are normally exported straight from KiCad (plot the layers to PDF + the fabrication/stack-up
report). One combined, A4-normalised "PCB documentation" PDF per side would mirror how the schematics
PDF is organised. I can assemble that for you the same way if you export the layer PDFs.

## 4. The main gap: EMC testing
Self-declaration under the EMC Directive still requires **evidence** of compliance — in practice an
**EMC test report** (radiated/conducted emissions to EN 55032 and immunity to EN 55035) from a test lab.
This is the one item that generally cannot be produced from existing files; budget for a lab booking.
The report + the standards list + risk assessment then support the DoC.

## 5. EU Declaration of Conformity
One page, signed, typically containing: manufacturer name & address; product identification
(model/type, and enough to trace it); "this declaration is issued under the sole responsibility of the
manufacturer"; the object of the declaration; the list of Union legislation and harmonised standards
applied; place & date of issue; name/signature of the authorised person. Keep the DoC + technical file
for **10 years** after the last unit is placed on the market.

## 6. Marking & labelling
- **CE mark** (correct proportions), on the product and packaging.
- **Manufacturer** name and postal address; **importer/EU Responsible Person** details if applicable.
- **Model/type** identifier and a **batch or serial number** for traceability.
- **WEEE** crossed-out wheelie-bin symbol.
- Any warnings required by the risk assessment.

## 7. Suggested order of work
1. Export the **PCB layer/fab/assembly PDFs** from KiCad (I can then compose + A4-normalise them).
2. Write the **general description + theory of operation** (short).
3. Book **EMC testing**; get the report.
4. Draft the **risk assessment** (EMC + GPSR) and **user manual**.
5. Finalise **marking/label** artwork and confirm the **EU Responsible Person**.
6. Issue the **EU Declaration of Conformity** and assemble everything into the master technical file.

## Sources
- EMC Directive 2014/30/EU (text): https://eur-lex.europa.eu/eli/dir/2014/30/oj/eng
- EMCD guide & technical-file contents: https://f2labs.com/technotes/2017/04/07/ce-marking-and-the-technical-file/ · https://cetecomadvanced.com/en/news/emc-directive/
- USB power & Low Voltage Directive scope: https://f2labs.com/technotes/2020/03/04/my-product-is-recharges-or-powers-from-a-usb-cable-do-i-need-to-comply-with-the-low-voltage-directive-2014-35-eu/
- EN 55032 / EN 55035 (multimedia equipment EMC): https://www.element.com/resources/articles/what-you-need-to-know-about-en-55032-and-55035-cispr-32-and-35 · https://ecocomply.ai/blog/emc-harmonised-standards-list-2014-30-eu
- RoHS technical documentation, EN IEC 63000:2018: https://getenviropass.com/2018-12-15-en-iec-63000-for-product-assessment/ · https://www.tuv.com/regulations-and-standards/en/eu-en-iec-63000-2018-new-harmonized-standard-to-demonstrate-rohs-compliance.html
- GPSR (EU) 2023/988 technical file & Responsible Person: https://prodlaw.eu/2025/01/gpsr-focus-risk-analysis-and-technical-documentation-template/ · https://digital.nemko.com/insights/gpsr
- EU Declaration of Conformity contents: https://www.compliancegate.com/electronics-declaration-of-conformity/
- PCB fabrication/assembly documentation: https://www.protoexpress.com/kb/fabrication-assembly-files/
