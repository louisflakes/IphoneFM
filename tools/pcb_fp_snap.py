"""Step 7.1: footprints turned through the API can keep 1 nm of rounding in their pads and graphics (0.799999 for 0.8),
which DRC reports as "does not match copy in library". Every point of the named footprints on the board is put back
on a 100 nm grid; the library coordinates and the placements are all multiples of 100 nm, so this restores them
exactly.
Usage (from the repository root, board open in KiCad): python tools/pcb_fp_snap.py REF[,REF...]"""
import sys

GRID = 100   # nm


def snap(msg):
    """Rounds every x_nm/y_nm pair in a protobuf message, recursively."""
    n = 0
    for field, value in msg.ListFields():
        if field.message_type is None:
            continue
        items = value if field.label == field.LABEL_REPEATED else [value]
        for v in items:
            names = {f.name for f in v.DESCRIPTOR.fields}
            if {"x_nm", "y_nm"} <= names:
                x, y = round(v.x_nm / GRID) * GRID, round(v.y_nm / GRID) * GRID
                n += (x, y) != (v.x_nm, v.y_nm)
                v.x_nm, v.y_nm = x, y
            else:
                n += snap(v)
    return n


if __name__ == "__main__":
    from kipy import KiCad
    refs = sys.argv[1].split(",")
    board = KiCad().get_board()
    fps = [f for f in board.get_footprints() if f.reference_field.text.value in refs]
    for f in fps:
        moved = sum(snap(it.proto) for it in f.definition.items)
        print(f"{f.reference_field.text.value}: {moved} points snapped")
    commit = board.begin_commit()
    board.update_items(fps)
    board.push_commit(commit, "Step 7.1: footprint points back on the library grid")
    board.save()
