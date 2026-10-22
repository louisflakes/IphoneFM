"""Puts a PWR_FLAG on each Rev A power net fed from the connector or through a passive part (step 1.31), so ERC knows
the net is driven [EES p39, p77-78]. Each flag stands on a short stub off a point the net already has. Run after the
wiring (sch_wire) and before sch_labels; everything it draws has a uuid starting with UID, so a rerun replaces it.
Usage: python tools/sch_flags.py [--dry-run]"""
import re
import sys

from kicadcheck import sexpr, atom
from sch_place import SCH
from sch_power import POWER_LIB, balanced

UID = "f1a90000"
# net: (a point already on the net, where the flag stands at the end of a stub from it)
FLAGS = {
    "VBUS": ((40.64, 254.0), (27.94, 254.0)),  # at TP1 (the connector's VBUS)
    "GND": ((76.2, 257.81), (86.36, 257.81)),  # at TP3
    "VDDA": ((274.32, 205.74), (281.94, 205.74)),  # FB2's output, at C8
    "RX_VDD": ((411.48, 266.7), (416.56, 266.7)),  # FB3's output, at C33
    "U5_VDD": ((530.86, 111.76), (523.24, 111.76)),  # R16's output, at the corner into U5 VDD
}


def strip(text):
    out, i = [], 0
    for m in re.finditer(r'\n\t\((?:symbol|wire)\b', text):
        if m.start() < i:
            continue
        s = m.start() + 2
        e = balanced(text, s)
        if f'(uuid "{UID}-' in text[s:e]:
            out.append(text[i:m.start()])
            i = e
    out.append(text[i:])
    return "".join(out)


def embed(text):
    if '(symbol "power:PWR_FLAG"' in text:
        return text
    lib = open(POWER_LIB, encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "PWR_FLAG"\n', lib)
    blk = lib[m.start() + 2:balanced(lib, m.start() + 2)].replace('(symbol "PWR_FLAG"', '(symbol "power:PWR_FLAG"', 1)
    s = text.index("\t(lib_symbols")
    e = balanced(text, s + 1)
    return text[:e - 1] + "\t" + blk.replace("\n", "\n\t") + "\n" + text[e - 1:]


def main():
    text = embed(strip(open(SCH, encoding="utf-8").read()))
    sheet_uuid = atom(sexpr(text), "uuid")
    new, n = [], 0
    for k, (net, ((ax, ay), (fx, fy))) in enumerate(FLAGS.items(), 1):
        n += 1
        new.append(f'\t(wire\n\t\t(pts (xy {ax:.2f} {ay:.2f}) (xy {fx:.2f} {fy:.2f}))\n\t\t(stroke (width 0) (type default))\n'
                   f'\t\t(uuid "{UID}-0000-4000-8000-{n:012x}")\n\t)\n')
        n += 1
        ref = f"#FLG{k:02d}"
        new.append(f'\t(symbol\n\t\t(lib_id "power:PWR_FLAG")\n\t\t(at {fx:.2f} {fy:.2f} 0)\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n'
                   f'\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid "{UID}-0000-4000-8000-{n:012x}")\n'
                   f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {fx:.2f} {fy - 1.91:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
                   f'\t\t(property "Value" "PWR_FLAG"\n\t\t\t(at {fx:.2f} {fy - 3.81:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)\n'
                   f'\t\t(property "Footprint" ""\n\t\t\t(at {fx:.2f} {fy:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
                   f'\t\t(property "Datasheet" ""\n\t\t\t(at {fx:.2f} {fy:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
                   f'\t\t(instances\n\t\t\t(project "IphoneFM"\n\t\t\t\t(path "/{sheet_uuid}"\n\t\t\t\t\t(reference "{ref}") (unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    i = text.rindex("\t(sheet_instances")
    text = text[:i] + "".join(new) + text[i:]
    print(f"{len(FLAGS)} power flags: {', '.join(FLAGS)}")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
