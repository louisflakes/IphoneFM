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
