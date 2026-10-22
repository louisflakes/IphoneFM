"""Wires one chain of the Rev A schematic: every net among that chain's parts, as netlist.json says, on the 1.27 mm grid.
A maze router joins each net's pins one at a time to the part of the net already drawn. It never passes through a part
body, a power symbol or another net's pin, never turns or ends on another net's wire (so nets can cross but never touch),
and avoids text where it can. A pin is never entered from its body side. Pins of parts in other chains are left for
the net labels of step 1.30 when they sit in another zone of the sheet; within a zone a net is wired whole, by the
earliest chain that has a pin in it, and a passive placed at a pin (local_to) counts as being in that pin's chain. Everything this tool draws for chain N has a uuid starting with UID + N, so a rerun of that
chain replaces it.
Usage: python tools/sch_wire.py <chain> [--dry-run]"""
import heapq
import json
import math
import re
import sys

from kicadcheck import sexpr, kids, kid, atom, candidates
from sch_place import SCH, NETLIST, LIB, CW, prefix, symbols_and_pins
from sch_power import balanced, WIRED_RAILS

G = 1.27
UID = "5e1c"
SKIP = {"NC"}
# pins left unwired for the step 1.30 net labels: a part's far side that carries the net on toward another chain
# nets drawn along a given path instead of routed (absolute mm corners). Chain 6: U7's six control lines run left past
# their pull-downs, turn down one column each (row k at R_k - 6.35 mm) and step across to SW3's contacts; the inner
# lines turn first, so nothing crosses
PATHS = {}
for _k, _net in enumerate(["ATT_C16", "ATT_C8", "ATT_C4", "ATT_C2", "ATT_C1", "ATT_C0_5"]):
    _y, _x, _s = 132.08 + 2.54 * _k, 321.31 + 12.7 * _k, 355.6 + 2.54 * _k
    _yf = (170.18, 167.64, 165.1, 162.56, 162.56, 165.1)[_k]
    PATHS[_net] = [(403.86, _y), (_x, _y), (_x, _yf), (_s, _yf), (_s, 177.8)]
# chain 8: U4's left-side lines (pin tips at x 365.76): I2C up to its pull-ups; RSTB and the I2S lines down in a ribbon
# to R19 and the series resistors; the GPO lines straight into their caps
PATHS.update({
    # chain 7: U5 CTRL drops below the FL1 line to C31 and R17; U5 VDD runs up and across to R16
    "RF_CTRL": [(515.62, 134.62), (513.08, 134.62), (513.08, 147.32), (499.11, 147.32)],
    "U5_VDD": [(530.86, 116.84), (530.86, 111.76), (541.02, 111.76)],
    # chain 3: PA9 and PA10 step down to R7 and R8 right of the space PA11-PA15 need for their labels and test pads
    "FSK_FS_MCU": [(238.76, 241.3), (261.62, 241.3), (261.62, 248.92), (265.43, 248.92)],
    "FSK_DATA_MCU": [(238.76, 243.84), (259.08, 243.84), (259.08, 259.08), (265.43, 259.08)],
    # chain 9: the LED cathodes into their resistors, the lower two stepped down (blue's step nearest the LED)
    "LED_R_K": [(137.16, 297.18), (125.73, 297.18)],
    "LED_G_K": [(137.16, 302.26), (130.81, 302.26), (130.81, 309.88), (125.73, 309.88)],
    "LED_B_K": [(137.16, 307.34), (133.35, 307.34), (133.35, 322.58), (125.73, 322.58)],
    "I2C_SCL": [(365.76, 289.56), (358.14, 289.56), (358.14, 281.94)],
    "I2C_SDA": [(365.76, 292.1), (340.36, 292.1), (340.36, 284.48)],
    "RX_RST": [(365.76, 297.18), (298.45, 297.18), (298.45, 341.63)],
    "RX_SCK": [(365.76, 309.88), (312.42, 309.88), (312.42, 341.63)],
    "RX_FS": [(365.76, 312.42), (326.39, 312.42), (326.39, 341.63)],
    "RX_SD": [(365.76, 314.96), (340.36, 314.96), (340.36, 341.63)],
    "RX_GPO1": [(365.76, 320.04), (350.52, 320.04)],
    "RX_GPO2": [(365.76, 322.58), (360.68, 322.58)],
})
# nets wired across a zone boundary because their parts meet at it
WIRE_ACROSS = {"TX_RF_ATT", "FMI"}  # U7 RF2 feeds FL1 directly; U4 FMI runs straight to its front end
LEAVE = {("U6", "6"), ("U6", "4")}  # USBLC6 pass-through pins, on toward U1
RAILS = {"VBUS", "3V3", "VDDA", "RX_VDD", "GND"}  # drawn with power symbols (sch_power.py)
BEND, CROSS, TEXT = 3, 25, 6  # extra cost, in grid steps, of a turn, a crossing and a step through text


