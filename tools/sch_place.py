"""Places the Rev A passives on the schematic beside the pin each one serves (netlist.json "local_to").
Reads the sheet to find every placed symbol's pin positions, then puts each passive just outside its pin,
avoiding everything already on the sheet. Shunt parts (one end on GND or a supply) hang vertically; series
parts sit in line with their pin. Parts listed in MANUAL go where the sheet plan puts them.
Usage: python tools/sch_place.py [--dry-run]"""
import json
import math
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicadcheck import sexpr, kids, kid, atom  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCH = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.kicad_sch")
NETLIST = os.path.join(ROOT, "design", "rev-a", "netlist.json")
G = 1.27
CW = 1.1  # width of one 1.27 mm character, with a margin
PWR_ROOM = 8.9  # half height of an upright passive with power symbols on its ends
PIN_ROOM = 10.2  # stub, power symbol and its name beyond a chip pin on a rail
RAILS = {"GND", "3V3", "VBUS"}
SUPPLIES = {"VBUS", "3V3", "VDDA", "RX_VDD"}
LIB = {"R": "Device:R", "C": "Device:C", "L": "Device:L", "FB": "Device:FerriteBead"}
FOOT = {("R", "0402"): "Resistor_SMD:R_0402_1005Metric", ("C", "0402"): "Capacitor_SMD:C_0402_1005Metric",
        ("C", "0603"): "Capacitor_SMD:C_0603_1608Metric", ("C", "0805"): "Capacitor_SMD:C_0805_2012Metric",
        ("L", "0603"): "Inductor_SMD:L_0603_1608Metric", ("FB", "0402"): "Inductor_SMD:L_0402_1005Metric"}
# Chains drawn where the sheet plan puts them (sheet-plan.md): FL1 between U7 and U5, the RX front end in its own zone,
# and U2's loop filter as a compact group at CPout. (x, y, rotation); rotation 90 = horizontal.
MANUAL = {
    # chain 6: U7 pull-downs, one per control line, each hanging in the gap left as the lines below it turn down to SW3
    "R10": (327.66, 135.89, 0), "R11": (340.36, 138.43, 0), "R12": (353.06, 140.97, 0),
    "R13": (365.76, 143.51, 0), "R14": (378.46, 146.05, 0), "R15": (391.16, 148.59, 0),
    "C27": (431.8, 113.03, 0),
    # chain 5: U2 supply caps in two rows on a 3V3 bus above U2; loop filter in a row on CPout (C24 down, R5 on, C25 down);
    # C26 on RFoutTx toward U7; bypass caps C20-C23 as a staggered ladder on one ground bar; R9 off CE, text left
    "C14": (299.72, 31.75, 0), "C15": (322.58, 31.75, 0), "C17": (347.98, 31.75, 0), "C19": (370.84, 31.75, 0),
    "C18": (299.72, 49.53, 0), "C13": (347.98, 49.53, 0), "C16": (370.84, 49.53, 0),
    "C24": (356.87, 85.09, 0), "R5": (370.84, 81.28, 90), "C25": (374.65, 85.09, 0), "C26": (363.22, 73.66, 90),
    "C20": (360.68, 96.52, 90), "C21": (368.3, 99.06, 90), "C22": (360.68, 101.6, 90), "C23": (368.3, 104.14, 90),
    "R9": (309.88, 107.95, 0, True),
    # chain 4: a 3V3 line above Y2 with C12 (text left) and C11 hanging from it; R4 straight off Y2 OUT
    "C12": (215.9, 31.75, 0, True), "C11": (231.14, 31.75, 0), "R4": (248.92, 50.8, 90),
    # chain 3: the shunt caps on U1 PA2-PA5 lie on their pin rows in two staggered columns, ground ends run right to one
    # bar (sch_power WIRED_RAILS); R6-R8 straight off PA8 and stepped down off PA9, PA10
    "C39": (248.92, 223.52, 90), "C40": (256.54, 226.06, 90), "C36": (248.92, 228.6, 90), "C41": (256.54, 231.14, 90),
    "R6": (248.92, 238.76, 90), "R7": (248.92, 248.92, 90), "R8": (248.92, 259.08, 90),
    # chain 3: U1 decoupling in a 2 x 2 block on the 3V3 bus over U1, FB2 then C7, C8 on the VDDA branch to its right;
    # C10 (NRST), R3 (BOOT0) and C9 (VCAP) hang from their lines on U1's left, text on the left
    "C3": (175.26, 184.15, 0), "C5": (198.12, 184.15, 0), "C6": (175.26, 201.93, 0), "C4": (198.12, 201.93, 0),
    "FB2": (243.84, 201.93, 0), "C7": (251.46, 209.55, 0), "C8": (274.32, 209.55, 0),
    "C10": (187.96, 222.25, 0, True), "R3": (198.12, 237.49, 0, True), "C9": (200.66, 288.29, 0, True),
    # chain 2: C1 hangs from the VBUS line into U3 VIN (text on the left, clear of U3), C2 from the 3V3 line out of VOUT
    "C1": (105.41, 46.99, 0, True), "C2": (135.89, 46.99, 0),
    # chain 1: R2 hangs from the CC2 line just right of J1, R1 from the CC1 line beyond D4 (sch_layout.py)
    "R2": (63.5, 67.31, 0), "R1": (114.3, 64.77, 0),
    # FL1 along y 83.82 from U7 RF2 (424.18) toward U5: shunt C, series L, shunt C, series L, shunt C
    "C28": (444.5, 88.9, 0), "L2": (452.12, 83.82, 90), "C29": (459.74, 88.9, 0), "L3": (467.36, 83.82, 90), "C30": (474.98, 88.9, 0),
    # RX front end zone, right to left at U4 FMI's height (289.56): C34 series, L1 shunt, FB1 series, C35 shunt
    "C34": (487.68, 289.56, 90), "L1": (477.52, 294.64, 0), "FB1": (467.36, 289.56, 90), "C35": (457.2, 294.64, 0),
}


