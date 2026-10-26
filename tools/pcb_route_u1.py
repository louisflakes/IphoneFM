"""Phase 5, floorplan B3: U1's escape on all four sides and its own small parts, planned as copper (tools/pcb_plan.py)
and checked before it is laid. U1 sits 2.5 mm further north than at B3's placement, which gives the corridor to U2
room for the FSK series resistors. Each side hands its lines on in the lanes of the lane plan (phase5-lanes.json).
  west   WHEEL1 north to RV1 (C39 beside it); WHEEL2, WHEEL3, RF_MODE, CC1, CC2 west, then south down the strip
         between the pots' pins and U1's capacitors, 0.45 mm apart (C40 on WHEEL2 at U1, C41 on WHEEL3 between the
         pots); VCAP straight into C9; pin 24's 3V3 down the gap beside C9 to C4, then out with the south lines.
  south  3V3, MICROWIRE (0.45 mm, 0.6 mm round its clock), FSK (0.65-0.7 mm) and USB D- jog west together, clear of U2's west parts,
         FSK into R6-R8 side by side; D- then dives (the USB pair runs on the bottom to U6); D+ and SWDIO dive below
         their pins; pin 36 to C5.
  north  the LED lines straight north; VDDA north to its parts (C7, C8, FB2) and C3 above the NRST/CE/REF20 runs;
         NRST, CE and REF20 north then east (C10 on NRST); CE and REF20 drop to the bottom to pass under the
         receiver bundle; pin 1 (VBAT) round to C6 with pin 48, 3V3 fed from below.
  east   the receiver bundle east, then north into the U4 corner's lanes, RST one lane west of it; BOOT0 drops to the
         bottom on the way (the bundle's lines step 0.1 mm apart round its via); SWCLK drops to TP7 on the bottom.
  GND    every VSS pin straight into the exposed pad.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_u1.py place | lay [--dry-run]"""
import sys

sys.path.insert(0, "tools")
from pcb_plan import B, Plan, T, jog, main, turn

P = Plan()
W = 0.2
TIP = 0.438                       # U1's pad half-length: pad centre to tip
CX, CY = 36.135, 90.595           # U1's centre
XW, XE = CX - 3.437, CX + 3.437   # west and east pin columns
YN, YS = CY - 3.438, CY + 3.437   # north and south pin rows


def wy(pin):   # west side, pins 13 (top) to 24
    return CY - 2.75 + (pin - 13) * 0.5


def sx(pin):   # south side, pins 25 (left) to 36
    return CX - 2.75 + (pin - 25) * 0.5


def nx(pin):   # north side, pins 1 (right) to 12
    return CX + 2.75 - (pin - 1) * 0.5


def ey(pin):   # east side, pins 37 (bottom) to 48
    return CY + 2.75 - (pin - 37) * 0.5


# --- parts -----------------------------------------------------------------------------------------------------
P.place.update({
    "U1": (CX, CY, -90),
    "C39": (30.14, 84.5, 180),    # WHEEL1 reservoir, beside WHEEL1's run north
    "C40": (30.2, 87.4, 90),      # WHEEL2 reservoir, on WHEEL2's run west
    "C41": (27.6, 103.5, 180),    # WHEEL3 reservoir, between RV2's and RV3's pins
    "C9": (30.63, 94.03, -90),    # VCAP
    "C4": (30.63, 97.0, -90),     # pin 24's 100 nF
    "C5": (39.3, 96.1, -90),      # pin 36's 100 nF
    "C6": (41.625, ey(48) - 0.2, 0),  # pin 48's 100 nF, with pin 1
    "R3": (29.15, 129.3, 90),     # BOOT0 pull-down, at SW2
    "C7": (35.84, 83.2, 0),       # VDDA 100 nF
    "C8": (36.44, 81.6, 0),       # VDDA 1 uF
    "FB2": (35.2, 79.6, -90),     # 3V3 to VDDA
    "C3": (38.0, 79.4, 0),        # 3V3 bulk
    "C10": (38.8, 83.15, 90),     # NRST filter
})

