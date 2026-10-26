"""Phase 5, floorplan B3: U2 (the synthesizer) on all four sides with its own parts, Y2's supply and the lines that
pass between U2 and U6, planned as copper (tools/pcb_plan.py) and checked before it is laid.
  west   pin 1 rises to C13 at U2's top-left corner, BYP1 and BYP2 fan up into C20 and C21 beside it, pin 9 straight
         into C14; the FSK lines come down from R6-R8 in two lanes west of the capacitors and turn into pins 4, 6 and 7.
         FSK_CLK starts west of FS and DATA but enters U2 above them, so it hops under both on the bottom and comes up
         beside C21. The 3V3 for pins 1 and 9 comes on the bottom from the U1 trunk's via, under the lanes.
  south  MICROWIRE turns east from its lanes and north into pins 10-13, 0.6 mm apart round its clock; MUX drops to TP5
         on the bottom. Pin 15 goes into C17 and out east of it, round C17's ground via, to a via clear of the RF zone,
         fed from the trunk on the bottom under U6.
  USB    D- and D+ run on the bottom from U1 down the gap between the 3V3 vias and U2's pads and come up north of U6, which
         sits 0.7 mm lower to make room; U6.2 has its ground via between them.
  east   the PLL capacitors stand in a column, each line leaving its pin east, rising at 45 degrees (outer lines first)
         and entering its capacitor: pin 27 to C16 and the north 3V3 line, CP_LOOP to C24 and on between C24 and C22
         to R5 (C25 below it), VREFVCO to C22, VREGVCO to C23, pin 20 to C15. CE runs east under the column and
         north up the lane beside R5 and R9. The column is closed in by CE, so the 3V3 at pin 20 drops to the bottom
         and runs under CE to C27 and U7's supply (bottom link 1); U7's LE pin is tied high by bottom link 2. Both are
         the user's exceptions to the RF zone (tools/pcb_freeroute.py RF_BOTTOM_ALLOW).
  north  REF20 from Y2 through R4 west and down into pin 34; pins 32 and 33 up into the 3V3 line from C18 and C19 to
         C16 and Y2; Y2 fed from C12 and C11.
  GND    U2's ground pins bridge into its exposed pad, which has a 3 x 3 via array; each capacitor has its own via.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_u2.py place | lay [--dry-run]"""
import sys

sys.path.insert(0, "tools")
from pcb_plan import B, Plan, main

P = Plan()
W = 0.2

P.place.update({
    "C13": (36.5, 104.4, 0),      # pin 1's 3V3 capacitor at U2's top-left corner, 3V3 pad west
    "C20": (34.95, 106.4, 180),   # BYP1, BYP2: up and right so pins 1-3 fan into them
    "C21": (34.95, 107.67, 180),
    "TP5": (32.7, 112.75, 180),   # MUX test pad on the bottom, beside its via
    "U6": (35.925, 118.2, -90),   # 0.7 mm lower: the USB pair comes up north of it, under MICROWIRE's rows
    "C16": (46.88, 104.39, 0),    # the PLL column, 1.3 mm apart (courtyards 0.3 mm), far enough east for the fan
    "C24": (46.66, 105.66, 0),
    "C22": (46.66, 106.97, 0),
    "C23": (46.0, 108.55, 0),
    "C15": (46.4, 110.13, 0),
    "R5": (48.38, 106.82, -90),   # loop filter beside the column, C25 under R5
    "C25": (48.38, 108.96, -90),
    "C27": (44.325, 113.9, 0),    # U7's supply capacitor with its 3V3 pad straight above U7 pin 2
})

# ---- west: supply and bypass capacitors
P.run("3V3", [(36.9, 106.8), (36.55, 106.8), (36.02, 106.27), (36.02, 104.4)])               # pin 1 to C13
P.run("/LMX_BYP1", [(36.9, 107.3), (36.48, 107.3), (35.58, 106.4), (35.43, 106.4)])     # pin 2 to C20
P.run("/LMX_BYP2", [(36.9, 107.8), (36.3, 107.8), (36.17, 107.67), (35.43, 107.67)])    # pin 3 to C21
P.run("3V3", [(36.9, 110.8), (35.39, 110.8)])                                              # pin 9 to C14
P.run("GND", [(36.98, 104.4), (37.9, 104.4), (38.3, 104.8), (38.3, 105.9)])               # C13 to pin 35
# 3V3 vias for pins 1 and 9, joined on the bottom and fed from the trunk's via
P.via("3V3", 35.3, 104.4)
P.run("3V3", [(35.3, 104.4), (36.02, 104.4)])
P.via("3V3", 35.3, 111.75)
P.run("3V3", [(35.3, 111.75), (35.39, 111.66), (35.39, 110.8)])
P.run("3V3", [(35.3, 104.4), (35.3, 111.75)], 0.3, B)
# the U1 trunk on down past MICROWIRE's turn to its via, then east under U6 on the bottom (to pin 15) and up to y 108.3
P.run("3V3", [(30.05, 106.0), (30.05, 115.6), (30.65, 116.2)], 0.25)
P.via("3V3", 30.65, 116.2)
P.run("3V3", [(30.65, 116.2), (31.05, 116.6), (38.75, 116.6), (39.15, 116.2), (39.15, 115.7)], 0.3, B)
P.run("3V3", [(30.65, 116.2), (30.05, 115.6), (30.05, 108.7), (30.45, 108.3), (35.3, 108.3)], 0.3, B)

