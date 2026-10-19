# Design decisions

Each decision is backed by a primary source (datasheet page or spec section). Newest at the bottom.

| Area | Decision | Why | Source |
|---|---|---|---|
| USB audio | USB Audio Class 2, asynchronous endpoints with feedback | Apple's recommended class; async needs no USB-locked audio clock | Apple TN3190 |
| Power | Board draws ≤ 100 mA before enumeration, requests ≤ 500 mA | iPhone accessory rule | Apple ADG p382, p386 |
| Power | AP2112K-3.3 regulator from VBUS | 600 mA, 65 dB PSRR at 1 kHz | AP2112 p1, p4 |
| USB-C | 5.1 kΩ Rd on each CC line, sensed by ADC | Sink detection and current advertisement | USB Type-C R2.5 Table 4-28 p246 |
| Transmitter | LV2285VB, analog audio from MCU DAC | In stock, I²C tunable 88–108 MHz | LV2285VB ENA1494 |
| Receiver | Si4704, digital audio to MCU | Lets the iPhone app play received FM | Si4704/05-D60 |
| Receiver clock | Si4704 RCLK from MCU LSE on LSCO (PA2) | Si4704 can't use its own crystal with digital audio | Si4704 p14, p17 · DS14217 p45, p99 |
| MCU | STM32U535CEU6 (Plan C) | 2 KB USB buffer, 274 KB RAM, 2-ch DAC, SAI, crystal-less ROM USB DFU | DS14217 p1, p83 · AN2606 p386–388 |
| MCU | Archive Plans A (F072) and B (SAMD51) | A lacked headroom for RX; B needed a debugger | [design/archive](../design/archive/README.md) |
| Programming | BOOT0 doubles as the tune-up button; SWD pads kept as backup | ST does not publish U5 factory option bytes | DS14217 p29 · UM3062 p28 |
| Bootloader safety | CC lines on PA0/PA1, not PA7 | PA7 gets a bootloader pull-down that would pull Rd out of tolerance | AN2606 p387 |
| LED | Anode on VBUS, MCU sinks through 510/390/390 Ω | Blue/green VF up to 3.2 V leaves no headroom on 3.3 V | ASCB-WTF0 p3 · DS14217 p130, p205 |
| LED | PWM at 10-bit ≈ 156 kHz | Above the FM stereo baseband (53 kHz) and RDS (57 kHz) | DS14217 p243 |
| Antenna | RP-SMA, not standard SMA | §15.203 prohibits a standard antenna jack on a transmitter | 47 CFR §15.203 |
| RF path | PE42421 SPDT switch, one shared antenna | ≈ 85 dB typ isolation at 100 MHz protects the Si4704 (0.4 Vpk max) | PE42421 p3, p5 · Si4704 p15 |
| TX/RX mode | Slider drives the RF switch directly; MCU reads it on PB0 | Physical position always matches the RF path | PE42421 p4 |
| U1 crystal | ABS07 32.768 kHz, CL 7 pF, 5.6 pF load caps, LSEDRV ≥ medium-high | Low CL keeps start-up margin; worst case ≈ −92 ppm at 60 °C, inside U4's ±100 ppm | ABS07 p1 · DS14217 p188 · Si4704 p14 |
| U2 modulation | Pin 7 drives an SVC710 varactor in the VCO tank; it is not a test point | Corrects Plans A–C; the p4 application circuit shows it | ENA1494 p4 |
| U2 76 kHz | Drive pin 22 from U1 TIM16 (PB8) through 2.2 k/1 k + 10 nF; pin 21 open | No 76 kHz crystal is buyable (DigiKey, Findchips, JLCPCB/LCSC); pin 22 is a self-biased 0.7 V input clamped to 0–2.8 V | ENA1494 p2, p7 |
| Clocks | SYSCLK 152 MHz | 152 MHz ÷ 2000 = 76.000 kHz exactly; LED PWM becomes ≈ 148 kHz | ENA1494 p2 |
| Legacy stock | Buy LV2285VB and SVC710 together, enough for the whole run | Both are end-of-life with remaining distributor stock | DigiKey, 2026-10-19 |
| USB-C CC | Rd fitted on both CC pins | A standard C-to-C cable carries one CC wire, so the source sees one Rd (it attaches only with exactly one). A straight-through adapter would need CC2's Rd removed | Type-C R2.5 Table 3-11 p84, p186 |