# --- west ------------------------------------------------------------------------------------------------------
(w1,) = turn([(XW, wy(13))], (-1, 0), (0, -1), [-30.9], 0.45, tips=TIP)
P.run("/WHEEL1", w1 + [(30.9, 82.4), (28.5, 80.0), (26.8, 80.0)])
P.run("/WHEEL1", [(30.9, 84.5), (30.62, 84.5)])                       # to C39
LANE = {"/CC2": 29.6, "/CC1": 29.15, "/RF_MODE": 28.7, "/WHEEL3": 28.25, "/WHEEL2": 27.8}
group = [(19, "/CC2"), (18, "/CC1"), (17, "/RF_MODE"), (15, "/WHEEL3"), (14, "/WHEEL2")]   # inside of the bend first
fan = dict(zip([n for _, n in group],
               turn([(XW, wy(p)) for p, _ in group], (-1, 0), (0, 1), [-LANE[n] for _, n in group], 0.45, tips=TIP)))
P.run("/WHEEL2", fan["/WHEEL2"] + [(27.8, 96.7), (27.5, 97.0), (26.8, 97.0)])
P.run("/WHEEL2", [(30.2, 119.4686 - 30.2), (30.2, 87.88)])             # to C40, off WHEEL2's diagonal
Y_HAND = 103.0  # the west lane plan carries RF_MODE, CC1 and CC2 on from here
P.run("/WHEEL3", fan["/WHEEL3"] + [(28.25, 103.5)])
P.run("/WHEEL3", [(28.25, 103.5), (28.08, 103.5)])                     # to C41
P.run("/WHEEL3", [(28.25, 103.5), (28.25, 113.25), (27.5, 114.0), (26.8, 114.0)])
for net in ("/RF_MODE", "/CC1", "/CC2"):
    P.run(net, fan[net] + [(LANE[net], Y_HAND)])
P.run("/VCAP", [(XW, wy(22)), (31.9, wy(22)), (31.2, wy(22) + 0.7)], 0.3)
# GND pins straight into the exposed pad
for a, b in [((XW, wy(23)), (33.6, wy(23))), ((nx(8), YN), (nx(8), YN + 0.95)),
             ((sx(35), YS), (sx(35), YS - 0.95)), ((XE, ey(47)), (38.6, ey(47)))]:
    P.run("GND", [a, b], 0.25)

# --- south -----------------------------------------------------------------------------------------------------
y24 = wy(24)
P.run("3V3", [(XW, y24), (32.06, y24), (31.875, y24 + 0.185), (31.875, 96.52)], 0.25)
P.run("3V3", [(31.875, 96.52), (30.63, 96.52)], 0.25)                  # to C4
south = [("3V3", 31.875, None)] + [(n, sx(p), YS) for p, n in [
    (25, "/LMX_LE"), (26, "/LMX_DATA"), (27, "/LMX_CLK"), (28, "/LMX_MUX"), (29, "/FSK_CLK_MCU"),
    (30, "/FSK_FS_MCU"), (31, "/FSK_DATA_MCU"), (32, "/USB_DM")]]
R_ROW = {"/FSK_CLK_MCU": 32.775, "/FSK_FS_MCU": 34.105, "/FSK_DATA_MCU": 35.435}
# MICROWIRE's CLK is a Clock-class line: 0.6 mm to its neighbours, 0.45 mm between the others
lanes = [30.05, 30.475, 30.925, 31.525, 32.125, 32.775, 34.105, 35.435, 36.3]
gaps = [0.425, 0.45, 0.6, 0.6, 0.65, 0.65, 0.7, 0.7]
# the two clock lines get 0.6 mm to their neighbours right after the 1 mm exit, inside the escape area
# (pcb_freeroute.CLOCK_ESCAPE): every line west of FSK's FS steps west, the westmost first, 0.07 mm apart;
# (shift west, delay)
STEP = {"/LMX_LE": (0.4, 0.0), "/LMX_DATA": (0.4, 0.07), "/LMX_CLK": (0.3, 0.14), "/LMX_MUX": (0.2, 0.21),
        "/FSK_CLK_MCU": (0.1, 0.28)}
heads = {}
for net, x, y in south:
    if net in STEP:
        s, d = STEP[net]
        y1 = y + TIP + 1.0 + d
        heads[net] = [(x, y), (x, y1), (x - s, y1 + abs(s))]
