"""Moves chips, connectors and diodes on the Rev A schematic to where a chain's wiring reads cleanly (the passives
follow in sch_place.py's MANUAL). Visible fields are stacked to the side given, left-justified, so they clear the pins.
Rerun order after a change: sch_layout, sch_place, sch_fields, sch_power, then sch_wire for each wired chain.
Usage: python tools/sch_layout.py [--dry-run]"""
import re
import sys

from sch_place import SCH
from sch_power import balanced

# ref: (x, y, rotation, (dx, dy) of the first visible field from the symbol; the next ones stack 2.54 mm below)
LAYOUT = {
    # chain 1: U6 below J1 on the DM/DP rows; the CC ESD diodes turned so IO is on top, hanging from their CC lines
    "U6": (66.04, 101.6, 0, (6.35, 8.89)),
    "D4": (93.98, 69.85, 180, (-1.27, 6.35)),
    "D3": (142.24, 67.31, 180, (3.81, -1.27)),
}


def main():
    text = open(SCH, encoding="utf-8").read()
    for ref, (x, y, rot, (fx, fy)) in LAYOUT.items():
        m = re.search(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)(?:(?!\n\t\(symbol\n).)*?\(property "Reference" "%s"\n' % re.escape(ref), text, re.S)
        s = m.start() + 2
        e = balanced(text, s)
        blk = text[s:e]
        blk = re.sub(r'^(\t\t\(at )[\d.-]+ [\d.-]+(?: [\d.-]+)?\)', lambda q: f"{q.group(1)}{x:.2f} {y:.2f} {rot})", blk, count=1, flags=re.M)
        k = 0

        def field(q):
            nonlocal k
            body = q.group(0)
            if "(hide yes)" in body:
                return re.sub(r'\(at [\d.-]+ [\d.-]+ [\d.-]+\)', f"(at {x:.2f} {y:.2f} 0)", body, count=1)
            at = f"(at {x + fx:.2f} {y + fy + 2.54 * k:.2f} 0)"
            k += 1
            just = "right" if rot in (90, 180) else "left"  # KiCad mirrors justification on a turned part
            body = re.sub(r'\(at [\d.-]+ [\d.-]+ [\d.-]+\)', at, body, count=1)
            body = re.sub(r'\(effects \(font \(size 1\.27 1\.27\)\)(?: \(justify [a-z ]+\))?\)', f"(effects (font (size 1.27 1.27)) (justify {just}))", body, count=1)
            return body
        blk = re.sub(r'\t\t\(property "(?:Reference|Value|MPN|LCSC|Manufacturer|Footprint|Datasheet)" "[^"]*"\n\t\t\t\(at [^)]*\)\n\t\t\t\(effects .*?\)\n\t\t\)\n', field, blk, flags=re.S)
        text = text[:s] + blk + text[e:]
        print(f"{ref:4} {x:7.2f} {y:7.2f} {rot}")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
