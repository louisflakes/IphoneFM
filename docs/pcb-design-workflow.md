# PCB design workflow and rules

The process to follow for schematic capture and layout, with each rule cited to a book in `Books/` (kept local, not in the repo).
Where the books disagree, the conflict is listed at the end rather than settled silently. Fab-house rules override every number here.

## Sources

| Tag | Book | Pages cited |
|---|---|---|
| EES | KiCad team, *Schematic Editor* reference manual (©2010–2024, KiCad 8) | Printed page numbers |
| KLAP | Dalmaris, *KiCad Like a Pro* 3rd ed., course companion (2021) | Printed page numbers. Companion edition: the design-principles and workflow-detail chapters are omitted (p5) |
| BAC | Bay Area Circuits, *Introduction to PCB Design* v1.1 (2016) | Printed page numbers |
| HHG | EMA Design Automation, *The Hitchhiker's Guide to PCB Design* (2018) | Printed page numbers |
| KHA | Khandpur, *Printed Circuit Boards: Design, Fabrication, Assembly and Testing* (McGraw-Hill, 2006) | Printed page numbers |

Also in `Books/` but not used for rules: Allied, *Understanding Schematic Diagrams* (1967); an introductory electronics/Arduino textbook (503 pp); Young, *Complete Guide to Reading Schematic Diagrams* (scanned images, no text layer, not read).

## 0. Before any CAD work

1. Collect constraints first: outline, thickness, mounting holes, fixed-position parts, keep-outs, height limits, environment, volume, cost [HHG p16–25, p35–36; KHA p109].
2. Read the fab's and assembler's design rules and use them as the starting point. Never set rules at the fab's minimum [HHG p15, p63–65; BAC p4, p11].
3. Never trust tool defaults. Review every rule before use [HHG p15, p63–64].

## 1. Schematic capture (KiCad Eeschema)

Steps: setup → symbols → arrange, annotate, associate → wire → nets → ERC → comments [KLAP contents p7; EES p8].

Drawing:
- Place symbols and wires on the 50 mil (1.27 mm) grid. Wires connect only where their ends coincide exactly, and ERC flags off-grid ends [EES p10, p29, p81].
- Crossing wires don't connect without a junction dot. Only wire ends connect [EES p28, p30].
- Signal flow runs left to right, with higher voltages toward the top of the sheet [KHA p108; BAC p3].
- Draw each bypass cap beside its IC, and add layout notes on the sheet [BAC p3].
- Use the IEEE/ASME reference designator conventions [HHG p27, p34; KHA p106].
- Make the schematic readable by other people, and get it reviewed [BAC p3; HHG p28, p32].

Nets and power:
- Each net gets one name; two different labels on one net is an ERC violation. Name priority is global label > power symbol > local label > hierarchical label > sheet pin [EES p31, p38].
- Label scope: a local label connects within one sheet, a global label everywhere, a hierarchical label to its sheet pin [EES p31, p66].
- In KiCad 8, a power symbol joins its net globally by its Value field [EES p37].
- Put a PWR_FLAG on any rail fed from a connector or a non-power-output pin, and usually on GND too. Without it ERC reports an undriven power input [EES p39, p77–78].
- Avoid hidden power pins [EES p39, p142].
- Put a no-connect flag on every intentionally unused pin [EES p39].
- Assign net classes in the schematic, by pattern, directive label or a label field [EES p39–44].

Symbols:
- Pin electrical types decide what ERC can catch, so choose each pin's type for the ERC behavior you want [EES p74, p132–135].
- Symbol pin numbers must match footprint pad numbers [EES p133].
- Check symbols against their datasheets. ERC won't catch wrong footprint mapping or pin numbering [HHG p33–34].
- Name diode pins A and K rather than 1 and 2 [HHG p29].
- Add an MPN field to every part with a field-name template [EES p54].

Finishing:
- Resolve every ERC violation before layout; ERC can't catch everything [EES p74; KLAP p39].
- Assign footprints using the symbol's footprint filters and pin-count filter [EES p85–92].
- Mounting holes get symbols too, so DRC doesn't flag them [KLAP p105].
- Move the design to the board with Update PCB from Schematic (F8); no netlist file is needed [EES p96–97].

## 2. Footprints

- Start from the maker's land pattern and compare it with IPC-7351. Joints should meet J-STD-001 [HHG p35]. For this project the passive land patterns are recorded in [design/plan-c/packages.md](../design/plan-c/packages.md).
- Paste layer is 1:1 with the land; leave stencil compensation to the assembler [HHG p96, p113].
- Silkscreen: draw the body outline at real size, mark polarity and pin 1, keep ink off pads, use ≥0.25 mm (10 mil) line width, and print only designators [BAC p13; KHA p149].

