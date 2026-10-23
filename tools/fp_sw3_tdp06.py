"""Builds SW3's footprint (C&K TDP06H1SBD1, 6-position side-actuated DIP switch, 1.27 mm pitch). The twelve pads are
copied unchanged from KiCad's SW_DIP_SPSTx06_Slide_KingTek_DSHP06TS_W7.62mm_P1.27mm, which match C&K's land pattern
(TDP datasheet rev. CM.06/17/25 p3): 1.27 x 0.76 mm pads, 1.27 mm pitch, rows 7.62 mm apart. The body is C&K's:
8.74 x 6.0 mm with 1.0 mm chamfers on the back corners, and six levers standing 0.75 mm out of the front face (the
side the switch numbers are printed on). Pin 1 is switch 1's front leg; switch n joins pins n and 13 - n.
KiCad has no 3D model for this switch.
Writes kicad/rev-a/IphoneFM.pretty/SW_DIP_SPSTx06_Side_CK_TDP06H1SBD1_W7.62mm_P1.27mm.kicad_mod.
Usage: python tools/fp_sw3_tdp06.py"""
import os
import re

KICAD_FP = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Button_Switch_SMD.pretty\SW_DIP_SPSTx06_Slide_KingTek_DSHP06TS_W7.62mm_P1.27mm.kicad_mod"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "SW_DIP_SPSTx06_Side_CK_TDP06H1SBD1_W7.62mm_P1.27mm"
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", NAME + ".kicad_mod")

BX, BY = 6.0 / 2, 8.74 / 2  # body: front face (levers) at -BX, switch 1 at -BY
CHAMFER = 1.0  # back corners
LEVER_OUT, LEVER_W = 0.75, 0.6
ROWS = [-3.175 + 1.27 * i for i in range(6)]  # switch 1 to 6
PAD_X0 = 3.81 - 1.27 / 2  # pads start 3.175 mm out and end 4.445 mm out
PAD_Y = ROWS[-1] + 0.76 / 2  # last pad edge, 3.555 mm
SILK, GAP = 0.12, 0.2  # line width; clearance from pads
SX, SY = BX + 0.1, BY + 0.1  # silkscreen just outside the body
FRONT = -(PAD_X0 + 1.27 + GAP + SILK / 2)  # front-face line, outside the pads
CRT_L, CRT_R, CRT_Y = -5.1, 4.7, BY + 0.25  # around the pads, body, levers and the pin-1 triangle


def line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line\n\t\t(start {x1:g} {y1:g})\n\t\t(end {x2:g} {y2:g})\n'
            f'\t\t(stroke\n\t\t\t(width {w:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t)\n')


def poly(pts, layer, fill):
    xy = " ".join(f"(xy {x:g} {y:g})" for x, y in pts)
    return (f'\t(fp_poly\n\t\t(pts {xy})\n\t\t(stroke\n\t\t\t(width {SILK:g})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(fill {"yes" if fill else "no"})\n\t\t(layer "{layer}")\n\t)\n')


def text(kind, value, x, y, layer, size=1.0, thick=0.15, angle=0):
    head = f'\t(property "{kind}" "{value}"' if kind else f'\t(fp_text user "{value}"'
    return (f'{head}\n\t\t(at {x:g} {y:g} {angle:g})\n\t\t(layer "{layer}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size:g} {size:g})\n\t\t\t\t(thickness {thick:g})\n\t\t\t)\n\t\t)\n\t)\n')


def main():
    src = open(KICAD_FP, encoding="utf-8").read()
    pads = "".join(m.group(0) for m in re.finditer(r'\t\(pad "\d+" smd .*?\n\t\)\n', src, flags=re.S))
    out = [f'(footprint "{NAME}"\n\t(version 20260206)\n\t(generator "fp_sw3_tdp06.py")\n\t(layer "F.Cu")\n',
           '\t(descr "C&K TDP06H1SBD1 6-position side-actuated half-pitch DIP switch, extended levers; pads per C&K\'s land pattern (TDP datasheet rev. CM.06/17/25 p3), copied from KiCad\'s KingTek DSHP06TS; body 8.74 x 6.0 mm")\n',
           '\t(tags "SMD DIP Switch SPST Side 1.27mm C&K TDP")\n',
           text("Reference", "REF**", 0, -CRT_Y - 0.8, "F.SilkS"),
           text("Value", NAME, 0, CRT_Y + 0.8, "F.Fab"),
           '\t(attr smd)\n',
           text(None, "${REFERENCE}", 0.6, 0, "F.Fab", 0.8, 0.12, 90)]
    # fab: body with back-corner chamfers, the six levers on the front face, "1" at switch 1
    body = [(-BX, -BY), (BX - CHAMFER, -BY), (BX, -BY + CHAMFER), (BX, BY - CHAMFER), (BX - CHAMFER, BY), (-BX, BY)]
    out.append(poly(body, "F.Fab", False).replace(f"(width {SILK:g})", "(width 0.1)"))
    for y in ROWS:
        out.append(poly([(-BX, y - LEVER_W / 2), (-BX - LEVER_OUT, y - LEVER_W / 2), (-BX - LEVER_OUT, y + LEVER_W / 2), (-BX, y + LEVER_W / 2)],
                        "F.Fab", False).replace(f"(width {SILK:g})", "(width 0.1)"))
    out.append(text(None, "1", -BX + 0.5, ROWS[0], "F.Fab", 0.6, 0.1))
    # silk: body ends, back side with chamfers, front-face line outside the pads, triangle at switch 1
    stop = PAD_Y + GAP + SILK / 2  # the chamfer lines stop short of the back row of pads
    cx = SX - CHAMFER + (SY - stop)
    out += [line(FRONT, -SY, SX - CHAMFER, -SY, "F.SilkS", SILK), line(FRONT, SY, SX - CHAMFER, SY, "F.SilkS", SILK),
            line(SX - CHAMFER, -SY, cx, -stop, "F.SilkS", SILK), line(SX - CHAMFER, SY, cx, stop, "F.SilkS", SILK),
            line(FRONT, -SY, FRONT, SY, "F.SilkS", SILK)]
    out.append(poly([(FRONT - 0.25, ROWS[0] - 0.3), (FRONT - 0.25, ROWS[0] + 0.3), (FRONT - 0.05, ROWS[0])], "F.SilkS", True))
    out += [line(CRT_L, -CRT_Y, CRT_R, -CRT_Y, "F.CrtYd", 0.05), line(CRT_R, -CRT_Y, CRT_R, CRT_Y, "F.CrtYd", 0.05),
            line(CRT_R, CRT_Y, CRT_L, CRT_Y, "F.CrtYd", 0.05), line(CRT_L, CRT_Y, CRT_L, -CRT_Y, "F.CrtYd", 0.05)]
    out.append(pads)
    out.append('\t(embedded_fonts no)\n)\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write("".join(out))
    print(OUT)


if __name__ == "__main__":
    main()
