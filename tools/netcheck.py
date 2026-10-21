"""Checks design/analog-fm/netlist.json, the parts list (and later the nets) that every other design file is checked against.
Usage: python tools/netcheck.py            (from the repo root; exit code 1 if any check fails)
       python tools/netcheck.py --bom      also print the BOM grouped by part number"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, "design", "analog-fm")
NETLIST = os.path.join(DESIGN, "netlist.json")
REQUIRED = ("ref", "value", "mpn", "maker", "lcsc", "package", "pins", "chain", "function")
TOO_SMALL = ("0201", "01005")  # JLC economic assembly and the user's rule: nothing smaller than 0402

fails = []


def check(ok, text):
    print(("PASS  " if ok else "FAIL  ") + text)
    if not ok:
        fails.append(text)


def ref_key(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


doc = json.load(open(NETLIST, encoding="utf-8"))
parts = doc["parts"]
refs = [p["ref"] for p in parts]
by_ref = {p["ref"]: p for p in parts}
placed = [p for p in parts if p["mpn"]]  # test pads are bare copper, not ordered parts

dupes = sorted({r for r in refs if refs.count(r) > 1})
check(not dupes, f"Designators unique ({len(refs)} parts)" + (f": duplicates {', '.join(dupes)}" if dupes else ""))

missing = [f"{p.get('ref', '?')}.{f}" for p in parts for f in REQUIRED if f not in p]
check(not missing, "Every part has " + ", ".join(REQUIRED) + (f": missing {', '.join(missing)}" if missing else ""))

bad_ref = [r for r in refs if not re.fullmatch(r"(U|J|SW|D|Y|RV|FB|L|C|R|TP)\d+", r)]
check(not bad_ref, "Designators use the standard prefixes" + (f": {', '.join(bad_ref)}" if bad_ref else ""))

bad_lcsc = [p["ref"] for p in placed if not re.fullmatch(r"C\d+", p["lcsc"])]
check(not bad_lcsc, "Every ordered part has a JLC/LCSC code" + (f": missing on {', '.join(bad_lcsc)}" if bad_lcsc else ""))

small = [p["ref"] for p in parts if any(s in p["package"] for s in TOO_SMALL)]
check(not small, "Nothing smaller than 0402" + (f": {', '.join(small)}" if small else ""))

# The same part number must always carry the same code, package and value
seen, clash = {}, []
for p in placed:
    key = (p["lcsc"], p["package"], p["value"], p["maker"])
    if p["mpn"] in seen and seen[p["mpn"]] != key:
        clash.append(p["mpn"])
    seen.setdefault(p["mpn"], key)
check(not clash, "Each part number has one code, package and value" + (f": {', '.join(sorted(set(clash)))}" if clash else ""))
codes = {}
for p in placed:
    codes.setdefault(p["lcsc"], set()).add(p["mpn"])
shared = [c for c, m in codes.items() if len(m) > 1]
check(not shared, "Each JLC code belongs to one part number" + (f": {', '.join(shared)}" if shared else ""))

bad_local = [f"{p['ref']} → {p['local_to']}" for p in parts if "local_to" in p and p["local_to"].split(".")[0] not in by_ref]
check(not bad_local, "Every 'local_to' names a part that exists" + (f": {', '.join(bad_local)}" if bad_local else ""))

# Every ordered part number must appear in bom.md, so the two lists can't drift apart
BOM_PATH = os.path.join(DESIGN, "bom.md")
bom_text = open(BOM_PATH, encoding="utf-8").read()
bom = bom_text.upper()
absent = sorted({p["mpn"] for p in placed if p["mpn"].upper() not in bom and p["mpn"].upper().replace("-", "") not in bom.replace("-", "")})
check(not absent, "Every part number appears in bom.md" + (f": not found {', '.join(absent)}" if absent else ""))

# Each "## Chain N" in bom.md opens with a designator line generated from the JSON; --sync-bom rewrites them
def designator_line(chain):
    items = sorted((p for p in parts if p["chain"] == chain), key=lambda p: ref_key(p["ref"]))
    return "**Designators:** " + "; ".join(f"{p['ref']} {p['function']}" + (f" ({p['value']})" if p["ref"][0] in "CRLF" else "") for p in items) + "."


chain_re = re.compile(r"^## Chain (\d+):.*\n\n(\*\*Designators:\*\*.*\n\n)?", re.M)
if "--sync-bom" in sys.argv:
    bom_text = chain_re.sub(lambda m: m.group(0)[:m.end(0) - m.start(0) - (len(m.group(2)) if m.group(2) else 0)] + designator_line(int(m.group(1))) + "\n\n", bom_text)
    open(BOM_PATH, "w", encoding="utf-8", newline="\n").write(bom_text)
    print("      rewrote the designator lines in bom.md")
stale = [m.group(1) for m in chain_re.finditer(bom_text) if (m.group(2) or "").strip() != designator_line(int(m.group(1)))]
check(not stale, "bom.md designator lines match netlist.json" + (f": out of date in chain {', '.join(stale)} (run with --sync-bom)" if stale else ""))

kinds = {}
for r in refs:
    kinds[ref_key(r)[0]] = kinds.get(ref_key(r)[0], 0) + 1
print("      " + ", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + f"; {len(placed)} placed parts, {len(seen)} part numbers")

if "--bom" in sys.argv:
    print()
    groups = {}
    for p in placed:
        groups.setdefault(p["mpn"], []).append(p["ref"])
    for mpn, rs in sorted(groups.items(), key=lambda kv: ref_key(sorted(kv[1], key=ref_key)[0])):
        p = by_ref[rs[0]]
        print(f"{len(rs):>3} × {mpn:<22} {p['lcsc']:<10} {p['package']:<34} {p['value']:<22} {', '.join(sorted(rs, key=ref_key))}")

sys.exit(1 if fails else 0)
