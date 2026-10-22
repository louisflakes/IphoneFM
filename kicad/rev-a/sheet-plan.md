# Rev A schematic sheet plan (step 1.3)

One A2 sheet (594 × 420 mm), laid out left to right in signal flow, higher voltages toward the top [KHA p108; BAC p3]. Each bypass cap is drawn beside its chip [BAC p3]. Zones are joined by net labels using the netlist.json names, and power by power symbols [EES p31, p37–38]. Approved by the user 2026-10-21.

Coordinates are sheet millimetres from the top-left corner (x right, y down), inside KiCad's 10 mm frame.

| Zone | x (mm) | y (mm) | Parts |
|---|---|---|---|
| USB and power | 19–167 | 19–161 | J1, U6, D3, D4, R1, R2, U3, C1–C3 |
| Controls and LED | 19–167 | 170–401 | RV1–RV3, C39–C41, SW1, R18, SW2, R3, D1, R25–R27, TP1–TP8 |
| Clock | 158–288 | 19–90 | Y2, C11, C12, R4 |
| MCU | 158–288 | 99–401 | U1, C4–C10, FB2, R6–R8 (at U1 on the board) |
| Transmit | 297–431 | 19–214 | U2, C13–C26, R5, R9; U7, C27, SW3, R10–R15 |
| Receive | 297–431 | 223–401 | U4, FB3, C32, C33, R19–R24, C36–C38 |
| RF out | 441–575 | 19–214 | FL1 (C28–C30, L2, L3), U5, R16, R17, C31, J2, D5 |
| RX front end | 441–575 | 223–312 | C34, L1, FB1, C35 (drawn right to left, from U5 back to U4) |
| Title block | 441–575 | 321–401 | KiCad frame |

Notes:
- R3 (BOOT0 pull-down) sits with SW2 in Controls, at the U1 end of the BOOT0 label.
- R18 (RF_MODE pull-down) sits with SW1; R17 and C31 sit at U5's CTRL pin in RF out.
