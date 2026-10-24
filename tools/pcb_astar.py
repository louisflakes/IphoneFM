"""Phase 5: routes one connection at a time on one layer, live in the board open in KiCad (one undo step), for the
critical nets laid by hand before the autorouter (steps 5.7-5.10). A* search on a 0.05 mm grid around everything
already on the board: other nets' pads, tracks and vias kept at the clearance rule (0.2 mm, or more with --clear),
the board edge at 0.5 mm, and any keep-out boxes given. Moves are straight or 45 degrees, with a cost on every turn
so the path has few bends [BAC p11; KHA p130-131]. The path is then cut into straight segments and locked.
Usage (from the repository root, board open in KiCad):
  python tools/pcb_astar.py NET FROM TO [--width 0.2] [--clear 0.2] [--layer F] [--avoid x0,y0,x1,y1 ...] [--dry-run]
  FROM and TO are pads (U2.34) or points (41.2,75.3)."""
import heapq
import math
import sys

import numpy as np

sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid
from pcb_fanout import rot

G = 0.05  # grid, mm
BOARD = (12.70, 59.56, 59.15, 130.96)
EDGE = 0.5


def board_copper(text):
    """Pads, tracks and vias: (kind, net, layers, geometry)."""
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
            shape = "circle" if p[3] == "circle" or p[2] == "np_thru_hole" else "rect"
            out.append(("pad", net[-1] if net else "", cu, (fx + dx, fy + dy, w / 2, h / 2, shape), f"{ref}.{p[1]}"))
    for s in kids(b, "segment"):
        x0, y0 = (float(v) for v in kid(s, "start")[1:3])
        x1, y1 = (float(v) for v in kid(s, "end")[1:3])
        out.append(("track", kid(s, "net")[-1], {kid(s, "layer")[1]}, (x0, y0, x1, y1, float(kid(s, "width")[1]) / 2), ""))
    for v in kids(b, "via"):
        x, y = (float(v_) for v_ in kid(v, "at")[1:3])
        out.append(("via", kid(v, "net")[-1], {"F.Cu", "B.Cu"}, (x, y, float(kid(v, "size")[1]) / 2), ""))
    return out


def blocked_map(copper, net, layer, inflate, avoid, extra_nets=None):
    """True where the centre line of a track of the given half-width plus clearance (`inflate`) may not go."""
    x0, y0, x1, y1 = BOARD
    nx, ny = int((x1 - x0) / G) + 1, int((y1 - y0) / G) + 1
    xs = x0 + np.arange(nx) * G
    ys = y0 + np.arange(ny) * G
    grid = np.zeros((ny, nx), bool)
    e = EDGE + inflate - 0.2  # inflate already holds the 0.2 clearance; the edge rule is 0.5
    grid[:, xs < x0 + e] = grid[:, xs > x1 - e] = True
    grid[ys < y0 + e, :] = grid[ys > y1 - e, :] = True

    def window(ax0, ay0, ax1, ay1):
        i0, i1 = max(0, int((ax0 - x0) / G)), min(nx, int((ax1 - x0) / G) + 2)
        j0, j1 = max(0, int((ay0 - y0) / G)), min(ny, int((ay1 - y0) / G) + 2)
        return j0, j1, i0, i1

    for kind, n, layers, g, _ in copper:
        if n == net or layer not in layers:
            continue
        inf = inflate + (extra_nets or {}).get(n, 0.0)
        if kind == "pad":
            cx, cy, hw, hh, shape = g
            j0, j1, i0, i1 = window(cx - hw - inf, cy - hh - inf, cx + hw + inf, cy + hh + inf)
            X, Y = np.meshgrid(xs[i0:i1], ys[j0:j1])
            if shape == "circle":
                d = np.hypot(X - cx, Y - cy) - hw
            else:
                d = np.hypot(np.maximum(abs(X - cx) - hw, 0), np.maximum(abs(Y - cy) - hh, 0))
            grid[j0:j1, i0:i1] |= d < inf
        elif kind == "track":
            ax, ay, bx, by, hw = g
            j0, j1, i0, i1 = window(min(ax, bx) - hw - inf, min(ay, by) - hw - inf, max(ax, bx) + hw + inf, max(ay, by) + hw + inf)
            X, Y = np.meshgrid(xs[i0:i1], ys[j0:j1])
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy or 1e-12
            t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1)
            d = np.hypot(X - (ax + t * vx), Y - (ay + t * vy)) - hw
            grid[j0:j1, i0:i1] |= d < inf
        else:
            cx, cy, r = g
            j0, j1, i0, i1 = window(cx - r - inf, cy - r - inf, cx + r + inf, cy + r + inf)
            X, Y = np.meshgrid(xs[i0:i1], ys[j0:j1])
            grid[j0:j1, i0:i1] |= np.hypot(X - cx, Y - cy) - r < inf
    for ax0, ay0, ax1, ay1 in avoid:
        j0, j1, i0, i1 = window(ax0, ay0, ax1, ay1)
        grid[j0:j1, i0:i1] = True
    return grid, xs, ys


