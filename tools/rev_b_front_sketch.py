"""Rev B front face: a to-scale sketch of the board's top side with the new tuning wheel, station display and power DIP,
beside an impression of the finished unit held sideways. Sizes from the datasheets in docs/datasheets/rev-b
(SIQ-02FVS3 p3, GS3011AW-B p2 and p5, DHN-06-V p1); the edge parts that stay (J1, J2, SW1, SW2, D1) and the mounting
holes where Rev A has them. The new parts take Rev A's left column: the digits where RV1 and RV2 were, turned a quarter
so they read with the phone sideways (board's left edge down), the wheel where RV3 was, the DIP where SW3 was.
Usage: python tools/rev_b_front_sketch.py"""
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

OUT = "design/rev-b/front-face-sketch.png"
BW, BH = 46.45, 71.4                     # board, mm (Rev A envelope), from its top-left corner, y down
K, SS = 12, 3                            # px per mm in the output; supersampling
HOLES = [(13, 7), (33, 7), (41, 57), (8, 66)]
PITCH, DX, DY = 8.0, 8.25, 26.5          # digit pitch (body 7.30 wide); display centre: pads 0.5-16.0 mm from the edge
DIGITS = [DY + (i - 1.5) * PITCH for i in range(4)]
SHOW, DP_AT = "1079", 2                  # 107.9
DIP = (BW / 2, 4.6)                      # SW3's place; pad rows 4.90 / 7.40 apart
ENC = (3.85, 52.44)                      # RV3's place; dial centre with the frame's far end on the board edge
DRV = (19.3, 14.0)                       # IS31FL3236A, roughly
SEGS = {"0": "ABCDEF", "1": "BC", "7": "ABC", "9": "ABCDFG"}
GREEN, GOLD, SILVER, CASE = "#23753a", "#d6a94c", "#b9bcc2", "#2a2c31"
LIT = "#f4f7ff"


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size * SS)


