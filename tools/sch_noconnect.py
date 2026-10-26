"""Puts a no-connect flag (an X) on every pin netlist.json marks NC, on the Rev A schematic (step 1.32) [EES p39].
Each was checked against its datasheet first (design/rev-a/kicad-build-procedure.md, step 1.32). A rerun replaces them.
Usage: python tools/sch_noconnect.py [--dry-run]"""
import json
import re
import sys

from kicadcheck import sexpr, candidates
from sch_place import SCH, NETLIST, symbols_and_pins
from sch_power import balanced

UID = "0c0c0000"


def main():
    text = open(SCH, encoding="utf-8").read()
    out, i = [], 0  # drop any earlier flags
    for m in re.finditer(r'\n\t\(no_connect\b', text):
        s = m.start() + 2
        e = balanced(text, s)
        if f'(uuid "{UID}-' in text[s:e]:
            out.append(text[i:m.start()])
            i = e
    text = "".join(out) + text[i:]
    placed = symbols_and_pins(sexpr(text))
    flags, done = [], []
    for p in json.load(open(NETLIST, encoding="utf-8"))["parts"]:
        for pin, d in p["pinmap"].items():
            if d["net"] != "NC":
                continue
            for c in candidates(pin, p):
                if c in placed.get(p["ref"], {}).get("pins", {}):
                    x, y, _ = placed[p["ref"]]["pins"][c]
                    flags.append(f'\t(no_connect\n\t\t(at {x:.2f} {y:.2f})\n\t\t(uuid "{UID}-0000-4000-8000-{len(flags) + 1:012x}")\n\t)\n')
                    done.append(f"{p['ref']}.{c}")
    k = text.rindex("\t(sheet_instances")
    text = text[:k] + "".join(flags) + text[k:]
    print(f"{len(flags)} no-connect flags: {', '.join(done)}")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
