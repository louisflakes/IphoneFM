"""Phase 5: routes connections one at a time, on the top, the bottom or both layers, live in the board open in KiCad,
for the nets laid by hand before the autorouter (U1's escape and its runs, steps 5.7-5.10). A* search on a 0.05 mm grid
around everything already on the board:
- other nets' pads, tracks and vias kept at the clearance rule (0.2 mm); clock tracks keep 0.4 mm from other nets'
  tracks and vias, and other tracks keep 0.4 mm from clock tracks, except inside the courtyards of the parts the clock
  lines start and end at (CLOCK_ENDS), as IphoneFM.kicad_dru;
- the board edge at 0.5 mm; no bottom-layer copper under the RF section (RF_BOTTOM, as pcb_freeroute.py) [AN4169 p12];
- a via (0.6 / 0.3 mm) only where it keeps 0.2 mm from other copper on both layers, 0.5 mm hole to hole, stays off
  every pad and out of the RF section, and costs the length of VIA_COST so the path changes layer only when it pays;
- each step on the bottom layer costs B_COST times a top-layer step, so crossings under other lines stay short and
  the ground plane stays whole;
- moves straight or at 45 degrees, never a 90-degree corner, with a cost on each bend [BAC p11; KHA p130-131].
The path is cut into straight segments and locked. As a module, route() lays several connections in one session, each
seeing the ones before it.
Usage (from the repository root, board open in KiCad):
  python tools/pcb_astar.py NET FROM TO [--width 0.2] [--layers F|B|FB] [--avoid x0,y0,x1,y1 ...] [--dry-run]
  FROM and TO are pads (U2.34) or points (41.2,75.3)."""
import heapq
import math
import sys

import numpy as np

sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid
from pcb_fanout import rot
from pcb_freeroute import RF_BOTTOM

G = 0.05  # grid, mm
BOARD = (12.70, 59.56, 59.15, 130.96)
EDGE, CLR, CLOCK_CLR = 0.5, 0.2, 0.4
VIA_D, VIA_DRILL, HOLE_GAP = 0.6, 0.3, 0.5
VIA_COST = 30.0  # grid steps (1.5 mm of track)
TURN = 4.0
B_COST = 3.0  # each step on the bottom layer counts this many times: it is the ground plane, so crossings there stay short
CLOCK = {"/FSK_CLK", "/FSK_CLK_MCU", "/REF20", "/REF20_MCU", "/RX_RCLK", "/RX_SCK", "/RX_SCK_MCU", "/LMX_CLK"}


def board_copper(text):
    """Pads, tracks and vias as (kind, net, layers, geometry, name)."""
    b = sexpr(text)
    out = []
    for fp in kids(b, "footprint"):
        ref = [p for p in kids(fp, "property") if p[1] == "Reference"][0][2]
        at = kid(fp, "at")
        fx, fy, fr = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        for p in kids(fp, "pad"):
            pat = kid(p, "at")
            pr = float(pat[3]) if len(pat) > 3 else fr
            dx, dy = rot(float(pat[1]), float(pat[2]), fr)
            w, h = (float(v) for v in kid(p, "size")[1:3])
            if round((pr % 180) / 90) % 2:
                w, h = h, w
            net = kid(p, "net")
            layers = kid(p, "layers")[1:]
            cu = {l for l in layers if l.endswith(".Cu")}
            if "*.Cu" in cu or p[2] in ("thru_hole", "np_thru_hole"):
                cu = {"F.Cu", "B.Cu"}
            dr = kid(p, "drill")
            drill = max([float(v) for v in dr[1:] if v.replace(".", "", 1).isdigit()] or [0]) if dr else 0.0
            shape = "circle" if p[3] == "circle" or p[2] == "np_thru_hole" else "rect"
            out.append(("pad", net[-1] if net else "", cu, (fx + dx, fy + dy, w / 2, h / 2, shape, drill / 2), f"{ref}.{p[1]}"))
    for s in kids(b, "segment"):
        x0, y0 = (float(v) for v in kid(s, "start")[1:3])
        x1, y1 = (float(v) for v in kid(s, "end")[1:3])
        out.append(("track", kid(s, "net")[-1], {kid(s, "layer")[1]}, (x0, y0, x1, y1, float(kid(s, "width")[1]) / 2), ""))
    for v in kids(b, "via"):
        x, y = (float(v_) for v_ in kid(v, "at")[1:3])
        out.append(("via", kid(v, "net")[-1], {"F.Cu", "B.Cu"}, (x, y, float(kid(v, "size")[1]) / 2, float(kid(v, "drill")[1]) / 2), ""))
    return out