class Panel:
    """Draws in board millimetres. sideways: the view turned a quarter anticlockwise, the board's left edge down."""

    def __init__(self, img, glow, ox, oy, sideways=False):
        self.d, self.g, self.ox, self.oy, self.side = ImageDraw.Draw(img), ImageDraw.Draw(glow), ox, oy, sideways

    def p(self, x, y):
        if self.side:
            x, y = y, BW - x
        return ((self.ox + x * K) * SS, (self.oy + y * K) * SS)

    def box(self, x0, y0, x1, y1):
        (a, b), (c, d) = self.p(x0, y0), self.p(x1, y1)
        return min(a, c), min(b, d), max(a, c), max(b, d)

    def poly(self, pts, fill, outline=None, width=0, glow=False):
        q = [self.p(*pt) for pt in pts]
        self.d.polygon(q, fill=fill, outline=outline, width=int(width * SS))
        if glow:
            self.g.polygon(q, fill=255)

    def rect(self, x0, y0, x1, y1, fill, outline=None, width=1, r=0):
        self.d.rounded_rectangle(self.box(x0, y0, x1, y1), radius=r * K * SS, fill=fill, outline=outline,
                                 width=width * SS)

    def circle(self, x, y, r, fill, outline=None, width=1, glow=0):
        self.d.ellipse(self.box(x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=width * SS)
        if glow:
            self.g.ellipse(self.box(x - r, y - r, x + r, y + r), fill=glow)

    def text(self, x, y, s, size, fill="#222", bold=False, anchor="la"):
        self.label(self.p(x, y), s, size, fill, bold, anchor)

    def label(self, xy, s, size, fill="#222", bold=False, anchor="la"):
        self.d.multiline_text(xy, s, font=font(size, bold), fill=fill, anchor=anchor, spacing=4 * SS,
                              align={"l": "left", "m": "center", "r": "right"}[anchor[0]])

    def callout(self, at, to, s, size=17, fill="#222"):
        """A leader from the part to the label (both in board mm); the label sits beyond the leader's end."""
        a, b = self.p(*at), self.p(*to)
        self.d.line([a, b], fill="#555", width=2 * SS)
        self.circle(*at, 0.35, "#555")
        right = b[0] >= a[0]
        self.label((b[0] + (1 if right else -1) * 0.6 * K * SS, b[1]), s, size, fill, False, "lm" if right else "rm")


def digit(pn, cx, cy, ch, dp, face, unlit, pads):
    """GS3011AW-B: body 7.30 x 12.00, segments 4.22 x 7.62 slanted 10 degrees, DP 0.90; pads 1.0 x 3.0 at 1.5 pitch.
    Drawn in the digit's own frame (u right, v down), turned so its top faces the board's right edge."""
    def put(pts):
        return [(cx - v, cy + u) for u, v in pts]

    def box(u0, v0, u1, v1):
        return put([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    if pads:
        for row in (-1, 1):
            for k in range(5):
                u = (k - 2) * 1.5
                pn.poly(box(u - 0.5, row * 6.25 - 1.5, u + 0.5, row * 6.25 + 1.5), GOLD)
    if face:
        pn.poly(box(-3.65, -6, 3.65, 6), face, "#3b3b3f", 0.4)
    w, h, t, g, sk = 4.22, 7.62, 0.85, 0.12, math.tan(math.radians(10))
    bu = -0.45

    def slant(pts):
        return put([(bu + u - v * sk, v) for u, v in pts])

    def hseg(v0):
        u1, u2 = -w / 2 + t / 2 + g, w / 2 - t / 2 - g
        return [(u1, v0), (u1 + t / 2, v0 - t / 2), (u2 - t / 2, v0 - t / 2), (u2, v0), (u2 - t / 2, v0 + t / 2),
                (u1 + t / 2, v0 + t / 2)]

    def vseg(u0, v1, v2):
        v1, v2 = v1 + g, v2 - g
        return [(u0, v1), (u0 + t / 2, v1 + t / 2), (u0 + t / 2, v2 - t / 2), (u0, v2), (u0 - t / 2, v2 - t / 2),
                (u0 - t / 2, v1 + t / 2)]

    top, bot, ru, lu = -h / 2 + t / 2, h / 2 - t / 2, w / 2 - t / 2, -w / 2 + t / 2
    segs = {"A": hseg(top), "G": hseg(0), "D": hseg(bot), "B": vseg(ru, top, 0), "C": vseg(ru, 0, bot),
            "F": vseg(lu, top, 0), "E": vseg(lu, 0, bot)}
    on = SEGS.get(ch, "")
    for name, pts in segs.items():
        pn.poly(slant(pts), LIT if name in on else unlit, glow=name in on)
    (dx, dy), = slant([(w / 2 + 0.75, h / 2 - 0.45)])
    pn.circle(dx, dy, 0.45, LIT if dp else unlit, glow=255 if dp else 0)


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
            pn.rect(x - 0.38, cy - 3.7, x + 0.38, cy - 2.45, GOLD)
            pn.rect(x - 0.38, cy + 2.45, x + 0.38, cy + 3.7, GOLD)
    pn.rect(cx - 4.425, cy - 2.25, cx + 4.425, cy + 2.25, "#17171a", "#3a3a3f", 1, 0.2)
    for k in range(6):
        x = cx + (k - 2.5) * 1.27
        pn.rect(x - 0.4, cy - 1.25, x + 0.4, cy + 1.25, "#303034")
        ly = cy - 1.25 if on[k] else cy + 0.15
        pn.rect(x - 0.36, ly, x + 0.36, ly + 1.1, "#f2f2f2")


def display(pn, face, unlit, pads):
    for i, y in enumerate(DIGITS):
        digit(pn, DX, y, SHOW[i], i == DP_AT, face, unlit, pads)


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
    # Rev A's middle and right, left as routed
    kept = [(22.6, 9.5), (BW - 0.8, 9.5), (BW - 0.8, 62.5), (16.4, 62.5), (16.4, 26.6), (22.6, 26.6)]
    pn.d.polygon([pn.p(*q) for q in kept], outline="#b8e0c2", width=2 * SS)
    pn.text((16.4 + BW - 0.8) / 2, 44, "Rev A parts and routing\nkept as they are\n(U1, U2, U4, RF, power)", 15,
            "#cfeed7", anchor="mm")
    # new front-panel parts
    pn.rect(DRV[0] - 2.5, DRV[1] - 2.5, DRV[0] + 2.5, DRV[1] + 2.5, "#1d1d20", "#55555a", 1, 0.2)
    dip(pn, *DIP)
    display(pn, "#121214", "#3c3c40", True)
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
    pn.rect(BW + 6.0, 22.0, BW + 9.6, 70.6, "#1d1e21", "#3c3d42", 1, 1.8)                      # antenna
    pn.rect(BW + w, 64.6, BW + 6.5, 69.9, "#e2bd62", "#a8802e", 1, 0.4)                        # SMA
    pn.rect(-w - 1.4, 65.0, -w + 0.2, 66.8, "#d9d9d9", "#999", 1, 0.3)                         # TX/RX slide
    pn.rect(-w, -w, BW + w, BH + w, CASE, "#45474d", 2, 4.0)
    # wheel: its rim through a slot in the side
    dial(pn, *ENC)
    pn.rect(ENC[0] - 2.6, ENC[1] - 7.6, ENC[0] + 7.6, ENC[1] + 7.6, CASE)
    pn.d.line([pn.p(ENC[0] - 2.6, ENC[1] - 7.0), pn.p(ENC[0] - 2.6, ENC[1] + 7.0)], fill="#16171a", width=3 * SS)
    # display window
    pn.rect(DX - 7.2, DIGITS[0] - 5.0, DX + 7.0, DIGITS[-1] + 5.2, "#0b0b0d", "#4a4c52", 2, 1.0)
    display(pn, None, "#1b1b1e", False)
    pn.text(DX + 6.6, DIGITS[-1] + 5.6, "MHz", 12, "#9a9ca3", anchor="la")
    # DIP in a recess, status LED light pipe, ports in the end wall
    pn.rect(DIP[0] - 5.6, DIP[1] - 3.2, DIP[0] + 5.6, DIP[1] + 3.2, "#1a1b1e", "#4a4c52", 1, 0.6)
    dip(pn, *DIP, pads=False)
    pn.circle(43.3, 3.45, 1.1, "#7fe0a0", "#bff0cf", 1, glow=150)
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
    d.text((1380 * SS, 72 * SS), "Phone turned sideways, in a case (impression; no enclosure designed yet)",
           font=font(20, True), fill="#1f3a6d")

    a = Panel(img, glow, 350, 150)
    board_view(a)
    a.callout((DIP[0] + 4.4, DIP[1] - 1.5), (BW + 13, -1.5),
              "Power DIP, Diptronics DHN-06-V\nin SW3's place, levers up")
    a.callout((44.0, 3.45), (BW + 13, 5.0), "D1 status LED (as Rev A)", 15, "#666")
    a.callout((DRV[0] + 2.5, DRV[1]), (BW + 13, 11.5),
              "LED driver IS31FL3236A\n(5 × 5 mm), roughly here")
    a.callout((0.6, DIGITS[0]), (-6.0, DIGITS[0] + 2),
              "Station display\n4 × GS3011AW-B, 0.3\" white,\nturned a quarter,\nwhere RV1 and RV2 were\n"
              "31.3 × 15.5 mm, 3.75 mm tall")
    a.callout((ENC[0] - 3.4, ENC[1] - 2.0), (-6.0, ENC[1] - 4.0),
              "Tuning wheel, SIQ-02FVS3\nwhere RV3 was\n3.4 mm past the edge\nturn + push in")
    a.callout((0.4, 64.0), (-6.0, 62.0), "SW1 TX / RX (as Rev A)", 15, "#666")
    a.callout((12.8, 69.0), (-6.0, 70.5), "SW2 BOOT (as Rev A)", 15, "#666")
    a.callout((BW / 2, 66.5), (BW + 13, 60.0), "J1 USB-C (as Rev A)", 15, "#666")
    a.callout((50.0, 68.5), (BW + 13, 66.0), "J2 SMA (as Rev A)", 15, "#666")

    b = Panel(img, glow, 1480, 330, sideways=True)
    unit_view(b)
    b.callout((ENC[0] - 3.3, ENC[1]), (-12.0, ENC[1]), "Turn to tune (15 clicks a turn),\npush the wheel in to select",
              17)
    b.callout((DX - 7.2, DY), (-12.0, DY), "Station in MHz", 17)
    b.callout((DIP[0], DIP[1] - 3.2), (DIP[0], -6.0), "TX power DIP\n(bench setting)", 17)
    b.callout((BW + 7.8, 46.0), (BW + 13, 46.0), "antenna on J2 (SMA)", 17)
    b.callout((-2.4, 65.9), (-2.4, 76.0), "TX / RX", 17)
    b.callout((BW / 2, BH + 1.6), (BW / 2, BH + 9.0), "USB-C", 17)

    glow = glow.filter(ImageFilter.GaussianBlur(SS * K * 0.45))
    halo = glow.point(lambda v: int(v * 0.5))
    img = ImageChops.add(img, Image.merge("RGB", (halo, halo, halo)))
    d = ImageDraw.Draw(img)
    notes = [
        "Heights above the board: SMA 9.5 mm (sets the case height) · wheel 4.0 · digits 3.75 · USB-C 3.26 · DIP 1.6.",
        "All new parts take Rev A's left column and SW3's spot. The middle and right of the board (U1, U2, U4, the RF "
        "chain, power, USB) keep their Rev A placement and routing.",
        "Freed by the change: RV1–RV3, their wiper lines and caps C39–C41. To move: the 3V3/VBUS feed at x 13–16 mm "
        "(under the display's inner pad row) and TP2/TP3 (where the driver goes).",
        "The digits read with the phone turned sideways, its left edge down; held upright they read side-on.",
    ]
    for i, s in enumerate(notes):
        d.text((30 * SS, (1170 + i * 32) * SS), s, font=font(19), fill="#333")
    img = img.resize((W, H), Image.LANCZOS)
    img.save(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main()