## 3. Layout setup

- Board setup: units, stackup, design rules and net classes come from the fab's capability [KLAP contents p7–8; HHG p63–65].
- Put aggressor nets (clocks, switching lines) in a net class with wider spacing [HHG p64].
- Draw the board outline, mounting holes and keep-outs first [KHA p252; HHG p36].
- Size vias for the fab's aspect ratio and annular ring. Worked example: 0.010" hole + 0.003" tolerance + 0.002" plating + 0.002" position = 0.017" + 0.003" ring → 0.020" pad. Go larger if space allows [HHG p65–67].

## 4. Placement (the most important step [BAC p8; HHG p36])

1. Import the parts and group them by function off the board, with the shortest pin-to-pin distances; cross-probing helps [HHG p37, p46].
2. Place fixed mechanical parts first (connectors, switches, LEDs, holes) and lock them [HHG p46; KHA p127, p147; KLAP p100].
3. Place critical parts next, so critical nets stay shortest; then the rest in signal-flow order [KHA p127, p253].
4. Move the groups onto the board. Large parts before small ones; give like parts the same rotation and align polarized parts [KHA p127, p148; HHG p46].
5. Decoupling caps go at the power pins, and the supply routes to the cap first, then the pin [BAC p21–22; HHG p40].
6. Crystals go close to their IC, and HF circuits get ground around them [HHG p40; KHA p191].
7. Keep analog away from digital, and HF/high-current circuits away from sensitive ones [BAC p10; HHG p40; KHA p161]. For grounding, see conflict C1.
8. Keep the HF amplifier input away from its output (oscillation) [KHA p160].
9. Keep parts on one side unless they won't fit; a second side adds a full assembly pass [HHG p38–39].
10. Check courtyards and mechanical fit, and plan test points now rather than after routing [HHG p39, p48].

## 5. Routing

Order: fanout (power and ground first, then lock) → power → critical nets → everything else; lock the critical nets [HHG p74–78; BAC p9; KHA p253].

General:
- Keep nets short [BAC p11; KHA p131, p156].
- Use 45° corners, never acute angles; KHA allows nothing under 60° [BAC p11; KHA p130–131, p200].
- End traces at pad centres [BAC p11].
- Space traces evenly through gaps and avoid bunching [KHA p131, p200–201].
- On two layers, run one side mostly at 90° to the other [BAC p13; KHA p131, p199].
- Review net lengths and remove detours [HHG p77].

Width:
- Set width from current first (IPC-2221 charts), then impedance, then the fab limit; use the widest practical width.
- Copper temperature rise: 10 °C is conservative, ≤20 °C is safe [BAC p4–5; HHG p75, p78].
- KHA values for 35 µm copper at 10 °C rise: 0.5 A → 0.15 mm, 1 A → 0.40 mm, 2 A → 0.80 mm [KHA p184].
- Ground ≥ supply ≥ signal in width [KHA p132, p201].

Power:
- Run power and ground close together, as a low-area loop; don't daisy-chain power from part to part [BAC p11; KHA p148, p170].

Return paths and planes:
- The AC return current flows in the plane directly under its trace, so keep the plane solid there [HHG p69, p76; KHA p134, p173–174].
- Never route a signal over a gap in its reference plane [BAC p11, p22; HHG p69, p76; KHA p203].
- Keep loop areas small. On a two-layer board, loop area needs particular care [KHA p190–191].
- Avoid layer changes on critical nets; each via is a discontinuity [BAC p22; HHG p78; KHA p174, p203].

Crosstalk:
- Coupling scales with 1/(1+(D/H)²), so wider spacing D or a closer plane H both reduce it [KHA p167–168].
- A ground trace between two signals also reduces it [KHA p125].
- Avoid parallel runs on adjacent layers [HHG p76].

RF and transmission lines:
- A trace behaves as a transmission line once its length passes about 1/7 of the wavelength, or its two-way delay exceeds the signal's rise time. FR4 delay is about 5–10 ns/m [KHA p164, p170, p190].
- RF counts as "high frequency" above ~100 MHz analog [KHA p169, p237].
- Microstrip: impedance rises with dielectric height and falls with width and √εr; keep the ground under the trace at least 10× the trace width; mitre bends at 45° [KHA p173–174, p178].
- Get close with an impedance calculator, then let the fab tune width and dielectric, never copper thickness [HHG p59–62, p72].
- Stitching vias along RF traces reduce radiation [BAC p22].
- A coax connector is better entering through the ground plane than at the board edge [KHA p178].