starts = [(x, 96.52) if y is None else (heads[net][-1] if net in heads else (x, y + TIP + 1.0)) for net, x, y in south]
J = jog(starts, (0, 1), (-1, 0), [s[0] - l for s, l in zip(starts, lanes)], gaps, lead=1.6)  # 3V3 bends below C4
y_jog = max(p[-1][1] for p in J)
Y_R = 101.9                       # R6-R8 centres (pads 0.51 above and below), high enough that FSK clears C13
Y_SOUTH = 106.0                   # the U2-west plan picks MICROWIRE and 3V3 up here
for (net, x, y), pts, lane in zip(south, J, lanes):
    w = 0.25 if net == "3V3" else W
    head = [] if y is None else heads.get(net, [(x, y)])
    if net == "/USB_DM":
        via = (lane, pts[-1][1] + 0.15)
        P.run(net, head + pts + [via])
        P.via(net, *via)
        dm_bend = pts[1][1]
    elif net in R_ROW:
        P.run(net, head + pts + [(lane, Y_R - 0.51)])
        P.place[{"/FSK_CLK_MCU": "R6", "/FSK_FS_MCU": "R7", "/FSK_DATA_MCU": "R8"}[net]] = (lane, Y_R, -90)
    else:
        P.run(net, head + pts + [(lane, Y_SOUTH)], w)
# D+ and SWDIO dive below their pins; pin 36 to C5
y_dp = round(dm_bend + 0.65, 3)
P.run("/USB_DP", [(sx(33), YS), (sx(33), y_dp)])
P.via("/USB_DP", sx(33), y_dp)
P.run("/SWDIO", [(sx(34), YS), (sx(34), YS + TIP + 1.0), (sx(34) + 0.515, YS + TIP + 1.515)])
P.via("/SWDIO", sx(34) + 0.515, YS + TIP + 1.515)
P.run("/SWDIO", [(38.4, 95.985), (38.4, 99.3), (40.3, 101.2)], W, B)             # to TP8 on the bottom
P.run("3V3", [(sx(36), YS), (sx(36), 95.1), (39.3, 95.515), (39.3, 95.62)], 0.25)

# --- north -----------------------------------------------------------------------------------------------------
Y_L = 78.0  # the LED lines carry on in the lane plan from here
for p, n in [(12, "/LED_B"), (11, "/LED_G"), (10, "/LED_R")]:
    P.run(n, [(nx(p), YN), (nx(p), Y_L)])
P.run("VDDA", [(nx(9), YN), (nx(9), 80.6), (35.2, 80.285), (35.2, 80.09)], 0.3)
P.run("VDDA", [(nx(9), 83.2), (35.36, 83.2)], 0.3)                    # to C7
P.run("VDDA", [(nx(9), 81.6), (35.665, 81.6)], 0.3)                   # to C8
P.run("3V3", [(35.2, 79.11), (35.2, 78.9), (35.5, 78.6), (36.6, 78.6), (37.05, 79.05), (37.05, 79.4)], 0.3)  # FB2 to C3
P.via("3V3", 36.1, 78.6)                                              # fed from below
runs = turn([(nx(5), YN), (nx(6), YN), (nx(7), YN)], (0, -1), (1, 0), [-85.3, -84.7, -84.1], 0.6, tips=TIP)
X_D = {"/REF20_MCU": 43.4, "/LMX_CE": 42.6}   # REF20 0.8 mm from CE's vias (Clock class)
P.run("/REF20_MCU", runs[0] + [(43.4, 85.3)])
P.run("/LMX_CE", runs[1] + [(42.3, 84.7), (42.6, 84.4)])
P.run("/NRST", runs[2] + [(40.0, 84.1)])
P.run("/NRST", [(38.8, 84.1), (38.8, 83.63)])                         # to C10
P.via("/NRST", 40.0, 84.1)                                            # TP6 on the bottom
P.run("/NRST", [(40.0, 84.1), (40.0, 83.0)], W, B)
P.place["TP6"] = (40.0, 83.0, 0)
# CE and REF20 under the receiver bundle on the bottom, up again south of it
Y_DS = 95.8
for n, x in X_D.items():
    y0 = 85.3 if n == "/REF20_MCU" else 84.4
    P.via(n, x, y0)
    y1 = Y_DS if n == "/LMX_CE" else 99.6   # REF20 stays below until past the 3V3 line to Y2
    P.run(n, [(x, y0), (x, y1)], W, B)
    P.via(n, x, y1)
