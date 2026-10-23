"""Phase 3 board setup on kicad/rev-a/IphoneFM.kicad_pcb, from kicad/rev-a/fab-rules.md. Rewrites its own sections on
every run, so it can be re-run after any change to the rules.
- Step 3.1: the layer stack-up, JLC's JLC0216A from their impedance calculator (fab-rules.md, 50 ohm section): 0.030 mm
  copper, 1.43 mm FR-4 core, 0.030 mm copper; core Dk 4.6 and solder mask Dk 3.8, 0.6 mil (0.015 mm) over copper, from
  JLC's impedance stack-up page (jlcpcb.com/impedance, read 2026-10-23). The sum, about 1.52 mm, is inside JLC's
  +-10% on the 1.6 mm board we order. No surface finish: that is chosen with the order. And the title block, the same
  as the schematic's.
- Step 3.2: the design rules from fab-rules.md's "Our design rules": Board Setup's constraints and defaults in
  IphoneFM.kicad_pro, the 0.10 mm solder-mask web in the board's setup, and the two rules Board Setup has no field
  for (0.25 mm ring on plated holes, 0.3 mm courtyard gap) in IphoneFM.kicad_dru.
Close KiCad (or don't save from it) while this runs; reopen the project to see the result.
Usage (from the repository root): python tools/pcb_setup.py"""
import re

PCB = "kicad/rev-a/IphoneFM.kicad_pcb"
SCH = "kicad/rev-a/IphoneFM.kicad_sch"

STACKUP = """\t\t(stackup
\t\t\t(layer "F.SilkS"
\t\t\t\t(type "Top Silk Screen")
\t\t\t)
\t\t\t(layer "F.Paste"
\t\t\t\t(type "Top Solder Paste")
\t\t\t)
\t\t\t(layer "F.Mask"
\t\t\t\t(type "Top Solder Mask")
\t\t\t\t(thickness 0.015)
\t\t\t\t(epsilon_r 3.8)
\t\t\t)
\t\t\t(layer "F.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.03)
\t\t\t)
\t\t\t(layer "dielectric 1"
\t\t\t\t(type "core")
\t\t\t\t(thickness 1.43)
\t\t\t\t(material "FR4")
\t\t\t\t(epsilon_r 4.6)
\t\t\t\t(loss_tangent 0.02)
\t\t\t)
\t\t\t(layer "B.Cu"
\t\t\t\t(type "copper")
\t\t\t\t(thickness 0.03)
\t\t\t)
\t\t\t(layer "B.Mask"
\t\t\t\t(type "Bottom Solder Mask")
\t\t\t\t(thickness 0.015)
\t\t\t\t(epsilon_r 3.8)
\t\t\t)
\t\t\t(layer "B.Paste"
\t\t\t\t(type "Bottom Solder Paste")
\t\t\t)
\t\t\t(layer "B.SilkS"
\t\t\t\t(type "Bottom Silk Screen")
\t\t\t)
\t\t\t(copper_finish "None")
\t\t\t(dielectric_constraints no)
\t\t)
"""


PRO = "kicad/rev-a/IphoneFM.kicad_pro"
DRU = "kicad/rev-a/IphoneFM.kicad_dru"

# Step 3.2: fab-rules.md, "Our design rules (step 0.5)"
RULES = {
    "min_clearance": 0.20,             # copper to copper
    "min_track_width": 0.20,           # signals
    "min_via_diameter": 0.60,          # via pad
    "min_through_hole_diameter": 0.30, # smallest drill (vias)
    "min_via_annular_width": 0.15,     # 0.60 pad on a 0.30 drill; plated pads get 0.25 in IphoneFM.kicad_dru
    "min_hole_to_hole": 0.50,
    "min_hole_clearance": 0.30,        # hole to copper
    "min_copper_edge_clearance": 0.50,
    "min_silk_clearance": 0.20,        # silkscreen to pad
    "min_text_height": 1.0,
    "min_text_thickness": 0.15,
    "solder_mask_to_copper_clearance": 0.0,
}
DEFAULTS = {"silk_line_width": 0.25, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15}
CUSTOM = """(version 1)
# Step 3.2 rules KiCad's Board Setup has no field for (kicad/rev-a/fab-rules.md)
(rule "Plated hole annular ring 0.25 mm"
\t(condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'")
\t(constraint annular_width (min 0.25mm)))
(rule "Courtyard gap 0.3 mm"
\t(constraint courtyard_clearance (min 0.3mm)))
"""


def design_rules():
    import json
    pro = json.load(open(PRO, encoding="utf-8"))
    ds = pro["board"]["design_settings"]
    ds["rules"].update(RULES)
    ds["defaults"].update(DEFAULTS)
    ds["track_widths"] = [0.0, 0.20, 0.40, 0.92]  # first entry is KiCad's "use net class" slot
    ds["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.60, "drill": 0.30}]
    open(PRO, "w", encoding="utf-8", newline="\n").write(json.dumps(pro, indent=2) + "\n")
    open(DRU, "w", encoding="utf-8", newline="\n").write(CUSTOM)


def main():
    design_rules()
    text = open(PCB, encoding="utf-8").read()
    # mask: opened 1:1 (KiCad adds nothing), 0.10 mm minimum web; webs inside a footprint may be left out, as on U4 (step 2.8)
    text = re.sub(r"\t\t\(solder_mask_min_width [\d.]+\)\n", "", text)
    text = text.replace("\t\t(pad_to_mask_clearance 0)\n", "\t\t(pad_to_mask_clearance 0)\n\t\t(solder_mask_min_width 0.1)\n", 1)
    text = text.replace("(allow_soldermask_bridges_in_footprints no)", "(allow_soldermask_bridges_in_footprints yes)")
    # step 3.1: stack-up, first inside (setup)
    text = re.sub(r"\t\t\(stackup\n.*?\n\t\t\)\n", "", text, flags=re.S)
    text = text.replace("\t(setup\n", "\t(setup\n" + STACKUP, 1)
    total = sum(float(t) for t in re.findall(r"\(thickness ([\d.]+)\)", STACKUP))  # KiCad's board thickness is the stack's sum
    text = re.sub(r"(\t\(general\n\t\t\(thickness )[\d.]+\)", lambda m: f"{m.group(1)}{total:g})", text, count=1)
    # title block, copied from the schematic
    tb = re.search(r"\t\(title_block\n.*?\n\t\)\n", open(SCH, encoding="utf-8").read(), re.S).group(0)
    text = re.sub(r"\t\(title_block\n.*?\n\t\)\n", "", text, flags=re.S)
    text = re.sub(r'(\t\(paper "[^"]*"\)\n)', lambda m: m.group(1) + tb, text, count=1)
    open(PCB, "w", encoding="utf-8", newline="\n").write(text)
    print(PCB)


if __name__ == "__main__":
    main()
