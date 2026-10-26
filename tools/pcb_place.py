"""Phase 4: places named parts by hand at given positions and turns, live in the board open in KiCad (one undo step),
for the few parts pcb_local.py can't place (a part with no local_to, or one that belongs in a line rather than at a
pin). Each placement's reason goes in kicad-build-procedure.md.
Usage (from the repository root, board open in KiCad): python tools/pcb_place.py REF=X,Y,ROT [REF=X,Y,ROT ...]"""
import sys


def main():
    from kipy import KiCad
    from kipy.geometry import Vector2, Angle
    board = KiCad().get_board()
    fps = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
    items = []
    for arg in sys.argv[1:]:
        ref, spec = arg.split("=")
        x, y, a = (float(v) for v in spec.split(","))
        fps[ref].position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
        fps[ref].orientation = Angle.from_degrees(a)
        items.append(fps[ref])
        print(f"{ref:4} ({x:7.3f}, {y:7.3f}) {a:4.0f} deg")
    c = board.begin_commit()
    board.update_items(items)
    board.push_commit(c, "Place " + ", ".join(a.split("=")[0] for a in sys.argv[1:]))


if __name__ == "__main__":
    main()
