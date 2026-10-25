"""Phase 5: lists the connections still open once the board's copper and the routing plans are taken together: for each
net, the groups of pads that no copper (tracks, vias, through-hole pads) joins yet. Zones are left out (GND comes from
the pours), so GND is skipped unless asked for.
Usage (from the repository root, board open in KiCad): python tools/pcb_open.py [--plan A.py,B.py] [--gnd]"""
import collections
import sys

from shapely.geometry import LineString, Point, box

sys.path.insert(0, "tools")
from kipy import KiCad
from pcb_astar import board_copper
from pcb_quality import load_plan


def shape(kind, g):
    if kind == "pad":
        x, y, hw, hh, sh, _ = g
        return Point(x, y).buffer(hw) if sh == "circle" else box(x - hw, y - hh, x + hw, y + hh)
    if kind == "track":
        return LineString([g[:2], g[2:4]]).buffer(g[4])
    return Point(g[0], g[1]).buffer(g[2])


def main():
    a = sys.argv
    copper = board_copper(KiCad().get_board().get_as_string())
    if "--plan" in a:
        for path in a[a.index("--plan") + 1].split(","):
            copper += load_plan(path, copper)
    by_net = collections.defaultdict(list)
    for kind, net, lay, g, name in copper:
        if net and (net != "GND" or "--gnd" in a):
            by_net[net].append((kind, lay, shape(kind, g), name))
    report = []
    for net, items in sorted(by_net.items()):
        parent = list(range(len(items)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i][1] & items[j][1] and items[i][2].intersects(items[j][2]):
                    parent[find(i)] = find(j)
        groups = collections.defaultdict(list)
        for i, it in enumerate(items):
            if it[0] == "pad":
                groups[find(i)].append(it[3])
        groups = [g for g in groups.values() if g]
        if len(groups) > 1:
            report.append((net, groups))
    for net, groups in report:
        print(f"{net}: " + " | ".join(" ".join(sorted(set(g))) for g in groups))
    print(f"{len(report)} nets open")


if __name__ == "__main__":
    main()
