"""Builds U2's footprint (LMX2571, TI WQFN-36 NJK0036A) from KiCad's QFN-36-1EP_6x6mm_P0.5mm_EP4.1x4.1mm, with the pads
moved to TI's recommended land pattern (SNAS654A p61): 36 pads 0.25 x 0.6 mm at 0.5 mm pitch, centres on a 5.8 mm span,
and a 4.6 x 4.6 mm centre pad (37). TI gives no stencil, so the centre pad's paste is KiCad's own 4 x 4 windows for a
4.6 mm pad (from QFN-40-1EP_6x6mm_P0.5mm_EP4.6x4.6mm). Outline, courtyard and 3D model are KiCad's QFN-36.
Writes kicad/rev-a/IphoneFM.pretty/TI_NJK0036A_WQFN-36-1EP_6x6mm_P0.5mm_EP4.6x4.6mm.kicad_mod.
Usage: python tools/fp_u2_ti_njk.py"""
import os
import re

LIB = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Package_DFN_QFN.pretty"
KICAD_FP = os.path.join(LIB, "QFN-36-1EP_6x6mm_P0.5mm_EP4.1x4.1mm.kicad_mod")
PASTE_FP = os.path.join(LIB, "QFN-40-1EP_6x6mm_P0.5mm_EP4.6x4.6mm.kicad_mod")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "TI_NJK0036A_WQFN-36-1EP_6x6mm_P0.5mm_EP4.6x4.6mm"
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", NAME + ".kicad_mod")

ROW = 5.8 / 2  # pad centres 2.9 mm from the middle: pads run 2.6 to 3.2 mm out
PAD_LEN, PAD_W = 0.6, 0.25
EP = 4.6
PAD_RE = r'\t\(pad "([^"]*)" smd \S+\n.*?\n\t\)\n'


def pad(m):
    blk, num = m.group(0), m.group(1)
    if num == "":  # KiCad's paste windows for its 4.1 mm pad: replaced below
        return ""
    if num == "37":
        return re.sub(r"\(size [\d.]+ [\d.]+\)", f"(size {EP:g} {EP:g})", blk)
    x, y = (float(v) for v in re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", blk).groups())
    if abs(x) > abs(y):  # left and right rows
        x, w, h = ROW if x > 0 else -ROW, PAD_LEN, PAD_W
    else:  # top and bottom rows
        y, w, h = ROW if y > 0 else -ROW, PAD_W, PAD_LEN
    blk = blk.replace(" smd roundrect", " smd rect")
    blk = re.sub(r"\n\t\t\(roundrect_rratio [\d.]+\)", "", blk)
    blk = re.sub(r"\(at [-\d.]+ [-\d.]+\)", f"(at {x:g} {y:g})", blk)
    return re.sub(r"\(size [\d.]+ [\d.]+\)", f"(size {w:g} {h:g})", blk)


def main():
    text = open(KICAD_FP, encoding="utf-8").read()
    paste = "".join(m.group(0) for m in re.finditer(PAD_RE, open(PASTE_FP, encoding="utf-8").read(), flags=re.S)
                    if m.group(1) == "")
    text = text.replace('(footprint "QFN-36-1EP_6x6mm_P0.5mm_EP4.1x4.1mm"', f'(footprint "{NAME}"', 1)
    text = re.sub(r'\(descr "[^"]*"\)', '(descr "TI WQFN-36 NJK0036A, 6 x 6 mm; pads per TI\'s recommended land pattern (SNAS654A p61); centre-pad paste per KiCad\'s 4.6 mm pattern")', text, count=1)
    text = re.sub(r'(\(property "Value" )"[^"]*"', rf'\1"{NAME}"', text, count=1)
    text = re.sub(PAD_RE, pad, text, flags=re.S)
    text = text.replace('\t(pad "37"', paste + '\t(pad "37"', 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(OUT)


if __name__ == "__main__":
    main()
