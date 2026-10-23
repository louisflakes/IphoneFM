"""Step 4.2: groups the Rev A parts beside the board, each IC with the parts that sit at its pins (netlist.json's local_to),
so Phase 4 can place a group at a time with short pin-to-pin distances. Works on the board open in KiCad through its API
(the move shows live and is one undo step); KiCad saves it. Groups for the right half of the board stand to the right of
it, top to bottom in the order they sit on the sketch; the controls stand to the left; test pads and mounting holes
below. Within a group the IC comes first and its parts follow in pin order, in a grid beside it.
Usage (from the repository root, with the board open in KiCad's PCB editor): python tools/pcb_group.py [--dry-run]"""
import json
import math
import re
import sys

sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid

LIB = "kicad/rev-a/IphoneFM.pretty/"
BOARD = (12.70, 59.56, 59.15, 130.96)  # outline, layout.html ENVELOPE
GAP = 0.6  # mm between courtyards inside a group
GROUP_GAP = 4.0  # mm between groups

# Each group: its lead parts (placed first, in a row), then every part local to one of them (from netlist.json)
RIGHT = [("U2 synthesizer", ["U2"]), ("Y2 reference", ["Y2"]), ("U7 attenuator", ["U7", "SW3"]), ("U1 MCU", ["U1"]),
         ("U4 receiver", ["U4", "L1"]), ("U3 regulator", ["U3"]), ("J1 USB", ["J1", "U6"]),
         ("TX filter and switch", ["U5", "J2", "L2", "L3", "C29"])]
LEFT = [("Controls", ["RV1", "RV2", "RV3", "SW1", "SW2", "D1"])]
BELOW = [("Test pads", ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8"]), ("Mounting holes", ["H1", "H2", "H3", "H4"])]


def courtyard(lib_name):
    """Courtyard box (x0, y0, x1, y1) of a library footprint at rotation 0, from its F.CrtYd graphics."""
    fp = sexpr(open(LIB + lib_name + ".kicad_mod", encoding="utf-8").read())
    xs, ys = [], []
    for g in fp[1:]:
        if not (isinstance(g, list) and g[0] in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly")):
            continue
        if kid(g, "layer")[1] != "F.CrtYd":
            continue
        if g[0] == "fp_circle":
            (cx, cy), (ex, ey) = (tuple(map(float, kid(g, k)[1:3])) for k in ("center", "end"))
            r = math.hypot(ex - cx, ey - cy)
            xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
            continue
        pts = [kid(g, k) for k in ("start", "mid", "end") if kid(g, k)] or kid(g, "pts")[1:]
        for p in pts:
            xs.append(float(p[1])); ys.append(float(p[2]))
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (-0.5, -0.5, 0.5, 0.5)


def pin_key(local_to):
    """Sort key for a local_to like 'U2.25' or 'J1.A5': the pin number where there is one."""
    pin = local_to.split(".")[1] if "." in local_to else ""
    num = re.sub(r"\D", "", pin)
    return (int(num) if num else 0, pin)


def groups():
    parts = json.load(open("design/rev-a/netlist.json", encoding="utf-8"))["parts"]
    local = {p["ref"]: p.get("local_to", "") for p in parts}
    out, taken = [], set()
    for side, defs in (("right", RIGHT), ("left", LEFT), ("below", BELOW)):
        for name, leads in defs:
            members = [r for r in local if r not in leads and r not in taken and local[r].split(".")[0] in leads]
            # a part local to a member (C25 at R5) follows that member
            members += [r for r in local if r not in leads and r not in taken and r not in members and local[r].split(".")[0] in members]
            members.sort(key=lambda r: (leads.index(local[r].split(".")[0]) if local[r].split(".")[0] in leads else len(leads), pin_key(local[r])))
            taken.update(leads + members)
            out.append((side, name, leads, members))
    missing = set(local) - taken
    if missing:
        sys.exit(f"parts in no group: {sorted(missing)}")
    return out


def layout(lib_of):
    """Position (x, y) in mm of every part, keyed by reference."""
    box = {r: courtyard(lib_of[r]) for r in lib_of}
    w = lambda r: box[r][2] - box[r][0]
    h = lambda r: box[r][3] - box[r][1]
    pos = {}

    def place_group(x0, y0, leads, members):
        """Leads in a row from (x0, y0) top-left, members in a grid to their right; returns the group's width and height."""
        x, top = x0, y0
        lead_h = max(h(r) for r in leads)
        for r in leads:
            pos[r] = (x - box[r][0], top - box[r][1])
            x += w(r) + GAP
        if members:
            cw = max(w(r) for r in members) + GAP
            ch = max(h(r) for r in members) + GAP
            rows = max(2, int((lead_h + GAP) // ch))
            for i, r in enumerate(members):
                cx = x + (i // rows) * cw
                cy = top + (i % rows) * ch
                pos[r] = (cx - box[r][0], cy - box[r][1])
            x += math.ceil(len(members) / rows) * cw
            lead_h = max(lead_h, min(rows, len(members)) * ch)
        return x - x0, lead_h

    x0, y0, x1, y1 = BOARD
    y = y0
    for side, name, leads, members in [g for g in GROUPS if g[0] == "right"]:
        _, gh = place_group(x1 + 10, y, leads, members)
        y += gh + GROUP_GAP
    # controls: to the left, ending 12 mm short of the board's left edge (the wheels will hang 2.9 mm past it)
    for side, name, leads, members in [g for g in GROUPS if g[0] == "left"]:
        gw, _ = place_group(0, y0, leads, members)
        for r in leads + members:
            pos[r] = (pos[r][0] - gw + x0 - 12, pos[r][1])
    y = y1 + 10
    for side, name, leads, members in [g for g in GROUPS if g[0] == "below"]:
        _, gh = place_group(x0, y, leads, members)
        y += gh + GROUP_GAP
    return pos


GROUPS = groups()


def main():
    from kipy import KiCad
    from kipy.geometry import Vector2
    board = KiCad().get_board()
    fps = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
    lib_of = {r: fp.definition.id.name for r, fp in fps.items()}
    turned = [r for r, fp in fps.items() if fp.orientation.degrees % 360]
    if turned:
        sys.exit(f"expects every footprint at 0 degrees; turned: {turned}")
    pos = layout(lib_of)
    for side, name, leads, members in GROUPS:
        print(f"{side:6} {name:22} {' '.join(leads + members)}")
    if "--dry-run" in sys.argv:
        return
    for r, (x, y) in pos.items():
        fps[r].position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
    commit = board.begin_commit()
    board.update_items(list(fps.values()))
    board.push_commit(commit, "Step 4.2: group parts by chain beside the board")
    print(f"{len(pos)} parts moved")


if __name__ == "__main__":
    main()
