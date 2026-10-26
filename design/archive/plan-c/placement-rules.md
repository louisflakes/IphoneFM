# Plan C placement rules

A checklist for placing parts on the board envelope in [layout.html](layout.html), and for checking the placement afterwards.
Each rule names where it comes from: **User** (set in conversation, 2026-10-20), a datasheet or app note, or the [PCB design workflow](../../../docs/pcb-design-workflow.md) book tags (BAC, HHG, KHA).

Board orientation: looking at the back of the phone, camera at top left. The **top side** of the board faces away from the phone; the **bottom side** faces the phone and the MagSafe ring.

## Order of work

| # | Rule | Source |
|---|---|---|
| O1 | Place and lock the fixed mechanical parts first: J1, J2, SW1, SW2, SW3, D1. Then the critical parts, then the rest in signal-flow order | HHG p46; KHA p127, p147, p253 |
| O2 | Group parts by function off the board first, with the shortest pin-to-pin distances, then move the groups onto the board | HHG p37, p46 |

## Mechanical and user access

| # | Rule | Source | Check |
|---|---|---|---|
| M1 | J1 (USB-C) on the bottom edge, exactly on the envelope's midline, mouth facing the phone's bottom, front face flush with the board edge | User; GCT drawing, KiCad footprint (PCB edge at the body front) | J1 edge line on the bottom edge; 0.00 mm off the midline |
| M2 | J2 (SMA) on the side edge opposite the controls, as low on the board as it goes, barrel pointing out sideways; a tilt-swivel antenna then turns upwards along the phone's edge | User (2026-10-20) | J2 on the other side edge from SW1–SW3; footprint at the bottom edge |
| M3 | SW1, SW2 and SW3 all exit the same side edge, actuators out past it, reachable through the enclosure | User (2026-10-20); SW1 p2 | All three edge lines on one side edge |
| M4 | SW2 and SW3 are right-angle (side-push) buttons, tune up above tune down (towards the camera end), same orientation | User (2026-10-20); KHA p127 | Same rotation; SW2 above SW3 |
| M5 | D1 in the control strip on the controls' edge, so its light pipe exits with the controls and reads as the TX/RX mode indicator | User (status LED; placed with intent, 2026-10-20) | D1 between the buttons and the slider, at the edge |
| M6 | All parts on the top side; the bottom side faces the phone and the magnet ring | HHG p38–39; ADG R31 p279 (ring stack) | Nothing placed on the bottom |
| M7 | Through-hole leads stick out of the bottom side toward the phone: J2 about 2.3 mm (3.90 legs) and SW1 about 0.6 mm (my arithmetic on a 1.6 mm board). SW2/SW3 are SMD and have none. The board's bottom sits about 2.70 mm off the phone where the ring stack is (0.85 wall + 1.10 magnet + 0.05 + 0.70 shield). Keep these parts off the ring annulus (Ø46.0–54.1); along a side edge that means below about y 100 | J2 drawing; SW1 p2; ADG R31 p278–279 | No through-hole part over the ring annulus, or a lead-trim note |
| M8 | Tallest top-side parts set the enclosure height: J2 10.0 mm, SW1 6.3 mm body (actuator centre 3.7), SW2/SW3 1.35 mm | J2 drawing (13.90 − 3.90); SW1 p2; Panasonic ANCTB21E p2 | Heights noted for the enclosure |
| M9 | Copper at least 0.5 mm from the board edge (fab rule wins); edge-mounted J1, J2, SW1 excepted | Workflow C3; HHG p105, p113 | DRC edge clearance |
| M10 | Keep part courtyards clear of each other; check mechanical fit before routing | HHG p39 | No courtyard overlaps |
| M11 | Leave routing room: the main ICs (U1, U2, U4) at least 8 mm apart edge to edge, every other part at least 2 mm from its neighbours, so the passives and traces fit. Crystals and ESD parts stay close to their pins but with room for their load caps and traces. Use the whole board rather than clustering | User (2026-10-20); HHG p37 (room per functional group). The 8 mm and 2 mm figures are my working numbers | Edge-to-edge gaps between footprints |

## Placement of the main parts

