# Tools

| Script | Use |
|---|---|
| `stock.py <keyword>…` | Search DigiKey and Mouser for stock and price |
| `dk_cat.py <categoryId> <out.json>` | Dump every in-stock DigiKey product in a category |
| `dk_pn.py <MPN>…` | Exact DigiKey part lookup: stock, status, key specs |
| `dk_find.py "<keywords>" Param=value…` | In-stock DigiKey search filtered by parameters |
| `jlc.py <keyword>…` | Search the JLCPCB assembly library (LCSC stock); no key needed |
| `freq.py` | Parse DigiKey frequency strings (`covers_fm()`) |
| `shot.cjs <page.html> <out.png>` | Screenshot a wiring diagram with Playwright |
| `netcheck.py [--bom] [--sync-bom]` | Check `design/rev-a/netlist.json`: designators, part numbers, JLC codes and sizes; every pin of every part mapped to a net (pin coverage), nets that join only one part, shorted passives, unpowered supply pins; and pin-by-pin agreement with `bom.md` and `wiring.html`; `--bom` prints the grouped BOM, `--sync-bom` rewrites the designator line at the top of each BOM chain |
| `kicadcheck.py --net/--bom/--pcb <file>` | Check KiCad's exported schematic netlist, BOM and board file against `netlist.json` and the Rev A placement: opens, shorts, missing pins, JLC codes, footprint sizes, sides, outline, positions. See `design/rev-a/verification.md` |
| `kicadcheck_test.py` | Self-test for `kicadcheck.py`: synthetic files with deliberate faults, plus KiCad's StickHub demo |
| `kicad_symbol.py` | `add_symbol()` builds a readable project symbol from a datasheet pin table into `kicad/rev-a/symbols/IphoneFM.kicad_sym` |
| `sch_place.py [--dry-run]` | Place every passive on the Rev A schematic beside the pin its `local_to` names, clear of other parts and their text; needs one R, C, L and FB seeded first |
| `setup-kicad.sh` | Install KiCad 10 and pre-cache the KiCad MCP server (Ubuntu 24.04, as root) |

API keys come from environment variables (`DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET`, `MOUSER_API_KEY`). Never commit keys.
DigiKey limits a search to offset + limit ≤ 300, so `dk_cat.py` can truncate large categories.
`shot.cjs` loads Playwright from `PLAYWRIGHT_MODULE` if set, else `playwright`, and needs absolute paths.

The KiCad MCP server ([kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro)) is registered in `../.mcp.json` with the read-only `default` profile; on the design PC a local override runs it with the `full` profile in `write` mode, so Claude can edit the KiCad project. It needs KiCad from `setup-kicad.sh`.
