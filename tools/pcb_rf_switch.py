"""Step 4.9: places U5 (RF switch), the transmit low-pass filter FL1 and the parts at U5's pins, live in the board open in
KiCad (one undo step). U5's pins run receive (1), transmit (3), antenna (5) round the chip, so with the antenna to the
right (J2), the transmit line comes down the left and the receive line leaves upward to U4 above (the user's choice,
2026-10-23: no RF lines cross). The filter is an L just west of U5, its two inductors at 90 degrees (AN4169 p11-12):
C28 shunt -> L2 (vertical) -> C29 shunt -> L3 (horizontal) -> C30 shunt -> U5 pin 3. Every courtyard keeps the 0.35 mm
gap pcb_local.py uses. Positions are worked out from the courtyards below, not read off a drawing.
Usage (from the repository root, board open in KiCad): python tools/pcb_rf_switch.py [--dry-run]"""
import sys

GAP = 0.35
U5 = (47.0, 125.0)  # the sketch's place; SOT-363 courtyard +-1.45 x +-1.1
PIN3_Y = U5[1] + 0.65  # transmit pin, left side, lower
L06_HX, L06_HY = 1.48, 0.73  # 0603 inductor courtyard half sizes (lying along x)
C04_HX, C04_HY = 0.91, 0.46  # 0402 capacitor
R04_HX, R04_HY = 0.93, 0.47
L06_PAD = 0.7875  # 0603 pad centre from the part centre

u5_left, u5_top, u5_bot, u5_right = U5[0] - 1.45, U5[1] - 1.1, U5[1] + 1.1, U5[0] + 1.45
l3 = (u5_left - GAP - L06_HX, PIN3_Y)                       # L3 lying along the line into pin 3
node2_x, node3_x = l3[0] - L06_PAD, l3[0] + L06_PAD         # its pads: filter middle (left) and TX_RF (right)
below = l3[1] + L06_HY + GAP + C04_HX                       # shunt capacitors standing below L3, centres
l2 = (node2_x, l3[1] - L06_HY - GAP - L06_HX)               # L2 standing above L3's left pad: 90 deg to L3
node1_y = l2[1] - L06_PAD                                   # its top pad: the filter input
c28 = (node2_x + L06_HY + GAP + C04_HX, node1_y)            # input shunt, lying to the right of L2's top pad
c34 = (c28[0] + C04_HX + GAP + C04_HY, u5_top - GAP - C04_HX)  # RX DC block standing above U5 pin 1, clear of C28
r16 = (c34[0] + C04_HY + GAP + R04_HY, c34[1])              # U5 VDD resistor standing above pin 6
d5 = (U5[0] + 1.45 + GAP + 0.6 + 0.05, U5[1] + 0.6)         # antenna ESD, standing just below the antenna line
c31 = (U5[0] + 0.84, u5_bot + GAP + C04_HX)                 # CTRL filter standing below pin 4
r17 = (c31[0] - C04_HY - GAP - R04_HY, c31[1])              # CTRL series resistor beside it

# ref: (x, y, turn) — turns put each part's pad on the line's net toward the line (KiCad turns counter-clockwise)
PLACE = {
    "U5": (U5[0], U5[1], 0),     # antenna pin 5 faces J2 on the right
    "L3": (l3[0], l3[1], 0),     # pad 1 (filter middle) left, pad 2 (TX_RF) right toward pin 3
    "C30": (node3_x, below, -90),  # pad 1 (TX_RF) up, ground pad down
    "C29": (node2_x, below, -90),  # pad 1 (filter middle) up
    "L2": (l2[0], l2[1], -90),   # pad 1 (from U7) up, pad 2 (filter middle) down
    "C28": (c28[0], c28[1], 0),  # pad 1 (from U7) left, toward L2's top pad
    "C34": (c34[0], c34[1], 90),  # pad 1 (RX_RF) down, toward pin 1; the receive line leaves upward
    "R16": (r16[0], r16[1], -90),  # pad 2 (U5_VDD) down, toward pin 6
    "D5": (d5[0], d5[1], -90),   # pad 1 (ANT) up, under the antenna line
    "C31": (c31[0], c31[1], -90),  # pad 1 (RF_CTRL) up, toward pin 4
    "R17": (r17[0], r17[1], 90),  # pad 2 (RF_CTRL) up
}


def main():
    for ref, (x, y, a) in PLACE.items():
        print(f"{ref:4} ({x:7.3f}, {y:7.3f}) {a:4} deg")
    if "--dry-run" in sys.argv:
        return
    from kipy import KiCad
    from kipy.geometry import Vector2, Angle
    board = KiCad().get_board()
    fps = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
    items = []
    for ref, (x, y, a) in PLACE.items():
        fps[ref].position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
        fps[ref].orientation = Angle.from_degrees(a)
        items.append(fps[ref])
    c = board.begin_commit()
    board.update_items(items)
    board.push_commit(c, "Step 4.9: U5, the TX filter and U5's parts")
    print(f"{len(items)} parts placed")


if __name__ == "__main__":
    main()
