"""Builds U4's footprint (Skyworks Si4705-D60-GM, QFN-20 3 x 3 mm) from KiCad's SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm
(kept at step 2.2) with two changes from the Phase 2 review (step 2.8, the user's choice):
- the 16 side pads narrowed from 0.30 to 0.28 mm, Skyworks' width (Si4704/05-D60 Rev 1.2 Table 16, X 0.28 max);
- every pad's solder-mask opening 0.06 mm larger all round, as Skyworks asks ("non-solder mask defined... 60 um
  minimum, all the way around the pad", p32). The board's own mask expansion is 0 (fab-rules.md).
With 0.28 mm pads at 0.5 mm pitch the mask strip left between neighbouring side pads is 0.10 mm, JLC's minimum.
Writes kicad/rev-a/IphoneFM.pretty/SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm.kicad_mod; run tools/fp_silk_trim.py afterwards.
Usage: python tools/fp_u4_si4705.py"""
import os
import re

KICAD_FP = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Package_DFN_QFN.pretty\SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm.kicad_mod"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", "SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm.kicad_mod")
SIDE_W, MASK = 0.28, 0.06


def pad(m):
    blk = m.group(0)
    if m.group(1) == "":  # paste windows: unchanged
        return blk
    blk = re.sub(r"\(size 0\.9 0\.3\)", f"(size 0.9 {SIDE_W:g})", blk)  # side pads (top and bottom rows are rotated 90)
    return blk.replace("\n\t)\n", f"\n\t\t(solder_mask_margin {MASK:g})\n\t)\n")


def main():
    text = open(KICAD_FP, encoding="utf-8").read()
    text, n = re.subn(r'\t\(pad "([^"]*)" smd .*?\n\t\)\n', pad, text, flags=re.S)
    assert text.count("(size 0.9 0.28)") == 16 and text.count("(solder_mask_margin 0.06)") == 21, n
    text = re.sub(r'\(descr "([^"]*)"\)', r'(descr "\1; side pads 0.28 mm and mask 0.06 mm clear of every pad, per Skyworks Si4704/05-D60")', text, count=1)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(OUT)


if __name__ == "__main__":
    main()
