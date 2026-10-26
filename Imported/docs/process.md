# Process — gates and tools

## Gates

Nothing moves to the next gate until it passes review against `spec.md`.

| Gate | Output | Pass criteria | Who signs off |
|---|---|---|---|
| 0. Spec | `spec.md` v1.0 | Jake + EE agree | Jake |
| 1. Sourcing audit | `bom.md` with live stock for every part | Every part passes the sourcing rule | Jake |
| 2. Schematic | KiCad schematic + `hardware/connections.md` | ERC clean, netlist diff matches `connections.md`, EE review | EE |
| 3. Layout | KiCad PCB | DRC clean, fits C1, RF/USB/audio routed by EE, EE review | EE |
| 4. Order | Gerbers, BOM, CPL for JLCPCB | Stock rechecked the same day | Jake + EE |
| 5. Bring-up | Firmware on real boards | USB enumerates on iPhone, transmit level measured ≤ Part 15 | Jake |

Firmware work starts in parallel with Gate 2 on dev modules (ESP32-S3 dev board + breakouts).

## Tools

- **KiCad 10** with the KiCad API turned on (Preferences → Plugins)
- **kicad-mcp-pro** (MIT) — https://github.com/oaslananka/kicad-mcp-pro — set up in `.mcp.json`.
  Starts in the read-only `default` profile. Use the `build` (write) profile only inside this repo.
- **kicad-cli** — netlist export, ERC/DRC from the command line
- **git** — every change is a commit

## KiCad MCP guardrails

Lessons from JLCPCB's write-up
(https://jlcpcb.com/blog/kicad-mcp-how-to-design-a-pcb-with-claude-code):

1. **ERC can pass with a short in it.** Overlapping net labels shorted two nets there and ERC only
   warned. → After every schematic change, export the netlist and diff it against
   `hardware/connections.md`.
2. **Multi-unit parts** (dual op-amps etc.) can stack or fail to wire. → Check every unit is placed and connected.
3. **No autorouter, and naive routing is bad.** Their first pass ran a feedback trace next to a
   switching node. → Claude does not route RF, USB or audio. The EE does.
4. **Part search in the server was unreliable.** → Check parts directly against JLCPCB/LCSC.
5. **Batch operations can run twice** (they got a duplicate board outline). → Check the result after every batch.
6. **Connection failures:** only one KiCad window open, no modal dialog waiting, board open in the PCB Editor.
7. **Zero DRC errors ≠ correct design.** Human review at every gate.
