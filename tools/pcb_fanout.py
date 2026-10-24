"""Step 5.1: ground fan-out, live in the board open in KiCad (one undo step), then locked.
- Exposed pads: vias where the paste windows leave gaps, so solder doesn't wick down the holes [AN4169 p12; ADI
  "IC Ground Plane"; LMX2571 EVM, SNAS654A p55]: U2 and U1 3 x 3, U7 a cross of 5, U4 one (its 1.8 mm pad has room
  for no more).
- An IC's ground pins on its sides: a stub straight inward to its own exposed pad, as wide as the pin.
- Every other ground pad on the top: its own via right beside it, joined by a short track [AN4169 p7; ADI "Grounding of
  Shunt-Connected Components"], looked for outward from the part first, then sideways. A via keeps 0.2 mm copper
  clearance (fab-rules.md), 0.5 mm hole to hole, 0.5 mm from the edge, and stays out of the planned RF lines and the
  digital corridor (KEEP_OUT, from step 4.9-4.13's plan).
Vias are 0.6 / 0.3 mm, KiCad's netclass default. Run it once; a rerun would add a second set. A pad with no room
beside it (U5's middle ground pin, between its RF pins) joins through the top ground pour in Phase 6.
Usage (from the repository root, board open in KiCad): python tools/pcb_fanout.py [--only C13,C20,...] [--dry-run]
--only redoes just those parts' pads (after they moved; remove their old vias and stubs first)."""
import math
import sys

sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid

VIA_D, VIA_DRILL, CLR, HOLE_GAP, EDGE = 0.6, 0.3, 0.2, 0.5, 0.5
BOARD = (12.70, 59.56, 59.15, 130.96)
STUB_W = 0.3  # mm, pad-to-via and pin-to-paddle stubs
EP_VIAS = {  # exposed pad: via positions in the footprint's own frame, in the paste gaps
    "U2": [(x, y) for x in (-1.15, 0, 1.15) for y in (-1.15, 0, 1.15)],
    "U1": [(x, y) for x in (-1.4, 0, 1.4) for y in (-1.4, 0, 1.4)],
    "U7": [(0, 0), (0.95, 0), (-0.95, 0), (0, 0.95), (0, -0.95)],
    "U4": [(0, 0)],
}
# planned routes from the placement review (x0, y0, x1, y1): no fan-out vias here
KEEP_OUT = [
    (43.9, 84.0, 46.1, 92.0),     # TX: C26 to U7's RF in
    (44.3, 96.0, 46.2, 107.0),    # TX: U7's RF out, straight down
    (42.0, 106.5, 46.2, 109.3),   # TX: the step left
    (42.0, 108.8, 43.9, 122.0),   # TX: down to the filter
    (46.0, 116.4, 48.9, 121.8),   # RX: C34 up to the FB1/L1 node
    (47.8, 124.3, 52.0, 125.7),   # antenna line to J2
    (52.4, 70.0, 58.7, 108.0),    # digital corridor down the right edge
    (36.0, 69.2, 52.4, 72.4),     # digital corridor over U2 (C18/C19's ground vias sit at its lower edge)
    (33.6, 75.0, 37.2, 89.6),     # digital corridor up from U1 (widened when Y2 moved left)
    (36.0, 78.3, 39.8, 80.6),     # the FSK lines' way in to U2 pins 4, 6 and 7, between C21 and C14
]


def rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def read_board(text):
    """Every pad as (ref, number, net, x, y, half_w, half_h, kind, drill) in board coordinates, and every footprint's place."""
    b = sexpr(text)
    pads, places, vias = [], {}, []
    for fp in kids(b, "footprint"):
        ref = [p for p in kids(fp, "property") if p[1] == "Reference"][0][2]
        at = kid(fp, "at")
        fx, fy, fr = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        places[ref] = (fx, fy, fr)
        for p in kids(fp, "pad"):
            pat = kid(p, "at")
            lx, ly = float(pat[1]), float(pat[2])
            pr = float(pat[3]) if len(pat) > 3 else fr  # board files store the pad's total turn
            dx, dy = rot(lx, ly, fr)
            w, h = (float(v) for v in kid(p, "size")[1:3])
            if round((pr % 180) / 90) % 2:
                w, h = h, w
            net = kid(p, "net")
            dr = kid(p, "drill")
            drill = max(float(v) for v in dr[1:] if v.replace(".", "", 1).isdigit()) if dr else 0.0
            layers = kid(p, "layers")[1:]
            pads.append((ref, p[1], net[-1] if net else "", fx + dx, fy + dy, w / 2, h / 2, p[2], drill, layers))
    for v in kids(b, "via"):
        at = kid(v, "at")
        vias.append((float(at[1]), float(at[2]), float(kid(v, "size")[1]) / 2, float(kid(v, "drill")[1]) / 2))
    return pads, places, vias


