"""Step 2.6: writes each Rev A part's footprint, as chosen in kicad/rev-a/footprints.md (the IphoneFM.pretty copies), into
the Footprint field of its symbol on the schematic. Prints what changed.
Usage (from the repository root): python tools/sch_footprints.py [--dry-run]"""
import re
import sys

sys.path.insert(0, "tools")
from rev_a_footprints import project_map

SCH = "kicad/rev-a/IphoneFM.kicad_sch"
BLOCK = re.compile(r"\n\t\(symbol\n.*?\n\t\)(?=\n)", re.S)  # placed symbols (library symbols sit one level deeper)


def main():
    fps = {ref: "IphoneFM:" + path.split("/")[-1] for ref, path in project_map().items()}
    text = open(SCH, encoding="utf-8").read()
    seen, changed = set(), 0

    def repl(m):
        nonlocal changed
        blk = m.group(0)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk)
        if not ref or ref.group(1).startswith("#"):
            return blk
        ref = ref.group(1)
        if ref not in fps:
            print(f"{ref}: no footprint chosen")
            return blk
        seen.add(ref)
        old = re.search(r'\(property "Footprint" "([^"]*)"', blk).group(1)
        if old != fps[ref]:
            changed += 1
            print(f"{ref:5} {old or '(empty)':52} -> {fps[ref]}")
        return re.sub(r'(\(property "Footprint" )"[^"]*"', lambda q: f'{q.group(1)}"{fps[ref]}"', blk, count=1)

    text = BLOCK.sub(repl, text)
    missing = sorted(set(fps) - seen)
    print(f"{len(seen)} symbols, {changed} changed; chosen but not on the schematic: {missing or 'none'}")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
