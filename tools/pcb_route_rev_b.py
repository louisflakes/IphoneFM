"""Rev B Phase B5: routing for the front panel, as a plan laid into kicad/rev-b/IphoneFM.kicad_pcb with KiCad's own Python
(file edits, for use while the Rev B board is NOT open in KiCad). Lines leave pins straight, bend only by 45 degrees and
keep one spacing per bus (routing-quality standard; tools/pcb_plan.py turn/jog).

Sections, in laying order:
  B5.3  U8's 32 outputs: the bottom and right sides on the top layer in one bus between the digits' pad columns; the left
        side and pins 32-33 through 0.4/0.2 mm vias to a bus on the bottom layer, which comes up through vias beside the
        pads of DS3 and DS4. Inside the "U8 fan-out" rule areas: 0.127 mm tracks and gaps, 0.4/0.2 mm vias (the user's
        approval, 2026-11-06)
  B5.4  VBUS: the bottom spine at x 25.6 up to DS1, one via at each digit's pin 8 (pins 3 and 8 are one node, B5.1);
        DS1's pin 8 on to the north band's riser; a bottom riser at x 27.35 to C44, C42, C43 and U8's VCC
  B5.5  U8's control lines: SCL, SDA and SDB on the bottom east under the top-edge parts and down x 28.2-29.0; SDB to
        U1 PC13, SCL and SDA to the I2C lines east of U1; R_EXT to R28; AD to the exposed pad
  B5.6  3V3 re-joined: TP2 to the bottom feed, a hop under DS1/DS2 and a trunk down the middle of the digits to R31,
        R32, R30 and U3 (C2), U3 to U2's island, FB2/C3 over the I2C lines, U1's north pins by x 41.2
  B5.7  Encoder lines and RF_MODE: vias off U1's west pins, a bottom bus at x 27.25-28.45 to R31, R32, R30 (and SW4),
        RF_MODE on to TP4, SW1, R18 and R17 as Rev A
  B5.8  Ground: U8's exposed-pad vias; Rev A stitching vias in the new lines' way taken up (pours re-stitch in B6)

Usage (from the repository root, KiCad closed on the Rev B board):
  "%LOCALAPPDATA%/Programs/KiCad/10.0/bin/python.exe" tools/pcb_route_rev_b.py lay
  python tools/pcb_route_rev_b.py json OUT.json      the plan as polylines for the scratch viewer
"""
import json
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcb_plan import turn, jog, T, B  # noqa: E402

BOARD = "kicad/rev-b/IphoneFM.kicad_pcb"
FINE_W = 0.127                       # tracks inside the U8 fan-out areas
W = 0.2                              # signals
PW = 0.4                             # power (VBUS, 3V3)
FINE_VIA, STD_VIA = (0.4, 0.2), (0.6, 0.3)
AREA = "U8 fan-out"
# the rule areas: around U8 on both layers, and the bottom layer under DS1 where the bottom bus widens out
AREAS = [((T, B), [(13.21, 60.06), (24.55, 60.06), (24.55, 69.6), (13.21, 69.6)]),
         ((B,), [(13.21, 69.6), (23.2, 69.6), (23.2, 73.0), (13.21, 73.0)]),
         ((T,), [(16.3, 69.6), (21.3, 69.6), (21.3, 70.7), (16.3, 70.7)])]   # the bottom side's exits, under U8
EXIT_WIDE_Y = 70.6                   # and its lines from U8's bottom side below this
BOT_WIDE_Y = 73.0                    # and the bottom bus's lines below this
TURN_P = (0.4 + 0.254) / math.sqrt(2)  # diagonals of a 90-degree turn from 0.4 mm-pitch pins onto 0.254 mm lanes


