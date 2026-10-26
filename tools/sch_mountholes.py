"""Places the Rev A mounting holes H1-H4 (KiCad Mechanical:MountingHole) on the schematic, in a row in the free space
between the layout notes and the title block (step 3.5). They have no pins and stay out of the BOM; their board
positions, from the board's top-left corner, are in BOARD_POS (agreed with the user 2026-10-23) and are used when the
parts are placed in Phase 4. A rerun replaces them.
Usage: python tools/sch_mountholes.py [--dry-run]"""
import os
import re
import sys
import uuid

from sch_place import SCH
from sch_power import POWER_LIB, balanced
from kicadcheck import sexpr, atom

FOOTPRINT = "IphoneFM:MountingHole_2.2mm_M2"
VALUE = "M2"
BOARD_POS = {"H1": (13, 7), "H2": (33, 7), "H3": (41, 57), "H4": (8, 66)}  # mm from the board's top-left corner
ROW_Y, ROW_X0, STEP = 358.14, 452.12, 15.24  # schematic positions, on the 1.27 mm grid
LABEL = "MOUNTING HOLES: M2, 2.2 mm unplated. Board positions from the top-left corner: H1 (13, 7), H2 (33, 7), H3 (41, 57), H4 (8, 66) mm"


def embed(text):
    if '(symbol "Mechanical:MountingHole"' in text:
        return text
    lib = open(os.path.join(os.path.dirname(POWER_LIB), "Mechanical.kicad_sym"), encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "MountingHole"\n', lib)
    blk = lib[m.start() + 2:balanced(lib, m.start() + 2)].replace('(symbol "MountingHole"', '(symbol "Mechanical:MountingHole"', 1)
    s = text.index("\t(lib_symbols")
    e = balanced(text, s + 1)
    return text[:e - 1] + "\t" + blk.replace("\n", "\n\t") + "\n" + text[e - 1:]


def block(ref, x, y, sheet_uuid):
    hid = "(effects (font (size 1.27 1.27)) (hide yes))"
    return (f'\t(symbol\n\t\t(lib_id "Mechanical:MountingHole")\n\t\t(at {x:.2f} {y:.2f} 0)\n\t\t(unit 1)\n\t\t(exclude_from_sim no)\n'
            f'\t\t(in_bom no)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid "{uuid.uuid5(uuid.NAMESPACE_URL, "IphoneFM/" + ref)}")\n'
            f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {x:.2f} {y - 5.08:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)\n'
            f'\t\t(property "Value" "{VALUE}"\n\t\t\t(at {x:.2f} {y - 3.175:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)\n'
            f'\t\t(property "Footprint" "{FOOTPRINT}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t{hid}\n\t\t)\n'
            f'\t\t(property "Datasheet" "~"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t{hid}\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project "IphoneFM"\n\t\t\t\t(path "/{sheet_uuid}"\n\t\t\t\t\t(reference "{ref}") (unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def main():
    text = embed(open(SCH, encoding="utf-8").read())
    for ref in BOARD_POS:  # drop any earlier copy
        m = re.search(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)(?:(?!\n\t\(symbol\n).)*?\(property "Reference" "%s"\n' % re.escape(ref), text, re.S)
        if m:
            text = text[:m.start() + 1] + text[balanced(text, m.start() + 2) + 1:]
    text = re.sub(r'\t\(text "MOUNTING HOLES:[^"]*"\n.*?\n\t\)\n', "", text, flags=re.S)
    sheet_uuid = atom(sexpr(text), "uuid")
    new = "".join(block(ref, ROW_X0 + i * STEP, ROW_Y, sheet_uuid) for i, ref in enumerate(BOARD_POS))
    new += (f'\t(text "{LABEL}"\n\t\t(exclude_from_sim no)\n\t\t(at {ROW_X0 - 7.62:.2f} {ROW_Y - 10.16:.2f} 0)\n'
            f'\t\t(effects (font (size 1.27 1.27)) (justify left bottom))\n\t\t(uuid "{uuid.uuid5(uuid.NAMESPACE_URL, "IphoneFM/mounting-holes-label")}")\n\t)\n')
    k = text.rindex("\t(sheet_instances")
    text = text[:k] + new + text[k:]
    print(f"{len(BOARD_POS)} mounting holes placed")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
