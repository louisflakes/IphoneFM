# Holding the carrier without killing the bass

Decision brief, 2026-10-21. It replaces the single coarse/fine proposal in bom.md chain 6.

## Requirement

- **Audio response:** flat from 20 Hz to 20 kHz, designed for **10 Hz to 25 kHz**.
- **Stereo:** the signal reaches 53 kHz.
- **Deviation:** ±75 kHz.
- **Carrier:** locked to the 20 MHz crystal.
- **Assembly:** every part assembled by JLC.

## Why it's hard

The audio moves the oscillator's frequency. A PLL that holds the carrier treats any slow movement as an error and cancels it. So with modulation at the oscillator, the PLL acts as a high-pass filter on the audio, with its corner near the loop bandwidth.

To stay within about 0.3 dB at 10 Hz, the loop has to cross over near **1 Hz**. Our LC oscillator tunes at about 13 MHz/V, and the ADF4002's smallest charge-pump current is 0.294 mA (ADF4002 Figure 18, p13). A 1 Hz analog loop then needs:

| PLL's share of tuning | C1 | C2 | 10 Hz response |
|---|---|---|---|
| Full (direct) | 26,000 µF | 342,000 µF | +0.3 dB |
| ÷100 (coarse/fine) | 265 µF | 3,400 µF | +0.3 dB |
| ÷300 | 88 µF | 1,100 µF | +0.3 dB |
| ÷30 at a 30 Hz loop (the earlier proposal) | 1.0 µF | 12.7 µF | Fails: bass rolls off below about 60 Hz |

Second-order passive loop, 60° phase margin.

## Strategies

| | Strategy | 10 Hz – 25 kHz? | Hardware change | Firmware | Main risk |
|---|---|---|---|---|---|
| A | Analog charge-pump loop (ADF4002), with or without coarse/fine split | **No** with practical parts | Small | Small | Bass loss, or mF capacitors |
| B | Software PLL: ADF4002 used only as a divider; the MCU closes a ~0.1 Hz loop | **Yes** | Small (two RC paths) | Large: loop, calibration | Oscillator noise faster than 0.1 Hz is not corrected |
| C | Two-point modulation: audio into a fractional-N PLL's divider *and* the oscillator, gains matched | **Yes** | Medium | Large: gain matching | Mismatch distorts the response |
| D | Direct digital FM: the MCU streams the stereo signal into a fractional-N PLL (TI LMX2571) whose loop is wider than the audio | **Yes** (DC to about 100 kHz) | Medium: new PLL chip | Medium: I²S stream, setup | Deviation setup and sampling sidebands |
| E | Lock, then hold the tuning voltage while transmitting | Yes | Small | Small | Carrier drifts; relocking clicks |

### A. Analog loop (current plan)

The table above rules it out for a 10 Hz requirement. A loop near 30 Hz with tantalum capacitors is buildable, but bass below about 60 Hz rolls off.

### B. Software PLL ("Huff-and-Puff" style)

- **How it works:**
  - The ADF4002's MUXOUT outputs its N-divider signal (carrier ÷ N, about 100 kHz; Figure 18, p13).
  - An MCU timer timestamps those edges against the 20 MHz crystal timebase.
  - A firmware loop with about 0.1 Hz bandwidth trims the varicap. The actuator is DAC channel 2 for coarse steps plus a 16-bit PWM through a ÷30 divider for fine steps (about 20 Hz per step), both RC-filtered near 1 Hz.
  - Audio enters the varicap from DAC channel 1, as in chain 5.
- **Response:** flat from well under 1 Hz.
- **Precedent:** Huff-and-Puff stabilizers, which correct an LC oscillator slowly through a varicap: G7IXH (QEX, Nov. 1998), PA0KSB, and Hans Summers' versions ([hanssummers.com](https://hanssummers.com/huffpuff/minimalist/1chip.html), [PY2OHH](https://qsl.net/py2ohh/trx/huffpuff1/huffpuffpa0ksb.htm)).
- **Costs:**
  - The free-running oscillator's noise and fast drift pass straight through, so audio hiss is set by the oscillator itself. That isn't quantified yet.
  - Deviation varies about 2–3× across the band, so firmware needs a per-channel table. The MCU can measure it itself through the divider.
  - The ADF4002's charge pump goes unused.

### C. Two-point modulation

Low audio frequencies go into the PLL's divider, and high frequencies go into the oscillator. When the two gains match, the PLL's high-pass and low-pass responses sum to a flat response. This is a standard technique, for example [US 6,674,331](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6674331) on tuning a two-point modulated PLL; known here from search summaries, not a full read. This needs a fractional-N PLL that accepts modulation (the LMX2571 below), plus a gain match across the band. That match varies with the oscillator's tuning gain, so it needs calibration. With this chip, D does the same job more simply.

### D. Direct digital FM through a wide-loop fractional-N PLL (TI LMX2571)

