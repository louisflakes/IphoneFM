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
- When wiring a chain, also wire every passive placed at one of its chips' pins, and lay out crowded pins so they can be wired, as [docs/pcb-design-workflow.md](../../docs/pcb-design-workflow.md) §1 "Wiring around a dense chip" says. Net labels (step 1.30) join only nets that run between zones.
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
- [x] 1.16 Place D1, D3, D4 and D5 and check their pins against their datasheets, with diode pins named A and K [HHG p29].
- [x] 1.17 Place every passive beside the pin it serves, as netlist.json's `local_to` says [BAC p3].
- [x] 1.18 Give every symbol its designator, value, MPN and LCSC code from netlist.json, without letting KiCad renumber them [HHG p27, p34; KHA p106].

Wiring (one bom.md chain per step):
- [x] 1.19 Wire the power symbols for VBUS, 3V3, VDDA, RX_VDD and GND [EES p37].
- [x] 1.20 Wire chain 1: J1, the CC resistors and the USB ESD parts.
- [x] 1.21 Wire chain 2: U3 and its capacitors.
- [x] 1.22 Wire chain 3: U1's supply, reset, boot and debug pins.
- [x] 1.23 Wire chain 4: Y2, its capacitors and R4.
- [x] 1.24 Wire chain 5: U2, its supply capacitors, the loop filter and its control lines.
- [x] 1.25 Wire chain 6: U7, its pull-downs and SW3.
- [x] 1.26 Wire chain 7: FL1, U5, SW1, J2 and D5.
- [x] 1.27 Wire chain 8: U4 and its front end, supply and digital lines.
- [x] 1.28 Wire chain 9: the wheels, the BOOT button and the LED.
- [x] 1.29 Wire chain 10: the test pads TP1–TP8.
- [x] 1.30 Label every net with its netlist.json name, one name per net [EES p31, p38].
- [x] 1.31 Put a PWR_FLAG on every rail fed from a connector or from a pin that isn't a power output, and on GND [EES p39, p77–78].
- [x] 1.32 Put a no-connect flag on every pin netlist.json marks NC [EES p39].
  - Each of the 21 pins was checked against its datasheet before its flag went on (2026-10-22): U3 pin 4 "NC: No Connection" (AP2112 pin table); U4 pins 1, 20 "No connect. Leave floating." (Si4705 §5.1); U2 NC 8, 14, 26 "Do not connect these pins", Fin "Leave it open… if not being used", CPoutExt/FLout1/FLout2 outputs for external-VCO mode only, OSCin* left open for a single-ended clock (SNAS654A Table 37), RFoutRx an output switched off in its registers; J1 A8/B8 are SBU1/SBU2 (HRO pin table), unused by USB 2.0; U1 PC13–15, PH1, PA7, PA15, PB9 spare, every pin in analog state after reset (DS14217 §3.9.6).
- [x] 1.33 Assign net classes for the RF nets, the clock and switching nets, and power [EES p39–44; HHG p64].
- [x] 1.34 Add layout notes on the sheet: decoupling at the pins, rule R8 for the I²S clock, and no thermal reliefs on the FMI shunt parts [BAC p3; AN383 p17; LMX2571 p55].

Checks:
- [x] 1.35 Run ERC and fix everything until it reports zero errors, recording any deliberate exclusion with its reason [EES p74; KLAP p39].
  - ERC found 2 errors, both the deliberate U4 LOUT/ROUT tie to ground. Reviewed together with the user and confirmed harmless (AN383 p17; digital-only mode), then recorded as exclusions with that reason. ERC now reports 0 errors, 0 warnings (details in [verification.md](verification.md)).
- [x] 1.36 Export the netlist and run `kicadcheck.py --net` until every check passes.
- [x] 1.37 Export the BOM and run `kicadcheck.py --bom` until every check passes.
- [x] 1.38 **Review checkpoint:** the user reviews the whole sheet and the check results.

## Phase 2: Footprints

- [x] 2.1 Choose each part's footprint source in this order and record it: KiCad's library, then the maker's own, then LCSC/EasyEDA.
- [x] 2.2 Compare each footprint's pads with its datasheet land pattern and the true-size drawing in layout.html, one part per step [HHG p35].
  - Done 2026-10-22, each part approved by the user on a to-scale overlay of the footprint's pads and the maker's lands; results per part in [footprints.md](../../kicad/rev-a/footprints.md). The body sizes in layout.html agree with every footprint.
  - Built as project footprints (kicad/rev-a/IphoneFM.pretty, scripts in tools/): J1 (HRO's 2020 layout), U2 (TI's 4.6 mm centre pad), D1 (Xinglight), SW3 (KingTek pads, C&K body), RV1–RV3 (Alps). Kept KiCad's for the rest, including U4 by the user's decision.
  - Datasheets replaced with the makers' current ones on the way: U6 (ST DS4260 Rev 7), D5 (Semtech Rev 4.0).
