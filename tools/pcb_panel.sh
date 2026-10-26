#!/bin/sh
# Step 8.3: the JLC assembly panel, one board in a frame of rails on all four edges (fab-rules.md, "What this means for
# Rev A"). Rails 6.5 mm wide (JLC: at least 5 mm, and room for fiducials 3.35 mm in); 9.5 mm gap left and right, past
# J2's 7.45 mm barrel and the wheels' 1.9 mm rims; 3 mm gap top and bottom. Tabs and fiducials from tools/kikit_tabs.py;
# mouse bites 0.5 mm holes 1.0 mm apart (JLC: unplated holes 0.5 mm, 0.45 mm between holes), centred on the board edge
# so they stay 0.25 mm clear of the copper's 0.5 mm edge margin. Nets and references keep their names.
# Usage (from the repository root, board saved): sh tools/pcb_panel.sh
KIPY="C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/bin/python.exe"
mkdir -p kicad/rev-a/panel
"$KIPY" -m kikit.ui panelize \
  --layout "grid; rows: 1; cols: 1; renamenet: {orig}; renameref: {orig}" \
  --source "auto; tolerance: 12mm" \
  --tabs "annotation; fillet: 0.5mm" \
  --cuts "mousebites; drill: 0.5mm; spacing: 1.0mm; offset: 0mm; prolong: 0mm" \
  --framing "frame; width: 6.5mm; hspace: 9.5mm; vspace: 3mm; cuts: none" \
  --post "millradius: 0.5mm" \
  --text "simple; text: IphoneFM Rev A; anchor: mt; voffset: 3.25mm; width: 1.5mm; height: 1.5mm; thickness: 0.25mm" \
  --plugin "tools/kikit_tabs.py.Tabs:-" \
  kicad/rev-a/IphoneFM.kicad_pcb kicad/rev-a/panel/IphoneFM-panel.kicad_pcb
# KiKit suffixes zone names with the board number; IphoneFM.kicad_dru finds its rule areas by name, so restore them
sed -i 's/(name "\(Clock escape\|GND bottom\|GND top\|MagSafe ring opening\|MagSafe ring\)_1")/(name "\1")/' \
  kicad/rev-a/panel/IphoneFM-panel.kicad_pcb
# the panel's own library table, pointing at the project footprints one folder up
printf '(fp_lib_table\n\t(version 7)\n\t(lib (name "IphoneFM")(type "KiCad")(uri "${KIPRJMOD}/../IphoneFM.pretty")(options "")(descr "Rev A project footprints"))\n)\n' \
  > kicad/rev-a/panel/fp-lib-table
# refill the pours round the mouse-bite holes, then check
"C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe" pcb drc --format json --severity-all \
  --refill-zones --save-board -o kicad/rev-a/panel/drc-panel.json kicad/rev-a/panel/IphoneFM-panel.kicad_pcb
