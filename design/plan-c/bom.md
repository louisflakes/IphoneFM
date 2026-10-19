# Plan C bill of materials

Built one chain at a time, each checked against its datasheet. Stock is DigiKey, checked 2026-10-19.
Chains not listed yet still show values only on the [wiring diagram](wiring.html).

## Chain 1: U1 low-speed crystal (also clocks U4 RCLK)

| Ref | Part | Value / spec | Stock | Source |
|---|---|---|---|---|
| Y1 | Abracon ABS07-32.768KHZ-7-T | 32.768 kHz, CL 7 pF, ESR ≤ 70 kΩ, C0 ≤ 2.0 pF, ±20 ppm | 398,912 | ABS07 p1 |
| C (×2) | Murata GRM1555C1H5R6CA01D | 5.6 pF ±0.25 pF C0G 0402, PC14 and PC15 to GND | 98,873 | DS14217 p188–189 |

- Load caps: C = 2 × (CL − 3 pF pin parasitics − ~1.5 pF board) ≈ 5 pF → 5.6 pF. The board figure is an estimate.
- Start-up: crystal gmcrit ≈ 4 · 70 kΩ · (2π · 32.768 kHz)² · (2.0 + 7 pF)² ≈ 0.96 µA/V. Set LSEDRV to medium-high (limit 1.7 µA/V) or higher.
- Accuracy for U4 (needs ±100 ppm): ±20 initial, −0.040 ppm/°C² from a 20–30 °C turnover, ±3 aging → about −92 ppm worst case at 60 °C.

## Chain 2: U2 LV2285VB transmitter

Values from the 88–108 MHz, 75 µs application circuit (ENA1494 p4) unless noted.

| Ref / pin | Part | Value | Stock | Note |
|---|---|---|---|---|
| U2 | LV2285VB-TLM-E-SA | FM transmitter | 2,000 | Legacy part; onsemi-branded LV2285VB-TLM-E is obsolete with 18,000 left |
| Pins 1, 24 series | TDK C1608X7R1C105K080AC | 1 µF X7R 16 V 0603 | 1,062,271 | AC coupling |
| Pins 1, 24 pre-emphasis | Yageo RC0402FR-0751KL ∥ Murata GRM1555C1H152JA01D | 51 kΩ ∥ 1.5 nF C0G | 393,412 / 80,420 | 75 µs |
| Pin 4 | KEMET T491A106K010AT | 10 µF tantalum 10 V | 518,295 | Drawn polarized on p4 |
| Pin 6 | Murata GRM155R71C104KA88J | 100 nF X7R 0402 | 7,438,959 | From the AC test circuit, p11 |
| Pin 7 | Murata GRM1555C1H221JA01D | 220 pF C0G | 736,993 | Also drives D2 anode (modulation) |
| Pin 8 loop filter | Yageo RC0402FR-07510RL + KEMET T491A156K006AT | 510 Ω + 15 µF tantalum 6.3 V to GND | 367,619 / 5,919 | |
| Pin 8 loop filter | Murata GRM155R71C104KA88J | 100 nF to GND | 7,438,959 | |
| Pin 8 → D2 | Yageo RC0402FR-0710KL | 10 kΩ | 10,493,057 | |
| #3 (pin 10) | Murata GRM1555C1H271JA01D | 270 pF C0G | 480,738 | |
| #4 | Murata GRM1555C1H820JA01D | 82 pF C0G | 142,871 | |
| #5 | Coilcraft 0805CS-101XJRC | 100 nH ±5%, SRF 1.25 GHz | 9,836 | Replaces TOKO LL2012-FHL |
| #6 (pins 11–12) | Coilcraft 0805CS-331XJRC | 330 nH ±5%, SRF 650 MHz | 8,882 | Replaces TOKO LL2012-FHL |
| Pin 11 | Murata GRM155R71C104KA88J | 100 nF | 7,438,959 | |
| Pin 12 → U5 | Murata GRM1555C1H102JA01D | 1 nF C0G DC block | 4,655,333 | U5 RF pins must be at 0 V DC |
| Pin 14 | Murata GRM155R71C104KA88J | 100 nF | 7,438,959 | |
| D2 | onsemi SVC710-TL-E | Varactor, 18.5–21.5 pF @ 1 V, 3.5–4.8 pF @ 4 V | 80,615 | Obsolete; same part as p4 |
| Y2 (pin 16) | Epson TSX-3225 16.0000MF09Z-AC0 | 16 MHz, CL 9 pF, ±10 ppm | 98,801 | Datasheet gives no CL; same family as p4 |
| Pin 16 series | Murata GRM1555C1H120JA01J | 12 pF C0G | 43,887 | |
| Pin 20 | Murata GRM188R71A225KE15D | 2.2 µF X7R 10 V 0603 | 416,961 | Auto-sleep ≈ 70 s (45–300 s, p2) |
| Pin 22 drive | Yageo RC0402FR-072K2L, RC0402FR-071KL, Murata GRM155R71H103KA88D | 2.2 kΩ series, 1 kΩ to GND, 10 nF series | 123,395 / 3,538,473 / 4,003,430 | From U1 PB8 TIM16, replaces the obsolete 76 kHz crystal |
| Pins 2, 21, 23 | — | Not connected | | 2/23 unused in I²C mode (p7); 21 is the oscillator output |