class Plan:
    def __init__(self):
        self.runs, self.vias = [], []

    def run(self, net, pts, w=W, layer=T):
        pts = [tuple(round(c, 4) for c in p) for p in pts]
        self.runs.append((net, layer, pts, w))

    def via(self, net, x, y, size=STD_VIA):
        self.vias.append((net, round(x, 4), round(y, 4), size))

    def segments(self):
        for net, layer, pts, w in self.runs:
            for a, b in zip(pts, pts[1:]):
                if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-6:
                    yield net, layer, a, b, w


P = Plan()


def split_run(net, pts, y_wide, layer):
    """A line that is FINE_W wide above y_wide and W below it (it runs downwards)."""
    fine, wide = [pts[0]], []
    for a, b in zip(pts, pts[1:]):
        if wide:
            wide.append(b)
        elif b[1] <= y_wide + 1e-9:
            fine.append(b)
        else:  # crosses y_wide on this segment
            t = (y_wide - a[1]) / (b[1] - a[1]) if b[1] != a[1] else 0.0
            m = (a[0] + t * (b[0] - a[0]), y_wide)
            if t > 1e-6:
                fine.append(m)
                wide = [m, b]
            else:
                wide = [a, b]
    P.run(net, fine, FINE_W, layer)
    if wide:
        P.run(net, wide, W, layer)


def peel_out(lane, y_pad):
    """From a lane, west into an outer pad (x 14.71) of a digit: a 45-degree step to x 17.0 at the pad's row."""
    return [(lane, y_pad - (lane - 17.0)), (17.0, y_pad), (14.71, y_pad)]


def peel_in(lane, y_pad):
    """From a lane, east into an inner pad (x 27.21): a 45-degree step to x 24.91 at the pad's row."""
    return [(lane, y_pad - (24.91 - lane)), (24.91, y_pad), (27.21, y_pad)]


DS_Y0, DS_P = 73.61, 8.3


def pad_y(digit, pin):
    """Board y of a digit's pad: pins 1-5 outer column, 10-6 inner column, 1.5 mm apart, pin 3/8 at the digit's centre."""
    row = {1: -2, 2: -1, 3: 0, 4: 1, 5: 2, 10: -2, 9: -1, 8: 0, 7: 1, 6: 2}[pin]
    return round(DS_Y0 + DS_P * (digit - 1) + 1.5 * row, 4)


SEG_PIN = {"A": 7, "B": 6, "C": 4, "D": 2, "E": 1, "F": 9, "G": 10, "DP": 5}
OUTER = {"C", "D", "E", "DP"}


def seg(net):
    d, s = int(net[3]), net[5:]
    return d, s, pad_y(d, SEG_PIN[s]), s in OUTER


# ---------------------------------------------------------------- B5.3 U8's outputs
# U8 at (18.0, 65.47); pin positions from the footprint (corner pins sit 0.1 mm further out)
def u8_left(k):    # pins 1-11, top to bottom; pad centre, toe at x 15.0
    return (15.40 if k in (1, 11) else 15.50), 63.47 + 0.4 * (k - 1)


def u8_bottom(k):  # pins 12-22, left to right; toe at y 68.47
    return 16.0 + 0.4 * (k - 12), (68.07 if k in (12, 22) else 67.97)


def u8_right(k):   # pins 23-33, bottom to top; toe at x 21.0
    return (20.60 if k in (23, 33) else 20.50), 67.47 - 0.4 * (k - 23)


def u8_top(k):     # pins 34-44, right to left; toe at y 62.47
    return 20.0 - 0.4 * (k - 34), (62.87 if k in (34, 44) else 62.97)


# the segment each output drives (netlist.json, step B5.2): the order the lines leave U8
TOP_BUS = [(12, "SEG1_E"), (13, "SEG1_D"), (14, "SEG1_C"), (15, "SEG1_DP"), (16, "SEG2_E"), (18, "SEG2_D"), (19, "SEG2_C"),
           (20, "SEG2_DP"), (21, "SEG3_E"), (22, "SEG3_D"), (23, "SEG3_C"), (24, "SEG2_B"), (25, "SEG2_A"), (26, "SEG2_F"),
           (27, "SEG2_G"), (28, "SEG1_B"), (29, "SEG1_A"), (30, "SEG1_F"), (31, "SEG1_G")]