def snap(v):
    return round(v / G) * G


def prefix(ref):
    return re.match(r"[A-Z]+", ref).group(0)


def symbols_and_pins(root):
    libpins = {}
    for ls in kids(kid(root, "lib_symbols"), "symbol"):
        pins = []
        for sub in kids(ls, "symbol"):
            for p in kids(sub, "pin"):
                at = kid(p, "at")
                pins.append((atom(kid(p, "number"), "number") or kid(p, "number")[1], float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                             float(atom(p, "length", "2.54"))))
        libpins[ls[1]] = pins
    placed = {}
    for s in kids(root, "symbol"):
        lib_id = atom(s, "lib_id")
        at = kid(s, "at")
        x, y, r = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0
        mirror = atom(s, "mirror")  # KiCad turns the symbol first, then mirrors it on the sheet
        ref = next((p[2] for p in kids(s, "property") if p[1] == "Reference"), None)
        pins = {}
        for num, px, py, pa, ln in libpins.get(lib_id, []):
            a = math.radians(r)
            rx, ry = px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)
            ang = math.radians(pa + r)
            out = (-round(math.cos(ang)), round(math.sin(ang)))  # outward from the body, in sheet (y-down) axes
            if mirror == "y":
                rx, out = -rx, (-out[0], out[1])
            elif mirror == "x":
                ry, out = -ry, (out[0], -out[1])
            pins[str(num)] = (x + rx, y - ry, out)
        placed[ref] = {"lib_id": lib_id, "x": x, "y": y, "rot": r, "mirror": mirror, "pins": pins}
    return placed


def bbox_of(sym):
    xs = [p[0] for p in sym["pins"].values()] or [sym["x"]]
    ys = [p[1] for p in sym["pins"].values()] or [sym["y"]]
    return (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)


def overlaps(a, b, m=0.5):
    return a[0] < b[2] + m and b[0] < a[2] + m and a[1] < b[3] + m and b[1] < a[3] + m


def text_width(p):
    return max(len(p["ref"]), len(p["value"])) * CW


def part_box(x, y, horizontal, w, left=False):
    # body plus its pins (7.62 mm long) and its reference/value text: above a horizontal part, beside a vertical one
    if horizontal:
        return (x - 5.08, y - 6.6, max(x + 5.08, x - 3.81 + w), y + 2.6)
    # upright parts mostly end on a rail: leave room above and below for its power symbol and name
    return (x - 3.3 - w, y - PWR_ROOM, x + 2.6, y + PWR_ROOM) if left else (x - 2.6, y - PWR_ROOM, x + 3.3 + w, y + PWR_ROOM)


