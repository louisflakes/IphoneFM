# IphoneFM

A MagSafe accessory for the iPhone 17 Pro that transmits and receives FM (88–108 MHz).
The board lies flat on the back of the phone and connects to the phone through a very short, flexible USB-C cable.
The iPhone sees a USB audio device: it sends audio to transmit, or plays audio the board receives.
Transmit and receive are half duplex, selected by a TX/RX slider. Three thumbwheels set the frequency; a DIP switch sets the transmit level.

The project also asks a question: can Claude design a working PCB, from requirements to a board JLCPCB assembles in full?

## Status

**Rev A** is the active design: the analog-FM rendition, option D2. The MCU computes the FM modulation and streams it over I²S to a TI LMX2571 synthesizer, whose internal VCO is the carrier ([modulation-strategies.md](design/rev-a/modulation-strategies.md)). Every part is checked against its datasheet, every pin is mapped to a net, and the placement is agreed. Next: the KiCad build, following [kicad-build-procedure.md](design/rev-a/kicad-build-procedure.md) one step at a time.

| Design | Transmitter | Status |
|---|---|---|
| Rev A (analog FM, D2) | TI LMX2571, direct digital FM | **Active** |
| Plan C | onsemi LV2285VB | Archived: the transmitter is obsolete and needs a large minimum order |
| Plans A, B | | Archived |

## Rev A design files (`design/rev-a/`)

| File | What it is |
|---|---|
| [netlist.json](design/rev-a/netlist.json) | **Source of truth:** every part (designator, part number, JLC code, package) and every pin with its net |
| [bom.md](design/rev-a/bom.md) | Why each part and value was chosen, chain by chain, with datasheet pages |
| [wiring.html](design/rev-a/wiring.html) | Wiring diagram and netlist table |
| [layout.html](design/rev-a/layout.html) | True-size parts on the board envelope, and the Rev A placement |
| [placement-rules.md](design/rev-a/placement-rules.md) | Placement rules, with the user's feedback |
| [sourcing.md](design/rev-a/sourcing.md) | Key parts, JLC stock and second routes |
| [modulation-strategies.md](design/rev-a/modulation-strategies.md) | Why direct digital FM on the LMX2571 |
| [verification.md](design/rev-a/verification.md) | The checks that keep every file, and later KiCad, in step |
| [kicad-build-procedure.md](design/rev-a/kicad-build-procedure.md) | The KiCad build, one reviewed step at a time |

The KiCad project goes in `kicad/rev-a/`. Open the `.html` pages in a browser; `layout.html` needs `local/apple/phone-outline.js`, which stays on the design PC (Apple's drawings say not to republish it).

## Checks

```
python tools/netcheck.py                      # netlist.json against itself, bom.md and wiring.html
python tools/kicadcheck.py --net … --pcb …    # KiCad's exports against netlist.json and the Rev A placement
python tools/kicadcheck_test.py               # proves kicadcheck catches real faults
```

## Open items

1. KiCad build: [kicad-build-procedure.md](design/rev-a/kicad-build-procedure.md).
2. Before ordering: re-run JLC stock for the thin parts (Si4705, LMX2571) and the two global-sourcing parts (STM32U535, TDP06 DIP).
3. Bench checks on the first boards: which slider direction is TX (TP4); the SMA's centre contact; transmit level and harmonics in the Faraday cage against FCC §15.239 as a target; the receiver's matching inductor L1 by RSSI sweep (AN383 p50–53); 3V3 current.
4. Firmware: UAC2 audio, FM stereo multiplex and pre-emphasis, the I²S deviation stream to the LMX2571, receiver control over I²C, wheels, DIP-aware power setting, LED.
5. MagSafe enclosure (user-owned), with slots for the wheels, slider, DIP levers and USB-C, and a light pipe for the LED.

## Repository layout

| Path | Contents |
|---|---|
| `design/rev-a/` | The active design (above) |
| `kicad/rev-a/` | The KiCad project |
| `design/archive/` | Plans A, B and C, no longer developed |
| `docs/decisions.md` | Design decisions and their sources |
| `docs/pcb-design-workflow.md` | PCB capture and layout workflow and rules, cited to reference books, with conflicts flagged |
| `docs/reference-designs.md` | Existing FM transmitter designs, for patterns only |
| `docs/datasheets/` | Every datasheet and spec the design was checked against, with an index |
| `tools/` | Design checks, DigiKey/JLC stock scripts, KiCad setup |
| `.mcp.json` | KiCad MCP server for Claude Code |
| `Imported/` | Notes from an earlier session, kept for later reference |
