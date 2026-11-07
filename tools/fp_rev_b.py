"""Builds Rev B's four new footprints into kicad/rev-b/IphoneFM.pretty, each from its maker's own drawing (step B3.2):

U8   Lumissil IS31FL3236A, QFN-44 5 x 5 mm, 0.4 mm pitch (datasheet Rev. I, 10/14/2024: p14 package, p16 recommended
     land pattern). 44 pads 0.25 mm wide, 1.0 mm long (2.0 to 3.0 mm out); the eight corner pads 0.8 mm long (2.2 to
     3.0 mm out) with their facing corners cut back, so neighbouring corner pads stay apart; a 2.45 mm centre pad (45)
     joined, as Lumissil draws it, to the middle pad of the top and bottom rows (pins 39 and 17, both GND). Lumissil
     rounds those corners (R0.125) and the joins (R0.1); KiCad pads can't round a single corner, so the corners are
     chamfered 0.125 mm (0.21 mm between corner pads against Lumissil's 0.20) and the joins are square. No stencil is
     given, so the centre pad's paste is KiCad's own four 0.99 mm windows for a 2.45 mm pad (65%).
DS1-DS4  Guangcai GS3011AW-B, 0.3 in single digit, 7.3 x 12.0 mm (GS3011A/CX-X, 2020-09-20 Rev. A: p2 outline, p3 pin
     positions, p5 soldering pad size). Ten 1.0 x 3.0 mm pads at 1.5 mm pitch, rows 12.5 mm apart (9.5 mm gap,
     15.5 mm outside). Top view: pins 1-5 along the bottom, left to right; 6-10 along the top, right to left.
SW4  Mitsumi SIQ-02FVS3 push-wheel encoder (SIQ series catalogue p3, SIQ-02FVS3 land dimensions), origin at the knob
     centre, terminals toward +y. Terminals 1-4 (A, S, C, B left to right) 1.3 x 1.2 mm at x -4, -1.475, 1.475, 4 and
     y 7.1-8.3; frame tabs 5-8 1.2 x 1.3 mm, 9.6 mm apart inside, at y 1.3 and 5.4; frame tabs 9, 10 0.85 x 1.2 mm
     on the 45-degree lines toward the knob, 4.0 to 5.2 mm from its centre (read from the PDF's own vectors: centres
     4.60 mm out); two unplated 1.6 mm holes 6 mm apart, 4.5 mm below the centre, for the frame's 1.55 mm bosses.
     Mitsumi's stencil: 150 um, 100% apertures, so paste is 1:1.
SW3  Diptronics DHN-06-V, 6-position half-pitch DIP (DHN(F) series p41). Pads copied unchanged from KiCad's
     SW_DIP_SPSTx06_Slide_Omron_A6H-6101_W6.15mm_P1.27mm, which is Diptronics' P.C.B. layout exactly: 1.25 x 0.76 mm
     at 1.27 mm pitch, rows 4.90 mm apart inside and 7.40 outside. Body is Diptronics' 8.85 x 4.50 mm. Pins 1-6 down
     one row under the switch numbers, 7-12 back up the other (the "ON" side); switch n joins pins n and 13 - n.

Silkscreen here is drawn at the body; tools/fp_silk_trim.py then cuts it back from copper and makes the pin-1 dots.
Usage: python tools/fp_rev_b.py"""
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "kicad", "rev-b", "IphoneFM.pretty")
KICAD = r"C:\Users\jakep\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
SILK, FAB, CRT = 0.25, 0.1, 0.05

U8_NAME = "Lumissil_QFN-44-1EP_5x5mm_P0.4mm_EP2.45x2.45mm"
DS_NAME = "LED_7Segment_Guangcai_GS3011_7.3x12mm_P1.5mm"
SW4_NAME = "RotaryEncoder_Switch_Mitsumi_SIQ-02FVS3"
SW3_NAME = "SW_DIP_SPSTx06_Slide_Diptronics_DHN-06_W6.15mm_P1.27mm"


def f(v):
    return f"{round(v, 4) + 0.0:g}"


def line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n'
            f'\t\t(stroke\n\t\t\t(width {w:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t)\n')


def poly(pts, layer, w, fill=False):
    xy = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return (f'\t(fp_poly\n\t\t(pts {xy})\n\t\t(stroke\n\t\t\t(width {w:g})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(fill {"yes" if fill else "no"})\n\t\t(layer "{layer}")\n\t)\n')


