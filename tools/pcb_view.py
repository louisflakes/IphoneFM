"""Phase 5: draws a window of the board open in KiCad to a PNG, for routing plans and reports: pads (top red, bottom
blue, through-hole grey), tracks and vias, coloured by layer, with each part's reference and, optionally, net names
on the pads. Optional plan lines (dashed) are drawn over it; --runs adds a routing script's planned tracks and vias
(its plan() function) as copper, --zones shades the no-bottom-copper RF areas, and --pours draws the filled ground
pours of one layer (--pours F or --pours B) under the copper.
Usage (from the repository root, board open in KiCad):
  python tools/pcb_view.py X0 Y0 X1 Y1 OUT.png [--nets] [--plan FILE.json] [--runs SCRIPT.py[,SCRIPT.py]] [--zones] [--pours F|B] [--title T]"""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

sys.path.insert(0, "tools")
from pcb_astar import board_copper

TOP, BOT, TH = "#c8302c", "#2c62c8", "#888888"


def draw(board, box, out, nets=False, plan=None, runs=None, zones=False, title=None, pours=None):
    x0, y0, x1, y1 = box
    copper = board_copper(board.get_as_string())
    if runs:
        from pcb_quality import load_plan
        planned = []
        for path in runs.split(","):
            planned += load_plan(path, copper + planned)
        copper = copper + planned
    inbox = lambda x, y, m=1.0: x0 - m < x < x1 + m and y0 - m < y < y1 + m
    fig, ax = plt.subplots(figsize=(10, 10 * (y1 - y0) / (x1 - x0)), dpi=150)
    refs = {}
    for kind, net, lay, g, name in copper:
        if kind == "track":
            if not (inbox(g[0], g[1]) or inbox(g[2], g[3])):
                continue
            c = TOP if "F.Cu" in lay else BOT
            ax.plot([g[0], g[2]], [g[1], g[3]], color=c, lw=g[4] * 2 * 72 * 10 / (x1 - x0) / 1.0 * 0.9,
                    solid_capstyle="round", alpha=0.75 if c == BOT else 0.9, zorder=3 if c == TOP else 2)
        elif kind == "via":
            if inbox(g[0], g[1]):
                ax.add_patch(Circle(g[:2], g[2], color="#c9a227", zorder=4))
                ax.add_patch(Circle(g[:2], g[3], color="white", zorder=5))
        else:
            x, y, hw, hh, shape, dr = g
            if not inbox(x, y):
                continue
            c = TH if len(lay) == 2 else TOP if "F.Cu" in lay else BOT
            if shape == "circle":
                ax.add_patch(Circle((x, y), hw, color=c, alpha=0.6, zorder=1))
            else:
                ax.add_patch(Rectangle((x - hw, y - hh), 2 * hw, 2 * hh, color=c, alpha=0.6, zorder=1))
            ref, pin = name.split(".", 1)
            refs.setdefault(ref, []).append((x, y))
            if nets and net and net != "GND" and not net.startswith("unconnected"):
                ax.text(x, y, net.lstrip("/").replace("_MCU", "m"), fontsize=3.2, ha="center", va="center", zorder=6)
    for ref, pts in refs.items():
        if len(pts) < 2 and ref[0] not in "TJ":
            continue
        cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        if inbox(cx, cy, 0):
            ax.text(cx, cy, ref, fontsize=7 if ref[0] == "U" else 5, ha="center", va="center", weight="bold",
                    color="black", zorder=7, alpha=0.85)
    if pours:
        from pcb_stitch import fills
        geom = fills(board)[3 if pours == "F" else 34]
        for g in getattr(geom, "geoms", [geom]):
            ax.add_patch(Polygon(list(g.exterior.coords), closed=True, fc="#9aa5b1", ec="none", alpha=0.45, zorder=0.5))
            for h in g.interiors:
                ax.add_patch(Polygon(list(h.coords), closed=True, fc="white", ec="none", zorder=0.6))
    if zones:
        from pcb_freeroute import RF_BOTTOM_POLYS
        for poly in RF_BOTTOM_POLYS:
            ax.add_patch(Polygon(poly, closed=True, fill=False, hatch="///", ec="#2c62c8", lw=0.6, alpha=0.45, zorder=0))
    scale = 72 * 10 / (x1 - x0)  # points per mm
    for p in plan or []:
        col = p.get("color", "#1a9850")
        if p.get("pts"):
            xs, ys = zip(*p["pts"])
            if p.get("w"):  # a lane: a band as wide as the lines it carries
                ax.plot(xs, ys, "-", color=col, lw=p["w"] * scale, alpha=0.28, solid_capstyle="butt",
                        solid_joinstyle="miter", zorder=8)
                ax.plot(xs, ys, "-", color=col, lw=0.6, zorder=8)
            else:
                ax.plot(xs, ys, "--", color=col, lw=1.2, zorder=8)
        for hx, hy in p.get("hops", []):  # a bottom-layer hop: one marker per via pair
            ax.add_patch(Circle((hx, hy), 0.55, fc="#f28e2b", ec="black", lw=0.5, zorder=10))
        if p.get("label"):
            lx, ly = p["at"] if "at" in p else p["pts"][-1] if p.get("pts") else p["hops"][0]
            ax.text(lx, ly, p["label"], fontsize=p.get("size", 6.5), color=col, weight="bold", zorder=11,
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.2, alpha=0.4)
    ax.tick_params(labelsize=6)
    if title:
        ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(out)


def main():
    from kipy import KiCad
    a = sys.argv[1:]
    box = tuple(float(v) for v in a[:4])
    plan = json.load(open(a[a.index("--plan") + 1])) if "--plan" in a else None
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    draw(KiCad().get_board(), box, a[4], "--nets" in a, plan, opt("--runs"), "--zones" in a, opt("--title"), opt("--pours"))


if __name__ == "__main__":
    main()