- [x] 2.3 Confirm every symbol pin number has a pad of the same number [EES p133].
  - Checked 2026-10-22 with `tools/pinpad_check.py` on all 102 symbols. First run: one mismatch, SW1, whose symbol calls the four tabs pin 4 while KiCad's footprint names them "SH" (they would have been left unconnected). At the user's choice, SW1 now uses a project copy with the tabs numbered 4, as Shou Han's drawing does. Second run: 0 mismatches. Pads sharing a number, all intended: J1's four shell pads (SH), J2's four ground legs (2), SW1's four tabs (4), SW2's 1/1′ and 2/2′ (joined inside the switch).
- [x] 2.4 Check each footprint's silkscreen: real-size body outline, pin 1 and polarity marks, no ink on pads, lines at least 0.25 mm wide [BAC p13; KHA p149].
  - Checked 2026-10-23 with `tools/silk_check.py`. KiCad's footprints (and ours, which followed them) draw silkscreen 0.10–0.12 mm wide, under JLC's 0.15 mm minimum and our 0.25 mm, and 11 of 24 put ink closer than 0.20 mm to a pad. The user chose to keep the 0.25 mm rule and trim. `tools/fp_silk_trim.py` makes every footprint a project copy with lines widened to 0.25 mm and cut back to 0.20 mm from copper and holes; every pin-1 mark is a round dot 0.55 mm across, at the user's request instead of KiCad's triangles (moved outward where needed), and D1 and Y2 get one beside pad 1. Re-check: 24 of 24 pass; the 0402/0603 parts, test pads and D5 are left without outlines, which the user accepted (bench reading is not a priority). Pin-to-pad check still 0 mismatches.
- [x] 2.5 Check each paste layer is 1:1 with its pads [HHG p96, p113].
  - Checked 2026-10-23 with `tools/paste_check.py`: every soldered pad gets paste its own size, with no paste margins, except the centre pads, which get separate windows: U1, U2 and U7 about 65% (KiCad's pattern; TI and pSemi give none), U4 36% (KiCad's, the user's decision at 2.2). The test pads, J2's and the through-hole pins get none, as intended. One deviation found and fixed: KiCad's D_SOD-882 (D5) printed reduced paste, about 36% of each pad, from Nexperia's drawing; Semtech gives no stencil and TI prints 1:1 on the same-size D3/D4, so `tools/fp_d5_sod882.py` makes it 1:1. Re-check: 0 footprints with paste problems; silkscreen and pin-to-pad checks still pass.
- [x] 2.6 Assign the footprints in the footprint assignment tool, using its filters [EES p85–92].
  - Done 2026-10-23 for all 102 symbols in one pass, at the user's suggestion, with `tools/sch_footprints.py` (writes each part's IphoneFM footprint from footprints.md into its Footprint field) rather than the assignment tool. 87 symbols already carried KiCad library names, none conflicting with the choices; 15 were empty. Checked with KiCad's own exports: the netlist lists 102 footprints, all IphoneFM, each with a file in IphoneFM.pretty; ERC unchanged (0 errors, the two U4 items excluded); `kicadcheck.py --net --bom` 17 of 17 pass.
- [x] 2.7 Re-run ERC, re-export the netlist and run `kicadcheck.py --net` again.
  - Run 2026-10-23 on the schematic with all footprints assigned: ERC 0 errors and 0 open warnings, with the two U4 LOUT/ROUT items still excluded (step 1.35); KiCad's netlist re-exported; `kicadcheck.py --net` 11 of 11 pass (every part present, every connected pin has a pad, no opens, no shorts, NC pins open, LCSC codes and part numbers match, passive footprint sizes right).
- [ ] 2.8 **Review checkpoint:** the user reviews the footprint list and its sources.
  - Review items agreed 2026-10-23, before starting: the built footprints (J1, U2, D1, SW3, RV1–RV3); departures from the makers (U4, Y2, larger IPC pads, D5 paste); interpreted pin numbering (D1, SW3, SW1, SW2); datasheets still from LCSC copies; trimmed silkscreen; and six not yet considered: footprint origins against JLC's placement point, through-hole J2 on an assembled board, missing 3D models, parts at the board edge, board-level holes and fiducials, and U4's 60 µm solder-mask clearance.
  - Decided 2026-10-23: U4's mask. Skyworks asks for the mask 60 µm clear of every pad; on KiCad's 0.30 mm pads that leaves 0.08 mm strips between pins, under JLC's 0.10 mm. The user chose to narrow the side pads to Skyworks' 0.28 mm and open the mask 0.06 mm (`tools/fp_u4_si4705.py`), which meets both with 0.10 mm strips between pins. Origins, through-hole J2, parts at the edge, and mounting holes and fiducials: no change (owned by steps 8.3, Phase 0 sourcing, Phase 4, and 3.5/3.7). 3D models and the datasheets still from LCSC copies: closed with no action at the user's judgement. JLC builds from the copper, mask, paste and placement files and uses its own part models, and the enclosure heights are in placement-rules.md M9; the five LCSC copies are the makers' own documents, each footprint was checked against them and approved, and the two replaced earlier (U6, D5) changed nothing on the land patterns.

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
- [ ] 6.3 Connect the FMI shunt parts (C35, L1) and the GPO caps (C37, C38) to the top ground fill without thermal reliefs [AN383 p17].
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
