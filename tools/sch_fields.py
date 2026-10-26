"""Writes each Rev A symbol's value, MPN, LCSC code and manufacturer from netlist.json into the schematic.
Designators are left exactly as placed (never re-annotated); a symbol whose designator is not in netlist.json stops the run.
On chips and other non-passives the value describes the part, so the MPN is shown under it; on passives it stays hidden.
Usage: python tools/sch_fields.py [--dry-run]"""
import json
import re
import sys

from sch_place import SCH, NETLIST, LIB, prefix

FIELDS = (("MPN", "mpn"), ("LCSC", "lcsc"), ("Manufacturer", "maker"))


def prop(name, val, x, y, effects, angle=0):
    return f'\t\t(property "{name}" "{val}"\n\t\t\t(at {x:.2f} {y:.2f} {angle})\n\t\t\t{effects}\n\t\t)\n'


def fill(block, p):
    ref = p["ref"]
    block = re.sub(r'(\(property "Value" )"[^"]*"', lambda m: f'{m.group(1)}"{p["value"]}"', block, count=1)
    for name, _ in FIELDS:  # drop any earlier copy so a rerun gives the same result
        block = re.sub(r'\t\t\(property "%s" "[^"]*"\n.*?\n\t\t\)\n' % name, "", block, flags=re.S)
    x, y = (float(v) for v in re.search(r'\n\t\t\(at ([\d.-]+) ([\d.-]+)', block).groups())
    vx, vy, va, veff = re.search(r'\(property "Value" "[^"]*"\n\t\t\t\(at ([\d.-]+) ([\d.-]+) ?([\d.-]*)\)\n\t\t\t(\(effects .*\))\n', block).groups()
    hidden = "(effects (font (size 1.27 1.27)) (hide yes))"
    shown = prefix(ref) not in LIB
    new = prop("MPN", p["mpn"], float(vx), float(vy) + 2.54, veff if shown else hidden, va or 0)  # same angle as the value
    new += prop("LCSC", p["lcsc"], x, y, hidden) + prop("Manufacturer", p["maker"], x, y, hidden)
    k = block.index("\t\t(instances")
    return block[:k] + new + block[k:]


def main():
    text = open(SCH, encoding="utf-8").read()
    by = {p["ref"]: p for p in json.load(open(NETLIST, encoding="utf-8"))["parts"]}
    out, i, done = [], 0, []
    for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id ', text):
        s = m.start() + 2  # the symbol's opening bracket
        depth = 0
        for j in range(s, len(text)):
            depth += {"(": 1, ")": -1}.get(text[j], 0)
            if depth == 0:
                break
        block = text[s:j + 1]
        ref = re.search(r'\(property "Reference" "([^"]+)"', block).group(1)
        if not re.search(r'\(reference "%s"\)' % re.escape(ref), block):
            raise SystemExit(f"{ref}: instance designator differs from its Reference field")
        if ref.startswith("#"):  # power symbols carry no part data
            continue
        if ref not in by:
            raise SystemExit(f"{ref}: not in netlist.json")
        out.append(text[i:s] + fill(block, by[ref]))
        i = j + 1
        done.append(ref)
    out.append(text[i:])
    print(f"{len(done)} symbols filled; designators unchanged")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write("".join(out))


if __name__ == "__main__":
    main()
