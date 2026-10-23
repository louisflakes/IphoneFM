"""Phase 4 (steps 4.8-4.13): places an IC's local parts at its pins, live in the board open in KiCad (one undo step).
Each part netlist.json puts at one of the IC's pins (local_to "U2.25") stands just outside the IC's courtyard on that
pin's side, long axis pointing at the pin, its pad on the pin's net nearest the IC, as on TI's LMX2571 evaluation
board (SNAS654A p55). Parts on one side are spread evenly about their pins with the 0.3 mm courtyard gap; parts named
with --outer go in a second row. A part local to one of those parts (C25 at R5.2) continues outward from it. A part
that would touch anything already on the board steps out a row. Optionally moves the IC first.
Usage (from the repository root, board open in KiCad):
  python tools/pcb_local.py U2 [--at X Y ROT] [--outer R9,...] [--skip C28,...] [--dry-run]
--skip leaves parts out, for ones placed by hand (an RF filter's first shunt capacitor, say)."""
import json
import math
import sys

sys.path.insert(0, "tools")
from pcb_group import courtyard, BOARD

GAP = 0.35  # mm between courtyards: the 0.3 mm rule plus a little
SIDES = {(1, 0): 180, (-1, 0): 0, (0, 1): 90, (0, -1): -90}  # outward direction -> turn that points a part's +x pad inward


