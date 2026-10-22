# Rev A KiCad build procedure

The established order for turning the Rev A design into a board, broken into single steps. It follows [docs/pcb-design-workflow.md](../../docs/pcb-design-workflow.md), which cites each rule to a reference book (tags in brackets: EES, KLAP, BAC, HHG, KHA, AN383, AN4169, ADI). The books agree on the order: schematic first, then footprints, then board setup, placement, routing, pours, checks and outputs.

## How we work through it

- Reports name the phase as in the original order and the step by its number, e.g. "Phase 0 (constraints and fab rules), step 0.4".

- Claude does exactly one step, reports what it did in a line or two with proof (a screenshot or a check's output), and waits for the user's OK.
- A step is ticked only after the user agrees with it.
- If a step turns up a problem, we stop and settle it before moving on; nothing is skipped quietly.
- Any change to the design goes into [netlist.json](netlist.json) first, then the page that explains it, then KiCad.
- Claude makes changes through the KiCad MCP server where it can, and otherwise gives the user the exact menu path to click.
- At each review checkpoint, the user sees a screenshot and the check results before the next phase starts.
- Schematic edits are written to the file, so the open schematic editor shows them only after File → Revert; while Claude works on the schematic, the user doesn't edit or save it in KiCad, so neither copy overwrites the other. Board edits go through KiCad's live API and appear directly.

## Phase 0: Constraints and fab rules

- [x] 0.1 Create the KiCad 10 project `IphoneFM` in `kicad/rev-a/`.
- [x] 0.2 Fill in the title block: IphoneFM, Rev A, today's date, and the author (schematic done 2026-10-21; the board's title block is set in step 3.1).
- [x] 0.3 Read JLCPCB's current 2-layer PCB capabilities and record the trace, space, via, drill, annular ring, edge-clearance and silkscreen numbers we use in `kicad/rev-a/fab-rules.md`, with the source link [HHG p15, p63–65; BAC p4, p11].
- [x] 0.4 Read JLCPCB's assembly rules (part spacing, edge clearance, fiducials) and add them to the same file [conflict C4].
- [x] 0.5 Set our own design rules a step above JLC's minimums and write them beside the minimums [HHG p15, p63–64].
- [x] 0.6 Use JLC's impedance calculator to find the 50 Ω grounded-coplanar line width and gap for their 1.6 mm 2-layer stackup, and record it [AN4169 p6, p11; workflow "Gaps"].
- [x] 0.7 **Review checkpoint:** the user reviews fab-rules.md.

## Phase 1: Schematic

Setup:
- [x] 1.1 Open the schematic editor and set the page size, the 50 mil grid and the title block [EES p10].
- [x] 1.2 Add field-name templates for MPN, LCSC and Manufacturer so every symbol carries them [EES p54].
- [x] 1.3 Plan one sheet laid out left to right in signal flow, with USB and power on the left, the MCU in the middle, transmit and receive to the right, and higher voltages toward the top [KHA p108; BAC p3]. Plan: `kicad/rev-a/sheet-plan.md`.

