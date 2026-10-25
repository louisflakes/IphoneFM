"""Step 5.7 (planned in Phase 5 prep): the U4 corner, where the seven receiver lines from U1 reach U4 and its parts.
U1's east side gives them in the order RST, SCL, SDA, FS, SD, RCLK, SCK (north to south, after the 2026-10-25 swap of
RST to PB9 and RCLK to PB4). U4 takes them clockwise as SCK (west side), FS, SD (top, through R23 and R22),
RCLK, SDA, SCL (east side) and RST (bottom, with R19), so:
  SCK      leaves the bundle first, east into R24 on U4's west side;
  RCLK     drops to the bottom layer, runs under the pocket above U4 and comes up at an escape via beside pin 9;
  RST      drops to the bottom layer too, runs outside RCLK and comes up beside R19 below U4;
  FS / SD  swap within the bundle (FS dives under SD into RCLK's vacated lane), because SAI1 block B fixes FS on PB6
           above SD on PB5 while U4 has FS before SD;
  SDA/SCL  run east over the pocket and down the strip on U4's east side into pins 8 and 7; R21 hangs off SDA in the
           strip, R20 off SCL outside the corner, so neither pull-up needs a crossing.
The pocket above U4 holds the FS/SD series parts (C36, R23, R22) and U4's supply (FB3, C33, C32), with 3V3 by a via
from the bottom trunk along the east edge. Bus pitch 0.6 mm (the Clock class needs 0.4 mm between tracks).
Usage (from the repository root, board open in KiCad): python tools/pcb_route_u4.py lay [--dry-run]"""
import math
import sys

T, B = "F.Cu", "B.Cu"
W = 0.2
P = 0.6
VIA, DRILL = 0.6, 0.3
S2 = P * (2 - math.sqrt(2))  # how much longer each next line out runs before its 45-degree bend, so bends stay concentric

# band lanes northbound along U4's west side (x), runs eastbound over the pocket (y)
LANE = dict(RST=45.5, SCL=46.1, SDA=46.7, FS=47.3, SD=47.9, RCLK=48.5, SCK=49.1)
RUN = dict(SCL=77.4, SDA=78.0, SD=78.6, FS=79.2)
Y0 = 88.0  # where this plan picks the band up


def turn_ne(x, y_run, k):
    """Points of a northbound lane at x turning east onto y_run, k lines in from the inside of the bend."""
    e = 0.4 + k * S2
    return [(x, y_run + e), (x + e, y_run)]


