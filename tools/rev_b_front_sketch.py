"""Rev B front face: a to-scale sketch of the board's top side with the new tuning wheel, station display and power DIP,
beside an impression of the finished unit. Sizes from the datasheets in docs/datasheets/rev-b (SIQ-02FVS3 p3,
GS3011AW-B p2 and p5, DHN-06-V p1); the edge parts that stay (J1, J2, SW1, SW2, D1) and the mounting holes where
Rev A has them. Usage: python tools/rev_b_front_sketch.py"""
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

OUT = "design/rev-b/front-face-sketch.png"
BW, BH = 46.45, 71.4                     # board, mm (Rev A envelope), from its top-left corner, y down
K, SS = 12, 3                            # px per mm in the output; supersampling
HOLES = [(13, 7), (33, 7), (41, 57), (8, 66)]
PITCH, ROW_Y = 8.0, 18.0                 # digit pitch (body 7.30 wide), digit body centre line
DIGITS = [BW / 2 + (i - 1.5) * PITCH for i in range(4)]
SHOW, DP_AT = "1079", 2                  # 107.9
DIP = (BW / 2, 4.6)                      # centre; pad rows 4.90 / 7.40 apart
ENC = (3.85, 35.0)                       # dial centre: the frame's far end on the board edge, dial 3.4 mm past it
SEGS = {"0": "ABCDEF", "1": "BC", "7": "ABC", "9": "ABCDFG"}
GREEN, GOLD, SILVER, CASE = "#23753a", "#d6a94c", "#b9bcc2", "#2a2c31"
LIT = "#f4f7ff"


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size * SS)


class Panel:
    def __init__(self, img, glow, ox, oy):
        self.d, self.g, self.ox, self.oy = ImageDraw.Draw(img), ImageDraw.Draw(glow), ox, oy

    def p(self, x, y):
        return ((self.ox + x * K) * SS, (self.oy + y * K) * SS)

    def poly(self, pts, fill, outline=None, width=0, glow=False):
        q = [self.p(*pt) for pt in pts]
        self.d.polygon(q, fill=fill, outline=outline, width=int(width * SS))
        if glow:
            self.g.polygon(q, fill=255)

    def rect(self, x0, y0, x1, y1, fill, outline=None, width=1, r=0):
        self.d.rounded_rectangle((*self.p(x0, y0), *self.p(x1, y1)), radius=r * K * SS, fill=fill, outline=outline,
                                 width=width * SS)

    def circle(self, x, y, r, fill, outline=None, width=1):
        self.d.ellipse((*self.p(x - r, y - r), *self.p(x + r, y + r)), fill=fill, outline=outline, width=width * SS)

    def text(self, x, y, s, size, fill="#222", bold=False, anchor="la"):
        self.d.multiline_text(self.p(x, y), s, font=font(size, bold), fill=fill, anchor=anchor, spacing=4 * SS,
                              align={"l": "left", "m": "center", "r": "right"}[anchor[0]])

    def callout(self, at, to, s, size=17, fill="#222", bold=False):
        """A leader from the part (mm) to the label (mm); the label sits left or right of its end by the leader's way."""
        self.d.line([self.p(*at), self.p(*to)], fill="#555", width=2 * SS)
        self.circle(*at, 0.35, "#555")
        right = to[0] >= at[0]
        self.text(to[0] + (0.6 if right else -0.6), to[1], s, size, fill, bold, "lm" if right else "rm")
        if "\n" in s:   # multi-line: centre the block on the leader
            pass


