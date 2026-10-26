"""Step 5.1 (planned last, laid first): ground vias. Exposed pads get via arrays between their paste windows (U1, U4,
U7; U2's are in tools/pcb_route_u2.py); every other ground pad on the top layer that no planned copper already takes
to a via (or to a through-hole ground pin) gets one of its own, with a straight link of 0.25 mm at a multiple of 45
degrees, at the nearest spot that clears all other copper of every plan on both layers, hole spacing, the board edge
and the Clock class's 0.4 mm. A pad within reach of a via placed for its neighbour shares it.
The sites are computed from the board and the other plans each time, so this plan is checked and laid after them.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_gnd.py [list] | lay [--dry-run]"""
import math
import sys

from shapely.geometry import LineString, Point, box

sys.path.insert(0, "tools")
from pcb_plan import Plan, main

PLANS = ["tools/pcb_route_u1.py", "tools/pcb_route_u4.py", "tools/pcb_route_rf.py", "tools/pcb_route_u2.py",
         "tools/pcb_route_j1.py", "tools/pcb_route_att.py", "tools/pcb_route_north.py"]
VIA_R, DRILL_R, LINK = 0.3, 0.15, 0.25
EDGE = (12.7, 59.56, 59.15, 130.96)
EP_VIAS = {   # exposed pads: vias between the paste windows
    "U1": [(x, y) for x in (34.735, 36.135, 37.535) for y in (89.195, 90.595, 91.995)],
    "U4": [(53.9, 86.0)],
    "U7": [(42.8, 117.8)],
}
# ground pins bridged straight into their own exposed pad (as U1's and U2's are in their plans)
BRIDGES = {"U4": (53.9, 86.0, 0.9), "U7": (42.8, 117.8, 1.375)}
NO_BRIDGE = ("U4.6",)     # U4's corner ground pad: RST's pin is in the way, so it gets a via
# by hand: C6's ground pad doglegs round CE's bottom line; RV2's detent pads join its ground pin down the pad column
EXTRA_VIAS = [(41.955, 86.75), (50.1, 88.0)]
EXTRA_LINKS = [[(42.105, 87.645), (42.105, 86.9), (41.955, 86.75)], [(26.8, 95.0), (26.8, 91.0)],
               [(49.87, 85.75), (49.87, 87.77), (50.1, 88.0)]]      # C37, C38 (0.4 mm off SCK)
CLOCK = ("/FSK_CLK", "/FSK_CLK_MCU", "/REF20", "/REF20_MCU", "/RX_RCLK", "/RX_SCK", "/RX_SCK_MCU", "/LMX_CLK")


def shape(kind, g):
    if kind == "pad":
        x, y, hw, hh, sh, _ = g
        return Point(x, y).buffer(hw) if sh == "circle" else box(x - hw, y - hh, x + hw, y + hh)
    if kind == "track":
        return LineString([g[:2], g[2:4]]).buffer(g[4])
    return Point(g[0], g[1]).buffer(g[2])