def runs():
    r = []
    # SCK: north, then into R24 on U4's west; R24 to pin 17
    r += [("/RX_SCK_MCU", T, [(LANE["SCK"], Y0), (LANE["SCK"], 84.0), (49.71, 83.39), (50.75, 83.39)], W),
          ("/RX_SCK", T, [(50.75, 84.41), (51.59, 85.25), (52.35, 85.25)], W)]
    # GPO caps on U4's west side
    # GPO caps beside U4's west side, one above the other
    r += [("/RX_GPO2", T, [(52.35, 85.75), (50.83, 85.75)], W),
          ("/RX_GPO1", T, [(52.35, 86.25), (51.68, 86.25), (50.83, 87.1)], W)]
    # RCLK: dive, bottom under the pocket, escape via beside pin 9
    r += [("/RX_RCLK", T, [(LANE["RCLK"], Y0), (LANE["RCLK"], 82.6)], W),
          ("/RX_RCLK", B, [(LANE["RCLK"], 82.6), (56.2, 82.6), (56.6, 83.0), (56.6, 85.45)], W),
          ("/RX_RCLK", T, [(56.6, 85.45), (56.3, 85.75), (55.45, 85.75)], W)]
    # RST: dive, bottom outside RCLK, up beside R19; R19 to pin 5
    r += [("/RX_RST", T, [(LANE["RST"], Y0), (LANE["RST"], 82.0)], W),
          ("/RX_RST", B, [(LANE["RST"], 82.0), (56.95, 82.0), (57.35, 82.4), (57.35, 89.02)], W),
          ("/RX_RST", T, [(57.35, 89.02), (54.65, 89.02)], W),
          ("/RX_RST", T, [(54.65, 89.02), (54.65, 87.55)], W)]
    # FS under SD: FS dives in its lane, SD steps west into it, FS comes up in SD's old lane (RCLK has left by then)
    fs_x, sd_x = LANE["SD"], LANE["FS"]
    r += [("/RX_FS_MCU", T, [(LANE["FS"], Y0), (LANE["FS"], 81.2)], W),
          ("/RX_FS_MCU", B, [(LANE["FS"], 81.2), (fs_x, 80.6), (fs_x, 79.9)], W)]
    sd = [(LANE["SD"], Y0), (LANE["SD"], 80.8), (sd_x, 80.2)] + turn_ne(sd_x, RUN["SD"], 1)
    fs = [(fs_x, 79.9)] + turn_ne(fs_x, RUN["FS"], 0)
    r += [("/RX_SD_MCU", T, sd + [(52.36, RUN["SD"]), (52.76, RUN["SD"] + 0.4), (52.76, 80.09)], W),
          ("/RX_FS_MCU", T, fs + [(50.1, RUN["FS"]), (51.03, RUN["FS"]), (51.43, RUN["FS"] + 0.4), (51.43, 80.09)], W),
          ("/RX_FS_MCU", T, [(50.1, RUN["FS"]), (50.1, 80.12)], W)]                     # to C36
    # SDA and SCL: north, east over the pocket, down the strip into pins 8 and 7
    sda_x, scl_x = 57.4, 58.0
    r += [("/I2C_SDA", T, [(LANE["SDA"], Y0)] + turn_ne(LANE["SDA"], RUN["SDA"], 2)
           + [(sda_x - 0.4, RUN["SDA"]), (sda_x, RUN["SDA"] + 0.4), (sda_x, 85.85), (57.0, 86.25), (55.45, 86.25)], W),
          ("/I2C_SDA", T, [(sda_x, 81.11), (56.75, 81.11)], W)]                          # to R21
    e = 0.4 + S2
    r += [("/I2C_SCL", T, [(LANE["SCL"], Y0)] + turn_ne(LANE["SCL"], RUN["SCL"], 3)
           + [(scl_x - e, RUN["SCL"]), (scl_x, RUN["SCL"] + e), (scl_x, 86.75 - (scl_x - 57.0 - 0.349)),
              (57.0 + 0.349, 86.75), (55.45, 86.75)], W),
          ("/I2C_SCL", T, [(57.0, RUN["SCL"]), (57.0, 76.4)], W)]                        # to R20
    # FS and SD from their series resistors to U4
    r += [("/RX_FS", T, [(51.43, 81.11), (51.43, 83.53), (52.65, 84.75)], W),
          ("/RX_SD", T, [(52.76, 81.11), (52.76, 82.61), (53.15, 83.0), (53.15, 84.45)], W)]
    # U4's supply: 3V3 by via to FB3 and R21; RX_VDD to C33, C32, pin 11 and across to pin 10
    r += [("3V3", T, [(55.42, 79.2), (55.42, 80.115)], 0.3),
          ("3V3", T, [(55.42, 80.115), (56.75, 80.115)], 0.3),
          ("RX_VDD", T, [(54.09, 81.085), (55.42, 81.085)], 0.3),
          ("RX_VDD", T, [(55.42, 81.085), (55.15, 81.355), (55.15, 82.6)], 0.3),
          ("RX_VDD", T, [(55.15, 82.6), (55.15, 84.75)], 0.25),
          ("RX_VDD", T, [(55.15, 84.75), (55.15, 85.25), (55.45, 85.25)], 0.2)]
    return r


VIAS = [("/RX_RCLK", 48.5, 82.6), ("/RX_RCLK", 56.6, 85.45), ("/RX_RST", 45.5, 82.0), ("/RX_RST", 57.35, 89.02),
        ("/RX_FS_MCU", 47.3, 81.2), ("/RX_FS_MCU", 47.9, 79.9), ("3V3", 55.42, 79.2), ("3V3", 58.02, 75.6)]
EXTRA = [("3V3", T, [(58.02, 75.6), (58.02, 76.4)], 0.3)]                              # R20's 3V3 via


def segments():
    out = []
    for net, layer, pts, w in runs() + EXTRA:
        for a, b in zip(pts, pts[1:]):
            if a != b:
                out.append((net, layer, a, b, w))
    return out


def plan(copper=None):
    out = [("track", n, {l}, (a[0], a[1], b[0], b[1], w / 2), "plan") for n, l, a, b, w in segments()]
    out += [("via", n, {T, B}, (x, y, VIA / 2, DRILL / 2), "plan") for n, x, y in VIAS]
    return out


def lay():
    from kipy import KiCad
    from kipy.board_types import Track, Via
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    board = KiCad().get_board()
    nets = {n.name: n for n in board.get_nets()}
    mm = lambda v: round(v * 1e6)
    items = []
    for net, layer, (x0, y0), (x1, y1), w in segments():
        t = Track()
        t.start, t.end = Vector2.from_xy(mm(x0), mm(y0)), Vector2.from_xy(mm(x1), mm(y1))
        t.width, t.layer, t.net = mm(w), BoardLayer.BL_F_Cu if layer == T else BoardLayer.BL_B_Cu, nets[net]
        items.append(t)
    for net, x, y in VIAS:
        v = Via()
        v.position = Vector2.from_xy(mm(x), mm(y))
        v.diameter, v.drill_diameter, v.net = mm(VIA), mm(DRILL), nets[net]
        items.append(v)
    print(f"{len(items)} items")
    if "--dry-run" in sys.argv:
        return
    c = board.begin_commit()
    board.create_items(items)
    board.push_commit(c, "Step 5.7: U4 corner")


if __name__ == "__main__":
    {"lay": lay}[sys.argv[1]]()