BOT_BUS = [(11, "SEG3_DP"), (10, "SEG4_E"), (9, "SEG4_D"), (8, "SEG4_C"), (7, "SEG4_DP"), (6, "SEG4_B"), (5, "SEG4_A"),
           (4, "SEG4_F"), (3, "SEG4_G"), (2, "SEG3_B"), (1, "SEG3_A"), (33, "SEG3_F"), (32, "SEG3_G")]
NET = dict(TOP_BUS + BOT_BUS)

# top bus lanes, west to east, 0.4 mm apart; G1 (pin 31) stays on its fan-out lane
TOP_LANE = {pin: round(24.232 - 0.4 * (len(TOP_BUS) - 1 - i), 4) for i, (pin, _) in enumerate(TOP_BUS)}


def u8_top_bus():
    ends = {}
    # pin 12 runs straight down into DS1's E pad
    x, y = u8_bottom(12)
    P.run(NET[12], [(x, y), (x, pad_y(1, 1))])
    # pins 13-22 (not 17, ground) straight out 1 mm past the toe, then step right onto their lanes (rightmost first)
    # (0.127 mm until they are on their lanes, so pin 13 clears DS1's E pad; all step together, diagonals 0.28 mm
    # apart, 0.57 mm across pin 17)
    pins = [k for k in range(22, 12, -1) if k != 17]
    starts = [(u8_bottom(k)[0], 69.47) for k in pins]
    shifts = [TOP_LANE[k] - u8_bottom(k)[0] for k in pins]
    gaps = [round(abs(a[0] - b[0]) / math.sqrt(2), 4) for a, b in zip(starts, starts[1:])]
    for k, (s, p, q) in zip(pins, jog(starts, (0, 1), (1, 0), shifts, gaps)):
        assert q[1] < EXIT_WIDE_Y, (k, q)
        x = q[0]
        split_run(NET[k], [u8_bottom(k), s, p, q, (x, EXIT_WIDE_Y)] + tail(k, (x, EXIT_WIDE_Y)), EXIT_WIDE_Y, T)
    # pins 23-31 out of the right side, turned down at 0.254 mm past H1, then stepped left onto their lanes
    pins = list(range(23, 32))
    fine = [round(22.2 + 0.254 * i, 4) for i in range(len(pins))]
    tips = [21.0 - u8_right(k)[0] for k in pins]
    turned = turn([u8_right(k) for k in pins], (1, 0), (0, 1), fine, TURN_P, tips=tips, min_exit=1.0)
    movers = pins[:-1]   # pin 31 (G1) keeps its lane
    jogged = jog([turned[i][2] for i in range(len(movers))], (0, 1), (-1, 0),
                 [fine[i] - TOP_LANE[k] for i, k in enumerate(movers)], 0.254, lead=0.25)
    wide_y = round(max(q[1] for _, _, q in jogged) + 0.05, 4)   # widen once every line is on its lane
    assert wide_y < AREAS[0][1][2][1], wide_y
    for i, k in enumerate(pins):
        pts = turned[i][:]
        if k in movers:
            pts += jogged[i][1:]
        x = pts[-1][0]
        split_run(NET[k], pts + [(x, wide_y)] + tail(k, (x, wide_y))[0:], wide_y, T)


def tail(k, at):
    """From a top-bus line's last point down its lane and into its pad."""
    d, s, yp, outer = seg(NET[k])
    lane = TOP_LANE[k]
    path = peel_out(lane, yp) if outer else peel_in(lane, yp)
    return [p for p in path if p != at]


# bottom bus: 13 lanes 0.4 mm apart, x 18.0-22.8, west to east in BOT_BUS order
BOT_LANE = {pin: round(18.0 + 0.4 * i, 4) for i, (pin, _) in enumerate(BOT_BUS)}
VIA_OUT, VIA_IN = 16.9, 24.6        # vias beside the outer and inner pad columns


