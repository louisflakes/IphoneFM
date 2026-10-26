"""Steps 5.4-5.6: the RF lines of floorplan B3, laid by hand on the top layer of the board open in KiCad (one undo
step), then locked, with ground stitching vias along both sides of the 50 ohm lines.
Lines run at the RF class's 0.92 mm (a 50 ohm grounded coplanar line with a 0.20 mm gap on this stack, fab-rules.md)
wherever there is room, and neck down to the pin's own width at fine-pitch pins. At 88-108 MHz every run is far below
a tenth of a wavelength (about 1.5 m in FR-4), so the necks and bends are electrically negligible
(docs/pcb-design-workflow.md conflict C9; KHA p190). The receiver's FMI side stays narrow (0.25 mm): AN383 counts
3-4 pF per inch of FMI trace against its input (p15, p17, p52). Bends are 45 degrees [ADI "Transmission Line Bends"].
  transmit  U2 RF out -> C26 (DC block) -> U7 (attenuator) -> L2/L3 low-pass (C28, C29, C30 shunts) -> U5 pin 3;
            the filter's output climbs past L2 and drops into U5's north side, since U5 turns its RF pins north;
  antenna   U5 pin 5 -> south, then east between J2's ground legs to its centre pin, with D5 hanging below the line;
  receive   U5 pin 1 -> north-east, up past H3's west side and up the right edge to C34 (DC block), about 40 mm of 50 ohm
            line with stitching vias on both sides [AN4169 p6, p11]; then L1 (shunt) and FB1 to U4's FMI, with C35 at it;
  switch    U5's supply (R16 feed) and control (C31 shunt, R17 from RF_MODE) leave straight south.
Coordinates are the pads' own (read from the board). PLACE holds the nudges this plan needs.
Usage (from the repository root, board open in KiCad):
  python tools/pcb_route_rf.py place | lay [--only NET,NET] [--dry-run]"""
import math
import sys

W, NECK = 0.92, 0.25
VIA, DRILL = 0.6, 0.3
STITCH_OFF, STITCH_PITCH = 1.1, 2.0   # stitching via centres: from the line's centre, and along it
STITCHED = ("/RX_RF", "/ANT")
# no stitching vias where the U7 control lanes (SW3 to U7) run beside the receive line's west side; that side keeps its
# ground pour, the east side keeps its vias (lane plan, 2026-10-25)
RESERVED = [[(46.0, 119.6), (49.4, 119.6), (49.4, 114.4), (53.1, 110.7), (53.1, 95.8), (49.8, 95.8), (49.8, 109.6),
             (46.0, 113.4)]]

# ref: (x, y, rotation) nudges for this plan
PLACE = {
    "U5": (47.0, 123.9, -90),     # up 1.1 mm: the antenna line turns east between J2's legs after a straight exit
    "C17": (40.03, 113.69, -90),  # left 0.135 mm, so C26 sits straight under U2's RF pin
    "C26": (41.3, 113.69, -90),
    "C28": (40.85, 121.42, 180),  # filter input shunt beside the attenuator's output line
    "C30": (44.5075, 127.64, -90),  # filter output shunt below L3 (back where it was)
    "C31": (47.7, 128.6, 0),      # control shunt beside the control line, under the antenna line
    "R17": (45.84, 129.95, 0),    # control series resistor at the foot of the control line; RF_MODE comes from the west
    "R16": (49.5, 126.55, 180),   # supply feed level with U5's supply line, above the antenna line
    "D5": (49.6, 128.65, -90),    # ESD diode just below the antenna line
    "L1": (55.187, 93.0, 0),      # match shunt with its pad 1 on the FMI_MATCH line
    "FB1": (53.15, 89.53, 90),    # under U4's FMI pin (U4's group sits 2.5 mm lower since the corner plan)
    "C35": (51.87, 89.525, -90),  # FMI shunt beside FB1
    "C34": (54.4, 96.64, 90),     # DC block at the top of the receive line
}

# net: [(points, width), ...] -- each run is a polyline; a line ends at a pad's centre, never just across it
RUNS = {
    "/LMX_RF": [([(41.3, 111.7), (41.3, 113.21)], 0.30)],
    "/ATT_IN": [([(41.3, 114.17), (41.3, 114.45), (42.05, 115.2)], 0.30),
                ([(42.05, 115.2), (42.05, 115.825)], NECK)],
    "/TX_RF_ATT": [([(42.05, 119.775), (42.05, 121.0)], NECK),
                   ([(42.05, 121.0), (42.05, 121.42), (42.932, 122.302)], W),
                   ([(42.05, 121.42), (41.33, 121.42)], 0.5)],                   # to C28
    "/TX_LPF_MID": [([(42.932, 123.877), (42.932, 125.65), (42.932, 127.16)], W)],  # L2 pad 2, L3 pad 1, C29 pad 1
    "/TX_RF": [([(44.508, 127.16), (44.508, 125.65), (44.508, 121.55), (45.008, 121.05), (45.85, 121.05), (46.35, 121.55)], W),
               ([(46.35, 121.55), (46.35, 123.062)], 0.35)],                     # into U5 pin 3 from the north
    "/ANT": [([(47.0, 124.738), (47.0, 127.05), (47.5, 127.55)], 0.35),
             ([(47.5, 127.55), (49.6, 127.55), (54.99, 127.55)], W),
             ([(49.6, 127.55), (49.6, 128.3)], 0.35)],                           # to D5
    "/U5_VDD": [([(47.65, 124.738), (47.65, 126.25), (47.95, 126.55), (48.99, 126.55)], NECK)],
    "/RF_CTRL": [([(46.35, 124.738), (46.35, 128.6), (46.35, 129.95)], NECK),
                 ([(46.35, 128.6), (47.22, 128.6)], NECK)],                      # to C31
    "/RX_RF": [([(47.65, 123.062), (47.65, 121.55)], 0.35),
               ([(47.65, 121.55), (50.2, 119.0), (50.2, 114.0), (54.4, 109.8), (54.4, 97.12)], W)],
    "/FMI_MATCH": [([(54.4, 96.16), (54.4, 93.0), (54.4, 91.5), (53.15, 90.25), (53.15, 90.015)], NECK)],
    "/FMI": [([(53.15, 89.045), (53.15, 87.55)], NECK),
             ([(53.15, 89.045), (51.87, 89.045)], NECK)],                       # to C35
}


