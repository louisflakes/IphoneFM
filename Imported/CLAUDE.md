# iPhone FM Radio — instructions for Claude

You are working on a USB-C iPhone accessory: an FM transmitter (Part 15 legal) that is also an
FM receiver / channel scanner (not at the same time). Jake owns the project. An electrical-engineer
friend designs, tests and orders the boards. Claude writes and tests the firmware live over USB-C,
and helps build the schematic in KiCad through the KiCad MCP server.

Read these before doing anything:
- `docs/spec.md` — the frozen spec. It is the contract. Do not change it without Jake saying so.
- `docs/bom.md` — selected parts, verified stock, and the sourcing rule.
- `docs/process.md` — the gate process and KiCad MCP guardrails.
- `docs/decisions.md` — the decision log. Add an entry for every decision.

## Rules (the reason these exist: we flip-flopped before)

1. **Never state a price or stock level from memory.** Check it live (LCSC / JLCPCB parts
   library / DigiKey / Mouser) and record the date in `docs/bom.md`.
2. **No guessing.** If something can't be verified or isn't feasible, say so plainly.
3. **Every part must pass the sourcing rule** in `docs/bom.md` before it goes in the schematic.
4. **Every decision goes in `docs/decisions.md`** with the date and the reason. Don't reopen a
   closed decision unless new evidence appears, and write down the evidence.
5. **Passing ERC is not proof.** After every schematic change, export the netlist with
   `kicad-cli` and diff it pin-by-pin against `hardware/connections.md`.
6. **Don't route RF, USB or audio traces.** Place parts and run checks; the EE routes these.
7. **Commit small.** One logical change per commit, so the EE can review the diff.

## Layout of the repo

- `hardware/` — KiCad project (to be created), `connections.md` (intended netlist)
- `firmware/` — ESP32-S3 firmware (ESP-IDF + TinyUSB), to be created
- `docs/` — spec, BOM, process, decisions

## Who to ask

- Spec, scope, budget → Jake
- Layout, RF, manufacturability → the EE friend (via Jake, or GitHub issues)
