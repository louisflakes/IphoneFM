"""Phase 5: draws a window of the board open in KiCad to a PNG, for routing plans and reports: pads (top red, bottom
blue, through-hole grey), tracks and vias, coloured by layer, with each part's reference and, optionally, net names
on the pads. Optional plan lines (dashed) are drawn over it.
Usage (from the repository root, board open in KiCad):
  python tools/pcb_view.py X0 Y0 X1 Y1 OUT.png [--nets] [--plan FILE.json]"""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

sys.path.insert(0, "tools")
from pcb_astar import board_copper

TOP, BOT, TH = "#c8302c", "#2c62c8", "#888888"


def draw(board, box, out, nets=False, plan=None):
    x0, y0, x1, y1 = box
    copper = board_copper(board.get_as_string())
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
    for p in plan or []:
        xs, ys = zip(*p["pts"])
        ax.plot(xs, ys, "--", color=p.get("color", "#1a9850"), lw=1.2, zorder=8)
        if p.get("label"):
            ax.text(xs[-1], ys[-1], p["label"], fontsize=6, color=p.get("color", "#1a9850"), zorder=9)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)
    ax.set_aspect("equal")
    ax.grid(True, lw=0.2, alpha=0.4)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out)


def main():
    from kipy import KiCad
    a = sys.argv[1:]
    box = tuple(float(v) for v in a[:4])
    plan = json.load(open(a[a.index("--plan") + 1])) if "--plan" in a else None
    draw(KiCad().get_board(), box, a[4], "--nets" in a, plan)


if __name__ == "__main__":
    main()
