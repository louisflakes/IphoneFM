"""Phase 8: the files for the JLC order, from the schematic and the panel (tools/pcb_panel.sh). Run by tools/pcb_export.sh.
  BOM  kicad-cli's schematic BOM grouped by LCSC code, in JLC's columns (Comment, Designator, Footprint, LCSC Part #).
  CPL  kicad-cli's position file of the panel, cut to the ordered parts (fiducials and mounting holes left out), in
       JLC's columns (Designator, Mid X, Mid Y, Layer, Rotation); checked one for one against the BOM.
  ZIP  the Gerbers and drill files, without the drill maps (those are for people).
Usage: python tools/jlc_outputs.py POS.csv OUT_DIR"""
import csv
import glob
import os
import sys
import zipfile

pos_csv, out = sys.argv[1], sys.argv[2]
bom = list(csv.DictReader(open(os.path.join(out, "IphoneFM-RevA-BOM.csv"), encoding="utf-8")))
refs = {r for row in bom for r in row["Designator"].split(",")}
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
        w.writerow([p["Ref"], f'{float(p["PosX"]):.4f}mm', f'{float(p["PosY"]):.4f}mm',
                    "Top" if p["Side"] == "top" else "Bottom", f'{float(p["Rot"]) % 360:g}'])
with zipfile.ZipFile(os.path.join(out, "IphoneFM-RevA-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(glob.glob(os.path.join(out, "gerbers", "*"))):
        if not p.endswith(".pdf"):
            z.write(p, os.path.basename(p))
print(f"BOM {len(bom)} lines, CPL {len(pos)} parts (matches the BOM), zip written")
