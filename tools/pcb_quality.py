"""Phase 5: checks that the routing looks planned, alongside DRC (tools/pcb_drc.py). DRC proves the copper is legal;
this proves it is tidy (routing-quality standard, 2026-10-25):
  angle   every segment runs at a multiple of 45 degrees;
  bend    every bend between two segments of a line turns 45 degrees (no 90 or 135 degree corners);
  exit    a line leaves an IC or connector pad straight along the pad's long axis, outwards, for at least MIN_EXIT
          (measured from the pad's edge to the first bend), unless it reaches its other pad first;
  pitch   parallel neighbours of different nets that run side by side form a bus, and each bus keeps one pitch;
  clear   copper of other nets on the same layer is at least CLEAR away (catches problems in plans, before DRC runs);
  rf      no bottom-layer copper inside RF_BOTTOM_POLYS [AN4169 p12].
Tracks come from the board open in KiCad; --plan adds the hand-laid runs of a routing script (its RUNS table, top layer)
so a plan can be scored before any copper goes down.
Usage (from the repository root): python tools/pcb_quality.py [--plan tools/pcb_route_rf.py] [--nets A,B] [--min-exit 1.0]"""
import collections
import importlib.util
import math
import sys

from shapely.geometry import LineString, Point, Polygon, box

sys.path.insert(0, "tools")
from pcb_astar import board_copper
from pcb_freeroute import RF_BOTTOM_POLYS

MIN_EXIT = 1.0     # mm of straight line beyond the pad's edge before the first bend
LOCAL = 2.5        # mm: a line that reaches its other pad within this length is a local connection (a decoupling
                   # capacitor or series part at the pin) and only has to leave straight, not for MIN_EXIT
CLEAR = 0.2        # mm, the board's copper clearance
BUS_GAP = 1.0      # mm, centre-to-centre: closer parallel neighbours count as one bus
BUS_RUN = 1.0      # mm of side-by-side overlap before two lines count as neighbours
TOL = 0.01


def load_plan(path, copper):
    spec = importlib.util.spec_from_file_location("plan", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "plan"):
        return mod.plan(copper)
    out = []
    for net, runs in mod.RUNS.items():
        for pts, w in runs:
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                out.append(("track", net, {"F.Cu"}, (x0, y0, x1, y1, w / 2), "plan"))
    return out


def pad_shape(g):
    x, y, hw, hh, shape, _ = g
    return Point(x, y).buffer(hw) if shape == "circle" else box(x - hw, y - hh, x + hw, y + hh)


def key(x, y):
    return round(x, 3), round(y, 3)


def heading(ax, ay, bx, by):
    return math.degrees(math.atan2(by - ay, bx - ax)) % 360


