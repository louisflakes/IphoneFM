"""Phase 5: runs KiCad's DRC on the saved board (kicad-cli) and prints the copper findings, leaving out the ones
expected while routing is under way (unconnected items and dangling vias before the pours) and the silkscreen
findings that Phase 7 tidies. Save the board in KiCad first.
Usage (from the repository root): python tools/pcb_drc.py [--all]"""
import collections
import json
import os
import subprocess
import sys
import tempfile

CLI = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
BOARD = "kicad/rev-a/IphoneFM.kicad_pcb"
LATER = {"unconnected_items", "via_dangling", "track_dangling", "silk_overlap", "silk_over_copper", "silk_edge_clearance",
         "lib_footprint_mismatch"}  # the last: 3D model links dropped by API turns; not needed for fabrication


def main():
    out = os.path.join(tempfile.gettempdir(), "iphonefm-drc.json")
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-error", "--severity-warning", "-o", out, BOARD],
                   capture_output=True)
    v = json.load(open(out))["violations"]
    print(dict(collections.Counter(x["type"] for x in v)))
    for x in v:
        if x["type"] in LATER and "--all" not in sys.argv:
            continue
        items = "; ".join(f"{i['description'][:50]} @({i['pos']['x']:.2f},{i['pos']['y']:.2f})" for i in x["items"])
        print(f"{x['type']:16} {items}")


if __name__ == "__main__":
    main()