def astar(grid, start, goal, turn=4.0):
    ny, nx = grid.shape
    moves = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    (si, sj), (gi, gj) = start, goal
    h = lambda i, j: max(abs(i - gi), abs(j - gj)) + 0.414 * min(abs(i - gi), abs(j - gj))
    openq = [(h(si, sj), 0.0, si, sj, -1)]
    best = {(si, sj, -1): 0.0}
    came = {}
    while openq:
        f, g, i, j, d = heapq.heappop(openq)
        if (i, j) == (gi, gj):
            path = [(i, j)]
            key = (i, j, d)
            while key in came:
                key = came[key]
                path.append(key[:2])
            return path[::-1]
        if g > best.get((i, j, d), 1e18):
            continue
        for k, (di, dj, c) in enumerate(moves):
            a, b_ = i + di, j + dj
            if not (0 <= a < nx and 0 <= b_ < ny) or (grid[b_, a] and (a, b_) != (gi, gj)):
                continue
            if d >= 0 and d != k:
                dd = moves[d]
                if dd[0] * di + dd[1] * dj < 0 or (dd[0] * di + dd[1] * dj == 0 and abs(dd[0]) + abs(dd[1]) == 1 and abs(di) + abs(dj) == 1):
                    continue  # no U-turns, no 90-degree corners: 45 degrees at a time [KHA p130-131]
            ng = g + c + (turn if d >= 0 and d != k else 0.0)
            key = (a, b_, k)
            if ng < best.get(key, 1e18):
                best[key] = ng
                came[key] = (i, j, d)
                heapq.heappush(openq, (ng + h(a, b_), ng, a, b_, k))
    return None


def simplify(points):
    out = [points[0]]
    for p in points[1:-1]:
        a, b = out[-1], p
        nxt = points[points.index(p) + 1]
        if (b[0] - a[0]) * (nxt[1] - b[1]) - (b[1] - a[1]) * (nxt[0] - b[0]) != 0:
            out.append(p)
    out.append(points[-1])
    return out


def main():
    args = sys.argv[1:]
    net, a, b = args[0], args[1], args[2]
    opt = lambda k, d: args[args.index(k) + 1] if k in args else d
    width, clear = float(opt("--width", "0.2")), float(opt("--clear", "0.2"))
    layer = {"F": "F.Cu", "B": "B.Cu"}[opt("--layer", "F")]
    avoid = []
    for i, x in enumerate(args):
        if x == "--avoid":
            avoid.append(tuple(float(v) for v in args[i + 1].split(",")))
    from kipy import KiCad
    board = KiCad().get_board()
    copper = board_copper(board.get_as_string())
    padxy = {name: g[:2] for kind, n, l, g, name in copper if kind == "pad"}
    pt = lambda s: padxy[s] if s in padxy else tuple(float(v) for v in s.split(","))
    (ax, ay), (bx, by) = pt(a), pt(b)
    grid, xs, ys = blocked_map(copper, net, layer, width / 2 + clear, avoid)
    idx = lambda x, y: (int(round((x - xs[0]) / G)), int(round((y - ys[0]) / G)))
    si, gi = idx(ax, ay), idx(bx, by)
    for (i, j) in (si, gi):  # the pads themselves are free to leave and enter
        grid[max(0, j - 3):j + 4, max(0, i - 3):i + 4] = False
    path = astar(grid, si, gi)
    if not path:
        sys.exit(f"no path for {net} {a} -> {b}")
    pts = [(xs[0] + i * G, ys[0] + j * G) for i, j in simplify(path)]
    pts[0], pts[-1] = (ax, ay), (bx, by)
    length = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
    print(f"{net} {a} -> {b}: {len(pts) - 1} segments, {length:.1f} mm on {layer}")
    if "--dry-run" in args:
        print([(round(x, 3), round(y, 3)) for x, y in pts])
        return
    from kipy.board_types import Track
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    netobj = next(n for n in board.get_nets() if n.name == net)
    items = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = Track()
        t.start = Vector2.from_xy(round(x0 * 1e6), round(y0 * 1e6))
        t.end = Vector2.from_xy(round(x1 * 1e6), round(y1 * 1e6))
        t.width = round(width * 1e6)
        t.layer = BoardLayer.BL_F_Cu if layer == "F.Cu" else BoardLayer.BL_B_Cu
        t.net = netobj
        t.locked = True
        items.append(t)
    c = board.begin_commit()
    board.create_items(items)
    board.push_commit(c, f"Route {net}")


if __name__ == "__main__":
    main()
