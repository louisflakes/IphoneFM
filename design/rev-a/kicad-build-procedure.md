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
- [x] 2.8 **Review checkpoint:** the user reviews the footprint list and its sources.
  - Review items agreed 2026-10-23, before starting: the built footprints (J1, U2, D1, SW3, RV1–RV3); departures from the makers (U4, Y2, larger IPC pads, D5 paste); interpreted pin numbering (D1, SW3, SW1, SW2); datasheets still from LCSC copies; trimmed silkscreen; and six not yet considered: footprint origins against JLC's placement point, through-hole J2 on an assembled board, missing 3D models, parts at the board edge, board-level holes and fiducials, and U4's 60 µm solder-mask clearance.
  - Decided 2026-10-23: U4's mask. Skyworks asks for the mask 60 µm clear of every pad; on KiCad's 0.30 mm pads that leaves 0.08 mm strips between pins, under JLC's 0.10 mm. The user chose to narrow the side pads to Skyworks' 0.28 mm and open the mask 0.06 mm (`tools/fp_u4_si4705.py`), which meets both with 0.10 mm strips between pins. Origins, through-hole J2, parts at the edge, and mounting holes and fiducials: no change (owned by steps 8.3, Phase 0 sourcing, Phase 4, and 3.5/3.7). 3D models and the datasheets still from LCSC copies: closed with no action at the user's judgement. JLC builds from the copper, mask, paste and placement files and uses its own part models, and the enclosure heights are in placement-rules.md M9; the five LCSC copies are the makers' own documents, each footprint was checked against them and approved, and the two replaced earlier (U6, D5) changed nothing on the land patterns.

## Phase 3: Board setup

- [x] 3.1 Open the PCB editor and set the stackup to JLC's 2-layer 1.6 mm FR4 with 1 oz copper [KLAP contents p7–8; HHG p63–65].
  - Done 2026-10-23 with `tools/pcb_setup.py` (file edit, KiCad closed): JLC0216A as recorded in fab-rules.md (0.030 mm copper, 1.43 mm FR-4 core) with JLC's published Dk (core 4.6, mask 3.8, mask 0.015 mm over copper; jlcpcb.com/impedance, read 2026-10-23). The stack sums to 1.52 mm, inside JLC's ±10% on the 1.6 mm order. Surface finish left for the order. Title block copied from the schematic. KiCad loads the board; DRC's only finding is the missing outline, which 3.4 adds.
- [x] 3.2 Enter the design rules from fab-rules.md.
  - Done 2026-10-23 with `tools/pcb_setup.py`: every row of fab-rules.md's "Our design rules" is in Board Setup (IphoneFM.kicad_pro) or, where Board Setup has no field, in IphoneFM.kicad_dru (0.25 mm ring on plated holes, 0.3 mm courtyard gap); 0.10 mm mask web, with webs inside a footprint allowed to drop out (U4, step 2.8); ready-made track widths 0.20/0.40/0.92 and the 0.30/0.60 via. KiCad parses the rules (DRC runs; only finding the missing outline). Checking the footprints' plated holes against them: J1's four shell slots have a 0.15 mm copper ring (HRO's 2020 drawing: 0.9 mm pad on a 0.6 mm slot), under our 0.25 mm and JLC's 0.18 mm absolute minimum; J2's are 0.40–0.45 mm.
  - Fixed the same day at the user's choice: `tools/fp_j1_hro2020.py` makes J1's shell pads 0.2 mm bigger both ways (1.1 × 2.2 and 1.1 × 1.9 mm) for a 0.25 mm ring, slots and positions unchanged; 0.275 mm copper and 0.525 mm hole clearance to the nearest signal pad. Silkscreen, paste and pin-to-pad checks still pass.
- [x] 3.3 Set the net classes' widths and clearances: default, power, 50 Ω RF lines and wider-spaced clocks [HHG p64].
  - Checked 2026-10-23: the four classes set at step 1.33 match fab-rules.md (Default 0.20/0.20, Power 0.40 track, RF 0.92 track with 0.20 gap, Clock 0.40 gap; 0.30/0.60 via in each), all at or above the step 3.2 rules. KiCad's own exported netlist puts exactly the nets fab-rules.md names in Power (4), RF (9) and Clock (8), and the other 72 in Default. No change needed.
- [x] 3.4 Draw the 46.45 × 71.40 mm outline on Edge.Cuts, with the grid origin at the envelope's top-left corner so board and sketch coordinates line up [KHA p252; HHG p36].
  - Done 2026-10-23 with `tools/pcb_setup.py`: a square-cornered 46.45 × 71.40 mm rectangle on Edge.Cuts at layout.html's envelope coordinates (x 12.70–59.15, y 59.56–130.96), so KiCad's absolute positions read the same as the sketch's; grid and drill origins on the top-left corner (12.70, 59.56), so positions relative to them are the board-corner offsets used for the mounting holes. KiCad's DRC: 0 violations.
