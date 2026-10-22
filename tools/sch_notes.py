"""Writes the layout notes block onto the Rev A schematic (step 1.34) [BAC p3]. A rerun replaces it.
Usage: python tools/sch_notes.py [--dry-run]"""
import re
import sys

from sch_place import SCH
from sch_power import balanced

UID = "a07e5000"
AT = (444.5, 322.58)  # top-left corner, in the free space above the title block
NOTES = [
    "LAYOUT NOTES",
    "1. Decoupling: put each bypass capacitor right at the supply pin it serves,",
    "   with its ground pad straight into the ground fill [BAC p3].",
    "2. U2 (LMX2571): keep the I2S/FSK clock and every other switching line away from",
    "   the loop filter (C24, R5, C25) and from OSCin, pin 34 (rule R8) [LMX2571 p55].",
    "3. U4 (Si4705): ground pads of the FMI shunt parts (C35, L1) and the GPO caps",
    "   (C37, C38) go straight into the top ground fill, with no thermal reliefs and an",
    "   unbroken top-ground path to system ground [AN383 p17].",
]


def main():
    text = open(SCH, encoding="utf-8").read()
    out, i = [], 0
    for m in re.finditer(r'\n\t\(text\b', text):
        s = m.start() + 2
        e = balanced(text, s)
        if f'(uuid "{UID}-' in text[s:e]:
            out.append(text[i:m.start()])
            i = e
    text = "".join(out) + text[i:]
    body = "\\n".join(NOTES)
    block = (f'\t(text "{body}"\n\t\t(exclude_from_sim no)\n\t\t(at {AT[0]:.2f} {AT[1]:.2f} 0)\n'
             f'\t\t(effects (font (size 1.27 1.27)) (justify left top))\n\t\t(uuid "{UID}-0000-4000-8000-000000000001")\n\t)\n')
    k = text.rindex("\t(sheet_instances")
    text = text[:k] + block + text[k:]
    print(f"layout notes: {len(NOTES) - 1} lines at {AT}")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
