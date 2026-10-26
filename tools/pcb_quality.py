"""Phase 5: checks that the routing looks planned, alongside DRC (tools/pcb_drc.py). DRC proves the copper is legal;
this proves it is tidy (routing-quality standard, 2026-10-25):
  angle   every segment runs at a multiple of 45 degrees;
  bend    every bend between two segments of a line turns 45 degrees (no 90 or 135 degree corners);
  exit    a line leaves a fine-pitch pad (an IC or connector) straight along the pad's long axis, outwards, for at
          least MIN_EXIT (pad edge to first bend), unless it reaches its other pad or an escape via within LOCAL;
          power nets need only leave straight;
  pitch   parallel neighbours of one net class that run side by side form a bus, and each bus keeps one pitch;
  clear   copper of other nets on the same layer is at least CLEAR away (catches problems in plans, before DRC runs);
  via     vias clear other nets' copper by CLEAR, their holes clear other copper by 0.3 mm and other holes by 0.5 mm;
  clock   Clock class tracks keep 0.4 mm from other tracks and vias outside the escape areas (CLOCK_ESCAPE);
  rf      no bottom-layer copper inside RF_BOTTOM_POLYS [AN4169 p12].
Tracks come from the board open in KiCad; --plan adds the hand-laid runs of a routing script (its RUNS table, top layer)
so a plan can be scored before any copper goes down.
Usage (from the repository root): python tools/pcb_quality.py [--plan SCRIPT.py[,SCRIPT.py]] [--nets A,B] [--min-exit 1.0]"""
import collections
import importlib.util
import math
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, "tools")
from pcb_astar import board_copper
from pcb_freeroute import CLOCK_ESCAPE, CLOCK_SMALL, RF_BOTTOM_ALLOW, RF_BOTTOM_POLYS

MIN_EXIT = 1.0     # mm of straight line beyond the pad's edge before the first bend
LOCAL = 4.5        # mm: a line that reaches its other pad within this length is a local connection (a decoupling
                   # capacitor or series part at the pin) and only has to leave straight, not for MIN_EXIT
CLEAR = 0.2        # mm, the board's copper clearance
BUS_GAP = 1.0      # mm, centre-to-centre: closer parallel neighbours count as one bus
BUS_RUN = 1.0      # mm of side-by-side overlap before two lines count as neighbours
TOL = 0.01


def net_classes():
    """Net name -> net class, from the project's netclass patterns (plain names and /names)."""
    import json
    import re
    pro = json.load(open("kicad/rev-a/IphoneFM.kicad_pro", encoding="utf-8"))
    pats = [(re.compile("^" + p["pattern"].replace("*", ".*") + "$"), p["netclass"])
            for p in pro["net_settings"].get("netclass_patterns") or []]

    def cls(net):
        for rx, c in pats:
            if rx.match(net):
                return c
        return "Default"
    return cls


POWER = ("Power",)


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