def u8_bottom_bus():
    # left side: odd pins to vias at x 14.35, even pins between them to vias at x 13.55 (top layer, 0.127 mm)
    vias = {}
    for k in range(1, 12):
        x, y = u8_left(k)
        vx = 14.35 if k % 2 else 13.55
        P.run(NET[k], [(x, y), (vx, y)], FINE_W)
        P.via(NET[k], vx, y, FINE_VIA)
        vias[k] = (vx, y)
    # bottom: east under U8's left pins, turned down at 0.254 mm (innermost, pin 11, westmost)
    order = list(range(11, 0, -1))
    lanes = [round(15.0 + 0.254 * i, 4) for i in range(len(order))]
    tips = [0.0 if k % 2 else 14.74 - 13.55 for k in order]   # even lines stay straight past the odd vias
    turned = turn([vias[k] for k in order], (1, 0), (0, 1), lanes, TURN_P, tips=tips, min_exit=0.0)
    paths = {k: turned[i] for i, k in enumerate(order)}
    # pins 33 and 32: out of the right side to vias, back west on the bottom and down under U8's right pins
    for k, vx in ((33, 21.65), (32, 22.45)):
        x, y = u8_right(k)
        P.run(NET[k], [(x, y), (vx, y)], FINE_W)
        P.via(NET[k], vx, y, FINE_VIA)
    paths[33] = [(21.65, 63.47), (20.65, 63.47), (20.3, 63.82)]
    paths[32] = [(22.45, 63.87), (20.8, 63.87), (20.6, 64.07)]
    # all 13 step east onto the bus lanes (eastmost first), 0.254 mm apart on the diagonals
    seq = [32, 33] + list(range(1, 12))
    starts = [(paths[k][-1][0], 68.0) for k in seq]
    jogged = jog(starts, (0, 1), (1, 0), [BOT_LANE[k] - paths[k][-1][0] for k in seq], 0.254)
    for i, k in enumerate(seq):
        pts = paths[k] + jogged[i]
        d, s, yp, outer = seg(NET[k])
        lane = BOT_LANE[k]
        if outer:   # west into a via beside the outer pad
            end = [(lane, yp - (lane - VIA_OUT)), (VIA_OUT, yp)]
            pad = (14.71, yp)
            vx = VIA_OUT
        else:
            end = [(lane, yp - (VIA_IN - lane)), (VIA_IN, yp)]
            pad = (27.21, yp)
            vx = VIA_IN
        split_run(NET[k], pts + [(lane, BOT_WIDE_Y)] + end, BOT_WIDE_Y, B)
        P.via(NET[k], vx, yp)
        P.run(NET[k], [(vx, yp), pad])


# ---------------------------------------------------------------- B5.4 VBUS
def vbus():
    P.run("VBUS", [(25.6, 79.9), (25.6, 73.61)], PW, B)                    # the spine on up to DS1
    for d in (1, 2, 3, 4):                                                 # each digit's pin 8
        y = pad_y(d, 8)
        P.via("VBUS", VIA_IN, y)
        P.run("VBUS", [(VIA_IN, y), (25.6, y)], PW, B)
        P.run("VBUS", [(VIA_IN, y), (27.21, y)], PW)
    P.run("VBUS", [(27.21, 73.61), (31.9, 73.61), (32.3, 73.21), (32.3, 70.3)], PW)   # DS1 pin 8 to the north band
    # U8's feed: up the bottom at x 27.35, clear of H1, then west along the top under C44 and C42 to a via at x 21.0
    P.run("VBUS", [(25.6, 73.61), (27.35, 71.86), (27.35, 62.7)], PW, B)
    P.via("VBUS", 27.35, 62.7)
    P.run("VBUS", [(27.35, 62.7), (24.83, 62.7), (21.39, 62.7), (21.0, 62.7)], PW)
    P.run("VBUS", [(24.83, 62.7), (24.83, 60.8)], PW)                      # C44.1
    P.run("VBUS", [(21.39, 62.7), (21.39, 60.55)], PW)                     # C42.1
    P.via("VBUS", 21.0, 62.7)
    P.run("VBUS", [(21.0, 62.7), (19.02, 62.7), (18.4, 62.08)], 0.3, B)
    P.via("VBUS", 18.4, 62.08, FINE_VIA)                                   # between C43 and U8's VCC pin
    P.run("VBUS", [(18.4, 62.97), (18.4, 62.08), (18.4, 61.35)], 0.25)