- [x] 3.5 Ask the user whether the enclosure needs mounting holes, and if so add them as symbols and footprints [KLAP p105].
  - Asked 2026-10-23 while scoping Phase 3: yes, four M2 holes near the corners, marked by the user on the sketch. Standard corner spots are taken (top two on the MagSafe ring and D1, bottom two on SW1 and J2), so they sit near the corners at whole-millimetre offsets from the board's top-left corner for the enclosure model: H1 (13, 7), H2 (33, 7), H3 (41, 57), H4 (8, 66) mm. 2.2 mm unplated holes (KiCad MountingHole_2.2mm_M2) with a 4.4 mm copper-free circle; H1 and H2 sit inside the ring's open centre, H3 and H4 below it. H3 may move a millimetre or two in Phase 4 if the transmit filter needs room, staying on whole-millimetre offsets. Approved by the user.
  - Added 2026-10-23: H1–H4 in netlist.json (chain 10, no pins, not ordered, positions in their descriptions), on the schematic as Mechanical:MountingHole symbols beside the layout notes (`tools/sch_mountholes.py`, which keeps the board positions), with the footprint IphoneFM:MountingHole_2.2mm_M2 (KiCad's, out of the BOM and placement file). netcheck allows the H prefix. Checks: ERC 0 errors (the two U4 items excluded); `kicadcheck.py --net --bom` 17 of 17; pin-to-pad 106 of 106; silkscreen and paste pass. The holes go onto the board at their positions when the parts come across in Phase 4.
- [x] 3.6 Add keep-outs: copper at least 0.5 mm from the edge, and no through-hole parts over the magnet ring [HHG p105, p113; ADG R31 p278–279].
  - Done 2026-10-23 (`tools/pcb_setup.py`). Edge: the step 3.2 rule (copper 0.5 mm from the edge) covers every pad, track and pour, so no extra area is needed. Ring: two locked rule areas on both copper layers, "MagSafe ring" (Ø54.1 mm) and "MagSafe ring opening" (Ø46.0 mm), centred at (35.92, 77.74); they restrict nothing themselves. A rule in `IphoneFM.kicad_dru` flags any plated through-hole pad that touches the band between them (placement-rules.md M8); unplated holes and SMD parts over the ring stay allowed. The Alps wheels' locating pegs stand 0.9 mm below the frame, inside the 1.6 mm board (RK10J p2), so they need no rule. Checked on a throwaway copy: J2 on the band is flagged (5 pads); J2 in the open centre, an SMD part on the band and J2 at the sketch's position are not; a pad 0.34 mm from the edge is flagged. The real board: DRC 0 violations.
  - Seen while testing, for Phase 4: at the sketch's position J2's ground pins are 0.40 mm from the right and bottom edges, so J2 moves about 0.1 mm in. J1's two locating holes sit 0.22 mm from its four wide USB pads in HRO's own layout, under our 0.30 mm hole-to-copper rule; JLC's figure for unplated holes is 0.20 mm.
- [x] 3.7 Add fiducials if JLC's assembly rules call for them [conflict C4].
  - Done 2026-10-23: none on the board itself; they go on the rails. JLC's rule that part bodies sit 2.5 mm from the edge applies to every assembly order, and Rev A has parts at all four edges, so it needs break-off rails; at the 3.8 review the user chose rails on all four edges, in a panel we draw ourselves (fab-rules.md, "What this means for Rev A"). The fiducials go on those rails to JLC's size (1 mm copper, 2 mm mask opening, 3.35 mm from the rail edge, three or four of them). The rails are outside this board, in our own panel in Phase 8 (steps 8.3, 8.5). The board file is unchanged.
- [x] 3.8 **Review checkpoint:** the user reviews the empty board.
  - Prepared 2026-10-23: every Phase 3 setting read back from IphoneFM.kicad_pcb and .kicad_pro and matches 3.1–3.7 (stack 1.52 mm, outline 46.45 × 71.40 mm, origins on its top-left corner, rules, net classes Power 4 / RF 9 / Clock 8, the two ring areas, no footprints yet). DRC: 0 violations. Carried into Phase 4: J2 about 0.1 mm in from the corner, and J1's locating holes against the 0.30 mm hole-to-copper rule (3.6 notes). At the review the user pointed out the wheels need a rail on the left; rails are now planned on all four edges, drawn by us in Phase 8 (fab-rules.md).

## Phase 4: Placement (the most important step [BAC p8; HHG p36])

- [x] 4.1 Bring the parts across with Update PCB from Schematic (F8) [EES p96–97].
  - Done 2026-10-23 in KiCad (F8): 106 footprints (102 parts and H1–H4), 0 errors and 0 warnings in the dialog, all from the IphoneFM library; parked left of the board. KiCad had been open since before Phase 3, so its first save put back old design rules and J1's old shell pads from memory; KiCad was closed, the rules restored, and every footprint refreshed with Update Footprints from Library. Checked: every footprint's pads match the library file, schematic parity clean. KiCad also drops the mask Dk unless the mask material is named, so `tools/pcb_setup.py` now names it "Liquid Ink". DRC finds only the expected: parts piled on each other, nets not routed, and J1's locating holes (3.6 notes).
- [x] 4.2 Group the parts by chain off the board, with short pin-to-pin distances [HHG p37, p46].
  - Done 2026-10-23 with `tools/pcb_group.py`, live in the open board through KiCad's API (one undo step). Each IC stands with every part netlist.json puts at its pins, in pin order: to the right of the board, top to bottom as on the sketch, U2, Y2, U7 with SW3, U1 (with the wheel filter caps and SPI resistors at its pins), U4 with L1, U3, J1 with U6, and U5 with the TX filter and J2; the controls (wheels, SW1, SW2, D1 and their resistors) to the left; test pads and mounting holes below. No courtyards overlap and nothing is on the board.
- [x] 4.3 Place and lock J1 at its Rev A position [HHG p46; KHA p127, p147].
  - Done 2026-10-23, live: J1 at (35.925, 127.77), 0°, locked. HRO's drawing puts the PCB edge 5.79 mm in front of the two Ø0.60 holes, so the shell front stands about 0.4 mm past the edge (the plug's moulding clears the board); the sketch had the shell flush (y 127.285), 0.49 mm further in, and is corrected (layout.html). DRC on J1: only its locating holes, 0.22–0.28 mm from the wide pads against our 0.30 mm rule (JLC 0.20 for unplated holes), still open. Seen in the same DRC, not J1: the Clock class's 0.4 mm clearance also applies between pins, so every clock pin on U1, U2 and U4 (0.25 mm apart) is flagged; the 0.4 mm was meant for the tracks.
  - Fixed 2026-10-23 (the user's choice): the Clock 0.4 mm now applies only from a clock track to other nets' tracks and vias (`IphoneFM.kicad_dru`, written by `tools/pcb_setup.py`); clock pins keep 0.2 mm. Tested on a copy: a clock track 0.30 mm from another track is flagged, 0.45 mm and plain tracks pass, the clock pins pass. The class itself still reads 0.4 in the project file until `pcb_setup.py` next runs with KiCad closed; the rule file governs either way.
- [x] 4.4 Place and lock J2 at its Rev A position.
  - Done 2026-10-23, live: J2 at (54.99, 126.80), −90° (the footprint's barrel is at its −y; this turns it out of the right edge), locked. The footprint's leg lands are Ø2.2, not the sketch's 2.0, so it sits 0.11 mm left and 0.10 mm up of the sketch to keep copper 0.5 mm (+0.01) from the right and bottom edges; sketch updated. DRC on J2: no errors; 7 warnings where its silkscreen square comes 0.125 mm from the edge (the fab clips silk at the edge). Off the magnet ring.
- [x] 4.5 Place and lock RV1–RV3 at their Rev A positions.
  - Done 2026-10-23, live: RV1–RV3 at x 17.80 (y 78, 95, 112), 90° (the footprint's rim side is its −y; this turns it out of the left edge), locked. Alps' drawing (RK10J p2) puts each frame's rim-side locating peg 4.2 mm from the knob centre, in a 2.2 × 1.1 mm slot; the sketch's edge at 4.1 mm cut through it. At the user's choice the wheels moved 1 mm in: edge 5.1 mm from the centre, slot on the board with 0.35 mm spare, 1.9 mm of wheel past the edge (was 2.9). Sketch, placement-rules.md M3 and fab-rules.md updated. DRC on the wheels: no errors; 11 warnings where their wheel outlines run past the edge (silkscreen off the board isn't printed). No courtyard overlaps.
- [x] 4.6 Place and lock SW1, SW2 and SW3 at their Rev A positions, SW3's levers facing out.
  - Done 2026-10-23, live, all at the sketch's positions and locked: SW1 (14.65, 125.5) −90°, handle out of the left edge; SW2 (25.5, 129.21) 0°, knob out of the bottom edge; SW3 (35.925, 64.51) −90°, levers facing out of the top edge (the footprint draws them on its −x side; switch 1 at the right). Copper 0.5 mm from each edge. DRC: no errors, no courtyard overlaps; 3 warnings where outlines run past the edge. The sketch drew SW1's middle terminal mirrored (−0.75 instead of +0.75, the approved footprint); corrected.
- [x] 4.7 Place and lock D1 at the top right.
  - Done 2026-10-23, live: D1 at the sketch's (56.0, 63.0), 0°, locked; pin 1 (red) top left, as the sketch and XINGLIGHT p8 draw it; pads 2.3 mm from the right edge. DRC: no errors; one warning where its reference text touches its own outline (reference text is tidied later).
- [x] 4.8 Place U2 with its loop filter and supply capacitors, and Y2 beside it [KHA p127, p253; LMX2571 p55].
  - Done 2026-10-23, live, with the new `tools/pcb_local.py` (reused for 4.9–4.13): U2 at the sketch's (46, 76), 0°: RF out (pin 17) faces U7 below, the FSK and MICROWIRE pins face U1. Its 16 local parts sit just outside its courtyard opposite their pins, each pointing at its pin with the pin's pad nearest, spread evenly along each side, as on TI's evaluation board (SNAS654A p55): the four Vcc3p3, two VccIO, VcpExt, Bypass1/2, VrefVCO and VregVCO (C23, 0603) capacitors; the loop filter at CPout (C24 and R5 side by side, C25 straight out from R5); C26, the DC block, at RF out. R9 (CE pull-down, not critical) is in a second row. Y2 at the sketch's (39.5, 84), turned 90° so its output pin faces U2's OSCin; R4 at its output, C11 and C12 at its supply pin. DRC: no errors, no courtyard overlaps; warnings only for reference text over pads and outlines (tidied later).
- [x] 4.9 Place U7, then FL1's five parts with its two inductors at 90° to each other, then U5 next to J2 [AN4169 p9, p11–12].
  - Done 2026-10-23, live. U5's pins run receive (1), transmit (3), antenna (5) round the chip, so with J2 to the right the sketch's layout (filter down the right, U4 up-left) would have made the transmit line cross the receive or antenna line. The user chose the arrangement with no crossing: the transmit line comes down the left of the RF section and U4 goes right of it, above U5 (about (49, 109.5), placed in 4.10). Sketch and placement-rules.md R3 updated. U7 at (46, 94), turned −90° (`pcb_local.py`): RF in (pin 5) at the top from U2, RF out (pin 14) at the bottom, its six switch pull-downs on its right, C27 at VDD. U5 at the sketch's (47, 125), 0°, antenna pin toward J2 (`tools/pcb_rf_switch.py`). FL1 is an L just west of U5: C28 shunt at the input, L2 standing, C29 shunt, L3 lying (90° to L2) straight into pin 3, C30 shunt at pin 3; shunt capacitors grounded away from the line. C34 (receive DC block) stands above pin 1, R16 above pin 6, C31 and R17 below pin 4, D5 under the antenna line between U5 and J2. Every part's pad on the line's net faces the line (checked pad by pad). DRC: no errors, no courtyard overlaps.
- [x] 4.10 Place U4 with its front end (C34, L1, FB1, C35) close to U5 [AN383 p15, p17].
  - Done 2026-10-23, live (worked ahead with steps 4.11–4.13 from the rollback point `rollback/phase4-before-corridor`, at the user's request). Placement order from the books first: fixed parts, then critical (RF) parts for the shortest critical lines, the most-connected part (U1, 34 signal connections) as the hub, the rest grouped round it [KHA p127, p253; BAC p9–10; HHG p40]. The non-critical lines that must reach the right of the transmit line (U4's 7, SW3's 6, D1's 3 and 3V3, about 17 tracks) go over the top of U2 and down the right edge, never under the RF parts [AN4169 p12]; U2 moved 3 mm left then 3 mm down to (43, 79), and Y2 to (33, 82), to make that corridor: about 6.4 mm over U2 plus 4 mm above H2, 6.5 mm down U2's right (measured from the courtyards). U4 at (48.5, 112), turned 90°: FMI (pin 2) faces U5, I²C and RCLK face the corridor; its 13 parts at their pins (`pcb_local.py`); FB1 and C35 at FMI, L1 standing under FB1 at the matching node (`tools/pcb_place.py`), C34 above U5 pin 1. 11.6 mm from U5's receive pin, 33 mm from U2.
- [x] 4.11 Place U1 with its decoupling, VCAP and NRST parts.
  - Done 2026-10-23, live: U1 at (36, 94), 0° (1 mm right and down of the sketch): the U2 lines (LMX, FSK) and USB on its right, U4's lines and LED_R on top toward the corridor, the wheels and CC on its left, the rest below. 17 parts at their pins; the transmit line leaves U7 straight down before stepping left near U4, which leaves room on U1's right. `pcb_local.py` now keeps parts on the board and slides them up to 6 mm along a side.
- [x] 4.12 Place U3, U6 and the USB parts by J1.
  - Done 2026-10-23, live: U6 at (35.925, 117.5), −90°, so D+ and D− pass straight through it from J1's B-row pads to U1 in the order U1 needs them; R1, D3 (CC1) and R2, D4 (CC2) beside J1's CC pads, clear of the USB pair; U3 at (31, 114.5), 90°, its input pins toward J1's VBUS, C1 at the input, C2 at the 3V3 output.
- [x] 4.13 Place every remaining passive at its pin, decoupling caps first [BAC p21–22; HHG p40].
  - Done 2026-10-23, live: R25 left of D1 and R26, R27 below it (D1 is in the corner, so its edge sides have no room); R18 at SW1's RF_MODE pin. H1–H4 placed and locked at their step 3.5 positions (fixed parts, missed at 4.3–4.7). Every part except TP1–TP8 (4.15) is on the board. DRC: no errors and no courtyard overlaps; only J1's eight known hole findings. One squeeze to watch in routing: RF_MODE to R17 passes between J1 and the filter (about 1.7 mm).
- [x] 4.14 Give like parts the same rotation and align polarized parts [KHA p127, p148; HHG p46].
  - Done 2026-10-23: HHG p46 asks for similar rotation of like parts for assembly and inspection. Each row of like parts at a pin already shares one rotation (U7's six pull-downs, U1's bottom row, each side of U2); the one polarized pair, D3 and D4 (CC ESD), match at 90°. Turning the radial parts to one angle would turn their pads away from their pins, so pin-first placement [BAC p21–22; HHG p40] keeps priority. No change.
- [x] 4.15 Place TP1–TP8 where a probe can reach them [HHG p39, p48].
  - Done 2026-10-23, live: the SWD set in one row under U1 at y 104.5 (TP6 NRST, TP3 GND, TP2 3V3, TP7 SWCLK, TP8 SWDIO, 2.85 mm apart); TP1 VBUS beside J1; TP4 RF_MODE above SW1; TP5 LMX_MUX between U1 and U2 on its line. All on the top side, clear of the tall parts (placement-rules T1).
- [x] 4.16 Check courtyards and mechanical fit [HHG p39].
  - Done 2026-10-23: DRC finds no courtyard overlaps and no copper-to-edge or ring-rule errors; every part on the top side (M7); no through-hole lead over the magnet ring (only J2 has them); the tall parts (J2, SW3, J1, wheels) are where M9 has them. Found while checking: turning or locking a part through KiCad's API drops its 3D model link, so the board had none left (positions and copper unaffected); restored with Update Footprints from Library.
- [x] 4.17 Run `kicadcheck.py --pcb` until placement and every local part pass.
  - Done 2026-10-23: every check passes. The first run had four local parts over 4 mm; C39/FB2 swapped and U1's left column moved up, C12 moved in beside Y2, R9 moved to U2's bottom corner. C28 (FL1's input shunt) was tied to U7 pin 14 in netlist.json from when the filter sat at U7; it now sits with the filter, so its local_to is L2.1 (placement anchor only, no connection changes; netcheck 19/19). DRC with schematic parity: 0 footprint errors; only J1's eight known hole findings.
- [x] 4.18 **Review checkpoint:** the user compares the placement and the 3D view with the layout page.
  - Approved 2026-10-23 ("looks okay to me to move forwards with trying to route"), from the 3D top and angled views and the placement drawn with its planned main routes; 3D model links restored first (Update Footprints from Library, nothing moved).

## Phase 5: Routing

- [x] 5.1 Fan out every ground pad and exposed pad with vias, as many as the rules allow under each IC, then lock them [HHG p74–78; AN4169 p12; ADI "IC Ground Plane"].
- [x] 5.2 Route 3V3 from U3 out to each load, not part to part [BAC p11; KHA p148, p170].
- [x] 5.3 Route VBUS from J1 to U3 and D1 at power width [KHA p184].
- [x] 5.4 Route the antenna line from J2 to U5 as a 50 Ω grounded coplanar line, with D5 at J2 [AN4169 p6, p11; ADI "Coplanar Waveguide"].
- [x] 5.5 Route the transmit path from U2 through C26, U7 and FL1 to U5 the same way.
- [x] 5.6 Route the receive path from U5 through C34, L1, FB1 and C35 to U4's FMI over unbroken ground [AN383 p15, p17].
- [x] 5.7 Route U2's loop filter and OSCin compactly, with no switching line near them [LMX2571 p55].
- [x] 5.8 Route the three I²S lines from U1's series resistors to U2, short and away from the loop filter.
- [x] 5.9 Route USB D+ and D− as a short side-by-side pair through U6 [BAC p11].
- [x] 5.10 Route U4's digital lines and RCLK away from its RF input [AN383 p15–16].
- [x] 5.11 Route everything else with 45° corners, the bottom layer running mostly at 90° to the top [BAC p11, p13; KHA p130–131].
  - Attempts so far (2026-10-23/24), for what they taught:
    - Freerouting v2.5.0 (official release; `tools/pcb_freeroute.py`), three runs around the locked ground fan-out, RF lines and loop filter, GND left to the pours and no bottom copper under the RF section: 45, 43, then 37 signal connections left unrouted (after nudging Y2 up, TP5 beside U1 and the SWD pads down). Nearly all were U1's: U1 is the hub, boxed in by the wheels, the transmit line, U2's parts and the test pads, and its lines to U4, D1 and U2's CE must go over U2 and down the right-edge corridor.
    - Hand-routing U1, attempt 1 (`tools/pcb_route_u1.py` on the two-layer `tools/pcb_astar.py`, from tag `rollback/phase5-before-u1-handroute`): 35 of 52 routed. U1's 18 short links to its own parts (decoupling, VDDA, VCAP, NRST, wheel filters, FSK resistors, BOOT0) came out clean. The long runs over U2 and down the corridor also worked (I²C SCL, RX SD and FS, LED R, RF_MODE, BOOT0). But routing one connection at a time, greedily, with no lanes planned and no rip-up, made medium runs wander (USB D+ 35 mm with 4 vias), added vias U1-to-U2 links don't need, three new hole-clearance findings, and boxed later pins in (17 failed).
    - Lessons: (1) U1's right side has a built-in crossing: MICROWIRE (pins 25–28, bottom of the side) goes up to U2, while USB and SWDIO (pins 32–34, top of the side) go down to U6 and TP8; R6–R8 and C5, radial at pins 29–31 and 36, stand in front of pins 27–28 and 32–33. So U1's right side needs its escape planned first: which lines leave on top and in which lane, which drop to the bottom and where their vias go, kept in pin order so nothing crosses. (2) Lay that escape before anything else near U1, then the U1–U2 links, then the rest. (3) Long runs keep to set lanes (the corridor) so they don't wall in what comes after. (4) Leave U1's short local links as they are.
    - Attempt 2, U1's right side (2026-10-24, tag `rollback/phase5-u1-right-done`): moving R6–R8 alone routed at most 8 of the 13 right-side lines (`tools/pcb_try_r678.py`, 6 places tried). The rest were crossings, settled by pin order (the user's decisions in bold):
      - **MICROWIRE reordered at U1: 28 MUX, 27 CLK, 26 DATA, 25 LE, driven by GPIO (bit-banged) instead of SPI2**, so the four lines reach U2's pins 10–13 in order. SPI2's fixed SCK and MOSI pins would have crossed DATA over two lines.
      - U6's two identical ESD channels swapped (D− on I/O1, D+ on I/O2) and TP7/TP8 traded places (TP8 SWDIO now west of TP7 SWCLK), so USB and SWD reach their pins in the order they leave U1. No change to function.
      - Laid by `tools/pcb_lay_u1right.py`: a seven-line top-layer bus from pins 25–31 up between U1 and the transmit line, turning up-left alongside ATT_IN (whose bend moved 1.7 mm toward C26 to make room). MICROWIRE runs straight into U2's bottom pins. The FSK lines run through R6–R8, now a row above U1's top-right corner, then drop to the bottom layer into U2's entry vias. USB D+/D−, SWDIO and SWCLK cross under the bus on 4–8 mm bottom-layer hops from hand-placed vias beside pins 32–37, then run down to U6, TP8 and TP7. C5 turned to stand at U1's corner.
      - Router fixes: vias were being placed at grid indices (off the board), so earlier "routed" results with vias were not real. Bottom-layer steps now cost 3× so crossings stay short. DRC: only J1's 8 known hole-clearance findings.
    - Floorplan study (2026-10-24/25, `tools/pcb_floorplan.py`, pictures `floorplan-round1.png`, `floorplan-round2.png`): every attempt stalled at U1, so the placement was scored before more routing. Each layout is routed roughly on one layer with negotiated congestion. Today's layout came out at 2281 mm and 525 cells over capacity. The cause: U4 and D1 sat across the transmit line from U1, so 11 lines wrapped over U2 through a 3.9 mm gap. **The user chose B3:** the transmit chain (U2, Y2, U7) below U1, feeding U5 from the west; U4 with its input parts (C34, L1, FB1, C35) at the top right, fed by the 50 Ω receive line up the right edge; U1 turned 90° so its I²S/MICROWIRE/USB side faces U2 and J1 and its receiver/LED side faces U4 and D1.
    - B3 placed (tag `rollback/phase5-b3-placed`, `placement-b3.png`): routing cleared for a fresh start; R6–R8 in a row between U1 and U2; Y2 turned to face both; SWD pads TP7/TP8 beside U1; TP6 by NRST; TP5 by the MICROWIRE lines. Scored as placed: 1299 mm, 125 cells over, 199 crossings (versus 2281 / 525 / 318 before).
    - Routing prep for B3 (2026-10-25):
      - **RF keep-out:** redrawn as three zones (`RF_BOTTOM_POLYS`: the transmit chain with U5/J2, the receive corridor, and U4's front end).
      - **RF lines planned in `tools/pcb_route_rf.py`** (`place`, then `lay`; pictures `phase5-rf-plan-tx.png`, `phase5-rf-plan-rx.png`):
        - U5 is up 1.1 mm, so the antenna line leaves straight and runs east between J2's legs.
        - The filter output climbs past L2 and drops into U5's north-facing pin 3.
        - The receive line runs about 40 mm at 50 Ω, with GND stitching vias on both sides.
        - Twelve small parts were nudged (C17, C26, C28, C30, C31, D4, R2, R16, R17, D5, L1, FB1, C35).
        - DRC is clean apart from J1's known hole findings.
      - **New `tools/pcb_quality.py`:** the routing-quality check, run alongside `pcb_drc.py`. It checks 45° segments, 45° bends, straight pin exits of at least 1 mm (local connections of up to 2.5 mm excepted), one pitch per bus, clearance and the RF bottom zones. It also scores plans before any copper goes down. The RF plan passes it.
      - **Lane plan** (`phase5-lanes.json`, `phase5-lane-plan.png`), for the user's review before routing.
    - Complications cleared before routing (2026-10-25, the user's go-ahead):
      - **U1 re-pin:** RX_RST moved to PB9 (46) and RX_RCLK to PB4 (40, TIM3_CH1 AF2). The receiver lines now leave U1 in nearly U4's order; the U1-to-U4 crossings drop from 8 to 3. Checked against DS14217 Tables 27/28 and AN2606 Table 165. FS/SD stays one crossing, because SAI1 block B fixes FS on PB6 above SD on PB5.
      - **U4 corner, fully planned** in `tools/pcb_route_u4.py`:
        - U4's group is 2.5 mm lower.
        - RCLK and RST reach U4 on the bottom layer; FS dives under SD within the bundle.
        - SDA and SCL run down the strip on U4's east side; the pull-ups sit where those lines are outermost.
        - The FS/SD series parts and U4's supply parts sit in a pocket above U4.
        - C36 (the datasheet's C9) moved to R23's U1 side, where Si4704/05 p16 draws it. R3 moved to SW2.
      - **U2's east capacitor column** re-stacked (and Y2 raised 0.9 mm), so U2's CE pin (19) has a straight way in below C15. R5/C25 and R9 moved east. C11 and C12 sit above Y2. R4 sits on the REF20 line. C18/C19 shifted, so REF20 reaches pin 34 straight from the north.
      - **U3, C1 and C2** moved 1.6 mm lower, so the MICROWIRE lines pass above them.
      - **RF plan:** follows the lower U4 group. Receive-line stitching vias skip the stretch where the U7 control lanes run on the line's west side.
      - **TP1, TP5 and TP8** moved to the bottom side as bare pads (the user's choice), flipped with KiCad's own flip action. All test pads are now out of the position files, so the bottom side adds no assembly.
    - **Routed, 2026-10-25/26** (tag `rollback/phase5-before-lay`, then laid and locked): eight region plans, each built
      as copper with `tools/pcb_plan.py`, checked, then laid through KiCad's API. In laying order: `pcb_route_gnd.py`
      (step 5.1), `pcb_route_u1.py`, `pcb_route_u2.py`, `pcb_route_j1.py`, `pcb_route_att.py`, `pcb_route_north.py`,
      `pcb_route_u4.py`, `pcb_route_rf.py`. 825 tracks and 180 vias in total.
      - **U2:** C13 at U2's top-left corner; BYP1/BYP2 fan into C20/C21; FSK_CLK hops under FS/DATA. The PLL
        capacitor column is re-stacked so each line rises at 45° into its capacitor. U6 is 0.7 mm lower, so the USB
        pair comes up north of it.
      - **The user's two bottom 3V3 links in the RF zone (2026-10-25):** link 1 runs from pin 27's line under the
        PLL column to pin 20/C15 and on to C27 and U7's supply (about 7 mm, longer than the 4–6 mm asked, because the
        enclosed pin-20 node needs a source). Link 2 is U7's LE pin. Both are recorded as `RF_BOTTOM_ALLOW`.
      - **J1 corner:** D+/D− flow straight through U6, with the A/B crossover at J1. CC2 hops under U6. VBUS runs to
        C1/U3 on top and joins U6.5 and the east VBUS pad on the bottom. RF_MODE runs west to TP4/SW1/R18 and east
        under J1 to R17.
      - **West strip (bottom), west to east:** VBUS (to the LED lane), BOOT0 (to SW2/R3), and the pots' 3V3 by vias.
        U1's north 3V3 group joins the rest along RV1.1–RV2.1 under the pot bodies.
      - **Attenuator bus:** RST moved to the top layer (over the U4 corner, down outside RCLK), which opens the
        bottom north of the receiver bundle. The six ATT lines then cross under the bundle in one via staircase and
        come up west of the U4 corner. R10–R15 moved 1.7 mm east to clear H2. The lines reach SW3 under its body.
      - **North band:** LEDs and VBUS hop under the ATT lanes. D1's resistors were re-placed so VBUS, B, G and R
        arrive in lane order (R25 now in the edge lane). 3V3 runs on the bottom from FB2/C3 to SW3's row (TP2),
        U4's supply via, R20's via, and down the east edge outside the RF zones to R16. TP3 is beside TP2.
      - **Ground (5.1):** via arrays in the U1, U2, U4 and U7 pads, with their ground pins bridged in. Every other
        ground pad has a via at the nearest clear spot. U5.2 (between U5's RF pins) is left to the pour.
      - **Checks added on the way:** vias against pads and holes, and the Clock class's 0.4 mm rule. DRC caught
        the clock rule after the first lay. That copper was removed and re-planned: U1's RCLK/SCK and
        LMX_CLK/FSK_CLK step out to 0.6 mm right after their 1 mm exits, and two vias moved off ground pads. The
        rule's escape exemption is now "Clock escape" rule areas (courtyard + 1.5 mm) round U1, U2 and U4,
        because the step-out ends about 1.5 mm past the pad tips rather than 1.0.
      - **Result:** `pcb_quality.py` 0 findings on the board; `pcb_open.py` 0 open nets (GND from the pours); DRC
        only J1's 8 known hole clearances, 104 ground vias waiting for the pours, and silkscreen (Phase 7).
- [x] 5.12 Review net lengths and remove detours [HHG p77].
  - Routed length against the minimum span of each net's pads (2,145 mm over 71 nets, GND aside). The high ratios
    are all deliberate: RX_RST 2.8× (over the U4 corner, so the ATT bus can pass under the receiver bundle); TX_RF
    2.0× (the filter output past L2, as the RF plan places it); I²C, MICROWIRE and LED_R_K 1.6–1.8× (their lanes
    over the U4 pocket, under U2 and round D1). No accidental detours; nothing removed. Pictures:
    `review/phase5-routed-board.png`, `-north.png`, `-south.png`.
- [x] 5.13 **Review checkpoint:** the user reviews the routing.
  - Approved 2026-10-26, including the 1.5 mm clock escape areas and the 7 mm bottom 3V3 link 1.

## Phase 6: Ground pours

- [x] 6.1 Pour ground on both layers, pulled back at least 0.5 mm from the edge [BAC p20; conflict C3].
  - Done 2026-10-26: zones "GND top" and "GND bottom" on the board outline (the 0.5 mm edge rule pulls them back), 0.2 mm clearance (the RF lines' coplanar gap), 0.2 mm minimum width, thermal reliefs 0.3/0.3 mm on pads, islands always removed. The bottom pour is unbroken under the RF zones apart from the two approved 3V3 links.
- [x] 6.2 Stitch the two pours with vias across the board, liberally through the RF area and along the RF lines [AN383 p15–16; ADI "Ground Planes"; BAC p22].
  - Done: `tools/pcb_stitch.py` placed 123 ground vias on a grid, 3 mm across the board and 1.5 mm inside the RF zones, each where both fills cover the whole via and it clears other copper, holes and vias. These are on top of the receive and antenna lines' own stitching (RF plan) and the 5.1 fan-out: 303 vias in all.
- [x] 6.3 Connect the FMI shunt parts (C35, L1) and the GPO caps (C37, C38) to the top ground fill without thermal reliefs [AN383 p17].
  - Done: solid (no thermal relief) on the ground pads of C35, L1, C37 and C38, and on the five pads DRC found starved of spokes (U5.2 between U5's RF pins, U4 pins 3/4, J1 A1/B12/A12/B1). U5.2 reaches the pour this way.
- [x] 6.4 Remove dead copper [BAC p6, p11].
  - Done: island removal leaves no dead copper. DRC finds no unconnected items, dangling vias or isolated fill.
- [x] 6.5 Check the copper is roughly balanced between the two sides [HHG p61–62; KHA p135].
  - Done: copper covers 71% of the top and 87% of the bottom (pours, tracks and pads). Roughly balanced for a two-layer 1.6 mm board with every part on top. Pictures: `review/phase6-pour-top.png`, `-bottom.png`, `-top-rf.png`.
- [x] 6.6 **Review checkpoint:** the user reviews the pours.
  - Approved 2026-10-26.

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
