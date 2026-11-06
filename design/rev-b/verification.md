# Analog FM verification checks

How the design stays on the rails from here into KiCad. One file holds the truth, and every other file is checked against it by a script, not by eye.

## The source of truth

[netlist.json](netlist.json) lists every part (designator, value, part number, JLC code, package, the pin it must sit next to) and every pin of every part with the net it joins. The human-readable pages follow from it:

| File | What it is | Kept in step by |
|---|---|---|
| [bom.md](bom.md) | Why each part and value was chosen, chain by chain | `netcheck.py` (part numbers; the designator line at the top of each chain) |
| [wiring.html](wiring.html) | The wiring diagram and netlist table | `netcheck.py` (every net name; every pin it draws) |
| [layout.html](layout.html) | True-size parts and the agreed Rev A placement | `kicadcheck.py --pcb` (positions on the real board) |
| [placement-rules.md](placement-rules.md) | Placement rules and the user's feedback | The checks in layout.html, then `kicadcheck.py --pcb` |

Changing the design means editing netlist.json first, then the page that explains it, then running the checks.

## Before KiCad: `python tools/netcheck.py`

| Check | Catches |
|---|---|
| Designators unique, standard prefixes, every field present | Two parts called C1; a part with no package |
| Every ordered part has a JLC code; nothing below 0402; one code per part number | A part JLC can't place; a 0201 sneaking in |
| Every part number appears in bom.md; designator lines match | The BOM and the list drifting apart |
| Pin coverage: each part's map has its datasheet pin count | A pin left out, like LMX2571 pin 15 |
| Every net described, used, and joining at least two parts | A misspelled net name, which would silently open a connection |
| No passive with both ends on one net | A shorted resistor or capacitor |
| Supply pins powered, ground pins on GND, NC pins open | An unpowered VDD; a do-not-connect pin wired up |
| Each 'local_to' part shares a net with its pin | A decoupling cap assigned to the wrong pin |
| Wiring page agrees pin by pin (147 pins) | The diagram showing something the list doesn't |

`--bom` prints the grouped BOM; `--sync-bom` rewrites the designator lines in bom.md after the list changes.

## In KiCad: `python tools/kicadcheck.py`

Run on KiCad's own exports (KiCad 10 is at `%LOCALAPPDATA%\Programs\KiCad\10.0\bin\kicad-cli.exe`):

```
kicad-cli sch export netlist --format kicadsexpr -o board.net board.kicad_sch
kicad-cli sch export bom --fields "Reference,Value,Footprint,LCSC,MPN" -o board.csv board.kicad_sch
python tools/kicadcheck.py --net board.net --bom board.csv --pcb board.kicad_pcb
```

| Input | Checks |
|---|---|
| `--net` (schematic) | Every part present and nothing extra; every connected pin has a pad; no net broken in two (an open); no two nets joined (a short); NC pins open; LCSC codes and part numbers match; passive footprints the right size |
| `--bom` | Every ordered part listed, nothing extra, codes and part numbers match |
| `--pcb` (the board file) | The same connection checks on the board's own pads; every part on the top side; outline 46.45 × 71.40 mm; each sketched part within 1.5 mm of the Rev A placement (anchored on J1); each 'local_to' part within 4 mm of its pin's pad |

Net names may differ from netlist.json (KiCad's automatic names are fine); the check compares which pins are joined, and lists renamed nets as a note. Footprint pad numbering is matched loosely where footprints differ: a paired USB-C contact (A1B12) may be one pad or two, SW1's four tabs may all be pad 4, an exposed pad is usually the next number after the last pin.

The order in which these run during the KiCad build is in [kicad-build-procedure.md](kicad-build-procedure.md).

## KiCad's own rule check (ERC)

Run with `kicad-cli sch erc --severity-all -o erc.rpt board.kicad_sch`. KiCad checks how pins are joined by their electrical type (two outputs fighting, an input nothing drives, a power pin with no source) and flags anything it can't tell is intended.

**Schematic, step 1.35 (2026-10-22).** The finished schematic gave 2 errors and 0 warnings. Both were the same deliberate design choice, caught automatically: U4's unused analog audio outputs (LOUT, ROUT) tied to ground, which ERC sees as outputs shorted together and to a power source. We stopped at this step and looked at them together before going on:
- U4 is the FM receiver. Its audio leaves through the digital I²S output to U1 and on over USB, so the analog outputs are unused.
- Skyworks AN383 p17 says to "Tie unused pin(s) to GND".
- U1 starts U4 in digital-only mode (POWER_UP 0xB0), so the analog outputs never drive into that ground.

Both were confirmed harmless and recorded in KiCad as exclusions, with that reason attached to each. ERC now reports 0 errors and 0 warnings, and lists the two as excluded.

## Testing the checker: `python tools/kicadcheck_test.py`

Before any KiCad work exists, the test builds KiCad-format files from netlist.json and the Rev A placement, which must pass, then breaks them one way at a time. Each break must be caught:
- U2 pin 15 removed
- R21 moved onto I2C_SCL (a short)
- U7's VDD taken off 3V3 (an open)
- U2's do-not-connect pin 8 tied to GND
- a wrong JLC code
- C23 missing from the BOM
- U2 moved 5 mm off the sketch
- C23 moved 10 mm from its pin
- R5 on the bottom side

It also exports a netlist from KiCad's own StickHub demo and checks it against that demo's board, so the readers are tested on real KiCad 10 files. Pad positions were separately checked against KiCad's pcbnew on the same board: all 266 pads, every side and rotation, agree exactly.
