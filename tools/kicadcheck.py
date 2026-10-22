"""Checks KiCad's own files against design/rev-a/netlist.json (connections, parts, JLC codes) and the Rev A placement in layout.html.
Usage (from the repo root; exit code 1 if any check fails):
  python tools/kicadcheck.py --net board.net                 schematic netlist: kicad-cli sch export netlist --format kicadsexpr
  python tools/kicadcheck.py --bom board.csv                 schematic BOM:     kicad-cli sch export bom --fields "Reference,Value,Footprint,LCSC,MPN"
  python tools/kicadcheck.py --pcb board.kicad_pcb           the board itself: pads and their nets, positions, sides, outline
  Options: --layout A (placement in layout.html to compare with), --tol 1.5 (mm, major-part position), --local 4 (mm, part to its pin)"""
import argparse
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, "design", "rev-a")
ENVELOPE = (46.45, 71.40)  # board outline, mm (layout.html, unchanged since 2026-10-20)


# ---- S-expressions (KiCad's file format) ----
def sexpr(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur); cur = []
        elif t == ")":
            done = cur; cur = stack.pop(); cur.append(done)
        else:
            cur.append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\") if t.startswith('"') else t)
    return cur[0]


def kids(node, tag):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == tag]


def kid(node, tag):
    k = kids(node, tag)
    return k[0] if k else None


def atom(node, tag, default=None):
    k = kid(node, tag)
    return k[1] if k and len(k) > 1 and not isinstance(k[1], list) else default


# ---- Readers ----
def read_reference():
    doc = json.load(open(os.path.join(DESIGN, "netlist.json"), encoding="utf-8"))
    return doc, {p["ref"]: p for p in doc["parts"]}


def read_net(path):
    """KiCad schematic netlist -> parts {ref: {value, footprint, fields}}, pins {(ref, pin): net}"""
    root = sexpr(open(path, encoding="utf-8").read())
    parts, pins = {}, {}
    for comp in kids(kid(root, "components"), "comp"):
        fields = {}
        for f in kids(kid(comp, "fields") or ["fields"], "field"):
            vals = [v for v in f[1:] if not isinstance(v, list)]
            fields[atom(f, "name")] = vals[0] if vals else ""
        for prop in kids(comp, "property"):
            fields.setdefault(atom(prop, "name"), atom(prop, "value", ""))
        parts[atom(comp, "ref")] = {"value": atom(comp, "value", ""), "footprint": atom(comp, "footprint", ""), "fields": fields}
    for net in kids(kid(root, "nets"), "net"):
        name = atom(net, "name", "")
        for node in kids(net, "node"):
            pins[(atom(node, "ref"), atom(node, "pin"))] = name
    return parts, pins


def read_pcb(path):
    """KiCad board -> footprints {ref: {x, y, rot, layer, fields, footprint, pads: {pad: (net, x, y)}}}, outline bbox"""
    root = sexpr(open(path, encoding="utf-8").read())
    fps = {}
    for fp in kids(root, "footprint"):
        at = kid(fp, "at"); X, Y = float(at[1]), float(at[2]); R = float(at[3]) if len(at) > 3 else 0.0
        props = {p[1]: p[2] for p in kids(fp, "property") if len(p) > 2 and not isinstance(p[2], list)}
        ref = props.get("Reference") or next((t[2] for t in kids(fp, "fp_text") if len(t) > 2 and t[1] == "reference"), "?")
        a = math.radians(R)
        pads = {}
        for pad in kids(fp, "pad"):
            pat = kid(pad, "at"); px, py = float(pat[1]), float(pat[2])
            # KiCad: y points down, footprint angle counter-clockwise on screen; bottom-side footprints are stored already mirrored.
            # Checked against KiCad's own pcbnew on the StickHub demo (every side and rotation)
            wx, wy = X + px * math.cos(a) + py * math.sin(a), Y - px * math.sin(a) + py * math.cos(a)
            net = kid(pad, "net")
            name = next((v for v in (net or [])[1:] if not isinstance(v, list) and not re.fullmatch(r"\d+", v)), "") if net else ""
            num = pad[1]
            if num == "" or (num in pads and pads[num][0] == name):
                continue  # unnumbered mechanical pads; repeated pads of one pin (e.g. a shell)
            while num in pads:
                num += "#"  # same pad number on two different nets: kept apart so the check reports it
            pads[num] = (name, wx, wy)
        fps[ref] = {"x": X, "y": Y, "rot": R, "layer": atom(fp, "layer", ""), "fields": props, "footprint": fp[1], "pads": pads}
    xs, ys = [], []
    for g in [n for n in root[1:] if isinstance(n, list) and n and n[0] in ("gr_line", "gr_rect", "gr_arc")]:
        if atom(g, "layer") == "Edge.Cuts":
            for tag in ("start", "end", "mid"):
                k = kid(g, tag)
                if k:
                    xs.append(float(k[1])); ys.append(float(k[2]))
    outline = (min(xs), min(ys), max(xs), max(ys)) if xs else None
    return fps, outline


