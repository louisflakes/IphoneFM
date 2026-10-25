"""Phase 5, floorplan B3: the J1 corner and the west strip, planned as copper (tools/pcb_plan.py) and checked before
it is laid.
  USB    D- and D+ pass straight through U6 (pads 3-4 and 1-6 tied under its body) and on down to J1's B7 and B6.
         J1 has the pair twice, interleaved B7 A6 A7 B6, so A7 loops back to D- round A6, and A6 comes up from a via
         fed on the bottom from D+.
  CC     CC1 leaves its lane east to D3 and R1 and drops at 45 degrees into A5. CC2 leaves its lane east, hops under
         U6 on the bottom and runs straight down past D4 and R2 into B5.
  VBUS   J1's west pad feeds C1, U3 and (by a via) the west strip; the east pad and U6.5 join it on the bottom, with
         TP1 on that bottom line.
  RF_MODE west under RV3 to TP4, R18 and SW1; east by a via under J1 on the bottom, up beside the filter and along
         the board's bottom edge to R17.
  3V3    U3's output to C2, up to RV3.1 and by a via on the bottom to the U1 trunk; SW1 and SW2 from a via at U3 on the
         bottom; RV2.1 and RV1.1 by vias from the U1 bottom lines.
  west strip (bottom, west to east): VBUS up to a via north of the pots for the LED lane, BOOT0 from U1's bottom line
         down to SW2 and R3.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_j1.py place | lay [--dry-run]"""
import sys

sys.path.insert(0, "tools")
from pcb_plan import B, Plan, main

P = Plan()
W = 0.2

P.place.update({
    "R1": (33.0, 121.09, 90),      # CC1 pull-down on the CC1 row, clear of U6
    "D3": (31.75, 121.25, 90),     # CC1 ESD on the row
    "R2": (38.185, 121.3, 0),      # CC2 pull-down with its pad 1 straight above B5
    "D4": (38.6, 119.9, 0),        # CC2 ESD beside the CC2 line
    "TP1": (29.95, 121.35, 180),   # VBUS test pad on the bottom VBUS line
    "C1": (28.45, 124.425, -90),   # U3 input, pad 1 on the VBUS line from J1
    "C2": (22.75, 121.575, -90),   # U3 output
    "R3": (29.15, 129.42, 90),     # BOOT0 pull-down level with SW2's BOOT0 pads
    "R18": (19.51, 129.6, 0),      # RF_MODE pull-down at the foot of the RF_MODE line, clear of H4
})

# ---- USB: through U6, then the A/B crossover at J1
P.run("/USB_DM", [(34.975, 117.062), (34.975, 122.32), (35.175, 122.52), (35.175, 124.1)])            # B7
P.run("/USB_DM", [(36.175, 124.1), (36.175, 122.45), (36.375, 122.25), (36.375, 121.35), (36.175, 121.15),
                  (34.975, 121.15)])                                                                    # A7
P.run("/USB_DP", [(36.875, 117.062), (36.875, 122.32), (36.675, 122.52), (36.675, 124.1)])            # B6
P.via("/USB_DP", 36.875, 120.75)
P.run("/USB_DP", [(36.875, 120.75), (35.675, 121.95)], W, B)
P.via("/USB_DP", 35.675, 121.95)
P.run("/USB_DP", [(35.675, 121.95), (35.675, 124.1)])                                                 # A6

# ---- CC
P.run("/CC1", [(29.15, 103.0), (29.15, 121.2), (29.55, 121.6), (33.075, 121.6), (34.675, 123.2), (34.675, 124.1)])
P.run("/CC2", [(29.6, 103.0), (29.6, 117.9), (30.0, 118.3), (33.4, 118.3)])
P.via("/CC2", 33.4, 118.3)
P.run("/CC2", [(33.4, 118.3), (37.675, 118.3)], W, B)
P.via("/CC2", 37.675, 118.3)
P.run("/CC2", [(37.675, 118.3), (37.675, 124.1)])                                                      # R2.1, B5
P.run("/CC2", [(37.675, 119.9), (38.25, 119.9)])                                                       # D4.1

# ---- VBUS
P.run("VBUS", [(33.525, 124.1), (33.525, 123.3), (33.125, 122.9), (29.2, 122.9), (28.45, 123.65),
               (27.5, 123.65), (26.71, 124.44), (26.55, 124.44)], 0.4)                                # C1, U3.3
P.run("VBUS", [(26.55, 124.44), (26.55, 123.7), (26.15, 123.3), (25.05, 123.3), (24.65, 123.7), (24.65, 124.44)], 0.3)
P.via("VBUS", 31.2, 122.9)
P.via("VBUS", 38.325, 122.95)
P.run("VBUS", [(38.325, 124.1), (38.325, 122.95)], 0.4)
P.via("VBUS", 35.925, 120.45)
P.run("VBUS", [(35.925, 119.338), (35.925, 120.45)], 0.3)                                             # U6.5
P.run("VBUS", [(38.325, 122.95), (38.325, 120.2), (37.925, 119.8), (36.575, 119.8), (35.925, 120.45),
               (32.1, 120.45), (31.2, 121.35), (31.2, 122.9)], 0.4, B)
P.run("VBUS", [(31.2, 121.35), (29.95, 121.35)], 0.4, B)                                               # TP1
# west strip: from a via north of U3 up the bottom to a via for the LED lane
P.via("VBUS", 25.6, 121.0)
P.run("VBUS", [(25.6, 121.0), (27.0, 121.0), (28.9, 122.9)], 0.4)
P.run("VBUS", [(25.6, 121.0), (25.6, 79.9), (27.9, 77.6), (32.3, 77.6)], 0.4, B)
P.via("VBUS", 32.3, 77.6)

