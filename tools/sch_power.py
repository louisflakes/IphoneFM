"""Wires a power symbol to every pin on VBUS, 3V3, VDDA, RX_VDD and GND on the Rev A schematic (netlist.json says which).
A lone pin gets its symbol right at the pin end, pointing away from the part. A run of neighbouring pins on one side of a
part on the same rail gets short stubs joined by a bar, with one symbol on the middle stub. Everything this tool draws has
a uuid starting with UID, so a rerun replaces it.
Usage: python tools/sch_power.py [--dry-run]"""
import json
import os
import re
import sys

from kicadcheck import sexpr, candidates
from sch_place import SCH, NETLIST, CW, symbols_and_pins, atom

POWER_LIB = os.path.join(os.environ.get("KICAD_SYMBOLS", r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\symbols"), "power.kicad_sym")
# netlist.json net -> (stock power symbol, its graphic points up (supply) or down (ground))
SYMBOL = {"VBUS": ("VBUS", "up"), "3V3": ("+3V3", "up"), "VDDA": ("VDDA", "up"), "RX_VDD": ("VDDA", "up"), "GND": ("GND", "down")}
UID = "50a7e500"
# Rails drawn as wires within a chain (sch_wire.py): chain -> {net: (pin that carries the one power symbol, [pins wired to it])}
WIRED_RAILS = {
    2: {"VBUS": ("C1.1", ["U3.1", "U3.3"]), "3V3": ("C2.1", ["U3.5"])},  # regulator in, past C1; out, past C2
    # U1 supply: a 3V3 bus over U1 with its decoupling caps and FB2; FB2 out to VDDA with C7, C8
    3: {"3V3": ("C3.1", ["C5.1", "C6.1", "C4.1", "FB2.1", "U1.1", "U1.24", "U1.36", "U1.48"]),
        "VDDA": ("C8.1", ["C7.1", "FB2.2", "U1.9"])},
}
WIRED = {tuple(p.split(".")) for rails in WIRED_RAILS.values() for _, pins in rails.values() for p in pins}
STUB = 2.54
# KiCad turns a symbol counter-clockwise; the angle that makes the graphic point along the pin, per outward direction
ROT = {"up": {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270},
       "down": {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}}


def uid(n):
    return f"{UID}-0000-4000-8000-{n:012x}"


def balanced(text, start):
    depth = 0
    for j in range(start, len(text)):
        depth += {"(": 1, ")": -1}.get(text[j], 0)
        if depth == 0:
            return j + 1


def strip_previous(text):
    """Remove every top-level item a previous run drew (its uuid starts with UID)"""
    out, i = [], 0
    for m in re.finditer(r'\n\t\((symbol|wire|junction)\b', text):
        if m.start() < i:
            continue
        s = m.start() + 2
        e = balanced(text, s)
        if re.search(r'\(uuid "%s-' % UID, text[s:e]):
            out.append(text[i:m.start()])
            i = e
    out.append(text[i:])
    return "".join(out)


def pin_nets(doc, placed):
    """{(ref, sheet pin number): net} for every pin on a rail that gets its own power symbol"""
    nets = {}
    for p in doc["parts"]:
        if p["ref"] not in placed:
            continue
        for pin, d in p["pinmap"].items():
            if d["net"] in SYMBOL:
                for c in candidates(pin, p):
                    if c in placed[p["ref"]]["pins"] and (p["ref"], c) not in WIRED:
                        nets[(p["ref"], c)] = d["net"]
    return nets


def groups(placed, nets):
    """Runs of neighbouring same-rail pins along one side of a part: [(net, out, [(x, y), ...])]"""
    out = []
    for ref, sym in placed.items():
        sides = {}
        for num, (x, y, o) in sym["pins"].items():
            pos = (round(x, 2), round(y, 2))
            sides.setdefault(o, {}).setdefault(pos, set()).add(nets.get((ref, num)))
        for o, pins in sides.items():
            along = 1 if o[0] != 0 else 0  # pins on a left/right side line up in y
            run = []
            for pos in sorted(pins, key=lambda q: q[along]):
                net = pins[pos].pop() if len(pins[pos]) == 1 else "conflict"
                if net == "conflict":
                    raise SystemExit(f"{ref}: stacked pins at {pos} are on different nets")
                if run and (net != run[0][0] or abs(pos[along] - run[-1][1][along]) > 2.6):
                    if run[0][0]:
                        out.append((run[0][0], o, [q for _, q in run]))
                    run = []
                run.append((net, pos))
            if run and run[0][0]:
                out.append((run[0][0], o, [q for _, q in run]))
    return out


def wire(a, b, n):
    return f'\t(wire\n\t\t(pts (xy {a[0]:.2f} {a[1]:.2f}) (xy {b[0]:.2f} {b[1]:.2f}))\n\t\t(stroke (width 0) (type default))\n\t\t(uuid "{uid(n)}")\n\t)\n'


def power(net, at, o, n, k, sheet_uuid):
    name, kind = SYMBOL[net]
    rot = ROT[kind][o]
    # value text just beyond the graphic, read left to right
    gx, gy = (0, -1) if kind == "up" else (0, 1)
    dx, dy = {0: (gx, gy), 90: (gy, -gx), 180: (-gx, -gy), 270: (-gy, gx)}[rot]
    d = 3.56 if dx == 0 else 3.3 + len(net) * CW / 2
    vx, vy = at[0] + dx * d, at[1] + dy * d
    ref = f"#PWR{k:03d}"
    return (f'\t(symbol\n\t\t(lib_id "power:{name}")\n\t\t(at {at[0]:.2f} {at[1]:.2f} {rot})\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
            f'\t\t(uuid "{uid(n)}")\n'
            f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {at[0]:.2f} {at[1]:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
            f'\t\t(property "Value" "{net}"\n\t\t\t(at {vx:.2f} {vy:.2f} {rot % 180})\n\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)\n'
            f'\t\t(property "Footprint" ""\n\t\t\t(at {at[0]:.2f} {at[1]:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
            f'\t\t(property "Datasheet" ""\n\t\t\t(at {at[0]:.2f} {at[1]:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project "IphoneFM"\n\t\t\t\t(path "/{sheet_uuid}"\n\t\t\t\t\t(reference "{ref}") (unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def embed_library(text):
    """Copy the stock power symbols this sheet uses into its lib_symbols"""
    lib = open(POWER_LIB, encoding="utf-8").read()
    s = text.index("\t(lib_symbols")
    e = balanced(text, s + 1)
    add = ""
    for name in sorted({v[0] for v in SYMBOL.values()}):
        if f'(symbol "power:{name}"' in text[s:e]:
            continue
        m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), lib)
        blk = lib[m.start() + 2:balanced(lib, m.start() + 2)]
        add += "\t" + blk.replace(f'(symbol "{name}"', f'(symbol "power:{name}"', 1).replace("\n", "\n\t") + "\n"
    return text[:e - 1] + add + text[e - 1:]


def main():
    text = strip_previous(open(SCH, encoding="utf-8").read())
    root = sexpr(text)
    doc = json.load(open(NETLIST, encoding="utf-8"))
    placed = {r: s for r, s in symbols_and_pins(root).items() if r and not r.startswith("#")}
    nets = pin_nets(doc, placed)
    sheet_uuid = atom(root, "uuid")
    new, n, k, ends = [], 0, 0, {}
    for net, o, pins in groups(placed, nets):
        if len(pins) == 1:
            at = pins[0]
        else:
            stubs = [(x + o[0] * STUB, y + o[1] * STUB) for x, y in pins]
            for p, s in zip(pins, stubs):
                n += 1; new.append(wire(p, s, n))
                ends[s] = ends.get(s, 0) + 1
            for a, b in zip(stubs, stubs[1:]):
                n += 1; new.append(wire(a, b, n))
                ends[a] = ends.get(a, 0) + 1; ends[b] = ends.get(b, 0) + 1
            at = stubs[len(stubs) // 2]
        n += 1; k += 1
        new.append(power(net, at, o, n, k, sheet_uuid))
    for pt, c in sorted(ends.items()):
        if c >= 3:  # a stub meeting the bar from both sides is a T: mark it
            n += 1
            new.append(f'\t(junction\n\t\t(at {pt[0]:.2f} {pt[1]:.2f})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{uid(n)}")\n\t)\n')
    text = embed_library(text)
    i = text.rindex("\t(sheet_instances")
    text = text[:i] + "".join(new) + text[i:]
    by_net = {}
    for (r, p), net in nets.items():
        by_net[net] = by_net.get(net, 0) + 1
    print(f"{k} power symbols, {sum(1 for x in new if x.startswith(chr(9) + '(wire'))} wires; rail pins on the sheet: {by_net}")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
