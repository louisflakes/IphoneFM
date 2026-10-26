"""Phase 5, floorplan B3: the north band and the east edge, planned as copper (tools/pcb_plan.py) and checked before it
is laid: D1 and its resistors, SW3's 3V3 row, the test pads TP2 and TP3, and the 3V3 trunk on the bottom.
  LEDs   LED_B, LED_G, LED_R carry on north from U1 (tools/pcb_route_u1.py stops them at y 78) with VBUS beside them
         (up from the west strip's via), turn east above SW3's 3V3 row, hop under the attenuator lanes on the bottom
         and come up south of D1 in the order VBUS, B, G, R. VBUS and B go straight up into D1's south pads through
         R27; G runs up its own lane through R26 and into D1's north-east pad from the east; R runs up the edge lane
         through R25 and round the north of D1 into its north-west pad.
  3V3    from the via at FB2/C3 (U1's north group) down on the bottom: west to SW3's 3V3 row and TP2 by a via, east
         under the band to U4's supply via and R20's, then down the east edge outside the RF zones and up before
         J2's ground legs, west on top to R16.
  TP3    ground test pad west of the band, with its via.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_north.py place | lay [--dry-run]"""
import sys

sys.path.insert(0, "tools")
from pcb_plan import B, Plan, main

P = Plan()
W = 0.2

P.place.update({
    "R27": (56.625, 65.4, 90),     # B: straight under D1's B pad
    "R25": (58.275, 65.4, 90),       # R: in the edge lane
    "R26": (57.45, 67.6, 90),        # G: in its lane, staggered below R27 and R25
    "TP2": (28.8, 69.3, 0),        # 3V3 test pad at the west end of SW3's 3V3 row
    "TP3": (30.6, 71.9, 0),        # ground test pad
})

# ---- LEDs and VBUS: north from U1, east above SW3's 3V3 row, staircase down at the west of the attenuator lanes
ROWS = [("VBUS", 32.3, 69.9, 0.4, 45.0, 55.375), ("/LED_B", 33.385, 70.6, W, 45.55, 56.625),
        ("/LED_G", 33.885, 71.2, W, 46.1, 57.45), ("/LED_R", 34.385, 71.8, W, 46.65, 58.275)]
for net, x, y, w, xw, xe in ROWS:
    y0 = 77.6 if net == "VBUS" else 78.0
    P.run(net, [(x, y0), (x, y + 0.4), (x + 0.4, y), (xw, y)], w)
    P.via(net, xw, y)
    P.run(net, [(xw, y), (xe, y)], w, B)
    P.via(net, xe, y)
# up to D1
P.run("VBUS", [(55.375, 69.9), (55.375, 63.475)], 0.4)                                     # D1.2
P.run("/LED_B", [(56.625, 70.6), (56.625, 65.91)])                                          # R27.1
P.run("/LED_B_K", [(56.625, 64.89), (56.625, 63.475)])                                      # R27.2 -> D1.4
P.run("/LED_G", [(57.45, 71.2), (57.45, 68.11)])                                              # R26.1
P.run("/LED_G_K", [(57.45, 67.09), (57.45, 62.925), (57.05, 62.525), (56.625, 62.525)])       # R26.2 -> D1.3
P.run("/LED_R", [(58.275, 71.8), (58.275, 65.91)])                                              # R25.1
P.run("/LED_R_K", [(58.275, 64.89), (58.275, 62.0), (57.875, 61.6), (55.775, 61.6), (55.375, 62.0),
                   (55.375, 62.525)])                                                       # R25.2 -> D1.1

# ---- 3V3 on the bottom from FB2/C3's via
P.run("3V3", [(36.1, 78.6), (36.1, 74.15), (35.7, 73.75), (30.0, 73.75), (29.6, 73.35), (29.6, 69.3)], 0.4, B)
P.via("3V3", 29.6, 69.3)
P.run("3V3", [(28.8, 69.3), (38.7, 69.3), (39.1, 68.9), (39.1, 68.32)], 0.25)              # TP2, SW3.7-12
for k in range(5):
    x = 32.75 + 1.27 * k
    P.run("3V3", [(x, 69.3), (x, 68.32)], 0.25)
P.run("3V3", [(36.1, 74.15), (36.5, 73.75), (57.85, 73.75), (58.02, 73.92), (58.02, 75.6)], 0.4, B)  # R20's via
P.run("3V3", [(55.0, 73.75), (55.0, 78.78), (55.42, 79.2)], 0.4, B)                          # U4's supply via
P.run("3V3", [(58.02, 75.6), (58.3, 75.88), (58.3, 120.8)], 0.4, B)                          # the east edge
P.via("3V3", 58.3, 120.8)
P.run("3V3", [(58.3, 120.8), (51.2, 120.8), (50.8, 121.2), (50.8, 125.9), (50.15, 126.55), (50.01, 126.55)], 0.4)

# ---- GND: TP3, the resistors and D1 have no ground pads; TP3 gets its via
P.via("GND", 30.6, 70.4)
P.run("GND", [(30.6, 71.9), (30.6, 70.4)])


def plan(copper=None):
    return P.copper()


if __name__ == "__main__":
    main(P, "Phase 5: north band and east edge")