def read_layout(n):
    """Placement concept n from layout.html: {ref: (x, y, rot)} in phone-back coordinates"""
    html = open(os.path.join(DESIGN, "layout.html"), encoding="utf-8").read()
    block = re.search(r"\n  %s: \{ name:.*?place: \[(.*?)\] \}" % re.escape(str(n)), html, re.S).group(1)
    return {r: (float(x), float(y), float(a)) for r, x, y, a in re.findall(r'\["(\w+)", ([\d.]+), ([\d.]+), (-?\d+)\]', block)}


# ---- Connectivity: pin names, then nets as groups of pins ----
def candidates(pin, part):
    """KiCad pad numbers a netlist.json pin may appear as"""
    c = {pin}
    m = re.fullmatch(r"(\d+)[a-z']", pin)
    if m:
        c.add(m.group(1))  # SW1 4a..4d -> 4, SW2 1' -> 1
    c |= set(re.findall(r"[AB]\d+", pin))  # J1 A1B12 -> A1, B12
    if pin in ("EP", "DAP"):
        numbered = [int(k) for k in part["pinmap"] if k.isdigit()]
        c |= {str(max(numbered) + 1), "EP", "0", "PAD"}
    if re.fullmatch(r"SH\d", pin):
        c |= {"S1", "SH", "0", "13", "MP"}
    if re.fullmatch(r"[DM]\d", pin):
        c |= {"4", "5", "6", "7", "MP"}
    return c


def compare(ref_parts, ref_pins, k_pins, label, out, ref_names=None):
    """ref_pins / k_pins: {(ref, pin): net}. ref_parts: {ref: part with pinmap} or None (generic reference)."""
    add = out.append
    k_refs = {r for r, _ in k_pins}
    r_refs = {r for r, _ in ref_pins}
    missing, extra = sorted(r_refs - k_refs), sorted(k_refs - r_refs - {r for r in k_refs if r.startswith(("H", "FID", "MH", "LOGO", "G"))})
    add((not missing, f"{label}: every part is present" + (f": missing {', '.join(missing)}" if missing else "")))
    add((not extra, f"{label}: no parts that aren't in the reference" + (f": extra {', '.join(extra)}" if extra else "")))
    # match each reference pin to a KiCad pad
    match, lost, used = {}, [], set()
    for (r, p), net in ref_pins.items():
        if r not in k_refs:
            continue
        cands = candidates(p, ref_parts[r]) if ref_parts else {p}
        hits = [c for c in sorted(cands, key=lambda c: c != p) if (r, c) in k_pins]
        if not hits:
            if net != "NC":
                lost.append(f"{r}.{p}")
            continue
        # a paired USB-C contact (A1B12) is one pad in some footprints and two in others: claim every pad it names
        for hit in (hits if re.fullmatch(r"([AB]\d+){2}", p) else hits[:1]):
            match[(r, p, hit)] = (r, hit); used.add((r, hit))
    add((not lost, f"{label}: every connected pin has a pad" + (f": none for {', '.join(lost[:20])}" + (" …" if len(lost) > 20 else "") if lost else "")))
    unmatched = sorted(f"{r}.{p}" for (r, p), net in k_pins.items() if r in r_refs and (r, p) not in used and net and not net.startswith("unconnected"))
    add((not unmatched, f"{label}: no connected pad without a reference pin" + (f": {', '.join(unmatched[:20])}" if unmatched else "")))
    # groups: a reference net must land on exactly one KiCad net, and a KiCad net must not join two reference nets
    k_of, r_of = {}, {}
    for (r, p, _), kp in match.items():
        rn, kn = ref_pins[(r, p)], k_pins[kp]
        if rn == "NC":
            continue
        k_of.setdefault(rn, set()).add(kn); r_of.setdefault(kn, set()).add(rn)
    split = sorted(f"{rn} → {' | '.join(sorted(ks))}" for rn, ks in k_of.items() if len(ks) > 1)
    merged = sorted(f"{kn or '(no net)'} joins {' + '.join(sorted(rs))}" for kn, rs in r_of.items() if len(rs) > 1)
    add((not split, f"{label}: no net broken in two (an open)" + (f": {'; '.join(split)}" if split else "")))
    add((not merged, f"{label}: no two nets joined (a short)" + (f": {'; '.join(merged)}" if merged else "")))
    # pins meant to be open must not share a KiCad net with anything
    counts = {}
    for kp, kn in k_pins.items():
        counts[kn] = counts.get(kn, 0) + 1
    nc_hit = sorted(f"{r}.{p}" for (r, p, _), kp in match.items() if ref_pins[(r, p)] == "NC" and k_pins[kp] and counts[k_pins[kp]] > 1 and not k_pins[kp].startswith("unconnected"))
    add((not nc_hit, f"{label}: pins meant to be open are open" + (f": connected {', '.join(nc_hit)}" if nc_hit else "")))
    if ref_names is not False:
        renamed = sorted(f"{rn} is {next(iter(ks))}" for rn, ks in k_of.items() if len(ks) == 1 and next(iter(ks)).lstrip("/") != rn.lstrip("/") and not next(iter(ks)).startswith("Net-("))
        if renamed:
            add((None, f"{label}: named differently (fine if intended): {', '.join(renamed[:15])}" + (" …" if len(renamed) > 15 else "")))