def circle(cx, cy, r, layer, w):
    return (f'\t(fp_circle\n\t\t(center {f(cx)} {f(cy)})\n\t\t(end {f(cx + r)} {f(cy)})\n'
            f'\t\t(stroke\n\t\t\t(width {w:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "{layer}")\n\t)\n')


def arc(cx, cy, r, a1, a2, layer, w):
    """Arc on a circle about (cx, cy), from angle a1 to a2 (degrees, measured as drawn: 0 = +x, 90 = -y)"""
    p = [(cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a))) for a in (a1, (a1 + a2) / 2, a2)]
    return (f'\t(fp_arc\n\t\t(start {f(p[0][0])} {f(p[0][1])})\n\t\t(mid {f(p[1][0])} {f(p[1][1])})\n\t\t(end {f(p[2][0])} {f(p[2][1])})\n'
            f'\t\t(stroke\n\t\t\t(width {w:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t)\n')


def rect(x1, y1, x2, y2, layer, w):
    return "".join(line(*a, layer, w) for a in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)))


def text(kind, value, x, y, layer, size=1.0, thick=0.15, angle=0):
    head = f'\t(property "{kind}" "{value}"' if kind else f'\t(fp_text user "{value}"'
    return (f'{head}\n\t\t(at {f(x)} {f(y)} {angle:g})\n\t\t(layer "{layer}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size:g} {size:g})\n\t\t\t\t(thickness {thick:g})\n\t\t\t)\n\t\t)\n\t)\n')


def pad(num, x, y, w, h, angle=0, layers='"F.Cu" "F.Mask" "F.Paste"', chamfer=None, extra=""):
    at = f"(at {f(x)} {f(y)}{f' {angle:g}' if angle else ''})"
    if chamfer:
        return (f'\t(pad "{num}" smd roundrect\n\t\t{at}\n\t\t(size {f(w)} {f(h)})\n\t\t(layers {layers})\n'
                f'\t\t(roundrect_rratio 0)\n\t\t(chamfer_ratio {chamfer[0]:g})\n\t\t(chamfer {chamfer[1]})\n{extra}\t)\n')
    return f'\t(pad "{num}" smd rect\n\t\t{at}\n\t\t(size {f(w)} {f(h)})\n\t\t(layers {layers})\n{extra}\t)\n'


def head(name, descr, tags, ref_y, val_y):
    return [f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "fp_rev_b.py")\n\t(layer "F.Cu")\n',
            f'\t(descr "{descr}")\n', f'\t(tags "{tags}")\n',
            text("Reference", "REF**", 0, ref_y, "F.SilkS"), text("Value", name, 0, val_y, "F.Fab"), '\t(attr smd)\n']


def write(name, parts):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name + ".kicad_mod")
    open(path, "w", encoding="utf-8", newline="\n").write("".join(parts) + '\t(embedded_fonts no)\n)\n')
    print(path)


def u8():
    PITCH, W, IN, OUT_, CIN, EP = 0.4, 0.25, 2.0, 3.0, 2.2, 2.45
    out = head(U8_NAME, "Lumissil QFN-44 5 x 5 mm, 0.4 mm pitch, 2.45 mm exposed pad joined to pins 17 and 39; pads per "
               "Lumissil's recommended land pattern (IS31FL3236A Rev. I p16); centre-pad paste per KiCad's 2.45 mm pattern",
               "QFN-44 0.4mm Lumissil IS31FL3236A", -4.1, 4.1)
    out.append(text(None, "${REFERENCE}", 0, 0, "F.Fab", 0.8, 0.12))
    b, c = 2.5, 0.6  # body half-size; pin-1 corner chamfer
    out.append(poly([(-b + c, -b), (b, -b), (b, b), (-b, b), (-b, -b + c)], "F.Fab", FAB))
    s = b + 0.11  # silkscreen corners at the body; trimming keeps what clears the pads
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        out += [line(sx * s, sy * s, sx * (s - 0.6), sy * s, "F.SilkS", SILK), line(sx * s, sy * s, sx * s, sy * (s - 0.6), "F.SilkS", SILK)]
    out.append(poly([(-3.45, -2.0), (-3.75, -2.25), (-3.75, -1.75)], "F.SilkS", SILK, True))  # pin 1, becomes a dot
    out.append(rect(-3.25, -3.25, 3.25, 3.25, "F.CrtYd", CRT))
    pads = []
    for k in range(1, 45):
        side, i = divmod(k - 1, 11)
        t = -IN + PITCH * i  # position along the side, first pin at the start of the side
        corner = i in (0, 10)
        inner = CIN if corner else IN
        if k == 17 or k == 39:  # joined to the centre pad
            inner = EP / 2
        mid, ln = (inner + OUT_) / 2, OUT_ - inner
        if side == 0:    # left, top to bottom
            x, y, w, h, along = -mid, t, ln, W, (1, 0)
        elif side == 1:  # bottom, left to right
            x, y, w, h, along = t, mid, W, ln, (0, -1)
        elif side == 2:  # right, bottom to top
            x, y, w, h, along = mid, -t, ln, W, (-1, 0)
        else:            # top, right to left
            x, y, w, h, along = -t, -mid, W, ln, (0, 1)
        ch = None
        if corner:  # cut the corner at the pad's inner end that faces the next side's corner pad
            sx, sy = (1 if x > 0 else -1), (1 if y > 0 else -1)
            if along[0]:  # horizontal pad: inner end toward the centre in x, corner side in y
                cx, cy = -sx, sy
            else:
                cx, cy = sx, -sy
            ch = (0.5, f"{'top' if cy < 0 else 'bottom'}_{'left' if cx < 0 else 'right'}")
        pads.append(pad(k, x, y, w, h, chamfer=ch))
    for x in (-0.61, 0.61):
        for y in (-0.61, 0.61):
            pads.append(f'\t(pad "" smd roundrect\n\t\t(at {f(x)} {f(y)})\n\t\t(size 0.99 0.99)\n\t\t(layers "F.Paste")\n\t\t(roundrect_rratio 0.25)\n\t)\n')
    pads.append(pad(45, 0, 0, EP, EP, layers='"F.Cu" "F.Mask"', extra="\t\t(property pad_prop_heatsink)\n"))
    write(U8_NAME, out + pads)