def main():
    from kipy import KiCad
    from kipy.board_types import Track, Via
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    board = KiCad().get_board()
    pads, places, old_vias = read_board(board.get_as_string())
    copper = [p for p in pads if any(l in ("F.Cu", "*.Cu") for l in p[9])]
    holes = [(p[3], p[4], p[8] / 2) for p in pads if p[8] > 0] + [(x, y, d) for x, y, _, d in old_vias]
    new_vias, new_tracks = [], []

    def clear_of_pads(x, y, r, net, skip=None):
        for p in copper:
            if p is skip or (p[2] == net and net):
                continue
            ex = max(abs(x - p[3]) - p[5], 0)
            ey = max(abs(y - p[4]) - p[6], 0)
            if math.hypot(ex, ey) < r + CLR:
                return False
        return True

    def via_ok(x, y, net="GND", own=None):
        r = VIA_D / 2
        x0, y0, x1, y1 = BOARD
        if not (x0 + EDGE + r <= x <= x1 - EDGE - r and y0 + EDGE + r <= y <= y1 - EDGE - r):
            return False
        if any(a <= x <= c and b <= y <= d for a, b, c, d in KEEP_OUT):
            return False
        if not clear_of_pads(x, y, r, net):
            return False
        for hx, hy, hr in holes + [(vx, vy, VIA_DRILL / 2) for vx, vy in new_vias]:
            if math.hypot(x - hx, y - hy) < HOLE_GAP + hr + VIA_DRILL / 2:
                return False
        return True

    def stub_ok(x0, y0, x1, y1, net, own, width=STUB_W):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.05))
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            for p in copper:
                if p[2] == net:
                    continue
                ex = max(abs(x - p[3]) - p[5], 0)
                ey = max(abs(y - p[4]) - p[6], 0)
                if math.hypot(ex, ey) < width / 2 + CLR:
                    return False
        return True

    # exposed pads, and side ground pins stubbed to them
    only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
    ep_refs = set(EP_VIAS)
    for ref, pts in EP_VIAS.items():
        if only is not None and ref not in only:
            continue
        fx, fy, fr = places[ref]
        for lx, ly in pts:
            dx, dy = rot(lx, ly, fr)
            new_vias.append((fx + dx, fy + dy))
        ep = max((p for p in pads if p[0] == ref and p[2] == "GND"), key=lambda p: p[5] * p[6])
        for p in pads:
            if p[0] == ref and p[2] == "GND" and p is not ep and p[7] == "smd":
                # straight in, at right angles to the pin's side, to the paddle's edge; as wide as the pin
                dx, dy = p[3] - fx, p[4] - fy
                if abs(dx) >= abs(dy):
                    end = (fx + math.copysign(ep[5] - 0.05, dx), p[4])
                    w = 2 * p[6]
                else:
                    end = (p[3], fy + math.copysign(ep[6] - 0.05, dy))
                    w = 2 * p[5]
                if stub_ok(p[3], p[4], *end, "GND", p, w):  # a corner pin's stub can run over the next side's first pin
                    new_tracks.append(((p[3], p[4]), end, w))
    # every other top-side ground pad
    missed = []
    for p in copper:
        ref, num, net, x, y, hw, hh, kind, drill, layers = p
        if (only is not None and ref not in only) or net != "GND" or ref in ep_refs or kind != "smd" or ref.startswith(("J", "TP")) or "F.Cu" not in layers:
            continue
        fx, fy, _ = places[ref]
        ox, oy = x - fx, y - fy
        if abs(ox) < 1e-6 and abs(oy) < 1e-6:
            ox, oy = 1.0, 0.0
        dirs = []
        main_dir = (1 if ox > 0 else -1, 0) if abs(ox) >= abs(oy) else (0, 1 if oy > 0 else -1)
        dirs.append(main_dir)
        dirs += [(main_dir[1], main_dir[0]), (-main_dir[1], -main_dir[0])]
        dirs += [(main_dir[0] + main_dir[1], main_dir[1] + main_dir[0]), (main_dir[0] - main_dir[1], main_dir[1] - main_dir[0])]
        done = False
        for step in (0.0, 0.15, 0.3, 0.5, 0.75, 1.0):
            for ux, uy in dirs:
                n = math.hypot(ux, uy)
                ux, uy = ux / n, uy / n
                reach = abs(ux) * hw + abs(uy) * hh
                vx, vy = x + ux * (reach + VIA_D / 2 + 0.1 + step), y + uy * (reach + VIA_D / 2 + 0.1 + step)
                if via_ok(vx, vy) and stub_ok(x, y, vx, vy, "GND", p):
                    new_vias.append((vx, vy))
                    new_tracks.append(((x, y), (vx, vy), STUB_W))
                    done = True
                    break
            if done:
                break
        if not done:
            missed.append(f"{ref}.{num}")

    print(f"{len(new_vias)} vias, {len(new_tracks)} stubs; no room beside: {missed}")
    if "--dry-run" in sys.argv:
        return
    gnd = next(n for n in board.get_nets() if n.name == "GND")
    items = []
    for vx, vy in new_vias:
        v = Via()
        v.position = Vector2.from_xy(round(vx * 1e6), round(vy * 1e6))
        v.diameter = round(VIA_D * 1e6)
        v.drill_diameter = round(VIA_DRILL * 1e6)
        v.net = gnd
        v.locked = True
        items.append(v)
    for (x0, y0), (x1, y1), w in new_tracks:
        t = Track()
        t.start = Vector2.from_xy(round(x0 * 1e6), round(y0 * 1e6))
        t.end = Vector2.from_xy(round(x1 * 1e6), round(y1 * 1e6))
        t.width = round(w * 1e6)
        t.layer = BoardLayer.BL_F_Cu
        t.net = gnd
        t.locked = True
        items.append(t)
    c = board.begin_commit()
    board.create_items(items)
    board.push_commit(c, "Step 5.1: ground fan-out")
    print("added")


if __name__ == "__main__":
    main()
