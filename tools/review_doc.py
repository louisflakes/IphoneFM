"""The Rev A design review, for an outside engineer: a short PDF (overview, key numbers, main parts, fabrication,
firmware plan, each signal chain drawn on the schematic with its datasheet references, and what to check).
Pictures are made here: the block diagram, and schematic crops with each chain's parts outlined and numbered in the
order the signal passes them. The PDF is printed from HTML by Chrome.
Usage (from the repository root): python tools/review_doc.py [--package]  (--package also fills review/rev-a/)"""
import html
import io
import os
import subprocess
import sys

import cairosvg
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "tools")
from sch_boxes import boxes

K = "C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe"
CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe"
OUT = "design/rev-a/review/design-review"
PDF = "design/rev-a/review/IphoneFM-RevA-design-review.pdf"
PX = 9                                          # schematic pixels per millimetre
FONT = "C:/Windows/Fonts/arialbd.ttf"

# ---- the chains: (title, colour, [(step, label, [refs])]) ----
CHAINS = {
    "power": ("Power and USB", "#1f6fd1", [
        (1, "J1 USB-C", ["J1"]), (2, "R1/R2 5.1 kΩ Rd, D3/D4 ESD", ["R1", "R2", "D3", "D4"]),
        (3, "U6 USB ESD", ["U6"]), (4, "U3 3.3 V LDO", ["U3", "C1", "C2"])]),
    "clock": ("Reference clock", "#8a3ffc", [
        (1, "Y2 20 MHz XO", ["Y2", "C11", "C12"]), (2, "R4 to U1 PH0", ["R4"])]),
    "tx": ("Transmit", "#d12f1f", [
        (1, "U2 LMX2571", ["U2"]), (2, "Loop filter C24 R5 C25", ["C24", "R5", "C25"]),
        (3, "C26 DC block", ["C26"]), (4, "U7 PE43711", ["U7"]), (5, "SW3 power DIP", ["SW3"]),
        (6, "FL1 low-pass", ["C28", "L2", "C29", "L3", "C30"]), (7, "U5 PE42421", ["U5"]),
        (8, "D5 ESD", ["D5"]), (9, "J2 SMA", ["J2"])]),
    "rx": ("Receive", "#0a8a4a", [
        (1, "C34 coupling", ["C34"]), (2, "L1 match", ["L1"]), (3, "FB1/C35 filter", ["FB1", "C35"]),
        (4, "U4 Si4705", ["U4"]), (5, "R22–R24 I²S to U1", ["R22", "R23", "R24"])]),
    "mcu": ("MCU", "#b06a00", [
        (1, "U1 STM32U535", ["U1"]), (2, "R6–R8 FSK I²S", ["R6", "R7", "R8"]),
        (3, "FB2 VDDA filter", ["FB2", "C7", "C8"])]),
    "ui_a": ("Controls", "#5a5a5a", [(1, "RV1–RV3 wheels", ["RV1", "RV2", "RV3"])]),
    "ui_b": ("Controls", "#5a5a5a", [(2, "SW1 TX/RX slider", ["SW1", "R18"]), (3, "SW2 BOOT", ["SW2"]),
                                     (4, "D1 RGB LED", ["D1", "R25", "R26", "R27"])]),
    "ui": ("Controls", "#5a5a5a", [
        (1, "RV1–RV3 wheels", ["RV1", "RV2", "RV3"]), (2, "SW1 TX/RX slider", ["SW1", "R18"]),
        (3, "SW2 BOOT", ["SW2"]), (4, "D1 RGB LED", ["D1", "R25", "R26", "R27"])]),
}


def schematic_png():
    os.makedirs(OUT, exist_ok=True)
    subprocess.run([K, "sch", "export", "svg", "--exclude-drawing-sheet", "-o", OUT + "/",
                    "kicad/rev-a/IphoneFM.kicad_sch"], check=True, capture_output=True)
    svg = os.path.join(OUT, "IphoneFM.svg")
    data = cairosvg.svg2png(url=svg, output_width=int(594.0044 * PX), background_color="white")
    os.remove(svg)
    return Image.open(io.BytesIO(data)).convert("RGB")