def digit(pn, cx, cy, ch, dp, face, unlit, pads):
    """GS3011AW-B: body 7.30 x 12.00, segments 4.22 x 7.62 slanted 10 degrees, DP 0.90; pads 1.0 x 3.0 at 1.5 pitch."""
    if pads:
        for row in (-1, 1):
            for k in range(5):
                x = cx + (k - 2) * 1.5
                pn.rect(x - 0.5, cy + row * 6.25 - 1.5, x + 0.5, cy + row * 6.25 + 1.5, GOLD)
    if face:
        pn.rect(cx - 3.65, cy - 6, cx + 3.65, cy + 6, face, "#3b3b3f", 1, 0.15)
    w, h, t, g, sk = 4.22, 7.62, 0.85, 0.12, math.tan(math.radians(10))
    bx = cx - 0.45

    def put(pts):
        return [(bx + x - y * sk, cy + y) for x, y in pts]

    def hseg(y0):
        x1, x2 = -w / 2 + t / 2 + g, w / 2 - t / 2 - g
        return [(x1, y0), (x1 + t / 2, y0 - t / 2), (x2 - t / 2, y0 - t / 2), (x2, y0), (x2 - t / 2, y0 + t / 2),
                (x1 + t / 2, y0 + t / 2)]

    def vseg(x0, y1, y2):
        y1, y2 = y1 + g, y2 - g
        return [(x0, y1), (x0 + t / 2, y1 + t / 2), (x0 + t / 2, y2 - t / 2), (x0, y2), (x0 - t / 2, y2 - t / 2),
                (x0 - t / 2, y1 + t / 2)]

    top, bot, rx, lx = -h / 2 + t / 2, h / 2 - t / 2, w / 2 - t / 2, -w / 2 + t / 2
    segs = {"A": hseg(top), "G": hseg(0), "D": hseg(bot), "B": vseg(rx, top, 0), "C": vseg(rx, 0, bot),
            "F": vseg(lx, top, 0), "E": vseg(lx, 0, bot)}
    on = SEGS.get(ch, "")
    for name, pts in segs.items():
        pn.poly(put(pts), LIT if name in on else unlit, glow=name in on)
    (dx, dy), = put([(w / 2 + 0.75, h / 2 - 0.45)])
    pn.circle(dx, dy, 0.45, LIT if dp else unlit)
    if dp:
        pn.g.ellipse((*pn.p(dx - 0.45, dy - 0.45), *pn.p(dx + 0.45, dy + 0.45)), fill=255)


def dial(pn, cx, cy):
    """SIQ-02FVS3 knob: diameter 14.5, knurled, black, four dimples."""
    pts = []
    for i in range(720):
        a = 2 * math.pi * i / 720
        r = 7.05 + 0.2 * math.cos(16 * a)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pn.poly(pts, "#1c1c1f", "#6c6c74", 0.6)
    pn.circle(cx, cy, 4.85, "#242428", "#3e3e44", 1)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        pn.circle(cx + 1.9 * math.cos(a), cy + 1.9 * math.sin(a), 1.1, "#151518", "#38383d", 1)


def encoder(pn, cx, cy):
    """Frame 10.3 along the edge, from 3.85 outboard of the dial centre to the terminals 7.25 inboard; terminals at
    2.95 pitch (A, S, C, B), 8 overall."""
    for k in range(4):
        y = cy + (k - 1.5) * 2.95
        pn.rect(cx + 7.0, y - 0.5, cx + 8.3, y + 0.5, GOLD)
    pn.rect(cx - 3.85, cy - 5.15, cx + 7.25, cy + 5.15, SILVER, "#8d9096", 1, 1.2)
    dial(pn, cx, cy)


def dip(pn, cx, cy, on=(1, 1, 0, 1, 0, 0), pads=True):
    """DHN-06-V: body 8.85 x 4.50, six levers at 1.27, pad rows 4.90 / 7.40 apart, pads 0.76 wide."""
    for k in range(6):
        x = cx + (k - 2.5) * 1.27
        if pads:
            for row in (-1, 1):
                pn.rect(x - 0.38, cy + row * 2.45 - (1.25 if row < 0 else 0), x + 0.38,
                        cy + row * 2.45 + (1.25 if row > 0 else 0), GOLD)
    pn.rect(cx - 4.425, cy - 2.25, cx + 4.425, cy + 2.25, "#17171a", "#3a3a3f", 1, 0.2)
    for k in range(6):
        x = cx + (k - 2.5) * 1.27
        pn.rect(x - 0.4, cy - 1.25, x + 0.4, cy + 1.25, "#303034")
        ly = cy - 1.25 if on[k] else cy + 0.15
        pn.rect(x - 0.36, ly, x + 0.36, ly + 1.1, "#f2f2f2")
    pn.text(cx - 4.1, cy - 2.2, "ON", 9, "#e8e8e8")


