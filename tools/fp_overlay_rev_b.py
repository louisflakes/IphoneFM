"""Step B3.2 overlays (design/rev-b/footprint-overlays.png): to-scale: footprint pads filled (blue), maker's pads outlined on top (red), body grey, silkscreen black."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
from kicadcheck import sexpr, kids, kid

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kicad", "rev-b", "IphoneFM.pretty") + os.sep
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "design", "rev-b", "footprint-overlays.png")


def rot(pts, ang, cx, cy):
    a = math.radians(ang)
    return [(cx + x * math.cos(a) + y * math.sin(a), cy - x * math.sin(a) + y * math.cos(a)) for x, y in pts]


def rect_pts(w, h, chamfer=None, c=0):
    pts = {"top_left": (-w / 2, -h / 2), "top_right": (w / 2, -h / 2), "bottom_right": (w / 2, h / 2), "bottom_left": (-w / 2, h / 2)}
    out = []
    for k, (x, y) in pts.items():
        if k == chamfer:
            sx, sy = (1 if x > 0 else -1), (1 if y > 0 else -1)
            out += [(x, y - sy * c), (x - sx * c, y)] if k in ("top_left", "bottom_right") else [(x - sx * c, y), (x, y - sy * c)]
        else:
            out.append((x, y))
    return out


def fp_pads(name):
    fp = sexpr(open(LIB + name + ".kicad_mod", encoding="utf-8").read())
    pads, silk = [], []
    for p in kids(fp, "pad"):
        at = kid(p, "at"); x, y = float(at[1]), float(at[2]); a = float(at[3]) if len(at) > 3 else 0
        w, h = map(float, kid(p, "size")[1:3])
        layers = kid(p, "layers")[1:]
        if p[2] == "np_thru_hole":
            pads.append(("hole", x, y, w)); continue
        if "F.Cu" not in layers:
            continue
        ch = kid(p, "chamfer")
        c = float(kid(p, "chamfer_ratio")[1]) * min(w, h) if ch else 0
        pads.append(("poly", p[1], rot(rect_pts(w, h, ch[1] if ch else None, c), a, x, y)))
    for g in kids(fp, "fp_line"):
        if kid(g, "layer")[1] == "F.SilkS":
            silk.append([tuple(map(float, kid(g, k)[1:3])) for k in ("start", "end")])
    for g in kids(fp, "fp_arc"):
        if kid(g, "layer")[1] == "F.SilkS":
            silk.append([tuple(map(float, kid(g, k)[1:3])) for k in ("start", "mid", "end")])
    dots = [(tuple(map(float, kid(g, "center")[1:3]))) for g in kids(fp, "fp_circle") if kid(g, "layer")[1] == "F.SilkS"]
    return pads, silk, dots


def draw(ax, name, maker, body, title, rows, lim, extra=None):
    pads, silk, dots = fp_pads(name)
    for b in body:
        ax.add_patch(b)
    for p in pads:
        if p[0] == "hole":
            ax.add_patch(Circle((p[1], p[2]), p[3] / 2, fc="white", ec="#1f4e9c", lw=1.2, hatch="////"))
        else:
            ax.add_patch(Polygon(p[2], closed=True, fc="#6f9fe0", ec="#1f4e9c", lw=0.6, alpha=0.85))
            xs = [q[0] for q in p[2]]; ys = [q[1] for q in p[2]]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            ax.text(cx, cy, p[1], ha="center", va="center", fontsize=6 if len(pads) > 20 else 8, color="#0b2350")
    for m in maker:
        ax.add_patch(m)
    for s in silk:
        ax.plot([q[0] for q in s], [q[1] for q in s], color="black", lw=1.4, solid_capstyle="round")
    for d in dots:
        ax.add_patch(Circle(d, 0.275, fc="black"))
    if extra:
        extra(ax)
    ax.set_xlim(-lim[0], lim[0]); ax.set_ylim(lim[1], -lim[1]) if len(lim) == 2 else ax.set_ylim(lim[3], lim[2])
    ax.set_aspect("equal"); ax.grid(True, lw=0.3, alpha=0.5); ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel("mm"); ax.tick_params(labelsize=7)
    t = ax.table(cellText=rows, colLabels=["", "Ours", "Maker"], loc="right", bbox=[1.08, 0.05, 1.55, 0.9], cellLoc="left",
                 colWidths=[0.22, 0.42, 0.36])
    t.auto_set_font_size(False); t.set_fontsize(8.5)


def mk(x, y, w, h, ang=0, ls="-", col="red"):
    pts = rot(rect_pts(w, h), ang, x, y)
    return Polygon(pts, closed=True, fill=False, ec=col, lw=1.3, ls=ls)


def grey(*pts):
    return Polygon(pts, closed=True, fc="#d9d9d9", ec="#9a9a9a", lw=0.8)


def rounded_corner_pad(x0, x1, y0, y1, corner, r=0.125, n=8):
    """Rectangle with one rounded corner (corner = (sx, sy) which corner)"""
    cxs, cys = corner
    verts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = []
    for j, (px, py) in enumerate(verts):
        if px == (x1 if cxs > 0 else x0) and py == (y1 if cys > 0 else y0):
            ccx, ccy = px - cxs * r, py - cys * r
            prev_shares_y = verts[j - 1][1] == py
            ts = [i / n * math.pi / 2 for i in range(n + 1)]
            for t in (reversed(ts) if prev_shares_y else ts):
                pts.append((ccx + cxs * r * math.cos(t), ccy + cys * r * math.sin(t)))
        else:
            pts.append((px, py))
    return Polygon(pts, closed=True, fill=False, ec="red", lw=1.3)


def u8(ax):
    maker = []
    for k in range(1, 45):
        side, i = divmod(k - 1, 11)
        t = -2.0 + 0.4 * i
        corner = i in (0, 10)
        inner = 2.2 if corner else 2.0
        if k in (17, 39):
            inner = 1.225
        if side == 0: x0, x1, y0, y1 = -3.0, -inner, t - 0.125, t + 0.125
        elif side == 1: x0, x1, y0, y1 = t - 0.125, t + 0.125, inner, 3.0
        elif side == 2: x0, x1, y0, y1 = inner, 3.0, -t - 0.125, -t + 0.125
        else: x0, x1, y0, y1 = -t - 0.125, -t + 0.125, -3.0, -inner
        if corner:
            cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
            sx, sy = (1 if cx_ > 0 else -1), (1 if cy_ > 0 else -1)
            horiz = side in (0, 2)
            c = (-sx, sy) if horiz else (sx, -sy)
            maker.append(rounded_corner_pad(x0, x1, y0, y1, c))
        else:
            maker.append(Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True, fill=False, ec="red", lw=1.3))
    maker.append(mk(0, 0, 2.45, 2.45))
    body = [grey((-2.5, -2.5), (2.5, -2.5), (2.5, 2.5), (-2.5, 2.5))]
    rows = [["Pads", "44 + centre 45", "44 + centre (Lumissil p16)"], ["Pitch", "0.40", "0.40"],
            ["Pad size", "0.25 x 1.00 (corners 0.80)", "0.25 x 1.00 (corners 0.80)"],
            ["Pad rows", "2.0 to 3.0 mm out (4.0 inside, 6.0 outside)", "4.0 inside, 6.0 outside"],
            ["Corner pads", "facing corners chamfered 0.125; 0.21 apart", "facing corners rounded R0.125; 0.20 apart"],
            ["Centre pad", "2.45 sq, joined to 17 and 39", "2.45 sq, joined to 17 and 39 (R0.1 fillets)"],
            ["Paste", "pads 1:1; centre 4 x 0.99 sq (65%)", "not given"],
            ["Body / pin 1", "5.0 x 5.0; pin 1 top left, CCW", "5.00 x 5.00 (p14); pin 1 top left"]]
    draw(ax, "Lumissil_QFN-44-1EP_5x5mm_P0.4mm_EP2.45x2.45mm", maker, body, "U8  IS31FL3236A  QFN-44 5x5, 0.4 mm", rows, (4.2, 4.2))


def ds(ax):
    maker = [mk(-3.0 + 1.5 * i, y, 1.0, 3.0) for i in range(5) for y in (-6.25, 6.25)]
    body = [grey((-3.65, -6), (3.65, -6), (3.65, 6), (-3.65, 6))]
    rows = [["Pads", "10", "10 (Guangcai p5)"], ["Pitch", "1.50", "1.5 x 4 = 6.00"], ["Pad size", "1.00 x 3.00", "1.00 x 3.00"],
            ["Rows", "9.50 inside, 12.50 centres, 15.50 outside", "9.50 / 12.50 / 15.50"],
            ["Numbering", "1-5 bottom L to R, 6-10 top R to L", "same (p3 top view)"], ["Paste", "1:1", "not given"],
            ["Body", "7.30 x 12.00", "7.30 x 12.00 (p2)"]]
    draw(ax, "LED_7Segment_Guangcai_GS3011_7.3x12mm_P1.5mm", maker, body, "DS1-DS4  GS3011AW-B  0.3 in digit", rows, (5.0, 9.0))


def sw4(ax):
    maker = [mk(x, 7.7, 1.3, 1.2) for x in (-4, -1.475, 1.475, 4)]
    maker += [mk(x, y, 1.2, 1.3) for x in (-5.4, 5.4) for y in (1.3, 5.4)]
    rc = 4.6
    maker += [mk(s * rc / math.sqrt(2), -rc / math.sqrt(2), 1.2, 0.85, 45 if s > 0 else 135) for s in (1, -1)]
    maker += [Circle((x, 4.5), 0.8, fill=False, ec="red", lw=1.3) for x in (-3, 3)]
    lc = 4.0  # LCSC's centres
    maker += [mk(s * lc / math.sqrt(2), -lc / math.sqrt(2), 1.2, 0.85, 45 if s > 0 else 135, ls="--", col="#e08a00") for s in (1, -1)]
    body = [Circle((0, 0), 7.25, fc="#ececec", ec="#9a9a9a", lw=0.8), grey((-5.15, 0), (5.15, 0), (5.15, 7.25), (-5.15, 7.25))]
    rows = [["Terminals 1-4 (A S C B)", "1.3 x 1.2 at x -4, -1.475, 1.475, 4; y 7.1-8.3", "same (Mitsumi p3)"],
            ["Side tabs 5-8", "1.2 x 1.3, 9.6 apart inside, y 1.3 / 5.4", "same"],
            ["Angled tabs 9, 10", "0.85 x 1.2 at 45 deg, 4.0-5.2 from centre", "same (PDF vectors: centres 4.60)"],
            ["Holes", "2 x 1.6 unplated, 6 apart, y 4.5", "2 x 1.6 +0.05/0"],
            ["Paste", "1:1", "150 um stencil, 100%"],
            ["LCSC footprint (orange)", "angled tabs' centres at 4.0", "differs from Mitsumi by 0.6 mm"]]
    draw(ax, "RotaryEncoder_Switch_Mitsumi_SIQ-02FVS3", maker, body, "SW4  SIQ-02FVS3  push-wheel encoder", rows, (8.0, -8.0, 9.6, -7.6)[:2] + (-7.8, 9.6) if False else (8.0, 9.6, -7.8, 9.6))


def sw3(ax):
    maker = [mk(x, -3.175 + 1.27 * i, 1.25, 0.76) for x in (-3.075, 3.075) for i in range(6)]
    body = [grey((-2.25, -4.425), (2.25, -4.425), (2.25, 4.425), (-2.25, 4.425))]
    rows = [["Pads", "12 (KiCad's Omron A6H-6101)", "12 (Diptronics p41)"], ["Pitch", "1.27", "1.27"],
            ["Pad size", "1.25 x 0.76", "1.25 x 0.76"], ["Rows", "4.90 inside, 7.40 outside", "4.90 / 7.40"],
            ["Numbering", "1-6 one row, 7-12 back; switch n = n, 13-n", "not numbered; standard DIP"],
            ["Body", "8.85 x 4.50", "8.85 x 4.50"]]
    draw(ax, "SW_DIP_SPSTx06_Slide_Diptronics_DHN-06_W6.15mm_P1.27mm", maker, body, "SW3  DHN-06-V  6-way DIP", rows, (5.0, 5.6))


fig, axs = plt.subplots(4, 1, figsize=(16, 30))
for f_, ax in zip((u8, ds, sw4, sw3), axs):
    f_(ax)
fig.text(0.01, 0.995, "Rev B footprints, to scale (grid 1 mm). Blue fill: our copper. Red outline: the maker's recommended pads.\n"
         "Grey: body. Black: silkscreen after trimming (the dot marks pin 1).", fontsize=13, va="top")
plt.subplots_adjust(left=0.04, right=0.36, top=0.97, bottom=0.02, hspace=0.18)
plt.savefig(OUT, dpi=110)
print(OUT)
