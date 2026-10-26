"""Places the Rev A test pads TP1-TP8 (KiCad Connector:TestPoint) on the schematic: each signal pad on the end of the line
it tests, the power pads together in the controls zone. They are bare copper, so they stay out of the BOM. A rerun
replaces them. Run before sch_place (they are obstacles for it); the wires reach them through sch_wire's chains.
Usage: python tools/sch_testpads.py [--dry-run]"""
import math
import os
import re
import sys
import uuid

from sch_place import SCH
from sch_power import POWER_LIB, balanced
from kicadcheck import sexpr, atom

FOOTPRINT = "TestPoint:TestPoint_Pad_D1.5mm"
# ref: (x, y of the pad's connection point, rotation); 0 = pad above its pin, 180 = below, 90 = to the left, 270 = right
PADS = {
    "TP1": (40.64, 254.0, 180), "TP2": (58.42, 254.0, 180), "TP3": (76.2, 257.81, 0),  # VBUS, 3V3, GND
    "TP4": (127.0, 363.22, 270),  # RF_MODE, past SW1's pull-down R18
    "TP5": (304.8, 101.6, 90),  # LMX_MUX, off U2 MUXout
    "TP6": (182.88, 218.44, 90),  # NRST, past C10 on U1
    "TP7": (248.92, 254.0, 270), "TP8": (243.84, 251.46, 270),  # SWCLK off U1 PA14, SWDIO off PA13 (staggered)
}


def embed(text):
    if '(symbol "Connector:TestPoint"' in text:
        return text
    lib = open(os.path.join(os.path.dirname(POWER_LIB), "Connector.kicad_sym"), encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "TestPoint"\n', lib)
    blk = lib[m.start() + 2:balanced(lib, m.start() + 2)].replace('(symbol "TestPoint"', '(symbol "Connector:TestPoint"', 1)
    s = text.index("\t(lib_symbols")
    e = balanced(text, s + 1)
    return text[:e - 1] + "\t" + blk.replace("\n", "\n\t") + "\n" + text[e - 1:]


def block(ref, value, x, y, rot, sheet_uuid):
    a = math.radians(rot)
    cx, cy = x - 3.302 * math.sin(a), y - 3.302 * math.cos(a)  # the pad circle, 3.302 mm out along the pin
    if rot in (0, 180):  # name to the right of the circle
        at, just = f"{cx + 1.524:.2f} {cy:.2f} 0", (" (justify right)" if rot == 180 else " (justify left)")
    elif rot == 270:  # at the end of a line running right: name on the line's row, past the circle
        at, just = f"{cx + 1.524:.2f} {cy:.2f} 90", " (justify left)"
    else:  # name above the circle
        at, just = f"{cx:.2f} {cy - 1.905:.2f} 90", ""
    hid = "(effects (font (size 1.27 1.27)) (hide yes))"
    return (f'\t(symbol\n\t\t(lib_id "Connector:TestPoint")\n\t\t(at {x:.2f} {y:.2f} {rot})\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n'
            f'\t\t(in_bom no)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {at})\n\t\t\t(effects (font (size 1.27 1.27)){just})\n\t\t)\n'
            f'\t\t(property "Value" "{value}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t{hid}\n\t\t)\n'
            f'\t\t(property "Footprint" "{FOOTPRINT}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t{hid}\n\t\t)\n'
            f'\t\t(property "Datasheet" "~"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t{hid}\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project "IphoneFM"\n\t\t\t\t(path "/{sheet_uuid}"\n\t\t\t\t\t(reference "{ref}") (unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def main():
    import json
    from sch_place import NETLIST
    values = {p["ref"]: p["value"] for p in json.load(open(NETLIST, encoding="utf-8"))["parts"]}
    text = embed(open(SCH, encoding="utf-8").read())
    for ref in PADS:  # drop any earlier copy
        m = re.search(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)(?:(?!\n\t\(symbol\n).)*?\(property "Reference" "%s"\n' % re.escape(ref), text, re.S)
        if m:
            text = text[:m.start() + 1] + text[balanced(text, m.start() + 2) + 1:]
    sheet_uuid = atom(sexpr(text), "uuid")
    new = "".join(block(ref, values[ref], *pos, sheet_uuid) for ref, pos in PADS.items())
    k = text.rindex("\t(sheet_instances")
    text = text[:k] + new + text[k:]
    print(f"{len(PADS)} test pads placed")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
