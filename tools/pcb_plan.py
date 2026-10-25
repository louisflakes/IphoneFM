"""Phase 5: geometry for planned routing, shared by the tools/pcb_route_*.py region plans.
A region plan builds a Plan (runs, vias and part placements) from these pieces, so bus lines leave their pins
straight, bend only by 45 degrees and keep one spacing through every bend (routing-quality standard):
  turn   lines leave an edge along u, then bend 90 degrees (two 45-degree bends) to run along v in given lanes;
  jog    parallel lines shift sideways (two 45-degree bends) to new lanes and carry on in the same direction.
Both choose where each line bends so the diagonals sit exactly `pitch` apart and every line leaves its pin straight
for at least `min_exit` beyond the pad's tip.
A Plan is checked with tools/pcb_quality.py (--plan) and drawn with tools/pcb_view.py (--runs) before it is laid."""
import math
import sys

T, B = "F.Cu", "B.Cu"
VIA, DRILL = 0.6, 0.3
R2 = math.sqrt(2)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def _offsets(pitch, k):
    """Cumulative diagonal offsets: pitch may be one spacing or a list of k-1 spacings."""
    gaps = pitch if isinstance(pitch, (list, tuple)) else [pitch] * (k - 1)
    off = [0.0]
    for g in gaps:
        off.append(off[-1] + g)
    return off


def turn(starts, u, v, lanes, pitch, tips=0.0, min_exit=1.0, min_tail=0.0, late=False):
    """Lines start at `starts` (pad centres, ordered from the inside of the bend outwards), leave along unit vector u,
    bend through 45 degrees and run along unit vector v at u-coordinates `lanes` (u . point = lane).
    `tips`: distance from each start to its pad's tip along u (a number or a list). `late` bends each line as late as
    the lanes allow (long straight runs, short diagonals) instead of as early. Returns, per line, the points
    [start, first bend, second bend]; the caller carries each line on along v."""
    n = ((u[0] - v[0]) / R2, (u[1] - v[1]) / R2)
    k = len(starts)
    tips = tips if isinstance(tips, (list, tuple)) else [tips] * k
    us = [dot(u, s) for s in starts]
    vs = [dot(v, s) for s in starts]
    # a_i = R2 * (D0 + i * pitch) - us_i + vs_i ; need a_i >= tip_i + min_exit and t_i = lane_i - us_i - a_i >= min_tail
    off = _offsets(pitch, k)
    lo = max((tips[i] + min_exit + us[i] - vs[i]) / R2 - off[i] for i in range(k))
    hi = min((lanes[i] - us[i] - min_tail + us[i] - vs[i]) / R2 - off[i] for i in range(k))
    if lo > hi + 1e-9:
        raise ValueError(f"turn: no room (needs {lo:.3f}, room up to {hi:.3f})")
    d0 = hi if late else lo  # late: run straight as far as the lanes allow, bend at the last moment
    out = []
    for i, s in enumerate(starts):
        a = R2 * (d0 + off[i]) - us[i] + vs[i]
        t = lanes[i] - us[i] - a
        b = add(s, u, a)
        c = add(add(b, u, t), v, t)
        out.append([s, b, c])
    return out


def jog(starts, u, w, shifts, pitch, lead=0.0):
    """Parallel lines at `starts` (ordered so the line moving first comes first) running along u shift sideways by
    `shifts` along unit vector w (each >= 0) through two 45-degree bends. `lead`: straight run before the first
    line's bend. Returns per line [start, bend 1, bend 2]; the caller carries each line on along u."""
    m = ((u[0] - w[0]) / R2, (u[1] - w[1]) / R2)
    us = [dot(u, s) for s in starts]
    ws = [dot(w, s) for s in starts]
    out = []
    off = _offsets(pitch, len(starts))
    # bend as early as every line allows: no line bends before its start, the first not before `lead`
    d0 = max([(us[0] + lead - ws[0]) / R2] + [(us[i] - ws[i]) / R2 - off[i] for i in range(len(starts))])
    for i, s in enumerate(starts):
        # diagonal i: m . P = (us + a - ws) / R2 = d0 + offset i
        a = R2 * (d0 + off[i]) - us[i] + ws[i]
        if a < -1e-9:
            raise ValueError(f"jog: line {i} would bend before its start ({a:.3f})")
        p = add(s, u, a)
        q = add(add(p, u, shifts[i]), w, shifts[i])
        out.append([s, p, q])
    return out


class Plan:
    def __init__(self):
        self.runs = []    # (net, layer, [points], width)
        self.vias = []    # (net, x, y)
        self.place = {}   # ref: (x, y, rotation)

    def run(self, net, pts, w=0.2, layer=T):
        pts = [tuple(round(c, 4) for c in p) for p in pts]
        self.runs.append((net, layer, pts, w))

    def via(self, net, x, y):
        self.vias.append((net, round(x, 4), round(y, 4)))

    def segments(self):
        out = []
        for net, layer, pts, w in self.runs:
            for a, b in zip(pts, pts[1:]):
                if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-6:
                    out.append((net, layer, a, b, w))
        return out

    def copper(self):
        out = [("track", n, {l}, (a[0], a[1], b[0], b[1], w / 2), "plan") for n, l, a, b, w in self.segments()]
        out += [("via", n, {T, B}, (x, y, VIA / 2, DRILL / 2), "plan") for n, x, y in self.vias]
        return out

    def apply_place(self):
        from kipy import KiCad
        from kipy.geometry import Vector2, Angle
        board = KiCad().get_board()
        fps = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
        for ref, (x, y, a) in self.place.items():
            fps[ref].position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
            fps[ref].orientation = Angle.from_degrees(a)
        c = board.begin_commit()
        board.update_items([fps[r] for r in self.place])
        board.push_commit(c, "Place parts for the routing plan")
        board.save()
        print(f"placed {len(self.place)} parts")

    def lay(self, title, dry=False, lock=False):
        from kipy import KiCad
        from kipy.board_types import Track, Via
        from kipy.geometry import Vector2
        from kipy.proto.board.board_types_pb2 import BoardLayer
        board = KiCad().get_board()
        nets = {n.name: n for n in board.get_nets()}
        mm = lambda v: round(v * 1e6)
        items = []
        for net, layer, (x0, y0), (x1, y1), w in self.segments():
            t = Track()
            t.start, t.end = Vector2.from_xy(mm(x0), mm(y0)), Vector2.from_xy(mm(x1), mm(y1))
            t.width, t.net = mm(w), nets[net]
            t.layer = BoardLayer.BL_F_Cu if layer == T else BoardLayer.BL_B_Cu
            t.locked = lock
            items.append(t)
        for net, x, y in self.vias:
            v = Via()
            v.position = Vector2.from_xy(mm(x), mm(y))
            v.diameter, v.drill_diameter, v.net, v.locked = mm(VIA), mm(DRILL), nets[net], lock
            items.append(v)
        print(f"{title}: {len(items)} items")
        if dry:
            return
        c = board.begin_commit()
        board.create_items(items)
        board.push_commit(c, title)


def main(plan, title):
    """Command line for a region plan: place | lay [--dry-run] [--lock]"""
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "place":
        plan.apply_place()
    elif cmd == "lay":
        plan.lay(title, "--dry-run" in sys.argv, "--lock" in sys.argv)
    else:
        print(__doc__)
