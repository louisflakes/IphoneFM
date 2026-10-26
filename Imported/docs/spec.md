# Frozen spec — v0.1 (2026-10-18)

Status: **DRAFT — waiting for Jake and the EE to sign off.** After sign-off, changes need a
dated entry in `decisions.md`.

## What it is

A small board on the back of an iPhone. It plugs into the iPhone's USB-C port. It has two modes,
one at a time:

- **Transmit:** the iPhone plays audio to the board as a USB sound card. The board transmits it
  as stereo FM to a nearby radio.
- **Receive / scan:** the board tunes FM, sends the audio back to the iPhone as a USB microphone,
  and scans the band to find empty channels for transmit.

## Hard constraints

| # | Constraint | Value |
|---|---|---|
| C1 | Size | 95–115 mm × 64–82 mm, ≤ 15 mm thick including enclosure (target 9–12 mm) |
| C2 | Power | USB-C bus power from the iPhone. No battery in v1. |
| C3 | iPhone software | No driver and no required app. Must be USB class-compliant: UAC2 audio (speaker + mic) and USB-MIDI for control. CDC serial allowed for debugging. |
| C4 | Transmit band | 88.1–107.9 MHz, 200 kHz steps (US) |
| C5 | Transmit level | FCC Part 15 §15.239: ≤ 250 µV/m at 3 m. Power set in firmware with a hard cap. Must be measured before use. |
| C6 | Receive | 87.5–108 MHz FM, RSSI/SNR per channel for scanning, RDS if the chip supports it |
| C7 | Audio quality | No cheap car-adapter sound. Targets: transmit SNR ≥ 60 dB, THD ≤ 0.5 %, 75 µs pre-emphasis, stereo, 15 kHz bandwidth. A digital path from USB to the transmitter where practical. |
| C8 | Sourcing | Every part passes the sourcing rule in `bom.md` |
| C9 | Firmware access | USB bootloader (no extra hardware needed), SWD/JTAG pads, BOOT + RESET buttons, debug serial |
| C10 | Assembly | JLCPCB PCBA (turnkey parts preferred; consigned parts only from authorized distributors) |

## Must-have board features (for the EE)

- Low-pass filter after the transmitter output (harmonics at 176–216 MHz and above)
- π-attenuator footprint in the transmit path (0 Ω by default) so output can be trimmed down
- U.FL (or similar) test point on the transmit RF path, for measurement
- Receive antenna: wire or enclosure-edge trace. A PCB trace alone is weak at 100 MHz.
- Dual transmit footprint (QN8027 + KT0803L) if layout allows; firmware finds which one is fitted over I²C
- I²C pull-ups, clean 3.3 V for the RF chips (LDO, not straight from a switcher)

## Out of scope for v1

- SDR / other bands (deferred; see `decisions.md` D-001)
- Bluetooth audio
- Battery, MagSafe magnets (mechanical choice for later)
- Transmit and receive at the same time
