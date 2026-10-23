"""Phase 3 board setup on kicad/rev-a/IphoneFM.kicad_pcb, from kicad/rev-a/fab-rules.md. Rewrites its own sections on
every run, so it can be re-run after any change to the rules.
- Step 3.1: the layer stack-up, JLC's JLC0216A from their impedance calculator (fab-rules.md, 50 ohm section): 0.030 mm
  copper, 1.43 mm FR-4 core, 0.030 mm copper; core Dk 4.6 and solder mask Dk 3.8, 0.6 mil (0.015 mm) over copper, from
  JLC's impedance stack-up page (jlcpcb.com/impedance, read 2026-10-23). The sum, about 1.52 mm, is inside JLC's
  +-10% on the 1.6 mm board we order. No surface finish: that is chosen with the order. And the title block, the same
  as the schematic's.
Close KiCad's PCB editor (or don't save from it) while this runs.
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


def main():
    text = open(PCB, encoding="utf-8").read()
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
