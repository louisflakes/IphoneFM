"""Phase 5: finds a place for U1's FSK series resistors R6-R8 where every line on U1's right side routes. For each
candidate place of the three resistors it routes, on the board open in KiCad: USB D+ and D- to U6, SWDIO to TP8,
U1 to R6-R8 (FSK_*_MCU), R6-R8 to their entry vias at U2 (FSK_*), and the four MICROWIRE lines to U2; scores the
result (connections routed, then vias, then length), and undoes it before the next try. The resistors only need to be
somewhere along these short lines: 15 mm is electrically short at I2S speeds, and TI's evaluation board keeps its FSK
resistors well away from the chip (SNAS654A p55).
Usage (from the repository root, board open in KiCad): python tools/pcb_try_r678.py [--apply N]"""
import sys

sys.path.insert(0, "tools")
from pcb_astar import route
from pcb_group import courtyard
from pcb_local import turned_box

# candidate places: {ref: (x, y, turn)}; R6 carries FSK_CLK (pin 29), R7 FSK_FS (pin 30), R8 FSK_DATA (pin 31)
CANDIDATES = {
    "now (first ring)": None,
    "box NE, flat, x41": {"R8": (41.0, 86.0, 0), "R7": (41.0, 87.3, 0), "R6": (41.0, 88.6, 0)},
    "box NE, flat, x40.2": {"R8": (40.2, 86.0, 0), "R7": (40.2, 87.3, 0), "R6": (40.2, 88.6, 0)},
    "box NE, upright, y87": {"R8": (40.4, 87.2, 90), "R7": (41.7, 87.2, 90), "R6": (43.0, 87.2, 90)},
    "east ring, x43.4": {"R8": (43.4, 92.96, 0), "R7": (43.4, 94.25, 0), "R6": (43.4, 95.54, 0)},
    "south-east, upright": {"R8": (41.0, 98.3, 90), "R7": (42.3, 98.3, 90), "R6": (43.6, 98.3, 90)},
}
LINES = [
    ("/SWDIO", "U1.34", "TP8.1"), ("/USB_DP", "U1.33", "U6.1"), ("/USB_DM", "U1.32", "U6.3"),
    ("/FSK_DATA_MCU", "U1.31", "R8.1"), ("/FSK_FS_MCU", "U1.30", "R7.1"), ("/FSK_CLK_MCU", "U1.29", "R6.1"),
    ("/FSK_DATA", "39.25,79.45", "R8.2"), ("/FSK_FS", "39.25,80.3", "R7.2"), ("/FSK_CLK", "39.25,78.65", "R6.2"),
    ("/LMX_LE", "U1.25", "U2.13"), ("/LMX_CLK", "U1.26", "U2.11"), ("/LMX_MUX", "U1.27", "U2.10"), ("/LMX_DATA", "U1.28", "U2.12"),
]
ORDERS = {"out-group first": LINES, "MICROWIRE first": LINES[9:] + LINES[:9]}


def clear(board):
    """Remove these lines' routes, keeping the hand-placed FSK entry vias and their stubs at U2."""
    nets = {n for n, _, _ in LINES}
    keep = lambda x, y: abs(x - 39.25e6) < 1e3 or (abs(x - 39.4e6) < 1e3) or (abs(x - 39.5e6) < 1e3)
    tr = [t for t in board.get_tracks() if t.net.name in nets and not (t.net.name.startswith("/FSK_") and not t.net.name.endswith("_MCU") and keep(t.start.x, t.start.y) and t.end.x <= 40.11e6)]
    vi = [v for v in board.get_vias() if v.net.name in nets and not (v.net.name.startswith("/FSK_") and abs(v.position.x - 39.25e6) < 1e3)]
    if tr or vi:
        c = board.begin_commit(); board.remove_items(tr + vi); board.push_commit(c, "Clear U1 right-side lines")


def place(board, where):
    from kipy.geometry import Vector2, Angle
    fps = {f.reference_field.text.value: f for f in board.get_footprints()}
    items = []
    for ref, (x, y, a) in where.items():
        f = fps[ref]
        f.position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
        f.orientation = Angle.from_degrees(a)
        items.append(f)
    c = board.begin_commit(); board.update_items(items); board.push_commit(c, "Try R6-R8 place")


def overlaps(board, where):
    fps = {f.reference_field.text.value: f for f in board.get_footprints()}
    box = lambda r, x, y, a: (lambda b: (x + b[0], y + b[1], x + b[2], y + b[3]))(turned_box(courtyard(fps[r].definition.id.name), a))
    mine = {r: box(r, *v) for r, v in where.items()}
    hits = []
    for r, f in fps.items():
        if r in where:
            continue
        o = box(r, f.position.x / 1e6, f.position.y / 1e6, f.orientation.degrees)
        for m, b in mine.items():
            if b[0] < o[2] + 0.3 and o[0] < b[2] + 0.3 and b[1] < o[3] + 0.3 and o[1] < b[3] + 0.3:
                hits.append(f"{m}/{r}")
    return hits


def trial(board, lines):
    made, ok, vias, length, failed = [], 0, 0, 0.0, []
    for net, a, z in lines:
        r = route(board, net, a, z, 0.2, "FB", margin=14)
        if r:
            ok += 1; vias += len(r[1]); length += r[2]; made += r[3]
        else:
            failed.append(net)
    return ok, vias, length, failed, made


def main():
    from kipy import KiCad
    board = KiCad().get_board()
    fps = {f.reference_field.text.value: f for f in board.get_footprints()}
    home = {r: (fps[r].position.x / 1e6, fps[r].position.y / 1e6, fps[r].orientation.degrees) for r in ("R6", "R7", "R8")}
    clear(board)
    results = []
    for name, where in CANDIDATES.items():
        where = where or home
        hits = overlaps(board, where) if where is not home else []
        if hits:
            print(f"{name:24} skipped, courtyards meet: {hits}", flush=True)
            continue
        place(board, where)
        for oname, lines in ORDERS.items():
            ok, vias, length, failed, made = trial(board, lines)
            results.append((ok, -vias, -length, name, oname))
            print(f"{name:24} {oname:16} routed {ok}/{len(lines)}  vias {vias:2}  {length:6.1f} mm  failed {failed}", flush=True)
            if made:
                c = board.begin_commit(); board.remove_items(made); board.push_commit(c, "Undo trial")
    place(board, home)
    best = max(results)
    print("best:", best[3], "/", best[4], f"routed {best[0]}, vias {-best[1]}, {-best[2]:.1f} mm")


if __name__ == "__main__":
    main()
