"""Builds the footprint for RV1-RV3 (Alps RK10J11R0A0H, reflow-type thumbwheel potentiometer) from Alps' PC board
drawing for the RK10J1#R (catalog p390, docs/datasheets/analog-fm/POT_Alps_RK10J.pdf p2), viewed from the mounting
side. The origin is the centre of the knob.
- Five terminal lands 1.2 x 1.4 mm at 2 mm pitch, 8.3 to 9.7 mm below the knob centre: 1, 2, D1, D2, 3 from the left
  (terminal layout, p3: 1, 2, dummy, dummy, 3).
- Two mounting lands M1, M2, 2.2 x 1.4 mm, 10 mm apart (inner edges), 1.8 to 3.2 mm above the knob centre.
- Two unplated slots for the frame's locating bosses, 2.2 mm wide, 1 mm above the mounting lands and 7.4 mm below
  their top edge, i.e. 4.2 mm either side of the knob centre. The drawing doesn't size them across; 1.1 mm follows
  LCSC's footprint for this part (C470766), whose lands and slots reproduce every dimension above.
KiCad has no footprint or 3D model for this part.
Writes kicad/rev-a/IphoneFM.pretty/Potentiometer_Alps_RK10J_Reflow_Thumbwheel_14mm.kicad_mod.
Usage: python tools/fp_rv_rk10j.py"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "Potentiometer_Alps_RK10J_Reflow_Thumbwheel_14mm"
OUT = os.path.join(ROOT, "kicad", "rev-a", "IphoneFM.pretty", NAME + ".kicad_mod")

TERM_W, TERM_H, TERM_Y = 1.2, 1.4, 8.3 + 1.4 / 2
TERMS = {"1": -4, "2": -2, "D1": 0, "D2": 2, "3": 4}
MNT_W, MNT_H, MNT_Y, MNT_X = 2.2, 1.4, -(1.8 + 1.4 / 2), 10 / 2 + 2.2 / 2
SLOT_W, SLOT_H, SLOT_Y = 2.2, 1.1, 4.2
WHEEL_R = 7.0
FRAME = (-5.35, 3.8, 6.0, 8.5)  # terminal end of the frame below the wheel: left, top, right, bottom
SILK, GAP = 0.12, 0.2
CRT = (-7.45, -7.25, 7.45, TERM_Y + TERM_H / 2 + 0.25)


def line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line\n\t\t(start {x1:.4g} {y1:.4g})\n\t\t(end {x2:.4g} {y2:.4g})\n'
            f'\t\t(stroke\n\t\t\t(width {w:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t)\n')


def text(kind, value, x, y, layer, size=1.0, thick=0.15):
    head = f'\t(property "{kind}" "{value}"' if kind else f'\t(fp_text user "{value}"'
    return (f'{head}\n\t\t(at {x:g} {y:g} 0)\n\t\t(layer "{layer}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size:g} {size:g})\n\t\t\t\t(thickness {thick:g})\n\t\t\t)\n\t\t)\n\t)\n')


def smd(num, x, y, w, h):
    return (f'\t(pad "{num}" smd rect\n\t\t(at {x:g} {y:g})\n\t\t(size {w:g} {h:g})\n'
            f'\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n\t)\n')


def pads():
    out = [smd(n, x, TERM_Y, TERM_W, TERM_H) for n, x in TERMS.items()]
    out += [smd("M1", -MNT_X, MNT_Y, MNT_W, MNT_H), smd("M2", MNT_X, MNT_Y, MNT_W, MNT_H)]
    out += [f'\t(pad "" np_thru_hole oval\n\t\t(at 0 {y:g})\n\t\t(size {SLOT_W:g} {SLOT_H:g})\n'
            f'\t\t(drill oval {SLOT_W:g} {SLOT_H:g})\n\t\t(layers "*.Cu" "*.Mask")\n\t)\n' for y in (-SLOT_Y, SLOT_Y)]
    return out


def clear_of_pads(x, y):
    boxes = [(x0, TERM_Y, TERM_W, TERM_H) for x0 in TERMS.values()] + [(-MNT_X, MNT_Y, MNT_W, MNT_H), (MNT_X, MNT_Y, MNT_W, MNT_H)]
    return all(math.hypot(max(abs(x - bx) - w / 2, 0), max(abs(y - by) - h / 2, 0)) >= GAP + SILK / 2 for bx, by, w, h in boxes)


def main():
    out = [f'(footprint "{NAME}"\n\t(version 20260206)\n\t(generator "fp_rv_rk10j.py")\n\t(layer "F.Cu")\n',
           '\t(descr "Alps RK10J11R0A0H reflow-type thumbwheel potentiometer, 14 mm knurled wheel; lands and boss slots per Alps\' PC board drawing for the RK10J1#R (catalog p390); origin at the knob centre")\n',
           '\t(tags "potentiometer thumbwheel Alps RK10J reflow")\n',
           text("Reference", "REF**", 0, CRT[1] - 0.8, "F.SilkS"),
           text("Value", NAME, 0, CRT[3] + 0.8, "F.Fab"),
           '\t(attr smd)\n',
           text(None, "${REFERENCE}", 0, 0, "F.Fab", 0.8, 0.12)]
    # fab: wheel and the frame's terminal end
    out.append(f'\t(fp_circle\n\t\t(center 0 0)\n\t\t(end {WHEEL_R:g} 0)\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "F.Fab")\n\t)\n')
    l, t, r, b = FRAME
    out += [line(l, t, l, b, "F.Fab", 0.1), line(l, b, r, b, "F.Fab", 0.1), line(r, b, r, t, "F.Fab", 0.1)]
    # silk: the wheel's outline 0.1 mm outside it, broken where it would come near the mounting lands
    rs, step = WHEEL_R + 0.1, 5
    for a in range(0, 360, step):
        x1, y1 = rs * math.cos(math.radians(a)), rs * math.sin(math.radians(a))
        x2, y2 = rs * math.cos(math.radians(a + step)), rs * math.sin(math.radians(a + step))
        if clear_of_pads(x1, y1) and clear_of_pads(x2, y2) and clear_of_pads((x1 + x2) / 2, (y1 + y2) / 2):
            out.append(line(x1, y1, x2, y2, "F.SilkS", SILK))
    # pin-1 mark: a short bar left of terminal 1
    px = TERMS["1"] - TERM_W / 2 - GAP - SILK / 2 - 0.3
    out.append(line(px, TERM_Y - TERM_H / 2, px, TERM_Y + TERM_H / 2, "F.SilkS", SILK))
    x0, y0, x1, y1 = CRT
    out += [line(x0, y0, x1, y0, "F.CrtYd", 0.05), line(x1, y0, x1, y1, "F.CrtYd", 0.05),
            line(x1, y1, x0, y1, "F.CrtYd", 0.05), line(x0, y1, x0, y0, "F.CrtYd", 0.05)]
    out += pads()
    out.append('\t(embedded_fonts no)\n)\n')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write("".join(out))
    print(OUT)


if __name__ == "__main__":
    main()