# ---- west: FSK. FS and DATA drop from R7 and R8 into two lanes west of the capacitors and turn into pins 7 and 6;
# CLK hops under them from R6 and comes up beside C21 into pin 4.
P.run("/FSK_DATA", [(35.435, 102.41), (35.435, 103.4), (32.925, 105.91), (32.925, 108.9), (33.325, 109.3), (36.9, 109.3)])
P.run("/FSK_FS", [(34.105, 102.41), (34.105, 104.095), (32.525, 105.675), (32.525, 109.066), (33.259, 109.8), (36.9, 109.8)])
P.run("/FSK_CLK", [(32.775, 102.41), (32.775, 103.3)])
P.via("/FSK_CLK", 32.775, 103.3)
P.run("/FSK_CLK", [(32.775, 103.3), (32.775, 106.535), (33.69, 107.45)], W, B)
P.via("/FSK_CLK", 33.69, 107.45)
P.run("/FSK_CLK", [(33.69, 107.45), (33.69, 108.1), (33.89, 108.3), (36.9, 108.3)])

# ---- south: MICROWIRE from the lanes U1's plan hands on at y 106 into pins 10-13; MUX also to TP5
MW = [("/LMX_MUX", 32.125, 113.0, 32.525, 113.4, 37.4, 113.0, 37.8),
      ("/LMX_CLK", 31.525, 113.249, 32.276, 114.0, 37.649, 113.349, 38.3),
      ("/LMX_DATA", 30.925, 113.497, 32.028, 114.6, 37.897, 113.697, 38.8),
      ("/LMX_LE", 30.475, 113.683, 31.842, 115.05, 38.083, 113.833, 39.3)]
for net, lane, yb, xr, row, xe, ye, pin in MW:
    P.run(net, [(lane, 106.0), (lane, yb), (xr, row), (xe, row), (pin, ye), (pin, 111.7)])
P.via("/LMX_MUX", 34.0, 112.75)
P.run("/LMX_MUX", [(34.0, 112.75), (34.0, 113.4)])
P.run("/LMX_MUX", [(34.0, 112.75), (32.7, 112.75)], W, B)                                 # to TP5
# pin 15 into C17, out round its east side to a via outside the RF zone
P.run("3V3", [(40.3, 111.7), (40.3, 112.85), (40.665, 113.215), (40.665, 114.75), (39.715, 115.7), (39.15, 115.7)])
P.run("3V3", [(40.665, 113.21), (40.03, 113.21)])
P.via("3V3", 39.15, 115.7)

# ---- USB under U2's west pins, up north of U6; U6.2's ground via between them
P.run("/USB_DM", [(36.3, 100.598), (36.3, 112.4), (34.975, 113.725), (34.975, 115.75)], W, B)
P.run("/USB_DP", [(37.385, 100.513), (36.875, 101.023), (36.875, 115.75)], W, B)
for net, x in (("/USB_DM", 34.975), ("/USB_DP", 36.875)):
    P.via(net, x, 115.75)
    P.run(net, [(x, 115.75), (x, 117.062)])
P.via("GND", 35.925, 115.85)
P.run("GND", [(35.925, 115.85), (35.925, 117.062)])