def cell(x, y):
    return (round(x / G), round(y / G))


def uid(chain, n):
    return f"{UID}{chain:04x}-0000-4000-8000-{n:012x}"


def strip_chain(text, chain):
    out, i = [], 0
    for m in re.finditer(r'\n\t\((wire|junction)\b', text):
        if m.start() < i:
            continue
        s = m.start() + 2
        e = balanced(text, s)
        if f'(uuid "{UID}{chain:04x}-' in text[s:e]:
            out.append(text[i:m.start()])
            i = e
    out.append(text[i:])
    return "".join(out)


def to_sheet(sym, lx, ly):
    a = math.radians(sym["rot"])
    rx, ry = lx * math.cos(a) - ly * math.sin(a), lx * math.sin(a) + ly * math.cos(a)
    if sym.get("mirror") == "y":
        rx = -rx
    elif sym.get("mirror") == "x":
        ry = -ry
    return sym["x"] + rx, sym["y"] - ry


def bodies(root, placed):
    """{ref: (x0, y0, x1, y1)} body outline on the sheet: the symbol's rectangles plus its pin ends"""
    rects = {}
    for ls in kids(kid(root, "lib_symbols"), "symbol"):
        pts = []
        for sub in kids(ls, "symbol"):
            for r in kids(sub, "rectangle"):
                pts += [(float(kid(r, "start")[1]), float(kid(r, "start")[2])), (float(kid(r, "end")[1]), float(kid(r, "end")[2]))]
        rects[ls[1]] = pts
    out = {}
    for ref, s in placed.items():
        pins = [(x, y) for x, y, _ in s["pins"].values()]
        if prefix(ref) in LIB:  # a two-pin passive: the width of its body between its pin tips (a wire may meet a tip from the side)
            xs, ys = [p[0] for p in pins], [p[1] for p in pins]
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            if x1 - x0 < 1:
                x0, x1, y0, y1 = x0 - 1.27, x1 + 1.27, y0 + 1.27, y1 - 1.27
            else:
                x0, x1, y0, y1 = x0 + 1.27, x1 - 1.27, y0 - 1.27, y1 + 1.27
        else:
            pts = [to_sheet(s, x, y) for x, y in rects.get(s["lib_id"], [])] + pins
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        out[ref] = (x0, y0, x1, y1)
    return out


def text_cells(root):
    """Grid cells under every visible field (soft obstacles)"""
    cells = set()
    for s in kids(root, "symbol"):
        rot = float(kid(s, "at")[3]) if len(kid(s, "at")) > 3 else 0
        for p in kids(s, "property"):
            eff = kid(p, "effects")
            if eff is None or kid(eff, "hide") is not None:
                continue
            at = kid(p, "at")
            x, y = float(at[1]), float(at[2])
            w = len(p[2]) * CW
            j = kid(eff, "justify")
            just = j[1] if j else "center"
            if just in ("left", "right") and rot in (90, 180):
                just = "right" if just == "left" else "left"
            x0 = x if just == "left" else x - w if just == "right" else x - w / 2
            c0, c1 = cell(x0, y), cell(x0 + w, y)
            for cx in range(c0[0], c1[0] + 1):
                for cy in {round((y + dy) / G) for dy in (-0.6, 0, 0.6)}:  # 1.27 mm text: its own row, and a half row either side
                    cells.add((cx, cy))
    return cells


