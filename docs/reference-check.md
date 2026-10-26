# Plan C reference check

An adversarial check of the [wiring diagram](../design/archive/plan-c/wiring.html). For each key part, find 2–3 existing schematics or board designs that use the exact part number, compare how they wired it pin by pin, and record any gap against Plan C. Passive values may differ; the check is about purpose and function.

One part at a time, in the order below (highest risk first). Started 2026-10-20.

## Tracker

| # | Ref | Exact part | What to compare pin by pin | Risk | Designs found | Status | Gaps found |
|---|---|---|---|---|---|---|---|
| 1 | U2 | onsemi LV2285VB (LV2285VB-TLM-E) | I²C mode strapping (I2CSW, L/R-CONT), audio input coupling and pre-emphasis, VCO tank and varactor (D2), loop filter, RF output bias and matching, 16 MHz crystal, the 76 kHz oscillator (we drive pin 22 from U1 instead of a crystal), LDO pins 4/11/14, auto-sleep TC | High: obsolete, few public designs, our 76 kHz drive is unusual | 0 | Done: none found | No public design to compare; the datasheet's application circuit stays the only reference |
| 2 | U4 | Skyworks Si4704-D60-GU (SSOP-24) | Digital audio out (DOUT/DFS/DCLK series R and the DFS cap), RCLK source, 2-wire bus strapping (GPO1/GPO2, SEN), FMI front end (coupling, match, ESD, emissions filter), LPI and NC pins, VA/VD/DBYP decoupling | High: RF front end and digital-audio mode | 1 exact (Skyworks EVB) + 1 sibling (Si4705-D60) | Done | 3 gaps, 1 risk (see below) |
| 3 | U1 | ST STM32U535CEU6 (UFQFPN48) | Power pins (VDD, VDDA, VBAT, VCAP, no VDDUSB on this package), NRST and BOOT0, USB FS without external pull-up, LSE crystal and LSCO out, SAI and DAC pin use, SWD | Medium: new family, VCAP and USB-on-VDD details | 0 exact; 1 same die and flash (LQFP48) + 3 siblings | Done | 1 gap (see below) |
| 4 | U5 | pSemi PE42421 | VDD and CTRL series resistors, RF port DC blocking, no RFC shunt, ground | Medium | 4 exact (2 independent designs) | Done | 1 gap (see below) |
| 5 | J1 | GCT USB4105-GF-A | CC1/CC2 Rd, D+/D− pair shorting, SBU, shell ground, VBUS capacitance | Medium: USB-C sink detection | 3 exact | Done | None |
| 6 | U3 | Diodes AP2112K-3.3 | EN tied to VIN, input and output caps, NC pin | Low | 3 exact | Done | None |
| 7 | U6 | ST USBLC6-2SC6 | Which pins carry D+, D− and VBUS; ground; placement at the connector | Low | 4 exact | Done | None |
| 8 | D1 | Broadcom ASCB-WTF0-0A30A | Independent chips: anodes to VBUS, each cathode through its resistor to an open-drain MCU pin | Low | 0 | Done: none found | No public design; the datasheet pin table stays the reference |
| 9 | D5 | TI TPD1E0B04DPLR | Placement and orientation on an RF antenna line, capacitance at 100 MHz | Low | 3 exact (DPY package) on RF inputs | Done | None |

Not checked: the switches (SW1–SW3), crystals and passives, whose wiring is fixed by their own datasheets.

## Running list: where Plan C differs, and why

One part at a time, in plain words. Each entry says whether the difference is understood and whether it still needs proof.

### U2 LV2285VB transmitter

No designs found online, so the reference is the datasheet's 88–108 MHz application circuit (ENA1494 p4). Plan C matches it except:

1. **Inductors from Coilcraft instead of TOKO** (100 nH, 330 nH, same values). TOKO's parts are no longer made. Understood; fine.
2. **1 nF DC block added between U2's output and the RF switch.** U2's output pin sits at a DC voltage; the switch's RF pins must be at 0 V (PE42421 p8). Understood; needed.
3. **16 MHz crystal chosen by us.** The datasheet gives no crystal spec; we took one from the same family as its example circuit. Understood; a reasoned choice.
4. **76 kHz crystal replaced by a clock from U1.** The datasheet's only option is a crystal across pins 21–22 (external clock input is offered on the 16 MHz pin, not this one). No 76 kHz crystal is sold any more, so U1 feeds pin 22 through 2.2 kΩ, 1 kΩ and 10 nF. Understood why, **but not proven**: it relies on the pin's described self-bias (0.7 V, ENA1494 p7), not on a documented mode. First board: check U2 makes a clean stereo pilot from this clock (TP4).