P.run("/REF20_MCU", [(43.4, 99.6), (42.3, 100.7), (42.3, 101.58)])
P.run("/LMX_CE", [(42.6, Y_DS), (48.4, Y_DS), (49.0, Y_DS + 0.6), (49.0, 104.0)])   # the U2 plan carries CE on
# pin 1 (VBAT) round the corner to C6 with pin 48; 3V3 from below
P.run("3V3", [(nx(1), YN), (nx(1), 86.45), (39.135, 86.2), (40.7, 86.2), (41.145, 86.645), (41.145, ey(48) - 0.2)], 0.25)
P.run("3V3", [(XE, ey(48)), (41.145, ey(48))], 0.25)
P.via("3V3", 39.9, 86.2)

# --- east ------------------------------------------------------------------------------------------------------
X1 = XE + TIP + 1.0  # one millimetre out from the tips
# step the rows 0.1 mm apart round BOOT0, then turn north into the U4 corner's lanes (tools/pcb_route_u4.py)
rows = [(45, "/I2C_SCL", -0.1, 0.0), (43, "/I2C_SDA", 0.1, 0.0), (42, "/RX_FS_MCU", 0.1, 0.0),
        (41, "/RX_SD_MCU", 0.1, 0.0), (40, "/RX_RCLK", 0.2, 0.1), (39, "/RX_SCK_MCU", 0.3, 0.0)]
# (pin, net, step, delay): RCLK and SCK step 0.2 / 0.3 mm south so the clocks run 0.6 mm from their neighbours;
# RCLK steps 0.1 mm after SCK so the two steps stay 0.4 mm apart; all end inside the escape area
U4_LANES = {"/I2C_SCL": 46.2, "/I2C_SDA": 46.8, "/RX_FS_MCU": 47.4, "/RX_SD_MCU": 48.0, "/RX_RCLK": 48.6,
            "/RX_SCK_MCU": 49.2}
Y0 = 88.0  # where the U4 corner plan picks the lanes up
stepped = [(X1 + dl + abs(d), ey(p) + d) for p, _, d, dl in rows]
T_ = turn(stepped, (1, 0), (0, -1), [U4_LANES[n] for _, n, _, _ in rows], 0.6, min_exit=0.0, min_tail=0.3, late=True)
for (p, n, d, dl), pts in zip(rows, T_):
    P.run(n, [(XE, ey(p)), (X1 + dl, ey(p))] + pts + [(U4_LANES[n], Y0)])
# RST runs on top beside the bundle (one lane west of SCL), handed on to the U4 corner plan at Y0; it stays off the
# bottom here so the attenuator bus can cross under the bundle (tools/pcb_route_att.py). BOOT0 dives and heads west
y_rst = ey(46) - 0.2
P.run("/RX_RST", [(XE, ey(46)), (X1, ey(46)), (X1 + 0.2, y_rst), (45.2, y_rst), (45.6, y_rst - 0.4), (45.6, Y0)])
P.run("/BOOT0", [(XE, ey(44)), (41.5, ey(44))])
P.via("/BOOT0", 41.5, ey(44))
P.run("/BOOT0", [(41.5, ey(44)), (39.4, ey(44)), (39.0, ey(44) - 0.4), (39.0, 87.4), (38.6, 87.0), (31.0, 87.0)], W, B)
P.run("3V3", [(39.9, 86.2), (31.0, 86.2)], 0.4, B)
# SWCLK drops to TP7 on the bottom
P.run("/SWCLK", [(XE, ey(37)), (40.6, ey(37))])
P.via("/SWCLK", 40.6, ey(37))
P.run("/SWCLK", [(40.6, ey(37)), (40.8, ey(37) + 0.2), (40.8, 97.0)], W, B)
P.place["TP7"] = (40.8, 97.0, 0)
# 3V3 for pin 36 (C5) from pin 24's line, on the bottom under the south pins; on to Y2 on top
P.via("3V3", 31.875, 95.2)
P.run("3V3", [(31.875, 95.2), (39.6, 95.2), (39.95, 95.55), (39.95, 95.62)], 0.4, B)
P.via("3V3", 39.95, 95.62)
P.run("3V3", [(39.3, 95.62), (40.0, 95.62), (41.58, 97.2), (46.15, 97.2), (46.55, 97.6), (46.55, 98.5)], 0.4)


def plan(copper=None):
    return P.copper()


if __name__ == "__main__":
    main(P, "Phase 5: U1 escape")
