# Analog FM rendition: bill of materials

Built one chain at a time. Each chain is checked against its datasheet and against published designs that use the exact part. Key parts and their stock are in [sourcing.md](sourcing.md); datasheets are in [docs/datasheets/analog-fm/](../../docs/datasheets/analog-fm/) and `plan-c/`.

Rules carried over from Plan C: every passive is populated with a best-guess value (no empty pads), and every part needs deep stock at JLC or a second route.

Reference designs are read with a small connectivity script on their KiCad files. It traces wires, labels and power symbols to list what sits on each pin of the part.

## Chain order

| # | Chain | Status |
|---|---|---|
| 1 | J1 USB-C receptacle and USB ESD | **Done** |
| 2 | U3 3.3 V regulator and bulk capacitors | **Done** |
| 3 | U1 STM32U535 support (VDDA filter, clock source) | **Done** |
| 4 | Y2 20 MHz reference oscillator | **Done** |
| 5 | Oscillator, varicap, buffer, lock gate | **Done** |
| 6 | U2 ADF4002 PLL and loop filter | — |
| 7 | PE43711 attenuator and DIP switch | — |
| 8 | FL1 low-pass, DC block, U5 RF switch, J2, D5 | — |
| 9 | U4 Si4705 receiver (QFN) | — |
| 10 | DAC output filter | — |
| 11 | Controls: thumbwheels, slider, BOOT button, LED | — |
| 12 | Test pads and power budget | — |

## Chain 1: J1 USB-C receptacle (Korean Hroparts TYPE-C-31-M-12)

Pinout from the HRO drawing (`J1_HRO_TYPE-C-31-M-12.pdf` p1): A1/A12/B1/B12 GND, A4/A9/B4/B9 VBUS, A5 CC1, B5 CC2, A6/B6 D+, A7/B7 D−, A8/B8 SBU, four shell legs. The wiring is the same as Plan C chain 6 (USB Type-C R2.5) and chain 11 (ESD).

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| R1 (A5 CC1) | Yageo RC0402FR-075K1L | 5.1 kΩ 1% to GND | C105872, 2,164,069 | Type-C R2.5 Table 4-28 p246 |
| R2 (B5 CC2) | Yageo RC0402FR-075K1L | 5.1 kΩ 1% to GND | C105872 | Fitted on both CC pins (Plan C decision) |
| D3, D4 (CC1, CC2) | TI TPD1E05U06DPYR | ESD | C436349, 75,576 | Plan C chain 11 |
| U6 (D+, D−, VBUS) | ST USBLC6-2SC6 | ESD array | C7519, 42,385 | Plan C chain 11; D+ on I/O1, D− on I/O2, VBUS pin 5 |
| A6–B6, A7–B7 | — | Joined at the connector, stub ≤ 3.5 mm | | Type-C R2.5 p76 |
| A8, B8 (SBU) | — | Not connected | | |
| Shell legs | — | GND | | |

Reference designs with this exact connector:

| Pin | IphoneFM | LinHT handheld radio ([M17-Project/LinHT-hw](https://github.com/M17-Project/LinHT-hw), connectors sheet, J12) | echoplayer ([amachronic/echoplayer](https://github.com/amachronic/echoplayer), r1-rev1.1 USB sheet, J2) | Beepy ([sqfmi/beepy-hardware](https://github.com/sqfmi/beepy-hardware), schematic PDF) | Verdict |
|---|---|---|---|---|---|
| CC1, CC2 | 5.1 kΩ each to GND | 5k1 each (R46, R47) | 5.1 kΩ each (R14, R15) | 5.1K each (R2, R3) | Match |
| D+, D− | Pairs joined, through USBLC6 to U1 | Pairs joined, through USBLC6-2SC6 (U8) | Pairs joined, to the USB PHY | Pairs joined, to the RP2040 via its 27 Ω resistors | Match (27 Ω is an RP2040 requirement, not ours) |
| VBUS | USBLC6 pin 5, then U3 input | USBLC6 pin 5 and a 220 Ω ferrite | 100 nF to GND | To the charger | Match; see note |
| SBU | Open | Open | Open | — | Match |
| Shell | GND | GND | GND | — | Match |

No gaps. Note: echoplayer puts 100 nF on VBUS at the connector. Ours has U3's 1 µF input capacitor (chain 2) close by, and the phone on a short cable is the only source. No change.

## Chain 2: U3 AP2112K-3.3 regulator

Circuit as Plan C chain 5 (AP2112 DS39724 p1–2), already compared against three published designs in reference-check.md (U3: RP2040 Stamp, Beepy, PicoROM; no gaps). What changes here: two capacitor part numbers that JLC can't supply.

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| U3 | Diodes AP2112K-3.3TRG1 | 3.3 V 600 mA LDO, SOT-25 | C51118, 17,723 | VIN 1, GND 2, EN 3, NC 4, VOUT 5 |
| C (VIN 1) | **Samsung CL10B105KO8NNNC** | 1 µF X7R 16 V ±10% 0603 | C59782, 234,150 | Replaces TDK C1608X7R1C105K080AC (JLC: 157, minimum buy 206). Same spec: Samsung code 10 = 0603, B = X7R, 105 = 1 µF, K = ±10%, O = 16 V, 8 = 0.8 mm (catalog p4–5) |
| C (VOUT 5) | Samsung CL10B105KO8NNNC | 1 µF X7R 16 V 0603 | C59782 | AP2112 is stable with ≥ 1 µF (p1) |
| EN 3 | — | Tied to VIN | | Internal pull-down (p2) |
| U1 VDD bulk | **Samsung CL21A106KOQNNNE** | 10 µF X5R 16 V ±10% 0805 | C1713, 836,963 | Replaces Yageo CC0805KRX5R7BB106 (JLC: 0). Samsung code 21 = 0805, A = X5R, 106 = 10 µF, Q = 1.25 mm (catalog p4–5) |

- Load on 3V3 (estimate, to be summed in chain 12): MCU, Si4705, ADF4002 (5–6 mA, ADF4002 p3), 20 MHz oscillator (≤ 5 mA, YSO110TR p1), PE43711, oscillator and buffer. Well under the AP2112's 600 mA. The LED runs from VBUS.
- Start-up (foldback, 50 mA into the rail capacitance) is re-checked in chain 12, once every block's capacitors are known.
- DC bias: the Samsung catalog gives no DC-bias curve. The output's ≥ 1 µF stability minimum (p1) is met with margin, because U1's 10 µF and every bypass capacitor sit on the same 3V3 rail. The 1 µF input capacitor follows the datasheet's typical circuit (p2), which sets no minimum for it.

## Chain 3: U1 STM32U535 support

Power pins as Plan C chain 4 (DS14217 Figure 23 power scheme p127, Figure 37 NRST p212), already compared against four published designs in reference-check.md (U1). Changes for this rendition:

1. **VDDA ferrite added** (reference-check U1 gap 1). VREF+ is bonded to VDDA on this package, so VDDA noise goes straight into the DAC audio. The CAN-node reference design feeds VDDA through a 600 Ω ferrite, and that is adopted here.
2. **Clock from the 20 MHz reference oscillator.** Y2 drives PH0-OSC_IN in HSE digital bypass mode, and the PLL runs the system clock from it. DS14217 allows a 4–50 MHz external clock with OSC_IN high ≥ 0.7 × VDD and low ≤ 0.3 × VDD (p184–185); Y2 gives ≥ 90% and ≤ 10% of VDD (YSO110TR p1). ST's own Nucleo-U545 offers the same external-oscillator-into-PH0 option (UM3062 p27). The audio sample clock and the 19 kHz pilot become crystal-accurate. USB stays on HSI48 locked to USB start-of-frame by the CRS, as in Plan C, so the ROM bootloader still works with no crystal.
3. **32.768 kHz crystal removed.** Plan C needed Y1 only to give the receiver its reference clock through LSCO. The Si4705 accepts any RCLK from 31.13 kHz to 40 MHz and divides it down with REFCLK_PRESCALE (Si4704/05 p14; AN332 p37–38), so U1 passes 20 MHz to it from **PA8 (MCO)** (DS14217 p46, p114) with a prescale of 610 (REFCLK = 32,787 Hz). Accuracy improves from Plan C's −92 ppm worst case to ±20 ppm. Y1 and its two 5.6 pF capacitors are gone.

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| U1 | ST STM32U535CEU6 | MCU, UFQFPN48 | Global sourcing (DigiKey 1,394) | |
| VDD 24, 36, 48 (×3) | **Samsung CL05B104KO5NNNC** | 100 nF X7R 16 V 0402 | C1525, 38,027,442 | One per pin. Replaces Murata GRM155R71C104KA88J (39,537) with JLC's basic 100 nF: code 05 = 0402, B = X7R, 104 = 100 nF, O = 16 V (Samsung catalog p4–5). This part is used for every 100 nF on the board |
| VDD bulk | Samsung CL21A106KOQNNNE | 10 µF X5R 16 V 0805 | C1713 | Chain 2 |
| FB2 (3V3 → VDDA) | **Murata BLM15AG601SN1D** | 600 Ω ±25% at 100 MHz, ≤ 0.11 Ω DC, 0402 | C76884, 1,227,301 | `FB_Murata_BLM15AG_ENFA0018.pdf` p1. VDDA draws far less than its current rating, so the DC drop is negligible |
| VDDA 9 | Samsung CL05B104KO5NNNC + CL10B105KO8NNNC | 100 nF + 1 µF, after FB2 | C1525 / C59782 | DS14217 Figure 23 (p127) |
| VCAP 22 | Murata GRM21BR71C475KE51L | 4.7 µF X7R 16 V 0805 | C408144, 10,473 | Plan C chain 4; meets ≥ 10 V and ±20% (p127) |
| NRST 7 | Samsung CL05B104KO5NNNC | 100 nF | C1525 | Internal 40 kΩ pull-up (p211) |
| BOOT0 (PH3) 44 | Yageo RC0402FR-0710KL | 10 kΩ pull-down; SW2 to 3V3 | C60490, 5,222,786 | Plan C chain 4 |
| VBAT 1 | — | Tied to 3V3 | | Plan C chain 4 |
| PH0-OSC_IN | — | From Y2 through R4 (chain 4) | | HSE digital bypass |
| PH1-OSC_OUT | — | Free GPIO | | Not needed in bypass mode |
| PA8 (MCO) | — | 20 MHz to U4 RCLK | | Series resistor in chain 9 |

Removed from Plan C: Y1 (ABS07 32.768 kHz) and its two 5.6 pF capacitors; LSCO on PA2; TIM16 on PB8 (the LV2285 76 kHz drive). The full U1 pin map is redone when the schematic is drawn.

## Chain 4: Y2 20 MHz reference oscillator (YXC OT322520MJBA4SL)

One CMOS oscillator is the frequency reference for the whole board. It drives U1 (system clock and audio timing), U2 (PLL reference), and through U1's MCO, U4 (receiver reference).

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| Y2 | YXC OT322520MJBA4SL | 20 MHz CMOS, 1.8–3.3 V, 3.2 × 2.5 mm | C725987, 4,055 | Pins: 1 tri-state, 2 GND, 3 OUT, 4 VDD (YSO110TR p2) |
| Pin 1 (tri-state) | — | Tied to VDD | | High or floating enables the output (p1); tied, not left floating |
| Pin 4 VDD | Samsung CL05B104KO5NNNC + CL21A106KOQNNNE | 100 nF + 10 µF to GND | C1525 / C1713 | The maker's test circuit (p4) |
| R4 (pin 3 → U1 PH0) | Yageo RC0402FR-0733RL | 33 Ω series | C138002, 6,823,372 | Source termination at Y2 to damp ringing on the line to U1 (best guess; the Nucleo uses a series R and C on its external clock path, UM3062 p26) |
| C (pin 3 → U2 REFIN) | Samsung CL05B103KB5NNNC | 10 nF X7R 50 V 0402, series | C15195, 5,730,112 | AC coupling. REFIN self-biases at AVDD/2 through 100 kΩ (ADF4002 Figure 10, p8; note 3, p4). HELIOS couples REFIN through 10 nF (C25) |

- Level at REFIN: Y2 swings 0 to 3.3 V, inside REFIN's 0.8 V p-p to VDD (ADF4002 p3).
- Load: U1's OSC_IN plus U2's REFIN (10 pF max, ADF4002 p3), about the 15 pF Y2 is specified into (YSO110TR p1). U4's clock comes from U1's MCO, not from Y2, to keep Y2's load there.
- Reference designs: [HELIOS](https://github.com/JoshCrouch/HELIOS) reference board (ADF4002 locking a 100 MHz VCXO), REFIN AC-coupled through 10 nF; ADF4002 datasheet Figure 21 (p17), reference straight into REFIN.

## Chain 5: Oscillator, buffer and lock gate

**Topology** follows the published 5 W PLL FM transmitter from pira.cz ([schematic](https://www.pira.cz/entx4.htm), the TSA5511 + PIC design):
- **Oscillator:** a common-base Colpitts. The base is held at RF ground, and the collector carries the LC tank.
- **Varicap:** couples into the tank through 330 pF. The tune voltage and the audio are summed onto it through resistors.
- **PLL sample:** taken from the oscillator's emitter.
- **Buffer:** a common-emitter stage.

Two more published designs use the same single-varicap scheme, with audio superimposed on the tune voltage and the PLL loop held below audio:
- **Gamma Electronics PLL stereo transmitter** ([page](https://www.gammaelectronics.xyz/transmitter-projects-DIY_8.html)): loop bandwidth under 20 Hz.
- **Broadcast Warehouse PLL kits** ([review](https://radio.xtreamlab.net/bc-ware-1w-pll.html)): one BB809 is both "audio modulator" and "VCO control element".

The 2 m [STM32 + ADF4002 transceiver](https://github.com/Zachnad0/KICAD_VHF-FM-2m-TxRx-STM32) plans the same thing (README: loop "~30 Hz to avoid suppression of audio FM"), though its schematic has no values yet. So **the separate modulation varicap mentioned earlier is dropped**. Firmware scales the audio level per channel, because modulation sensitivity varies across the band.

**Varicap change: 1SV281 → 1SV322.**
- **1SV281 doesn't fit.** Its guaranteed capacitance is 15–17 pF at 1 V and 7.3–8.7 pF at 4 V. Even two in parallel cover 88–108 MHz only if the tank's other capacitance stays under about 7 pF. The Colpitts feedback capacitors alone take about 6 pF.
- **1SV322 does.** Toshiba's 1SV322 is guaranteed 26.5–29.5 pF at 1 V and 6.0–7.1 pF at 4 V, ratio ≥ 4.0, rs ≤ 0.8 Ω at 100 MHz, 10 V max (`VAR_Toshiba_1SV322.pdf` p1).
- **Tank check (worst case):** with L1 = 120 nH, about 9 pF of fixed capacitance, and the varicap seen through 330 pF, the tank spans about 78–115 MHz between 1 and 4 V. 88 MHz falls near 1.7 V and 108 MHz near 3.4 V, inside the ADF4002's 0.5 V to VP − 0.5 V linear charge-pump range (ADF4002 p3).
- **Caveat:** the datasheet is watermarked "Not Recommended for New Design". DigiKey still has 6,000 active at buy-1, and JLC doesn't list it, so it comes through global sourcing.

**Modulation sensitivity** (estimate from the 1SV322 curve, p2): about 13 MHz/V at mid-band. So ±75 kHz deviation needs only about ±6 mV at the varicap.
- **Audio attenuation:** a 1 MΩ / 10 kΩ divider attenuates the DAC's audio by about 100:1. That puts full deviation near ±0.6 V at the DAC, leaving headroom.
- **Noise:** the divider's thermal noise (about 3 µV over 53 kHz) works out to roughly 40 Hz rms of deviation, about 65 dB below ±75 kHz.

| Ref | Part | Value | JLC | Note |
|---|---|---|---|---|
| R5 (3V3 → VCC_VCO) | Yageo RC0402FR-0710RL | 10 Ω | C138066, 946,391 | Supply filter for oscillator and buffer; with 10 µF, corner ≈ 1.6 kHz. The pira design gives its oscillator a separate regulator |
| C (VCC_VCO) | Samsung CL21A106KOQNNNE + CL05B104KO5NNNC | 10 µF + 100 nF | C1713 / C1525 | At L1's supply end |
| Q1 | onsemi MMBTH10LT1G | VHF NPN oscillator | C16204, 2,858 | fT ≥ 650 MHz at 100 MHz (MMBTH10 p2) |
| R6, R7 (Q1 base divider) | Yageo RC0402FR-0710KL | 10 kΩ / 10 kΩ | C60490 | pira R1/R2. Base ≈ 1.6 V |
| C (Q1 base) | Samsung CL05B103KB5NNNC | 10 nF to GND | C15195 | Base at RF ground (pira C1) |
| R8 (Q1 emitter) | Yageo RC0402FR-07270RL | 270 Ω to GND | C163474, 224,286 | pira R3. About 3 mA |
| C (Q1 collector–emitter) | Samsung CL05C150JB5NNNC | 15 pF C0G | C86285, 87,112 | pira C2 (feedback) |
| C (Q1 emitter–GND) | Samsung CL05C100JB5NNNC | 10 pF C0G | C32949, 1,736,580 | pira C3 (feedback) |
| L1 (VCC_VCO → Q1 collector) | **Murata LQW18ANR12G00D** | 120 nH ±2%, Q ≥ 32 at 150 MHz, SRF ≥ 1.6 GHz | C86138, 12,530 | Tank (LQW18AN spec p3) |
| C (collector → varicap) | Samsung CL05C331JB5NNNC | 330 pF C0G | C13533, 266,791 | pira C5 |
| D2 | **Toshiba 1SV322(TPH3,F)** | Varicap; cathode to the 330 pF node, anode to GND | Global sourcing (DigiKey 6,000) | See above |
| R9 (loop filter → varicap cathode) | Yageo RC0402FR-0710KL | 10 kΩ | C60490 | Feeds the tune voltage; keeps RF off the loop filter |
| R10 + C (audio → varicap cathode) | Yageo RC0402FR-071ML + Samsung CL05B104KO5NNNC | 1 MΩ + 100 nF in series | C138033 / C1525 | ≈ 1/100 with R9. High-pass 1.6 Hz. Audio comes from the DAC filter (chain 10) |
| R11 + C (Q1 emitter → U2 RFINA) | Yageo RC0402FR-07220RL + Samsung CL05C150JB5NNNC | 220 Ω + 15 pF in series | C112291 / C86285 | The PLL sample, as pira's 680 Ω + 15 pF. Lowered to 220 Ω because the ADF4002 needs −10 to 0 dBm (p3); its input is about 500 Ω per pin (Figure 11, p8). Estimate about −4 dBm; check on the bench |
| C (Q1 emitter → Q2 base) | Samsung CL05C220JB5NNNC | 22 pF C0G | C70464, 250,294 | pira C8 |
| Q2 | onsemi MMBTH10LT1G | Buffer, common emitter | C16204 | |
| R12 (Q2 collector → base) | Yageo RC0402FR-0718KL | 18 kΩ | C138044, 971,385 | Collector-feedback bias; with hFE ≥ 60 (p2), Ic ≈ 4 mA, VCE ≈ 2 V |
| R13 (VCC_VCO → Q2 collector) | Yageo RC0402FR-07270RL | 270 Ω | C163474 | |
| R14 + C (Q2 emitter) | Yageo RC0402FR-0747RL + Samsung CL05B103KB5NNNC | 47 Ω ∥ 10 nF to GND | C137973 / C15195 | pira R8 + C9 |
| C (Q2 collector → U7 RF1) | Murata GRM1555C1H102JA01D | 1 nF C0G, series | C76947, 880,292 | The PE43711's RF pins must be at 0 V DC (PE43711 p1, p28); Q2's collector sits near 2.2 V |
| Q3 (lock gate) | onsemi MMBT3904LT1G | Collector to Q2 base, emitter to GND | C81464 | VCE(sat) ≤ 0.2 V (p2), below Q2's turn-on, so the buffer is off |
| R15 (MCU GPIO → Q3 base) | Yageo RC0402FR-0710KL | 10 kΩ | C60490 | Driven low by firmware once U2 reports lock (MUXOUT) |
| R16 (3V3 → Q3 base) | Yageo RC0402FR-0710KL | 10 kΩ pull-up | C60490 | Buffer muted from power-up until firmware releases it |

Bench items: the tune voltage at 88.1 and 107.9 MHz (target about 1.7 V and 3.4 V), the RFINA level, the buffer output level, and the per-channel modulation sensitivity for the firmware's audio-level table.
