# Analog FM placement rules

The checklist for placing the analog-FM parts on the board envelope in [layout.html](layout.html), and for checking the placement afterwards. It carries over [Plan C's rules](../archive/plan-c/placement-rules.md) and the user's feedback on the Plan C layouts. Rules that changed with the new parts are marked **New** or **Changed**.

Board orientation: looking at the back of the phone, camera at top left. The **top side** of the board faces away from the phone; the **bottom side** faces the phone and the MagSafe ring. The envelope (x 12.70–59.15, y 59.56–130.96) and the antenna placement are fixed (user, 2026-10-21).

## User feedback carried over from Plan C (2026-10-20)

- The MCU right at the top of the board looks wrong (Plan C layout B, rejected). The U parts sit more or less near the middle, set by the schematic.
- The top of the envelope was too sparse. Spread the non-tactile parts out so there is room for traces and interconnects.
- J1 exactly on the envelope's midline, on the bottom edge.
- J2 on a side edge opposite the user controls, as low as the board allows; the antenna turns up along the phone's edge.
- Edge controls come out of the board's edges, not its top face (right-angle parts).

## User feedback on the first analog-FM layouts (2026-10-21)

- Layout 1 (wheels down the side) over layout 2.
- Wheels as far out over the edge as they go, so they have room to spin, and lower on the board: the top wheel was at the very top. SW1 moves down to make room.
- D1 to the top right, out of the control area.
- SW3 on the top edge on the midline, parallel to J1, levers facing out through the top edge (towards the user, not into the board).

## Mechanical and user access

| # | Rule | Source | Check |
|---|---|---|---|
| M1 | J1 (USB-C) on the bottom edge, exactly on the midline, front flush with the board edge | User; HRO TYPE-C-31-M-12 drawing (PCB edge line) | 0.00 mm off the midline |
| M2 | J2 (SMA) on the side edge opposite the user controls, as low as it goes, barrel out sideways. Unchanged from Plan C | User (2026-10-20, 2026-10-21) | J2's footprint ends 0.5 mm above the bottom edge |
| M3 | **Changed.** The user controls are SW1 (TX/RX slider) and RV1–RV3 (the three tuning wheels), on the left edge. The wheels stand 1.9 mm of rim past the edge, knob centres 5.1 mm in, so each frame's rim-side locating peg stays on the board (step 4.5, the user's choice; 2.9 mm before), with room between them to spin; they don't share an edge with J2. The tune-up and tune-down buttons are gone: the wheels replaced them | User (wheels chosen 2026-10-20; right-angle controls 2026-10-21) | Each control's edge line on a board edge |
| M4 | **New.** SW3 (power DIP) is a bench setting: on the top edge on the midline, parallel to J1, levers facing out of the board. Its six lines to U7 carry static DC levels, so their length doesn't matter | User (2026-10-21); netlist ATT_C16…C0_5 | SW3 on the top edge, levers outward |
| M5 | **Changed.** SW2 is now only the BOOT button, pressed while plugging in. It sits on the bottom edge next to J1, so one hand can hold it while the cable goes in | DS14217 p29 · AN2606 p30 (BOOT0 sampled at reset) | SW2 on the bottom edge |
| M6 | D1 is top-emitting (0.6 mm tall, XL-1615RGBC-RF p8): top right of the board, under a light pipe in the enclosure's top face | User (2026-10-21); XL-1615RGBC-RF p8 | D1 at the top right |
| M7 | All parts on the top side; the bottom faces the phone and the magnet ring | HHG p38–39; ADG R31 p279 | Nothing on the bottom |
| M8 | Through-hole leads stay off the magnet ring (Ø46.0–54.1). Only J2 has them now: 3.5 mm legs, about 1.9 mm out of the bottom of a 1.6 mm board. SW1's two locating posts don't go through | BWSMA-KWE-Z001 p6; MSK12C02 p1; ADG R31 p278–279 | No through-hole leads over the ring |
| M9 | Tallest top-side parts set the enclosure height: J2 9.5 mm (axis 6.4), SW3 4.1, J1 3.26, RV1–RV3 2.5, SW1 about 1.4 | BWSMA p6; TDP p3; HRO p1; RK10J p2; MSK12C02 p1 | Heights noted for the enclosure |
| M10 | Copper at least 0.5 mm from the board edge; the edge parts' actuators and barrels may overhang | Workflow C3; HHG p105, p113 | Edge lines in the tray |
| M11 | Courtyards clear of each other; main ICs (U1, U2, U4) at least 8 mm apart edge to edge, everything else at least 2 mm, and use the whole board | User (2026-10-20); HHG p37, p39 | Edge-to-edge gaps |