def json_pins(by_ref):
    return {(r, pin): d["net"] for r, p in by_ref.items() for pin, d in p.get("pinmap", {}).items() if not r.startswith("TP")}


def check_fields(by_ref, kparts, label, out):
    """JLC needs the LCSC code on every ordered part; the part number and package must match the reference"""
    no_code, wrong_code, wrong_mpn, wrong_pkg = [], [], [], []
    for r, kp in kparts.items():
        p = by_ref.get(r)
        if not p or not p["mpn"]:
            continue
        f = {k.upper(): v for k, v in kp["fields"].items() if k}
        code = f.get("LCSC") or f.get("LCSC PART") or f.get("JLCPCB PART #") or f.get("JLC")
        if not code:
            no_code.append(r)
        elif code != p["lcsc"]:
            wrong_code.append(f"{r} {code}≠{p['lcsc']}")
        mpn = f.get("MPN") or f.get("MANUFACTURER PART NUMBER") or f.get("MFR PART")
        if mpn and mpn.upper() != p["mpn"].upper():
            wrong_mpn.append(f"{r} {mpn}≠{p['mpn']}")
        size = re.fullmatch(r"0402|0603|0805", p["package"])
        if size and kp["footprint"] and size.group(0) not in kp["footprint"] and {"0402": "1005", "0603": "1608", "0805": "2012"}[size.group(0)] not in kp["footprint"]:
            wrong_pkg.append(f"{r} {kp['footprint']} (want {p['package']})")
    out.append((not no_code, f"{label}: every ordered part carries its LCSC code" + (f": missing on {', '.join(no_code)}" if no_code else "")))
    out.append((not wrong_code, f"{label}: LCSC codes match netlist.json" + (f": {', '.join(wrong_code)}" if wrong_code else "")))
    out.append((not wrong_mpn, f"{label}: part numbers match netlist.json" + (f": {', '.join(wrong_mpn)}" if wrong_mpn else "")))
    out.append((not wrong_pkg, f"{label}: passive footprints are the right size" + (f": {', '.join(wrong_pkg)}" if wrong_pkg else "")))


