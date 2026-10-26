"""Names every signal net on the Rev A schematic with a local label carrying its netlist.json name (step 1.30).
KiCad's own netlist says how the sheet is connected now; every connected group of a netlist.json net (an island) gets one
label: a lone chip pin at the end of a short stub (a lone passive pin at its tip), text running out from the pin; a wired group on one of its wire runs, text alongside, where
the text clears every part, power symbol, wire, field and earlier label. Islands of one net share one name, which is what
joins them. Rails are named by their power symbols and NC pins are left for step 1.32. A rerun replaces the labels.
Usage: python tools/sch_labels.py [--dry-run]"""
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid

from kicadcheck import sexpr, kids, kid, read_net, candidates
from sch_place import SCH, NETLIST, CW, LIB, prefix, symbols_and_pins
from sch_power import balanced
from sch_wire import G, cell, bodies, obstacles, existing_wires, line_cells

KICAD_CLI = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
RAILS = {"VBUS", "3V3", "VDDA", "RX_VDD", "GND", "NC"}
UID = "1abe1000"


def strip_labels(text):
    out, i = [], 0
    for m in re.finditer(r'\n\t\((?:label|wire)\b', text):
        if m.start() < i:
            continue
        s = m.start() + 2
        e = balanced(text, s)
        if f'(uuid "{UID}-' in text[s:e]:
            out.append(text[i:m.start()])
            i = e
    out.append(text[i:])
    return "".join(out)


def text_box(anchor, d, name):
    """Grid cells under a label's text: d is the direction the text runs from its anchor (left/right/up/down)"""
    n = int(len(name) * CW / G) + 1
    (ax, ay), cells = anchor, set()
    for i in range(1, n + 1):
        if d[0]:  # horizontal text sits just above its line, within one grid row
            cells.add((ax + d[0] * i, ay - 1))
        else:  # vertical text sits just left of its line
            cells.add((ax - 1, ay + d[1] * i))
    return cells


def label(name, anchor, d, n):
    x, y = anchor[0] * G, anchor[1] * G
    angle, just = {(1, 0): (0, "left"), (-1, 0): (180, "right"), (0, -1): (90, "left"), (0, 1): (270, "right")}[d]
    return (f'\t(label "{name}"\n\t\t(at {x:.2f} {y:.2f} {angle})\n\t\t(effects (font (size 1.27 1.27)) (justify {just} bottom))\n'
            f'\t\t(uuid "{UID}-0000-4000-8000-{n:012x}")\n\t)\n')


def main():
    text = strip_labels(open(SCH, encoding="utf-8").read())
    tmp = tempfile.mkdtemp()
    sch, net = os.path.join(tmp, "s.kicad_sch"), os.path.join(tmp, "s.net")
    open(sch, "w", encoding="utf-8", newline="\n").write(text)
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, sch], check=True, capture_output=True)
    _, kpins = read_net(net)
    root = sexpr(text)
    doc = json.load(open(NETLIST, encoding="utf-8"))
    placed = {r: s for r, s in symbols_and_pins(root).items() if r and not r.startswith("#")}
    hard, soft, pin_cell, foreign, ends = obstacles(root, placed, bodies(root, placed))
    blocked = hard | soft | set(foreign)
    # islands: the KiCad nets each netlist.json net is split into
    islands = {}
    for p in doc["parts"]:
        for pin, d in p["pinmap"].items():
            if d["net"] in RAILS:
                continue
            for c in candidates(pin, p):
                if (p["ref"], c) in kpins:
                    islands.setdefault((d["net"], kpins[(p["ref"], c)]), []).append((p["ref"], c))
    # wire runs, for islands with wires: each straight wire belongs to the island whose pins it reaches
    runs = [(a, b) for a, b in existing_wires(root)]
    adj = {}
    for a, b in runs:
        adj.setdefault(a, []).append((a, b)); adj.setdefault(b, []).append((a, b))
    chip = lambda ref: prefix(ref) not in LIB and not ref.startswith("TP")
    tips = {pin_cell[p][0] for p in pin_cell if chip(p[0])}
    near_tip = {(t[0] + dx, t[1] + dy) for t in tips for dx in range(-1, 2) for dy in range(-1, 2) if dx == 0 or dy == 0}
    drawn, placed_text, failed, n = [], set(), [], 0
    for (name, knet), pins in sorted(islands.items(), key=lambda kv: (len(kv[1]) > 1, kv[0])):
        n += 1
        options, own, tip_options = [], set(), []
        pins = list(dict.fromkeys(pins))
        for p in pins:  # at a pin tip, text running out from the part (or, on a two-pin part, along its side);
            c, o = pin_cell[p]  # a lone chip pin gets a 2.54 mm stub first, so its name clears the pin number
            if chip(p[0]):
                if len(pins) == 1:
                    options.append(((c[0] + 2 * o[0], c[1] + 2 * o[1]), o, c))
                continue
            tip_options += [(c, o)] + ([(c, d) for d in ((o[1], o[0]), (-o[1], -o[0]))] if prefix(p[0]) in LIB else [])
        if len(pins) > 1:  # walk the island's wires from its pins and try every run, longest first
            seen, stack = set(), [pin_cell[p][0] for p in pins]
            mine, own = [], set()
            while stack:
                c = stack.pop()
                for a, b in adj.get(c, []):
                    if (a, b) not in seen:
                        seen.add((a, b)); mine.append((a, b)); stack += [a, b]
            for a, b in mine:
                own |= set(line_cells(min(a, b), max(a, b)))
            for a, b in sorted(mine, key=lambda r: -max(abs(r[0][0] - r[1][0]), abs(r[0][1] - r[1][1]))):
                horiz = a[1] == b[1]
                for c in line_cells(min(a, b), max(a, b)):
                    if c not in near_tip:  # never right at a chip pin, where the name would run into its number
                        options += [(c, (1, 0)), (c, (-1, 0))] if horiz else [(c, (0, -1)), (c, (0, 1))]
        for opt in options + tip_options:  # a wired net reads best along one of its runs; a part's pin tip is the fallback
            c, d, stub = opt if len(opt) == 3 else (*opt, None)
            box = text_box(c, d, name) | ({c, (c[0] - d[0], c[1] - d[1])} if stub else set())
            if not box & ((blocked - (own if len(pins) > 1 else set())) | placed_text):
                if stub:
                    n += 1
                    drawn.append(f'\t(wire\n\t\t(pts (xy {stub[0] * G:.2f} {stub[1] * G:.2f}) (xy {c[0] * G:.2f} {c[1] * G:.2f}))\n'
                                 f'\t\t(stroke (width 0) (type default))\n\t\t(uuid "{UID}-0000-4000-8000-{n:012x}")\n\t)\n')
                    n += 1
                drawn.append(label(name, c, d, n))
                placed_text |= box
                break
        else:
            failed.append(f"{name} ({', '.join(f'{r}.{p}' for r, p in pins[:3])})")
    i = text.rindex("\t(sheet_instances")
    text = text[:i] + "".join(drawn) + text[i:]
    print(f"{sum(1 for x in drawn if x.startswith(chr(9) + '(label'))} labels on {len({k[0] for k in islands})} nets" + (f"; NO ROOM for {len(failed)}: {'; '.join(failed)}" if failed else ""))
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