## Placement of the main parts

| # | Rule | Source | Check |
|---|---|---|---|
| P1 | U1 central; the transmit chain (Y2, U2, U7, FL1) and receive (U4) between U1 and J2; U3 and U6 by J1 | User; BAC p11 | Room for local parts around each IC |
| P2 | U1's USB pins (32–33) face J1; D+/D− short and side by side through U6 | BAC p11 | Short, parallel USB pair |
| P3 | U3 near J1's VBUS; 3V3 fanned out to each load, not daisy-chained | BAC p11; KHA p148, p170 | U3 between J1 and the loads |
| P4 | ESD parts at their connectors: U6, D3, D4 at J1; D5 at J2 | Netlist | At the connector pins |
| P5 | **New.** Y2 between U1 and U2: it drives U1 PH0 (through 33 Ω) and U2 OSCin directly | Netlist REF20 | Y2 near both |
| P6 | Like parts in the same orientation | KHA p127, p148 | By eye |

## RF section (U2 synthesizer, U7 attenuator, FL1, U5 switch, U4 receiver, J2)

| # | Rule | Source | Check |
|---|---|---|---|
| R1 | U5 next to J2; ANT short, 50 Ω grounded coplanar | AN4169 p6, p11 | U5 within a few mm of J2 |
| R2 | U4 close to U5 RF1; FB1 and C14 at FMI | AN383 p15, p17, p52 | Short RX_RF |
| R3 | **Changed.** U2 → U7 → FL1 → U5 in a short line, U2's RF output away from its digital inputs. Since step 4.9 (the user's choice) the transmit line runs down the left of the RF section into U5 pin 3, with FL1 an L just west of U5, and U4 sits right of it above U5, so no RF lines cross (U5's pins run receive, transmit, antenna round the chip) | AN4169 p11; KHA p160 | Short TX path |
| R4 | Transmit (U2, U7, FL1) and receive (U4) apart, with top-layer ground between | AN4169 p11 | U2 to U4 at least 10 mm |
| R5 | FL1's two inductors at 90° to each other | AN4169 p9, p11–12 | Inductor orientations |
| R6 | Solid ground under the RF parts; U2's DAP and U7's pad stitched to it | AN4169 p12; LMX2571 p53 | No digital nets through the RF area |
| R7 | **Changed.** U1, its clock and the I²S/SPI lines kept off U4's input; the continuous I²S stream to U2 runs short (33 Ω at U1) | AN383 p15–16; netlist FSK_* | U1 outside the RF area |

| R8 | **New.** Keep the I²S clock (FSK_CLK, R6 to U2 pin 4) and every other switching line away from U2's loop filter (C24, R5, C25 at pin 25) and from OSCin (pin 34). Consider a separate OSCin ground return to cut crosstalk spurs. TI's layout example is on p56 | LMX2571 p55 (Layout Guidelines), p56 (Figure 87) | Loop filter and OSCin clear of switching traces |

## Clocks and decoupling

| # | Rule | Source | Check |
|---|---|---|---|
| C1 | Every bypass cap at its power pin, its own ground via; U2's seven 100 nF and its 2.2 µF VregVCO at the pins | BAC p21–22; AN4169 p7; LMX2571 p54 | Each cap beside its pin |
| C2 | U2's loop filter (C1, R2, C2) right at CPout, pin 25 | LMX2571 p53 | Short loop node |

## Test and assembly

| # | Rule | Source | Check |
|---|---|---|---|
| T1 | TP1–TP5 on the top side, reachable with a probe | HHG p39, p48; bom.md chain 10 | Clear of tall parts |
| T2 | Fiducials and mounting holes as JLC and the enclosure need. Mounting holes (user, 2026-10-23): four M2, 2.2 mm unplated, at H1 (13, 7), H2 (33, 7), H3 (41, 57), H4 (8, 66) mm from the board's top-left corner, whole-millimetre offsets for the enclosure model | Workflow C4; kicad-build-procedure 3.5 | Asked of the assembler; holes as placed |
