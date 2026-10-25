"""Phase 5, floorplan B3: U1's escape on all four sides and its own small parts, planned as copper (tools/pcb_plan.py)
and checked before it is laid. Each side hands its lines on in the lanes of the lane plan (phase5-lanes.json).
  west   WHEEL1 north to RV1 (C39 beside it); WHEEL2, WHEEL3, RF_MODE, CC1, CC2 west then south down the strip
         between the pots' pins and U1's capacitors, 0.45 mm apart (C40 on WHEEL2 at U1, C41 on WHEEL3 between the
         pots); VCAP straight into C9; pin 24's 3V3 down the gap beside C9 to C4, then out with the south lines.
  south  3V3, MICROWIRE (0.45 mm), FSK (0.6 mm, a clock) and USB D- jog west together, clear of U2's west parts;
         D- then dives (the USB pair runs on the bottom to U6), D+ and SWDIO dive below their pins; pin 36 to C5.
  GND    every VSS pin straight into the exposed pad.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_u1.py place | lay [--dry-run]"""
import sys

sys.path.insert(0, "tools")
from pcb_plan import B, Plan, T, jog, main, turn

P = Plan()
W = 0.2
TIP = 0.438  # U1's pad half-length: pad centre to tip

# --- parts -----------------------------------------------------------------------------------------------------
P.place.update({
    "C39": (30.14, 87.0, 180),    # WHEEL1 reservoir, beside WHEEL1's run north
    "C40": (30.2, 89.9, 90),      # WHEEL2 reservoir, on WHEEL2's run west
    "C41": (27.6, 103.5, 180),    # WHEEL3 reservoir, between RV2's and RV3's pins
    "C9": (30.63, 95.5, -90),     # VCAP, pad 1 level with pin 22
    "C4": (30.63, 98.55, -90),    # pin 24's 100 nF
    "C5": (39.3, 98.6, -90),      # pin 36's 100 nF
})

# --- west ------------------------------------------------------------------------------------------------------
west = {13: ("/WHEEL1", 90.345), 14: ("/WHEEL2", 90.845), 15: ("/WHEEL3", 91.345), 17: ("/RF_MODE", 92.345),
        18: ("/CC1", 92.845), 19: ("/CC2", 93.345)}
XW = 32.698
# WHEEL1: west, then north up to RV1's wiper
(w1,) = turn([(XW, 90.345)], (-1, 0), (0, -1), [-30.9], 0.45, tips=TIP)
P.run("/WHEEL1", w1 + [(30.9, 83.0), (27.9, 80.0), (26.8, 80.0)])
P.run("/WHEEL1", [(30.9, 87.0), (30.62, 87.0)])                       # to C39
# the south group: inside of the bend first
LANE = {"/CC2": 29.6, "/CC1": 29.15, "/RF_MODE": 28.7, "/WHEEL3": 28.25, "/WHEEL2": 27.8}
order = [19, 18, 17, 15, 14]
fan = turn([(XW, west[p][1]) for p in order], (-1, 0), (0, 1), [-LANE[west[p][0]] for p in order], 0.45, tips=TIP)
ends = {}
for p, pts in zip(order, fan):
    net = west[p][0]
    ends[net] = pts
P.run("/WHEEL2", ends["/WHEEL2"] + [(27.8, 96.7), (27.5, 97.0), (26.8, 97.0)])
P.run("/WHEEL2", [(30.2, 90.845), (30.2, 90.38)])                      # to C40
Y_HAND = 103.0  # the south group carries on in the west-lane plan from here
P.run("/WHEEL3", ends["/WHEEL3"] + [(28.25, Y_HAND), (28.25, 103.5)])
P.run("/WHEEL3", [(28.25, 103.5), (28.08, 103.5)])                     # to C41
for net in ("/RF_MODE", "/CC1", "/CC2"):
    P.run(net, ends[net] + [(LANE[net], Y_HAND)])
# VCAP into C9's pad 1; GND pins into the exposed pad
P.run("/VCAP", [(XW, 94.845), (30.63, 94.845)], 0.3)
for a, b in [((32.697, 95.345), (33.6, 95.345)), ((35.385, 89.657), (35.385, 90.6)),
             ((38.385, 96.532), (38.385, 95.6)), ((39.572, 90.845), (38.6, 90.845))]:
    P.run("GND", [a, b], 0.25)

# --- south -----------------------------------------------------------------------------------------------------
YS = 96.532
# pin 24's 3V3 runs down the gap beside C9 (C4 on the way) and joins the south group as its outer line
P.run("3V3", [(XW, 95.845), (31.875, 95.845), (31.875, 98.07)], 0.25)
P.run("3V3", [(31.875, 98.07), (30.63, 98.07)], 0.25)                  # to C4
south = [("3V3", 31.875, None), ("/LMX_LE", 33.385, YS), ("/LMX_DATA", 33.885, YS), ("/LMX_CLK", 34.385, YS),
         ("/LMX_MUX", 34.885, YS), ("/FSK_CLK_MCU", 35.385, YS), ("/FSK_FS_MCU", 35.885, YS),
         ("/FSK_DATA_MCU", 36.385, YS), ("/USB_DM", 36.885, YS)]
lanes = [30.05, 30.475, 30.925, 31.375, 31.825, 32.425, 33.025, 33.625, 34.225]
gaps = [0.425, 0.45, 0.45, 0.45, 0.6, 0.6, 0.6, 0.6]
starts = [(x, 98.07 if y is None else y + TIP + 1.0) for _, x, y in south]
J = jog(starts, (0, 1), (-1, 0), [s[0] - l for s, l in zip(starts, lanes)], gaps, lead=0.4)
Y_SOUTH = 104.0  # the corridor plan picks the south group up here
for (net, x, y), pts, lane in zip(south, J, lanes):
    w = 0.25 if net == "3V3" else W
    head = [] if y is None else [(x, y)]
    if net == "/USB_DM":
        P.run(net, head + pts)
        P.via(net, *pts[-1])
    else:
        P.run(net, head + pts + [(lane, Y_SOUTH)], w)
# D+ and SWDIO dive below their pins; pin 36 to C5
P.run("/USB_DP", [(37.385, YS), (37.385, 99.6)])
P.via("/USB_DP", 37.385, 99.6)
P.run("/SWDIO", [(37.885, YS), (37.885, 97.97), (38.2, 98.285)])
P.via("/SWDIO", 38.2, 98.285)
P.run("3V3", [(38.885, YS), (38.885, 97.6), (39.3, 98.015), (39.3, 98.12)], 0.25)


def plan(copper=None):
    return P.copper()


if __name__ == "__main__":
    main(P, "Phase 5: U1 escape")
