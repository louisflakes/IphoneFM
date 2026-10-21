# Analog FM rendition: bill of materials

Built one chain at a time. Each chain is checked against its datasheet and against published designs that use the exact part. Key parts and their stock are in [sourcing.md](sourcing.md); datasheets are in [docs/datasheets/analog-fm/](../../docs/datasheets/analog-fm/) and `plan-c/`.

Rules carried over from Plan C: every passive is populated with a best-guess value (no empty pads), and every part needs deep stock at JLC or a second route.

Reference designs are read with a small connectivity script on their KiCad files. It traces wires, labels and power symbols to list what sits on each pin of the part.

## Chain order

| # | Chain | Status |
|---|---|---|
| 1 | J1 USB-C receptacle and USB ESD | **Done** |
| 2 | U3 3.3 V regulator and bulk capacitors | **Done** |
| 3 | U1 STM32U535 support (VDDA filter, clock source) | Next |
| 4 | Y2 20 MHz reference oscillator | — |
| 5 | Oscillator, modulation varactor, buffer, lock gate | — |
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