# ---------------------------------------------------------------- B5.5 U8's control lines
def control():
    # top: SCL and SDA straight up to vias (R28 sits over them), R_EXT up and into R28, SDB to a via and R29, AD inward
    P.run("/I2C_SCL", [u8_top(42), (16.8, 62.1), (16.3, 61.6)], FINE_W)
    P.via("/I2C_SCL", 16.3, 61.6, FINE_VIA)
    P.run("/I2C_SDA", [u8_top(41), (17.2, 62.05)], FINE_W)
    P.via("/I2C_SDA", 17.2, 62.05, FINE_VIA)
    P.run("/DRV_REXT", [u8_top(40), (17.6, 61.66), (17.3, 61.36), (17.03, 61.36)], FINE_W)
    P.run("/LED_SDB", [u8_top(36), (19.2, 62.05), (19.65, 61.6)], FINE_W)
    P.via("/LED_SDB", 19.2, 62.05, FINE_VIA)
    P.run("GND", [u8_top(37), (18.8, 64.3)], W)
    # bottom: east under the top-edge parts, 0.4 mm apart, turned down at x 28.2 (SDB), 28.6 (SDA), 29.0 (SCL)
    starts = [(19.4, 61.85), (17.8, 61.45), (16.85, 61.05)]   # each a 45-degree step up out of its via
    turned = turn(starts, (1, 0), (0, 1), [28.2, 28.6, 29.0], 0.8 / math.sqrt(2), min_exit=0.0, min_tail=0.4, late=True)
    sdb, sda, scl = turned
    # down past DS1, then east between the 3V3 feed (y 73.75) and DS2: SCL at 75.6, SDA 76.0, SDB 76.4
    P.run("/I2C_SCL", [(16.3, 61.6)] + scl + [(29.0, 75.2), (29.4, 75.6), (49.4, 75.6), (49.8, 76.0), (49.8, 77.4)], W, B)
    P.run("/I2C_SDA", [(17.2, 62.05)] + sda + [(28.6, 75.6), (29.0, 76.0), (48.6, 76.0), (49.0, 76.4), (49.0, 78.0)], W, B)
    P.via("/I2C_SCL", 49.8, 77.4)                                           # on U1-U4's SCL line
    P.via("/I2C_SDA", 49.0, 78.0)                                           # on U1-U4's SDA line
    P.run("/LED_SDB", [(19.2, 62.05)] + sdb + [(28.2, 76.0), (28.6, 76.4), (33.1, 76.4), (33.5, 76.8), (33.5, 85.65),
                                                (33.9, 86.05), (38.1, 86.05)], W, B)
    P.via("/LED_SDB", 38.1, 86.05)                                          # by U1 PC13
    P.run("/LED_SDB", [(38.38, 87.16), (38.38, 86.33), (38.1, 86.05)], W)