def crop(sheet, box, name, chains, margin=5, extra=None):
    """Crop the sheet to the parts of the given chains (plus `extra` mm box), outline them and number the steps."""
    b = boxes()
    sel = [(c, s, lab, r) for c in chains for s, lab, refs in CHAINS[c][2] for r in refs]
    xs = [v for _, _, _, r in sel for v in (b[r][0], b[r][2])]
    ys = [v for _, _, _, r in sel for v in (b[r][1], b[r][3])]
    x0, y0, x1, y1 = min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin
    if extra:
        x0, y0, x1, y1 = min(x0, extra[0]), min(y0, extra[1]), max(x1, extra[2]), max(y1, extra[3])
    im = sheet.crop((int(x0 * PX), int(y0 * PX), int(x1 * PX), int(y1 * PX))).copy()
    d = ImageDraw.Draw(im, "RGBA")
    f = ImageFont.truetype(FONT, int(PX * 2.6))
    done = set()
    for c, s, lab, r in sel:
        col = CHAINS[c][1]
        rx0, ry0, rx1, ry1 = ((b[r][0] - x0 - 1) * PX, (b[r][1] - y0 - 1) * PX,
                              (b[r][2] - x0 + 1) * PX, (b[r][3] - y0 + 1) * PX)
        rgb = tuple(int(col[i:i + 2], 16) for i in (1, 3, 5))
        d.rounded_rectangle((rx0, ry0, rx1, ry1), radius=PX, outline=rgb + (255,), width=max(3, PX // 3),
                            fill=rgb + (28,))
        if (c, s) not in done:                    # one numbered badge per step, at its first part
            done.add((c, s))
            rad = PX * 2.2
            cx, cy = rx0, ry0
            d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=rgb + (255,))
            d.text((cx, cy), str(s), font=f, fill="white", anchor="mm")
    path = os.path.join(OUT, name + ".png")
    im.save(path)
    return path


