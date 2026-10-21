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

# ---- Nets: every pin of every part ----
nets = doc.get("nets", {})
no_map = [p["ref"] for p in parts if "pinmap" not in p]
check(not no_map, "Every part has a pin map" + (f": missing on {', '.join(no_map)}" if no_map else ""))
count = [f"{p['ref']} {len(p['pinmap'])}/{p['pins']}" for p in parts if "pinmap" in p and len(p["pinmap"]) != p["pins"]]
check(not count, f"Pin coverage: every part's map has exactly its datasheet pin count ({sum(p['pins'] for p in parts)} pins)" + (f": {', '.join(count)}" if count else ""))

members = {}
for p in parts:
    for pin, d in p.get("pinmap", {}).items():
        members.setdefault(d["net"], []).append(f"{p['ref']}.{pin}")
used = set(members) - {"NC"}
undescribed, unused = sorted(used - set(nets)), sorted(set(nets) - used)
check(not undescribed and not unused, f"Every net is described and used ({len(used)} nets)"
      + (f": undescribed {', '.join(undescribed)}" if undescribed else "") + (f"; described but unused {', '.join(unused)}" if unused else ""))

single = [n for n in used if n not in doc.get("pad_nets", []) and len({m.split('.')[0] for m in members[n]} - {r for r in refs if r.startswith("TP")}) < 2]
check(not single, "Every net joins at least two parts (test pads don't count; SWD pads listed in pad_nets)" + (f": {', '.join(sorted(single))}" if single else ""))

shorted = [p["ref"] for p in parts if p["pins"] == 2 and "pinmap" in p and len({d["net"] for d in p["pinmap"].values()}) < 2 and p["ref"][0] in "CRLF"]
check(not shorted, "No two-pin passive has both ends on one net" + (f": {', '.join(shorted)}" if shorted else ""))

SUPPLY = re.compile(r"^(VDD|VDDA|VBAT|VA|VD|VIN|Vcc3p3|VccIO|VcpExt)$")
GROUND = re.compile(r"^(GND|VSS|VSSA|RFGND|Exposed pad|DAP)$")
bad_pwr = [f"{p['ref']}.{k} {d['name']}→{d['net']}" for p in parts for k, d in p.get("pinmap", {}).items()
           if "name" in d and ((SUPPLY.match(d["name"]) and d["net"] in ("NC", "GND")) or (GROUND.match(d["name"]) and d["net"] != "GND")
                               or (d["name"] == "NC" and d["net"] != "NC"))]
check(not bad_pwr, "Supply pins powered, ground pins on GND, NC pins open" + (f": {', '.join(bad_pwr)}" if bad_pwr else ""))

far = []
for p in parts:
    lt = p.get("local_to", "")
    if "." in lt:
        ref, pin = lt.split(".", 1)
        target = by_ref[ref].get("pinmap", {}).get(pin, {}).get("net")
        mine = {d["net"] for d in p.get("pinmap", {}).values()}
        if target is None or target not in mine:
            far.append(f"{p['ref']} vs {lt} ({target})")
check(not far, "Every part placed 'local_to' a pin shares a net with it" + (f": {', '.join(far)}" if far else ""))

# ---- The wiring page must agree pin by pin ----
WIRING = os.path.join(DESIGN, "wiring.html")
w = open(WIRING, encoding="utf-8").read()
w_nets = set(re.findall(r'\{ name: "([A-Z0-9_]+)", layer:', w)) | {"ATT_" + c for c in re.findall(r'\["(C[0-9_]+)", \d+, \d+, \d+, "', w)} | {f"WHEEL{n}" for n in (1, 2, 3)}
missing_w = sorted(n for n in w_nets if n not in nets)
check(not missing_w, f"Every net on the wiring page exists in netlist.json ({len(w_nets)} nets)" + (f": {', '.join(missing_w)}" if missing_w else ""))


def pin_ids(num, name):
    tokens = num.replace("′", "'").split()
    if tokens and all(re.fullmatch(r"\d+'?|[AB]\d+", t) for t in tokens):
        return tokens
    ids = []
    for a, b in re.findall(r"(\d+)(?:–(\d+))?", name):
        ids += [str(k) for k in range(int(a), int(b) + 1)] if b else [a]
    return ids + (["DAP"] if "DAP" in name else []) + (["EP"] if "pad" in name else [])


segment = doc.get("page_segments", {})
mismatch, compared, skipped = [], 0, []
for ref, body in re.findall(r'const \w+ = \{ ref: "(\w+)",(.*?)\] \};', w, re.S):
    if ref not in by_ref:
        continue
    pm = by_ref[ref]["pinmap"]
    for line in re.findall(r"\{ side: [^\n]*", body):
        if 'num: "' not in line:
            continue  # generated rows (U7/SW3 attenuator bits) are covered by the net-name check
        num = re.search(r'num: "([^"]*)"', line).group(1)
        name = re.search(r'name: "([^"]*)"', line).group(1)
        net = re.search(r'net: "([^"]*)"', line)
        layer = re.search(r'layer: "([^"]*)"', line)
        ext = re.search(r'ext: \["([^"]*)"', line)
        if net:
            ok = lambda j: segment.get(j, j) == net.group(1)
        elif ext and ext.group(1).startswith("▲ 3V3"):
            ok = lambda j: j in ("3V3", "RX_VDD", "U5_VDD")
        elif layer and layer.group(1) in ("gnd", "rf") and (num in ("NC", "OPEN") or (ext and ext.group(1).startswith("Not connected"))):
            ok = lambda j: j == "NC"
        elif layer and layer.group(1) == "gnd":
            ok = lambda j: j == "GND"
        else:
            continue
        ids = [i for i in pin_ids(num, name) if i in pm]
        if not ids:  # pins the page groups or names differently: J1's paired contacts, SW1's tab pin 4, J2's centre and legs
            usb = set(re.findall(r"[AB]\d+", num + " " + name))
            norm = lambda t: t.lower().rstrip("s")
            ids = [k for k, v in pm.items() if (usb and usb & set(re.findall(r"[AB]\d+", k))) or (k[:len(num)] == num and k[len(num):].isalpha())
                   or (name and norm(v.get("name", "")) == norm(name))]
        if not ids:
            skipped.append(f"{ref} {num}")
        for i in ids:
            compared += 1
            if not ok(pm[i]["net"]):
                mismatch.append(f"{ref}.{i} page {net.group(1) if net else (ext.group(1) if ext else layer.group(1))} vs JSON {pm[i]['net']}")
check(not mismatch, f"Wiring page and netlist.json agree on {compared} pins" + (f": {'; '.join(mismatch)}" if mismatch else ""))
if skipped:
    print(f"      not compared (pin names differ between the two files): {', '.join(skipped)}")

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