class Grid:
    def __init__(self):
        x0, y0, x1, y1 = BOARD
        self.nx, self.ny = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
        self.xs = x0 + np.arange(self.nx) * G
        self.ys = y0 + np.arange(self.ny) * G
        X, Y = np.meshgrid(self.xs, self.ys)
        self.rf = inside(X, Y, RF_BOTTOM)

    def window(self, ax0, ay0, ax1, ay1):
        x0, y0 = BOARD[:2]
        i0, i1 = max(0, int((ax0 - x0) / G)), min(self.nx, int((ax1 - x0) / G) + 2)
        j0, j1 = max(0, int((ay0 - y0) / G)), min(self.ny, int((ay1 - y0) / G) + 2)
        return j0, j1, i0, i1

    def edge_mask(self, e):
        x0, y0, x1, y1 = BOARD
        m = np.zeros((self.ny, self.nx), bool)
        m[:, self.xs < x0 + e] = m[:, self.xs > x1 - e] = True
        m[self.ys < y0 + e, :] = m[self.ys > y1 - e, :] = True
        return m

    def mark(self, m, kind, g, inf):
        """Set m where the distance to the item is under inf."""
        if kind == "pad":
            cx, cy, hw, hh, shape, _ = g
            j0, j1, i0, i1 = self.window(cx - hw - inf, cy - hh - inf, cx + hw + inf, cy + hh + inf)
            X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
            d = np.hypot(X - cx, Y - cy) - hw if shape == "circle" else np.hypot(np.maximum(abs(X - cx) - hw, 0), np.maximum(abs(Y - cy) - hh, 0))
        elif kind == "track":
            ax, ay, bx, by, hw = g
            j0, j1, i0, i1 = self.window(min(ax, bx) - hw - inf, min(ay, by) - hw - inf, max(ax, bx) + hw + inf, max(ay, by) + hw + inf)
            X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
            vx, vy = bx - ax, by - ay
            t = np.clip(((X - ax) * vx + (Y - ay) * vy) / (vx * vx + vy * vy or 1e-12), 0, 1)
            d = np.hypot(X - (ax + t * vx), Y - (ay + t * vy)) - hw
        else:  # a circle: via or hole
            cx, cy, r = g[:3]
            j0, j1, i0, i1 = self.window(cx - r - inf, cy - r - inf, cx + r + inf, cy + r + inf)
            X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
            d = np.hypot(X - cx, Y - cy) - r
        m[j0:j1, i0:i1] |= d < inf


def inside(X, Y, poly):
    res = np.zeros(X.shape, bool)
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        cond = (y0 > Y) != (y1 > Y)
        xint = x0 + (Y - y0) * (x1 - x0) / ((y1 - y0) or 1e-12)
        res ^= cond & (X < xint)
    return res


CLOCK_ENDS = ("U1", "U2", "U4", "Y2", "R4", "R6", "R24")  # inside these courtyards clock escapes keep 0.2 mm (IphoneFM.kicad_dru)