def board_view(pn):
    pn.rect(0, 0, BW, BH, GREEN, "#18562a", 2)
    for x, y in HOLES:
        pn.circle(x, y, 1.1, "#101012")
    # parts that stay where Rev A has them
    pn.rect(BW / 2 - 4.47, BH - 7.3, BW / 2 + 4.47, BH, SILVER, "#8d9096", 1, 0.5)          # J1 USB-C
    pn.rect(0.4, 62.6, 3.5, 69.2, "#2b2b2e", "#55555a", 1, 0.3)                                # SW1 TX/RX slide
    pn.rect(-1.4, 65.2, 0.4, 66.6, "#d9d9d9")
    pn.rect(11.05, 68.3, 14.55, BH, "#c8c8cc", "#8d9096", 1, 0.3)                            # SW2 BOOT
    pn.rect(39.1, 64.1, 45.45, 70.4, GOLD, "#a8802e", 1, 0.3)                                  # J2 SMA
    pn.rect(43.0, 64.1, 52.5, 70.4, "#e2bd62", "#a8802e", 1, 0.4)
    pn.rect(42.55, 2.7, 44.05, 4.2, "#f4f4f4", "#999", 1)                                       # D1
    # new front-panel parts
    dip(pn, *DIP)
    for i, x in enumerate(DIGITS):
        digit(pn, x, ROW_Y, SHOW[i], i == DP_AT, "#121214", "#3c3c40", True)
    encoder(pn, *ENC)
    # board size
    y = BH + 3.2
    pn.d.line([pn.p(0, y), pn.p(BW, y)], fill="#555", width=2 * SS)
    for x in (0, BW):
        pn.d.line([pn.p(x, y - 1), pn.p(x, y + 1)], fill="#555", width=2 * SS)
    pn.text(BW / 2, y + 0.6, "46.45 mm", 16, "#444", anchor="ma")
    x = BW + 9.5
    pn.d.line([pn.p(x, 0), pn.p(x, BH)], fill="#555", width=2 * SS)
    for yy in (0, BH):
        pn.d.line([pn.p(x - 1, yy), pn.p(x + 1, yy)], fill="#555", width=2 * SS)
    pn.text(x + 0.8, BH / 2, "71.4 mm", 16, "#444", anchor="lm")


def unit_view(pn):
    """Impression only: no enclosure is designed yet."""
    w = 1.6
    pn.rect(-w + 0.8, -w + 1.0, BW + w + 0.8, BH + w + 1.0, "#d5d6da", r=4.5)                 # shadow
    # antenna and SMA on the right side
    pn.rect(BW + w, 64.6, BW + 6.5, 69.9, "#e2bd62", "#a8802e", 1, 0.4)
    pn.rect(BW + 6.0, 22.0, BW + 9.6, 70.6, "#1d1e21", "#3c3d42", 1, 1.8)
    pn.rect(-w - 1.4, 65.0, -w + 0.2, 66.8, "#d9d9d9", "#999", 1, 0.3)                         # TX/RX slide
    pn.rect(-w, -w, BW + w, BH + w, CASE, "#45474d", 2, 4.0)
    # wheel: its rim through a slot in the left side
    dial(pn, *ENC)
    pn.rect(ENC[0] - 2.6, ENC[1] - 7.6, ENC[0] + 7.6, ENC[1] + 7.6, CASE)
    pn.d.line([pn.p(ENC[0] - 2.6, ENC[1] - 7.0), pn.p(ENC[0] - 2.6, ENC[1] + 7.0)], fill="#16171a", width=3 * SS)
    # display window
    pn.rect(DIGITS[0] - 5.0, ROW_Y - 7.0, DIGITS[-1] + 5.2, ROW_Y + 7.0, "#0b0b0d", "#4a4c52", 2, 1.0)
    for i, x in enumerate(DIGITS):
        digit(pn, x, ROW_Y, SHOW[i], i == DP_AT, None, "#1b1b1e", False)
    pn.text(DIGITS[-1] + 5.2, ROW_Y + 8.4, "MHz", 12, "#9a9ca3", anchor="ra")
    # DIP in a recess, status LED light pipe, ports in the bottom wall
    pn.rect(DIP[0] - 5.6, DIP[1] - 3.2, DIP[0] + 5.6, DIP[1] + 3.2, "#1a1b1e", "#4a4c52", 1, 0.6)
    dip(pn, *DIP, pads=False)
    pn.circle(43.3, 3.45, 1.1, "#7fe0a0", "#bff0cf", 1)
    pn.g.ellipse((*pn.p(42.6, 2.75), *pn.p(44.0, 4.15)), fill=150)
    pn.rect(BW / 2 - 4.6, BH + w - 1.2, BW / 2 + 4.6, BH + w + 0.4, "#111214", r=0.6)
    pn.rect(11.8, BH + w - 0.9, 13.8, BH + w + 0.3, "#111214", r=0.3)