# ---------------------------------------------------------------- B5.6 3V3
def v33():
    P.run("3V3", [(30.65, 74.84), (32.0, 74.84)], PW)                       # TP2 to the bottom feed
    P.via("3V3", 32.0, 74.84)
    P.run("3V3", [(32.0, 74.84), (32.0, 73.75)], PW, B)
    # TP2 down and under DS1/DS2's inner pads, across under DS2-DS3, then down the middle of the digits
    P.run("3V3", [(30.65, 74.84), (30.65, 77.36), (30.25, 77.76), (27.3, 77.76)], PW)
    P.via("3V3", 27.3, 77.76)
    P.run("3V3", [(27.3, 77.76), (27.3, 86.06)], PW, B)
    P.via("3V3", 27.3, 86.06)
    P.run("3V3", [(27.3, 86.06), (24.2, 86.06), (23.8, 86.46), (23.8, 103.6), (24.2, 104.0), (27.33, 104.0),
                  (27.73, 104.4), (27.73, 108.0), (27.73, 113.47), (27.73, 116.0), (27.73, 116.85), (27.73, 117.3),
                  (27.33, 117.7), (25.95, 117.7), (24.65, 119.0), (24.65, 120.8), (24.65, 122.16)], PW)
    P.run("3V3", [(24.65, 120.8), (22.75, 120.8)], PW)                      # C2
    P.via("3V3", 27.73, 116.85)                                             # under to U2's island (Rev A's link)
    P.run("3V3", [(27.73, 116.85), (30.0, 116.85), (30.65, 116.2)], PW, B)
    # FB2/C3 up over the I2C lines to the bottom feed
    P.run("3V3", [(36.1, 78.6), (36.1, 74.75)], 0.3)
    P.via("3V3", 36.1, 74.75)
    P.run("3V3", [(36.1, 74.75), (36.1, 74.15)], PW, B)
    # U1's north pins (U1.1, U1.48, C6): from the feed over the I2C lines, then down x 41.2
    P.via("3V3", 41.2, 73.75)
    P.run("3V3", [(41.2, 73.75), (41.2, 77.0)], PW)
    P.via("3V3", 41.2, 77.0)
    P.run("3V3", [(41.2, 77.0), (41.2, 85.5), (40.5, 86.2), (39.9, 86.2)], PW, B)
    P.via("3V3", 39.9, 86.2)


# ---------------------------------------------------------------- B5.7 encoder and RF_MODE
def enc_rf():
    VA, VB, VSW, VRF = (30.5, 87.65), (29.4, 88.1), (29.85, 89.3), (31.2, 89.65)
    P.run("/ENC_A", [(32.7, 87.84), (30.69, 87.84), VA])
    P.run("/ENC_B", [(32.7, 88.34), (29.64, 88.34), VB])
    P.run("/ENC_SW", [(32.7, 88.84), (30.31, 88.84), VSW])
    P.run("/RF_MODE", [(32.7, 89.84), (31.39, 89.84), VRF])
    for net, v in (("/ENC_A", VA), ("/ENC_B", VB), ("/ENC_SW", VSW), ("/RF_MODE", VRF)):
        P.via(net, *v)
    # bottom bus x 27.35 (B), 27.75 (SW), 28.15 (A), 28.55 (RF_MODE): more than 1 mm from BOOT0 at x 26.3
    P.run("/ENC_B", [VB, (27.35, 90.15), (27.35, 106.7), (26.95, 107.1)], W, B)
    P.run("/ENC_SW", [VSW, (27.75, 91.4), (27.75, 111.77), (26.95, 112.57)], W, B)
    P.run("/ENC_A", [VA, (30.5, 89.5), (28.15, 91.85), (28.15, 113.9), (26.95, 115.1)], W, B)
    P.run("/RF_MODE", [VRF, (28.55, 92.3), (28.55, 115.1)], W, B)
    for net, y, pad_y_ in (("/ENC_B", 107.1, 108.0), ("/ENC_SW", 112.57, 113.47), ("/ENC_A", 115.1, 116.0)):
        P.via(net, 26.95, y)
        P.run(net, [(26.95, y), (26.71, y + 0.24), (26.71, pad_y_), (24.89, pad_y_)])   # R3x.1 and SW4's terminal
    # RF_MODE over the 3V3 link, then Rev A's way to R17 and to TP4, SW1 and R18
    P.via("/RF_MODE", 28.55, 115.1)
    P.run("/RF_MODE", [(28.55, 115.1), (28.7, 115.25), (28.7, 117.95), (28.55, 118.1)])
    P.via("/RF_MODE", 28.55, 118.1)
    P.run("/RF_MODE", [(28.55, 118.1), (28.55, 126.4), (28.95, 126.8), (41.25, 126.8)], W, B)
    P.via("/RF_MODE", 41.25, 126.8)
    P.run("/RF_MODE", [(41.25, 126.8), (41.25, 129.5), (41.7, 129.95), (45.33, 129.95)])
    P.run("/RF_MODE", [(28.55, 126.4), (28.55, 127.8), (28.15, 128.2), (19.0, 128.2)], W, B)
    P.via("/RF_MODE", 19.0, 128.2)
    P.run("/RF_MODE", [(19.0, 121.1), (19.0, 125.85), (19.0, 128.2), (19.0, 129.6)])
    P.run("/RF_MODE", [(19.0, 125.85), (18.6, 126.25), (16.6, 126.25)])


