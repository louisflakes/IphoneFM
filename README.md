# IphoneFM

A MagSafe accessory for the iPhone 17 Pro that transmits and receives FM (88–108 MHz).
The board lies flat on the back of the phone and connects through a short USB-C plug-to-plug bridge (Adafruit 6367).
The iPhone sees a USB audio device: it sends audio to transmit, or plays audio the board receives.
Transmit and receive are half duplex, selected by a TX/RX slider.

## Status

Plan C is the active design. Its block-level wiring is complete and every part is sourced from a datasheet.

| Plan | MCU | Status | Why |
|---|---|---|---|
| C | STM32U535CEU6 | **Active** | Programmable over USB-C from first plug-in (ROM bootloader); meets all requirements |
| B | ATSAMD51G18A | Archived | Needed a debugger for its first flash |
| A | STM32F072CB | Archived | Scoped for transmit only; no headroom for the FM receiver |

Open the wiring diagrams in a browser. The netlist table under each diagram is the source of truth.

- Plan C: [`design/plan-c/wiring.html`](design/plan-c/wiring.html)
- Archived plans: [`design/archive/`](design/archive/)

## Plan C parts

| Function | Part |
|---|---|
| USB-C socket | GCT USB4105 |
| 3.3 V regulator | Diodes AP2112K-3.3 |
| MCU | ST STM32U535CEU6 (UFQFPN48) |
| FM transmitter | onsemi LV2285VB |
| FM receiver | Skyworks Si4704 |
| RF switch | pSemi PE42421 |
| Antenna connector | TE Linx CONREVSMA002-G (RP-SMA, right angle) |
| TX/RX slider | Same Sky SLW-158562-5A-RA-N-D |
| Buttons (tune up/bootloader, tune down) | Same Sky TS02-66-110-BK-160-LCR-D |
| RGB LED | Broadcom ASCB-WTF0-0A30A |

## Open items

1. Pick the 32.768 kHz crystal (U1) and the LV2285's 76 kHz crystal, with load capacitors.
2. Pick part numbers for local passives (LV2285 tuning set, Si4704 bypass, MCU decoupling). Values are on the diagram.
3. Pick an RP-SMA antenna for 88–108 MHz.
4. Check transmit level against FCC §15.239 (250 µV/m at 3 m).
5. Verify on hardware: a blank U535 enters the bootloader with BOOT0 held; which slider direction is TX.
6. Board outline, layout and MagSafe enclosure.
7. Firmware: UAC2 asynchronous audio with feedback, SAI receive, I²C drivers, LED PWM, CC sensing, mode handling.

## Repository layout

| Path | Contents |
|---|---|
| `design/plan-c/` | Active wiring diagram and netlist |
| `design/archive/` | Plans A and B, no longer developed |
| `docs/decisions.md` | Design decisions and their sources |
| `docs/reference-designs.md` | Existing FM transmitter designs, for patterns only |
| `tools/` | DigiKey stock scripts and diagram screenshot script |
| `Imported/` | Notes from an earlier session, kept for later reference |
