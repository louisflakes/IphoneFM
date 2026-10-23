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
| `sch_place.py [--dry-run]` | Place every passive on the Rev A schematic beside the pin its `local_to` names, clear of other parts and their text; needs one R, C, L and FB seeded first; upright parts are turned so ground is at the bottom and supplies on top, with room left for power symbols. Rerun order: `sch_testpads`, `sch_layout`, `sch_place`, `sch_fields`, `sch_power`, `sch_wire` per chain, `sch_flags`, `sch_labels`, `sch_noconnect`, `sch_notes`, `sch_pinids` |
| `sch_fields.py [--dry-run]` | Write each symbol's value, MPN, LCSC code and manufacturer from `netlist.json` into the Rev A schematic, leaving designators as placed |
| `sch_power.py [--dry-run]` | Wire a power symbol to every pin on VBUS, 3V3, VDDA, RX_VDD and GND (per `netlist.json`); neighbouring pins on one rail share a bar and one symbol; reruns replace its own drawing |
| `sch_layout.py [--dry-run]` | Move chips, connectors and diodes to where a chain's wiring reads cleanly, with their visible fields stacked clear of the pins |
| `sch_testpads.py [--dry-run]` | Place the test pads TP1–TP8 (out of the BOM): signal pads on the end of the line they test, power pads in the controls zone |
| `sch_wire.py <chain> [--dry-run]` | Wire every net among one chain's parts (maze router on the 1.27 mm grid): never through a body, power symbol or another net's pin; nets may cross but never touch; reruns replace that chain's wires |
| `sch_flags.py [--dry-run]` | Put a PWR_FLAG on each power net fed from the connector or through a passive part (VBUS, GND, VDDA, RX_VDD, U5_VDD), on a short stub; run before `sch_labels` |
| `sch_labels.py [--dry-run]` | Name every signal net with a local label carrying its `netlist.json` name, one per connected group (lone chip pins on a short stub), placed clear of parts, wires and text; the matching names join the groups. Reruns replace them |
| `sch_noconnect.py [--dry-run]` | Put a no-connect flag (X) on every pin `netlist.json` marks NC |
| `sch_notes.py [--dry-run]` | Write the layout notes block onto the Rev A schematic |
| `sch_footprints.py [--dry-run]` | Step 2.6: write each part's IphoneFM footprint (from `footprints.md`, via `rev_a_footprints.py`) into its symbol's Footprint field |
| `sch_pinids.py [--dry-run]` | Give every symbol pin a fixed ID, as KiCad saves them, so ERC exclusions survive a reload; run last |
| `fp_j1_hro2020.py` | Build J1's project footprint: KiCad's HRO USB-C footprint with pads and holes moved to HRO's 2020 drawing |
| `fp_u2_ti_njk.py` | Build U2's project footprint to TI's NJK0036A land pattern (4.6 mm centre pad), on KiCad's QFN-36 outline and 3D model |
| `fp_sw1_msk12c02.py` | Build SW1's project footprint: KiCad's MSK12C02 with the four tab pads numbered 4 to match the symbol |
| `rev_a_footprints.py` | The footprint chosen for each Rev A part (from `kicad/rev-a/footprints.md`), shared by the checks below |
| `silk_check.py [--render DIR]` | Step 2.4: each footprint's silkscreen line widths and closest ink to a pad, against `fab-rules.md`; `--render` draws sheets of them |
| `fp_silk_trim.py` | Step 2.4: copy every Rev A footprint into `IphoneFM.pretty` with silkscreen widened to 0.25 mm and trimmed 0.20 mm clear of pads; run after any `fp_*.py` builder |
| `paste_check.py` | Step 2.5: each footprint's solder paste against its pads (1:1, or centre-pad windows with their coverage) |
| `fp_u4_si4705.py` | Build U4's project footprint: KiCad's SiliconLabs QFN-20 with Skyworks' 0.28 mm side pads and 0.06 mm mask clearance |
| `fp_d5_sod882.py` | Build D5's project footprint: KiCad's D_SOD-882 with the paste made 1:1 with the pads |
| `pinpad_check.py` | Step 2.3: check every Rev A symbol pin has a pad of the same number on its chosen footprint (and no pad lacks a pin) |
| `fp_d1_xl1615.py` | Build D1's project footprint to Xinglight's XL-1615RGBC-RF soldering pattern (KiCad has none) |
| `fp_sw3_tdp06.py` | Build SW3's project footprint: KiCad's KingTek 6-way DIP pads with C&K TDP06's real body and lever side |
| `fp_rv_rk10j.py` | Build RV1–RV3's project footprint to Alps' RK10J reflow-type PC board drawing (KiCad has none) |
| `pcb_setup.py` | Phase 3: write the board setup (stack-up and title block so far) into `IphoneFM.kicad_pcb` from `fab-rules.md`; re-runnable |
| `setup-kicad.sh` | Install KiCad 10 and pre-cache the KiCad MCP server (Ubuntu 24.04, as root) |

API keys come from environment variables (`DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET`, `MOUSER_API_KEY`). Never commit keys.
DigiKey limits a search to offset + limit ≤ 300, so `dk_cat.py` can truncate large categories.
`shot.cjs` loads Playwright from `PLAYWRIGHT_MODULE` if set, else `playwright`, and needs absolute paths.

The KiCad MCP server ([kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro)) is registered in `../.mcp.json` with the read-only `default` profile; on the design PC a local override runs it with the `full` profile in `write` mode, so Claude can edit the KiCad project. It needs KiCad from `setup-kicad.sh`.