def maps(grid, copper, net, width, avoid, courtyards=None):
    """Blocked maps for the track centre line on F and B, and for a via centre."""
    hw = width / 2
    clock = net in CLOCK
    mF, mB = grid.edge_mask(EDGE + hw), grid.edge_mask(EDGE + hw)
    mV = grid.edge_mask(EDGE + VIA_D / 2)
    mB |= grid.rf
    mV |= grid.rf
    xF = np.zeros_like(mF)  # the extra 0.2 mm a clock pair needs, lifted inside CLOCK_ENDS courtyards
    xB, xV = np.zeros_like(mF), np.zeros_like(mF)
    for kind, n, layers, g, _ in copper:
        pair = kind != "pad" and (clock or n in CLOCK)
        if n != net:
            for layer, m, x in (("F.Cu", mF, xF), ("B.Cu", mB, xB)):
                if layer in layers:
                    grid.mark(m, kind, g, hw + CLR)
                    if pair:
                        grid.mark(x, kind, g, hw + CLOCK_CLR)
            grid.mark(mV, kind, g, VIA_D / 2 + CLR)
            if pair:
                grid.mark(xV, kind, g, VIA_D / 2 + CLOCK_CLR)
        elif kind == "pad":
            grid.mark(mV, kind, g, VIA_D / 2)  # no via in a pad, even its own net's
        if kind == "via" or (kind == "pad" and g[5] > 0):  # every hole, any net: 0.5 mm hole to hole
            cx, cy = g[0], g[1]
            r = g[3] if kind == "via" else g[5]
            grid.mark(mV, "via", (cx, cy, r), HOLE_GAP + VIA_DRILL / 2)
    lift = np.zeros_like(mF)
    for x0, y0, x1, y1 in (courtyards or []):
        j0, j1, i0, i1 = grid.window(x0, y0, x1, y1)
        lift[j0:j1, i0:i1] = True
    mF |= xF & ~lift
    mB |= xB & ~lift
    mV |= xV & ~lift
    for ax0, ay0, ax1, ay1 in avoid:
        j0, j1, i0, i1 = grid.window(ax0, ay0, ax1, ay1)
        for m in (mF, mB, mV):
            m[j0:j1, i0:i1] = True
    return mF, mB, mV


MOVES = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]


def astar(blocked, mV, starts, goals, window, b_cost=1.0):
    """starts/goals: sets of (i, j, layer). blocked: [mF, mB]. Returns [(i, j, layer)]."""
    i0, i1, j0, j1 = window
    gl = list(goals)
    h = lambda i, j: min(max(abs(i - a), abs(j - b)) + 0.414 * min(abs(i - a), abs(j - b)) for a, b, _ in gl)
    openq, best, came = [], {}, {}
    for (i, j, l) in starts:
        best[(i, j, l, -1)] = 0.0
        heapq.heappush(openq, (h(i, j), 0.0, i, j, l, -1))
    while openq:
        f, g, i, j, l, d = heapq.heappop(openq)
        if (i, j, l) in goals:
            out, key = [(i, j, l)], (i, j, l, d)
            while key in came:
                key = came[key]
                out.append(key[:3])
            return out[::-1]
        if g > best.get((i, j, l, d), 1e18):
            continue
        for k, (di, dj, c) in enumerate(MOVES):
            a, b = i + di, j + dj
            if not (i0 <= a < i1 and j0 <= b < j1) or (blocked[l][b, a] and (a, b, l) not in goals):
                continue
            if d >= 0 and d != k:
                pi, pj, _ = MOVES[d]
                dot = pi * di + pj * dj
                if dot < 0 or (dot == 0 and abs(pi) + abs(pj) == 1 and abs(di) + abs(dj) == 1):
                    continue  # no U-turns and no 90-degree corners
            ng = g + c * (b_cost if l == 1 else 1.0) + (TURN if d >= 0 and d != k else 0.0)
            key = (a, b, l, k)
            if ng < best.get(key, 1e18):
                best[key], came[key] = ng, (i, j, l, d)
                heapq.heappush(openq, (ng + h(a, b), ng, a, b, l, k))
        if not mV[j, i]:
            key = (i, j, 1 - l, -1)
            ng = g + VIA_COST
            if ng < best.get(key, 1e18):
                best[key], came[key] = ng, (i, j, l, d)
                heapq.heappush(openq, (ng + h(i, j), ng, i, j, 1 - l, -1))
    return None


