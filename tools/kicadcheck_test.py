"""Self-test for kicadcheck.py, runnable before any KiCad work exists.
1. Builds KiCad-format files (schematic netlist, BOM, board) from netlist.json and the Rev A placement, which must pass every check.
2. Breaks them one way at a time (a missing pin, a short, an open, a wrong code, a moved part...), each of which must fail.
3. If KiCad's demo projects are installed, reads a real exported netlist and board (StickHub) and checks they agree.
Usage: python tools/kicadcheck_test.py"""
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicadcheck as kc  # noqa: E402

doc, by_ref = kc.read_reference()
PLAN = kc.read_layout("A")
OFF = (100.0, 20.0)  # where the synthetic board sits in KiCad coordinates, relative to the phone-back sketch
FOOT = {"0402": "Capacitor_SMD:C_0402_1005Metric", "0603": "Capacitor_SMD:C_0603_1608Metric", "0805": "Capacitor_SMD:C_0805_2012Metric"}


def kicad_pins(ref, pin):
    """How a KiCad footprint may number a netlist.json pin (exercises kicadcheck's pin matching)"""
    p = by_ref[ref]
    if pin in ("EP", "DAP"):
        return [str(max(int(k) for k in p["pinmap"] if k.isdigit()) + 1)]
    if re.fullmatch(r"(\d+)[a-z]", pin):
        return [pin[:-1]]
    if re.fullmatch(r"[AB]\d+[AB]\d+", pin):
        return re.findall(r"[AB]\d+", pin)
    return [pin]


def model():
    """{(ref, kicad_pin): net}, with NC pins as unconnected single-pin nets"""
    pins = {}
    for r, p in by_ref.items():
        for pin, d in p["pinmap"].items():
            for k in kicad_pins(r, pin):
                pins[(r, k)] = f"unconnected-({r}-Pad{k})" if d["net"] == "NC" else "/" + d["net"]
    return pins


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_net(pins, path, lcsc=None):
    comps = []
    for r, p in by_ref.items():
        code = (lcsc or {}).get(r, p["lcsc"])
        comps.append(f'(comp (ref {q(r)}) (value {q(p["value"])}) (footprint {q(FOOT.get(p["package"], "Lib:" + p["ref"]))})'
                     f' (fields (field (name "LCSC") {q(code)}) (field (name "MPN") {q(p["mpn"])})))')
    nets = {}
    for (r, k), n in pins.items():
        nets.setdefault(n, []).append(f"(node (ref {q(r)}) (pin {q(k)}))")
    body = "".join(f"(net (code {q(i + 1)}) (name {q(n)}) {' '.join(v)})" for i, (n, v) in enumerate(nets.items()))
    open(path, "w", encoding="utf-8").write(f'(export (version "E") (components {" ".join(comps)}) (nets {body}))')


def positions():
    """Board positions: the sketch for major parts; each other part 1.5 mm from the part it belongs next to"""
    pos = {r: (x + OFF[0], y + OFF[1]) for r, (x, y, _) in PLAN.items()}
    for r, p in by_ref.items():
        if r in pos:
            continue
        target = p.get("local_to", "U7").split(".")[0]
        tx, ty = pos.get(target, pos["U7"])
        pos[r] = (tx + 1.5, ty)
    return pos


def write_pcb(pins, path, pos, layer=None):
    fps = []
    for r, (x, y) in pos.items():
        p = by_ref[r]
        pads = " ".join(f"(pad {q(k)} smd rect (at 0 0) (size 0.5 0.5) (layers \"F.Cu\") (net {i} {q(n)}))"
                        for i, ((rr, k), n) in enumerate(pins.items()) if rr == r)
        fps.append(f'(footprint {q(FOOT.get(p["package"], "Lib:" + r))} (layer {q((layer or {}).get(r, "F.Cu"))}) (at {x:.3f} {y:.3f} 0)'
                   f' (property "Reference" {q(r)}) (property "LCSC" {q(p["lcsc"])}) (property "MPN" {q(p["mpn"])}) {pads})')
    x0, y0, x1, y1 = 12.70 + OFF[0], 59.56 + OFF[1], 59.15 + OFF[0], 130.96 + OFF[1]
    edge = f'(gr_rect (start {x0} {y0}) (end {x1} {y1}) (layer "Edge.Cuts"))'
    open(path, "w", encoding="utf-8").write(f'(kicad_pcb (version 20250000) {" ".join(fps)} {edge})')


