"""Step 2.3 check: every symbol pin number on the Rev A schematic has a pad of the same number on the footprint chosen
for that part in kicad/rev-a/footprints.md, and no pad is left without a pin; also lists pad numbers used more than once.
Run from the repository root: python tools/pinpad_check.py"""
import sys, collections
sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid
from rev_a_footprints import project_map
FP = project_map()
sch = sexpr(open("kicad/rev-a/IphoneFM.kicad_sch", encoding="utf-8").read())
libs = {s[1]: s for s in kids(kid(sch, "lib_symbols"), "symbol")}
def pins(sym):
    out = []
    for sub in kids(sym, "symbol"):
        out += [kid(pp, "number")[1] for pp in kids(sub, "pin")]
    return out
res = collections.OrderedDict()
for s in kids(sch, "symbol"):
    lib = kid(s, "lib_id")[1]
    ref = next((pr[2] for pr in kids(s, "property") if pr[1] == "Reference"), None)
    if not ref or ref.startswith("#"): continue
    if ref not in FP: res[ref] = ("NO FOOTPRINT", lib, [], []); continue
    sp = pins(libs[lib]); fp = sexpr(open(FP[ref] + ".kicad_mod", encoding="utf-8").read())
    pads = [p[1] for p in kids(fp, "pad") if p[1] != ""]
    res[ref] = (FP[ref].split("/")[-1], lib, sp, pads)
bad = 0
groups = collections.defaultdict(list)
for ref, (fpn, lib, sp, pads) in res.items():
    ms = sorted(set(sp) - set(pads), key=str); xp = sorted(set(pads) - set(sp), key=str)
    if fpn == "NO FOOTPRINT" or ms or xp:
        bad += 1; print(f"{ref:5} {fpn}\n      symbol pins without a pad: {ms}\n      pads without a symbol pin: {xp}\n      pad numbers: {collections.Counter(pads)}")
    else:
        groups[fpn].append(ref)
print("\nOK:", {k: len(v) for k, v in groups.items()})
print("symbols checked:", len(res), " with mismatches:", bad)
print()
for r in [r for r in res if len(set(res[r][3])) < len(res[r][3])]:
    fpn, lib, sp, pads = res[r]
    c1, c2 = collections.Counter(sp), collections.Counter(pads)
    print(r, "symbol pins used twice or more:", {k: v for k, v in c1.items() if v > 1}, "| pads used twice or more:", {k: v for k, v in c2.items() if v > 1})
