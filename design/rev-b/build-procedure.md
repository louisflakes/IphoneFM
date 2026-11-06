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

- [x] B0.1 Copy the Rev A design files and KiCad project to `design/rev-b/` and `kicad/rev-b/`, so Rev A stays as
  ordered. Title blocks to Rev B.
  - Done 2026-11-06 (tag `rev-b-b0`): design files and the KiCad sources (no outputs or panel) copied; title blocks Rev B, 2026-11-06. `tools/netcheck.py` and `tools/kicadcheck.py` take `IPHONEFM_REV=rev-b`; Rev A still passes all 19 netcheck checks.

## Phase B1: Design changes (netlist.json and the pages, before KiCad)

- [x] B1.1 Remove RV1–RV3, their reservoir caps C39–C41 and the nets WHEEL1–WHEEL3; free U1 pins 13–15.
  - Done 2026-11-06: RV1–RV3, C39–C41 and WHEEL1–3 removed; U1 pins 13–15 now carry the encoder.
- [x] B1.2 SW3 becomes Diptronics DHN-06-V (C224997); check its pin numbering against p1. Same nets as Rev A.
  - Done 2026-11-06: same pin map as Rev A (switch n between pins n and 13−n); the numbering is confirmed on the footprint in Phase B3.
- [x] B1.3 Add the encoder (Mitsumi SIQ-02FVS3, C2925423): A, B and the push switch to U1 pins, common to GND, with
  pull-ups. Check the chosen U1 pins against DS14217 (a timer's encoder inputs if one is free) and AN2606 (bootloader).
  - Done 2026-11-06: SW4 A → PA3, B → PA4, S → PA5, C and 6 frame tabs → GND, R30–R32 10 kΩ pull-ups (0.33 mA, under the contacts' 0.5 mA). No timer has both encoder inputs on free pins, so firmware decodes it (EXTI3–5). PA4/PA5 are the bootloader's SPI1 NSS/SCK inputs; both contacts are open at every detent, so they idle high (SIQ p3, AN2606 p387).
- [x] B1.4 Add the display: 4 × GS3011AW-B (C22462661), anodes 3 and 8 to VBUS, 32 segments to the driver.
  - Done 2026-11-06: DS1–DS4 pins from GS3011A/CX-X p3; nets SEG1_A … SEG4_DP; C44 10 µF at the anodes.
- [x] B1.5 Add the driver IS31FL3236A (C246443): every pin from its datasheet, VCC from VBUS with decoupling, REXT for
  the segment current, SDB held low until firmware runs, an I²C address clear of U4, on U1's I²C bus. Re-check the bus
  pull-ups for two devices.
  - Done 2026-11-06: U8 pins from p2 (45 with the pad); OUT1–32 to the digits in reading order, OUT33–36 open; AD → GND (0x3C; U4 is 0x11); R28 10 kΩ (7.6 mA per segment maximum, p10); C42 1 µF + C43 100 nF (p1); SDB from U1 PC13 with R29 100 kΩ pull-down (PC13 is analog at reset; DS14217 Table 26 note 2 allows this light load). R20/R21 6.8 kΩ stay right for two devices.
- [x] B1.6 Update the current budget (display from VBUS, off before USB set-up).
  - Done 2026-11-06 (bom.md chain 10): display ≤ 252 mA from VBUS, about 169 mA showing a station at full brightness; board total ≤ 363 mA after USB set-up, unchanged before it (U8 shut down).
- [x] B1.7 Update bom.md (chain 9), sourcing.md, part-provenance.md and the wiring page.
  - Done 2026-11-06: bom.md chain 9, chain 6 SW3 row, U1 pin map; sourcing.md Rev B section; part-provenance.md; wiring.html (hosted: https://claude.ai/artifact/DUR85HqCDaUoV6nrXSEaHV).
- [x] B1.8 Run `tools/netcheck.py`.
  - Done 2026-11-06: 19 of 19 pass (102 placed parts, 47 part numbers).
- [x] B1.9 **Review checkpoint:** the user reviews the netlist changes.
  - Approved by the user 2026-11-06 ("looks ok"), with the instruction to work the schematic rigorously from the makers' own documents.

## Phase B2: Schematic (Rev A Phase 1, for the changed parts)

- [x] B2.1 Delete RV1–RV3 and C39–C41 from the sheet.
  - Done 2026-11-06 (`tools/sch_rev_b.py`): RV1–RV3, C39–C41 and their library symbol removed, with chain 3's wires from U1 PA3–PA5 to those caps and their ground bar (by uuid; chain 3 itself isn't rerouted, since every later chain's wires now cross its area).
- [x] B2.2 Place the encoder, the four digits, the driver and the new SW3, each checked pin by pin against its datasheet
  (Rev A steps 1.4–1.16), with their passives at the pins they serve (1.17) and their fields from netlist.json (1.18).
  - Done 2026-11-06. Makers' documents first: U8 from Lumissil's own Rev. I datasheet (10/14/2024, lumissil.com) and its evaluation-board guide (Rev. G, 02/14/2025), both saved in docs/datasheets/rev-b; the board's schematic confirms OUT1→43, OUT2→44, OUT3–18→1–16, OUT19–36→18–35, AD to GND, 100 kΩ on SDB, 1 µF on VCC. Guangcai's site only offers its PDF as a download; the saved copy is Guangcai's own spec (Rev A, 2020). Mitsumi's and Diptronics' saved copies are their own catalogue pages.
  - Symbols, pin by pin: U8 `IphoneFM:IS31FL3236A` built from the QFN-44 table (45 pins with the pad; OUTx open collector, VCC/GND/EP power in); DS1–DS4 `IphoneFM:GS3011AW-B`, KiCad's KCSA02-105 drawing, whose ten pins match GS3011A/CX-X p3 one for one, with the LED pins made passive; SW4 `IphoneFM:SIQ-02FVS3`, terminals 1 A, 2 S, 3 C, 4 B and frame tabs 5–10 (not M1–M6: the tools read Mn as pad 4–7); SW3 keeps `Switch:SW_DIP_x06`.
  - Placed per kicad/rev-b/sheet-plan.md (new Display zone under U1); passives at their pins; fields from netlist.json (`sch_fields`).
- [x] B2.3 Wire the new chain, label the nets, flags and no-connects (1.19–1.32), net classes and layout notes
  (1.33–1.34).
  - Done 2026-11-06 with the Rev A tools in their order (`sch_layout`, `sch_fields`, `sch_power`, `sch_wire 9`, `sch_flags`, `sch_labels`, `sch_noconnect`, `sch_notes`, `sch_pinids`): 48 chain-9 nets wired, every signal net labelled (the two labels Rev A placed by hand are now in `sch_labels.HAND`), NC flags on U8 OUT33–36 and none left on U1 PC13. New nets stay in the Default class (7.6 mA segments, far from the RF and the loop filter). Layout note 4 added for U8.
- [x] B2.4 ERC to zero errors; `kicadcheck.py --net` and `--bom` pass (1.35–1.37).
  - Done 2026-11-06: ERC 0 errors, 0 open warnings (Rev A's two reviewed U4 LOUT/ROUT exclusions remain); `kicadcheck.py --net --bom` 17 of 17; Rev A's sheet unchanged and still 11 of 11.
- [x] B2.5 **Review checkpoint:** the user reviews the sheet and the check results.
  - Approved by the user 2026-11-06 ("lets continue to footprints"). Found at B3.4: B2.1 had left the wheels' unused library symbol in the sheet (the removal looked for entries two tabs in; the sheet keeps them one tab in). Fixed in `sch_rev_b.drop_lib_symbol` and removed; nothing placed used it.

## Phase B3: Footprints (Rev A Phase 2, for the new parts)

- [x] B3.1 Choose each new part's footprint source in Rev A's order (KiCad's library, then the maker's, then LCSC) and record it in kicad/rev-b/footprints.md.
  - Done 2026-11-06. KiCad has no 5 × 5 mm 0.4 mm-pitch QFN-44, no GS3011 and no SIQ encoder, so U8, DS1–DS4 and SW4 are built from the makers' drawings. SW3 keeps KiCad's Omron A6H-6101 pads, which are Diptronics' layout exactly. The RV1–RV3 and C&K TDP06 footprints leave the Rev B library.
- [x] B3.2 Compare each footprint's pads with its maker's land pattern on a to-scale overlay, one table per part (Rev A 2.2).
  - Done 2026-11-06 (`tools/fp_rev_b.py`, overlay [footprint-overlays.png](footprint-overlays.png) by `tools/fp_overlay_rev_b.py`). Every pad matches the maker's drawing. The departures:
    - U8: KiCad can't round a single pad corner, so the corner pads' R0.125 corners are chamfered 0.125 instead (0.21 mm apart against Lumissil's 0.20), and the joins from pins 17 and 39 to the centre pad are square, not R0.1.
    - SW4: the angled frame tabs follow Mitsumi, which LCSC's footprint does not. Mitsumi's "2–4" is to the tabs' inner ends; the PDF's vectors put their centres 4.60 mm from the knob centre, where LCSC has 4.0.
  - LCSC's footprints were read as a second opinion only (footprints.md).
- [x] B3.3 Pin-to-pad, silkscreen and paste checks (Rev A 2.3–2.5).
  - Done 2026-11-06: `pinpad_check` 114 of 114, 0 mismatches. `fp_silk_trim` then `silk_check` pass (0.25 mm lines, ink at least 0.20 mm from copper); a second trim changes nothing. The encoder's wheel is drawn as chords, because the trim drops a circle whole. `paste_check`: 0 problems; pads 1:1, U8's centre pad four windows (65%).
- [x] B3.4 Assign the footprints, re-run ERC, re-export the netlist and run `kicadcheck.py --net --bom` (Rev A 2.6–2.7).
  - Done 2026-11-06 (`sch_footprints`). 15 symbols changed. KiCad's netlist has 114 parts, all on IphoneFM footprints that exist. ERC: 0 errors, 0 warnings (the two U4 items still excluded). kicadcheck 17 of 17. Rev A untouched (pin-to-pad still 106 of 106).
  - Carried to the board (Phase B4):
    - U8's pins are 0.15 mm apart in copper, under our 0.20 mm rule, so U8 needs its own clearance rule (JLC's minimum is 0.10).
    - Each digit's pads span 15.5 mm, not the body's 12.
    - SW4's knob (Ø14.5) overhangs everything inside its circle.
    - SW4's origin is the knob centre (placement-file offsets at Rev A step 8.3).
- [x] B3.5 **Review checkpoint:** the user reviews the footprints and their sources.
  - Approved by the user 2026-11-06 ("so we're good to continue?", after the overlay and the B3 report). Found at B4.2: `sch_power` had numbered one of its ground symbols #PWR103, which a ground symbol placed by hand in Rev A already uses (Rev B has more power symbols, so its count reached it); KiCad reported an annotation error on netlist export, ERC did not. `sch_power` now skips numbers held by symbols it didn't draw; rerun with `sch_pinids`, nothing else changed (every wire, symbol and position identical); ERC 0.

## Phase B4: Placement (Rev A Phase 4, for the new parts)

The board starts as Rev A's, placed and routed. The new parts go into the left column per the sketch
(`front-face-sketch.png`); the middle and right keep their Rev A placement and routing. Board edits are file edits with
KiCad's own Python (`tools/pcb_rev_b.py`), since the Rev B board is not open in KiCad. Copper the new parts land on is
taken up here and listed for Phase B5 (routing).

- [ ] B4.1 Board setup for the new parts: U8's own clearance rule (its pins are 0.15 mm apart; JLC's minimum is 0.10).
  - Done 2026-11-06 (`pcb_rev_b.py rules`): inside U8's courtyard, copper keeps 0.15 mm (pads and the tracks leaving them); 0.20 mm everywhere else. Checked once U8 is on the board (B4.9).
- [ ] B4.2 Bring the schematic across (Rev A 4.1): remove RV1–RV3 and C39–C41 and the copper only they used; swap SW3's
  footprint; add SW4, DS1–DS4, U8, R28–R32 and C42–C44 beside the board; every pad's net from KiCad's netlist.
  - Done 2026-11-06 (`pcb_rev_b.py update`), from KiCad's own netlist of the sheet: RV1–RV3 and C39–C41 removed with the 19 tracks on WHEEL1–3; SW3 swapped in place; 14 parts added beside the board; 127 pad nets set (the new parts', U1 PA3–PA5 and PC13); H1–H4 given the sheet's empty MPN/LCSC/Manufacturer fields. KiCad's DRC with schematic parity: 0 differences, so the board matches the sheet as Update PCB from Schematic would leave it.
- [ ] B4.3 Place and lock SW3 at Rev A's SW3 position, levers up (Rev A 4.6), and join its tracks to the new pads.
  - Done 2026-11-06 (`pcb_rev_b.py fixed`): SW3 at Rev A's (35.925, 64.51), −90°, locked: pins 1–6 (ATT_C16 … C0_5) along the top row with pin 1 at the right, 7–12 (3V3) along the bottom, so "ON" (the 7–12 side) faces into the board. The pitch is Rev A's 1.27 mm, so the 12 Rev A track ends were moved straight onto the new rows (4.90/7.40 mm apart, Rev A 7.62).
- [ ] B4.4 Place and lock SW4 where RV3 was, wheel out of the left edge, copper 0.5 mm from the edge (Rev A 4.5).
  - Done 2026-11-06: knob centre (17.19, 112.0), 90° (terminals into the board), locked. The sketch had the frame's end on the edge (centre 16.55), but the two 45° frame tabs then reach 0.13 mm past the edge; the knob moved 0.64 mm in so their copper is 0.51 mm from it (our 0.50 rule). The wheel stands 2.76 mm past the edge (sketch 3.4, Rev A's wheels 1.9), so the panel's left rail gap must clear 2.76 mm (Phase 8). TP4 moved 0.1 mm down, clear of SW4's courtyard.
- [ ] B4.5 Place and lock DS1–DS4 where RV1 and RV2 were, turned to read with the phone's left edge down, DS1 at the top.
  - Done 2026-11-06: DS1–DS4 at x 20.96, y 73.61 / 81.91 / 90.21 / 98.51, −90° (each digit's top toward the board's right edge, so they read 1-0-7-9 left to right with the phone's left edge down), locked; outer pads 0.51 mm from the left edge. Pitch 8.3 mm, not the sketch's 8.0: at 8.0 the B3 courtyards (body + 0.35 mm) touch, against our 0.3 mm courtyard gap; the display keeps the sketch's centre. Digits 1.0 mm apart instead of 0.7.
- [ ] B4.6 Place U8 by the display with R28, R29, C42 and C43 at its pins (Rev A 4.11, 4.13).
  - Stopped for the user's choice (2026-11-06): the sketch's spot right of DS1 ("roughly here") is not free: U8's 6.5 mm courtyard there overlaps DS1's courtyard, TP2, TP3, the 3V3 feed from TP2 and three of U1's LED lines to D1, all Rev A routing. The space above the display (left of H1, x 13–23, y 60–69) holds only ground stitching vias. Picture: placement-b4.png (A, B).
- [ ] B4.7 Place R30–R32 at SW4's terminals and C44 at the anodes (Rev A 4.13).
  - R30–R32 done 2026-11-06 (`pcb_rev_b.py pullups`): each straight out from its terminal (A, B, S), its signal pad toward it, 0.3 mm courtyard gap to SW4. C44 waits for B4.6: DS2 pin 3 (its local_to) is in the outer pad row by the edge, with no room beside it, so it goes on the display's VBUS feed by U8.
- [ ] B4.8 Move TP2 and TP3 and clear the left column: Rev A copper under the new parts is taken up and listed for B5.
  - Copper taken up 2026-11-06 (`pcb_rev_b.py clear`): every Rev A track and via a new part's pad, hole or courtyard lands on, then what that left dangling, then Rev A copper that had taken a new pad's net (a ground stub under R31). Against the B4 start: 149 items: 19 wheel tracks, 69 ground stitching vias and 14 ground stubs in the left column, 27 on 3V3 (the top-layer feed up the column) and 20 on RF_MODE (U1 to SW1, TP4, R18 and R17). Bottom-layer tracks under the digits stay (VBUS at x 25.6). For B5: 3V3 and RF_MODE to re-route, plus the new nets. TP2 and TP3 wait for B4.6.
- [ ] B4.9 Check courtyards, mechanical fit and DRC; `kicadcheck.py --pcb`; schematic parity (Rev A 4.16–4.17).
- [ ] B4.10 **Review checkpoint:** the user reviews the placement.

## Phase B5 onward: routing, pours, outputs

As Rev A Phases 5–8, for the new parts and the copper B4 takes up: local re-routing, pours, DRC and the netlist
comparison, then the JLC files (the left rail's gap widened for the wheel). The steps are written out when Phase B4 is
done.