Symbols (each checked pin by pin against its datasheet before use, because ERC can't catch wrong pin numbers [HHG p33–34; EES p133]):
- [x] 1.4 Place U1 (STM32U535CEU6) and check all 48 pins and the exposed pad against DS14217 Figure 10.
- [x] 1.5 Place U2 (LMX2571) and check all 36 pins and the DAP against SNAS654A p3–4.
- [x] 1.6 Place U3 (AP2112K-3.3) and check its 5 pins against DS39724 p2.
- [x] 1.7 Place U4 (Si4705-D60-GM, QFN) and check all 20 pins and the pad against the datasheet's p16.
- [x] 1.8 Place U5 (PE42421) and check its 6 pins against p8.
- [x] 1.9 Place U6 (USBLC6-2SC6) and check its 6 pins against p1–2.
- [x] 1.10 Place U7 (PE43711) and check all 24 pins and the pad against Table 9 p28.
- [x] 1.11 Place Y2 (20 MHz oscillator) and check its 4 pins against YSO110TR p2.
- [x] 1.12 Place J1 (USB-C) and check its contacts and shell against the HRO drawing.
- [x] 1.13 Place J2 (SMA) and check its centre pin and legs against the BAT Wireless drawing.
- [x] 1.14 Place SW1, SW2 and SW3 and check their pins against their drawings, confirming the DIP switch's numbering.
- [x] 1.15 Place RV1–RV3 and check their terminals, dummy pins and mounting lands against the Alps drawing.
- [ ] 1.16 Place D1, D3, D4 and D5 and check their pins against their datasheets, with diode pins named A and K [HHG p29].
- [ ] 1.17 Place every passive beside the pin it serves, as netlist.json's `local_to` says [BAC p3].
- [ ] 1.18 Give every symbol its designator, value, MPN and LCSC code from netlist.json, without letting KiCad renumber them [HHG p27, p34; KHA p106].

Wiring (one bom.md chain per step):
- [ ] 1.19 Wire the power symbols for VBUS, 3V3, VDDA, RX_VDD and GND [EES p37].
- [ ] 1.20 Wire chain 1: J1, the CC resistors and the USB ESD parts.
- [ ] 1.21 Wire chain 2: U3 and its capacitors.
- [ ] 1.22 Wire chain 3: U1's supply, reset, boot and debug pins.
- [ ] 1.23 Wire chain 4: Y2, its capacitors and R4.
- [ ] 1.24 Wire chain 5: U2, its supply capacitors, the loop filter and its control lines.
- [ ] 1.25 Wire chain 6: U7, its pull-downs and SW3.
- [ ] 1.26 Wire chain 7: FL1, U5, SW1, J2 and D5.
- [ ] 1.27 Wire chain 8: U4 and its front end, supply and digital lines.
- [ ] 1.28 Wire chain 9: the wheels, the BOOT button and the LED.
- [ ] 1.29 Wire chain 10: the test pads TP1–TP8.
- [ ] 1.30 Label every net with its netlist.json name, one name per net [EES p31, p38].
- [ ] 1.31 Put a PWR_FLAG on every rail fed from a connector or from a pin that isn't a power output, and on GND [EES p39, p77–78].
- [ ] 1.32 Put a no-connect flag on every pin netlist.json marks NC [EES p39].
- [ ] 1.33 Assign net classes for the RF nets, the clock and switching nets, and power [EES p39–44; HHG p64].
- [ ] 1.34 Add layout notes on the sheet: decoupling at the pins, rule R8 for the I²S clock, and no thermal reliefs on the FMI shunt parts [BAC p3; AN383 p17; LMX2571 p55].

Checks:
- [ ] 1.35 Run ERC and fix everything until it reports zero errors, recording any deliberate exclusion with its reason [EES p74; KLAP p39].
- [ ] 1.36 Export the netlist and run `kicadcheck.py --net` until every check passes.
- [ ] 1.37 Export the BOM and run `kicadcheck.py --bom` until every check passes.
- [ ] 1.38 **Review checkpoint:** the user reviews the whole sheet and the check results.

## Phase 2: Footprints

- [ ] 2.1 Choose each part's footprint source in this order and record it: KiCad's library, then the maker's own, then LCSC/EasyEDA.
- [ ] 2.2 Compare each footprint's pads with its datasheet land pattern and the true-size drawing in layout.html, one part per step [HHG p35].
- [ ] 2.3 Confirm every symbol pin number has a pad of the same number [EES p133].
- [ ] 2.4 Check each footprint's silkscreen: real-size body outline, pin 1 and polarity marks, no ink on pads, lines at least 0.25 mm wide [BAC p13; KHA p149].
- [ ] 2.5 Check each paste layer is 1:1 with its pads [HHG p96, p113].
- [ ] 2.6 Assign the footprints in the footprint assignment tool, using its filters [EES p85–92].
- [ ] 2.7 Re-run ERC, re-export the netlist and run `kicadcheck.py --net` again.
- [ ] 2.8 **Review checkpoint:** the user reviews the footprint list and its sources.

## Phase 3: Board setup

- [ ] 3.1 Open the PCB editor and set the stackup to JLC's 2-layer 1.6 mm FR4 with 1 oz copper [KLAP contents p7–8; HHG p63–65].
- [ ] 3.2 Enter the design rules from fab-rules.md.
- [ ] 3.3 Set the net classes' widths and clearances: default, power, 50 Ω RF lines and wider-spaced clocks [HHG p64].
- [ ] 3.4 Draw the 46.45 × 71.40 mm outline on Edge.Cuts, with the grid origin at the envelope's top-left corner so board and sketch coordinates line up [KHA p252; HHG p36].
- [ ] 3.5 Ask the user whether the enclosure needs mounting holes, and if so add them as symbols and footprints [KLAP p105].
- [ ] 3.6 Add keep-outs: copper at least 0.5 mm from the edge, and no through-hole parts over the magnet ring [HHG p105, p113; ADG R31 p278–279].
- [ ] 3.7 Add fiducials if JLC's assembly rules call for them [conflict C4].
- [ ] 3.8 **Review checkpoint:** the user reviews the empty board.

## Phase 4: Placement (the most important step [BAC p8; HHG p36])

- [ ] 4.1 Bring the parts across with Update PCB from Schematic (F8) [EES p96–97].
- [ ] 4.2 Group the parts by chain off the board, with short pin-to-pin distances [HHG p37, p46].
- [ ] 4.3 Place and lock J1 at its Rev A position [HHG p46; KHA p127, p147].
- [ ] 4.4 Place and lock J2 at its Rev A position.
- [ ] 4.5 Place and lock RV1–RV3 at their Rev A positions.
- [ ] 4.6 Place and lock SW1, SW2 and SW3 at their Rev A positions, SW3's levers facing out.
- [ ] 4.7 Place and lock D1 at the top right.
- [ ] 4.8 Place U2 with its loop filter and supply capacitors, and Y2 beside it [KHA p127, p253; LMX2571 p55].
- [ ] 4.9 Place U7, then FL1's five parts with its two inductors at 90° to each other, then U5 next to J2 [AN4169 p9, p11–12].
- [ ] 4.10 Place U4 with its front end (C34, L1, FB1, C35) close to U5 [AN383 p15, p17].
- [ ] 4.11 Place U1 with its decoupling, VCAP and NRST parts.
- [ ] 4.12 Place U3, U6 and the USB parts by J1.
- [ ] 4.13 Place every remaining passive at its pin, decoupling caps first [BAC p21–22; HHG p40].
- [ ] 4.14 Give like parts the same rotation and align polarized parts [KHA p127, p148; HHG p46].
- [ ] 4.15 Place TP1–TP8 where a probe can reach them [HHG p39, p48].
- [ ] 4.16 Check courtyards and mechanical fit [HHG p39].
- [ ] 4.17 Run `kicadcheck.py --pcb` until placement and every local part pass.
- [ ] 4.18 **Review checkpoint:** the user compares the placement and the 3D view with the layout page.

## Phase 5: Routing

- [ ] 5.1 Fan out every ground pad and exposed pad with vias, as many as the rules allow under each IC, then lock them [HHG p74–78; AN4169 p12; ADI "IC Ground Plane"].
- [ ] 5.2 Route 3V3 from U3 out to each load, not part to part [BAC p11; KHA p148, p170].
- [ ] 5.3 Route VBUS from J1 to U3 and D1 at power width [KHA p184].
- [ ] 5.4 Route the antenna line from J2 to U5 as a 50 Ω grounded coplanar line, with D5 at J2 [AN4169 p6, p11; ADI "Coplanar Waveguide"].
- [ ] 5.5 Route the transmit path from U2 through C26, U7 and FL1 to U5 the same way.
- [ ] 5.6 Route the receive path from U5 through C34, L1, FB1 and C35 to U4's FMI over unbroken ground [AN383 p15, p17].
- [ ] 5.7 Route U2's loop filter and OSCin compactly, with no switching line near them [LMX2571 p55].
- [ ] 5.8 Route the three I²S lines from U1's series resistors to U2, short and away from the loop filter.
- [ ] 5.9 Route USB D+ and D− as a short side-by-side pair through U6 [BAC p11].
- [ ] 5.10 Route U4's digital lines and RCLK away from its RF input [AN383 p15–16].
- [ ] 5.11 Route everything else with 45° corners, the bottom layer running mostly at 90° to the top [BAC p11, p13; KHA p130–131].
- [ ] 5.12 Review net lengths and remove detours [HHG p77].
- [ ] 5.13 **Review checkpoint:** the user reviews the routing.

## Phase 6: Ground pours

- [ ] 6.1 Pour ground on both layers, pulled back at least 0.5 mm from the edge [BAC p20; conflict C3].
- [ ] 6.2 Stitch the two pours with vias across the board, liberally through the RF area and along the RF lines [AN383 p15–16; ADI "Ground Planes"; BAC p22].
- [ ] 6.3 Connect the FMI shunt parts to ground without thermal reliefs [AN383 p17].
- [ ] 6.4 Remove dead copper [BAC p6, p11].
- [ ] 6.5 Check the copper is roughly balanced between the two sides [HHG p61–62; KHA p135].
- [ ] 6.6 **Review checkpoint:** the user reviews the pours.

## Phase 7: DRC and the netlist comparison

- [ ] 7.1 Run DRC against the JLC rules until it reports zero errors [BAC p17].
- [ ] 7.2 Run DRC's schematic parity check until the board matches the schematic [KHA p236–238].
- [ ] 7.3 Run `netcheck.py` and `kicadcheck.py --net --bom --pcb` until every check passes.
- [ ] 7.4 Check hole sizes, annular rings and part clearances [BAC p12; KHA p151].
- [ ] 7.5 Check part heights in the 3D view against the enclosure notes (placement rule M9).
- [ ] 7.6 **Review checkpoint:** the user reviews every check result.

## Phase 8: Outputs

- [ ] 8.1 Export Gerbers and the Excellon drill file with JLC's recommended settings [HHG p79–93].
- [ ] 8.2 Export the BOM in JLC's format (comment, designator, footprint, LCSC code).
- [ ] 8.3 Export the pick-and-place file and check every part's rotation in JLC's preview [HHG p94–113].
- [ ] 8.4 Inspect the Gerbers in KiCad's Gerber viewer [KLAP p68–69].
- [ ] 8.5 Upload to JLC for a quote and DFM check only; the user places the order.
- [ ] 8.6 **Final review:** commit the project and tag it `rev-a`.
