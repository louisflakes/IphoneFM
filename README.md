# IphoneFM

A MagSafe accessory for the iPhone 17 Pro that transmits and receives FM (88–108 MHz).
The board lies flat on the back of the phone and connects to the phone through a very short, flexible USB-C cable.
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
| Antenna connector | TE Linx CONSMA002-G (SMA, right angle) |
| TX/RX slider | Same Sky SLW-158562-5A-RA-N-D |
| Buttons (tune up/bootloader, tune down) | Panasonic EVQ-P7J01P (side-push) |
| RGB LED | Broadcom ASCB-WTF0-0A30A |

## Open items

1. Done: every chain has part numbers checked against its datasheet, including ESD protection and a TX low-pass filter; see [`design/plan-c/bom.md`](design/plan-c/bom.md).
2. Antenna (chosen 2026-10-20, prototype): Great Scott Gadgets ANT500 telescopic whip, 75 MHz–1 GHz, 20–88 cm, SMA male, with a rotating shaft and adjustable elbow (Adafruit 3584). It screws straight onto J2, which changed from RP-SMA to SMA for it (docs/decisions.md). A certified product would need a permanently attached or uniquely coupled antenna (§15.203).
3. Check transmit level against FCC §15.239 (250 µV/m at 3 m).
4. Verify on hardware: a blank U535 enters the bootloader with BOOT0 held; which slider direction is TX; the LV2285 runs from the MCU's 76 kHz drive.
5. Board outline, layout and MagSafe enclosure. Board envelope (held for now): 46.45 × 71.40 mm, ½ in in from the phone's sides and ¾ in up from its bottom edge, set by the user over Apple's no-metal zones. The layout sketch is [`design/plan-c/layout.html`](design/plan-c/layout.html); Apple's keepouts and the phone outline it overlays are in `local/apple/`, which stays on the design PC (git-ignored; Apple's drawings say not to republish). Board thickness: 1.6 mm, the only thickness any part specifies (SW1 slider drawing, SLW-158562-5A-RA-N-D p2); J2's legs are 3.90 mm (TE drawing).
6. Firmware: UAC2 asynchronous audio with feedback, SAI receive, I²C drivers, LED PWM, CC sensing, mode handling.
7. RX front end: no practical antenna at this size is 50 Ω at FM; a whip is electrically short and capacitive (AN383 p37: a 56 cm whip is 18–32 pF across the US band). So U4 FMI has a shunt matching inductor, L1 150 nH (Coilcraft 0805CS-151XJRC), after the 1 nF C2, as in AN383's whip circuit (p37, Figure 23). It's centred for the ANT500 collapsed, its usual state; the bench RSSI sweep may move it (AN383 p50–53). Every passive is populated with a best-guess value; nothing is left empty for bench work. The TX filter FL1 (designed for 50 Ω) needs bench tuning too, and FMI should be checked in TX mode against its 0.4 Vpk limit (bom.md chain 3).

## Repository layout

| Path | Contents |
|---|---|
| `design/plan-c/` | Active wiring diagram and netlist, BOM, passive package table, board layout sketch, placement rules |
| `design/archive/` | Plans A and B, no longer developed |
| `docs/decisions.md` | Design decisions and their sources |
| `docs/pcb-design-workflow.md` | PCB capture and layout workflow and rules, cited to reference books, with conflicts flagged |
| `docs/reference-designs.md` | Existing FM transmitter designs, for patterns only |
| `docs/datasheets/` | Every datasheet and spec the design was checked against, with an index |
| `tools/` | DigiKey stock scripts, diagram screenshot script, KiCad setup |
| `.mcp.json` | KiCad MCP server for Claude Code |
| `Imported/` | Notes from an earlier session, kept for later reference |