# ---------------------------------------------------------------- B5.8 ground
def ground():
    for y in (64.67, 65.47, 66.27):     # U8's exposed pad, a column clear of the bottom bus
        P.via("GND", 18.6, y)
    # the bottom lines close in the pour under U8, so U8's ground (pin 39, joined to the exposed pad) runs up between
    # R_EXT and C43 to a via at the top edge, into the bottom pour between the edge and the SCL line; the top-edge
    # parts' ground pads join it there
    P.run("GND", [(18.0, 62.97), (18.0, 62.35), (17.9, 62.25), (17.9, 60.8), (17.7, 60.6)], FINE_W)
    P.via("GND", 17.7, 60.6, FINE_VIA)
    P.run("GND", [(17.03, 60.34), (17.44, 60.34), (17.7, 60.6)], FINE_W)        # R28.2
    P.run("GND", [(18.4, 60.39), (17.91, 60.39), (17.7, 60.6)], FINE_W)         # C43.2
    P.via("GND", 20.52, 60.6, FINE_VIA)
    P.run("GND", [(19.77, 60.34), (20.26, 60.34), (20.52, 60.6)], FINE_W)       # R29.2
    P.via("GND", 23.85, 60.55, FINE_VIA)
    P.run("GND", [(22.93, 60.55), (23.85, 60.55)], FINE_W)                      # C42.2
    # the north band's ground (SW3's resistors, TP3, U8 and the top-edge parts) reached the rest through Rev A's
    # stitching in the left column, which the digits now fill: by H1 the top pour is the north band's and the bottom
    # pour the rest's, so two stitching vias there join them
    P.via("GND", 26.2, 64.06)
    P.via("GND", 24.0, 63.4)
    # and where the top pour is the rest's and the bottom the north band's: under the LED lines (y 72.8) and beside
    # DS2's B pad (found by overlaying the two layers' pour pieces)
    for x in (36.5, 38.5, 40.5):
        P.via("GND", x, 72.75)
    P.via("GND", 23.56, 84.65)


# Rev A copper in the new lines' way: (net, kind, geometry) with kind "via" (x, y) or "seg" (x0, y0, x1, y1)
TAKE_UP = [
    ("VBUS", "seg", (25.6, 79.9, 27.9, 77.6)), ("VBUS", "seg", (27.9, 77.6, 32.3, 77.6)), ("VBUS", "via", (32.3, 77.6)),
    ("VBUS", "seg", (32.3, 77.6, 32.3, 70.3)),
    ("3V3", "seg", (36.1, 78.6, 36.1, 74.15)), ("3V3", "via", (36.1, 78.6)),
    ("GND", "seg", (29.66, 84.5, 29.66, 83.79)), ("GND", "via", (29.66, 83.79)),
    ("GND", "seg", (30.2, 86.92, 30.2, 85.29)), ("GND", "via", (30.2, 85.29)),
    ("GND", "seg", (27.12, 103.5, 27.12, 104.21)), ("GND", "via", (27.12, 104.21)),
] + [("GND", "via", v) for v in [(14.2, 61.06), (14.2, 64.06), (14.2, 67.06), (23.2, 64.06), (23.2, 67.06), (26.2, 64.06),
                                 (29.2, 61.06), (29.2, 64.06), (29.2, 67.06), (29.2, 88.06), (35.2, 76.06), (38.2, 76.06),
                                 (41.2, 76.06), (41.2, 79.06), (41.2, 82.06), (23.2, 103.06),
                                 (32.2, 79.06), (32.2, 82.06), (32.2, 85.06)]]   # the last three now join two islands
