"""Phase 5: lays U1's up-going right-side lines by hand on the board open in KiCad (one undo step), then locks them.
Seven lines leave pins 25-31 and run up between U1 and the transmit line as one bus, then turn up-left together:
- MICROWIRE (pins 28 MUX, 27 CLK, 26 DATA, 25 LE, reordered 2026-10-24 so they reach U2's pins 10-13 in order with
  no crossing) runs straight into U2's bottom pins;
- the FSK lines (pins 31 DATA, 30 FS, 29 CLK) run into R8, R7, R6, standing in a row above U1's top-right corner,
  then drop to the bottom layer and enter U2's left side through the entry vias at x 39.25 (C14's 3V3 link blocks
  the top layer there). FSK_CLK comes in from the east, the other two from the west, so nothing crosses.
- USB D+/D-, SWDIO and SWCLK go the other way (down to U6 and the SWD pads), so they drop to the bottom layer through
  vias beside pins 32-37 and come back up just below the bus; pcb_astar.py routes them on from those vias. U6's two
  identical channels (D- on I/O1, D+ on I/O2) and the SWD pads' places (TP8 SWDIO west of TP7 SWCLK) are chosen so the
  four lines reach them in the order they leave U1.
Spacing: 0.4 mm centre to centre between plain lines, 0.6 mm next to a clock line (FSK_CLK, LMX_CLK); segments that
start inside U1's or U2's courtyard keep the escape exemption in IphoneFM.kicad_dru. The bends are 45 degrees and the
diagonals are parallel (equal x - y per line), with the outer line 0.5 mm clear of ATT_IN's bend.
Usage (from the repository root, board open in KiCad): python tools/pcb_lay_u1right.py [--dry-run]"""
import sys

S = 0.2
# R6-R8 upright in a row, pin 1 (the U1 side) at the bottom
PARTS = {"R8": (37.6, 85.0, 90), "R7": (38.9, 85.0, 90), "R6": (40.2, 85.0, 90)}
# net: (layer, points) runs
TRACKS = {
    "/FSK_DATA_MCU": [("F", [(39.4375, 93.75), (42.0, 93.75), (42.0, 89.68), (37.8, 85.48), (37.6, 85.48)])],
    "/FSK_FS_MCU": [("F", [(39.4375, 94.25), (42.4, 94.25), (42.4, 89.51), (38.9, 86.01), (38.9, 85.48)])],
    "/FSK_CLK_MCU": [("F", [(39.4375, 94.75), (43.0, 94.75), (43.0, 89.25), (40.2, 86.45), (40.2, 85.48)])],
    "/LMX_MUX": [("F", [(39.4375, 95.25), (39.85, 95.25), (39.95, 95.35), (43.6, 95.35), (43.6, 88.99), (40.9, 86.29), (40.9, 83.1), (41.0, 83.0), (41.0, 81.9)])],
    "/LMX_CLK": [("F", [(39.4375, 95.75), (44.2, 95.75), (44.2, 88.72), (41.5, 86.02), (41.5, 81.9)])],
    "/LMX_DATA": [("F", [(39.4375, 96.25), (39.85, 96.25), (39.95, 96.35), (44.8, 96.35), (44.8, 88.46), (42.0, 85.66), (42.0, 81.9)])],
    "/LMX_LE": [("F", [(39.4375, 96.75), (45.2, 96.75), (45.2, 88.28), (42.5, 85.58), (42.5, 81.9)])],
    # after the resistors: up to a via, then the bottom layer to U2's entry vias
    "/FSK_DATA": [("F", [(37.6, 84.52), (37.6, 83.75)]),
                  ("B", [(37.6, 83.75), (37.6, 83.35), (38.3, 82.65), (38.3, 79.75), (38.6, 79.45), (39.25, 79.45)])],
    "/FSK_FS": [("F", [(38.9, 84.52), (38.9, 83.75)]),
                ("B", [(38.9, 83.75), (38.9, 80.65), (39.25, 80.3)])],
    "/FSK_CLK": [("F", [(40.2, 84.52), (40.2, 83.75)]),
                 ("B", [(40.2, 83.75), (40.2, 78.95), (39.9, 78.65), (39.25, 78.65)])],
}
# USB D+/D-, SWDIO and SWCLK cross under the bus: short top-layer stubs to vias beside pins 32-37, placed by hand
# (three 0.6 mm vias between 0.5 mm-pitch pins need the stagger); pcb_astar.py routes on from the vias
TRACKS.update({
    "/SWCLK": [("F", [(38.75, 90.5625), (38.75, 90.5), (40.05, 90.5)])],
    "/SWDIO": [("F", [(39.4375, 92.25), (40.05, 92.25), (40.4, 91.9)])],
    "/USB_DP": [("F", [(39.4375, 92.75), (40.2, 92.75), (40.425, 92.525), (41.4, 92.525)])],
    "/USB_DM": [("F", [(39.4375, 93.25), (40.65, 93.25), (40.75, 93.15)])],
})
POCKET = {"/SWCLK": (40.05, 90.5), "/SWDIO": (40.4, 91.9), "/USB_DP": (41.4, 92.525), "/USB_DM": (40.75, 93.15)}
VIAS = {"/FSK_DATA": [(37.6, 83.75)], "/FSK_FS": [(38.9, 83.75)], "/FSK_CLK": [(40.2, 83.75)], **{n: [p] for n, p in POCKET.items()}}


def main():
    n = sum(len(p) - 1 for runs in TRACKS.values() for _, p in runs)
    print(f"{n} segments, {sum(map(len, VIAS.values()))} vias, {len(PARTS)} parts")
    if "--dry-run" in sys.argv:
        return
    from kipy import KiCad
    from kipy.board_types import Track, Via
    from kipy.geometry import Vector2, Angle
    from kipy.proto.board.board_types_pb2 import BoardLayer
    board = KiCad().get_board()
    nets = {x.name: x for x in board.get_nets()}
    v = lambda x, y: Vector2.from_xy(round(x * 1e6), round(y * 1e6))
    fps = {f.reference_field.text.value: f for f in board.get_footprints()}
    moved = []
    for ref, (x, y, a) in PARTS.items():
        fps[ref].position, fps[ref].orientation = v(x, y), Angle.from_degrees(a)
        moved.append(fps[ref])
    items = []
    for net, runs in TRACKS.items():
        for layer, pts in runs:
            for p, q in zip(pts, pts[1:]):
                t = Track()
                t.start, t.end, t.width = v(*p), v(*q), round(S * 1e6)
                t.layer = BoardLayer.BL_F_Cu if layer == "F" else BoardLayer.BL_B_Cu
                t.net, t.locked = nets[net], True
                items.append(t)
    for net, pts in VIAS.items():
        for p in pts:
            w = Via()
            w.position, w.diameter, w.drill_diameter = v(*p), 600000, 300000
            w.net, w.locked = nets[net], True
            items.append(w)
    c = board.begin_commit()
    board.update_items(moved)
    board.create_items(items)
    board.push_commit(c, "U1 right side: bus, R6-R8 row, FSK entry")
    print("laid")


if __name__ == "__main__":
    main()
