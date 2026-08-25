# RoHS evidence — parts to certificates

Generated from **`parts-to-pdf-reference.xls`** (the source of truth) on 2026-08-24.
Regenerate rather than hand-edit; edit the `.xls` and re-derive.

Standard applied throughout: **Directive 2011/65/EU as amended by (EU) 2015/863.**

All 43 referenced evidence files are present in `RoHS/`. Every **populated** part has
evidence; the only rows without a certificate are unpopulated or bare-copper items
(`DBG1`, `DBG3`, `H1-H9`, `J38`, `JP1`, `SW1`, `TP1`, `TP14`) — headers not fitted,
mounting holes and test points covered by the PCB substrate evidence, and `SW1` is DNP.

| Ref(s) | Part | Qty | Mfr | LCSC | RoHS evidence in `RoHS/` | Notes |
|---|---|---:|---|---|---|---|
| **Capacitors** | | | | | | |
| `C1_1-C1_36` | 2.2uF 0603 25V | 36 | Samsung | C57895 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| `C2,C3_1-C3_36,C5_1-C5_36,C6_1-C6_36,C24,C25,C30-C32` | 1uF 0402 16V | 114 | Samsung | C52923 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| `C2_1-C2_36` | 2.2uF 0603 16V | 36 | Samsung | C23630 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| `C3,C8` | 27pF 0402 16V | 2 | Samsung | C86287 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| `C4,C10` | 4.7uF 0805 25V | 2 | Samsung | C1779 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| `C4_1-C4_36,C33,C34` | 4.7uF 3216 25V Tantalum | 38 | Vishay |  | `vishay-rohs-20250901.pdf` |  |
| `C5,C11` | 6.8pF 0603 50V | 2 | Samsung | C318672 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| `C6,C12-C14,C26` | 10uF 0805 16V | 5 | Samsung | C15850 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| `C9,C15-C23` | 100nF 0402 16V | 10 | Samsung | C1525 | `2304140030_Samsung-Electro-Mechanics-CL05A105KA5NQNC_C52923.pdf` |  |
| **Diodes / LEDs** | | | | | | |
| `D1` | Red 0805 C84256 | 1 | NationStar | C84256 | `2409272203_Foshan-NationStar-Optoelectronics-NCD0805R1_C84256.pdf` |  |
| `D1_1-D1_36,D12` | 1N4148WSX | 37 | Shenzhen JingYang | C6423741 | `2405091035_Shenzhen-JingYang-1N4148WSX_C6423741.pdf` |  |
| `D2` | 1N5819WS | 1 | Hottech | C191023 | `ROHS-2025-HottechElectronics-CTI-A225024736310100101.pdf` | CTI report 17-Apr-2025, covers SOD-323; supersedes ROHS3HOTTECH.pdf (SOD-123 only) |
| `D5` | Green 0805 C2297 | 1 | Hubei KENTO | C2293 | `C2297.pdf` |  |
| `D6` | Yellow 0805 C2296 | 1 | Hubei KENTO | C2296 | `1806151129_Hubei-KENTO-Elec-KT-0805Y_C2296.pdf` |  |
| **Ferrite beads** | | | | | | |
| `FB1,FB2` | GZ2012D601TF | 2 | Sunlord | C1017 | `2310301640_Sunlord-GZ2012D601TF_C1017.pdf` |  |
| **Connectors** | | | | | | |
| `J1-J36` | FH34SRJ-14S-0.5SH | 36 | JUSHUO | C324724 | `FH34SRJ-14S-0.5SH(50)_CL0580-1252-8-50_SpecSheet_0000414509.pdf` | (also the alternative) |
| `J37` | FH34SRJ-12S-0.5SH | 1 | Hirose | C424659 | `FH34SRJ-12S-0.5SH(99)_CL0580-1253-0-99_SpecSheet_0000414526.pdf` |  |
| `J39` | FH12-30S-0.5SH | 1 | Hirose | C506793 | `FH12-30S-05SH.pdf` |  |
| `USB1,USB2` | TYPE-C-31-M-12 | 2 | Hroparts | C165948 | `2410010003_Korean-Hroparts-Elec-TYPE-C-31-M-12_C165948.pdf` |  |
| **Inductors** | | | | | | |
| `L1,L2` | 2.2uH | 2 | SXN | C133191 | `2108131530_SXN-Shun-Xiang-Nuo-Elec-SMMS0420-2R2M_C133191.pdf` |  |
| **RGB LEDs** | | | | | | |
| `LED1-LED36` | XL-3030RGBC | 36 | Xinglight | C5349958 | `2402181502_XINGLIGHT-XL-3030RGBC-WS2812B_C5349958.pdf` |  |
| **Resistors** | | | | | | |
| `R1,R2` | 22 0603 | 2 | Yageo | C108405 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R10,R11,R30` | 390k 0603 1% | 3 | Yageo | C114659 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R12,R17` | 150k 0603 | 2 | Yageo | C114660 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R13` | 12k 0603 | 1 | Yageo | C114659 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R14` | 680k 0603 | 1 | Yageo | C137690 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R18` | 10M 0603 | 1 | Yageo | C141675 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R1_1-R1_36,R15,R20,R25` | 10k 0402 | 39 | Yageo | C60490 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R22,R23` | 27 0603 | 2 | Yageo | C137753 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R24` | 2M2 0603 | 1 | Yageo | C137747 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R3,R4,R7,R9` | 5.1K 0402 | 4 | Yageo | C144745 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R5,R6,R16,R19,R21` | 1k 0402 | 5 | Yageo | C144789 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| `R8` | 5.6K 0402 | 1 | Yageo | C163457 | `2304140030_YAGEO-RC0603JR-0710ML_C141675.pdf` |  |
| **Switches / sockets** | | | | | | |
| `SW2,SW3` | EVQPUC02K | 2 | Panasonic | C79174 | `panasonic_rohs_2ma_2000379.pdf` |  |
| `SW_K_1-SW_K_36` | Kailh CPG151101S11-16 | 36 | Kailh |  | `2208291600_Kailh-CPG151101S11-16_C5156480.pdf` |  |
| **ICs** | | | | | | |
| `U1,U2` | TLV62569DBVR | 2 | TI | C141836 | `TexasTLV62569DBVR.pdf` |  |
| `U10` | RP2040 | 1 | Raspberry Pi | C2040 | `rp2040-rohs.png` |  |
| `U11,U26` | TPD4E05U06DQAR | 2 | MSKSEMI |  | `C2836386-TPD4E05U06DQAR-MS.pdf` |  |
| `U12-U25` | 74AHC1G125GW,125 | 14 | Nexperia |  | `Nexperia - Statement on RoHS 20241008.pdf` |  |
| `U3` | SY6280AAC | 1 | Silergy | C55136 | `ROHS-2024-SilergyCorp.pdf` |  |
| `U4-U8` | 74HC595BQ | 5 | Nexperia |  | `Nexperia - Statement on RoHS 20241008.pdf` |  |
| `U9` | BY25Q64ESCIG(R) | 1 | BOYAMICRO | C50176394 | `2006180000_BOYAMICRO-BY25Q64ESCIG-R_C50176394.pdf` | was Winbond W25Q64JVXGIM / winbond-W25Q64JV-rohs.png; part changed 2026-08 |
| **Crystal** | | | | | | |
| `Y1` | 7M12000044 | 1 | TXC | C93114 | `TXC-7M12000044.pdf` |  |