# (36.1, 78.6) stays a junction on the top: FB2/C3's 3V3 now leaves it upwards


def build():
    u8_top_bus()
    u8_bottom_bus()
    vbus()
    control()
    v33()
    enc_rf()
    ground()


def lay():
    import pcbnew
    mm = pcbnew.FromMM
    board = pcbnew.LoadBoard(BOARD)
    near = lambda a, b: abs(a - b) < 0.006
    gone, tracks, doomed = 0, list(board.GetTracks()), []   # (this build fails re-reading the list after a removal)
    for net, kind, g in TAKE_UP:
        hit = []
        for t in tracks:
            if t.GetNetname() != net:
                continue
            is_via = t.GetClass() == "PCB_VIA"
            if kind == "via" and is_via:
                p = t.GetPosition()
                if near(pcbnew.ToMM(p.x), g[0]) and near(pcbnew.ToMM(p.y), g[1]):
                    hit.append(t)
            elif kind == "seg" and not is_via:
                s, e = t.GetStart(), t.GetEnd()
                a = (pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))
                if all(near(u, v) for u, v in zip(a, g)) or all(near(u, v) for u, v in zip(a[2:] + a[:2], g)):
                    hit.append(t)
        if len(hit) != 1:
            sys.exit(f"take-up: {net} {kind} {g}: found {len(hit)}")
        doomed.append(hit[0])
    for t in doomed:
        board.Remove(t)
        gone += 1
    nets = {}

    def net(name):
        if name not in nets:
            n = board.FindNet(name) or board.FindNet("/" + name)   # sheet-local nets carry a leading /
            if n is None:
                sys.exit(f"no net {name}")
            nets[name] = n
        return nets[name]
    n_t = 0
    for name, layer, a, b, w in P.segments():
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
        t.SetWidth(mm(w))
        t.SetLayer(pcbnew.F_Cu if layer == T else pcbnew.B_Cu)
        t.SetNet(net(name))
        board.Add(t)
        n_t += 1
    for name, x, y, (d, h) in P.vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(d))
        v.SetDrill(mm(h))
        v.SetNet(net(name))
        board.Add(v)
    # the rule areas
    have = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetZoneName() == AREA]
    for z in have:
        board.Remove(z)
    for layers, pts in AREAS:
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetZoneName(AREA)
        ls = pcbnew.LSET()
        for l in layers:
            ls.AddLayer(pcbnew.F_Cu if l == T else pcbnew.B_Cu)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False)
        z.SetDoNotAllowZoneFills(False); z.SetDoNotAllowFootprints(False)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(mm(x), mm(y))
        board.Add(z)
    pcbnew.SaveBoard(BOARD, board)
    print(f"lay: {gone} Rev A items taken up; {n_t} tracks, {len(P.vias)} vias laid; {len(AREAS)} rule areas", flush=True)
    os._exit(0)


def to_json(path):
    col = {T: "#c0392b", B: "#2471a3"}
    out = [{"pts": list(map(list, pts)), "color": col[layer]} for net, layer, pts, w in P.runs]
    for net, x, y, (d, h) in P.vias:
        r = d / 2
        out.append({"pts": [[x - r, y], [x, y - r], [x + r, y], [x, y + r], [x - r, y]], "color": "#b7950b"})
    json.dump(out, open(path, "w"))


if __name__ == "__main__":
    build()
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "lay":
        lay()
    elif cmd == "json":
        to_json(sys.argv[2])
    else:
        print(__doc__)
