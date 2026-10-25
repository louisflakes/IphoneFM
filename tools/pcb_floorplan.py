"""Phase 5 floorplan study: scores candidate block placements by estimating how the board would route, before anyone
re-places parts. Reads the board open in KiCad (parts, pads, nets, courtyards), moves whole blocks per candidate, then:
- breaks every net except GND (the pours) into two-pin connections (a minimum spanning tree of its pads);
- U1's general-purpose pins are free (all candidates but "now"): such a connection may leave U1 from any edge, as if U1 were re-pinned to suit
  (fixed pins stay: power, OSC_IN, NRST, BOOT0, USB, SWD);
- routes them all on one layer on a 0.5 mm grid with negotiated congestion (PathFinder: rip up and reroute, raising
  the price of crowded cells each round [McMurchie and Ebeling 1995]); a cell holds one 0.2 mm track at 0.4 mm pitch;
- walls: the board edge (0.5 mm), mounting holes, ICs, connectors, switches, pots and the RF parts and lines (the RF
  nets are not routed here; their straight runs between pads, 0.8 mm each side, are walls), except at a connection's own
  part; small passives cost extra to cross but stay passable.
Scores: total length; overflow (cells used beyond one track: what would need the bottom layer or more room); the
largest overflow hot spot; straight-line crossings between connections (vias needed, roughly); connections whose
straight line crosses an RF wall (forced detours).
Usage (from the repository root, board open in KiCad): python tools/pcb_floorplan.py [CANDIDATE ...] [--draw DIR]"""
import heapq
import math
import sys

import numpy as np

sys.path.insert(0, "tools")
from pcb_group import courtyard
from pcb_local import turned_box

G = 0.5
BOARD = (12.70, 59.56, 59.15, 130.96)
RF_NETS = {"/LMX_RF", "/ATT_IN", "/TX_RF_ATT", "/TX_LPF_MID", "/TX_RF", "/ANT", "/RX_RF", "/FMI_MATCH", "/FMI"}
U1_FIXED = {"1", "5", "7", "8", "9", "22", "23", "24", "32", "33", "34", "35", "36", "37", "44", "47", "48", "EP"}
WALL_PREFIX = ("U", "J", "SW", "RV", "H", "Y", "TP", "D1")

