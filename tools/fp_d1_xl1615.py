"""Builds D1's footprint (XINGLIGHT XL-1615RGBC-RF, 1.6 x 1.5 mm RGB LED) from Xinglight's recommended soldering pattern
(datasheet p8): four 0.45 x 0.65 mm pads, 1.25 mm apart across (0.8 mm gap) and 0.95 mm apart up/down (0.3 mm gap).
Pads are numbered as the top view shows them: 1 (R) top left, 2 (common anode) bottom left, 3 (G) top right, 4 (B)
bottom right. KiCad has no footprint or 3D model for this package.
Writes kicad/rev-a/IphoneFM.pretty/LED_RGB_XINGLIGHT_XL-1615RGBC_1.6x1.5mm.kicad_mod.
Usage: python tools/fp_d1_xl1615.py"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "LED_RGB_XINGLIGHT_XL-1615RGBC_1.6x1.5mm"
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", NAME + ".kicad_mod")

PAD_W, PAD_H = 0.45, 0.65
X = (0.45 + 0.8) / 2  # pad centres 0.625 mm either side
Y = (0.65 + 0.3) / 2  # and 0.475 mm above and below the middle
PADS = {"1": (-X, -Y), "2": (-X, Y), "3": (X, -Y), "4": (X, Y)}
BODY_W, BODY_H = 1.6, 1.5
SILK_Y = 1.0  # silk lines 0.2 mm clear of the pads (0.14 mm after half the line width)
CRT_X, CRT_Y = 1.2, 1.15  # around the silkscreen, which sits 0.2 mm outside the pads


def line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line\n\t\t(start {x1:g} {y1:g})\n\t\t(end {x2:g} {y2:g})\n'
            f'\t\t(stroke\n\t\t\t(width {w:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t)\n')


def text(kind, value, y, layer):
    return (f'\t(property "{kind}" "{value}"\n\t\t(at 0 {y:g} 0)\n\t\t(layer "{layer}")\n'
            '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n')


def main():
    bx, by = BODY_W / 2, BODY_H / 2
    out = [f'(footprint "{NAME}"\n\t(version 20260206)\n\t(generator "fp_d1_xl1615.py")\n\t(layer "F.Cu")\n',
           '\t(descr "XINGLIGHT XL-1615RGBC-RF RGB LED, common anode, 1.6 x 1.5 mm; pads per Xinglight\'s recommended soldering pattern (datasheet p8)")\n',
           '\t(tags "LED RGB 1615")\n',
           text("Reference", "REF**", -1.8, "F.SilkS"),
           text("Value", NAME, 1.8, "F.Fab"),
           '\t(attr smd)\n',
           '\t(fp_text user "${REFERENCE}"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n'
           '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.3 0.3)\n\t\t\t\t(thickness 0.05)\n\t\t\t)\n\t\t)\n\t)\n']
    # body on the fab layer, corner cut by pin 1
    c = 0.3
    out += [line(-bx + c, -by, bx, -by, "F.Fab", 0.1), line(bx, -by, bx, by, "F.Fab", 0.1),
            line(bx, by, -bx, by, "F.Fab", 0.1), line(-bx, by, -bx, -by + c, "F.Fab", 0.1),
            line(-bx, -by + c, -bx + c, -by, "F.Fab", 0.1)]
    # silk: lines above and below, and a pin-1 mark left of pad 1
    px = X + PAD_W / 2
    out += [line(-px, -SILK_Y, px, -SILK_Y, "F.SilkS", 0.12), line(-px, SILK_Y, px, SILK_Y, "F.SilkS", 0.12),
            line(-px - 0.2, -SILK_Y, -px - 0.2, -Y + PAD_H / 2 - 0.3, "F.SilkS", 0.12),
            line(-px - 0.2, -SILK_Y, -px, -SILK_Y, "F.SilkS", 0.12)]
    out += [line(-CRT_X, -CRT_Y, CRT_X, -CRT_Y, "F.CrtYd", 0.05), line(CRT_X, -CRT_Y, CRT_X, CRT_Y, "F.CrtYd", 0.05),
            line(CRT_X, CRT_Y, -CRT_X, CRT_Y, "F.CrtYd", 0.05), line(-CRT_X, CRT_Y, -CRT_X, -CRT_Y, "F.CrtYd", 0.05)]
    for num, (x, y) in PADS.items():
        out.append(f'\t(pad "{num}" smd rect\n\t\t(at {x:g} {y:g})\n\t\t(size {PAD_W:g} {PAD_H:g})\n'
                   f'\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n\t)\n')
    out.append('\t(embedded_fonts no)\n)\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write("".join(out))
    print(OUT)


if __name__ == "__main__":
    main()
