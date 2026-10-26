"""Phase 8: the files for the JLC order, from the schematic and the panel (tools/pcb_panel.sh). Run by tools/pcb_export.sh.
  BOM  kicad-cli's schematic BOM grouped by LCSC code, in JLC's columns (Comment, Designator, Footprint, LCSC Part #).
       Comments are rewritten in ASCII (u, Ohm, x): JLC's reader showed µ, Ω and × as mojibake.
  CPL  kicad-cli's position file of the panel, cut to the ordered parts (fiducials and mounting holes left out), in
       JLC's columns (Designator, Mid X, Mid Y, Layer, Rotation); checked one for one against the BOM. JLC places each
       part with its own (EasyEDA) footprint, whose zero rotation and origin can differ from ours: JLC_FIX holds, per
       LCSC code, the turn and the origin shift that land JLC's footprint on ours. Each was found by fitting JLC's pads
       to ours pin by pin (2026-10-26, from the footprints JLC's placement viewer loads); D1 and J2 by hand, see there.
  ZIP  the Gerbers and drill files, without the drill maps (those are for people).
Usage: python tools/jlc_outputs.py POS.csv OUT_DIR"""
import csv
import glob
import os
import sys
import math
import zipfile

# LCSC code: (turn in degrees, counter-clockwise; x, y shift in mm in our footprint's frame, y down). Ours = turn(JLC) + shift.
JLC_FIX = {
    "C440388": (270, 0, 0),        # U2 WQFN-36
    "C51118": (270, 0, 0),         # U3 SOT-23-5
    "C470893": (180, 0, 0),        # U5 SC-70-6
    "C7519": (270, 0, 0),          # U6 SOT-23-6
    "C470929": (270, 0, 0),        # U7 VQFN-24
    "C221994": (270, 0, 0),        # SW3 DIP switch
    "C431540": (0, 0, -0.25),      # SW1: JLC's pin row sits 0.25 mm lower in its footprint
    "C165948": (0, 0, -1.196),     # J1: JLC's origin is 1.2 mm behind ours
    "C470766": (0, 0, 2.4),        # RV1-RV3: JLC's origin is 2.4 mm toward the pins
    # D1: JLC numbers the LED's pads 1 BR, 2 TR, 3 TL, 4 BL; the datasheet (p8) and ours 1 TL, 2 BL, 3 TR, 4 BR, mark on
    # the 1-2 side. A half turn puts JLC's pin 1 and 2 (and the mark) on ours; its 3/4 labels are mirrored, the part isn't.
    "C965840": (180, 0, 0),
    # J2: square legs fit any quarter turn; JLC's model has the barrel toward +x, ours toward -y (seen in JLC's preview)
    "C496551": (90, 0, 0),
}
ASCII = {"µ": "u", "Ω": "Ohm", "×": "x"}

pos_csv, out = sys.argv[1], sys.argv[2]
bom_path = os.path.join(out, "IphoneFM-RevA-BOM.csv")
bom = list(csv.DictReader(open(bom_path, encoding="utf-8")))
for row in bom:
    for a, b in ASCII.items():
        row["Comment"] = row["Comment"].replace(a, b)
with open(bom_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(bom[0]))
    w.writeheader()
    w.writerows(bom)
lcsc = {r: row["LCSC Part #"] for row in bom for r in row["Designator"].split(",")}
refs = set(lcsc)
pos = [p for p in csv.DictReader(open(pos_csv, encoding="utf-8")) if p["Ref"] in refs]
missing = refs - {p["Ref"] for p in pos}
if missing:
    sys.exit(f"ordered but not placed: {sorted(missing)}")


def order(p):
    stem = p["Ref"].rstrip("0123456789")
    return stem, int(p["Ref"][len(stem):])


with open(os.path.join(out, "IphoneFM-RevA-CPL.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for p in sorted(pos, key=order):
        rot = float(p["Rot"])
        turn, sx, sy = JLC_FIX.get(lcsc[p["Ref"]], (0, 0, 0))
        a = math.radians(rot)                       # the shift turned with the part (y down, counter-clockwise)
        dx = sx * math.cos(a) + sy * math.sin(a)
        dy = -sx * math.sin(a) + sy * math.cos(a)
        x, y = float(p["PosX"]) + dx, float(p["PosY"]) - dy        # the position file's y points up
        w.writerow([p["Ref"], f"{x:.4f}mm", f"{y:.4f}mm", "Top" if p["Side"] == "top" else "Bottom",
                    f"{(rot + turn) % 360:g}"])
with zipfile.ZipFile(os.path.join(out, "IphoneFM-RevA-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(glob.glob(os.path.join(out, "gerbers", "*"))):
        if not p.endswith(".pdf"):
            z.write(p, os.path.basename(p))
print(f"BOM {len(bom)} lines, CPL {len(pos)} parts (matches the BOM), zip written")