def plan(doc, placed):
    boxes = [bbox_of(s) for r, s in placed.items() if s["pins"] and prefix(r) not in LIB]  # passives already on the sheet get re-placed
    from sch_power import pin_nets  # room for the power symbol (and its stub) at every chip pin on a rail
    for (r, num), net in pin_nets(doc, placed).items():
        if prefix(r) not in LIB:
            px, py, (ox, oy) = placed[r]["pins"][num]
            ex, ey = px + ox * PIN_ROOM, py + oy * PIN_ROOM
            boxes.append((min(px, ex) - 2.5, min(py, ey) - 2.5, max(px, ex) + 2.5, max(py, ey) + 2.5))
    out = {}
    passives = [p for p in doc["parts"] if prefix(p["ref"]) in LIB]
    order = sorted(passives, key=lambda p: (p["ref"] not in MANUAL, int(re.sub(r"\D", "", p["ref"]))))
    for p in order:
        ref, nets = p["ref"], [d["net"] for d in p["pinmap"].values()]
        shunt = any(n in RAILS for n in nets)
        if ref in MANUAL:
            x, y, rot, *left = MANUAL[ref]
            out[ref] = (x, y, rot, bool(left and left[0])); boxes.append(part_box(x, y, rot == 90, text_width(p), bool(left and left[0]))); continue
        tgt = p.get("local_to", "")
        if "." not in tgt or tgt.split(".")[0] not in out and (tgt.split(".")[0] not in placed or prefix(tgt.split(".")[0]) in LIB):
            raise SystemExit(f"{ref}: no placed target for local_to {tgt!r}; add it to MANUAL")
        tref, tpin = tgt.split(".", 1)
        if tref not in out:
            px, py, (ox, oy) = placed[tref]["pins"][tpin]
        else:  # target is a passive placed earlier in this run: sit beside it
            tx, ty = out[tref][:2]
            px, py, (ox, oy) = tx, ty, (1, 0)
        side_horizontal = ox != 0  # pin points left or right
        horizontal = (not shunt) and side_horizontal
        left = ox < 0 and not horizontal  # on a chip's left side the text goes on the left, away from the chip
        best = None  # the free spot nearest the pin, over every lane and offset
        for lane in range(0, 8):
            d = 10.16 + lane * 12.7
            for k in range(0, 40):
                t = (k + 1) // 2 * 7.62 * (1 if k % 2 else -1)
                x = snap(px + ox * d + (0 if side_horizontal else t))
                y = snap(py + oy * d + (t if side_horizontal else 0))
                b = part_box(x, y, horizontal, text_width(p), left)
                cost = math.hypot(x - px, y - py)
                if (best is None or cost < best[0]) and not any(overlaps(b, o) for o in boxes) and 20 < x < 575 and 20 < y < 400:
                    best = (cost, (x, y, 90 if horizontal else 0, left))
        if not best:
            raise SystemExit(f"{ref}: no free spot near {tgt}")
        out[ref] = best[1]
        boxes.append(part_box(best[1][0], best[1][1], horizontal, text_width(p), left))
    return out


def upside_down(p):
    """Pin 1 is at the top of an upright R, C, L or FB: true when that puts ground on top or a supply below a signal"""
    n1, n2 = p["pinmap"]["1"]["net"], p["pinmap"]["2"]["net"]
    return n1 == "GND" or (n2 in SUPPLIES and n1 not in SUPPLIES)


# parts stacked one grid step apart: the compact capacitor symbol, name and value on the part's own row past its ground bar
INLINE = {"C39": 12.7, "C40": 5.08, "C36": 12.7, "C41": 5.08, "C20": 12.7, "C21": 5.08, "C22": 12.7, "C23": 5.08}  # ref: x of the name from the part's centre
SMALL = "Device:C_Small"
# pull-downs hanging side by side in a ribbon of lines (chain 6): name and value centred under the ground symbol
BELOW = {"R10", "R11", "R12", "R13", "R14", "R15"}


