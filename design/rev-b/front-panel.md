# Rev B front panel: tuning, station display, power DIP

Replaces Rev A's three thumbwheel pots (RV1–RV3) and the out-of-stock side-lever DIP switch (SW3). Chosen by the user
2026-11-06 from `front-panel-candidates.png`. Datasheets in [docs/datasheets/rev-b/](../../docs/datasheets/rev-b/).

| Role | Part | LCSC, JLC stock (2026-11-06) | Checked against the datasheet |
|---|---|---|---|
| Tuning | **Mitsumi SIQ-02FVS3** edge thumbwheel encoder | C2925423, 1,350 (also SAMZO C29780879, XUNPU C42416825, Shou Han C56192303) | 15 detents (24° each), A/B quadrature, plus a slide switch worked by pushing the wheel in: turn and press. Ø14.5 mm dial, 4 mm tall, reflow (S3). 0.5 mA, 5 V. Land pattern p3 |
| Station display | **4 × Guangcai GS3011AW-B**, 0.3" single digit, white, black face, common anode | C22462661, 818 | 12 × 7.3 mm each (four in a row ≈ 31 mm), 3.75 mm tall. White VF 3.0 typ / 3.8 V max at 10 mA, 60–180 mcd, IF max 30 mA. Anodes pins 3 and 8 (p2–4) |
| Display driver | **ISSI IS31FL3236A**, 36-channel constant-current LED driver | C246443, 6,185 | 2.7–5.5 V; I²C, logic high ≥ 1.4 V at 5.5 V, so 3.3 V logic is fine at a 5 V supply; headroom 0.4–0.6 V at 20 mA; 256-step PWM per channel at 3 or 22 kHz; SDB pin shuts it down; 4 I²C addresses. QFN-44 5 × 5 mm, 0.4 mm pitch |
| Power DIP | **Diptronics DHN-06-V-T/R**, 6-position, top lever, 1.27 mm | C224997, 14,336 | 1.6 mm tall, 25 mA / 24 V, gold contacts, 1,000 operations. PCB layout on p1 |

## How they connect (to be drawn in the schematic)

- **Display:** the 32 segments (4 digits × 8, including the decimal point) each go to one IS31FL3236A output; digit anodes go to VBUS.
  Static drive, so nothing is multiplexed and there is no flicker or scan noise. The driver runs from VBUS as well, because its
  outputs may not rise above its own supply (absolute maximum VCC + 0.3 V), and with the anodes on 5 V an off segment's
  output sits near 5 V. White VF up to 3.8 V leaves about 0.6–1 V headroom from a 4.75–5 V VBUS.
- **Bus:** the driver shares I²C with the Si4705, with pull-ups to 3V3 (address 0x3C–0x3F, no clash with the Si4705).
- **Off at power-up:** SDB is held low by a pull-down until firmware runs, so the display draws nothing before USB set-up
  (Apple's 100 mA limit).
- **Encoder:** A, B and the push switch to three MCU inputs, common to GND, with pull-ups. The three ADC pins the wheels used
  are freed.
- **DIP switch:** wired as Rev A's SW3 to the PE43711's parallel inputs, with 10 kΩ pull-downs.

## Current

At 3 mA a segment, "107.9" lights 21 segments: about 65 mA from VBUS, plus about 9 mA for the driver. Firmware sets the
brightness, and the display stays well inside the 500 mA available after USB set-up.
