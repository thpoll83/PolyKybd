# Task (for Claude Code): author the remaining CE technical-file documents

You have access to the full PolyKybd repo(s). Produce the written CE documents below for the
**PolyKybd Split72** — a **wired USB (5 V) mechanical split keyboard, RP2040-based, no wireless**.
Pull real details from the repo (schematics, `RoHS/parts-to-pdf-reference.xls`, `poly_kybd/` KiCad
project, firmware) rather than inventing them. Cross-check against the existing files in `RoHS/`
(`CE-Technical-File-Checklist.md`, `RoHS-decisions-log.md`, the schematics/PCB/appendix PDFs).

Deliverables (put them in `RoHS/` or a new `CE/` folder; A4, consistent with the other PDFs):

## 1. General description & product identification
- Product name, model/type designation, variants (left/right halves), photos/renders.
- Intended use and environment (indoor/office), user profile.
- Electrical ratings: powered from USB 5 V; typical/max current; interface (USB-C, HID).
- Physical: dimensions, weight, materials of enclosure/plate.
- Firmware name + version and what it does at a high level.

## 2. Theory of operation
- Block diagram + narrative: RP2040 MCU, key matrix / per-key SSD1306 OLED + WS2812 LED chain,
  74-series buffers, shift registers, power path (USB 5 V -> TLV62569 buck / SY6280 load switch),
  ESD protection (TPD4E05), crystal, inter-half connection. Reference the schematic sheets by name.

## 3. List of harmonised standards applied (with justification)
- EMC emissions: **EN 55032** (multimedia equipment, Class B). Immunity: **EN 55035**.
- Note EN 61000-3-2/3-3 not applicable (USB-powered, not mains-connected).
- RoHS: **EN IEC 63000:2018** (already satisfied by the RoHS appendix/matrix).
- State the class and rationale; leave exact edition years as fields to confirm against the current OJEU list.

## 4. Risk assessment
- (a) EMC standards-selection / risk rationale.
- (b) **GPSR (EU 2023/988) safety risk analysis**: enumerate hazards (electrical at 5 V, thermal,
  mechanical/sharp edges, small parts/choking, materials/skin contact, foreseeable misuse, cable
  strain), likelihood/severity, and mitigations. Use a simple risk table.

## 5. User manual / instructions with safety & disposal info
- Setup/use, do's and don'ts, cleaning, warnings, and **WEEE disposal** (crossed-out wheelie-bin).
- Written for the consumer; include space for translations into the languages of the countries of sale.

## 6. Marking & label artwork
- Product/packaging label containing: **CE mark** (correct proportions), manufacturer name & address,
  importer / EU Responsible Person (GPSR) if applicable, model/type, batch or serial number, **WEEE**
  symbol, and any warnings from the risk assessment. Provide print-ready artwork (SVG/PDF) + placement.

## Context / status (already done, in `RoHS/`)
- RoHS technical documentation per EN IEC 63000: `PolyKybd-RoHS-Compliance-Matrix.xlsx`,
  `PolyKybd-RoHS-Appendix.pdf`, `parts-to-pdf-reference.xls`, `RoHS-decisions-log.md`.
- Schematics: `PolyKybd-Schematics.pdf`. BOM: `schematics/parts.csv`.
- PCB layers: `PolyKybd-PCB-Layers.pdf` (copper x4, mask, paste, outline). **Silkscreen layers were not
  rendered here** — regenerate all layer plots cleanly with `kicad-cli pcb export pdf` from
  `poly_kybd/poly_kybd_split72_left.kicad_pcb` and `..._right.kicad_pcb` (KiCad is available to you),
  including the silkscreen, and refresh `PolyKybd-PCB-Layers.pdf`. Also export a fabrication/stack-up
  drawing and an assembly drawing (component placement + reference designators).
- A draft **EU Declaration of Conformity** exists (`RoHS/EU-Declaration-of-Conformity.docx`) with
  placeholder fields — fill in manufacturer/RP details and final standard editions.

## Notes
- Keep everything A4. Where a legal fact must be confirmed (standard editions, Responsible Person,
  address), leave a clearly-marked `[TO CONFIRM]` field rather than guessing.
- The main external gap remains **EMC test reports** (EN 55032 / EN 55035) from a test lab — reference
  where they will slot into the file.