def side_by_side(a, b, name):
    """Two crops next to each other at the same height."""
    ia, ib = Image.open(a), Image.open(b)
    h = max(ia.height, ib.height)
    im = Image.new("RGB", (ia.width + ib.width + 4 * PX, h), "white")
    im.paste(ia, (0, (h - ia.height) // 2))
    im.paste(ib, (ia.width + 4 * PX, (h - ib.height) // 2))
    path = os.path.join(OUT, name + ".png")
    im.save(path)
    return path


def block_diagram():
    fig, ax = plt.subplots(figsize=(10.6, 3.2))
    ax.set_xlim(0, 112.5)
    ax.set_ylim(0, 32)
    ax.axis("off")

    def node(x, y, w, h, ref, part, col):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.8", fc=col + "18",
                                    ec=col, lw=1.4))
        ax.text(x + w / 2, y + h * 0.64, ref, ha="center", va="center", fontsize=8.6, fontweight="bold", color=col)
        ax.text(x + w / 2, y + h * 0.28, part, ha="center", va="center", fontsize=6.8, color="#222")

    def arrow(a, b, col="#444", text=None, style="-|>", rad=0.0):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=9, lw=1.1, color=col,
                                     connectionstyle=f"arc3,rad={rad}"))
        if text:
            ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.9, text, ha="center", va="bottom", fontsize=6.2,
                    color=col)

    P, C, T, R, M, U = (CHAINS[k][1] for k in ("power", "clock", "tx", "rx", "mcu", "ui"))
    node(0.5, 13, 9, 7, "iPhone", "USB-C audio", "#333333")
    node(14, 13, 10, 7, "J1 + U6", "USB-C, ESD", P)
    node(14, 2, 10, 7, "U3", "3.3 V LDO", P)
    node(31, 11, 12, 11, "U1", "STM32U535\nMCU", M)
    node(31, 25, 12, 6.5, "Y2", "20 MHz XO", C)
    node(31, 0.8, 12, 7, "Controls", "wheels, slider,\nDIP, BOOT, LED", U)
    node(50, 23, 11, 7, "U2", "LMX2571\nsynthesizer", T)
    node(65, 23, 11, 7, "U7", "PE43711\nattenuator", T)
    node(80, 23, 10, 7, "FL1", "5-pole\nlow-pass", T)
    node(95, 13, 8.5, 7, "U5", "PE42421\nT/R switch", "#444444")
    node(106.5, 13, 5.5, 7, "J2", "SMA", "#444444")
    node(65, 3, 11, 7, "U4", "Si4705\nFM receiver", R)
    node(80, 3, 10, 7, "RX filter", "C34, L1,\nFB1, C35", R)

    arrow((9.5, 16.5), (14, 16.5), "#333", "USB")
    arrow((24, 16.5), (31, 16.5), P, "D+/D−")
    arrow((19, 13), (19, 9), P)
    ax.text(19.7, 11, "VBUS", fontsize=6.2, color=P, va="center")
    arrow((24, 6), (31, 12.5), P)
    ax.text(26.6, 10.2, "3V3", fontsize=6.2, color=P, ha="right")
    arrow((37, 25), (37, 22), C)
    arrow((43, 28.2), (50, 27), C, "20 MHz")
    arrow((43, 19), (50, 25), T)
    ax.text(46.8, 19.6, "FSK I²S\n+ SPI", fontsize=6.2, color=T, va="top")
    arrow((61, 26.5), (65, 26.5), T)
    arrow((76, 26.5), (80, 26.5), T)
    arrow((90, 25), (97, 20), T)
    ax.text(94.6, 23.2, "TX", fontsize=6.4, color=T)
    arrow((103.5, 16.5), (106.5, 16.5), "#444")
    arrow((97, 13), (90, 8.5), R)
    ax.text(94.8, 9.4, "RX", fontsize=6.4, color=R)
    arrow((80, 6.5), (76, 6.5), R)
    arrow((65, 7.5), (43, 13.5), R)
    ax.text(55, 11.3, "I²S audio, I²C", fontsize=6.2, color=R, ha="center")
    arrow((37, 7.8), (37, 11), U)
    ax.text(70.5, 21.8, "SW3 sets 0–31.5 dB", fontsize=6, color=T, ha="center", va="top")
    ax.text(99.25, 11.8, "SW1: TX or RX", fontsize=6, color="#444", ha="center", va="top")
    path = os.path.join(OUT, "block.png")
    fig.savefig(path, dpi=220, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return path


def esc(s):
    return html.escape(s, quote=False)


def main():
    sheet = schematic_png()
    img = {
        "block": block_diagram(),
        "power": crop(sheet, None, "chain-power", ["power"]),
        "clock": crop(sheet, None, "chain-clock", ["clock"]),
        "mcu": crop(sheet, None, "chain-mcu", ["mcu"]),
        "tx": crop(sheet, None, "chain-tx", ["tx"]),
        "rx": crop(sheet, None, "chain-rx", ["rx"]),
        "ui": side_by_side(crop(sheet, None, "chain-ui-a", ["ui_a"]), crop(sheet, None, "chain-ui-b", ["ui_b"]),
                           "chain-ui"),
    }
    src = open("tools/review_doc.html", encoding="utf-8").read()
    for k, v in img.items():
        src = src.replace("{{" + k + "}}", "file:///" + os.path.abspath(v).replace("\\", "/"))
    page = os.path.abspath(os.path.join(OUT, "review.html"))
    open(page, "w", encoding="utf-8").write(src)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={os.path.abspath(PDF)}", "file:///" + page.replace("\\", "/")],
                   check=True, capture_output=True)
    print("written", PDF)


if __name__ == "__main__":
    main()


# ---- the review folder in the repository ----
DATASHEETS = ["U6_USBLC6-2_ST_DS4260_Rev7.pdf", "D3-D4_TPD1E05U06_TI.pdf", "U3_AP2112_DS39724_Rev2-2.pdf",
              "U1_STM32U535_DS14217_Rev5.pdf", "U1_ST_AN2606_bootloader_Rev61.pdf", "XO_YXC_OT322520MJBA4SL.pdf",
              "PLL_TI_LMX2571_SNAS654A.pdf", "AN_TI_SNAA309_LMX2571_FSK.pdf", "ATT_pSemi_PE43711.pdf",
              "U5_PE42421_DOC-33214-1.03.pdf", "ESD_Semtech_RClamp0521PA_Rev4.pdf", "U4_Si4704-05-D60_Rev1.2.pdf",
              "U4_Skyworks_AN332_programming_guide.pdf", "U4_Skyworks_AN383_antenna_layout.pdf",
              "D1_XINGLIGHT_XL-1615RGBC-RF.pdf", "J1_HRO_TYPE-C-31-M-12.pdf", "J2_BAT_BWSMA-KWE-Z001.pdf",
              "POT_Alps_RK10J.pdf", "SW1_ShouHan_MSK12C02.pdf", "SW2-SW3_Panasonic_EVQP7_ANCTB21E.pdf",
              "SW_CK_TDP_series.pdf", "L_Murata_LQW18AN_JELF243A-0024.pdf", "FB_Murata_BLM15AG_ENFA0018.pdf",
              "USB_Type-C_R2.5_Mar2026.pdf", "Apple_Accessory_Design_Guidelines.pdf"]
