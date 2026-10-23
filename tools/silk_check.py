"""Step 2.4 check: for each Rev A footprint, the silkscreen line widths and the closest any silkscreen ink comes to a
pad's copper, against kicad/rev-a/fab-rules.md (lines >= 0.25 mm, ink >= 0.20 mm from pads; JLC's own minimums 0.15).
Reference text is reported separately (its stroke rule is 0.15 mm). With --render DIR it also draws each footprint
(pads, body on the fab layer, silkscreen at its real width) into DIR as PNGs, six to a sheet.
Run from the repository root: python tools/silk_check.py [--render DIR]"""
import math
import sys

sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid
from rev_a_footprints import project_map

LINE_MIN, GAP_MIN = 0.25, 0.20


def rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def pad_shapes(fp):
    out = []
    for p in kids(fp, "pad"):
        at = kid(p, "at")
        x, y = float(at[1]), float(at[2])
        r = float(at[3]) if len(at) > 3 else 0.0
        w, h = map(float, kid(p, "size")[1:3])
        if p[2] == "np_thru_hole" and not any(l in ("*.Cu", "F.Cu") for l in kid(p, "layers")[1:]):
            continue
        out.append((p[1], p[3], x, y, r, w, h, p[2]))
    return out


def dist_to_pad(px, py, pad):
    _, shape, x, y, r, w, h, _ = pad
    lx, ly = rot(px - x, py - y, r)  # into the pad's own frame (KiCad angles are counter-clockwise, y down)
    if shape == "circle":
        return math.hypot(lx, ly) - w / 2
    if shape == "oval":
        if w >= h:
            dx = max(abs(lx) - (w - h) / 2, 0)
            return math.hypot(dx, ly) - h / 2
        dy = max(abs(ly) - (h - w) / 2, 0)
        return math.hypot(lx, dy) - w / 2
    dx, dy = abs(lx) - w / 2, abs(ly) - h / 2  # rect, roundrect (corners treated as square: slightly pessimistic)
    return math.hypot(max(dx, 0), max(dy, 0)) + min(max(dx, dy), 0)


def arc_points(s, m, e):
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return [s, e]
    ux = ((x1 ** 2 + y1 ** 2) * (y2 - y3) + (x2 ** 2 + y2 ** 2) * (y3 - y1) + (x3 ** 2 + y3 ** 2) * (y1 - y2)) / d
    uy = ((x1 ** 2 + y1 ** 2) * (x3 - x2) + (x2 ** 2 + y2 ** 2) * (x1 - x3) + (x3 ** 2 + y3 ** 2) * (x2 - x1)) / d
    rr = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(p[1] - uy, p[0] - ux) for p in (s, m, e))
    sweep = (a3 - a1) % (2 * math.pi)
    if (a2 - a1) % (2 * math.pi) > sweep:
        sweep -= 2 * math.pi
    n = max(8, int(abs(sweep) * rr / 0.05))
    return [(ux + rr * math.cos(a1 + sweep * i / n), uy + rr * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]


def silk_items(fp):
    """Each silkscreen graphic as (kind, width, polyline points, filled)."""
    out = []
    for g in fp[1:]:
        if not isinstance(g, list) or g[0] not in ("fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"):
            continue
        if kid(g, "layer")[1] != "F.SilkS":
            continue
        st = kid(g, "stroke")
        w = float(kid(st, "width")[1]) if st else float(kid(g, "width")[1])
        fill = kid(g, "fill")
        filled = bool(fill) and fill[1] in ("yes", "solid")
        pt = lambda k: tuple(map(float, kid(g, k)[1:3]))
        if g[0] == "fp_line":
            pts = [pt("start"), pt("end")]
        elif g[0] == "fp_rect":
            (x1, y1), (x2, y2) = pt("start"), pt("end")
            pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
        elif g[0] == "fp_circle":
            (cx, cy), (ex, ey) = pt("center"), pt("end")
            rr = math.hypot(ex - cx, ey - cy)
            pts = [(cx + rr * math.cos(t / 90 * math.pi), cy + rr * math.sin(t / 90 * math.pi)) for t in range(181)]
        elif g[0] == "fp_arc":
            pts = arc_points(pt("start"), pt("mid"), pt("end"))
        else:
            pts = [tuple(map(float, x[1:3])) for x in kid(g, "pts")[1:]]
            pts.append(pts[0])
        out.append((g[0], w, pts, filled))
    return out


def sample(pts, step=0.01):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / step))
        for i in range(n + 1):
            yield x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n