# Candidates: block moves (refs, dx, dy, turn in degrees about the block's centre)
U1_BLOCK = ["U1", "C10", "FB2", "C7", "C8", "C39", "C40", "C36", "C41", "C9", "C3", "C4", "R6", "R7", "R8", "C5", "R3", "C6"]
U2_BLOCK = ["U2", "C13", "C20", "C21", "C14", "C17", "C26", "R9", "C15", "C23", "C22", "C24", "R5", "C16", "C19", "C18", "C25"]
Y2_BLOCK = ["Y2", "R4", "C11", "C12"]
U7_BLOCK = ["U7", "C27", "R10", "R11", "R12", "R13", "R14", "R15"]
TP_ROW = ["TP2", "TP3", "TP6", "TP7", "TP8"]
U4_BLOCK = ["U4", "L1", "FB1", "C35", "R19", "R20", "R21", "C33", "FB3", "C32", "R22", "R23", "R24", "C37", "C38"]
CANDIDATES = {
    "now": [],  # today's blocks and today's U1 pins (the only candidate scored with U1's pins as they are)
    "A": [],  # today's blocks; U1's free pins re-assigned (the scoring already assumes that for every candidate)
    # B: the transmit chain moves south of U1 and feeds U5 from the west; U4 moves to the right edge, on U1's side
    "B": [(U1_BLOCK, 0.0, -10.0, 0), (Y2_BLOCK, 0.0, 17.3, 0), (U2_BLOCK, -2.0, 22.0, 0), (U7_BLOCK, -3.5, 19.5, 0),
          (U4_BLOCK, 6.0, -13.5, 0), (["TP2", "TP3", "TP6", "TP7", "TP8"], 12.0, -22.0, 0), (["TP5"], 6.0, 22.0, 0)],
    # C: U1 moves above U2 (top centre, under SW3); U2 and Y2 sit between U1 and the transmit chain, which is as today
    "C": [(U1_BLOCK, 0.0, -14.0, 0), (Y2_BLOCK, 0.0, 13.3, 0), (U2_BLOCK, -2.0, 17.0, 0), (U7_BLOCK, 0.0, 9.4, 0),
          (["TP5"], 0.0, 18.0, 0)],
    # Round 2, branches of B: U4 with its input parts (C34 too) at the top right, 10+ mm from U2, fed by a 50-ohm receive
    # line from U5 up the right edge; B1 keeps B's U1, B2 leaves U1 where it is and packs U2, Y2 and U7 below it,
    # B3 is B2 with U1 turned so its I2S/USB side faces U2 and J1 and its receiver/LED side faces U4 and D1
    "B1": dict(moves=[(U1_BLOCK, 0, -10, 0), (Y2_BLOCK, 0, 17.3, 0), (U2_BLOCK, -2, 22, 0), (U7_BLOCK, -3.5, 19.5, 0),
                      (U4_BLOCK + ["C34"], 6, -28.5, 0), (TP_ROW, 8, -36, 0), (["TP5"], 6, 22, 0)], rf={"/RX_RF": None}),
    "B2": dict(moves=[(Y2_BLOCK, 16.3, 19.1, 90), (U2_BLOCK, -3.2, 29.8, 0), (U7_BLOCK, 3.1, 15.4, 0),
                      (U4_BLOCK + ["C34"], 6, -28.5, 0), (TP_ROW, 8, -36, 0)], rf={"/RX_RF": None}),
    "B3": dict(moves=[(U1_BLOCK, 1.7, 0, 90), (Y2_BLOCK, 16.3, 19.8, 90), (U2_BLOCK, -3.2, 29.8, 0), (U7_BLOCK, 3.1, 15.4, 0),
                      (U4_BLOCK + ["C34"], 6, -28.5, 0), (TP_ROW, 8, -36, 0)], rf={"/RX_RF": None}),
}


def rx_up_right_edge(P):
    """Round 2's receive line: U5 RF1 to C34 up the right edge, clear of H3."""
    a, b = P[("U5", "1")], P[("C34", "1")]
    return [a, (49.5, 121.0), (57.4, 113.1), (57.4, b[1] + 1.5), b]


for _c in CANDIDATES.values():
    if isinstance(_c, dict):
        _c["rf"] = {k: rx_up_right_edge for k in _c["rf"]}


def load(board):
    """Parts {ref: (x, y, turn, courtyard box rel.)}, pads [(ref, pin, net, x, y)]."""
    parts, pads = {}, []
    for f in board.get_footprints():
        ref = f.reference_field.text.value
        x, y, a = f.position.x / 1e6, f.position.y / 1e6, f.orientation.degrees
        parts[ref] = (x, y, turned_box(courtyard(f.definition.id.name), a))
        for p in f.definition.pads:
            pads.append((ref, p.number, p.net.name, p.position.x / 1e6, p.position.y / 1e6))
    return parts, pads


def apply(parts, pads, moves):
    parts, pads = dict(parts), list(pads)
    for refs, dx, dy, turn in moves:
        xs = [parts[r][0] for r in refs]; ys = [parts[r][1] for r in refs]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        rot = lambda x, y: (cx + c * (x - cx) - s * (y - cy) + dx, cy + s * (x - cx) + c * (y - cy) + dy)
        for r in refs:
            x, y, (b0, b1, b2, b3) = parts[r]
            nx, ny = rot(x, y)
            if turn % 180:
                b0, b1, b2, b3 = -b3, b0, -b1, b2
            parts[r] = (nx, ny, (b0, b1, b2, b3))
        pads = [(r, n, net, *rot(x, y)) if r in refs else (r, n, net, x, y) for r, n, net, x, y in pads]
    return parts, pads


