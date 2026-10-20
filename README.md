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

1. Done: every chain has part numbers checked against its datasheet, including ESD protection and a TX low-pass filter; see [`design/plan-c/bom.md`](design/plan-c/bom.md).
2. Pick an RP-SMA antenna for 88–108 MHz.
3. Check transmit level against FCC §15.239 (250 µV/m at 3 m).
4. Verify on hardware: a blank U535 enters the bootloader with BOOT0 held; which slider direction is TX; the LV2285 runs from the MCU's 76 kHz drive.
5. Board outline, layout and MagSafe enclosure. Board thickness: 1.6 mm, the only thickness any part specifies (SW1 slider drawing, SLW-158562-5A-RA-N-D p2); RP-SMA legs are 3.90 mm (TE drawing).
6. Firmware: UAC2 asynchronous audio with feedback, SAI receive, I²C drivers, LED PWM, CC sensing, mode handling.
7. RX front end: with a true 50 Ω antenna (item 2), the 1 nF C2 into U4 FMI is enough. FMI is a high-impedance input (~4–6 kΩ in parallel with ~4–6 pF, AN383 p51–52), which a 50 Ω source drives with almost no loss. AN383's matching inductor (100–400 nH, AN383 p18–23, p37–38, p50–53) is for high-impedance antennas: headphone wires, cables and short whips. The USB FM Radio reference uses 56 nH because its antenna is a telescopic whip ([docs/reference-designs.md](docs/reference-designs.md)). Only if a short whip is chosen does FMI need a matching inductor, and any added voltage gain at FMI means rechecking TX leakage against the 0.4 Vpk limit (wiring.html, RX_RF).

## Repository layout

| Path | Contents |
|---|---|
| `design/plan-c/` | Active wiring diagram and netlist, BOM, passive package table |
| `design/archive/` | Plans A and B, no longer developed |
| `docs/decisions.md` | Design decisions and their sources |
| `docs/pcb-design-workflow.md` | PCB capture and layout workflow and rules, cited to reference books, with conflicts flagged |
| `docs/reference-designs.md` | Existing FM transmitter designs, for patterns only |
| `docs/datasheets/` | Every datasheet and spec the design was checked against, with an index |
| `tools/` | DigiKey stock scripts, diagram screenshot script, KiCad setup |
| `.mcp.json` | KiCad MCP server for Claude Code |
| `Imported/` | Notes from an earlier session, kept for later reference |