def route(board, net, a, b, width=0.2, layers="FB", avoid=(), margin=12.0, dry=False, b_cost=B_COST):
    """Lay one connection on the live board; returns (segments, vias, length) or None."""
    copper = board_copper(board.get_as_string())
    pads = {name: (g, l) for kind, n, l, g, name in copper if kind == "pad"}
    grid = Grid()
    from pcb_group import courtyard
    from pcb_local import turned_box
    cys = []
    for fp in board.get_footprints():
        if fp.reference_field.text.value in CLOCK_ENDS:
            bx = turned_box(courtyard(fp.definition.id.name), fp.orientation.degrees)
            px, py = fp.position.x / 1e6, fp.position.y / 1e6
            cys.append((px + bx[0], py + bx[1], px + bx[2], py + bx[3]))
    mF, mB, mV = maps(grid, copper, net, width, list(avoid), cys)
    if "F" not in layers:
        mF[:] = True
    if "B" not in layers:
        mB[:] = True
    idx = lambda x, y: (int(round((x - BOARD[0]) / G)), int(round((y - BOARD[1]) / G)))

    def ends(s):
        if s in pads:
            g, l = pads[s]
            (x, y), lay = g[:2], [k for k, name in ((0, "F.Cu"), (1, "B.Cu")) if name in l]
        else:
            (x, y), lay = tuple(float(v) for v in s.split(",")), [0, 1]
        i, j = idx(x, y)
        for m in (mF, mB):  # the pad itself is free to leave and enter
            m[max(0, j - 3):j + 4, max(0, i - 3):i + 4] = False
        return (x, y), {(i, j, k) for k in lay}

    (ax, ay), S = ends(a)
    (bx, by), T = ends(b)
    (si, sj), (ti, tj) = idx(ax, ay), idx(bx, by)
    win = (max(0, min(si, ti) - int(margin / G)), min(grid.nx, max(si, ti) + int(margin / G)),
           max(0, min(sj, tj) - int(margin / G)), min(grid.ny, max(sj, tj) + int(margin / G)))
    path = astar([mF, mB], mV, S, T, win, b_cost)
    if not path:
        return None
    # cut into runs per layer, keep only the bends
    segs, vias, cur = [], [], [path[0]]
    for p in path[1:]:
        if p[2] != cur[-1][2]:
            segs.append(cur)
            vias.append(p[:2])
            cur = [p]
        else:
            cur.append(p)
    segs.append(cur)
    xy = lambda p: (BOARD[0] + p[0] * G, BOARD[1] + p[1] * G)
    runs = []
    for run in segs:
        keep = [run[0]] + [q for k, q in enumerate(run[1:-1], 1)
                           if (q[0] - run[k - 1][0], q[1] - run[k - 1][1]) != (run[k + 1][0] - q[0], run[k + 1][1] - q[1])] + [run[-1]]
        runs.append((run[0][2], [xy(q) for q in keep]))
    runs[0][1][0] = (ax, ay)
    runs[-1][1][-1] = (bx, by)
    length = sum(math.dist(p, q) for _, pts in runs for p, q in zip(pts, pts[1:]))
    if dry:
        return runs, [xy(v) for v in vias], length
    from kipy.board_types import Track, Via
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    netobj = next(n for n in board.get_nets() if n.name == net)
    items = []
    for layer, pts in runs:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if (x0, y0) == (x1, y1):
                continue
            t = Track()
            t.start, t.end = Vector2.from_xy(round(x0 * 1e6), round(y0 * 1e6)), Vector2.from_xy(round(x1 * 1e6), round(y1 * 1e6))
            t.width = round(width * 1e6)
            t.layer = BoardLayer.BL_F_Cu if layer == 0 else BoardLayer.BL_B_Cu
            t.net, t.locked = netobj, True
            items.append(t)
    for vx, vy in (xy(v) for v in vias):
        v = Via()
        v.position = Vector2.from_xy(round(vx * 1e6), round(vy * 1e6))
        v.diameter, v.drill_diameter = round(VIA_D * 1e6), round(VIA_DRILL * 1e6)
        v.net, v.locked = netobj, True
        items.append(v)
    c = board.begin_commit()
    made = board.create_items(items)
    board.push_commit(c, f"Route {net} {a} -> {b}")
    return runs, [xy(v) for v in vias], length, made


def main():
    args = sys.argv[1:]
    net, a, b = args[0], args[1], args[2]
    opt = lambda k, d: args[args.index(k) + 1] if k in args else d
    avoid = [tuple(float(v) for v in args[i + 1].split(",")) for i, x in enumerate(args) if x == "--avoid"]
    from kipy import KiCad
    res = route(KiCad().get_board(), net, a, b, float(opt("--width", "0.2")), opt("--layers", "FB"), avoid, dry="--dry-run" in args)
    if not res:
        sys.exit(f"no path for {net} {a} -> {b}")
    runs, vias, length = res[:3]
    print(f"{net} {a} -> {b}: {length:.1f} mm, {len(vias)} via(s), layers {''.join('FB'[l] for l, _ in runs)}")


if __name__ == "__main__":
    main()
