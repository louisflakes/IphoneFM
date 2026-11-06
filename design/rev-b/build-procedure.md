# Rev B build procedure

Rev B changes only the front panel ([front-panel.md](front-panel.md), [front-face-sketch.png](front-face-sketch.png)):
the three tuning wheels become one push-wheel encoder, a four-digit station display and its driver are added, and the
side-lever DIP becomes a top-lever one. Everything else is Rev A as built and reviewed (tag `rev-a-reviewed`).

The order and the rules are Rev A's ([../rev-a/kicad-build-procedure.md](../rev-a/kicad-build-procedure.md)): a design
change goes into netlist.json first, then the pages that explain it, then the schematic, then footprints, placement and
routing. Each new symbol and footprint is checked against its datasheet as in Rev A. Only the steps Rev B touches are
listed; the rest of Rev A carries over unchanged.

Work is done in batches from a rollback point (a commit before each batch), with a report and a picture at the end of
each batch; a choice that is the user's stops the batch at once.

## Phase B0: Set up

- [ ] B0.1 Copy the Rev A design files and KiCad project to `design/rev-b/` and `kicad/rev-b/`, so Rev A stays as
  ordered. Title blocks to Rev B.

## Phase B1: Design changes (netlist.json and the pages, before KiCad)

- [ ] B1.1 Remove RV1–RV3, their reservoir caps C39–C41 and the nets WHEEL1–WHEEL3; free U1 pins 13–15.
- [ ] B1.2 SW3 becomes Diptronics DHN-06-V (C224997); check its pin numbering against p1. Same nets as Rev A.
- [ ] B1.3 Add the encoder (Mitsumi SIQ-02FVS3, C2925423): A, B and the push switch to U1 pins, common to GND, with
  pull-ups. Check the chosen U1 pins against DS14217 (a timer's encoder inputs if one is free) and AN2606 (bootloader).
- [ ] B1.4 Add the display: 4 × GS3011AW-B (C22462661), anodes 3 and 8 to VBUS, 32 segments to the driver.
- [ ] B1.5 Add the driver IS31FL3236A (C246443): every pin from its datasheet, VCC from VBUS with decoupling, REXT for
  the segment current, SDB held low until firmware runs, an I²C address clear of U4, on U1's I²C bus. Re-check the bus
  pull-ups for two devices.
- [ ] B1.6 Update the current budget (display from VBUS, off before USB set-up).
- [ ] B1.7 Update bom.md (chain 9), sourcing.md, part-provenance.md and the wiring page.
- [ ] B1.8 Run `tools/netcheck.py`.
- [ ] B1.9 **Review checkpoint:** the user reviews the netlist changes.

## Phase B2: Schematic (Rev A Phase 1, for the changed parts)

- [ ] B2.1 Delete RV1–RV3 and C39–C41 from the sheet.
- [ ] B2.2 Place the encoder, the four digits, the driver and the new SW3, each checked pin by pin against its datasheet
  (Rev A steps 1.4–1.16), with their passives at the pins they serve (1.17) and their fields from netlist.json (1.18).
- [ ] B2.3 Wire the new chain, label the nets, flags and no-connects (1.19–1.32), net classes and layout notes
  (1.33–1.34).
- [ ] B2.4 ERC to zero errors; `kicadcheck.py --net` and `--bom` pass (1.35–1.37).
- [ ] B2.5 **Review checkpoint:** the user reviews the sheet and the check results.

## Phase B3 onward: footprints, placement, routing, outputs

As Rev A Phases 2–8, for the new parts only: footprints checked on a to-scale overlay against the makers' land patterns,
placement in Rev A's left column per the sketch, local re-routing, pours, DRC and the netlist comparison, then the JLC
files. The steps are written out when Phase B2 is done.
