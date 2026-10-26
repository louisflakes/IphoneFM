"""Builds J1's footprint from KiCad's USB_C_Receptacle_HRO_TYPE-C-31-M-12, which follows HRO's 2015 drawing, with the pads
and holes moved to HRO's revised recommended layout (drawing dated 2020-12-08,
docs/datasheets/analog-fm/J1_HRO_TYPE-C-31-M-12.pdf). Outline, courtyard and 3D model are KiCad's.
Writes kicad/rev-a/IphoneFM.pretty/USB_C_Receptacle_HRO_TYPE-C-31-M-12_2020.kicad_mod.
Usage: python tools/fp_j1_hro2020.py"""
import os
import re

KICAD_FP = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Connector_USB.pretty\USB_C_Receptacle_HRO_TYPE-C-31-M-12.kicad_mod"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", "USB_C_Receptacle_HRO_TYPE-C-31-M-12_2020.kicad_mod")
NAME = "USB_C_Receptacle_HRO_TYPE-C-31-M-12_2020"

PEG_Y = -2.6  # the two locating-peg holes stay where KiCad has them: 5.78 mm apart on this line
SIGNAL_Y = PEG_Y - (0.50 + 1.64) / 2  # pads run from 0.50 to 1.64 mm behind the peg holes: 1.14 mm long
SIGNAL_LEN = 1.14
WIDE_X = {"A1": -3.20, "B12": -3.20, "A4": -2.40, "B9": -2.40, "B4": 2.40, "A9": 2.40, "B1": 3.20, "A12": 3.20}
FRONT_SLOT_Y = PEG_Y - 0.50  # front shell slots on the pads' front edge line
REAR_SLOT_Y = FRONT_SLOT_Y + 4.18
SLOT_X = 8.65 / 2


def pad(m):
    blk = m.group(0)
    num, kind = m.group(1), m.group(2)
    x, y = (float(v) for v in re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", blk).groups())
    if kind == "np_thru_hole":  # locating pegs: Ø0.60 mm holes
        blk = re.sub(r"\(size [\d.]+ [\d.]+\)", "(size 0.6 0.6)", blk)
        return re.sub(r"\(drill [\d.]+\)", "(drill 0.6)", blk)
    if kind == "smd":  # signal pads: 1.14 mm long; the four wide pads 0.05 mm further in
        x = WIDE_X.get(num, x)
        blk = re.sub(r"\(at [-\d.]+ [-\d.]+\)", f"(at {x:g} {SIGNAL_Y:g})", blk)
        return re.sub(r"\(size ([\d.]+) [\d.]+\)", lambda q: f"(size {q.group(1)} {SIGNAL_LEN:g})", blk)
    # shell legs: front slots 0.6 x 1.7 mm hole, rear 0.6 x 1.4, as HRO draws them. HRO's pads (0.9 x 2.0 and 0.9 x 1.7)
    # leave a 0.15 mm copper ring, under JLC's 0.18 mm minimum, so each pad is 0.2 mm bigger both ways: a 0.25 mm ring,
    # our rule (fab-rules.md; step 3.2, the user's choice)
    front = y < 0
    sy, (h, d) = (FRONT_SLOT_Y, (2.2, 1.7)) if front else (REAR_SLOT_Y, (1.9, 1.4))
    blk = re.sub(r"\(at [-\d.]+ [-\d.]+\)", f"(at {SLOT_X if x > 0 else -SLOT_X:g} {sy:g})", blk)
    blk = re.sub(r"\(size [\d.]+ [\d.]+\)", f"(size 1.1 {h:g})", blk)
    return re.sub(r"\(drill oval [\d.]+ [\d.]+\)", f"(drill oval 0.6 {d:g})", blk)


def main():
    text = open(KICAD_FP, encoding="utf-8").read()
    text = text.replace('(footprint "USB_C_Receptacle_HRO_TYPE-C-31-M-12"', f'(footprint "{NAME}"', 1)
    text = re.sub(r'\(descr "[^"]*"\)', '(descr "USB Type-C receptacle for USB 2.0 and PD, HRO TYPE-C-31-M-12; pads and holes per HRO\'s recommended PCB layout, drawing dated 2020-12-08 (KiCad\'s footprint follows the 2015 drawing)")', text, count=1)
    text = re.sub(r'(\(property "Value" )"[^"]*"', rf'\1"{NAME}"', text, count=1)
    text = re.sub(r'\t\(pad "([^"]*)" (smd|thru_hole|np_thru_hole) .*?\n\t\)\n', pad, text, flags=re.S)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(OUT)


if __name__ == "__main__":
    main()
