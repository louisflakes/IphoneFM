"""Builds SW1's footprint (Shou Han MSK12C02 slide switch) from KiCad's SW_SPDT_Shouhan_MSK12C02, unchanged except that
the four mounting-tab pads are numbered 4, as Shou Han's drawing numbers them, instead of KiCad's "SH". The schematic
symbol's tab pin is 4, so this joins the tabs to its net (GND).
Writes kicad/rev-a/IphoneFM.pretty/SW_SPDT_Shouhan_MSK12C02_Tabs4.kicad_mod.
Usage: python tools/fp_sw1_msk12c02.py"""
import os
import re

KICAD_FP = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Button_Switch_SMD.pretty\SW_SPDT_Shouhan_MSK12C02.kicad_mod"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "SW_SPDT_Shouhan_MSK12C02_Tabs4"
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", NAME + ".kicad_mod")


def main():
    text = open(KICAD_FP, encoding="utf-8").read()
    text = text.replace('(footprint "SW_SPDT_Shouhan_MSK12C02"', f'(footprint "{NAME}"', 1)
    text = re.sub(r'\(descr "([^"]*)"\)', r'(descr "\1; tab pads numbered 4 as on the Shou Han drawing")', text, count=1)
    text = re.sub(r'(\(property "Value" )"[^"]*"', rf'\1"{NAME}"', text, count=1)
    text, n = re.subn(r'\(pad "SH" ', '(pad "4" ', text)
    assert n == 4, n
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(OUT)


if __name__ == "__main__":
    main()
