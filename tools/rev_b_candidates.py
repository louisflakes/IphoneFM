"""Rev B front panel: the candidate comparison sheet (tuning control, station display, power DIP switch), drawn from
JLC's product photos. Usage: python tools/rev_b_candidates.py PHOTO_DIR  (photos named <LCSC code>.jpg)"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = "design/rev-b/front-panel-candidates.png"
SECTIONS = [
    ("Tuning control", [
        ("C2925423", "A  Edge thumbwheel encoder", "Mitsumi SIQ-02FVS3",
         "Flat 14 mm knurled wheel, SMD. Overhangs the edge like today's dials, so the stack stays thin.",
         "1,350 (+3 makers)", "$3.19", True),
        ("C470754", "B  Knob encoder", "Alps EC11E15244B2",
         "30 detents + push switch. Knob on the face: clearest to use, adds ~15–20 mm height + a knob cap.",
         "4,509", "$2.39", False),
        ("C143790", "C  Knob encoder, panel nut", "Bourns PEC11R-4215F-S0024",
         "24 detents + push switch, threaded bushing to bolt through an enclosure lid.", "4,321", "$2.37", False)]),
    ("Station display", [
        ("C22462661", "A  4 × 0.3\" white digits (SMD)", "Guangcai GS3011AW-B",
         "Four single digits, black face, ~31 mm wide, 3.75 mm thin. Machine-placed; static drive (no flicker).",
         "818", "$0.49 each", True),
        ("C2913068", "B  0.36\" white, 4-digit module", "Sunlight SLR0364DWC1BD",
         "One 30 × 14 mm block, bigger digits. Through-hole, 7.2 mm tall.", "931", "$1.15", False),
        ("C109199", "C  0.28\" red, 4-digit module", "ARKLED SR440281N",
         "Classic red LED look, 32 × 10 mm, 5.8 mm tall. Through-hole.", "2,388", "$0.50", False)]),
    ("Power DIP switch (top lever, 1.27 mm, SMD)", [
        ("C224997", "A  Diptronics DHN-06-V", "Diptronics", "Black body, white levers. Deepest stock.",
         "14,336", "$0.85", True),
        ("C3293146", "B  Kangshen DSHP06TSGER", "Kangshen",
         "Amber see-through body (the in-stock fallback noted in Rev A).", "12,494", "$0.62", False),
        ("C319048", "C  XKB DSHP06TS-S", "XKB", "Black body, amber levers.", "9,548", "$0.76", False)]),
]


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", size)


def main(photos):
    W, CARD, PH = 1500, 470, 240
    img = Image.new("RGB", (W, 90 + len(SECTIONS) * (70 + PH + 190)), "white")
    d = ImageDraw.Draw(img)
    d.text((30, 24), "Rev B front panel — candidates (all JLC-stocked; the A picks datasheet-checked)", font=font(34, True),
           fill="#111")
    y = 90
    for title, cards in SECTIONS:
        d.text((30, y), title, font=font(28, True), fill="#1f3a6d")
        y += 50
        for i, (code, name, mpn, desc, stock, price, rec) in enumerate(cards):
            x = 30 + i * (CARD + 20)
            d.rounded_rectangle((x, y, x + CARD, y + PH + 180), radius=14, outline="#1a8f4c" if rec else "#cccccc",
                                width=5 if rec else 2, fill="#fbfbfb")
            img.paste(Image.open(os.path.join(photos, code + ".jpg")).convert("RGB").resize((PH, PH)),
                      (x + (CARD - PH) // 2, y + 10))
            if rec:
                d.rounded_rectangle((x + 12, y + 12, x + 170, y + 48), radius=8, fill="#1a8f4c")
                d.text((x + 22, y + 15), "suggested", font=font(22, True), fill="white")
            ty = y + PH + 18
            d.text((x + 14, ty), name, font=font(22, True), fill="#111")
            d.text((x + 14, ty + 30), mpn + "  ·  " + code, font=font(18), fill="#555")
            ty += 58
            line = ""
            for word in desc.split():
                t = (line + " " + word).strip()
                if d.textlength(t, font=font(19)) > CARD - 28:
                    d.text((x + 14, ty), line, font=font(19), fill="#222")
                    ty, line = ty + 25, word
                else:
                    line = t
            d.text((x + 14, ty), line, font=font(19), fill="#222")
            d.text((x + 14, y + PH + 150), f"JLC stock {stock}   ·   {price}", font=font(19, True), fill="#1f3a6d")
        y += PH + 210
    img.save(OUT)
    print("written", OUT)


if __name__ == "__main__":
    main(sys.argv[1])