Thermal and soldering:
- Use thermal reliefs on plane-connected pads [BAC p25; KHA p204].
- Split heavy copper so small pads still solder [HHG p75].

## 6. Planes and copper fills

- Ground matters more than power; use as much ground copper as practical [BAC p20; KHA p168].
- Pour after routing. Remove dead (unconnected) copper [BAC p6, p11].
- Pull plane copper back 0.5–1.0 mm (20–40 mil) from the board edge [BAC p20]; see C3.
- Balance copper between the two sides to limit warp [HHG p61–62; KHA p135, p419].

## 7. Checks and clean-up

- Run DRC against the fab's rules, and compare the board's nets with the schematic's [BAC p17; KHA p236–238, p253].
- Check mounting-hole keep-outs, keep the number of hole sizes small, make sure via pads meet the annular ring, and check part-to-part clearance [BAC p12; KHA p151].
- Keep copper ≥0.5 mm from the board edge for depaneling [HHG p105, p113]; see C3.

## 8. Outputs

- Fab package:
  - Gerber RS-274X or X2, and an Excellon drill file with finished hole sizes
  - An IPC-D-356 netlist, plus IPC-2581 or ODB++
  - A fab drawing: stackup, IPC-6012/IPC-A-600 Class 2, FR4 per IPC-4101, thickness ±10%, UL94V-0, solder mask per IPC-SM-840
  - File names that include the part number and revision [HHG p79–93].
- Assembly package:
  - The BOM, including the bare PCB and hardware
  - A pick-and-place file (refdes, side, X, Y, rotation)
  - The paste layer, at 1:1
  - The test-point file
  - An assembly drawing per IPC-A-610 Class 2 and J-STD-001 [HHG p94–113].
- Inspect the Gerbers in a Gerber viewer before ordering [KLAP p68–69].

## Conflicts between sources

| # | Topic | Position A | Position B | Status |
|---|---|---|---|---|
| C1 | Analog/digital grounding | Separate analog and digital grounds, tied at one point [BAC p10, p20; HHG p69; KHA p132, p161–162, p168] | Keep one solid return plane under every signal and never route across a split [BAC p11, p22; HHG p69, p76; KHA p173–174, p203] | **Open.** The two can be reconciled (split only where no signal crosses), but none of these books says so outright. This repo already decided to keep the ground unbroken under the RF section. A primary grounding reference is needed before Plan C layout. |
| C2 | Teardrops | Not needed; no reliability gain [BAC p12] | Tear-drop pads at trace junctions [KHA p203] | Low impact. Follow the fab's preference. |
| C3 | Copper-to-edge clearance | ≥0.51 mm [HHG p105, p113]; plane pullback 0.5–1.0 mm [BAC p20] | 2–5 mm safety strip, parts ≥2 mm from edge [KHA p113, p253]; traces ≥2.5 mm [KHA p210] | KHA's figures date from sheared boards. Use the fab's routed-edge rule and keep ≥0.5 mm as a floor. |
| C4 | Fiducials | 1.5 mm pad, 3 mm mask clearance [BAC p24] | 1.0 mm pad, ~0.5 mm mask clearance [HHG p44]; 5 mm from corners [KHA p253] | Ask the assembler. |
| C5 | Corner shape | 45° mitres; round corners only for RF, HV or length matching [BAC p11] | Arcs for analog boards [KHA p200] | Either is acceptable. Use 45° mitres; KHA's own RF microstrip guidance is also 45° (p178). |
| C6 | Annular ring | 0.003" (0.076 mm) minimum ring in the via example [HHG p67] | 0.3–0.6 mm (≥0.5 mm PTH) [KHA p208–209]; also cites a 5 mil standard (p209) | KHA's large rings are for through-hole pads. Use the fab's via rule. |
| C7 | Placement grid | A small grid with snap-to-centre; no fab reason for grids [BAC p7–8] | Components on a 2.5 mm grid [KHA p127] | KHA reflects manual artwork. Use a fine grid for SMT; the 50 mil grid still applies to schematics [EES p10]. |
| C8 | Layer-count cost | 4 layers ≈ 2× the cost of 2 [HHG p57] | 4 → 8 layers ≈ +30% [KHA p118] | Different comparisons, not a real conflict. Get a quote from the fab. |

## Gaps (nothing in hand covers these)

- IPC-2221 and IPC-7351 themselves: every source cites them, but none reproduces their tables.
- RF layout practice for a sub-GHz 2-layer board beyond KHA §4.5 (microstrip on 1.6 mm FR4, RF switch and SMA launch).
- A primary reference on mixed-signal grounding, needed to settle C1.
- The design-principles and workflow chapters of *KiCad Like a Pro*, which are missing from the companion edition.