def existing_wires(root):
    """[(cell a, cell b)] for every wire on the sheet"""
    out = []
    for w in kids(root, "wire"):
        xy = kids(kid(w, "pts"), "xy")
        out.append((cell(float(xy[0][1]), float(xy[0][2])), cell(float(xy[1][1]), float(xy[1][2]))))
    return out


def line_cells(a, b):
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0))
    return [(x0 + (x1 - x0) * i // max(n, 1), y0 + (y1 - y0) * i // max(n, 1)) for i in range(n + 1)]


def route(src, dst, dst_in, hard, foreign, foreign_ends, soft, bound):
    """A* from any cell in src {cell: allowed first directions or None} to dst, arriving moving along dst_in"""
    D = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    h = lambda c: abs(c[0] - dst[0]) + abs(c[1] - dst[1])
    pq, best, prev = [], {}, {}
    for c, dirs in src.items():
        for d in (dirs or D):
            st = (c, d, True)
            best[st] = 0
            heapq.heappush(pq, (h(c), 0, st))
    while pq:
        f, g, st = heapq.heappop(pq)
        c, d, first = st
        if g > best.get(st, 1e9):
            continue
        if c == dst:
            path = [c]
            while st in prev:
                st = prev[st]
                path.append(st[0])
            return path[::-1]
        for nd in D:
            if nd == (-d[0], -d[1]) or (first and nd != d):
                continue
            n = (c[0] + nd[0], c[1] + nd[1])
            if not (bound[0] <= n[0] <= bound[2] and bound[1] <= n[1] <= bound[3]):
                continue
            if n == dst:
                if nd == (-dst_in[0], -dst_in[1]):  # never into a pin from its body side
                    continue
            elif n in hard or n in foreign_ends:
                continue
            turn = nd != d and not first
            if turn and c in foreign:  # never bend on another net's wire
                continue
            if n in foreign and foreign[n] == (nd[0] != 0):  # never run along another net's wire
                continue
            cost = 1 + (BEND if turn else 0) + (CROSS if n in foreign else 0) + (TEXT if n in soft else 0)
            ns = (n, nd, False)
            if g + cost < best.get(ns, 1e9):
                best[ns] = g + cost
                prev[ns] = st
                heapq.heappush(pq, (g + cost + h(n), g + cost, ns))
    return None


# zones of the sheet (kicad/rev-a/sheet-plan.md), x0, y0, x1, y1 in mm; the first that holds a part's origin is its zone
ZONES = [("clock", 158, 19, 288, 90), ("mcu", 158, 99, 288, 401), ("transmit", 297, 19, 431, 214),
         ("receive", 297, 223, 431, 401), ("rf_out", 441, 19, 575, 214), ("rx_front", 441, 223, 575, 312),
         ("usb", 19, 19, 167, 161), ("controls", 19, 170, 167, 401)]


def zone_of(sym):
    x, y = sym["x"], sym["y"]
    for name, x0, y0, x1, y1 in ZONES:
        if x0 <= x <= x1 and y0 <= y <= y1:
            return name
    return min(ZONES, key=lambda z: max(z[1] - x, 0, x - z[3]) + max(z[2] - y, 0, y - z[4]))[0]  # in a gutter: the nearest


def obstacles(root, placed, body):
    """Cells a wire or label must avoid: part bodies and pins (hard), power symbols with their names (hard), field
    text (soft), and every wire already drawn (foreign: crossable at right angles, never along or at an end)"""
    hard = set()
    for ref, (x0, y0, x1, y1) in body.items():
        a, b = cell(x0, y0), cell(x1, y1)
        for cx in range(a[0], b[0] + 1):
            for cy in range(a[1], b[1] + 1):
                hard.add((cx, cy))
    pin_cell = {}
    for ref, s in placed.items():
        for num, (x, y, o) in s["pins"].items():
            pin_cell[(ref, num)] = (cell(x, y), o)
    for (ref, num), (c, o) in pin_cell.items():
        hard.add(c)
    for s in kids(root, "symbol"):  # power symbols: their graphic and name, out from the pin
        if not atom(s, "lib_id", "").startswith("power:"):
            continue
        at = kid(s, "at")
        x, y, r = float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0
        name = next(p[2] for p in kids(s, "property") if p[1] == "Value")
        up = atom(s, "lib_id") != "power:GND"
        d = {0: (0, -1), 90: (-1, 0), 180: (0, 1), 270: (1, 0)}[r] if up else {0: (0, 1), 90: (1, 0), 180: (0, -1), 270: (-1, 0)}[r]
        c = cell(x, y)
        reach = 4 if d[0] == 0 else 3 + math.ceil(len(name) * CW / G)
        for i in range(1, reach + 1):  # a wire may meet the symbol's own pin tip from the side
            for t in ((-1, 0, 1) if d[0] != 0 else (-2, -1, 0, 1, 2)):  # a sideways symbol stays within its own row
                hard.add((c[0] + d[0] * i + (t if d[0] == 0 else 0), c[1] + d[1] * i + (t if d[0] != 0 else 0)))
    soft = text_cells(root)
    foreign, foreign_ends = {}, set()
    for a, b in existing_wires(root):
        horiz = a[1] == b[1]
        for c in line_cells(a, b):
            foreign[c] = horiz
        foreign_ends |= {a, b}
    return hard, soft, pin_cell, foreign, foreign_ends


def main():
    chain = int(sys.argv[1])
    text = strip_chain(open(SCH, encoding="utf-8").read(), chain)
    root = sexpr(text)
    doc = json.load(open(NETLIST, encoding="utf-8"))
    placed = {r: s for r, s in symbols_and_pins(root).items() if r and not r.startswith("#")}
    parts = {p["ref"]: p for p in doc["parts"]}
    body = bodies(root, placed)
    # every sheet pin's net
    pin_net = {}
    for ref, p in parts.items():
        if ref not in placed:
            continue
        for pin, d in p["pinmap"].items():
            for c in candidates(pin, p):
                if c in placed[ref]["pins"]:
                    pin_net[(ref, c)] = d["net"]
    hard, soft, pin_cell, foreign, foreign_ends = obstacles(root, placed, body)
    # nets of this chain
    def drawn_in(ref, net):
        """The chain that draws this pin: a passive placed at another part's pin is wired to it with that part"""
        p = parts[ref]
        t = p.get("local_to", "")
        if prefix(ref) in LIB and "." in t:
            tref, tpin = t.split(".", 1)
            if parts[tref]["pinmap"].get(tpin, {}).get("net") == net:
                return parts[tref].get("chain")
        return p.get("chain")

    # a net is wired within each zone of the sheet and labelled between zones (step 1.30); each zone's part of a net
    # is drawn by the earliest chain that has a pin in it
    groups = {}
    for (ref, num), net in pin_net.items():
        if net in SKIP | RAILS or (ref, num) in LEAVE:
            continue
        groups.setdefault((net, "across" if net in WIRE_ACROSS else zone_of(placed[ref])), []).append((ref, num))
    nets = {}
    for (net, zone), members in groups.items():
        if min(drawn_in(r, net) or 99 for r, _ in members) == chain:
            nets[f"{net}@{zone}"] = {pin_cell[m] for m in members}
    for net, (anchor, others) in WIRED_RAILS.get(chain, {}).items():  # rails this chain draws as wires
        for p in [anchor] + others:
            if p.startswith("@"):  # a free point under a power symbol: the wire arrives from above (ground) or below (supply)
                x, y = (float(v) for v in p[1:].split(","))
                nets.setdefault(net, set()).add((cell(x, y), (0, -1) if net == "GND" else (0, 1)))
                continue
            ref, num = p.split(".")
            nets.setdefault(net, set()).add(pin_cell[(ref, num)])
    bound = (cell(15, 15)[0], cell(15, 15)[1], cell(580, 405)[0], cell(580, 405)[1])
    drawn, n, failed = [], 0, []
    for net in sorted(nets, key=lambda k: (k in RAILS, -len(nets[k]))):  # signals first, wired rails last
        pins = sorted(nets[net])
        pins = list({c: o for c, o in pins}.items())  # stacked pins share a cell
        if len(pins) < 2:
            continue
        own_cells = {c for c, _ in pins}
        o0 = pins[0][1]  # leave the first pin any way but back into its body
        tree = {pins[0][0]: [d for d in ((1, 0), (-1, 0), (0, 1), (0, -1)) if d != (-o0[0], -o0[1])]}
        edges = set()
        todo = pins[1:]
        if net.split("@")[0] in PATHS:  # drawn as given, after checking it reaches every pin and touches nothing else
            todo = []
            pts = [cell(x, y) for x, y in PATHS[net.split("@")[0]]]
            for a, b in zip(pts, pts[1:]):
                run = line_cells(a, b)
                for c, d in zip(run, run[1:]):
                    edges.add((min(c, d), max(c, d)))
            on = {c for e in edges for c in e}
            bad = [c for c in on if (c in hard and c not in own_cells) or c in foreign or c in foreign_ends]
            if not own_cells <= on or bad:
                failed.append(f"{net} (path misses pins or touches {bad[:3]})")
                continue
        while todo:
            todo.sort(key=lambda q: min(abs(q[0][0] - t[0]) + abs(q[0][1] - t[1]) for t in tree))
            dst, o = todo.pop(0)
            h = hard - own_cells - set(tree)
            path = route(tree, dst, (-o[0], -o[1]), h, foreign, foreign_ends - set(tree), soft, bound)
            if not path:
                failed.append(net)
                break
            for a, b in zip(path, path[1:]):
                edges.add((min(a, b), max(a, b)))
            for c in path:
                tree.setdefault(c, None)
            tree[dst] = None
        # this net's wires now block the next nets
        for a, b in edges:
            foreign[a] = foreign[b] = a[1] == b[1]
        # straight runs between nodes (pins, bends, branches)
        nbr = {}
        for a, b in edges:
            nbr.setdefault(a, []).append(b)
            nbr.setdefault(b, []).append(a)
        node = {c for c, ns in nbr.items() if len(ns) != 2 or (ns[0][0] != ns[1][0] and ns[0][1] != ns[1][1]) or c in own_cells}
        seen = set()
        for a in node:
            for b in nbr[a]:
                if (a, b) in seen:
                    continue
                run, prevc, cur = [a], a, b
                while cur not in node:
                    nxt = [x for x in nbr[cur] if x != prevc][0]
                    prevc, cur = cur, nxt
                seen.add((a, b)); seen.add((cur, prevc))
                n += 1
                drawn.append(f'\t(wire\n\t\t(pts (xy {a[0] * G:.2f} {a[1] * G:.2f}) (xy {cur[0] * G:.2f} {cur[1] * G:.2f}))\n\t\t(stroke (width 0) (type default))\n\t\t(uuid "{uid(chain, n)}")\n\t)\n')
                foreign_ends |= {a, cur}
        for c, ns in nbr.items():
            if len(ns) + (c in own_cells) >= 3:  # a branch, or a wire passing a pin tip
                n += 1
                drawn.append(f'\t(junction\n\t\t(at {c[0] * G:.2f} {c[1] * G:.2f})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uid(chain, n)}")\n\t)\n')
    i = text.rindex("\t(sheet_instances")
    text = text[:i] + "".join(drawn) + text[i:]
    print(f"chain {chain}: {len(nets)} nets, {sum(1 for d in drawn if 'wire' in d[:7])} wires" + (f"; FAILED {failed}" if failed else ""))
    if "--dry-run" not in sys.argv and not failed:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