def ds():
    out = head(DS_NAME, "Guangcai GS3011A/CX-X 0.3 in single-digit SMD 7-segment display, 7.3 x 12.0 mm; pads per Guangcai's "
               "soldering pad size (GS3011A/CX-X 2020-09-20 Rev. A p5), pins per p3",
               "7-segment display SMD Guangcai GS3011", -8.6, 8.6)
    # step B5.1: the two common-anode pins are one node inside the part (GS3011A/CX-X p3, "3,8"), so KiCad may treat
    # them as joined and the board feeds VBUS to pin 8 only
    out.append('\t(jumper_pad_groups\n\t\t("3" "8")\n\t)\n')
    out.append(text(None, "${REFERENCE}", 0, 0, "F.Fab", 1.0, 0.15))
    bx, by = 7.3 / 2, 12.0 / 2
    out.append(rect(-bx, -by, bx, by, "F.Fab", FAB))
    # the digit on the fab layer: an outline 8 leaning 10 degrees, and the decimal point, as Guangcai draws them (p2)
    lean = math.tan(math.radians(10))
    for y1, y2 in ((-3.81, 0), (0, 3.81)):
        pts = [(-1.6 - y * lean, y) for y in (y1, y2)] + [(1.6 - y * lean, y) for y in (y2, y1)]
        out.append(poly(pts, "F.Fab", FAB))
    out.append(circle(2.6, 3.41 - 0.05, 0.45, "F.Fab", FAB))
    sx = bx + 0.11
    out += [line(-sx, -by, -sx, by, "F.SilkS", SILK), line(sx, -by, sx, by, "F.SilkS", SILK)]
    out.append(poly([(-3.0, 8.15), (-3.25, 8.45), (-2.75, 8.45)], "F.SilkS", SILK, True))  # pin 1, becomes a dot
    out.append(rect(-4.0, -8.0, 4.0, 8.0, "F.CrtYd", CRT))
    pads = []
    for k in range(1, 11):
        x = -3.0 + 1.5 * (k - 1) if k <= 5 else 3.0 - 1.5 * (k - 6)
        pads.append(pad(k, x, 6.25 if k <= 5 else -6.25, 1.0, 3.0))
    write(DS_NAME, out + pads)


