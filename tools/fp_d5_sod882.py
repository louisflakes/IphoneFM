"""Builds D5's footprint (Semtech RClamp0521PA, SLP1006P2) from KiCad's D_SOD-882 with the solder paste made 1:1 with
the two pads (step 2.5, HHG p96, p113): KiCad's copy, following Nexperia's SOD882 drawing, prints a separate 0.3 x 0.6 mm
paste window inside each 0.4 x 0.7 mm pad and shrinks it a further 0.05 mm, about 36% of the pad. Semtech gives no
stencil for this part, and TI prints 1:1 on the same-size DPY package (D3, D4).
Writes kicad/rev-a/IphoneFM.pretty/D_SOD-882.kicad_mod; run tools/fp_silk_trim.py afterwards.
Usage: python tools/fp_d5_sod882.py"""
import os
import re

KICAD_FP = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Diode_SMD.pretty\D_SOD-882.kicad_mod"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", "D_SOD-882.kicad_mod")


def main():
    text = open(KICAD_FP, encoding="utf-8").read()
    text, n = re.subn(r'\t\(pad "" smd \S+\n.*?\n\t\)\n', "", text, flags=re.S)  # the separate paste windows
    assert n == 2, n
    text = text.replace('(layers "F.Cu" "F.Mask")', '(layers "F.Cu" "F.Mask" "F.Paste")')
    text, n = re.subn(r'\n\t\t\(solder_paste_margin [-\d.]+\)', "", text)
    assert n == 2, n
    text = re.sub(r'\(descr "([^"]*)"\)', r'(descr "\1; solder paste 1:1 with the pads")', text, count=1)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(OUT)


if __name__ == "__main__":
    main()
