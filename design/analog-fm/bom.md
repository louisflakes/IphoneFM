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
| 4 | Y2 20 MHz reference oscillator | **Done** (updated for D2) |
| 5 | U2 LMX2571 synthesizer | **Done** |
| 6 | U7 PE43711 attenuator and SW3 DIP switch | **Done** |
| 7 | FL1 low-pass, U5 RF switch, J2, D5 | **Done** |
| 8 | U4 Si4705 receiver (QFN) | **Done** |
| 9 | Controls: thumbwheels, slider, BOOT button, LED | **Done** |
| 10 | Test pads and power budget | **Done** |

Dropped with the move to the LMX2571 (option D2): the discrete oscillator, buffer and lock gate, the ADF4002 loop, and the DAC audio filter. The MCU's DAC no longer carries transmit audio.

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

1. **VDDA ferrite added** (reference-check U1 gap 1). VREF+ is bonded to VDDA on this package, so VDDA noise reaches the ADC readings (thumbwheels, CC sensing). The DAC no longer carries transmit audio after the move to the LMX2571. The CAN-node reference design feeds VDDA through a 600 Ω ferrite, and that is adopted here.
2. **Clock from the 20 MHz reference oscillator.** Y2 drives PH0-OSC_IN in HSE digital bypass mode, and the PLL runs the system clock from it. DS14217 allows a 4–50 MHz external clock with OSC_IN high ≥ 0.7 × VDD and low ≤ 0.3 × VDD (p184–185); Y2 gives ≥ 90% and ≤ 10% of VDD (YSO110TR p1). ST's own Nucleo-U545 offers the same external-oscillator-into-PH0 option (UM3062 p27). The audio sample clock and the 19 kHz pilot become crystal-accurate. USB stays on HSI48 locked to USB start-of-frame by the CRS, as in Plan C, so the ROM bootloader still works with no crystal.
3. **32.768 kHz crystal removed.** Plan C needed Y1 only to give the receiver its reference clock through LSCO. Now a U1 timer makes 32,787 Hz (160 MHz ÷ 4880) from the crystal-referenced system clock (chain 8). It is inside the Si4705's 31,130–34,406 Hz REFCLK range (AN332 p37), and accuracy improves from Plan C's −92 ppm worst case to ±20 ppm. Y1 and its two 5.6 pF capacitors are gone.

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
| U1 timer output | — | 32,787 Hz (160 MHz ÷ 4880) to U4 RCLK | | Chain 8. Replaces the earlier plan of 20 MHz from MCO, to keep 20 MHz and its 100.0 MHz harmonic away from the receiver |
| SAI1 sub-block A | — | I²S out to U2 (CLK, DATA, FS) at about 912 kSa/s | | Chain 5. Sub-block B receives U4's digital audio at 48 kHz; each sub-block has its own clock generator (DS14217 p80) |
| SPI2 + GPIOs | — | U2 programming (CLK, DATA, LE), CE, MUXout | | Chain 5 |

Removed from Plan C: Y1 (ABS07 32.768 kHz) and its two 5.6 pF capacitors; LSCO on PA2; TIM16 on PB8 (the LV2285 76 kHz drive). The full U1 pin map is redone when the schematic is drawn.

## Chain 4: Y2 20 MHz reference oscillator (YXC OT322520MJBA4SL)

One CMOS oscillator is the frequency reference for the whole board. It drives U1 (system clock and audio timing) and U2 (LMX2571 OSCin), and through U1's MCO, U4 (receiver reference).

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| Y2 | YXC OT322520MJBA4SL | 20 MHz CMOS, 1.8–3.3 V, 3.2 × 2.5 mm | C725987, 4,055 | Pins: 1 tri-state, 2 GND, 3 OUT, 4 VDD (YSO110TR p2) |
| Pin 1 (tri-state) | — | Tied to VDD | | High or floating enables the output (p1); tied, not left floating |
| Pin 4 VDD | Samsung CL05B104KO5NNNC + CL21A106KOQNNNE | 100 nF + 10 µF to GND | C1525 / C1713 | The maker's test circuit (p4) |
| R4 (pin 3 → U1 PH0) | Yageo RC0402FR-0733RL | 33 Ω series | C138002, 6,823,372 | Source termination at Y2 to damp ringing on the line to U1 (best guess; the Nucleo uses a series R and C on its external clock path, UM3062 p26) |
| — (pin 3 → U2 OSCin) | — | Direct | | Single-ended CMOS straight into OSCin, OSCin* unconnected (LMX2571 Table 37, p38; Figure 62, p44). The ADF4002's 10 nF coupling capacitor is gone |

