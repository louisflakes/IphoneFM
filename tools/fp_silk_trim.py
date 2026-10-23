"""Step 2.4: brings every Rev A footprint's silkscreen to kicad/rev-a/fab-rules.md: lines 0.25 mm wide, and no ink
within 0.20 mm of copper or a hole. Each silkscreen line, rectangle, circle and arc is widened to 0.25 mm and cut back
wherever its edge would come closer than 0.20 mm; leftover pieces shorter than 0.2 mm are dropped. Every filled mark (a
pin-1 triangle or dot) is redrawn as a round dot 0.55 mm across, slid straight outward until it clears. Reference text is left as it is (its rule is
a 0.15 mm stroke). KiCad library footprints are copied into kicad/rev-a/IphoneFM.pretty under their own names; the
project's own footprints are updated in place, so run this after any fp_*.py builder.
Usage (from the repository root): python tools/fp_silk_trim.py"""
import math
import os
import re
import sys

sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid
from rev_a_footprints import K, P, footprint_map
from silk_check import arc_points, dist_to_pad, sample

WIDTH, GAP, MIN_PIECE = 0.25, 0.20, 0.2
GRAPHIC = re.compile(r'\t\((fp_line|fp_rect|fp_circle|fp_arc|fp_poly)\n.*?\n\t\)\n', re.S)


def holes_and_pads(fp):
    out = []
    for p in kids(fp, "pad"):
        at = kid(p, "at")
        x, y = float(at[1]), float(at[2])
        r = float(at[3]) if len(at) > 3 else 0.0
        w, h = map(float, kid(p, "size")[1:3])
        out.append((p[1], p[3], x, y, r, w, h, p[2]))  # every pad and every unplated hole
    return out


def clearance(px, py, pads):
    return min(dist_to_pad(px, py, pad) for pad in pads) if pads else math.inf


def graphic_points(g):
    pt = lambda k: tuple(map(float, kid(g, k)[1:3]))
    if g[0] == "fp_line":
        return [pt("start"), pt("end")]
    if g[0] == "fp_rect":
        (x1, y1), (x2, y2) = pt("start"), pt("end")
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    if g[0] == "fp_circle":
        (cx, cy), (ex, ey) = pt("center"), pt("end")
        rr = math.hypot(ex - cx, ey - cy)
        n = max(24, int(2 * math.pi * rr / 0.1))
        return [(cx + rr * math.cos(2 * math.pi * i / n), cy + rr * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
    if g[0] == "fp_arc":
        return arc_points(pt("start"), pt("mid"), pt("end"))
    pts = [tuple(map(float, x[1:3])) for x in kid(g, "pts")[1:]]
    return pts + [pts[0]]


def line(x1, y1, x2, y2):
    return (f'\t(fp_line\n\t\t(start {x1:.4f} {y1:.4f})\n\t\t(end {x2:.4f} {y2:.4f})\n'
            f'\t\t(stroke\n\t\t\t(width {WIDTH:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "F.SilkS")\n\t)\n')


def trim(pts, pads):
    """Pieces of the polyline whose ink stays clear of every pad, as fp_line text."""
    need = GAP + WIDTH / 2
    out = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / 0.005))
        run = None
        for i in range(n + 1):
            t = i / n
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            ok = clearance(x, y, pads) >= need
            if ok and run is None:
                run = (x, y)
            if run is not None and (not ok or i == n):
                end = (x, y) if ok else (x1 + (x2 - x1) * (i - 1) / n, y1 + (y2 - y1) * (i - 1) / n)
                if math.hypot(end[0] - run[0], end[1] - run[1]) >= MIN_PIECE:
                    out.append(line(*run, *end))
                run = None
    return out


# Parts whose orientation matters but whose own pin-1 mark is cut away by the trimming: they get a dot beside pad 1
PIN1_DOT = {"LED_RGB_XINGLIGHT_XL-1615RGBC_1.6x1.5mm", "Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm"}
DOT_R = 0.15  # drawn radius; with the 0.25 mm stroke the ink is 0.55 mm across


def add_pin1_dot(text, pads):
    """A filled dot on the line from the footprint's centre through pad 1, just far enough out to clear every pad."""
    _, _, px, py, _, _, _, _ = next(p for p in pads if p[0] == "1")
    d = math.hypot(px, py)
    ux, uy = px / d, py / d
    ink = DOT_R + WIDTH / 2
    for i in range(400):
        x, y = px + ux * i * 0.01, py + uy * i * 0.01
        if clearance(x, y, pads) >= GAP + ink:
            break
    return text.replace("\t(pad ", dot(x, y) + "\t(pad ", 1)


def dot(x, y):
    return (f'\t(fp_circle\n\t\t(center {x:.4f} {y:.4f})\n\t\t(end {x + DOT_R:.4f} {y:.4f})\n'
            f'\t\t(stroke\n\t\t\t(width {WIDTH:g})\n\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n\t\t(layer "F.SilkS")\n\t)\n')


def process(src, dst, name):
    text = open(src + ".kicad_mod", encoding="utf-8").read()
    fp = sexpr(text)
    pads = holes_and_pads(fp)
    kept_marks, lost_marks = 0, 0

    def repl(m):
        nonlocal kept_marks, lost_marks
        blk = m.group(0)
        g = sexpr(blk.strip())
        if kid(g, "layer")[1] != "F.SilkS":
            return blk
        fill = kid(g, "fill")
        if fill and fill[1] in ("yes", "solid"):  # a pin-1 mark: drawn as a round dot where the mark was
            pts = graphic_points(g)
            cx, cy = sum(p[0] for p in pts[:-1]) / (len(pts) - 1), sum(p[1] for p in pts[:-1]) / (len(pts) - 1)
            ux, uy = (cx / math.hypot(cx, cy), cy / math.hypot(cx, cy)) if math.hypot(cx, cy) > 1e-6 else (-1.0, 0.0)
            for step in range(0, 41):  # slide it straight out from the footprint's centre, up to 2 mm, until it clears
                x, y = cx + ux * step * 0.05, cy + uy * step * 0.05
                if clearance(x, y, pads) >= GAP + DOT_R + WIDTH / 2:
                    kept_marks += 1
                    return dot(x, y)
            lost_marks += 1
            return ""
        return "".join(trim(graphic_points(g), pads))

    text = GRAPHIC.sub(repl, text)
    if name in PIN1_DOT:
        text = add_pin1_dot(text, pads)
    open(dst + ".kicad_mod", "w", encoding="utf-8", newline="\n").write(text)
    return kept_marks, lost_marks


def main():
    done = set()
    for ref, path in footprint_map().items():
        if path in done:
            continue
        done.add(path)
        name = path.split("/")[-1]
        dst = P + name
        kept, lost = process(path, dst, name)
        print(f"{name:52} {'project copy' if path.startswith(K) else 'updated in place':16} filled marks kept {kept}, dropped {lost}")


if __name__ == "__main__":
    main()