REVIEW = "review/rev-a"


def package():
    """review/rev-a/: the PDF, schematic, JLC files, assembly drawing and board pictures, with a README linking the
    KiCad project and every datasheet the PDF cites (already in docs/datasheets/). Run tools/pcb_export.sh first."""
    import glob
    import shutil
    os.makedirs(REVIEW, exist_ok=True)
    shutil.copy(PDF, REVIEW)
    subprocess.run([K, "sch", "export", "pdf", "-o", REVIEW + "/IphoneFM-RevA-schematic.pdf",
                    "kicad/rev-a/IphoneFM.kicad_sch"], check=True, capture_output=True)
    for f in ("IphoneFM-RevA-gerbers.zip", "IphoneFM-RevA-BOM.csv", "IphoneFM-RevA-CPL.csv"):
        shutil.copy("kicad/rev-a/output/jlc/" + f, REVIEW)
    shutil.copy("kicad/rev-a/output/assembly/IphoneFM-RevA-assembly.pdf", REVIEW)
    shutil.copy("design/rev-a/review/phase8-gerber-top.png", REVIEW + "/IphoneFM-RevA-board-top.png")
    shutil.copy("design/rev-a/review/phase8-gerber-bottom.png", REVIEW + "/IphoneFM-RevA-board-bottom.png")
    links = []
    for name in DATASHEETS:
        src = glob.glob("docs/datasheets/**/" + name, recursive=True)
        if not src:
            sys.exit("datasheet not found: " + name)
        links.append(f"- [{name}](../../{src[0].replace(os.sep, '/')})")
    for src in sorted(glob.glob("docs/datasheets/analog-fm/basic/*.pdf")):
        links.append(f"- [{os.path.basename(src)}](../../{src.replace(os.sep, '/')})")
    readme = f"""# IphoneFM Rev A — design review

Start with **[IphoneFM-RevA-design-review.pdf](IphoneFM-RevA-design-review.pdf)** (4 pages). It cites datasheet pages;
the documents are linked below.

| File | What it is |
|---|---|
| [IphoneFM-RevA-design-review.pdf](IphoneFM-RevA-design-review.pdf) | Overview, key numbers, main parts, each signal chain on the schematic, what to check |
| [IphoneFM-RevA-schematic.pdf](IphoneFM-RevA-schematic.pdf) | The schematic, one A2 sheet |
| [IphoneFM-RevA-gerbers.zip](IphoneFM-RevA-gerbers.zip) | Gerbers and drill files of the JLC panel (one board in rails) |
| [IphoneFM-RevA-BOM.csv](IphoneFM-RevA-BOM.csv), [IphoneFM-RevA-CPL.csv](IphoneFM-RevA-CPL.csv) | Parts list and placement file in JLC's format |
| [IphoneFM-RevA-assembly.pdf](IphoneFM-RevA-assembly.pdf) | Assembly drawing, every reference, both sides |
| [IphoneFM-RevA-board-top.png](IphoneFM-RevA-board-top.png), [IphoneFM-RevA-board-bottom.png](IphoneFM-RevA-board-bottom.png) | The board as built, drawn from the Gerbers |
| [kicad/rev-a/](../../kicad/rev-a/) | KiCad 10 project (schematic, board, rules, footprints) |

## Datasheets cited

{chr(10).join(links)}

Generated by `tools/review_doc.py --package`.
"""
    open(REVIEW + "/README.md", "w", encoding="utf-8").write(readme)
    print("written", REVIEW, len(os.listdir(REVIEW)), "files")


if __name__ == "__main__" and "--package" in sys.argv:
    package()
