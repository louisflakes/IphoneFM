#!/bin/sh
# Phase 8: every output for the JLC order and the bench, from the saved board, schematic and panel. Gerber and drill
# settings per JLC's KiCad guide (kicad-build-procedure.md 8.1). Run tools/pcb_panel.sh first.
# Usage (from the repository root): [IPHONEFM_REV=rev-b] sh tools/pcb_export.sh
set -e
REV=${IPHONEFM_REV:-rev-a}
export IPHONEFM_REV=$REV
case $REV in rev-a) N=RevA;; rev-b) N=RevB;; esac
D=kicad/$REV
K="C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe"
PY="C:/Users/jakep/.kicad-mcp/venv/Scripts/python.exe"
P=$D/panel/IphoneFM-panel.kicad_pcb
O=$D/output/jlc
rm -rf "$O" && mkdir -p "$O/gerbers"
"$K" pcb export gerbers -l "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" \
  --subtract-soldermask --check-zones -o "$O/gerbers/" "$P"
"$K" pcb export drill --format excellon --drill-origin absolute --excellon-units mm --excellon-zeros-format decimal \
  --excellon-oval-format alternate --excellon-separate-th --generate-map --map-format pdf -o "$O/gerbers/" "$P"
"$K" sch export bom --fields 'Value,Reference,Footprint,LCSC,${QUANTITY}' \
  --labels 'Comment,Designator,Footprint,LCSC Part #,Qty' --group-by 'LCSC,Value,Footprint' --ref-range-delimiter '' \
  --exclude-dnp -o "$O/IphoneFM-$N-BOM.csv" $D/IphoneFM.kicad_sch
"$K" pcb export pos --format csv --units mm --side both -o "$O/panel-positions.csv" "$P"
"$PY" tools/jlc_outputs.py "$O/panel-positions.csv" "$O"
rm "$O/panel-positions.csv"
mkdir -p $D/output/assembly
if [ "$REV" = rev-a ]; then   # Rev A: read from the board open in KiCad, as when it was made
  "$PY" tools/pcb_assembly.py $D/output/assembly/IphoneFM-$N-assembly.pdf
else
  "$PY" tools/pcb_assembly.py $D/output/assembly/IphoneFM-$N-assembly.pdf --pcb $D/IphoneFM.kicad_pcb     --title "IphoneFM Rev ${N#Rev}"
fi
