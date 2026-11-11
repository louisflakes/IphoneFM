# Rev B pre-order checks (2026-11-07; Rev C fan-out 2026-11-11)

What was checked before ordering, beyond DRC/ERC and the check scripts (build-procedure.md B7), aimed at what could go
wrong once the boards arrive. Everything below passed unless it says otherwise.

## Pins and nets, from the board file itself

| Part | Checked against | Result |
|---|---|---|
| U8 IS31FL3236A | Lumissil DS Rev. I p3 pin table (QFN-44) | 1–16 OUT3–18, 17/39/pad GND, 18–35 OUT19–36, 36 SDB → LED_SDB, 37 AD → GND, 38 VCC → VBUS, 40 R_EXT → R28 → GND, 41 SDA, 42 SCL, 43/44 OUT1/2 open, 34/35 OUT35/36 open |
| DS1–DS4 GS3011AW-B | Guangcai GS3011A/CX-X p3 | 7 A, 6 B, 4 C, 2 D, 1 E, 9 F, 10 G, 5 DP, 3/8 common anode (VBUS) on all four |
| SW4 SIQ-02FVS3 | Mitsumi p3 | 1 A → PA3, 2 S → PA5, 3 C → GND, 4 B → PA4, frame tabs 5–10 → GND; R30–R32 10 kΩ to 3V3 on A, B, S |
| SW3 DHN-06-V | Diptronics p41 | Pins 1–6 ATT_C16…C0_5, 7–12 3V3; the "ON" side is the 7–12 row |
| R29, C42–C44 | netlist.json | SDB 100 kΩ to GND; 1 µF + 100 nF + 10 µF VBUS to GND |
| U1 | bom.md pin map (DS14217 Tables 26–28, AN2606) | pin 2 PC13 → SDB, 13–15 PA3–PA5 → encoder, 43/45 I²C |

## Electrical limits

| Item | Limit (source) | On this board |
|---|---|---|
| U8 logic high on SDA, SCL, SDB | VIH ≥ 1.4 V at VCC 2.7–5.5 V (Lumissil p5) | 3.3 V from U1: fine with U8 on 5 V |
| U8 supply | 2.7–5.5 V (p5) | VBUS |
| Segment current | IMAX = 58.5 × 1.3 V / REXT (p11) | R28 10 kΩ: 7.6 mA; digits allow 30 mA |
| Driver headroom | 0.6 V max at 20 mA (p5) | VBUS 4.75 V − VF 3.8 V max = 0.95 V at the worst |
| VBUS drop to the display | — | 0.4 mm tracks, about 0.09 Ω J1 to U8: ≤ 22 mV at the full 252 mA |
| Anode current per digit | — | ≤ 61 mA through pin 8 (pin 3 joined inside the part) |
| I²C addresses | AD = GND → 0x3C (p6); Si4705 0x11 | No clash |

## JLC

| Item | JLC (capabilities page, read 2026-11-07) | Ours |
|---|---|---|
| Track / gap, 2-layer | 0.10 / 0.10 mm | 0.127 in U8's fan-out areas, 0.20 elsewhere |
| Via | 0.15 mm hole / 0.25 mm pad; JLC prices any hole under 0.3 mm as high-precision (plugged vias, 4-wire test: about $51 more for 5 panels) | Rev C: 0.30 / 0.45 in the fan-out (ring 0.075, JLC's preferred), 0.30 / 0.60 elsewhere; JLC quotes it as a standard board ($7.50 for 5 bare panels, 2026-11-11) |
| Via hole to track | 0.20 mm | 0.20 mm at the closest (fan-out: via centre 0.4155 mm from a 0.127 mm line) |
| Copper to routed edge | 0.20 mm | 0.50 mm |
| Unplated holes | 0.50 mm min; no tolerance listed | SW4 bosses Ø1.6 (Mitsumi +0.05/−0) for Ø1.55 (−0.05/0) bosses, drawn as Rev A's locating holes |
| Reflow | ~245 °C lead-free | GS3011: 245 ± 5 °C, 260 max, ≤ 2 passes; SIQ-02FVS3 reflow type; DHN-06-V lead-free solderable |

Stock (2026-11-07, JLC's own figures for the new and scarce parts, LCSC for the rest), against 6 boards: every
line covered. U8 6,136; GS3011AW-B 798 (24 needed); SIQ-02FVS3 1,339; DHN-06-V 14,336; Si4705 (U4) 43, DigiKey as in
Rev A. The 1 nF C1523 (C31, C34) shows 0 at LCSC but 2,293,930 in JLC's basic stock. U1 is global sourcing, as Rev A.

Placement rotations: JLC places each part with its EasyEDA footprint. The new parts' EasyEDA footprints (read from
EasyEDA's public component API, which JLC's viewer draws from) were fitted to ours pin by pin over all four turns,
as Rev A's JLC_FIX was found:

| Part | Turn | Origin shift | Worst pin after the fit |
|---|---|---|---|
| U8 QFN-44 | 270° | — | 0.04 mm (pins 17/39 differ only by our joins to the centre pad) |
| SW3 DHN-06-V | 270° | — | 0.23 mm (JLC's rows 6.6 mm apart, Diptronics' 6.15) |
| SW4 SIQ-02FVS3 | 0° | 2.44 mm toward the terminals | 0.00 mm (terminals); frame tabs within 0.6 mm, LCSC's known angled-tab offset |
| DS1–DS4 | 0° | — | 0.00 mm |
| R28–R32, C42–C44 | 0° | — | under 0.08 mm (pad sizes) |

Added to `tools/jlc_outputs.py` (JLC_FIX); the CPL is rebuilt with them. JLC's own 3D preview at upload is the last
look, as for Rev A.

## For firmware: the display

U8 at I²C 0x3C (7-bit). Write a segment's brightness to its PWM register (0x00 + n for OUTn), set its LED control
register (0x25 + n) to 0x01 (on, full IMAX), write 0x00 to 0x25 to latch, 0x01 to 0x00 to leave shutdown, and drive
PC13 high (SDB). A segment lights when its OUT sinks: the digits are common anode on VBUS.

| Segment | DS1 | DS2 | DS3 | DS4 |
|---|---|---|---|---|
| A | OUT30 (pin 29) | OUT26 (pin 25) | OUT4 (pin 2) | OUT12 (pin 10) |
| B | OUT29 (pin 28) | OUT25 (pin 24) | OUT6 (pin 4) | OUT3 (pin 1) |
| C | OUT16 (pin 14) | OUT20 (pin 19) | OUT24 (pin 23) | OUT7 (pin 5) |
| D | OUT15 (pin 13) | OUT19 (pin 18) | OUT23 (pin 22) | OUT9 (pin 7) |
| E | OUT14 (pin 12) | OUT18 (pin 16) | OUT22 (pin 21) | OUT11 (pin 9) |
| F | OUT31 (pin 30) | OUT27 (pin 26) | OUT34 (pin 33) | OUT10 (pin 8) |
| G | OUT32 (pin 31) | OUT28 (pin 27) | OUT33 (pin 32) | OUT8 (pin 6) |
| DP | OUT17 (pin 15) | OUT21 (pin 20) | OUT13 (pin 11) | OUT5 (pin 3) |

DS1 is the digit nearest U8; with the board turned so its right edge is up, the digits read DS1 to DS4 left to
right. OUT1, OUT2, OUT35 and OUT36 are open. The encoder: A on PA3 and B on PA4 are both open (high) at every detent,
the push switch on PA5 reads low when pressed.