class Grid:
    def __init__(self):
        self.nx, self.ny = int((BOARD[2] - BOARD[0]) / G), int((BOARD[3] - BOARD[1]) / G)

    def ij(self, x, y):
        return (min(self.nx - 1, max(0, int((x - BOARD[0]) / G))), min(self.ny - 1, max(0, int((y - BOARD[1]) / G))))

    def box(self, x0, y0, x1, y1):
        i0, j0 = self.ij(x0, y0); i1, j1 = self.ij(x1, y1)
        return slice(j0, j1 + 1), slice(i0, i1 + 1)


def seg_cells(g, a, b, r):
    """Cells within r of segment a-b."""
    out = set()
    L = max(1, int(math.dist(a, b) / (G / 2)))
    for k in range(L + 1):
        x, y = a[0] + (b[0] - a[0]) * k / L, a[1] + (b[1] - a[1]) * k / L
        sl = g.box(x - r, y - r, x + r, y + r)
        for j in range(sl[0].start, sl[0].stop):
            for i in range(sl[1].start, sl[1].stop):
                out.add((i, j))
    return out


def mst(points):
    n = len(points)
    if n < 2:
        return []
    used, edges = {0}, []
    best = {i: (math.dist(points[0], points[i]), 0) for i in range(1, n)}
    while best:
        i = min(best, key=lambda k: best[k][0])
        edges.append((best[i][1], i)); used.add(i); del best[i]
        for k in best:
            d = math.dist(points[i], points[k])
            if d < best[k][0]:
                best[k] = (d, i)
    return edges


def cross(p1, p2, p3, p4):
    d = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if {p1, p2} & {p3, p4}:
        return False
    return (d(p1, p2, p3) * d(p1, p2, p4) < 0) and (d(p3, p4, p1) * d(p3, p4, p2) < 0)