| # | Rule | Source | Check |
|---|---|---|---|
| P1 | U parts more or less near the middle of the envelope, their exact spots set by the schematic: U1 central; the RF parts between J2 and the middle (R1–R4); U3 and U6 by J1 | User (2026-10-20); BAC p11 (keep nets short) | Each IC has room for its local parts around it |
| P2 | U1's USB pins (PA11/PA12, pins 32–33) face J1; D+/D− run short and side by side from J1 through U6 to U1 | BAC p11; netlist USB_DP/USB_DM | Short, parallel USB pair |
| P3 | U3 (regulator) near J1's VBUS entry; 3V3 distributed from U3 to each load, not daisy-chained | BAC p11; KHA p148, p170 | U3 between J1 and the loads |
| P4 | ESD parts at their connectors: U6, D3 and D4 at J1; D5 at J2 | Netlist (USB_DP, USB_DM, CC1, CC2, ANT: "at J1", "at J2") | Each ESD part next to its connector pins |
| P5 | Like parts in the same orientation, polarized parts aligned | KHA p127, p148; HHG p46 | Visual check |

## RF section (U2 transmitter, U4 receiver, U5 switch, J2)

| # | Rule | Source | Check |
|---|---|---|---|
| R1 | U5 next to J2: the ANT trace is short, 50 Ω grounded coplanar | AN4169 p6, p11; netlist ANT | U5 within a few mm of J2's centre pin |
| R2 | U4 close to U5 RF1: a short FMI path (each inch of trace adds about 3–4 pF); FB1, C14 and C5 as close to FMI as possible | AN383 p15, p17, p52 | Short RX_RF path |
| R3 | U2's RF output to FL1 to U5 RF2 short; U2's RF output kept away from its inputs | AN4169 p11; KHA p160 | Short TX_RF path |
| R4 | TX and RX sections apart, separated by top-layer ground | AN4169 p11 | Ground strip between the U2 and U4 areas |
| R5 | FL1's two inductors and U2's coils (#5, #6) at 90° to each other, never side by side in parallel | AN4169 p9, p11–12 | Inductor orientations |
| R6 | Solid ground under the RF parts; keep other routing out of the RF area | AN4169 p12; AN383 p15–16; ADI "Ground Planes" | No digital nets through the RF area |
| R7 | Digital parts and lines (U1, its 152 MHz clock, SAI, I²C, RCLK, LED PWM) away from the RF section and from U4's VCO and audio pins | AN383 p15–16; BAC p10; HHG p40; KHA p161 | U1 outside the RF area |

## Clocks and decoupling

| # | Rule | Source | Check |
|---|---|---|---|
| C1 | Y1 next to U1 PC14/PC15 (pins 3–4) with its 5.6 pF caps beside it; Y2 next to U2 pin 16 with its 12 pF cap | HHG p40; KHA p191; AN4169 p12 | Crystals within a few mm of their pins |
| C2 | Every bypass cap at its power pin, supply routed to the cap first; U4 C1 close to VA, C4 close to VD; U1 VCAP 4.7 µF at pin 22 | BAC p21–22; HHG p40; Si4704 p17 notes; DS14217 p127 | Each cap beside its pin |
| C3 | Each decoupling cap gets its own ground via | AN4169 p7 | One via per cap |

## Test and assembly

| # | Rule | Source | Check |
|---|---|---|---|
| T1 | TP1–TP5 reachable with a probe when the board is out of the enclosure; plan them now, not after routing | HHG p39, p48; bom.md chain 13 | All five pads on the top side, clear of tall parts |
| T2 | Fiducials and mounting holes as the assembler and enclosure need | Workflow C4; user-owned enclosure | Asked of the assembler |

## Already decided

- The board envelope overlaps Apple's no-metal zones below y 105, by the user's instruction ([layout.html](layout.html) panel).
- Electrically the RF runs are short at 108 MHz, so a 2-layer 1.6 mm board stays (workflow conflict C9).

- SW2/SW3 are Panasonic EVQ-P7J01P side-push SMD buttons, replacing the top-actuated TS02 (2026-10-20). Their knobs reach 0.35 mm past the board edge, so the enclosure needs plungers to bridge the ½ in (12.7 mm) margin to its wall; SW1's actuator (4.05 mm past the edge) needs an extension too.