# ---- east: the PLL column. Lines leave east, the outer ones rise first, each into its capacitor's west pad.
P.run("3V3", [(42.7, 106.8), (43.1, 106.8), (45.51, 104.39)], 0.25)                      # pin 27 to the 3V3 line
P.run("/CP_LOOP", [(42.7, 107.8), (43.6, 107.8), (45.74, 105.66), (46.18, 105.66)])      # to C24
P.run("/CP_LOOP", [(45.74, 105.66), (46.39, 106.31), (48.38, 106.31)])                   # between C24 and C22 to R5
P.run("/LOOP_RC", [(48.38, 107.33), (48.38, 108.48)])                                     # R5 to C25
P.run("/LMX_VREFVCO", [(42.7, 109.3), (43.1, 109.3), (45.43, 106.97), (46.18, 106.97)])  # to C22
P.run("/LMX_VREGVCO", [(42.7, 109.8), (43.6, 109.8), (44.85, 108.55), (45.225, 108.55)])   # to C23
P.run("3V3", [(42.7, 110.3), (43.8, 110.3), (43.97, 110.13), (45.92, 110.13)], 0.25)     # pin 20 to C15
P.run("/LMX_CE", [(42.7, 110.8), (48.6, 110.8), (49.0, 110.4), (49.0, 104.0)])           # under the column, north
P.run("/LMX_CE", [(49.0, 103.01), (48.3, 103.01)])                                        # R9
# bottom link 1: from pin 27's line under the column to pin 20 and C15, on under CE to C27 and U7 pin 2
P.via("3V3", 43.6, 106.3)
P.run("3V3", [(43.6, 106.3), (43.6, 109.33), (44.4, 110.13)], 0.3, B)
P.via("3V3", 44.4, 110.13)
P.run("3V3", [(44.4, 110.13), (44.4, 112.05), (43.55, 112.9)], 0.3, B)
P.via("3V3", 43.55, 112.9)
P.run("3V3", [(43.55, 112.9), (43.55, 115.825)], 0.25)                                   # C27 pad 1, U7 pin 2
# bottom link 2: U7's LE pin, east past U7's lower-right corner, north to a via beside C27
P.run("3V3", [(43.05, 119.775), (43.05, 120.6)])
P.via("3V3", 43.05, 120.6)
P.run("3V3", [(43.05, 120.6), (43.35, 120.3), (44.0, 120.3), (44.4, 119.9), (44.4, 114.95)], 0.3, B)
P.via("3V3", 44.4, 114.95)
P.run("3V3", [(44.4, 114.95), (43.55, 114.95)], 0.25)

# ---- north: REF20, the 3V3 line and Y2's supply
P.run("/REF20", [(44.2, 102.65), (39.1, 102.65), (38.8, 102.95), (38.8, 105.9)])
P.run("3V3", [(39.3, 104.39), (46.4, 104.39)], 0.3)                                       # C18, C19, pin 27, C16
P.run("3V3", [(39.3, 105.9), (39.3, 104.39)])                                             # pin 33
P.run("3V3", [(39.8, 105.9), (39.8, 104.39)])                                             # pin 32
P.run("3V3", [(46.55, 98.5), (46.55, 99.9), (46.4, 100.05), (46.4, 104.39)], 0.3)       # C12, Y2 pins 1 and 4, C16
P.run("3V3", [(48.15, 98.98), (48.15, 99.45), (47.75, 99.85), (46.55, 99.85)], 0.3)     # C11

# ---- GND: U2's pins into its pad, the pad's vias, the capacitors' vias
for a, b in (((36.9, 108.8), (37.5, 108.8)), ((41.8, 111.7), (41.8, 111.1)), ((42.7, 108.8), (42.1, 108.8)),
             ((40.3, 105.9), (40.3, 106.5)), ((38.3, 105.9), (38.3, 106.5))):
    P.run("GND", [a, b])
for x in (38.65, 39.8, 40.95):
    for y in (107.65, 108.8, 109.95):
        P.via("GND", x, y)
GVIAS = [
    ((34.6, 105.35), [(34.47, 106.4), (34.47, 105.48), (34.6, 105.35)]),       # C20, C21 (joined)
    ((34.43, 111.75), [(34.43, 110.8), (34.43, 111.75)]),                         # C14
    ((41.8, 103.43), [(39.415, 103.43), (41.8, 103.43)]),                         # C18, C19
    ((44.4, 99.7), [(44.65, 98.5), (44.65, 99.45), (44.4, 99.7), (44.2, 99.9), (44.2, 100.75)]),  # C12, Y2 pin 2
    ((48.15, 97.3), [(48.15, 98.02), (48.15, 97.3)]),                             # C11
    ((48.3, 101.2), [(48.3, 101.99), (48.3, 101.2)]),                             # R9
    ((48.0, 104.39), [(47.36, 104.39), (48.0, 104.39)]),                          # C16
    ((47.95, 105.4), [(47.14, 105.66), (47.69, 105.66), (47.95, 105.4)]),         # C24
    ((47.55, 107.9), [(47.14, 106.97), (47.14, 107.49), (47.55, 107.9), (47.55, 108.1), (47.1, 108.55), (46.775, 108.55)]),  # C22, C23
    ((47.5, 110.13), [(46.88, 110.13), (47.5, 110.13)]),                          # C15
    ((45.1, 113.0), [(45.1, 113.9), (45.1, 113.0)]),                              # C27
    ((39.45, 114.75), [(40.03, 114.17), (39.45, 114.75)]),                        # C17
]
for (x, y), link in GVIAS:
    P.via("GND", x, y)
    P.run("GND", link)
P.run("GND", [(39.415, 103.43), (40.73, 103.43)])
P.run("GND", [(34.47, 106.4), (34.47, 107.67)])
P.run("GND", [(48.38, 109.44), (48.38, 109.6), (47.85, 110.13), (47.5, 110.13)])                                           # C25


def plan(copper=None):
    return P.copper()


if __name__ == "__main__":
    main(P, "Phase 5: U2 and its parts")