def sw4():
    out = head(SW4_NAME, "Mitsumi SIQ-02FVS3 push-wheel rotary encoder, 15 detents, reflow; origin at the knob centre; "
               "pads per Mitsumi's land dimensions (SIQ series catalogue p3)", "rotary encoder thumbwheel push Mitsumi SIQ",
               -8.4, 9.6)
    out.append(text(None, "${REFERENCE}", 0, 2.6, "F.Fab", 1.0, 0.15))
    R = 14.5 / 2  # knob
    out.append(circle(0, 0, R, "F.Fab", FAB))
    out.append(rect(-5.15, 0, 5.15, 7.25, "F.Fab", FAB))  # frame below the knob centre, 10.3 wide, 7.25 deep
    out.append(arc(0, 0, 4.2, 180 - 38, 38, "F.Fab", FAB))  # its arched top (R4.2), the angled tabs at 45 degrees on it
    out.append(text(None, "A S C B", 0, 6.4, "F.Fab", 0.6, 0.1))
    # the wheel, as 5-degree chords (fp_silk_trim splits a circle into 0.1 mm pieces, under its 0.2 mm minimum, and
    # would drop it whole); trimming opens it at the pads
    rs = R + 0.11
    for i in range(72):
        a1, a2 = math.radians(5 * i), math.radians(5 * (i + 1))
        out.append(line(rs * math.cos(a1), rs * math.sin(a1), rs * math.cos(a2), rs * math.sin(a2), "F.SilkS", SILK))
    out.append(poly([(-4.0, 9.0), (-4.25, 9.3), (-3.75, 9.3)], "F.SilkS", SILK, True))  # terminal 1 (A), becomes a dot
    out.append(rect(-7.5, -7.5, 7.5, 8.75, "F.CrtYd", CRT))
    pads = [pad(n, x, 7.7, 1.3, 1.2) for n, x in ((1, -4.0), (2, -1.475), (3, 1.475), (4, 4.0))]
    pads += [pad(n, x, y, 1.2, 1.3) for n, x, y in ((5, -5.4, 1.3), (6, -5.4, 5.4), (7, 5.4, 5.4), (8, 5.4, 1.3))]
    rc = 4.0 + 1.2 / 2
    for n, sgn in ((9, 1), (10, -1)):  # long side radial: 1.2 along the 45-degree line, 0.85 across it
        pads.append(pad(n, sgn * rc / math.sqrt(2), -rc / math.sqrt(2), 1.2, 0.85, angle=45 if sgn > 0 else 135))
    for x in (-3.0, 3.0):
        pads.append(f'\t(pad "" np_thru_hole circle\n\t\t(at {f(x)} 4.5)\n\t\t(size 1.6 1.6)\n\t\t(drill 1.6)\n\t\t(layers "*.Cu" "*.Mask")\n\t)\n')
    write(SW4_NAME, out + pads)


def sw3():
    src = open(os.path.join(KICAD, "Button_Switch_SMD.pretty", "SW_DIP_SPSTx06_Slide_Omron_A6H-6101_W6.15mm_P1.27mm.kicad_mod"), encoding="utf-8").read()
    pads = "".join(m.group(0) for m in re.finditer(r'\t\(pad "\d+" smd .*?\n\t\)\n', src, flags=re.S))
    out = head(SW3_NAME, "Diptronics DHN-06-V 6-position half-pitch DIP switch, top actuated, 8.85 x 4.50 mm; pads per Diptronics' "
               "P.C.B. layout (DHN(F) series p41), copied from KiCad's Omron A6H-6101", "SMD DIP Switch SPST Slide 1.27mm Diptronics DHN",
               -5.5, 5.5)
    bx, by = 4.5 / 2, 8.85 / 2
    out.append(rect(-bx, -by, bx, by, "F.Fab", FAB))
    for i in range(6):  # levers, shown at the OFF end (toward pins 1-6); "ON" is printed on the other side
        y = -3.175 + 1.27 * i
        out.append(rect(-1.6, y - 0.25, 1.6, y + 0.25, "F.Fab", FAB))
        out.append(rect(-1.6, y - 0.25, -0.53, y + 0.25, "F.Fab", FAB))
    out.append(text(None, "ON", 1.2, -by + 0.45, "F.Fab", 0.5, 0.08))
    out.append(text(None, "1", -1.2, -by + 0.45, "F.Fab", 0.5, 0.08))
    out.append(text(None, "${REFERENCE}", 0, 0, "F.Fab", 0.8, 0.12, 90))
    sy = by + 0.11
    out += [line(-bx, -sy, bx, -sy, "F.SilkS", SILK), line(-bx, sy, bx, sy, "F.SilkS", SILK)]
    out.append(poly([(-3.075, -4.0), (-3.325, -4.3), (-2.825, -4.3)], "F.SilkS", SILK, True))  # pin 1, becomes a dot
    out.append(rect(-3.95, -4.76, 3.95, 4.76, "F.CrtYd", CRT))
    write(SW3_NAME, out + [pads])


if __name__ == "__main__":
    u8()
    ds()
    sw4()
    sw3()