def check_bom(by_ref, path, out):
    import csv
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    col = lambda row, *names: next((row[k] for k in row if k and k.strip().upper() in names), "")
    kparts = {}
    for row in rows:
        for r in re.split(r"[,\s]+", col(row, "REFERENCE", "REFS", "REF", "DESIGNATOR")):
            if r:
                kparts[r] = {"value": col(row, "VALUE"), "footprint": col(row, "FOOTPRINT"),
                             "fields": {"LCSC": col(row, "LCSC", "LCSC PART", "JLCPCB PART #"), "MPN": col(row, "MPN", "MANUFACTURER PART NUMBER")}}
    want = {r for r, p in by_ref.items() if p["mpn"]}
    missing, extra = sorted(want - set(kparts)), sorted(set(kparts) - want - {r for r in kparts if r.startswith("TP")})
    out.append((not missing, "BOM: every ordered part is listed" + (f": missing {', '.join(missing)}" if missing else "")))
    out.append((not extra, "BOM: nothing extra" + (f": {', '.join(extra)}" if extra else "")))
    check_fields(by_ref, kparts, "BOM", out)


def check_pcb(by_ref, fps, outline, layout_n, tol, local, out):
    add = out.append
    k_pins = {(r, num): net for r, f in fps.items() for num, (net, _, _) in f["pads"].items()}
    compare(by_ref, json_pins(by_ref), k_pins, "Board", out)
    check_fields(by_ref, {r: {"value": "", "footprint": f["footprint"], "fields": f["fields"]} for r, f in fps.items()}, "Board", out)
    back = sorted(r for r, f in fps.items() if f["layer"] != "F.Cu")
    add((not back, "Board: every part on the top side (M7)" + (f": on the bottom {', '.join(back)}" if back else "")))
    if outline:
        w, h = outline[2] - outline[0], outline[3] - outline[1]
        add((abs(w - ENVELOPE[0]) < 0.1 and abs(h - ENVELOPE[1]) < 0.1, f"Board: outline {w:.2f} × {h:.2f} mm (envelope {ENVELOPE[0]} × {ENVELOPE[1]})"))
    else:
        add((False, "Board: no Edge.Cuts outline found"))
    # placement against the sketch: anchor on J1 (on the midline of the bottom edge), then compare every sketched part
    plan = read_layout(layout_n)
    if "J1" in fps and "J1" in plan:
        dx, dy = plan["J1"][0] - fps["J1"]["x"], plan["J1"][1] - fps["J1"]["y"]
        off = []
        for r, (x, y, _) in plan.items():
            if r in fps:
                d = math.hypot(fps[r]["x"] + dx - x, fps[r]["y"] + dy - y)
                if d > tol:
                    off.append(f"{r} {d:.1f} mm")
        add((not off, f"Board: major parts within {tol} mm of layout {layout_n} (anchored on J1)" + (f": {', '.join(off)}" if off else "")))
    # every part placed 'local_to' a pin sits near that pin's pad
    far = []
    for r, p in by_ref.items():
        lt = p.get("local_to", "")
        if "." not in lt or r not in fps:
            continue
        tr, tp = lt.split(".", 1)
        f = fps.get(tr)
        if not f:
            continue
        pad = next((f["pads"][c] for c in sorted(candidates(tp, by_ref[tr]), key=lambda c: c != tp) if c in f["pads"]), None)
        if pad:
            d = math.hypot(fps[r]["x"] - pad[1], fps[r]["y"] - pad[2])
            if d > local:
                far.append(f"{r} {d:.1f} mm from {lt}")
    add((not far, f"Board: every local part within {local} mm of its pin" + (f": {', '.join(far)}" if far else "")))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--net"); ap.add_argument("--bom"); ap.add_argument("--pcb")
    ap.add_argument("--layout", default="A"); ap.add_argument("--tol", type=float, default=1.5); ap.add_argument("--local", type=float, default=4.0)
    a = ap.parse_args(argv)
    if not (a.net or a.bom or a.pcb):
        ap.error("give at least one of --net, --bom, --pcb")
    doc, by_ref = read_reference()
    out = []
    if a.net:
        kparts, k_pins = read_net(a.net)
        compare(by_ref, json_pins(by_ref), k_pins, "Schematic", out)
        check_fields(by_ref, kparts, "Schematic", out)
    if a.bom:
        check_bom(by_ref, a.bom, out)
    if a.pcb:
        fps, outline = read_pcb(a.pcb)
        check_pcb(by_ref, fps, outline, a.layout, a.tol, a.local, out)
    for ok, text in out:
        print({True: "PASS  ", False: "FAIL  ", None: "NOTE  "}[ok] + text)
    return 1 if any(ok is False for ok, _ in out) else 0


if __name__ == "__main__":
    sys.exit(main())