- **How it works:**
  - The MCU computes the stereo signal as today, but sends it as 16-bit frequency-deviation words over I²S, from one SAI1 sub-block (the MCU has two independent ones; DS14217 p80).
  - The LMX2571 adds each word to its fractional divider ("FSK I2S mode", up to 100 MHz I²S clock, 17 clocks per frame; datasheet p13). Arbitrary-level FSK "can be used to construct… analog-FM modulation" (p10).
  - The loop bandwidth is set at or above the sample rate, so the whole stereo signal passes (TI SNAA309 §6.1).
- **Why it fits:**
  - The response runs from DC to roughly the loop bandwidth (about 100+ kHz).
  - Deviation is linear across the band, with no per-channel calibration (SNAA309 §6.3).
  - The wide loop also cleans up the oscillator's own noise.
  - TI lists wireless microphones as an application (datasheet p1), and SNAA309 walks through an analog-FM example.
- **Numbers (datasheet SNAS654A):**
  - OSCin: 10–150 MHz, so the 20 MHz reference works (p5).
  - FSK: 100 kSPS with a 200 kHz loop (p6).
  - Deviation: ±39 kHz in TI's test configuration, widened by using a smaller fractional denominator (SNAA309 §6.2; ±75 kHz plus margin is within reach at fPD = 20 MHz).
  - Sampling sidebands: they drop 12 dB per doubling of the sample rate, and TI recommends at least about 100 kHz (SNAA309 §6.3). We would stream 228 kHz or more.
- **Two hardware variants:**
  - **D1, external VCO.** Keeps our discrete transistor oscillator. The LMX2571 needs an external oscillator of at least 100 MHz (p6), so ours would be redesigned for **176–216 MHz**. The LMX2571 divides by 2 and outputs 88–108 MHz from its RF buffer (10–1400 MHz, p6). Its 5 V charge pump would run from VBUS.
  - **D2, internal VCO.** The LMX2571 makes 88–108 MHz by itself (10–1344 MHz, 0 dBm, second harmonic −25 dBc; p6). The discrete oscillator, varicap and buffer go away. This is the most certain variant, but no longer a transistor oscillator.
- **Part:** LMX2571NJKR. JLC C440388: 139 in stock. DigiKey: 1,244 (NJKR) and 1,386 (NJKT), cut tape, MOQ 1, $14–17. WQFN-36, 6 × 6 mm. It replaces the ADF4002, and DAC channel 1 is no longer needed for transmit audio.
- **Open:**
  - Loop-filter and deviation numbers, to be designed with TI's PLLatinum Sim tool.
  - For D1, the 2× oscillator design.
  - SAI clocking for both sub-blocks.
  - The VCP filter from VBUS.
  - TI's published example is narrowband (2 kHz deviation), and wideband FM-broadcast use rests on the same mechanism plus forum reports (TI E2E: a customer FM setup with a 204.8 kHz loop).

### E. Lock and hold