def block(ref, p, x, y, rot, left, sheet_uuid):
    lib = SMALL if ref in INLINE else LIB[prefix(ref)]
    foot = FOOT.get((prefix(ref), p["package"]), "")
    # text reads left to right in both orientations: above a horizontal part, beside a vertical one
    s = -1 if left else 1
    (rx, ry), (vx, vy) = ((-3.81, -5.59), (-3.81, -3.81)) if rot == 90 else ((2.54 * s, -1.27), (2.54 * s, 1.27))
    just = "right" if (rot == 90) != left else "left"  # KiCad mirrors justification on a part turned 90 degrees
    if ref in INLINE:
        (rx, ry), (vx, vy) = (INLINE[ref], 0), (INLINE[ref] + 5.08, 0)
    if ref in BELOW:  # name and value centred under the part's ground symbol
        (rx, ry), (vx, vy), just = (0, 10.16), (0, 12.7), None
    if rot == 0 and upside_down(p):  # turned over so ground ends at the bottom and a supply at the top
        rot, just = 180, (just and ("right" if just == "left" else "left"))
    jus = f" (justify {just})" if just else ""
    return (f'\t(symbol\n\t\t(lib_id "{lib}")\n\t\t(at {x:.2f} {y:.2f} {rot})\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
            f'\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {x + rx:.2f} {y + ry:.2f} {rot % 180})\n\t\t\t(effects (font (size 1.27 1.27)){jus})\n\t\t)\n'
            f'\t\t(property "Value" "{p["value"]}"\n\t\t\t(at {x + vx:.2f} {y + vy:.2f} {rot % 180})\n\t\t\t(effects (font (size 1.27 1.27)){jus})\n\t\t)\n'
            f'\t\t(property "Footprint" "{foot}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
            f'\t\t(property "Datasheet" "~"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project "IphoneFM"\n\t\t\t\t(path "/{sheet_uuid}"\n\t\t\t\t\t(reference "{ref}") (unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def embed_device(text, lib_id):
    """Copy a symbol from KiCad's Device library into the sheet's lib_symbols if it isn't there yet"""
    if f'(symbol "{lib_id}"' in text:
        return text
    from sch_power import POWER_LIB, balanced
    name = lib_id.split(":")[1]
    lib = open(os.path.join(os.path.dirname(POWER_LIB), "Device.kicad_sym"), encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), lib)
    blk = lib[m.start() + 2:balanced(lib, m.start() + 2)].replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    s = text.index("\t(lib_symbols")
    e = balanced(text, s + 1)
    return text[:e - 1] + "\t" + blk.replace("\n", "\n\t") + "\n" + text[e - 1:]


def main():
    text = open(SCH, encoding="utf-8").read()
    root = sexpr(text)
    doc = json.load(open(NETLIST, encoding="utf-8"))
    placed = {r: s for r, s in symbols_and_pins(root).items() if not r.startswith("#")}  # power symbols are redrawn by sch_power.py
    text = embed_device(text, SMALL)
    root = sexpr(text)
    missing = [l for l in LIB.values() if not any(s[1] == l for s in kids(kid(root, "lib_symbols"), "symbol"))]
    if missing:
        raise SystemExit(f"Seed one of each first (embeds the library symbol): {', '.join(missing)}")
    already = {r for r in placed if prefix(r) in LIB}
    out = plan(doc, placed)
    for ref, (x, y, rot, _) in sorted(out.items(), key=lambda kv: kv[0]):
        print(f"{ref:5} {x:7.2f} {y:7.2f} {'horizontal' if rot == 90 else 'vertical'}{'  (seeded, moved)' if ref in already else ''}")
    if "--dry-run" in sys.argv:
        return
    sheet_uuid = atom(root, "uuid")
    by = {p["ref"]: p for p in doc["parts"]}
    for ref in already:  # passives already on the sheet are rewritten in full, so every field moves with the part
        m = re.search(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)(?:(?!\n\t\(symbol\n).)*?\(property "Reference" "%s"\n' % re.escape(ref), text, re.S)
        i, depth = m.start() + 2, 0  # i is the symbol's opening bracket
        for j in range(i, len(text)):
            depth += {"(": 1, ")": -1}.get(text[j], 0)
            if depth == 0:
                text = text[:m.start() + 1] + text[j + 2:]
                break
    new = "".join(block(ref, by[ref], x, y, rot, left, sheet_uuid) for ref, (x, y, rot, left) in out.items())
    k = text.rindex("\t(sheet_instances")
    text = text[:k] + new + text[k:]
    open(SCH, "w", encoding="utf-8", newline="\n").write(text)
    print(f"placed {len(out) - len(already)} new, moved {len(already)}")


if __name__ == "__main__":
    main()
