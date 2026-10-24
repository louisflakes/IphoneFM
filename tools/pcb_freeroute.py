"""Step 5.11: autoroutes the remaining nets with Freerouting around the hand-laid, locked lines, then brings the new
tracks and vias into the board open in KiCad (one undo step, left unlocked for review).
  export   KiCad's Specctra export of the saved board (KiCad's own Python, pcbnew.ExportSpecctraDSN), then edited:
           - the MagSafe ring rule areas are dropped: KiCad exports them as keep-outs, but they only carry the
             through-hole rule (step 3.6);
           - GND keeps no pins: not routed (the Phase 6 pours join it), its vias still obstacles;
           - Clock nets get 0.2 mm to pins so they can reach 0.5 mm-pitch pins; the 0.4 mm between tracks is
             checked afterwards by IphoneFM.kicad_dru;
           - no tracks or vias on the bottom under the RF section [AN4169 p12] (RF_BOTTOM).
  route    Freerouting v2.5.0 (the official Windows release, unpacked in ~/.freerouting/2.5.0-full), up to N passes.
  import   pcbnew.ImportSpecctraSES on a copy, then every track and via there that the live board lacks is added.
Usage (from the repository root, board saved and open in KiCad):
  python tools/pcb_freeroute.py export DIR | route DIR [passes] | import DIR [--dry-run]"""
import os
import re
import subprocess
import sys

KICAD_PY = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\bin\python.exe"
FREEROUTING = os.path.expanduser(r"~\.freerouting\2.5.0-full\freerouting\freerouting.exe")
# U2's RF half (its exposed pad, RF out, loop filter side), the transmit line with about 1.5 mm each side, U7, U4 and its
# front end, and the switch, filter and antenna corner. U2's digital (left) side and the strip beside U1 stay open.
RF_BOTTOM = [(41.0, 70.0), (52.0, 70.0), (52.0, 86.6), (51.3, 86.6), (51.3, 106.0), (53.6, 106.0), (53.6, 119.0),
             (58.7, 119.0), (58.7, 131.0), (41.6, 131.0), (41.6, 106.5), (43.3, 106.5), (43.3, 86.6), (41.0, 86.6),
             (41.0, 70.0)]  # x 41.6 below U7: about 0.9 mm clear of the transmit line, leaving RF_MODE a way past J1


def export(d):
    for f in ("IphoneFM.kicad_pcb", "IphoneFM.kicad_pro", "IphoneFM.kicad_dru"):
        open(os.path.join(d, f), "wb").write(open(os.path.join("kicad", "rev-a", f), "rb").read())
    pcb, dsn = os.path.join(d, "IphoneFM.kicad_pcb"), os.path.join(d, "IphoneFM.dsn")
    subprocess.run([KICAD_PY, "-c", f"import pcbnew; b = pcbnew.LoadBoard(r'{pcb}'); assert pcbnew.ExportSpecctraDSN(b, r'{dsn}')"], check=True)
    t = open(dsn, encoding="utf-8").read()
    t = re.sub(r'\n    \(keepout "" \(polygon [FB]\.Cu 0 [^()]*\)\)', "", t)
    # GND stays defined with no pins: its vias and stubs stay obstacles, and nothing asks to be joined
    t = re.sub(r'\n    \(net GND\n(?:      [^\n]*\n)*?    \)', "\n    (net GND\n      (pins)\n    )", t)
    t = t.replace(' GND "unconnected-(J1-SBU1-PadA8)"', ' "unconnected-(J1-SBU1-PadA8)"')
    t = t.replace("      (rule\n        (width 200)\n        (clearance 400)\n      )", "      (rule\n        (width 200)\n        (clearance 200)\n      )")
    coords = "  ".join(f"{x * 1000:.0f} {-y * 1000:.0f}" for x, y in RF_BOTTOM)
    i = t.index('    (via "Via[0-1]_600:300_um")')
    t = t[:i].rstrip() + f'\n    (keepout "rf_bottom" (polygon B.Cu 0  {coords}))\n' + t[i:]
    open(os.path.join(d, "IphoneFM_fr.dsn"), "w", encoding="utf-8").write(t)
    print("wrote", os.path.join(d, "IphoneFM_fr.dsn"))