def score(parts, pads, draw=None, title="", repin=True, rf_paths=None):
    g = Grid()
    wall = np.zeros((g.ny, g.nx), dtype=np.int32)  # 0 free, else part index + 1 (or -1 for RF/edge)
    cost = np.ones((g.ny, g.nx))
    e = int(0.5 / G) + 1
    wall[:e, :] = wall[-e:, :] = -1; wall[:, :e] = wall[:, -e:] = -1
    refs = sorted(parts)
    idx = {r: k + 1 for k, r in enumerate(refs)}
    rf_parts = {r for r, n, net, x, y in pads if net in RF_NETS}
    for r in refs:
        x, y, (b0, b1, b2, b3) = parts[r]
        sl = g.box(x + b0, y + b1, x + b2, y + b3)
        if r.startswith(WALL_PREFIX) or r in rf_parts:
            wall[sl] = np.where(wall[sl] == 0, idx[r], wall[sl])
        else:
            cost[sl] = np.maximum(cost[sl], 3.0)
    rf_walls = []
    for net in RF_NETS:
        pts = [(x, y) for r, n, nn, x, y in pads if nn == net]
        if rf_paths and net in rf_paths:  # a hand-drawn run (pads at its ends)
            path = rf_paths[net](dict(((r, n), (x, y)) for r, n, nn, x, y in pads))
            segs = list(zip(path, path[1:]))
        else:
            segs = [(pts[a], pts[b]) for a, b in mst(pts)]
        for p, q in segs:
            rf_walls.append((p, q))
            for i, j in seg_cells(g, p, q, 0.8):
                wall[j, i] = -1
    for r, n, net, x, y in pads:  # every pad reachable from its own part, even inside a wall or a neighbour's courtyard
        if net not in RF_NETS:
            sl = g.box(x - 0.25, y - 0.25, x + 0.25, y + 0.25)
            wall[sl] = idx[r]
    # connections
    u1 = parts["U1"]; ub = (u1[0] + u1[2][0], u1[1] + u1[2][1], u1[0] + u1[2][2], u1[1] + u1[2][3])
    nets = {}
    for r, n, net, x, y in pads:
        if net and net != "GND" and net not in RF_NETS and not net.startswith("unconnected"):
            nets.setdefault(net, []).append((r, n, x, y))
    conns = []
    for net, ps in nets.items():
        pts = []
        for r, n, x, y in ps:
            pts.append((x, y))
        for a, b in mst(pts):
            ra, na = ps[a][:2]; rb, nb = ps[b][:2]
            conns.append((net, (ra, na, pts[a]), (rb, nb, pts[b])))
    free_u1 = lambda end: repin and end[0] == "U1" and end[1] not in U1_FIXED
    # straight-line metrics (U1 free ends taken at the nearest point of U1's edge toward the other end)
    def at_edge(end, other):
        if not free_u1(end):
            return end[2]
        ox, oy = other[2]
        x = min(max(ox, ub[0]), ub[2]); y = min(max(oy, ub[1]), ub[3])
        if ub[0] < ox < ub[2] and ub[1] < oy < ub[3]:
            return end[2]
        return (x, y)
    lines = [(net, at_edge(a, b), at_edge(b, a)) for net, a, b in conns]
    crossings = sum(1 for k in range(len(lines)) for m in range(k + 1, len(lines))
                    if lines[k][0] != lines[m][0] and cross(lines[k][1], lines[k][2], lines[m][1], lines[m][2]))
    rf_cross = sum(1 for net, p, q in lines if any(cross(p, q, a, b) for a, b in rf_walls))
    # route
    use = np.zeros((g.ny, g.nx)); hist = np.zeros((g.ny, g.nx))
    u1_edge = [g.ij(x, y) for x in np.arange(ub[0], ub[2] + 1e-6, G) for y in (ub[1] - 0.3, ub[3] + 0.3)] + \
              [g.ij(x, y) for y in np.arange(ub[1], ub[3] + 1e-6, G) for x in (ub[0] - 0.3, ub[2] + 0.3)]
    paths = {}
    order = sorted(range(len(conns)), key=lambda k: -math.dist(conns[k][1][2], conns[k][2][2]))
    pf = 0.5
    for it in range(6):
        for k in order:
            if k in paths:
                for c in paths[k]:
                    use[c[1], c[0]] -= 1
            net, a, b = conns[k]
            own = {idx[a[0]], idx[b[0]]}
            src = set(u1_edge) if free_u1(a) else {g.ij(*a[2])}
            dst = set(u1_edge) if free_u1(b) else {g.ij(*b[2])}
            if free_u1(a) and free_u1(b):
                src = {g.ij(*a[2])}
            p = astar(g, wall, cost, use, hist, src, dst, own, pf)
            paths[k] = p or []
            for c in paths[k]:
                use[c[1], c[0]] += 1
        over = np.maximum(use - 1, 0)
        hist += over * 0.6
        pf *= 1.8
    over = np.maximum(use - 1, 0)
    length = sum(len(p) for p in paths.values()) * G
    failed = [f"{conns[k][0]} {conns[k][1][0]}.{conns[k][1][1]}-{conns[k][2][0]}.{conns[k][2][1]}" for k, p in paths.items() if not p]
    res = dict(length=length, overflow=float(over.sum()), hot=int(over.max()), over_cells=int((over > 0).sum()),
               crossings=crossings, rf_cross=rf_cross, conns=len(conns), failed=failed)
    if draw:
        drawmap(g, wall, use, parts, rf_walls, draw, title, res)
    return res


