"""Steps 5.4-5.6: the RF lines, laid by hand on the top layer of the board open in KiCad (one undo step), then locked.
Lines run at the RF class's 0.92 mm (a 50 ohm grounded coplanar line on this stack, fab-rules.md) wherever there is room,
and neck down to the pin's own width over the last fraction of a millimetre at a 0.5 mm-pitch pin. At 88-108 MHz these
runs are far below a tenth of a wavelength (about 1.5 m in FR-4), so the necks and bends are electrically negligible
(docs/pcb-design-workflow.md conflict C9; KHA p190). The receiver's FMI side stays narrow (0.25 mm): AN383 counts
3-4 pF per inch of FMI trace against its input (p15, p17, p52). Bends are 45 degrees [ADI "Transmission Line Bends"].
Coordinates are the pads' own (read from the board), with the bends chosen clear of neighbours by at least 0.2 mm.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_rf.py [--only NET,NET] [--dry-run]"""
import sys

W, NECK = 0.92, 0.25
# net: [(points, width), ...] — each run is a polyline
RUNS = {
    # 5.5 transmit: U2 RF out -> C26 (DC block) -> U7 RF in
    "/LMX_RF": [([(44.500, 81.900), (44.500, 82.700), (44.635, 83.410)], 0.30)],
    # U7 at (48, 94) since phase 5; the bend starts 1.7 mm higher so U1's MICROWIRE lines can turn beside it
    "/ATT_IN": [([(44.635, 84.370), (44.635, 86.200), (47.250, 88.815), (47.250, 90.515)], W),
                ([(47.250, 90.515), (47.250, 92.025)], NECK)],
    # U7 RF out -> straight down, step left clear of U4, down to the filter's input (L2 pad 1, C28 pad 1)
    "/TX_RF_ATT": [([(47.250, 95.975), (47.250, 97.300)], NECK),
                   ([(47.250, 97.300), (47.250, 104.500), (42.932, 108.818), (42.932, 122.302)], W),
                   ([(42.932, 122.302), (44.443, 122.302)], W)],
    "/TX_LPF_MID": [([(42.932, 123.877), (42.932, 127.160)], W)],              # L2 pad 2, L3 pad 1, C29 pad 1 in line
    "/TX_RF": [([(44.508, 125.650), (44.508, 127.160)], W),                    # L3 pad 2 down to C30
               ([(44.508, 125.650), (45.100, 125.650)], W),
               ([(45.100, 125.650), (46.163, 125.650)], 0.35)],                # neck to U5 pin 3, clear of pin 2
    # 5.4 antenna: U5 pin 5 -> over D5's pad -> between J2's ground legs to its centre pin
    "/ANT": [([(47.837, 125.000), (48.700, 125.000), (48.900, 124.900)], 0.35),
             ([(48.900, 124.900), (50.200, 124.900), (52.100, 126.800), (54.990, 126.800)], W)],
    # 5.6 receive: U5 pin 1 -> C34 -> L1 (match) -> FB1 -> FMI, with C35 at the pin; narrow on the FMI side
    "/RX_RF": [([(46.163, 124.350), (46.642, 123.700), (46.642, 123.120)], 0.35)],
    "/FMI_MATCH": [([(46.642, 122.160), (46.642, 118.600), (47.600, 117.502), (48.247, 117.502), (48.247, 116.015)], NECK)],
    "/FMI": [([(48.247, 115.045), (47.750, 114.550), (47.750, 113.550)], NECK),
             ([(46.967, 115.030), (47.750, 114.550)], NECK)],
}


def main():
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    segs = [(net, a, b, w) for net, runs in RUNS.items() if not only or net in only for pts, w in runs for a, b in zip(pts, pts[1:])]
    print(f"{len(segs)} segments on {len(RUNS)} nets")
    if "--dry-run" in sys.argv:
        return
    from kipy import KiCad
    from kipy.board_types import Track
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    board = KiCad().get_board()
    nets = {n.name: n for n in board.get_nets()}
    items = []
    for net, (x0, y0), (x1, y1), w in segs:
        t = Track()
        t.start = Vector2.from_xy(round(x0 * 1e6), round(y0 * 1e6))
        t.end = Vector2.from_xy(round(x1 * 1e6), round(y1 * 1e6))
        t.width = round(w * 1e6)
        t.layer = BoardLayer.BL_F_Cu
        t.net = nets[net]
        t.locked = True
        items.append(t)
    c = board.begin_commit()
    board.create_items(items)
    board.push_commit(c, "Steps 5.4-5.6: RF lines")
    print("added")


if __name__ == "__main__":
    main()
