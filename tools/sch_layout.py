"""Moves chips, connectors and diodes on the Rev A schematic to where a chain's wiring reads cleanly (the passives
follow in sch_place.py's MANUAL). Visible fields are stacked to the side given, left-justified, so they clear the pins.
Rerun order after a change: sch_layout, sch_place, sch_fields, sch_power, then sch_wire for each wired chain.
Usage: python tools/sch_layout.py [--dry-run]"""
import re
import sys

from sch_place import SCH
from sch_power import balanced

# ref: (x, y, rotation, (dx, dy) of the first visible field from the symbol; the next ones stack 2.54 mm below);
# a rotation written "270y" also mirrors the symbol left to right
LAYOUT = {
    # chain 9: the three wheels side by side across the controls zone, as on the board edge; text off the wheels, LED
    # and BOOT button; SW2 down a little, clear of the LED_B line
    "RV1": (40.64, 205.74, 0, (15.24, 2.54)), "RV2": (91.44, 205.74, 0, (15.24, 2.54)), "RV3": (142.24, 205.74, 0, (15.24, 2.54)),
    "D1": (142.24, 302.26, 0, (-5.08, -15.24)), "SW2": (96.52, 335.28, 0, (-5.08, 5.08)),
    # chain 8: U4 right so its left-side lines have room to turn; its text below right
    "U4": (381.0, 307.34, 0, (17.78, 30.48)),
    # chain 7: U5 on the FL1 line (RF2 at 127), J2 at the end of it, D5 turned so its IO pin hangs from the antenna line
    "U5": (530.86, 129.54, 0, (-38.1, -25.4)),
    "J2": (571.5, 127.0, 0, (-22.86, -13.97)),
    "D5": (552.45, 130.81, 270, (-3.81, 10.16)),
    "SW1": (96.52, 368.3, 0, (3.81, 11.43)),
    # chain 6: U7 lower, so its six control lines can run left under U2 and turn down in a ribbon to SW3, with each
    # pull-down hanging in the gap the lines below it leave; SW3 turned and mirrored so its contacts point up, 1 to 6
    # left to right; U7's text to the lower right, SW3's to its right
    "U7": (421.64, 144.78, 0, (15.24, 33.02)),
    "SW3": (363.22, 185.42, "270y", (10.16, -2.54)),
    # chain 4: Y2 stays; its text moves to the lower right, clear of its pin names and below R4
    "Y2": (223.52, 50.8, 0, (16.51, 6.35)),
    # chain 2: U3 stays; its text moves above the body, clear of the VIN and VOUT lines
    "U3": (120.65, 45.72, 0, (-7.62, -12.7)),
    # chain 1: U6 below J1 on the DM/DP rows; the CC ESD diodes turned so IO is on top, hanging from their CC lines
    "U6": (66.04, 101.6, 0, (6.35, 8.89)),
    "D4": (93.98, 69.85, 180, (-1.27, 6.35)),
    "D3": (142.24, 67.31, 180, (3.81, -1.27)),
}


def main():
    text = open(SCH, encoding="utf-8").read()
    for ref, (x, y, rot, (fx, fy)) in LAYOUT.items():
        mirror = "y" if str(rot).endswith("y") else None
        rot = int(str(rot).rstrip("y"))
        m = re.search(r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)(?:(?!\n\t\(symbol\n).)*?\(property "Reference" "%s"\n' % re.escape(ref), text, re.S)
        s = m.start() + 2
        e = balanced(text, s)
        blk = text[s:e]
        blk = re.sub(r'^(\t\t\(at )[\d.-]+ [\d.-]+(?: [\d.-]+)?\)\n(?:\t\t\(mirror [xy]\)\n)?',
                     lambda q: f"{q.group(1)}{x:.2f} {y:.2f} {rot})\n" + (f"\t\t(mirror {mirror})\n" if mirror else ""), blk, count=1, flags=re.M)
        k = 0

        def field(q):
            nonlocal k
            body = q.group(0)
            if "(hide yes)" in body:
                return re.sub(r'\(at [\d.-]+ [\d.-]+ [\d.-]+\)', f"(at {x:.2f} {y:.2f} 0)", body, count=1)
            at = f"(at {x + fx:.2f} {y + fy + 2.54 * k:.2f} {rot % 180})"  # reads left to right on a turned part
            k += 1
            just = "right" if (rot in (90, 180)) != bool(mirror) else "left"  # KiCad mirrors justification on a turned or mirrored part
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