## Chain 3: U4 Si4704 receiver

Values from the SSOP application schematic and BOM (Si4704/05-D60 Rev 1.2 p17–18) unless noted.

| Ref / pin | Part | Value | Stock | Note |
|---|---|---|---|---|
| U4 | Skyworks SI4704-D60-GUR | FM receiver, SSOP-24 | 2,500 | |
| C1 (pin 22 ↔ 21) | Murata GRM155R71H223KA12D | 22 nF X7R 0402 | 244,384 | Between DBYP and VA, close to VA (not to GND) |
| C4 (pin 20) | Murata GRM155R71C104KA88J | 100 nF X7R 0402 | 7,438,959 | VD to GND |
| C2 (pin 8) | Murata GRM1555C1H102JA01D | 1 nF C0G | 4,655,333 | FMI coupling; also keeps U5 RF1 free of DC (PE42421 p8) |
| R1 (pin 1 DOUT) | Yageo RC0402FR-07604RL | 604 Ω 1% | 58,904 | Datasheet 600 Ω, not a standard value |
| R2 (pin 2 DFS) | Panasonic ERJ-2RKF2001X | 2 kΩ 1% | 3,482,510 | |
| R3 (pin 3 DCLK) | Panasonic ERJ-2RKF2001X | 2 kΩ 1% | 3,482,510 | DCLK ≥ 26 ns period (p10); ours ≈ 325 ns |
| C9 (DFS, U1 side of R2) | Murata GRM1555C1H3R3CA01D | 3.3 pF C0G | 279,629 | Datasheet 2–5 pF, noise mitigation |
| RX_RST pull-down | Yageo RC0402FR-0710KL | 10 kΩ | 10,493,057 | Holds U4 in reset until firmware runs |
| I²C pull-ups (×2) | Yageo RC0402FR-076K8L | 6.8 kΩ | 228,152 | Was 3.3 kΩ. U4 VOL is specified at ≤ 500 µA (p5); 6.8 kΩ = 0.49 mA. Rise ≈ 288 ns at 50 pF, inside U4's 300 ns (p7) and U2's 1000 ns (ENA1494 p9) |
| Pins 9, 10, 12 | — | GND | | p17, p27 |
| Pins 6, 7, 11 (LPI), 23, 24 | — | Not connected | | 6/7 per p27; LPI and analog outputs unused |

## Chain 4: U1 STM32U535 support parts

From DS14217 Rev 5: Figure 23 power scheme (p127), Figure 37 NRST (p212), I/O characteristics (p203).

| Ref / pin | Part | Value | Stock | Note |
|---|---|---|---|---|
| U1 | ST STM32U535CEU6 | MCU, UFQFPN48 | 1,394 | |
| VDD 24, 36, 48 (×3) | Murata GRM155R71C104KA88J | 100 nF X7R 0402 | 7,438,959 | One per pin |
| VDD bulk | Yageo CC0805KRX5R7BB106 | 10 µF X5R 16 V 0805 | 512,367 | One for all VDD pins |
| VDDA 9 | Murata GRM155R71C104KA88J + TDK C1608X7R1C105K080AC | 100 nF + 1 µF X7R | 7,438,959 / 1,062,271 | VREF+ bonded to VDDA on this package |
| VCAP 22 | Murata GRM21BR71C475KE51L | 4.7 µF X7R 16 V 0805 | 166,059 | Needs ESR < 20 mΩ at 3 MHz and ≥ 10 V (p127). ESR not yet verified: Murata's data site blocks automated access |
| NRST 7 | Murata GRM155R71C104KA88J | 100 nF | 7,438,959 | Close to the pin; internal 40 kΩ pull-up (p211) |
| BOOT0 44 pull-down | Yageo RC0402FR-0710KL | 10 kΩ | 10,493,057 | No internal pull-down at reset; ≤ 500 nA leakage → ~5 mV (p203) |
| VBAT 1 | — | Tied to 3V3 | | Figure 23 shows no VBAT cap; UM3062 p24 ties VBAT to VDD |
| SWD pads | — | SWCLK, SWDIO, NRST, 3V3, GND | | Backup programming only |
| PC13 (tune down) | — | Internal pull-down, 30–50 kΩ | | p203 |
