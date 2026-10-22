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
RAILS = {"GND", "3V3", "VBUS"}
LIB = {"R": "Device:R", "C": "Device:C", "L": "Device:L", "FB": "Device:FerriteBead"}
FOOT = {("R", "0402"): "Resistor_SMD:R_0402_1005Metric", ("C", "0402"): "Capacitor_SMD:C_0402_1005Metric",
        ("C", "0603"): "Capacitor_SMD:C_0603_1608Metric", ("C", "0805"): "Capacitor_SMD:C_0805_2012Metric",
        ("L", "0603"): "Inductor_SMD:L_0603_1608Metric", ("FB", "0402"): "Inductor_SMD:L_0402_1005Metric"}
# Chains drawn where the sheet plan puts them (sheet-plan.md): FL1 between U7 and U5, the RX front end in its own zone,
# and U2's loop filter as a compact group at CPout. (x, y, rotation); rotation 90 = horizontal.
MANUAL = {
    # U2 loop filter at CPout (pin 25 ends at 353.06, 81.28): R5 in line, C25 to GND after it, C24 to GND below the pin
    "R5": (363.22, 81.28, 90), "C25": (370.84, 86.36, 0), "C24": (358.14, 93.98, 0),
    # C26 in line between U2 RFoutTx (353.06, 73.66) and U7 RF1 (388.62, 83.82)
    "C26": (370.84, 73.66, 90),
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
        ref = next((p[2] for p in kids(s, "property") if p[1] == "Reference"), None)
        pins = {}
        for num, px, py, pa, ln in libpins.get(lib_id, []):
            a = math.radians(r)
            rx, ry = px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)
            ang = math.radians(pa + r)
            out = (-round(math.cos(ang)), round(math.sin(ang)))  # outward from the body, in sheet (y-down) axes
            pins[str(num)] = (x + rx, y - ry, out)
        placed[ref] = {"lib_id": lib_id, "x": x, "y": y, "rot": r, "pins": pins}
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
    return (x - 3.3 - w, y - 5.08, x + 2.6, y + 5.08) if left else (x - 2.6, y - 5.08, x + 3.3 + w, y + 5.08)


def plan(doc, placed):
    boxes = [bbox_of(s) for r, s in placed.items() if s["pins"] and prefix(r) not in LIB]  # passives already on the sheet get re-placed
    out = {}
    passives = [p for p in doc["parts"] if prefix(p["ref"]) in LIB]
    order = sorted(passives, key=lambda p: (p["ref"] not in MANUAL, int(re.sub(r"\D", "", p["ref"]))))
    for p in order:
        ref, nets = p["ref"], [d["net"] for d in p["pinmap"].values()]
        shunt = any(n in RAILS for n in nets)
        if ref in MANUAL:
            x, y, rot = MANUAL[ref]
            out[ref] = (x, y, rot, False); boxes.append(part_box(x, y, rot == 90, text_width(p))); continue
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


def block(ref, p, x, y, rot, left, sheet_uuid):
    lib = LIB[prefix(ref)]
    foot = FOOT.get((prefix(ref), p["package"]), "")
    # text reads left to right in both orientations: above a horizontal part, beside a vertical one
    s = -1 if left else 1
    (rx, ry), (vx, vy) = ((-3.81, -5.59), (-3.81, -3.81)) if rot == 90 else ((2.54 * s, -1.27), (2.54 * s, 1.27))
    just = "right" if (rot == 90) != left else "left"  # KiCad mirrors justification on a part turned 90 degrees
    return (f'\t(symbol\n\t\t(lib_id "{lib}")\n\t\t(at {x:.2f} {y:.2f} {rot})\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
            f'\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {x + rx:.2f} {y + ry:.2f} {rot})\n\t\t\t(effects (font (size 1.27 1.27)) (justify {just}))\n\t\t)\n'
            f'\t\t(property "Value" "{p["value"]}"\n\t\t\t(at {x + vx:.2f} {y + vy:.2f} {rot})\n\t\t\t(effects (font (size 1.27 1.27)) (justify {just}))\n\t\t)\n'
            f'\t\t(property "Footprint" "{foot}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
            f'\t\t(property "Datasheet" "~"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project "IphoneFM"\n\t\t\t\t(path "/{sheet_uuid}"\n\t\t\t\t\t(reference "{ref}") (unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def main():
    text = open(SCH, encoding="utf-8").read()
    root = sexpr(text)
    doc = json.load(open(NETLIST, encoding="utf-8"))
    placed = symbols_and_pins(root)
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