Supply: U2 is end-of-life. Both DigiKey listings are leftover stock resold by Rochester Electronics, in bulk with a 149-piece minimum: LV2285VB-TLM-E-SA (2,000, listed "Active" as Rochester's own listing) and LV2285VB-TLM-E (18,000, onsemi "Obsolete"). JLCPCB lists the part with 0 stock, so its parts have to be bought and sent to JLC. Its varactor D2 (SVC710) is the same: 80,615 left at Rochester, bulk, 1,572-piece minimum, not in JLC's library. Checked 2026-10-20.

## Comparisons

Each part gets a section here when its check is done: the designs found (with links), a pin-by-pin table against Plan C, and the gaps with what to do about them.

### 1. U2 LV2285VB: no designs found (2026-10-20)

Searched: GitHub code for the exact string and in KiCad, Eagle, Arduino and C files; English, Chinese and Japanese hobby sites; FCC filings. Every hit was the datasheet, an unrelated circuit, or a false match (the string inside base64 image data). The part is obsolete and was used mainly in mass-market car transmitters, whose schematics aren't public.

### 2. U4 Si4704-D60-GU (2026-10-20)

Designs found:
- **Skyworks Si47xx-EVB, Rev 0.8 (2021), Si471x/2x daughtercard Rev 1.4 in its "Si4705-06" population** (pp115–116, 131). The guide's Table 2 covers the Si4704/05/06 with this card. QFN package. The maker's own board, so it is a design, not just the datasheet circuit. Saved locally, not in the repo.
- **USB FM Radio** ([anttikes/usb-fm-radio](https://github.com/anttikes/usb-fm-radio), CC-BY-NC-SA, study only): **Si4705-D60-GM**. A sibling, not the exact part: same die and datasheet, adds RDS, identical pin functions. QFN. Closest in purpose: digital audio into an STM32, out over USB audio. Compared from its exported netlist.

No exact Si4704 design exists in public open hardware: GitHub, OSHWLab and Hackaday turned up only siblings (Si4705, Si4703, Si4707, Si4710, Si4721, Si473x) or symbol libraries.

Pin by pin (SSOP pin numbers for Plan C; the references use QFN):

| Function | Plan C | USB FM Radio (Si4705-D60-GM) | Skyworks EVB | Verdict |
|---|---|---|---|---|
| FMI front end | 1 nF C2, L1 150 nH shunt, FB1 75 Ω ferrite, C14 6 pF shunt at the pin; ESD D5 at J2 | 1 nF, L1 56 nH shunt, FB3 75 Ω ferrite, C14 6 pF shunt; CM1213 ESD at the SMA | 1 nF C1, L5 270 nH shunt, CM1213 ESD at FMI; 220 nH series on its SMA test input | Same topology. Inductor values differ by antenna, as expected |
| LPI | GND | GND | — | Match |
| RST | U1 PB2 with 10 kΩ pull-down | MCU pin with 10 kΩ pull-down | baseboard | Match |
| SEN | GND directly | 10 kΩ to GND | jumper | Equivalent |
| SCLK, SDIO | I²C to U1, 6.8 kΩ pull-ups | I²C to MCU, 4.7 kΩ pull-ups | baseboard | Match (our values set by the 500 µA SDIO limit) |
| DOUT, DFS, DCLK | 604 Ω, 2 kΩ + 3.3 pF, 2 kΩ | 604 Ω, 2 kΩ + 2.2 pF, 2 kΩ | 604 Ω and 2 kΩ series | Match |
| GPO1 | Floating + 33 pF | 33 pF only | — | Match |
| GPO2/INT | Floating + 33 pF; firmware polls | **330 Ω to an MCU interrupt pin + 33 pF** | jumper | Gap 2 |
| RCLK | U1 LSCO (32.768 kHz from U1's crystal) | **Dedicated 32.768 kHz oscillator** (Epson SG-3030CM), enabled by the MCU | baseboard or optional crystal | Risk 1 |
| VA, VD supply | 3V3 directly; 22 nF DBYP–VA, 100 nF on VD | **Through a 600 Ω@100 MHz ferrite (FB2)**, 22 nF + 100 nF | 22 nF, 0.1 µF | Gap 1 |
| Analog outputs (ROUT, LOUT) | Left open | **Tied to GND** | to the headphone amp | Gap 3 |

Gaps and risks:
1. **Supply ferrite.** The USB FM Radio feeds the radio from 3.3 V through a 600 Ω@100 MHz ferrite, keeping MCU and USB noise off the receiver. Plan C has none. Proposed: add a ferrite in series with U4's VA/VD supply, ahead of its caps.
2. **GPO2/INT unused.** The USB FM Radio wires the interrupt to the MCU through 330 Ω (AN383's R19, p8) so firmware needn't poll for tune and RDS events. Plan C polls. Optional; it needs a free U1 pin, which is a pin remap.
3. **ROUT/LOUT open.** AN383 p17 says to tie unused pins to GND (only NC pins stay open), and the USB FM Radio does. Plan C leaves them open. Proposed: tie U4 pins 23 and 24 to GND; firmware must keep the analog outputs off (digital-only OPMODE).
- Risk 1: **RCLK accuracy.** Plan C's worst case is about −92 ppm against the Si4704's ±100 ppm (bom.md chain 1), a thin margin. The reference uses a dedicated oscillator instead. Kept as designed; the first board should measure RCLK.

### 3. U1 STM32U535CEU6 (2026-10-20)

No public design uses the exact part (UFQFPN48); GitHub hits for "STM32U535CEU" were all part databases. Compared from exported netlists and ST's board manual:
- **TDT4295 board** ([fredrikr79/TDT4295-datamaskinprosjekt](https://github.com/fredrikr79/TDT4295-datamaskinprosjekt), no license, study only): **STM32U535CETx**. Same die, flash and pin map; LQFP48 instead of QFN.
- **TROPIC01 USB devkit TS1302** ([tropicsquare/tropic01-stm32u5-usb-devkit-hw](https://github.com/tropicsquare/tropic01-stm32u5-usb-devkit-hw), BSD-3-Clause-Clear): **STM32U535CCTx**, the 256 KB version. The only one that uses USB, as Plan C does.
- **CAN node** ([mrk-its/stm32-can-node](https://github.com/mrk-its/stm32-can-node), no license): **STM32U535CEUxQ**, the SMPS variant (study only). Same QFN, but pins 22–23 are the SMPS instead of VCAP.
- **ST NUCLEO-U545RE-Q** (UM3062, in the repo): STM32U545 in LQFP64. ST's own board.

Pin by pin:

| Function | Plan C | TDT4295 (CETx) | TS1302 (CCTx) | CAN node (CEUxQ) | Verdict |
|---|---|---|---|---|---|
| VDD 24, 36, 48 | 100 nF each + 10 µF | 100 nF ×4, 1 µF, 10 µF | 100 nF, 10 nF, 4.7 µF | 100 nF each + 10 µF, 22 µF | Match |
| VDDA 9 | 3V3 directly, 100 nF + 1 µF | +3.3 V directly | VCC directly | **Through a 600 Ω ferrite (FB1)**, 10 nF + 1 µF | Gap 1 |
| VBAT 1 | 3V3 | 3V3 | VCC | 3V3 | Match |
| VCAP 22 | 4.7 µF | 4.7 µF | 4.7 µF | n/a (SMPS: 2.2 µF on VDD11) | Match |
| NRST 7 | 100 nF, internal pull-up | Open | 10 nF + 33 kΩ pull-up | 100 nF + 10 kΩ pull-up | Match (an external pull-up is optional: internal 40 kΩ, DS14217 p211) |
| BOOT0 (PH3) 44 | 10 kΩ pull-down, button to 3V3 | Open | 1 kΩ pull-down, button to VCC | 10 kΩ pull-down | Match |
| USB D−/D+ (PA11/PA12) | Straight to J1 via U6 ESD | Not used | **10 Ω series each, 1.5 kΩ D+ pull-up to VCC**, PRTR5V0U2X ESD | Not used (CAN) | No change: see note |
| HSE (PH0/PH1) | Not used (USB from HSI48) | 48 MHz crystal, 6 pF | 8 MHz crystal, 10 pF | 16 MHz crystal, 10 pF | No change: see note |
| LSE (PC14/PC15) | 32.768 kHz crystal, 5.6 pF; LSCO feeds U4 RCLK | Open | Open | Test pads | Plan C only; already checked against DS14217 p188–189 |
| SWD (PA13/PA14) | Pads | 47 Ω series to a 14-pin header | Test pads | 5-pin header with NRST | Match |

Gap and notes:
1. **VDDA ferrite.** The CAN node feeds VDDA through a 600 Ω ferrite. ST's own scheme (DS14217 Figure 23, p127) shows only 100 nF + 1 µF, which Plan C follows. It matters more for Plan C than for the CAN node: VREF+ is bonded to VDDA on this package, so VDDA noise goes straight into the DAC audio that U2 transmits. Proposed: add a ferrite between 3V3 and VDDA, ahead of its caps (the same fix as U4 gap 1).
- USB: the TS1302's external 1.5 kΩ pull-up is not needed. AN2606 Table 165 (p388) says no external pull-up is needed for the U535's ROM DFU. ST's Nucleo connects D+/D− directly to its USB-C port (UM3062 p29), as Plan C does. The 10 Ω series resistors are the TS1302's own choice; no ST source asks for them.
- HSE: all three references fit a crystal. Plan C runs USB from HSI48 locked by CRS, and AN2606 (p386–388) lists no HSE need for the U535's DFU.

### 4. U5 PE42421 (2026-10-20)

Designs found, all with the exact part, compared from exported netlists:
- **LoRaPP LoRa module** ([daveshah1/LoRaPP](https://github.com/daveshah1/LoRaPP), no license, study only): single-pin control, as Plan C. SX1276 radio, 868 MHz.
- **Electronic Cats CatSniffer** ([ElectronicCats/CatSniffer](https://github.com/ElectronicCats/CatSniffer), license not stated), **Flipper Sub-GHz add-on** ([ElectronicCats/flipper-addons](https://github.com/ElectronicCats/flipper-addons)) and **Recon 2026 badge** ([ElectronicCats/badge-recon-2026](https://github.com/ElectronicCats/badge-recon-2026), GPL-3.0). One design reused on three boards: complementary-pin control (pin 6 driven as a second control line), sub-GHz.

All of them run at 433–915 MHz; none at 100 MHz. The datasheet covers 10–3000 MHz (p1).

Pin by pin:

| Pin | Plan C | LoRaPP | Electronic Cats (×3) | Verdict |
|---|---|---|---|---|
| 1 RF1 | RX to U4 via C2 1 nF | 1 nF to the receive LNA | Straight to a filter/balun IC | Match |
| 2 GND | GND | GND | GND | Match |
| 3 RF2 | TX from U2 via 1 nF and FL1 | 100 pF to the PA side | Straight to a filter/balun IC | Match |
| 4 CTRL | 1 kΩ series from SW1 (100 kΩ pull-down) | 0 Ω series, **1 nF to GND at the pin** | 100 Ω series, **1 nF to GND at the pin** | Gap 1 |
| 5 RFC | Straight to J2, D5 ESD at J2 | Straight to the antenna, ESDAXLC6 ESD at the antenna | 100 pF series into the antenna match | Match (no DC block needed at 0 V DC, p8) |
| 6 VDD | 3V3 via 1 kΩ, no cap (as the eval board, p7) | VCC rail directly | Second control line: 100 Ω series, 1 nF to GND | Match for single-pin mode |

Gap:
1. **No filter cap on CTRL.** Both designs put 1 nF from CTRL to GND at the pin. Plan C has only the eval board's 1 kΩ series resistor. Plan C needs it more: U2's TX signal (up to about 1 V rms) passes through the same part, and CTRL connects by a trace to SW1 on the board edge. Proposed: add 1 nF C0G from U5 pin 4 to GND, after the 1 kΩ. The 1 µs time constant is shorter than the switch's 1.5 µs switching time (p3) and is not a concern behind a hand-moved slider.

### 5. J1 USB4105-GF-A (2026-10-20)

Designs found, all with the exact part, compared from exported netlists:
- **AIOC ham-radio audio interface** ([skuep/AIOC](https://github.com/skuep/AIOC), MIT): a USB device with an STM32F373. The closest in purpose: radio audio over USB.
- **E-TKT label maker** ([andreisperid/E-TKT](https://github.com/andreisperid/E-TKT), MIT): a USB-C sink with an ESD array.
- **Antmicro Kria K26 dev board** ([antmicro/kria-k26-devboard](https://github.com/antmicro/kria-k26-devboard), Apache-2.0): a professional design. Its USB-C port runs through an FT4232HP with Type-C logic, so its CC wiring is not a plain sink.

Pin by pin:

| Pins | Plan C | AIOC | E-TKT | Antmicro K26 | Verdict |
|---|---|---|---|---|---|
| CC1 A5, CC2 B5 | 5.1 kΩ each to GND, D3/D4 ESD | 5.1 kΩ each | 5.1 kΩ each | Through a TVS array to the FT4232HP | Match |
| D+ A6/B6, D− A7/B7 | Pairs joined, to U6 then U1 | Pairs joined, straight to the MCU | Pairs joined, through a USB6B1 ESD array | Pairs joined, through a TVS array | Match |
| SBU A8, B8 | Open | Open | Open | Open | Match |
| VBUS A4/A9/B4/B9 | 1 µF (U3's input cap); U6 pin 5 clamps | Through a 600 Ω ferrite | Through a 750 mA polyfuse, USB6B1 clamps | 100 nF + SMF4L15CA TVS | Match (see note) |
| GND A1/A12/B1/B12 | GND | GND | GND | GND | Match |
| Shell | GND | GND | GND | Chassis net, 330 Ω ∥ 100 nF to GND | Match (a chassis net suits a board with several metal connectors) |

No gaps. Note: each design treats VBUS differently (ferrite, fuse, TVS). Plan C's is the simplest: U6 clamps VBUS, and the only source is the phone on a short cable. No change.

### 6. U3 AP2112K-3.3 (2026-10-20)

Designs found, all with the exact part, compared from exported netlists: **Solder Party RP2040 Stamp** ([solderparty/rp2040_stamp_hw](https://github.com/solderparty/rp2040_stamp_hw), license not stated), **Beepy** ([sqfmi/beepy-hardware](https://github.com/sqfmi/beepy-hardware), MIT) and **PicoROM** ([wickerwaka/PicoROM](https://github.com/wickerwaka/PicoROM), MIT). All three are USB-powered boards like Plan C.

| Pin | Plan C | RP2040 Stamp | Beepy | PicoROM | Verdict |
|---|---|---|---|---|---|
| 1 VIN | VBUS, 1 µF | VIN, 10 µF | 5 V, 10 µF | 5 V, 1 µF + 100 nF | Match |
| 3 EN | Tied to VIN | Tied to VIN | Tied to VIN | Tied to VIN | Match |
| 4 NC | Open | Open | Open | Open | Match |
| 5 VOUT | 1 µF + the rail's ≈ 11.6 µF | 10 µF + 1 µF and 100 nF bypass | 10 µF + bypass | 1 µF + bypass | Match |
| 2 GND | GND | GND | GND | GND | Match |

No gaps.

### 7. U6 USBLC6-2SC6 (2026-10-20)

Designs found, all with the exact part, compared from exported netlists: **LinHT handheld radio** ([M17-Project/LinHT-hw](https://github.com/M17-Project/LinHT-hw), license not stated), **M17 3310** ([M17-Project/M17_3310](https://github.com/M17-Project/M17_3310), license not stated), **fdcanusb** ([mjbots/fdcanusb](https://github.com/mjbots/fdcanusb), Apache-2.0, with the USB4110 sibling of J1) and **IC tester** ([jakubfi/ictester](https://github.com/jakubfi/ictester), no license).

| Pin | Plan C | All four references | Verdict |
|---|---|---|---|
| I/O1 (1, 6), I/O2 (3, 4) | D+ on 1/6, D− on 3/4, passing through from J1 to U1 (rule P2) | One pin of each pair to the connector, the other to the chip: the line passes through the part | Match (which line takes I/O1 varies) |
| 5 VBUS | VBUS at J1 | Connector VBUS, ahead of any ferrite | Match |
| 2 GND | GND | GND | Match |

No gaps.

### 8. D1 ASCB-WTF0-0A30A: no designs found (2026-10-20)

Searched: GitHub code for "ASCB-WTF0" and "ASCB-WTF0-0A30A" (0 hits) and the web (only Broadcom's datasheet). The wiring is three separate LEDs in one package, which the datasheet's pin table fixes.

### 9. D5 TPD1E0B04 (2026-10-20)

Designs found, all on an RF input at a connector, compared from exported netlists: **NexRx HF receiver** ([alanmimms/NexRx](https://github.com/alanmimms/NexRx), MIT), **USB RF power meter** ([andypfau/rf_powermeter](https://github.com/andypfau/rf_powermeter), MIT) and **TinkerRocket GNSS board** ([Tinkerbug-Robotics/TinkerRocket](https://github.com/Tinkerbug-Robotics/TinkerRocket), GPL-3.0). All use the DPY package; Plan C's DPL is the same part in a smaller package, under the same datasheet.

| Use | Plan C | NexRx | RF power meter | TinkerRocket | Verdict |
|---|---|---|---|---|---|
| Where | ANT line to GND, at J2 | Antenna line to GND, after a gas-discharge tube and 100 nF DC block at the SMA | RF input to GND, at the SMA | Antenna feed to GND, at the antenna | Match |
| Orientation | Either way (bidirectional) | Either way | Either way | Either way | Match |

No gaps.