def turned(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def turned_box(box, deg):
    """Courtyard box of a footprint turned by a multiple of 90 degrees (KiCad: counter-clockwise on screen)."""
    pts = [turned(x, y, deg) for x, y in ((box[0], box[1]), (box[2], box[3]))]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def overlaps(a, b):
    return a[0] < b[2] + GAP - 1e-6 and b[0] < a[2] + GAP - 1e-6 and a[1] < b[3] + GAP - 1e-6 and b[1] < a[3] + GAP - 1e-6


def spread(ideal, width):
    """1-D packing: positions as close as possible to `ideal` (sorted), neighbours at least (w_i + w_j)/2 + GAP apart."""
    blocks = []  # [start index, end index, position of the first item]
    for i in range(len(ideal)):
        blocks.append([i, i, ideal[i]])
        while len(blocks) > 1:
            a, b = blocks[-2], blocks[-1]
            a_end = a[2] + sum((width[k] + width[k + 1]) / 2 + GAP for k in range(a[0], a[1]))
            if a_end + (width[a[1]] + width[b[0]]) / 2 + GAP <= b[2] + 1e-9:
                break
            lo, hi = a[0], b[1]
            offs = [0.0]
            for k in range(lo, hi):
                offs.append(offs[-1] + (width[k] + width[k + 1]) / 2 + GAP)
            start = sum(ideal[lo + j] - offs[j] for j in range(hi - lo + 1)) / (hi - lo + 1)
            blocks[-2:] = [[lo, hi, start]]
    out = []
    for lo, hi, start in blocks:
        p = start
        for k in range(lo, hi + 1):
            out.append(p)
            if k < hi:
                p += (width[k] + width[k + 1]) / 2 + GAP
    return out


def main():
    from kipy import KiCad
    from kipy.geometry import Vector2, Angle
    ic_ref = sys.argv[1]
    outer = sys.argv[sys.argv.index("--outer") + 1].split(",") if "--outer" in sys.argv else []
    skip = sys.argv[sys.argv.index("--skip") + 1].split(",") if "--skip" in sys.argv else []
    board = KiCad().get_board()
    fps = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
    lib = {r: fp.definition.id.name for r, fp in fps.items()}
    ic = fps[ic_ref]

    def frame(fp):
        """{pad number: ((x, y) in the footprint's own frame, net)}."""
        px, py, a = fp.position.x / 1e6, fp.position.y / 1e6, fp.orientation.degrees
        return {p.number: (turned(p.position.x / 1e6 - px, p.position.y / 1e6 - py, -a), p.net.name) for p in fp.definition.pads}

    if "--at" in sys.argv:
        i = sys.argv.index("--at")
        cx, cy, ic_deg = (float(v) for v in sys.argv[i + 1:i + 4])
    else:
        cx, cy, ic_deg = ic.position.x / 1e6, ic.position.y / 1e6, ic.orientation.degrees
    ic_pads = {n: ((cx + turned(*xy, ic_deg)[0], cy + turned(*xy, ic_deg)[1]), net) for n, (xy, net) in frame(ic).items()}
    b = turned_box(courtyard(lib[ic_ref]), ic_deg)
    ic_box = (cx + b[0], cy + b[1], cx + b[2], cy + b[3])

    parts = json.load(open("design/rev-a/netlist.json", encoding="utf-8"))["parts"]
    local = {p["ref"]: p.get("local_to", "") for p in parts}
    direct = [r for r, lt in local.items() if lt.split(".")[0] == ic_ref and r not in skip]
    chained = [r for r, lt in local.items() if lt.split(".")[0] in direct]

    taken = [ic_box]
    x0, y0, x1, y1 = BOARD
    for r, fp in fps.items():
        px, py = fp.position.x / 1e6, fp.position.y / 1e6
        if r in direct or r in chained or r == ic_ref or not (x0 < px < x1 and y0 < py < y1):
            continue
        bb = turned_box(courtyard(lib[r]), fp.orientation.degrees)
        taken.append((px + bb[0], py + bb[1], px + bb[2], py + bb[3]))

    def oriented(ref, net, out):
        """Turn and courtyard box for ref pointing along `out`, its pad on `net` toward the IC."""
        pads = frame(fps[ref])
        inner = [xy for xy, n in pads.values() if n == net]
        if not inner:
            sys.exit(f"{ref} has no pad on {net}")
        deg = SIDES[out] + (0 if inner[0][0] > 0 else 180)
        return deg % 360, turned_box(courtyard(lib[ref]), deg)

    def side_of(x, y):
        dx, dy = x - cx, y - cy
        return ((1 if dx > 0 else -1), 0) if abs(dx) > abs(dy) else (0, (1 if dy > 0 else -1))

    def face(out):
        return {(1, 0): ic_box[2], (-1, 0): ic_box[0], (0, 1): ic_box[3], (0, -1): ic_box[1]}[out]

    placed = {}

    def drop(ref, deg, box, out, d, along):
        """Place ref with its courtyard d mm out from the IC's face at `along`; step outward or sideways until clear."""
        ux, uy = out
        depth = (box[2] - box[0]) if ux else (box[3] - box[1])
        for ring in range(8):
            for k in range(0, 41):
                for sgn in ((1,) if k == 0 else (1, -1)):
                    a = along + sgn * k * 0.1
                    if ux:
                        x = face(out) + ux * (d + depth / 2)
                        x -= (box[0] + box[2]) / 2
                        y = a - (box[1] + box[3]) / 2
                    else:
                        y = face(out) + uy * (d + depth / 2)
                        y -= (box[1] + box[3]) / 2
                        x = a - (box[0] + box[2]) / 2
                    ab = (x + box[0], y + box[1], x + box[2], y + box[3])
                    if not any(overlaps(ab, t) for t in taken):
                        taken.append(ab)
                        placed[ref] = (x, y, deg, ab, out)
                        return ab
            d += depth + GAP
        sys.exit(f"no room for {ref}")

    # first row: per side, spread about the pins
    by_side = {}
    for ref in direct:
        (px, py), net = ic_pads[local[ref].split(".")[1]]
        out = side_of(px, py)
        deg, box = oriented(ref, net, out)
        along = py if out[0] else px
        width = (box[3] - box[1]) if out[0] else (box[2] - box[0])
        by_side.setdefault(out, []).append((along, ref, deg, box, width))
    rows2 = []
    for out, items in by_side.items():
        first = sorted([it for it in items if it[1] not in outer])
        rows2 += [(out, it) for it in items if it[1] in outer]
        pos = spread([it[0] for it in first], [it[4] for it in first])
        for p, (_, ref, deg, box, _) in zip(pos, first):
            drop(ref, deg, box, out, GAP, p)
    for out, (along, ref, deg, box, width) in rows2:
        depth = max(((placed[r][3][2] - placed[r][3][0]) if out[0] else (placed[r][3][3] - placed[r][3][1]))
                    for r in placed if placed[r][4] == out) if any(placed[r][4] == out for r in placed) else 0
        drop(ref, deg, box, out, GAP + depth + GAP, along)
    for ref in chained:
        host, pin = local[ref].split(".")
        hx, hy, hdeg, hab, out = placed[host]
        net = [p.net.name for p in fps[host].definition.pads if p.number == pin][0]
        deg, box = oriented(ref, net, out)
        d = {(1, 0): hab[2] - ic_box[2], (-1, 0): ic_box[0] - hab[0], (0, 1): hab[3] - ic_box[3], (0, -1): ic_box[1] - hab[1]}[out]
        along = hy if out[0] else hx
        drop(ref, deg, box, out, d + GAP, along)

    for ref, (x, y, deg, _, out) in sorted(placed.items(), key=lambda kv: local[kv[0]]):
        print(f"{ref:4} {local[ref]:8} at ({x:7.3f}, {y:7.3f}) {deg:4.0f} deg")
    if "--dry-run" in sys.argv:
        return
    ic.position = Vector2.from_xy(round(cx * 1e6), round(cy * 1e6))
    ic.orientation = Angle.from_degrees(ic_deg)
    items = [ic]
    for ref, (x, y, deg, _, _) in placed.items():
        fps[ref].position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
        fps[ref].orientation = Angle.from_degrees(deg)
        items.append(fps[ref])
    c = board.begin_commit()
    board.update_items(items)
    board.push_commit(c, f"Place {ic_ref} and its local parts")
    print(f"{len(placed)} parts placed at {ic_ref}")


if __name__ == "__main__":
    main()