## Notes on shared certificates

Several rows point at one manufacturer document covering a whole series — this is
deliberate, not a mismatched reference:

- **Samsung MLCCs** all cite `…CL05A105KA5NQNC_C52923.pdf`, which contains a
  series-wide part list. Verified to include `CL05C270 J B 5NNN` (= `C86287`, the
  `C3,C8` part), so the 2026-08 switch of `C3,C8` from FH `C1557` to Samsung `C86287`
  needed **no new evidence**.
- **Yageo resistors** all cite `…YAGEO-RC0603JR-0710ML_C141675.pdf` for the same reason.
- **Nexperia logic** (`U4-U8`, `U12-U25`) cites the company-wide RoHS statement.

## Two rows carry history worth keeping

- **`U9`** — changed 2026-08 from Winbond `W25Q64JVXGIM` (evidence was
  `winbond-W25Q64JV-rohs.png`) to BOYAMICRO `BY25Q64ESCIG(R)` / `C50176394`.
- **`D2`** — evidence replaced 2026-08-24. The previous `ROHS3HOTTECH.pdf` (2020) was
  accepted on the belief that it covered the 323-series package; its sample list is
  `SOT-23, 323, 523, 723, … SOD-123`, where the `323` belongs to the **SOT** run, so
  **SOD-323 was never covered**. The 2025 CTI report lists `SOD-123/323/523/723`
  explicitly. See `RoHS-decisions-log.md` for the two limitations to be able to answer
  (tested as a whole; applicant is Shenzhen Hottech vs LCSC's Guangdong Hottech).