def main():
    W, H = 2560, 1330
    img = Image.new("RGB", (W * SS, H * SS), "white")
    glow = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(img)
    d.text((30 * SS, 22 * SS), "Rev B front face: to-scale sketch", font=font(34, True), fill="#111")
    d.text((30 * SS, 72 * SS), "Top side of the board, 12 px per mm (looking at the back of the phone, camera top left)",
           font=font(20, True), fill="#1f3a6d")
    d.text((1330 * SS, 72 * SS), "How it could look in a case (impression; no enclosure designed yet)",
           font=font(20, True), fill="#1f3a6d")

    a = Panel(img, glow, 350, 150)
    board_view(a)
    a.callout((DIP[0] + 4.4, DIP[1] - 1.5), (BW + 13, -1.5),
              "Power DIP, Diptronics DHN-06-V\n6 top levers, 8.85 × 4.5 mm, 1.6 mm tall")
    a.callout((DIGITS[-1] + 3.6, ROW_Y), (BW + 13, ROW_Y),
              "Station display, 4 × GS3011AW-B\n0.3\" (7.6 mm) white digits, black face\nrow 31.3 mm wide, 3.75 mm tall")
    a.callout((ENC[0] - 3.4, ENC[1] - 4.0), (-6.0, ENC[1] - 9.0),
              "Tuning wheel\nMitsumi SIQ-02FVS3\nØ14.5 mm, 4 mm tall,\n3.4 mm past the edge\nturn + push in")
    a.callout((44.0, 3.45), (BW + 13, 7.5), "D1 status LED (as Rev A)", 15, "#666")
    a.callout((0.4, 64.0), (-6.0, 60.0), "SW1 TX / RX\n(as Rev A)", 15, "#666")
    a.callout((12.8, 69.0), (-6.0, 71.0), "SW2 BOOT (as Rev A)", 15, "#666")
    a.callout((BW / 2, 66.5), (BW + 13, 60.0), "J1 USB-C (as Rev A)", 15, "#666")
    a.callout((50.0, 68.5), (BW + 13, 66.0), "J2 SMA (as Rev A)", 15, "#666")

    b = Panel(img, glow, 1640, 150)
    unit_view(b)
    b.callout((ENC[0] - 3.3, ENC[1]), (-8.5, ENC[1]), "Turn to tune\n15 clicks a turn\npush the wheel in\nto select", 17)
    b.callout((DIGITS[-1] + 5.2, ROW_Y - 3.0), (BW + 13, ROW_Y - 3.0), "Station in MHz", 17)
    b.callout((DIP[0] + 5.6, DIP[1]), (BW + 13, 3.0), "TX power DIP\n(bench setting)", 17)
    b.callout((BW + 7.8, 40.0), (BW + 13, 40.0), "antenna\non J2 (SMA)", 17)
    b.callout((-2.4, 65.9), (-8.5, 62.0), "TX / RX", 17)
    b.callout((BW / 2, BH + 1.6), (BW + 13, BH + 2.5), "USB-C below", 17)

    glow = glow.filter(ImageFilter.GaussianBlur(SS * K * 0.45))
    halo = glow.point(lambda v: int(v * 0.5))
    img = ImageChops.add(img, Image.merge("RGB", (halo, halo, halo)))
    d = ImageDraw.Draw(img)
    notes = [
        "Heights above the board: SMA 9.5 mm (sets the case height) · wheel 4.0 · digits 3.75 · USB-C 3.26 · DIP 1.6.",
        "The display uses the top band of the board (y 10–26 mm), which in Rev A held mostly traces, test points TP2/TP3 "
        "and the side DIP;",
        "the radio parts below it shift in layout. Its IS31FL3236A driver (QFN-44, 5 × 5 mm) goes in the board area "
        "and is not drawn.",
        "The wheel's push-in switch is the select button; the three Rev A wheels (RV1–RV3) on this edge are gone.",
    ]
    for i, s in enumerate(notes):
        d.text((30 * SS, (1155 + i * 32) * SS), s, font=font(19), fill="#333")
    img = img.resize((W, H), Image.LANCZOS)
    img.save(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
