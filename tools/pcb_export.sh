#!/bin/sh
# Phase 8: every output for the JLC order and the bench, from the saved board, schematic and panel. Gerber and drill
# settings per JLC's KiCad guide (kicad-build-procedure.md 8.1). Run tools/pcb_panel.sh first.
# Usage (from the repository root): sh tools/pcb_export.sh
set -e
K="C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe"
PY="C:/Users/jakep/.kicad-mcp/venv/Scripts/python.exe"
P=kicad/rev-a/panel/IphoneFM-panel.kicad_pcb
O=kicad/rev-a/output/jlc
rm -rf "$O" && mkdir -p "$O/gerbers"
"$K" pcb export gerbers -l "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" \
  --subtract-soldermask --check-zones -o "$O/gerbers/" "$P"
"$K" pcb export drill --format excellon --drill-origin absolute --excellon-units mm --excellon-zeros-format decimal \
  --excellon-oval-format alternate --excellon-separate-th --generate-map --map-format pdf -o "$O/gerbers/" "$P"
"$K" sch export bom --fields 'Value,Reference,Footprint,LCSC,${QUANTITY}' \
  --labels 'Comment,Designator,Footprint,LCSC Part #,Qty' --group-by 'LCSC,Value,Footprint' --ref-range-delimiter '' \
  --exclude-dnp -o "$O/IphoneFM-RevA-BOM.csv" kicad/rev-a/IphoneFM.kicad_sch
"$K" pcb export pos --format csv --units mm --side both -o "$O/panel-positions.csv" "$P"
"$PY" tools/jlc_outputs.py "$O/panel-positions.csv" "$O"
rm "$O/panel-positions.csv"
mkdir -p kicad/rev-a/output/assembly
"$PY" tools/pcb_assembly.py kicad/rev-a/output/assembly/IphoneFM-RevA-assembly.pdf
