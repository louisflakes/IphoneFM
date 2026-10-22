"""Gives every pin of every symbol on the Rev A schematic a fixed ID, as KiCad itself saves them. The tools here write
symbols without them, and KiCad then makes up new ones at each load, so anything keyed on a pin (an ERC exclusion) would
not survive a reload. Each ID is derived from the symbol's own uuid and the pin number, so reruns give the same IDs.
Run last, after every other sch_* tool.
Usage: python tools/sch_pinids.py [--dry-run]"""
import re
import sys
import uuid

from kicadcheck import sexpr, kids, kid, atom
from sch_place import SCH
from sch_power import balanced

NS = uuid.UUID("5f1d0000-0000-4000-8000-000000000000")


def main():
    text = open(SCH, encoding="utf-8").read()
    root = sexpr(text)
    pins_of = {}
    for ls in kids(kid(root, "lib_symbols"), "symbol"):
        nums = []
        for sub in kids(ls, "symbol"):
            for p in kids(sub, "pin"):
                n = atom(kid(p, "number"), "number") or kid(p, "number")[1]
                if n not in nums:
                    nums.append(n)
        pins_of[ls[1]] = nums
    out, i, added = [], 0, 0
    for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "([^"]+)"\)', text):
        s = m.start() + 2
        e = balanced(text, s)
        blk = text[s:e]
        blk = re.sub(r'\t\t\(pin "[^"]*"\n\t\t\t\(uuid "[^"]*"\)\n\t\t\)\n', "", blk)  # replace any earlier set
        sym = re.search(r'\n\t\t\(uuid "([^"]+)"\)', blk).group(1)
        new = "".join(f'\t\t(pin "{n}"\n\t\t\t(uuid "{uuid.uuid5(NS, sym + "/" + n)}")\n\t\t)\n' for n in pins_of.get(m.group(1), []))
        k = blk.index("\t\t(instances")
        out.append(text[i:s] + blk[:k] + new + blk[k:])
        i = e
        added += new.count("(pin ")
    out.append(text[i:])
    print(f"{added} pins given fixed IDs")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write("".join(out))


if __name__ == "__main__":
    main()