def astar(g, wall, cost, use, hist, src, dst, own, pf):
    nx, ny = g.nx, g.ny
    ok = lambda i, j: wall[j, i] == 0 or wall[j, i] in own
    tx = [d[0] for d in dst]; ty = [d[1] for d in dst]
    tx0, tx1, ty0, ty1 = min(tx), max(tx), min(ty), max(ty)
    h = lambda i, j: max(0, tx0 - i, i - tx1) + max(0, ty0 - j, j - ty1)
    openq, best, came = [], {}, {}
    for s in src:
        if 0 <= s[0] < nx and 0 <= s[1] < ny:
            best[s] = 0.0
            heapq.heappush(openq, (h(*s), 0.0, s))
    while openq:
        f, d, c = heapq.heappop(openq)
        if c in dst:
            out = [c]
            while c in came:
                c = came[c]; out.append(c)
            return out
        if d > best.get(c, 1e18):
            continue
        i, j = c
        for di, dj, step in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)):
            a, b = i + di, j + dj
            if not (0 <= a < nx and 0 <= b < ny) or not ok(a, b):
                continue
            over = max(0.0, use[b, a] + 1 - 1)
            nd = d + step * cost[b, a] * (1 + hist[b, a]) * (1 + pf * over)
            if nd < best.get((a, b), 1e18):
                best[(a, b)] = nd; came[(a, b)] = c
                heapq.heappush(openq, (nd + h(a, b), nd, (a, b)))
    return None


def drawmap(g, wall, use, parts, rf_walls, out, title, res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(figsize=(6, 6 * (BOARD[3] - BOARD[1]) / (BOARD[2] - BOARD[0])), dpi=130)
    ext = (BOARD[0], BOARD[0] + g.nx * G, BOARD[1] + g.ny * G, BOARD[1])
    heat = np.ma.masked_where(use == 0, use)
    ax.imshow(heat, extent=ext, cmap="YlOrRd", vmin=0, vmax=4, interpolation="nearest", alpha=0.9)
    for r, (x, y, (b0, b1, b2, b3)) in parts.items():
        big = r.startswith(("U", "J", "SW", "RV", "H", "Y", "D1"))
        ax.add_patch(Rectangle((x + b0, y + b1), b2 - b0, b3 - b1, fill=False, lw=0.8 if big else 0.3,
                               ec="#333" if big else "#999"))
        if big:
            ax.text(x, y, r, fontsize=6, ha="center", va="center", weight="bold")
    for a, b in rf_walls:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#2c62c8", lw=2.5, alpha=0.8)
    ax.set_xlim(BOARD[0], BOARD[2]); ax.set_ylim(BOARD[3], BOARD[1]); ax.set_aspect("equal")
    ax.set_title(f"{title}: overflow {res['overflow']:.0f}, length {res['length']:.0f} mm", fontsize=8)
    ax.tick_params(labelsize=5)
    fig.tight_layout(); fig.savefig(out)


def main():
    from kipy import KiCad
    args = sys.argv[1:]
    draw = args[args.index("--draw") + 1] if "--draw" in args else None
    names = [a for a in args if a in CANDIDATES] or list(CANDIDATES)
    parts0, pads0 = load(KiCad().get_board())
    for name in names:
        cand = CANDIDATES[name]
        moves, rf = (cand["moves"], cand["rf"]) if isinstance(cand, dict) else (cand, None)
        parts, pads = apply(parts0, pads0, moves)
        overlaps = []
        rs = sorted(parts)
        for k, r in enumerate(rs):
            x, y, b = parts[r]
            for s in rs[k + 1:]:
                X, Y, B = parts[s]
                if x + b[0] < X + B[2] and X + B[0] < x + b[2] and y + b[1] < Y + B[3] and Y + B[1] < y + b[3]:
                    overlaps.append(f"{r}/{s}")
        res = score(parts, pads, f"{draw}/floorplan-{name}.png" if draw else None, name, repin=name != "now", rf_paths=rf)
        print(f"{name:4} length {res['length']:6.0f} mm  overflow {res['overflow']:5.0f} in {res['over_cells']:4} cells (worst {res['hot']})"
              f"  crossings {res['crossings']:4}  across RF {res['rf_cross']:3}  failed {len(res['failed'])}"
              f"  overlaps {len(overlaps)} {overlaps[:12]}", flush=True)


if __name__ == "__main__":
    main()