def route(d, passes):
    # the full release's launcher: the native command-line build crashes snapshotting the board (v2.5.0)
    subprocess.run([FREEROUTING, "-de", "IphoneFM_fr.dsn", "-do", "IphoneFM_fr.ses", "-mp", str(passes),
                    "--gui.enabled=false"], cwd=d, check=True)


def import_(d, dry):
    pcb, ses, out = (os.path.join(d, f) for f in ("IphoneFM.kicad_pcb", "IphoneFM_fr.ses", "IphoneFM_routed.kicad_pcb"))
    subprocess.run([KICAD_PY, "-c", f"import pcbnew; b = pcbnew.LoadBoard(r'{pcb}'); assert pcbnew.ImportSpecctraSES(b, r'{ses}'); b.Save(r'{out}')"], check=True)
    sys.path.insert(0, "tools")
    from kicadcheck import sexpr, kids, kid
    routed = sexpr(open(out, encoding="utf-8").read())
    from kipy import KiCad
    from kipy.board_types import Track, Via
    from kipy.geometry import Vector2
    from kipy.proto.board.board_types_pb2 import BoardLayer
    board = KiCad().get_board()
    key_t = lambda net, l, a, b: (net, l, *sorted([tuple(round(v, 3) for v in a), tuple(round(v, 3) for v in b)]))
    have_t = {key_t(t.net.name, "F.Cu" if t.layer == BoardLayer.BL_F_Cu else "B.Cu", (t.start.x / 1e6, t.start.y / 1e6), (t.end.x / 1e6, t.end.y / 1e6)) for t in board.get_tracks()}
    have_v = {(v.net.name, round(v.position.x / 1e6, 3), round(v.position.y / 1e6, 3)) for v in board.get_vias()}
    nets = {n.name: n for n in board.get_nets()}
    items, nt, nv = [], 0, 0
    for s in kids(routed, "segment"):
        a = tuple(float(v) for v in kid(s, "start")[1:3])
        b = tuple(float(v) for v in kid(s, "end")[1:3])
        net, layer = kid(s, "net")[-1], kid(s, "layer")[1]
        if key_t(net, layer, a, b) in have_t or net not in nets:
            continue
        t = Track()
        t.start, t.end = Vector2.from_xy(round(a[0] * 1e6), round(a[1] * 1e6)), Vector2.from_xy(round(b[0] * 1e6), round(b[1] * 1e6))
        t.width = round(float(kid(s, "width")[1]) * 1e6)
        t.layer = BoardLayer.BL_F_Cu if layer == "F.Cu" else BoardLayer.BL_B_Cu
        t.net = nets[net]
        items.append(t)
        nt += 1
    for v in kids(routed, "via"):
        x, y = (float(c) for c in kid(v, "at")[1:3])
        net = kid(v, "net")[-1]
        if (net, round(x, 3), round(y, 3)) in have_v or net not in nets:
            continue
        via = Via()
        via.position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
        via.diameter = round(float(kid(v, "size")[1]) * 1e6)
        via.drill_diameter = round(float(kid(v, "drill")[1]) * 1e6)
        via.net = nets[net]
        items.append(via)
        nv += 1
    print(f"{nt} new tracks, {nv} new vias")
    if dry:
        return
    c = board.begin_commit()
    board.create_items(items)
    board.push_commit(c, "Step 5.11: Freerouting")


if __name__ == "__main__":
    cmd, d = sys.argv[1], sys.argv[2]
    {"export": lambda: export(d), "route": lambda: route(d, int(sys.argv[3]) if len(sys.argv) > 3 else 40),
     "import": lambda: import_(d, "--dry-run" in sys.argv)}[cmd]()
