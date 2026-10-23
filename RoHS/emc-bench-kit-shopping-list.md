# EMC bench kit — shopping list

Equipment to investigate the **1.35 dB margin at 43.74 MHz** in test report EMC-700
(§6b of `CE-document-status.md`). All prices from **eleshop.eu**, captured
2026-10-23.

**What this kit answers:** *are the emissions carried on the cables, or radiated
from the board?* That one question decides everything else — whether the
shield-bonding experiment (§7f) is worth running, and whether the €345.95 probe
set is worth buying at all.

**What it cannot answer:** your actual margin. That is a calibrated quasi-peak
measurement in a semi-anechoic chamber, and no bench setup reproduces it. You
will be able to say *"this peak dropped 7 dB"*, never *"I am now at 4 dB"*.
The verdict always goes back to KEBA.

⚠️ **None of this is required to ship.** 1.35 dB is a pass and the DoC can be
issued on it. This is insurance against production spread and a future re-test.

---

## Buy now — €156.73 ex-VAT

| Item | Price | Why |
|---|---|---|
| [tinySA Ultra+ ZS-406](https://eleshop.eu/tinysa-ultra-spectrum-analyser-7918.html) | €125.00 | 100 kHz–6 GHz, 4″ display |
| [10 dB SMA attenuator](https://eleshop.eu/10-db-sma-attenuator.html) | €8.26 | the linearity check |
| [20 dB SMA attenuator](https://eleshop.eu/20-db-sma-attenuator.html) | €8.26 | knocks down a strong signal; sacrificial on the input |
| [SMA m–m cable, 100 cm](https://eleshop.eu/cable-sma-male-to-sma-male-100-cm.html) | €10.33 | probe to analyser |
| [SMA m–m cable, 215 mm RG-174](https://eleshop.eu/sma-male-to-sma-male-cable.html) **× 2** | €4.88 | **one gets cut up to build the current probe** |
| Current clamp: 10 turns on a spare `74271111` | free | §7h |

⚠️ **Eleshop prices are excl. VAT.** The round-number test confirms it: €44.59 →
€53.95, €159.46 → €192.95, €27.23 → €32.95. With the GmbH VAT number, intra-EU
**reverse charge** applies, so the ex-VAT figures are likely what is actually paid.
Confirm at checkout.

### Why the Ultra and not the others

| | | |
|---|---|---|
| [tinySA basic](https://eleshop.eu/tinysa-spectrum-analyser.html) | €44.59 | 0.1–960 MHz. Covers 31–56 MHz fine — viable if minimising spend |
| **[Ultra+ ZS-406](https://eleshop.eu/tinysa-ultra-spectrum-analyser-7918.html)** | **€125.00** | **the pick.** Bigger screen, faster sweep and better dynamic range all matter when moving a probe one-handed and watching the display |
| [Ultra+ ZS-407](https://eleshop.eu/tinysa-ultra-zs-407-spectrum-analyser.html) | €159.46 | €34 for 6→8 GHz. The 1–6 GHz emission result passed with **no peaks**, so this buys nothing |

⚠️ **Clones are indistinguishable** — the project's own page says *"How to recognize
a cloned tinySA: simple answer is: you can't"*. Eleshop is on its
[official list](https://tinysa.org/wiki/pmwiki.php?n=Main.Buying); TinyRFEquip and
TinyRFLab are named there as claiming authorisation **without having it**.

---

## Defer — buy only if the clamp says the source is on the BOARD

| Item | Price | Note |
|---|---|---|
| [Tekbox TBPS01-TBWA2](https://eleshop.eu/tekbox-tbps01-tbwa2-set.html) | €345.95 | probes + wideband amp. ⚠️ **confirm it is the 20 dB, not 40 dB** — see below |
| [Tekbox TBPS01-TBHDR1](https://eleshop.eu/tekbox-tbps01-tbhdr1-emc-near-field-probe-set-and-rf-pre-amplifier.html) | €363.64 | probes + RF preamp, set stated 30 kHz–1.5 GHz |
| [Tekbox TBPS01 bare](https://eleshop.eu/emc-near-field-probe-set.html) | €204.95 | same probes, no amp — but the amp is what makes it work at 43 MHz |

**Either bundle is right; they are €18 apart and differ only at the extremes**
(HDR1 reaches lower, WA2 higher), neither of which matters here. **Decide on gain,
and less is better**: a tinySA overloads easily, and 40 dB with a probe moving from
a quiet spot to a hot one will compress — which corrupts exactly the dB comparison
being made. 20 dB is plenty.

⚠️ **An LNA is wanted *here* and harmful on the cable clamp.** A loop's output
scales with frequency, so at 43 MHz a small loop is weak and a preamp is standard.
On a current clamp the signal is already strong and a preamp only causes
compression. Verify either way with the 10 dB insert.

---

## Deliberately not buying

| Item | Price | Why not |
|---|---|---|
| [Owon EMI probe set](https://eleshop.eu/owon-emi-probe-set.html) | €275.00 | starts at **30 MHz** — our peaks sit on the bottom edge where a loop is least sensitive |
| [Rigol NFP-3](https://eleshop.eu/rigol-nfp-3-near-field-probe-kit.html) | €469.00 | same 30 MHz problem, more money |
| [GW Instek GKT-008](https://eleshop.eu/gw-instek-gkt-008-emi-probe-kit.html) / [COM-Power PS-400](https://eleshop.eu/com-power-ps-400.html) | €845 / €545 | 2–4× the price, no advantage at 43 MHz |
| [Tekbox TBAS2 attenuator set](https://eleshop.eu/tekbox-tbas2-sma-attenuator-termination-set.html) | €161.16 | its 20 dB and 30 dB are **terminations**, not through attenuators; characterised parts we do not need for relative work |
| [Tekbox TBESDT2 ESD target](https://eleshop.eu/tekbox-tbesdt2.html) | €1,192 | verifies an **ESD gun's** waveform. Needs the gun *and* a multi-GHz scope. Does nothing for the cover design (§6e2) |
| [RF Explorer power limiter](https://eleshop.eu/rf-explorer-power-limiter.html) | €49.54 | see the DC block below |
| Tekbox RM141 / RG-142 cables | €18.90–€110 | precision/armoured, specified to 18 GHz. At 60 MHz they buy nothing |
| All N-type attenuators | — | wrong connector; the tinySA is SMA |
| ZA-048 / telescopic antennas | — | far-field, wrong bands |

**Optional, genuinely cheap:**
[DC block SMA, €12.40](https://eleshop.eu/power-limiter-sma-female-to-sma-male.html) —
the €49.54 limiter's cheap equivalent. **Not needed**: a loop cannot pick up DC and
a ferrite clamp is transformer-coupled, so both are inherently DC-isolated. Worth it
only if the analyser is later connected straight to a circuit node.
[SMA female calibration set, €12.36](https://eleshop.eu/sma-female-calibration-set.html) —
VNA kit, but contains a **50 Ω terminator** (clean noise-floor reference) and a
**female-female through** (adapter).

---

## Building the current probe

Wind **10 turns** of thin insulated wire through one half of a spare `74271111`
snap core, spread evenly, and solder the ends to the centre and shield of a cut
215 mm SMA lead. Clamp it round the cable under test.

⚠️ **Why it does not disturb what it measures** — counter-intuitive, and worth
understanding or it will be mistrusted: the same core with **no** winding is a
suppressor presenting its full ~316 Ω. Wound and **terminated in 50 Ω**, the
secondary current opposes the flux and it reflects only `50/N²` = **0.5 Ω** into
the cable. Transfer impedance is `50/N` = 5 Ω, so 10 µA of common-mode current
reads ≈ −73 dBm.

⚠️ **Never take a reading with the SMA disconnected** — an open winding turns the
probe back into a suppressor, and the measurement becomes a measurement of the probe.

---

## Before trusting any number

Full procedure in `CE-document-status.md` §7h. The four checks, each of which must pass:

| Check | How | A failure means |
|---|---|---|
| Linearity | insert 10 dB at a **low** level first — that delta *is* the attenuator's true value — then repeat at the working level | different delta = compressing; every reading understated |
| Noise floor | unclamp the probe, **keep it terminated** | measuring instrument noise |
| It is ours | power the keyboard **off** | any surviving peak is ambient |
| Repeatability | **A → B → A** | geometry drift; the deltas are noise |

The ambient band is kinder than first assumed: the peaks are at **31–56 MHz**, well
below FM broadcast at 88–108 MHz. Still check — 27 MHz CB and the 50 MHz amateur
band are nearby.

Stimulus must be repeatable: **`KC_DEMO`** plays a 15-minute self-driving loop, and
for the bridge cable a shell loop around `polyctl overlay send` drives USB, the
460800-baud UART and 72 SPI writes together. The lab used **screensaver mode**,
because changing images gave the highest emission.