def segments(only=None):
    return [(net, a, b, w) for net, runs in RUNS.items() if not only or net in only
            for pts, w in runs for a, b in zip(pts, pts[1:])]


def stitching(copper):
    """GND via sites along both sides of the 50 ohm runs, kept where they clear all other copper by 0.2 mm."""
    from shapely.geometry import LineString, Point, Polygon, box
    obst = []
    for kind, net, lay, g, name in copper:
        if net == "GND" and kind != "pad":
            continue
        if kind == "pad":
            x, y, hw, hh, shape, _ = g
            shp = Point(x, y).buffer(hw) if shape == "circle" else box(x - hw, y - hh, x + hw, y + hh)
            obst.append(shp.buffer(0.3) if not net else shp)   # holes: 0.5 mm hole to hole
        elif kind == "track":
            obst.append(LineString([g[:2], g[2:4]]).buffer(g[4]))
        else:
            obst.append(Point(g[0], g[1]).buffer(g[2]))
    obst += [LineString([a, b]).buffer(w / 2) for _, a, b, w in segments()]
    obst += [Polygon(p) for p in RESERVED]
    sites = []
    for net in STITCHED:
        for pts, w in RUNS[net]:
            if w < W:
                continue
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                L = math.hypot(x1 - x0, y1 - y0)
                ux, uy = (x1 - x0) / L, (y1 - y0) / L
                for k in range(int(L // STITCH_PITCH) + 1):
                    t = min(STITCH_PITCH / 2 + k * STITCH_PITCH, L)
                    for s in (1, -1):
                        x, y = x0 + ux * t - s * uy * STITCH_OFF, y0 + uy * t + s * ux * STITCH_OFF
                        v = Point(x, y).buffer(VIA / 2)
                        if all(v.distance(o) >= 0.2 for o in obst) and all(math.hypot(x - a, y - b) >= VIA + 0.5 for a, b in sites):
                            sites.append((round(x, 3), round(y, 3)))
    return sites


def plan(copper):
    """The planned tracks and vias, in tools/pcb_astar.board_copper's form, for pcb_quality.py and pcb_view.py."""
    out = [("track", net, {"F.Cu"}, (a[0], a[1], b[0], b[1], w / 2), "plan") for net, a, b, w in segments()]
    out += [("via", "GND", {"F.Cu", "B.Cu"}, (x, y, VIA / 2, DRILL / 2), "plan") for x, y in stitching(copper)]
    return out


def place():
    from kipy import KiCad
    from kipy.geometry import Vector2, Angle
    board = KiCad().get_board()
    fps = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
    for ref, (x, y, a) in PLACE.items():
        fps[ref].position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
        fps[ref].orientation = Angle.from_degrees(a)
    c = board.begin_commit()
    board.update_items([fps[r] for r in PLACE])
    board.push_commit(c, "Steps 5.4-5.6: RF parts nudged for the RF lines")
    print(f"placed {len(PLACE)} parts")


def lay():
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    sys.path.insert(0, "tools")
    from pcb_astar import board_copper
    from kipy import KiCad
    from kipy.board_types import Track, Via
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    board = KiCad().get_board()
    segs = segments(only)
    sites = stitching(board_copper(board.get_as_string())) if not only else []
    print(f"{len(segs)} segments, {len(sites)} stitching vias")
    if "--dry-run" in sys.argv:
        return
    nets = {n.name: n for n in board.get_nets()}
    mm = lambda v: round(v * 1e6)
    items = []
    for net, (x0, y0), (x1, y1), w in segs:
        t = Track()
        t.start, t.end = Vector2.from_xy(mm(x0), mm(y0)), Vector2.from_xy(mm(x1), mm(y1))
        t.width = mm(w)
        t.layer = BoardLayer.BL_F_Cu
        t.net = nets[net]
        t.locked = True
        items.append(t)
    for x, y in sites:
        v = Via()
        v.position = Vector2.from_xy(mm(x), mm(y))
        v.diameter, v.drill_diameter = mm(VIA), mm(DRILL)
        v.net = nets["GND"]
        v.locked = True
        items.append(v)
    c = board.begin_commit()
    board.create_items(items)
    board.push_commit(c, "Steps 5.4-5.6: RF lines")
    print("added")


if __name__ == "__main__":
    {"place": place, "lay": lay}[sys.argv[1]]()