# ---- RF_MODE: west to TP4, SW1 and R18; east under J1 to R17
P.run("/RF_MODE", [(28.7, 103.0), (28.7, 114.6), (28.3, 115.0), (19.4, 115.0), (19.0, 115.4), (19.0, 129.6)])
P.run("/RF_MODE", [(19.0, 125.85), (18.6, 126.25), (16.6, 126.25)])                                  # SW1.2
P.run("/RF_MODE", [(28.7, 114.6), (28.7, 119.0), (28.4, 119.3)])
P.via("/RF_MODE", 28.4, 119.3)
P.run("/RF_MODE", [(28.4, 119.3), (28.4, 126.4), (28.8, 126.8), (41.25, 126.8)], W, B)
P.via("/RF_MODE", 41.25, 126.8)
P.run("/RF_MODE", [(41.25, 126.8), (41.25, 129.5), (41.7, 129.95), (45.33, 129.95)])

# ---- 3V3
P.run("3V3", [(24.65, 122.162), (24.65, 118.45), (26.8, 116.3), (26.8, 116.0)], 0.3)                  # U3 to RV3.1
P.run("3V3", [(22.75, 120.8), (24.65, 120.8)], 0.3)                                                    # C2
P.via("3V3", 27.95, 116.2)
P.run("3V3", [(27.95, 116.2), (27.75, 116.0), (26.8, 116.0)], 0.3)
P.run("3V3", [(27.95, 116.2), (30.65, 116.2)], 0.3, B)                                                # to the trunk
P.via("3V3", 21.5, 123.25)
P.run("3V3", [(21.5, 123.25), (23.9, 123.25), (24.65, 122.5), (24.65, 122.162)], 0.3)
P.via("3V3", 17.9, 123.25)
P.run("3V3", [(17.9, 123.25), (16.6, 123.25)], 0.3)                                                    # SW1.1
P.run("3V3", [(17.9, 123.25), (22.1, 123.25), (22.5, 123.65), (22.5, 126.9), (22.9, 127.3), (23.7, 127.3)], 0.3, B)
P.via("3V3", 23.7, 127.3)
P.run("3V3", [(23.7, 127.3), (23.7, 128.49), (27.3, 128.49)], 0.3)                                    # SW2.1 pads
P.via("3V3", 27.0, 100.4)
P.run("3V3", [(27.0, 100.4), (26.8, 100.2), (26.8, 99.0)], 0.3)                                       # RV2.1
P.run("3V3", [(31.875, 95.2), (30.475, 95.2), (27.0, 98.675), (27.0, 100.4)], 0.3, B)
P.via("3V3", 27.0, 83.1)
P.run("3V3", [(27.0, 83.1), (26.8, 82.9), (26.8, 82.0)], 0.3)                                         # RV1.1
P.run("3V3", [(31.0, 86.2), (30.1, 86.2), (27.0, 83.1)], 0.4, B)
P.run("3V3", [(36.1, 78.6), (36.1, 86.2)], 0.3, B)                                                    # FB2/C3 via
# U1's north 3V3 (pins 1 and 48, VDDA's parts, RV1) joins the rest along the pots' 3V3 pads, under the pot bodies
P.run("3V3", [(26.8, 82.0), (25.8, 82.0), (25.4, 82.4), (25.4, 98.6), (25.8, 99.0), (26.8, 99.0)], 0.3)

# ---- BOOT0 down the west strip to SW2 and R3
P.run("/BOOT0", [(31.0, 87.0), (26.7, 87.0), (26.3, 87.4), (26.3, 126.6)], 0.3, B)
P.via("/BOOT0", 26.3, 126.6)
P.run("/BOOT0", [(26.3, 126.6), (28.0, 126.6), (28.4, 127.0), (28.4, 129.93)], 0.3)
P.run("/BOOT0", [(23.7, 129.93), (29.15, 129.93)], 0.3)                                               # SW2.2 pads, R3.1

# ---- GND
P.run("GND", [(32.725, 124.1), (31.6, 124.1)], 0.3)                                                   # J1 A1/B12 to shell
P.run("GND", [(39.125, 124.1), (40.25, 124.1)], 0.3)                                                  # J1 A12/B1 to shell
GV = [((32.4, 119.6), [[(33.0, 120.58), (33.0, 120.2), (32.4, 119.6)], [(31.75, 120.9), (31.75, 119.95), (32.1, 119.6), (32.4, 119.6)]]),
      ((39.45, 121.3), [[(38.695, 121.3), (39.45, 121.3)]]),                         # R2
      ((39.6, 119.9), [[(38.95, 119.9), (39.6, 119.9)]]),                            # D4
      ((25.6, 125.75), [[(25.6, 124.438), (25.6, 125.75)]]),                         # U3.2
      ((29.25, 125.2), [[(28.45, 125.2), (29.25, 125.2)]]),                          # C1
      ((21.9, 122.35), [[(22.75, 122.35), (21.9, 122.35)]]),                         # C2
      ((29.15, 128.1), [[(29.15, 128.91), (29.15, 128.1)]]),                         # R3
      ((20.8, 129.6), [[(20.02, 129.6), (20.8, 129.6)]]),                            # R18
      ((17.9, 127.75), [[(16.6, 127.75), (17.9, 127.75)]]),                          # SW1.3
      ((14.65, 121.825), [[(13.55, 121.825), (15.75, 121.825)]]),                    # SW1 shell
      ((14.65, 129.175), [[(13.55, 129.175), (15.75, 129.175)]])]
for (x, y), links in GV:
    P.via("GND", x, y)
    for link in links:
        P.run("GND", link)


def plan(copper=None):
    return P.copper()


if __name__ == "__main__":
    main(P, "Phase 5: J1 corner and west strip")
