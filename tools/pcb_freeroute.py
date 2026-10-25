"""Step 5.11: autoroutes the remaining nets with Freerouting around the hand-laid, locked lines, then brings the new
tracks and vias into the board open in KiCad (one undo step, left unlocked for review).
  export   KiCad's Specctra export of the saved board (KiCad's own Python, pcbnew.ExportSpecctraDSN), then edited:
           - the MagSafe ring rule areas are dropped: KiCad exports them as keep-outs, but they only carry the
             through-hole rule (step 3.6);
           - GND keeps no pins: not routed (the Phase 6 pours join it), its vias still obstacles;
           - Clock nets get 0.2 mm to pins so they can reach 0.5 mm-pitch pins; the 0.4 mm between tracks is
             checked afterwards by IphoneFM.kicad_dru;
           - no tracks or vias on the bottom under the RF parts and lines [AN4169 p12] (RF_BOTTOM_POLYS).
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
# No bottom-layer copper under the RF parts and lines, so their ground return stays whole [AN4169 p12]. Floorplan B3:
# A, the transmit chain below U1: U2's RF half (exposed pad, RF out, loop filter side), C26, U7, the filter, U5, the
#    antenna line and J2; U2's digital (left) side stays open for the FSK and MICROWIRE hops;
# B, the 50-ohm receive line from U5 past H3's west side and up to C34, about 1.5 mm each side;
# C, U4 with its input parts (C34, L1, FB1, C35); its west edge leaves room for crossings beside U4, and its east edge
#    beside U4's digital pins room for the RCLK and RST lines that reach them on the bottom (tools/pcb_route_u4.py).
RF_BOTTOM_POLYS = [
    [(39.5, 104.5), (49.3, 104.5), (49.3, 121.3), (59.0, 121.3), (59.0, 131.0), (41.6, 131.0), (41.6, 121.0),
     (39.5, 121.0)],
    [(48.7, 121.3), (48.7, 113.4), (52.9, 109.2), (52.9, 96.0), (55.9, 96.0), (55.9, 110.4), (51.7, 114.6), (51.7, 121.3)],
    [(51.4, 83.1), (56.3, 83.1), (56.3, 90.6), (56.9, 90.6), (56.9, 98.6), (51.4, 98.6)],
]

# 3V3 may run on the bottom inside zone A in these two corridors only (the user's choice, 2026-10-25), because U7's
# supply and LE pins and C27 are boxed in on top by the RF lines, CE and the attenuator's control lines:
#   1  from a via inside the PLL capacitor column (on U2 pin 20's line to C15) south under CE to a via at C27;
#   2  from a via below U7's LE pin (16) east past U7's lower-right corner and north to a via beside C27.
# Neither passes under an RF line or RF pin (tools/pcb_route_u2.py lays both).
RF_BOTTOM_ALLOW = {"3V3": [
    [(43.95, 111.86), (42.91, 112.9), (43.55, 113.54), (44.85, 112.24), (44.85, 109.68), (43.95, 109.68)],
    [(43.54, 120.75), (44.85, 120.75), (44.85, 114.5), (43.95, 114.5), (43.95, 119.85), (43.16, 119.85),
     (42.41, 120.6), (43.05, 121.24)],
]}


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
    i = t.index('    (via "Via[0-1]_600:300_um")')
    keep = "".join(f'\n    (keepout "rf_bottom_{k}" (polygon B.Cu 0  ' + "  ".join(f"{x * 1000:.0f} {-y * 1000:.0f}" for x, y in poly + poly[:1]) + "))"
                   for k, poly in enumerate(RF_BOTTOM_POLYS))
    t = t[:i].rstrip() + keep + "\n" + t[i:]
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