def check(path):
    fp = sexpr(open(path + ".kicad_mod", encoding="utf-8").read())
    pads, items = pad_shapes(fp), silk_items(fp)
    widths = sorted({w for _, w, _, _ in items})
    gap = math.inf
    for kind, w, pts, filled in items:
        for px, py in sample(pts):
            for pad in pads:
                gap = min(gap, dist_to_pad(px, py, pad) - w / 2)
    ref = [t for t in kids(fp, "property") if t[1] == "Reference"]
    ref_layer = kid(ref[0], "layer")[1] if ref else None
    return fp, pads, items, widths, gap, ref_layer


def render(results, outdir):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("arial.ttf", 20)
    small = ImageFont.truetype("arial.ttf", 17)
    names = list(results)
    for sheet in range(0, len(names), 6):
        im = Image.new("RGB", (1800, 1260), "white")
        d = ImageDraw.Draw(im)
        for i, name in enumerate(names[sheet:sheet + 6]):
            fp, pads, items, widths, gap, refs = results[name]
            ox, oy = (i % 3) * 600, (i // 3) * 630
            xs, ys = [], []
            for _, _, x, y, r, w, h, _ in pads:
                xs += [x - max(w, h) / 2, x + max(w, h) / 2]; ys += [y - max(w, h) / 2, y + max(w, h) / 2]
            for _, _, pts, _ in items:
                xs += [p[0] for p in pts]; ys += [p[1] for p in pts]
            span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
            k = min(440 / span, 160)
            cx, cy = ox + 300 - (max(xs) + min(xs)) / 2 * k, oy + 300 - (max(ys) + min(ys)) / 2 * k
            P = lambda x, y: (cx + x * k, cy + y * k)
            for g in fp[1:]:
                if isinstance(g, list) and g[0] in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc") and kid(g, "layer")[1] == "F.Fab":
                    for kind, w, pts, _ in silk_items([None, [g[0]] + [x if not (isinstance(x, list) and x[0] == "layer") else ["layer", "F.SilkS"] for x in g[1:]]]):
                        d.line([P(*p) for p in pts], fill=(150, 150, 150), width=2)
            for num, shape, x, y, r, w, h, kind in pads:
                col = (90, 90, 90) if kind == "np_thru_hole" else (200, 60, 120)
                corners = [rot(sx * w / 2, sy * h / 2, -r) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                if shape in ("circle",):
                    d.ellipse([*P(x - w / 2, y - w / 2), *P(x + w / 2, y + w / 2)], fill=col)
                else:
                    d.polygon([P(x + c[0], y + c[1]) for c in corners], fill=col)
            for kind, w, pts, filled in items:
                if filled:
                    d.polygon([P(*p) for p in pts], fill=(220, 180, 0))
                d.line([P(*p) for p in pts], fill=(220, 180, 0), width=max(1, int(w * k)), joint="curve")
            ok_w = not widths or min(widths) >= LINE_MIN
            ok_g = gap >= GAP_MIN - 0.005
            d.text((ox + 20, oy + 10), name[:52], fill="black", font=font)
            d.text((ox + 20, oy + 560), f"lines {', '.join(f'{w:g}' for w in widths) or 'none'} mm", fill=(0, 130, 60) if ok_w else (200, 0, 0), font=small)
            d.text((ox + 20, oy + 585), f"closest ink to a pad {gap:.2f} mm" if gap < math.inf else "no silkscreen", fill=(0, 130, 60) if ok_g else (200, 0, 0), font=small)
        im.save(f"{outdir}/silk_sheet{sheet // 6 + 1}.png")


def main():
    fps = project_map()
    users = {}
    for ref, path in fps.items():
        users.setdefault(path, []).append(ref)
    results = {}
    for path, refs in users.items():
        name = path.split("/")[-1]
        results[name] = check(path)
        fp, pads, items, widths, gap, ref_layer = results[name]
        flag = []
        if widths and min(widths) < LINE_MIN:
            flag.append("thin lines")
        if gap < GAP_MIN - 0.005:
            flag.append("ink near pads")
        print(f"{name:52} {len(refs):3} parts | lines {', '.join(f'{w:g}' for w in widths) or 'none':14} | closest ink {'-' if gap == math.inf else f'{gap:.2f}':>5} | {'; '.join(flag) or 'OK'}")
    if "--render" in sys.argv:
        render(results, sys.argv[sys.argv.index("--render") + 1])


if __name__ == "__main__":
    main()