Lock the PLL, then freeze the tuning voltage with a sample-and-hold while transmitting, as in the Gamma Electronics design ([page](https://www.gammaelectronics.xyz/transmitter-projects-DIY_8.html)). The audio is flat, but the carrier drifts until the next relock, and each relock is audible. Not recommended.

## Where it lands

- **D (LMX2571)** is the one that meets the audio requirement *and* holds the carrier tightly with the least ongoing calibration.
  - **D1** keeps the transistor oscillator, at the cost of redesigning it at 2×.
  - **D2** is the most certain path.
- **B** keeps today's board almost unchanged and meets the audio requirement. It relies on more firmware and accepts the free-running oscillator's noise.
- **A** can't meet 10 Hz with practical parts.

Datasheets saved: `PLL_TI_LMX2571_SNAS654A.pdf`, `AN_TI_SNAA309_LMX2571_FSK.pdf`.

## D2 in depth: LMX2571 with its internal VCO (2026-10-21)

All page numbers are from SNAS654A unless noted.

### Features beyond FSK, and what each does for us

| Feature | Where | Use here |
|---|---|---|
| Direct digital FM (FSK I²S mode, arbitrary-level FSK) | p10, p13, p35–37; SNAA309 | The MCU streams the stereo signal as frequency steps. Deviation is the same on every channel, and the response runs from DC up to the loop bandwidth |
| **Output auto-mute** (OUTBUF_AUTOMUTE, on at reset) | p23 | Outputs stay muted until the PLL locks, at power-up and after every frequency change. **Replaces the MMBT3904 lock gate.** It does not mute if lock is lost later, so firmware also watches lock detect on MUXout |
| **Programmable output power** (OUTBUF_TX_PWR, 0–31) | p42 Figure 61 | About −18 to +3 dBm. Firmware power control (~20 dB) on top of the DIP-switch attenuator (31.5 dB) |
| Output buffer type: push-pull or open-drain | p42 Table 38 | Push-pull is a square wave: 3rd harmonic about −12 dBc at 480 MHz. Open-drain with an LC pull-up brings the 3rd–5th down to about −18 to −40 dBc. FL1 still follows |
| Two outputs, built-in T/R switch, two stored frequencies (F1/F2) switched by the TrCtl pin | p10, p37 | Available. In receive mode the chip should be powered down with CE, so its carrier can't interfere with the Si4705 |
| Integrated LDOs; single 3.3 V supply; logic accepts 1.8 V | p10, p54 | No low-noise regulator needed. VcpExt still needs 3.3 V or 5 V in synthesizer mode (p54) |
| Third and fourth loop-filter poles inside the chip, programmable | p11 | Only a 3-part filter on the board |
| MULT reference multiplier (up to ×6 before it adds noise) | p11, p42 | Raises the phase-detector frequency. Needed for the deviation plan below. Requires an XO, not a crystal, which we already have |
| Register readback on MUXout; lock detect | p14, p23 | Firmware can confirm configuration and lock |
| VCO calibration holds over −40 to +85 °C | p12 | No recalibration while running |
| 24-bit delta-sigma, programmable order and dithering | p11 | Spur tuning if needed |

### Frequency plan

- **VCO:** 4300–5376 MHz (p6).
- **Output dividers:** CHDIV1 (4–7) × CHDIV2 (1–64) (p12).
- **Divider ÷56** covers 88.1–95.9 MHz. **÷48** covers 96.1–107.9 MHz (it reaches from 89.6 MHz). **÷40** is unused.

### Deviation headroom (checked for all 100 US channels)

- **Step size:** steps = round(f_dev × DEN / f_PD) × CHDIV / prescaler (Equation 4, p35). One step must stay within ±32,767, and the channel's fractional numerator must stay at least one full swing away from 0 and from DEN (SNAA309 §6.2).
- **Target:** ±100 kHz, which is ±75 kHz plus margin.
- **At 20 MHz alone:** 13 channels fail.
- **With two reference settings,** picked per channel by firmware, every channel passes:
  - **f_PD = 40 MHz** (MULT ×2) with DEN = 400,000.
  - **f_PD = 100 MHz** (MULT ×5) with DEN = 1,000,000.
- **Resolution:** one step is 3.6 Hz at the output on ÷56 (4.2 Hz on ÷48). ±75 kHz is about ±21,000 steps, roughly 15 bits.

### Loop filter (first pass; to be finalised in TI's PLLatinum Sim)

Second-order passive filter, 60° phase margin, internal VCO about 56 MHz/V (p6):

| Loop bandwidth | C1 | C2 | R2 | Charge pump (f_PD 40 / 100 MHz) | Gain / phase at 15 kHz | Gain / phase at 53 kHz |
|---|---|---|---|---|---|---|
| 250 kHz | ~110 pF | ~1.4 nF | ~1.6 kΩ | 2.19 / 0.94 mA | +0.11 dB, −0.2° | +0.96 dB, −4.9° |
| 400 kHz | ~105 pF | ~1.35 nF | ~1.1 kΩ | 5.31 / 2.19 mA | +0.04 dB, −0.0° | +0.48 dB, −1.5° |

- **One filter for both settings:** firmware scales the charge-pump current with the reference setting (programmable in 312.5 µA steps up to about 7.2 mA, p5), so a single filter serves both.
- **Stereo:** the small lift near 53 kHz affects stereo separation. It's fixed in the MCU with a short pre-equaliser, since the loop response is known.

### Sample rate

- **The constraint:** sample-and-hold images of the stereo signal land near f_s − 53 kHz. If that's inside the loop bandwidth, it becomes out-of-channel FM.
- **The fix:** stream at about **912 kSa/s** (48 × 19 kHz), interpolated in the MCU. The first image then sits about 860 kHz out, beyond a 250–400 kHz loop.
- **Interfaces:** I²S needs at least 17 clocks per frame, so about 15.5 MHz, well under the LMX2571's 100 MHz (p13). STM32U535 SAI1 runs each sub-block master with its own clock generator (DS14217 p80): one streams to the LMX2571, the other receives from the Si4705 at 48 kHz.

### What D2 changes on the board

- **Removed:**
  - U2 ADF4002 and its RF sample network.
  - Chain 5's oscillator, buffer and lock gate: Q1, Q2, Q3, D2 1SV322, L1, and their resistors and capacitors.
  - The DAC-to-varicap audio path.
- **Added:**
  - LMX2571, with 100 nF on Vcc3p3, VccIO, VcpExt and Bypass, and 100 nF + 2.2 µF on VrefVCO/VregVCO (Figure 62, p44).
  - The 3-part loop filter.
  - A 100 pF output coupling capacitor (or the open-drain LC pull-up).
  - MCU lines: SPI (CLK, DATA, LE) and SAI-A (CLK, FS, DATA), plus CE, MUXout and TrCtl.
- **Unchanged:** Y2 (now also feeding OSCin), the PE43711 and DIP switch, FL1, U5, J2 and D5, the receiver, USB and the MCU.
- **The DAC is freed:** it no longer carries transmit audio.

### Still open for D2

- Loop filter and spurs in PLLatinum Sim.
- Push-pull or open-drain output, and the FL1 re-check for square-wave harmonics.
- The stereo pre-equaliser.
- Powering the LMX2571 down in receive mode.
- Stock: JLC 139 (LMX2571NJKR), with DigiKey as the second route.