def courtyard_box(text, ref):
    """Courtyard of a footprint on the board as a shapely polygon (its F.CrtYd lines and rectangles, turned)."""
    from kicadcheck import kid, kids, sexpr
    for fp in kids(sexpr(text), "footprint"):
        if not any(p[1] == "Reference" and p[2] == ref for p in kids(fp, "property")):
            continue
        at = kid(fp, "at")
        fx, fy, fr = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        pts = []
        for g in fp[1:]:
            if isinstance(g, list) and g[0] in ("fp_line", "fp_rect", "fp_poly") and kid(g, "layer") and                     kid(g, "layer")[1] == "F.CrtYd":
                for q in [kid(g, k) for k in ("start", "end") if kid(g, k)] or kid(g, "pts")[1:]:
                    x, y = float(q[1]), float(q[2])
                    c, s = math.cos(math.radians(-fr)), math.sin(math.radians(-fr))
                    pts.append((fx + x * c - y * s, fy + x * s + y * c))
        if pts:
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            return box(min(xs), min(ys), max(xs), max(ys))
    return None


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
        plan = []
        for path in a[a.index("--plan") + 1].split(","):
            plan += load_plan(path, copper + plan)
        copper = copper + plan
    cls = net_classes()
    pads = [c for c in copper if c[0] == "pad"]
    tracks = [c for c in copper if c[0] == "track"]
    vias = [c for c in copper if c[0] == "via"]
    fp_pads = collections.defaultdict(list)
    for p in pads:
        fp_pads[p[4].split(".")[0]].append(p)
    fp_centre = {r: (sum(p[3][0] for p in ps) / len(ps), sum(p[3][1] for p in ps) / len(ps)) for r, ps in fp_pads.items()}
    # the exit rule covers fine-pitch parts (ICs, connectors): some two pads 0.8 mm apart or closer
    fine = {}
    for r, ps in fp_pads.items():
        cs = [(q[3][0], q[3][1]) for q in ps if q[1] or True]
        fine[r] = len(ps) >= 5 and any(0 < math.hypot(a[0] - b[0], a[1] - b[1]) <= 0.81 for i, a in enumerate(cs) for b in cs[i + 1:])
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
            if not p or not fine.get(p[4].split(".")[0]) or pad_at(net, l, ox, oy) is p:
                continue
            q = pad_at(net, l, ox, oy)
            if q and q[4].split(".")[0] == p[4].split(".")[0]:
                continue  # a bridge between two pins of one part (tied supply pins)
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
            # local: within LOCAL of the pin along the line (through its bends and branches) there is another pad,
            # or an escape via (a decoupling capacitor, series part or escape at the pin)
            local, best, todo = False, {key(sx, sy): 0.0}, [((sx, sy), 0.0)]
            while todo and not local:
                cur2, length = todo.pop()
                for j, o in ends[(net, l, key(*cur2))]:
                    d2 = length + math.hypot(o[0] - cur2[0], o[1] - cur2[1])
                    if d2 > LOCAL or best.get(key(*o), 1e9) <= d2:
                        continue
                    best[key(*o)] = d2
                    far = pad_at(net, l, *o)
                    if (far is not None and far is not p) or any(
                            v[1] == net and abs(v[3][0] - o[0]) < 1e-3 and abs(v[3][1] - o[1]) < 1e-3 for v in vias):
                        local = True
                        break
                    todo.append((o, d2))
            edge = phw if axis[0] else phh
            straight = abs((run_end[0] - px) * axis[0] + (run_end[1] - py) * axis[1]) - edge
            if straight < min_exit - TOL and not reached_pad and not local and cls(net) not in POWER and net != "GND":
                found["exit"].append(f"{net} leaves {p[4]} straight for {straight:.2f} mm")

    # pitch: neighbours run parallel, overlap, on one layer, nets differ
    pairs = collections.defaultdict(list)
    for i, t in enumerate(tracks):
        for j in range(i + 1, len(tracks)):
            u = tracks[j]
            if t[1] == u[1] or t[2] != u[2] or "GND" in (t[1], u[1]):   # ground links are not bus lines
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
            side = (bx0 - ax0) * -ua[1] + (by0 - ay0) * ua[0] > 0
            pairs[i].append((j, d, side))
            pairs[j].append((i, d, not side))
    def fp_of(k):
        g = tracks[k][3]
        l = next(iter(tracks[k][2]))
        ps = [pad_at(tracks[k][1], l, g[0], g[1]), pad_at(tracks[k][1], l, g[2], g[3])]
        return {q[4].split(".")[0] for q in ps if q}
    for i in list(pairs):  # keep the nearest neighbour on each side
        best = {}
        for j, d, s in pairs[i]:
            if s not in best or d < best[s][1]:
                best[s] = (j, d)
        # nearest neighbours of any class, then only same-class pairs count towards a bus's pitch
        pairs[i] = [(j, d, s) for s, (j, d) in best.items()
                    if not (fp_of(i) & fp_of(j)) and cls(tracks[i][1]) == cls(tracks[j][1])]
    for i in list(pairs):
        pairs[i] = [(j, d, s) for j, d, s in pairs[i] if any(k == i for k, _, _ in pairs[j])]
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
            stack += [j for j, _, _ in pairs[k]]
        seen |= group
        if only and not any(tracks[k][1] in only for k in group):
            continue
        ds = sorted({round(d, 3) for k in group for _, d, _ in pairs[k]})
        if ds and ds[-1] - ds[0] > TOL:
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

    # via
    holes = [(c[3][0], c[3][1], c[3][3] if c[0] == "via" else c[3][5], c[1]) for c in copper
             if c[0] == "via" or (c[0] == "pad" and c[3][5] > 0)]
    for v in vias:
        if only and v[1] not in only:
            continue
        x, y, r, hr = v[3]
        disc = Point(x, y).buffer(r)
        for onet, ol, shp, name in shapes:
            if onet == v[1] or (not onet and name == "track"):
                continue
            d = disc.distance(shp)
            if d < CLEAR - 1e-3 and not (name == "via" and abs(shp.centroid.x - x) < 1e-6 and abs(shp.centroid.y - y) < 1e-6):
                found["via"].append(f"{v[1]} via at ({x:.2f},{y:.2f}) {d:.2f} mm from {name} ({onet or 'no net'})")
            elif name != "via" and name != "track" and Point(x, y).buffer(hr).distance(shp) < 0.3 - 1e-3:
                found["via"].append(f"{v[1]} via hole at ({x:.2f},{y:.2f}) under 0.3 mm from {name} ({onet or 'no net'})")
        for hx, hy, ohr, onet in holes:
            dd = math.hypot(hx - x, hy - y)
            if 1e-6 < dd < hr + ohr + 0.5 - 1e-3:
                found["via"].append(f"{v[1]} via hole at ({x:.2f},{y:.2f}) {dd - hr - ohr:.2f} mm from a hole ({onet or 'no net'})")

    # clock
    text = KiCad().get_board().get_as_string()
    small = [courtyard_box(text, r) for r in CLOCK_SMALL]
    escape = unary_union([box(*b) for b in CLOCK_ESCAPE.values()])
    others = [(c[1], c[2], c[0], (LineString([c[3][:2], c[3][2:4]]).buffer(c[3][4]) if c[0] == "track"
                                 else Point(c[3][0], c[3][1]).buffer(c[3][2]))) for c in tracks + vias]
    for t in shown:
        if cls(t[1]) != "Clock":
            continue
        g = t[3]
        seg = LineString([g[:2], g[2:4]])
        if any(s is not None and seg.intersects(s) for s in small):
            continue
        part = seg.difference(escape)
        if part.is_empty:
            continue
        l = next(iter(t[2]))
        for onet, olay, kind, shp in others:
            if onet == t[1] or l not in olay:
                continue
            d = part.distance(shp) - g[4]
            if d < 0.4 - 1e-3:
                found["clock"].append(f"{t[1]} ({g[0]:.2f},{g[1]:.2f})-({g[2]:.2f},{g[3]:.2f}) {d:.2f} mm from {kind} ({onet})")

    # rf
    zones = [Polygon(p) for p in RF_BOTTOM_POLYS]
    for t in shown + [v for v in vias if only is None or v[1] in only]:
        g = t[3]
        shp = LineString([g[:2], g[2:4]]).buffer(g[4]) if t[0] == "track" else Point(g[0], g[1]).buffer(g[2])
        allow = [Polygon(p) for p in RF_BOTTOM_ALLOW.get(t[1], [])]
        if any(a.contains(shp) for a in allow):
            continue
        if "B.Cu" in t[2] and t[1] != "GND" and any(z.intersects(shp) for z in zones):
            found["rf"].append(f"{t[1]} {t[0]} at ({g[0]:.2f},{g[1]:.2f}) on the bottom under the RF area")

    kinds = ("angle", "bend", "exit", "pitch", "clear", "via", "clock", "rf")
    print(f"{len(shown)} segments checked: " + ", ".join(f"{k} {len(found[k])}" for k in kinds))
    for k in kinds:
        for line in dict.fromkeys(found[k]):
            print(f"  {k:5} {line}")
    sys.exit(1 if any(found.values()) else 0)


if __name__ == "__main__":
    main()