- Level at OSCin: Y2 swings 0 to 3.3 V, a CMOS square wave, which TI recommends for the best spurs and phase noise (LMX2571 p11).
- Load: U1's OSC_IN plus U2's OSCin (about 1 pF typical, LMX2571 p38), well within the 15 pF Y2 is specified into (YSO110TR p1). U4's clock comes from U1's MCO, not from Y2.
- Reference: LMX2571 Figure 62 (p44) drives OSCin straight from an XO.

## Chain 5: U2 LMX2571 synthesizer (D2: internal VCO, direct digital FM)

Chosen 2026-10-21 (see [modulation-strategies.md](modulation-strategies.md)). It replaces the discrete oscillator, buffer and lock gate (old chain 5) and the ADF4002 loop (old chain 6). Both are in git history (commits 9f95801, 0414cd3).

**References:**
- **Datasheet SNAS654A:** pin functions (p3), typical synthesizer schematic (Figure 62, p44), Do's and Don'ts (Figure 86, p53), power-supply recommendations (p54), and OSCin configuration (Table 37, p38).
- **TI SNAA309:** analog FM in FSK I²S mode.
- **Published hardware:** no open schematic using the LMX2571 turned up. Open STM32 firmware does use it for FM: [yxy1003/Gaopin_lib_2025](https://github.com/yxy1003/Gaopin_lib_2025) streams frequency offsets to R33 (FSK SPI FAST, `LMX2571_FASTFSK`); [xjc666-666/Electronic-Design-Contest](https://github.com/xjc666-666/Electronic-Design-Contest) configures the FSK I²S fields. Both are Chinese electronic-design-contest libraries.

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| U2 | TI LMX2571NJKR | Synthesizer, WQFN-36 6 × 6 mm | C440388, 139 | DigiKey 1,244 as second route |
| Vcc3p3 1, 9, 20, 27 (×4) | Samsung CL05B104KO5NNNC | 100 nF each, at the pin | C1525 | "100 nF close to each of the power supply pins" (p54) |
| VccIO 33 | Samsung CL05B104KO5NNNC | 100 nF | C1525 | Figure 62 |
| VcpExt 32 | — + Samsung CL05B104KO5NNNC | 3V3, 100 nF | C1525 | Must be powered in synthesizer mode too, 3.3 V or 5 V (p53, p54) |
| Bypass1 2, Bypass2 3 | Samsung CL05B104KO5NNNC | 100 nF each | C1525 | Pin table (p3) |
| VrefVCO 22 | Samsung CL05B104KO5NNNC | 100 nF | C1525 | Figure 62 |
| VregVCO 21 | **Samsung CL10A225KO8NNNC** | 2.2 µF X5R 16 V 0603 | C23630, 3,207,467 | Figure 62; 100 nF here is marked "incorrect" (p53) |
| CPout 25: C1 to GND | Samsung CL05C101JB5NNNC | 100 pF C0G | C26409, 492,000 | Loop filter (see below) |
| CPout 25: R2 + C2 to GND | Panasonic ERJ-2RKF1101X + Murata GRM1555C1H152JA01D | 1.1 kΩ + 1.5 nF C0G | C409028, 51,663 / C668348, 97,247 | Loop filter |
| RFoutTx 17 → U7 RF1 | Samsung CL05C101JB5NNNC | 100 pF C0G, series | C26409 | Push-pull output needs only a DC block (Table 38, p42); the PE43711 RF pins must be at 0 V DC |
| OSCin 34 | — | Y2 output, direct | | Single-ended CMOS: IPBUF_SE_DIFF_SEL = 0, OSCin* unconnected (Table 37, p38) |
| OSCin* 36 | — | Not connected | | Table 37 |
| FSK_DV 4 / FSK_D1 6 / FSK_D0 7 | Yageo RC0402FR-0733RL ×3 | 33 Ω series, at U1 | C138002 | I²S CLK / DATA / FS from U1 SAI1 sub-block A (FSK I²S mode, p3, p13). The stream runs continuously next to the synthesizer, so series resistors soften the edges (HELIOS puts ferrites on its ADF4002 lines for the same reason) |
| FSK_D2 5 | — | GND | | Used only in FSK PIN mode (p3) |
| CLK 11, DATA 12, LE 13 | — | U1 SPI2 SCK, MOSI, and a GPIO | | MICROWIRE, 24-bit words (p15) |
| MUXout 10 | — | To a U1 input | | Lock detect or register readback (p14) |
| CE 19 | Yageo RC0402FR-0710KL | 10 kΩ pull-down; U1 GPIO | C60490 | Off until firmware enables it, and off in receive mode so its carrier can't reach U4 |
| TrCtl 18 | — | GND | | Output port and F1/F2 under register control (p37) |
| Fin 24 | — | Not connected | | "Leave it open… if not being used" (p3) |
| CPoutExt 30, FLout1 29, FLout2 28 | — | Not connected | | PLL-mode outputs, unused in synthesizer mode |
| RFoutRx 16 | — | Not connected | | RX buffer disabled in registers |
| NC 8, 14, 26 | — | Not connected | | "Do not connect" (p3) |
| GND 23, 31, 35, DAP | — | GND | | DAP must be grounded (p53) |

**Loop filter check** (second-order passive, the internal third and fourth poles bypassed: LF_R3 = LF_R4 = 0):
- **Model:** C1 = 100 pF, R2 = 1.1 kΩ, C2 = 1.5 nF, checked against the internal VCO's gain (56 MHz/V typical at 4.8 GHz, p6, swept 40–75 MHz/V) and both reference settings (f_PD 40 MHz, N ≈ 123–130; f_PD 100 MHz, N ≈ 49–52).
- **Result:** firmware picks the charge-pump current per setting (2.2–5.3 mA, in 312.5 µA steps, p5), which gives a 300–405 kHz loop at 61–62° phase margin.
- **Audio response:** +0.05–0.07 dB at 15 kHz. At 53 kHz, +0.5–0.7 dB and −1.7° to −2.5°; the MCU removes this with a fixed pre-equaliser.
- **Still to do:** confirm in TI's PLLatinum Sim, including spurs, before layout.

**Firmware set-up** (from the datasheet, recorded here so the hardware choices make sense):
- **Synthesizer mode.** Output divider 56 for 88.1–95.9 MHz, 48 for 96.1–107.9 MHz.
- **Per-channel reference:** f_PD = 40 MHz (MULT 2, DEN 400,000) or 100 MHz (MULT 5, DEN 1,000,000).
- **Modulation:** FSK I²S mode at about 912 kSa/s.
- **Output:** push-pull buffer, OUTBUF_AUTOMUTE on (default).
- **Power-on sequence:** R60 down to R0 (p15).

## Chain 6: U7 PE43711 attenuator and SW3 DIP switch

**References:**
- **PE43711 datasheet DOC-84940-8:** pin table (Table 9, p28), parallel truth table (Table 4, p6), programming modes and power-up behaviour (p8).
- **[bgelb/gpsrx](https://github.com/bgelb/gpsrx):** a GPS receiver that runs the PE43711 in serial mode. It bypasses VDD with 1 µF, ties its unused parallel inputs low through 1 kΩ, and feeds RF1 through a 1 nF DC block.
- No published design uses direct parallel mode with switches. The datasheet describes that mode as "ideal for manual control… using hardwire, switches, or jumpers" (p8).

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| U7 | pSemi PE43711B-Z | DSA, QFN-24 4 × 4 mm | C470929, 1,737 | |
| VDD 2 | Samsung CL10B105KO8NNNC | 3V3, 1 µF to GND | C59782 | As gpsrx. 2.3–5.5 V (p3) |
| P/S 3 | — | GND | | Parallel interface (p8) |
| LE 16 | — | 3V3 | | Direct parallel mode: the control pins act immediately (p8) |
| CLK 17, SI 18 | — | GND | | Serial interface unused |
| C0.25 (D0) 1 | — | GND | | "Ground… if not in use" (Table 9 note 1) |
| C16, C8, C4, C2, C1, C0.5 (pins 19–24) | Yageo RC0402FR-0710KL ×6 | 10 kΩ pull-down each | C60490 | So an open switch reads low (p8: floating pins at power-up give minimum attenuation) |
| SW3 | C&K TDP06H1SBD1 | 6-position side-actuated DIP | Global sourcing (DigiKey 1,180) | One side of every switch on 3V3. Switch 1 → C16 … switch 6 → C0.5. Silkscreen 16 / 8 / 4 / 2 / 1 / 0.5 dB. 0.33 mA per closed switch, within its 25 mA rating |
| RF1 5 | — | From U2 RFoutTx through the 100 pF in chain 5 | | RF pins must be at 0 V DC (Table 9 note 2) |
| RF2 14 | — | To FL1 (chain 7) | | 0 V DC |
| GND 4, 6–13, 15, pad | — | GND | | |

- **Power-up:** in direct mode the part sits at maximum attenuation for about 400 µs, then takes the switches' setting (p8).
- **Levels:** U2 delivers at most about +3 dBm (LMX2571 p42), far below the +28 dBm input limit (PE43711 p3). The insertion loss is about 1.5 dB at 0 dB (p4).
- **Range:** with U2's programmable output (about −18 to +3 dBm), the board can deliver about +1.5 dBm down to −51 dBm into FL1, before filter and switch loss.

## Chain 7: TX low-pass FL1, U5 RF switch, J2 SMA, D5 antenna ESD

Circuits as Plan C chains 7, 11 and 12. U5 is compared against four published designs, and the antenna ESD position against three, in reference-check.md. What changes:
- **FL1 now sees a true 50 Ω source** (the attenuator), as it was designed for.
- **The DC block after FL1 is dropped.** Both ends are now at 0 V DC: U7's RF pins (Table 9 note 2) and U5's RF pins (PE42421 p8). Plan C needed it only because the LV2285 output sat at a DC voltage.
- **The 1 nF filter capacitor on U5's control pin is added,** closing reference-check U5 gap 1.

| Ref / pin | Part | Value | JLC | Note |
|---|---|---|---|---|
| FL1 C (shunt, ×2) | Samsung CL05C330JB5NNNC | 33 pF C0G 0402 | C70465, 312,114 | Replaces Murata GRM1555C1H330JA01D (JLC: 0) |
| FL1 C (shunt, middle) | **Yageo CC0402JRNPO9BN560** | 56 pF C0G (NP0) ±5% 50 V 0402 | C107007, 630,922 | Replaces Murata GRM1555C1H560JA01D (JLC: 0) |
| FL1 L (series, ×2) | Murata LQW18ANR10G00D | 100 nH ±2%, Q ≥ 34 at 150 MHz | C98088, 43,869 | Sourcing replacement for the Coilcraft part |
| U5 | pSemi PE42421SCAA-Z | SPDT RF switch | C470893, 677 | |
| U5 VDD 6 | Yageo RC0402FR-071KL | 1 kΩ from 3V3 | C106235 | Eval board (PE42421 p7) |
| U5 CTRL 4 | Yageo RC0402FR-071KL + Murata GRM1555C1H102JA01D | 1 kΩ series, then 1 nF C0G to GND at the pin | C106235 / C76947 | 1 nF added (reference-check U5 gap 1; LoRaPP and Electronic Cats both fit it) |
| RF_MODE | Yageo RC0402FR-07100KL | 100 kΩ pull-down | C60491 | Holds receive while the slider is between contacts |
| SW1 | Shou Han MSK12C02 | SPDT slide switch | C431540, 195,730 | Common to RF_MODE; throws to 3V3 (TX) and GND (RX). U1 reads RF_MODE (Plan C PB0) and powers U2 down in receive |
| U5 RF2 3 | — | From FL1 | | TX |
| U5 RF1 1 | — | To U4 through C2 1 nF (chain 8) | | RX |
| U5 RFC 5 | — | To J2 centre | | 0 V DC (p8) |
| J2 | BAT Wireless BWSMA-KWE-Z001 | SMA jack, right angle | C496551, 129,042 | Footprint 5.1 mm square, Ø1.4 holes (drawing p6) |
| D5 | Semtech RClamp0521PATCT | Antenna line to GND, at J2 | C117554, 91,372 | Bidirectional, 0.3–0.5 pF, 5 V stand-off (p1–2) |

**Harmonics** (estimate):
- **At U2:** the push-pull output's harmonics are about −30 dBc (2nd), −12 dBc (3rd) and −16 dBc (5th) (LMX2571 Table 38, p42, measured at 480 MHz).
- **After FL1** (23–34 dB at the 2nd, ≥ 43 dB from 264 MHz; Plan C chain 12): about ≤ −53 dBc (2nd), ≤ −55 dBc (3rd), ≤ −59 dBc (5th).
- **Margin:** U2's open-drain output with an LC pull-up (Table 38) is the step to take if the bench wants more.

## Chain 8: U4 Si4705-D60-GM receiver (QFN-20)

**References:**
- **Datasheet Si4704/05-D60 Rev 1.2:** QFN typical schematic (p16), BOM (Table 12, p18), DC characteristics (p5), RCLK (p14).
- **AN332:** REFCLK (p37–38).
- **AN383:** FMI front end and emissions filter (p7–9, p17, p37).
- **[USB FM Radio](https://github.com/anttikes/usb-fm-radio):** uses this exact QFN part. It was compared pin by pin in reference-check.md (U4); its three gaps are closed here.

**RCLK change:** the reference clock now comes from a **U1 timer output at 32,787 Hz** (160 MHz ÷ 4880), with REFCLK_PRESCALE = 1 and REFCLK_FREQ = 32787. That is inside 31,130–34,406 Hz (AN332 p37). Because U1 now runs from Y2, the clock is accurate to ±20 ppm.
- **Why not MCO:** chain 3 had planned 20 MHz from MCO divided by 610 inside the Si4705. That is replaced because a 20 MHz trace near the receiver puts its 5th harmonic at 100.0 MHz, inside the band.
- **RCLK input:** high is ≥ 0.7 × VD (p5), which U1's 3.3 V output meets.

| Ref / pin (QFN) | Part | Value | JLC | Note |
|---|---|---|---|---|
| U4 | Skyworks SI4705-D60-GM | FM receiver, QFN-20 3 × 3 mm | C1526114, 48 | DigiKey 470 as second route |
| FB3 (3V3 → VA/VD) | Murata BLM15AG601SN1D | 600 Ω at 100 MHz | C76884 | Closes reference-check U4 gap 1 (USB FM Radio FB2) |
| C1 (VA 11 to GND) | Murata GRM155R71H223KA12D | 22 nF X7R, at the pin | C77023, 415,822 | QFN puts C1 from VA to GND (p16; Table 12, p18) |
| C4 (VD 10 to GND) | Samsung CL05B104KO5NNNC | 100 nF, at the pin | C1525 | p16, Table 12 |
| C2 (U5 RF1 → FMI chain) | Murata GRM1555C1H102JA01D | 1 nF C0G | C76947 | Coupling (Table 12); keeps U5's RF1 at 0 V DC |
| L1 (C2–FB1 node to GND) | Murata LQW18ANR15G00D | 150 nH ±2%, Q ≥ 32 | C113131, 25,316 | Whip-antenna match (AN383 p37 Figure 23), sized in Plan C chain 3 |
| FB1 (→ FMI 2) | Murata BLM15GA750SN1D | 75 Ω at 100 MHz | C113009, 18,276 | Emissions filter (AN383 p7, p9) |
| C14 (FMI 2 to GND) | Murata GJM1555C1H6R0CB01D | 6 pF C0G, at the pin | C161330, 3,416 | Emissions filter (AN383 p7) |
| RFGND 3, LPI 4 | — | GND | | AN383 p8, p17 |
| RSTB 5 | Yageo RC0402FR-0710KL | 10 kΩ pull-down; U1 GPIO | C60490 | Held in reset until firmware runs |
| SENB 6 | — | GND | | 2-wire bus |
| SCLK 7, SDIO 8 | Yageo RC0402FR-076K8L ×2 | 6.8 kΩ pull-ups to 3V3; U1 I²C | C93940 | SDIO sinks ≤ 500 µA (p5) |
| RCLK 9 | — | U1 timer output, 32,787 Hz | | See above |
| ROUT 13, LOUT 14 | — | GND | | Closes reference-check U4 gap 3 (AN383 p17; USB FM Radio). Firmware keeps analog outputs off |
| DOUT 15 | Yageo RC0402FR-07604RL | R1 604 Ω series → U1 SAI1-B SD | C273693 | Table 12 (600 Ω) |
| DFS 16 | Panasonic ERJ-2RKF2001X + Murata GRM1555C1H3R3CA01D | R2 2 kΩ series → SAI1-B FS; C9 3.3 pF C0G to GND at U1 | C413086, 12,348 / C76968, 14,752 | Table 12 (2 kΩ; C9 2–5 pF) |
| GPO3/DCLK 17 | Panasonic ERJ-2RKF2001X | R3 2 kΩ series → SAI1-B SCK | C413086 | Table 12 |
| GPO2/INT 18, GPO1 19 | Samsung CL05C330JB5NNNC ×2 | 33 pF to GND; otherwise floating | C70465 | AN383 p8 option 1. Firmware polls (reference-check gap 2 left as optional) |
| NC 1, 20 | — | Floating | | p16 note 3 |
| GND 12, pad | — | GND | | |


## Chain 9: Controls

| Ref | Part | Wiring | JLC | Note |
|---|---|---|---|---|
| RV1–RV3 | Alps RK10J11R0A0H | Pin 1 → 3V3, pin 3 → GND, wiper pin 2 → U1 ADC; the two dummy pins → GND pads | C470766, 913 | `POT_Alps_RK10J.pdf` p3 terminal layout |
| C (each wiper) | Samsung CL05B104KO5NNNC | 100 nF to GND at the ADC pin | C1525 | Charge reservoir for the ADC's sampling capacitor; ≤ 0.25 ms time constant with the pot, fine for a hand-turned wheel |
| SW1 | Shou Han MSK12C02 | Chain 7 | | |
| SW2 | Panasonic EVQ-P7J01P | 3V3 to U1 BOOT0 (10 kΩ pull-down, chain 3) | C2828254, 9,729 | BOOT button only (Plan C chain 9) |
| D1 | XINGLIGHT XL-1615RGBC-RF | Pin 2 (common anode) → VBUS; R pin 1 / G pin 3 / B pin 4 through resistors to U1 open-drain pins | C965840 | p8 pinout |
| R (red) | Yageo RC0402FR-07510RL | 510 Ω | C276273 | (5 − 1.9 − 0.4) / 510 ≈ 5.3 mA typical, 4.3 mA at VF max 2.4 V (p4). IF max 20 mA (p3) |
| R (green, blue) | Yageo RC0402FR-07390RL ×2 | 390 Ω | C137997, 1,797,586 | Replaces Panasonic ERJ-2RKF3900X (JLC: 21, minimum buy 828). (5 − 2.8 − 0.4) / 390 ≈ 4.6 mA typical, 3.1 mA at VF max 3.4 V |

The LED allows 5 V reverse voltage (p3), so the unplug case that worried Plan C's Broadcom part is covered.

## Chain 10: Test pads and power budget

**Test pads:** none on RF nets (Plan C chain 13 rule).
- TP1 VBUS
- TP2 3V3
- TP3 GND
- TP4 RF_MODE: which slide direction is TX
- TP5 U2 MUXout: PLL lock

**3V3 current** (maximum or high-setting figures):

| Load | Transmit | Receive | Source |
|---|---|---|---|
| U1 at 160 MHz plus USB, SAI, ADC | ~30 mA | ~30 mA | DS14217 p139: 13–17 mA typical, 20 mA max at 85 °C, plus peripherals (estimate) |
| U2 LMX2571 | ~57 mA at the highest output setting (39 mA typical) | ~0 (CE low) | LMX2571 p1, Figure 61 (p42) |
| U4 Si4705 | µA (powered down) | ≤ 23 mA (VA 9.5 + VD 13.5, digital mode) | Si4704/05 p5 |
| Y2 | ≤ 5 mA | ≤ 5 mA | YSO110TR p1 |
| U7, U5, pull-ups, DIP, wheels | ~4 mA | ~4 mA | |
| **3V3 total** | **~96 mA** | **~62 mA** | |
| D1 from VBUS | ≤ 15 mA | ≤ 15 mA | Chain 9 |

- **Apple limits:**
  - **Before USB setup (≤ 100 mA):** at power-up U2 is off (CE pull-down), U4 is in reset (RST pull-down) and the LED pins are high-impedance. That leaves about 35 mA.
  - **After setup (≤ 500 mA):** at most about 111 mA from VBUS.
- **Regulator:** 600 mA rating; dissipation about (5 − 3.3) × 0.1 A ≈ 0.17 W.
- **Start-up:**
  - **3V3 capacitance:** about 24 µF. That is U3's 1 µF, U1's 10 µF + 3 × 100 nF + VDDA's 1.1 µF, Y2's 10 µF + 100 nF, U2's six 100 nF supply caps, U7's 1 µF and U4's 122 nF. U2's VregVCO/Bypass caps sit behind its internal regulators.
  - **Ramp time:** the AP2112's 50 mA fold-back current (Plan C chain 5) charges it to 3.3 V in about 1.6 ms, or about 1.8 ms with Y2 already running. Every other load is off or in reset at that point.
