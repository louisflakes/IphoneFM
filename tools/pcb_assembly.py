"""Step 8.1a: the assembly drawing for bench work, one A3 page per side (the bottom seen from below, mirrored): the board
outline, every pad in grey, each part's body from its fab layer, and every reference written inside its body, as large
as the body allows and turned along its long side; test pads also carry their net. KiCad's own fab plot prints the passives' references inside their
pads at 0.5 mm, unreadable on this board.
Usage (from the repository root, board open in KiCad): python tools/pcb_assembly.py OUT.pdf"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MPoly
from shapely.geometry import box
from shapely.ops import unary_union

sys.path.insert(0, "tools")
from pcb_silk_refs import BOARD, mm, shape_geom

A3 = (11.69, 16.54)   # inches, portrait


def outline(ax, geom, **kw):
    for g in getattr(geom, "geoms", [geom]):
        if g.geom_type == "Polygon" and not g.is_empty:
            ax.add_patch(MPoly(list(g.exterior.coords), closed=True, **kw))


def page(pdf, board, side, title):
    from kipy.board_types import BoardLayer, BoardShape, Pad, to_concrete_board_shape
    cu = BoardLayer.BL_F_Cu if side == "F" else BoardLayer.BL_B_Cu
    fab = BoardLayer.BL_F_Fab if side == "F" else BoardLayer.BL_B_Fab
    fig = plt.figure(figsize=A3)
    ax = fig.add_axes([0.03, 0.02, 0.94, 0.93])
    ax.set_aspect("equal")
    x0, y0, x1, y1 = BOARD
    m = 1.5
    ax.set_xlim(x0 - m - (9 if side == "F" else 3), x1 + m + (8 if side == "F" else 3))
    ax.set_ylim(y1 + m, y0 - m)
    if side == "B":
        ax.invert_xaxis()
    fig.canvas.draw()
    ext = ax.get_window_extent()
    span = abs(ax.get_xlim()[1] - ax.get_xlim()[0]), abs(ax.get_ylim()[1] - ax.get_ylim()[0])
    pt_per_mm = min(ext.width / span[0], ext.height / span[1]) * 72 / fig.dpi
    ax.add_patch(MPoly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True, fill=False, lw=1.2, ec="black"))
    fps = board.get_footprints()
    pads = [it for f in fps for it in f.definition.items if isinstance(it, Pad) and cu in it.proto.pad_stack.layers]
    for poly in board.get_pad_shapes_as_polygons(pads, cu):
        if poly is not None:
            pts = [(mm(n.point.x), mm(n.point.y)) for n in poly.outline.nodes]
            ax.add_patch(MPoly(pts, closed=True, fc="#d9d9d9", ec="#9a9a9a", lw=0.3))
    for f in fps:
        if (f.layer == BoardLayer.BL_F_Cu) != (side == "F"):
            continue
        ref = f.reference_field.text.value
        body = [shape_geom(to_concrete_board_shape(it)) for it in f.definition.items
                if isinstance(it, BoardShape) and it.layer == fab]
        body = unary_union([g for g in body if g is not None])
        own = [p for p in f.definition.items if isinstance(p, Pad)]
        if body.is_empty:                        # test pads draw no body: label beside the pad
            if not own:
                continue
            px, py = mm(own[0].position.x), mm(own[0].position.y)
            body = box(px - 1.6, py + 0.9, px + 1.6, py + 2.1)
            net = own[0].net.name.lstrip("/")
            ax.text(px, py + 3.0, net, ha="center", va="center", fontsize=1.0 * pt_per_mm, color="#b00000")
        else:
            outline(ax, body, fc="none", ec="black", lw=0.5)
        bx0, by0, bx1, by1 = body.bounds
        w, h = bx1 - bx0, by1 - by0
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if ref.startswith("RV"):                 # the wheel's body is mostly overhang: label beside its pads
            cx = sum(mm(p.position.x) for p in own) / len(own) - 3.0
        rot = 90 if h > w * 1.2 else 0
        length, across = (h, w) if rot else (w, h)
        size_mm = min(across * 1.5, length * 1.25 / (0.62 * len(ref)), 2.4)   # may overhang a small body a little
        pts = size_mm * pt_per_mm
        ax.text(cx, cy, ref, rotation=rot, ha="center", va="center", fontsize=pts, fontweight="bold",
                family="DejaVu Sans", color="#b00000" if not ref.startswith(("C", "R", "L", "FB", "D")) or ref == "D1"
                else "black", bbox=dict(fc="white", ec="none", pad=0.05, alpha=0.75))
    ax.axis("off")
    ax.set_title(title, fontsize=14)
    pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    from kipy import KiCad
    b = KiCad().get_board()
    with PdfPages(sys.argv[1]) as pdf:
        page(pdf, b, "F", "IphoneFM Rev A: assembly drawing, top side")
        page(pdf, b, "B", "IphoneFM Rev A: assembly drawing, bottom side (seen from below)")
    print("written", sys.argv[1])
