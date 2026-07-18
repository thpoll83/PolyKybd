# PolyKybd Split72 — Risk Analysis (GPSR)

Regulation basis: **General Product Safety Regulation (EU) 2023/988 (GPSR)**. Supporting safety
reference standard: **EN 62368-1** (safety of audio/video, IT and communication equipment). The product
is powered from USB (5 V SELV) only, so the Low Voltage Directive does not apply; there is no radio
function (RED not applicable) and no battery.

Manufacturer: Thomas Pollak · Project R26_06 · Revision covered: PCB v3.2 / case r1.7 / firmware
[TO CONFIRM version]. This analysis must be re-checked whenever a supplier, part, mechanical revision or
firmware version changes (batch-level traceability).

## 1. Product and intended use
- **Product:** PolyKybd Split72 — a wired USB split mechanical keyboard for personal computers, with
  per-key 0.42" OLED displays, addressable RGB LEDs and MX-compatible hot-swap key switches, on an
  aluminium top plate in a 3D-printed or CNC case.
- **Power/interface:** powered and operated over USB-C at 5 V DC (SELV); the two halves are joined by a
  USB-C cable; the left half connects to the host PC by USB-C. No mains connection, no battery, no radio.
- **Intended users / environment:** general consumers and enthusiasts; indoor dry office/home use
  (residential, EN 55032/55035 Class B).
- **Supply form:** assembled unit **and/or kit**. When supplied as a kit, the information needed to build
  a compliant product (assembly, ESD, correct parts) must ship with it.

## 2. Method
Each hazard is rated before and after mitigation using Severity (S) × Probability (P), each 1–3
(1 = low, 3 = high). Risk R = S × P. R ≤ 2 acceptable · 3–4 acceptable with mitigation/instruction ·
≥ 6 requires design change. The goal is residual R ≤ 4 for all hazards.

## 3. Hazard assessment

| # | Hazard | Cause / scenario | Effect | S | P | R (pre) | Mitigation | S | P | R (res) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Electric shock | Contact with live parts | None — 5 V SELV from USB only, no mains, no battery | 1 | 1 | 1 | Design is SELV; no user-serviceable mains parts | 1 | 1 | 1 |
| 2 | ESD / immunity | Static discharge to USB, OLEDs, LEDs | Temporary malfunction / display glitch; possible component damage | 2 | 2 | 4 | ESD protection on USB (TPD4E05); EMC immunity to EN 55035; manual advises normal ESD care | 2 | 1 | 2 |
| 3 | Overheating / fire | Fault or short | Burns / fire | 3 | 1 | 3 | Low power (5 V, <~2.5 W typ.); USB host current limiting; RoHS/flammability-rated PCB; no battery | 2 | 1 | 2 |
| 4 | Sharp edges | Aluminium plate / machined case edges | Cuts / abrasion | 2 | 2 | 4 | Deburr / chamfer edges; note in manual; QC check | 1 | 1 | 1 |
| 5 | Small parts (choking) | Keycaps, switches, screws, stems detach or handled by a child | Choking if swallowed by small children | 3 | 1 | 3 | Not a toy; "keep away from children under 3" warning; small-parts note on packaging | 3 | 1 | 3 |
| 6 | Mechanical (pinch / snap) | Assembling hot-swap switches, closing case | Minor pinch, broken part | 1 | 2 | 2 | Assembly instructions; go-slow guidance | 1 | 1 | 1 |
| 7 | Liquid ingress | Spill onto keyboard | Short / malfunction; in worst case skin contact with wet electronics (still 5 V) | 2 | 2 | 4 | Manual: keep liquids away, disconnect and dry before reuse; no ingress rating claimed | 2 | 1 | 2 |
| 8 | Kit assembly (mechanical) | Inserting hot-swap switches/keycaps, connecting FPCs — **no soldering** (the base product ships without solder-in optional components) | Minor pinch; poor build | 1 | 2 | 2 | Build guide; hot-swap design (no soldering); handle with care | 1 | 1 | 1 |
| 9 | Non-compliant build / modification | User substitutes non-equivalent parts or modifies the design | Product may not meet EMC/safety | 2 | 2 | 4 | Kit ships full compliant-build instructions, BOM and firmware; warning that modifications void conformity | 2 | 1 | 2 |
| 10 | Cable strain / trip | USB cable pulled or tripped over | Connector damage; trip | 1 | 2 | 2 | Standard USB-C; manual routing advice | 1 | 1 | 1 |
| 11 | Prolonged use / ergonomics | Extended typing | RSI-type discomfort | 2 | 2 | 4 | Split/tenting design aids posture; manual advises breaks and proper setup | 2 | 1 | 2 |
| 12 | Foreseeable misuse | Wrong/again over-spec USB power, disassembly, outdoor/wet use | Damage / malfunction | 2 | 2 | 4 | Manual states intended use, 5 V USB only, indoor dry use; warnings against misuse | 2 | 1 | 2 |

## 4. Materials / substances
All electrical parts and the PCB are RoHS-compliant (see the RoHS compliance matrix and appendix).
Skin-contact materials (case, plate, keycaps, stems) are common polymers and anodised/plain aluminium;
no known sensitisers beyond ordinary use. Collect Material Safety Data Sheets for any coatings/adhesives
used and file them with the technical documentation. No battery, no hazardous substances beyond RoHS scope.

## 5. Conclusion
With the mitigations above, all residual risks are ≤ 4 (mostly 1–2). The main residual points are
(a) small-parts/choking → addressed by the "not a toy / keep from young children" warning, and (b) kit
assembly (mechanical only, **no soldering** — optional solder-in parts are not shipped) and possible part
substitution → addressed by the build guide and the "modifications void conformity" notice.
No hazard requires a design change. Outputs feed the **safety notice**, the **user manual**, and the
**labelling** (warnings, ISO 7010 symbols).

*Open items:* confirm firmware version covered; add any coating/adhesive MSDS; the examiner supplied a
risk-analysis template — transfer this content into it if a specific format is required.
