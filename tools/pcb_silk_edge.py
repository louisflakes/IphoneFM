"""Step 7.1: the parts that overhang the board edge (the three dials, SW3, J1 and J2) carry silkscreen outlines past
it, which the board house clips. Each silkscreen line of a placed footprint is cut back to 0.2 mm inside the edge
(Board Setup's silk clearance, plus half the line width); lines wholly outside are removed. The library footprints
are left as they are; only the parts on this board change.
Usage (from the repository root, board open in KiCad): python tools/pcb_silk_edge.py [list] | lay"""
import sys

from shapely.geometry import LineString, box

BOARD = (12.7, 59.56, 59.15, 130.96)
GAP = 0.2 + 0.02


def plan(board):
    from kipy.board_types import BoardLayer, BoardShape
    silk = (BoardLayer.BL_F_SilkS, BoardLayer.BL_B_SilkS)
    changed = {}
    for f in board.get_footprints():
        keep, cut, dropped = [], 0, 0
        for it in f.definition.items:
            if isinstance(it, BoardShape) and it.layer in silk and it.proto.shape.WhichOneof("geometry") == "segment":
                s = it.proto.shape.segment
                w = it.proto.shape.attributes.stroke.width.value_nm / 1e6
                m = GAP + w / 2
                inside = box(BOARD[0] + m, BOARD[1] + m, BOARD[2] - m, BOARD[3] - m)
                a, b = (s.start.x_nm / 1e6, s.start.y_nm / 1e6), (s.end.x_nm / 1e6, s.end.y_nm / 1e6)
                line = LineString([a, b])
                if not inside.contains(line):
                    part = line.intersection(inside)
                    if part.is_empty or part.length < 0.2:
                        dropped += 1
                        continue
                    (x0, y0), (x1, y1) = part.coords[0], part.coords[-1]
                    s.start.x_nm, s.start.y_nm = round(x0 * 1e6), round(y0 * 1e6)
                    s.end.x_nm, s.end.y_nm = round(x1 * 1e6), round(y1 * 1e6)
                    cut += 1
            keep.append(it)
        if cut or dropped:
            f.definition.items = keep
            changed[f.reference_field.text.value] = (f, cut, dropped)
    return changed


if __name__ == "__main__":
    from kipy import KiCad
    B = KiCad().get_board()
    C = plan(B)
    for ref, (f, cut, dropped) in sorted(C.items()):
        print(f"{ref}: {cut} lines cut back, {dropped} removed")
    if len(sys.argv) > 1 and sys.argv[1] == "lay" and C:
        commit = B.begin_commit()
        B.update_items([f for f, c, d in C.values()])
        B.push_commit(commit, "Step 7.1: silkscreen cut back from the board edge")
        B.save()
        print("laid and saved")