def build():
    from kipy import KiCad
    from pcb_astar import board_copper
    from pcb_quality import load_plan
    copper = board_copper(KiCad().get_board().get_as_string())
    for p in PLANS:
        copper += load_plan(p, copper)
    P = Plan()
    holes = [(g[0], g[1], g[3] if k == "via" else g[5]) for k, n, l, g, _ in copper
             if k == "via" or (k == "pad" and g[5] > 0)]
    others = [(k, n, l, shape(k, g)) for k, n, l, g, _ in copper if n != "GND"]
    pads = [(k, n, l, shape(k, g), name, g) for k, n, l, g, name in copper if k == "pad"]
    gnd_vias = [(g[0], g[1]) for k, n, l, g, _ in copper if k == "via" and n == "GND"]

    def via_ok(x, y):
        v = Point(x, y).buffer(VIA_R)
        if not (EDGE[0] + 0.8 <= x <= EDGE[2] - 0.8 and EDGE[1] + 0.8 <= y <= EDGE[3] - 0.8):
            return False
        for hx, hy, hr in holes:
            if math.hypot(x - hx, y - hy) < DRILL_R + hr + 0.5:
                return False
        for k, n, l, s in others:
            if v.distance(s) < (0.4 if n in CLOCK and k == "track" else 0.2):
                return False
        return all(v.distance(s) >= 0.05 for k, n, l, s, name, g in pads if n == "GND")   # never in a pad

    def link_ok(a, b, own):
        t = LineString([a, b]).buffer(LINK / 2)
        for k, n, l, s in others:
            if "F.Cu" in l and t.distance(s) < (0.4 if n in CLOCK and k == "track" else 0.2):
                return False
        return all(name == own or not t.intersects(s) for k, n, l, s, name, g in pads if n == "GND" and "F.Cu" in l)

    for ref, sites in EP_VIAS.items():
        for x, y in sites:
            P.via("GND", x, y)
            gnd_vias.append((x, y))
    for x, y in EXTRA_VIAS:
        P.via("GND", x, y)
        gnd_vias.append((x, y))
    for pts in EXTRA_LINKS:
        P.run("GND", pts, LINK)
    for ref, (cx, cy, h) in BRIDGES.items():
        for k, n, l, g, name in copper:
            if k == "pad" and n == "GND" and name.startswith(ref + ".") and max(g[2], g[3]) < h and name not in NO_BRIDGE:
                x, y = g[0], g[1]
                if abs(x - cx) > h:      # side pins: in along x
                    P.run("GND", [(x, y), (cx + math.copysign(h - 0.05, x - cx), y)], 0.2)
                elif abs(y - cy) > h:    # top and bottom pins: in along y
                    P.run("GND", [(x, y), (x, cy + math.copysign(h - 0.05, y - cy))], 0.2)
                else:                    # corner pads inside the pad's span
                    continue
    copper = copper + [("track", "GND", {"F.Cu"}, (a[0], a[1], b[0], b[1], w / 2), "plan")
                       for n, lay, pts, w in P.runs for a, b in zip(pts, pts[1:])]
    # ground pads already reaching a via through ground copper on top (or a through-hole ground pin)
    gnd = [(k, l, shape(k, g), name, g) for k, n, l, g, name in copper if n == "GND" and "F.Cu" in l]
    gnd += [("via", {"F.Cu", "B.Cu"}, Point(x, y).buffer(VIA_R), "", None) for x, y in gnd_vias]
    parent = list(range(len(gnd)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(gnd)):
        for j in range(i + 1, len(gnd)):
            if gnd[i][2].intersects(gnd[j][2]):
                parent[find(i)] = find(j)
    anchored = {find(i) for i, it in enumerate(gnd) if it[0] == "via" or (it[0] == "pad" and len(it[1]) == 2)}
    todo = [it for i, it in enumerate(gnd) if it[0] == "pad" and find(i) not in anchored and "B.Cu" not in it[1]]
    missing, done = [], set()
    comp = {it[3]: find(i) for i, it in enumerate(gnd) if it[0] == "pad"}
    for k, l, s, name, g in sorted(todo, key=lambda t: t[3]):
        if comp[name] in done:            # its group got a via from a pad before it
            continue
        x, y, hw, hh, sh, _ = g
        best = None
        for vx, vy in gnd_vias:           # share a nearby via
            d = math.hypot(vx - x, vy - y)
            ang = math.degrees(math.atan2(vy - y, vx - x)) % 45
            if d < max(hw, hh) + 1.2 and min(ang, 45 - ang) < 0.5 and link_ok((x, y), (vx, vy), name):
                best = (d, vx, vy, False) if not best or d < best[0] else best
        if not best:
            for a in range(0, 360, 45):
                ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
                for step in range(0, 30):
                    d = max(abs(ux) * hw + abs(uy) * hh, 0) + VIA_R + 0.05 + 0.05 * step
                    vx, vy = round(x + ux * d, 3), round(y + uy * d, 3)
                    if via_ok(vx, vy) and link_ok((x, y), (vx, vy), name):
                        if not best or d < best[0]:
                            best = (d, vx, vy, True)
                        break
        if not best:
            missing.append(name)
            continue
        d, vx, vy, new = best
        done.add(comp[name])
        if new:
            P.via("GND", vx, vy)
            gnd_vias.append((vx, vy))
            holes.append((vx, vy, DRILL_R))
        P.run("GND", [(x, y), (vx, vy)], LINK)
    return P, missing


def plan(copper=None):
    return build()[0].copper()


if __name__ == "__main__":
    PL, MISSING = build()
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print(f"{len(PL.vias)} ground vias, {len(PL.runs)} links; no site for: {', '.join(MISSING) or 'none'}")
    else:
        main(PL, "Step 5.1: ground vias")