def main():
    a = sys.argv[1:]
    min_exit = float(a[a.index("--min-exit") + 1]) if "--min-exit" in a else MIN_EXIT
    only = set(a[a.index("--nets") + 1].split(",")) if "--nets" in a else None
    from kipy import KiCad
    copper = board_copper(KiCad().get_board().get_as_string())
    if "--plan" in a:
        plan = load_plan(a[a.index("--plan") + 1], copper)
        planned = {c[1] for c in plan}
        copper = [c for c in copper if not (c[0] in ("track", "via") and c[1] in planned)] + plan
    pads = [c for c in copper if c[0] == "pad"]
    tracks = [c for c in copper if c[0] == "track"]
    vias = [c for c in copper if c[0] == "via"]
    fp_pads = collections.defaultdict(list)
    for p in pads:
        fp_pads[p[4].split(".")[0]].append(p)
    fp_centre = {r: (sum(p[3][0] for p in ps) / len(ps), sum(p[3][1] for p in ps) / len(ps)) for r, ps in fp_pads.items()}
    shown = [t for t in tracks if only is None or t[1] in only]
    found = collections.defaultdict(list)

    # angle
    for _, net, lay, (x0, y0, x1, y1, hw), _ in shown:
        h = heading(x0, y0, x1, y1)
        if min(h % 45, 45 - h % 45) > 0.5:
            found["angle"].append(f"{net} ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f}) at {h:.1f} deg")

    # ends by net and layer, for bends and straight runs
    ends = collections.defaultdict(list)
    for i, (_, net, lay, (x0, y0, x1, y1, hw), _) in enumerate(tracks):
        l = next(iter(lay))
        ends[(net, l, key(x0, y0))].append((i, (x1, y1)))
        ends[(net, l, key(x1, y1))].append((i, (x0, y0)))
    on_pad = collections.defaultdict(list)
    for p in pads:
        for l in p[2]:
            on_pad[(p[1], l)].append(p)

    def pad_at(net, l, x, y):
        for p in on_pad[(net, l)]:
            if pad_shape(p[3]).buffer(1e-3).contains(Point(x, y)):
                return p
        return None

    # bend
    for (net, l, pt), lst in ends.items():
        if (only and net not in only) or len(lst) != 2 or pad_at(net, l, *pt):
            continue
        (_, oa), (_, ob) = lst
        h1, h2 = heading(oa[0], oa[1], *pt), heading(pt[0], pt[1], *ob)
        turn = abs((h2 - h1 + 180) % 360 - 180)
        if turn > 45.5:
            found["bend"].append(f"{net} at ({pt[0]:.2f},{pt[1]:.2f}) turns {turn:.0f} deg")

    # exit
    for i, (_, net, lay, (x0, y0, x1, y1, hw), _) in enumerate(tracks):
        if only and net not in only:
            continue
        l = next(iter(lay))
        for (sx, sy), (ox, oy) in (((x0, y0), (x1, y1)), ((x1, y1), (x0, y0))):
            p = pad_at(net, l, sx, sy)
            if not p or len(fp_pads[p[4].split(".")[0]]) < 5 or pad_at(net, l, ox, oy) is p:
                continue
            px, py, phw, phh, shape, _ = p[3]
            if shape == "circle" or abs(phw - phh) < 0.02:
                continue
            cx, cy = fp_centre[p[4].split(".")[0]]
            axis = (1.0 if px > cx else -1.0, 0.0) if phw > phh else (0.0, 1.0 if py > cy else -1.0)
            d = math.hypot(ox - sx, oy - sy)
            u = ((ox - sx) / d, (oy - sy) / d) if d else axis
            if u[0] * axis[0] + u[1] * axis[1] < 0.999:
                found["exit"].append(f"{net} leaves {p[4]} sideways or inwards at ({sx:.2f},{sy:.2f})->({ox:.2f},{oy:.2f})")
                continue
            # walk the straight run to its first bend, or to another pad
            run_end, prev, cur, seen = (ox, oy), i, (ox, oy), {i}
            while True:
                nxt = [(j, o) for j, o in ends[(net, l, key(*cur))] if j not in seen]
                if pad_at(net, l, *cur) or len(nxt) != 1:
                    reached_pad = bool(pad_at(net, l, *cur))
                    break
                j, o = nxt[0]
                dj = math.hypot(o[0] - cur[0], o[1] - cur[1])
                if dj == 0 or abs((o[0] - cur[0]) / dj - u[0]) > 1e-3 or abs((o[1] - cur[1]) / dj - u[1]) > 1e-3:
                    reached_pad = False
                    break
                seen.add(j)
                cur = o
                run_end = o
            # local: follow the line on through its bends to where it ends
            length, cur2, seen2, prev2 = 0.0, (sx, sy), set(), None
            while True:
                nxt = [(j, o) for j, o in ends[(net, l, key(*cur2))] if j not in seen2]
                if len(nxt) != 1 or (prev2 is not None and pad_at(net, l, *cur2)):
                    break
                j, o = nxt[0]
                seen2.add(j)
                length += math.hypot(o[0] - cur2[0], o[1] - cur2[1])
                prev2, cur2 = cur2, o
            far = pad_at(net, l, *cur2)
            local = far is not None and far is not p and length <= LOCAL
            edge = phw if axis[0] else phh
            straight = abs((run_end[0] - px) * axis[0] + (run_end[1] - py) * axis[1]) - edge
            if straight < min_exit - TOL and not reached_pad and not local:
                found["exit"].append(f"{net} leaves {p[4]} straight for {straight:.2f} mm")

    # pitch: neighbours run parallel, overlap, on one layer, nets differ
    pairs = collections.defaultdict(list)
    for i, t in enumerate(tracks):
        for j in range(i + 1, len(tracks)):
            u = tracks[j]
            if t[1] == u[1] or t[2] != u[2]:
                continue
            (ax0, ay0, ax1, ay1, _), (bx0, by0, bx1, by1, _) = t[3], u[3]
            la, lb = math.hypot(ax1 - ax0, ay1 - ay0), math.hypot(bx1 - bx0, by1 - by0)
            if la < BUS_RUN or lb < BUS_RUN:
                continue
            ua = ((ax1 - ax0) / la, (ay1 - ay0) / la)
            ub = ((bx1 - bx0) / lb, (by1 - by0) / lb)
            if abs(abs(ua[0] * ub[0] + ua[1] * ub[1]) - 1) > 1e-4:
                continue
            d = abs((bx0 - ax0) * -ua[1] + (by0 - ay0) * ua[0])
            if d > BUS_GAP:
                continue
            s = sorted([0, la])
            tb = sorted([(bx0 - ax0) * ua[0] + (by0 - ay0) * ua[1], (bx1 - ax0) * ua[0] + (by1 - ay0) * ua[1]])
            if min(s[1], tb[1]) - max(s[0], tb[0]) < BUS_RUN:
                continue
            pairs[i].append((j, d))
            pairs[j].append((i, d))
    seen = set()
    for i in list(pairs):
        if i in seen:
            continue
        group, stack = set(), [i]
        while stack:
            k = stack.pop()
            if k in group:
                continue
            group.add(k)
            stack += [j for j, _ in pairs[k]]
        seen |= group
        if only and not any(tracks[k][1] in only for k in group):
            continue
        ds = sorted({round(d, 2) for k in group for _, d in pairs[k]})
        if ds[-1] - ds[0] > TOL:
            nets = sorted({tracks[k][1].lstrip("/") for k in group})
            found["pitch"].append(f"bus of {', '.join(nets)}: pitches {', '.join(f'{d:.2f}' for d in ds)} mm")

    # clear
    shapes = []
    for c in copper:
        for l in c[2]:
            if c[0] == "pad":
                shapes.append((c[1], l, pad_shape(c[3]), c[4]))
            elif c[0] == "via":
                shapes.append((c[1], l, Point(c[3][0], c[3][1]).buffer(c[3][2]), "via"))
            else:
                g = c[3]
                shapes.append((c[1], l, LineString([g[:2], g[2:4]]).buffer(g[4]), "track"))
    for t in shown:
        net, l, g = t[1], next(iter(t[2])), t[3]
        line = LineString([g[:2], g[2:4]]).buffer(g[4])
        for onet, ol, shp, name in shapes:
            if ol != l or onet == net or (not onet and name == "track"):
                continue
            d = line.distance(shp)
            if d < CLEAR - 1e-3:
                found["clear"].append(f"{net} ({g[0]:.2f},{g[1]:.2f})-({g[2]:.2f},{g[3]:.2f}) {d:.2f} mm from {name} ({onet or 'no net'})")

    # rf
    zones = [Polygon(p) for p in RF_BOTTOM_POLYS]
    for t in shown + [v for v in vias if only is None or v[1] in only]:
        g = t[3]
        shp = LineString([g[:2], g[2:4]]).buffer(g[4]) if t[0] == "track" else Point(g[0], g[1]).buffer(g[2])
        if "B.Cu" in t[2] and t[1] != "GND" and any(z.intersects(shp) for z in zones):
            found["rf"].append(f"{t[1]} {t[0]} at ({g[0]:.2f},{g[1]:.2f}) on the bottom under the RF area")

    print(f"{len(shown)} segments checked: " + ", ".join(f"{k} {len(found[k])}" for k in ("angle", "bend", "exit", "pitch", "clear", "rf")))
    for k in ("angle", "bend", "exit", "pitch", "clear", "rf"):
        for line in dict.fromkeys(found[k]):
            print(f"  {k:5} {line}")
    sys.exit(1 if any(found.values()) else 0)


if __name__ == "__main__":
    main()