def write_bom(path, drop=()):
    rows = ["Reference,Value,Footprint,LCSC,MPN"]
    groups = {}
    for r, p in by_ref.items():
        if p["mpn"] and r not in drop:
            groups.setdefault((p["mpn"], p["lcsc"], p["value"], FOOT.get(p["package"], "")), []).append(r)
    for (mpn, lcsc, value, foot), refs in groups.items():
        rows.append(f'"{",".join(refs)}","{value}","{foot}","{lcsc}","{mpn}"')
    open(path, "w", encoding="utf-8").write("\n".join(rows))


def run(args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = kc.main(args)
    return code, buf.getvalue()


def main():
    tmp = tempfile.mkdtemp(prefix="kicadcheck_")
    net, pcb, bom = (os.path.join(tmp, n) for n in ("t.net", "t.kicad_pcb", "t.csv"))
    pins, pos = model(), positions()
    results = []

    def expect(name, should_fail, args, pattern=None):
        code, text = run(args)
        failed = code != 0
        hit = pattern is None or re.search(pattern, text) is not None
        ok = failed == should_fail and hit
        results.append(ok)
        print(("ok    " if ok else "WRONG ") + name + ("" if ok else "\n" + text))

    write_net(pins, net); write_pcb(pins, pcb, pos); write_bom(bom)
    expect("clean files pass every check", False, ["--net", net, "--bom", bom, "--pcb", pcb])

    bad = dict(pins); del bad[("U2", "15")]
    write_net(bad, net); expect("missing pin (U2 pin 15) is caught", True, ["--net", net], r"FAIL .*pad.*U2\.15")
    bad = dict(pins); bad[("R21", "2")] = "/I2C_SCL"
    write_net(bad, net); expect("short (R21 onto I2C_SCL) is caught", True, ["--net", net], r"FAIL .*short")
    bad = dict(pins); bad[("U7", "2")] = "Net-(U7-VDD)"
    write_net(bad, net); expect("open (U7 VDD off 3V3) is caught", True, ["--net", net], r"FAIL .*open")
    bad = dict(pins); bad[("U2", "8")] = "/GND"
    write_net(bad, net); expect("a do-not-connect pin tied to GND is caught", True, ["--net", net], r"FAIL .*open are open")
    write_net(pins, net, lcsc={"C1": "C12345"}); expect("wrong JLC code is caught", True, ["--net", net], r"FAIL .*LCSC codes")
    write_bom(bom, drop=("C23",)); expect("part missing from the BOM is caught", True, ["--bom", bom], r"FAIL .*C23")
    moved = dict(pos); moved["U2"] = (pos["U2"][0] + 5, pos["U2"][1])
    write_pcb(pins, pcb, moved); expect("U2 5 mm off the sketch is caught", True, ["--pcb", pcb], r"FAIL .*U2 5\.0 mm")
    moved = dict(pos); moved["C23"] = (pos["C23"][0] + 10, pos["C23"][1])
    write_pcb(pins, pcb, moved); expect("C23 10 mm from its pin is caught", True, ["--pcb", pcb], r"FAIL .*C23 .* from U2\.21")
    write_pcb(pins, pcb, pos, layer={"R5": "B.Cu"}); expect("part on the bottom side is caught", True, ["--pcb", pcb], r"FAIL .*bottom R5")

    demo = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "KiCad", "10.0")
    cli, src = os.path.join(demo, "bin", "kicad-cli.exe"), os.path.join(demo, "share", "kicad", "demos", "stickhub")
    if os.path.exists(cli) and os.path.isdir(src):
        work = os.path.join(tmp, "stickhub"); shutil.copytree(src, work)
        out = os.path.join(work, "s.net")
        r = subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, os.path.join(work, "StickHub.kicad_sch")], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            results.append(False)
            print(f"WRONG real KiCad files: kicad-cli failed ({r.returncode}): {(r.stderr or r.stdout).strip()[:300]}")
            shutil.rmtree(tmp, ignore_errors=True)
            return 1
        parts, spins = kc.read_net(out)
        fps, _ = kc.read_pcb(os.path.join(work, "StickHub.kicad_pcb"))
        res = []
        kc.compare(None, spins, {(r, n): v for r, f in fps.items() for n, (v, _, _) in f["pads"].items()}, "StickHub", res, ref_names=False)
        ok = all(o is not False for o, _ in res) and len(parts) > 50
        results.append(ok)
        print(("ok    " if ok else "WRONG ") + f"real KiCad files (StickHub demo): exported netlist and board agree, {len(spins)} pins")
    else:
        print("skip  real KiCad files: KiCad 10 demos not found")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
