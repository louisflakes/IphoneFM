# Reference designs

Existing FM transmitter designs. For patterns only, not for sourcing.

| Design | FM chip | Audio input | Power | Source |
|---|---|---|---|---|
| Elechouse Radio Modulator v2 | KT0803M | Analog | 3.3 V | Schematic PDF (elechouse.com) |
| KulpLights K-FMT kit | QN8027 | Analog (3.5 mm jack) | USB | [kulplights.com](https://kulplights.com/product/k-fmt-fm-transmitter-kit/) |
| DigiKey Maker: Stereo Digital FM Transmitter (2023) | KT0803L | Analog (mic or AUX) | 7–9 V DC | [digikey.com](https://www.digikey.com/en/maker/projects/stereo-digital-fm-transmitter-circuit/3c7df7d64b7f4bfcab2050a762234d3e) |

## Open KiCad layouts

Checked 2026-10-20. Neither is 2-layer; both are useful for layout patterns only.

| Design | Chips | Board | License | Source |
|---|---|---|---|---|
| USB FM Radio (anttikes) | STM32F042 + Si4705-D60, I²S to MCU, USB Audio, SMA antenna | 4 layers, GND on all layers, 54.2 × 26.5 mm, KiCad 10 | CC-BY-NC-SA (study only, do not copy) | [github.com/anttikes/usb-fm-radio](https://github.com/anttikes/usb-fm-radio) |
| FM Transceiver (Longing-Ingernot) | ESP32-S3 + KT0803L TX + RDA5807M RX, separate antenna ports | 4 layers (GND In1, 3V3 In2), 100 × 69 mm | MIT | [github.com/Longing-Ingernot/FMTransceiver](https://github.com/Longing-Ingernot/FMTransceiver) |

- The USB FM Radio's FMI front end, from its netlist: SMA J3 → CM1213 ESD diode D2 (shunt) → 1 nF C16 (series) → 56 nH L1 (shunt) → 75 Ω@100 MHz ferrite FB3 (series) → 6 pF C14 (shunt) → FMI pin 2. The 56 nH + 1 nF + ESD part follows AN383's whip-antenna circuit (§7, p37–38); FB3 and C14 are AN383's FMI emissions filter (F1, C14; p17).
