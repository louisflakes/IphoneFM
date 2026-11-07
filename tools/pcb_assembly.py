"""Step 8.1a: the assembly drawing for bench work, one A3 page per side (the bottom seen from below, mirrored): the board
outline, every pad in grey, each part's body from its fab layer, and every reference written inside its body, as large
as the body allows and turned along its long side; test pads also carry their net. KiCad's own fab plot prints the passives' references inside their
pads at 0.5 mm, unreadable on this board.
The board is read either from KiCad's live API (Rev A, board open in KiCad) or, with --pcb, from the board file by
KiCad's own Python (Rev B: run in a second process, since KiCad's Python has no matplotlib); both give the same parts
list, drawn the same way.
Usage (from the repository root):
  python tools/pcb_assembly.py OUT.pdf [--pcb FILE --title "IphoneFM Rev B"]
  KiCad's python tools/pcb_assembly.py --collect FILE OUT.json      (used by --pcb)"""
import json
import os
import subprocess
import sys

BOARD = (12.7, 59.56, 59.15, 130.96)
A3 = (11.69, 16.54)   # inches, portrait
KICAD_PY = "C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/bin/python.exe"


def collect_kipy(board):
    """Parts from KiCad's live API: {pads: {F|B: [ring]}, parts: [{ref, side, body: [ring], pads: [(x, y)], net}]}"""
    from kipy.board_types import BoardLayer, BoardShape, Pad, to_concrete_board_shape
    from shapely.ops import unary_union
    sys.path.insert(0, "tools")
    from pcb_silk_refs import mm, shape_geom
    out = {"pads": {}, "parts": []}
    fps = board.get_footprints()
    for side, cu in (("F", BoardLayer.BL_F_Cu), ("B", BoardLayer.BL_B_Cu)):
        pads = [it for f in fps for it in f.definition.items if isinstance(it, Pad) and cu in it.proto.pad_stack.layers]
        out["pads"][side] = [[(mm(n.point.x), mm(n.point.y)) for n in poly.outline.nodes]
                             for poly in board.get_pad_shapes_as_polygons(pads, cu) if poly is not None]
    for f in fps:
        side = "F" if f.layer == BoardLayer.BL_F_Cu else "B"
        fab = BoardLayer.BL_F_Fab if side == "F" else BoardLayer.BL_B_Fab
        body = [shape_geom(to_concrete_board_shape(it)) for it in f.definition.items
                if isinstance(it, BoardShape) and it.layer == fab]
        body = unary_union([g for g in body if g is not None])
        own = [p for p in f.definition.items if isinstance(p, Pad)]
        out["parts"].append({"ref": f.reference_field.text.value, "side": side,
                             "body": [list(g.exterior.coords) for g in getattr(body, "geoms", [body])
                                      if g.geom_type == "Polygon" and not g.is_empty],
                             "pads": [(mm(p.position.x), mm(p.position.y)) for p in own],
                             "net": own[0].net.name if own else ""})
    return out


def collect_pcbnew(path, out_json):
    """The same parts list from the board file, with KiCad's own Python (pcbnew)."""
    import pcbnew
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    MM, ERR = 1e6, pcbnew.FromMM(0.005)

    def polys(ps):
        res = []
        for i in range(ps.OutlineCount()):
            c = ps.Outline(i)
            pts = [(c.CPoint(j).x / MM, c.CPoint(j).y / MM) for j in range(c.PointCount())]
            if len(pts) >= 3:
                res.append(Polygon(pts).buffer(0))
        return res

    board = pcbnew.LoadBoard(path)
    out = {"pads": {"F": [], "B": []}, "parts": []}
    for fp in board.GetFootprints():
        side = "B" if fp.IsFlipped() else "F"
        fab = pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab
        for p in fp.Pads():
            for s, layer in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
                if p.IsOnLayer(layer):
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, layer, 0, ERR, pcbnew.ERROR_INSIDE)
                    out["pads"][s] += [list(g.exterior.coords) for g in polys(ps)]
        body = []
        for g in fp.GraphicalItems():
            if g.GetLayer() == fab and g.GetClass() == "PCB_SHAPE":
                ps = pcbnew.SHAPE_POLY_SET()
                g.TransformShapeToPolygon(ps, fab, 0, ERR, pcbnew.ERROR_INSIDE)
                body += polys(ps)
        body = unary_union(body)
        pads = list(fp.Pads())
        out["parts"].append({"ref": fp.GetReference(), "side": side,
                             "body": [list(g.exterior.coords) for g in getattr(body, "geoms", [body])
                                      if g.geom_type == "Polygon" and not g.is_empty],
                             "pads": [(p.GetPosition().x / MM, p.GetPosition().y / MM) for p in pads],
                             "net": pads[0].GetNetname() if pads else ""})
    json.dump(out, open(out_json, "w"))
    os._exit(0)


def page(pdf, data, side, title):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
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
    for pts in data["pads"][side]:
        ax.add_patch(MPoly(pts, closed=True, fc="#d9d9d9", ec="#9a9a9a", lw=0.3))
    for f in data["parts"]:
        if f["side"] != side:
            continue
        ref, own = f["ref"], f["pads"]
        body = unary_union([Polygon(r) for r in f["body"]])
        if body.is_empty:                        # test pads draw no body: label beside the pad
            if not own:
                continue
            px, py = own[0]
            body = box(px - 1.6, py + 0.9, px + 1.6, py + 2.1)
            ax.text(px, py + 3.0, f["net"].lstrip("/"), ha="center", va="center", fontsize=1.0 * pt_per_mm,
                    color="#b00000")
        else:
            for g in getattr(body, "geoms", [body]):
                if g.geom_type == "Polygon" and not g.is_empty:
                    ax.add_patch(MPoly(list(g.exterior.coords), closed=True, fc="none", ec="black", lw=0.5))
        bx0, by0, bx1, by1 = body.bounds
        w, h = bx1 - bx0, by1 - by0
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if ref.startswith("RV"):                 # the wheel's body is mostly overhang: label beside its pads
            cx = sum(p[0] for p in own) / len(own) - 3.0
        rot = 90 if h > w * 1.2 else 0
        length, across = (h, w) if rot else (w, h)
        size_mm = min(across * 1.5, length * 1.25 / (0.62 * len(ref)), 2.4)   # may overhang a small body a little
        pts = size_mm * pt_per_mm
        ax.text(cx, cy, ref, rotation=rot, ha="center", va="center", fontsize=pts, fontweight="bold",
                family="DejaVu Sans", color="#b00000" if not ref.startswith(("C", "R", "L", "FB", "D")) or ref == "D1"
                or ref.startswith("DS") else "black", bbox=dict(fc="white", ec="none", pad=0.05, alpha=0.75))
    ax.axis("off")
    ax.set_title(title, fontsize=14)
    pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    if sys.argv[1] == "--collect":
        collect_pcbnew(sys.argv[2], sys.argv[3])
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.backends.backend_pdf import PdfPages
    out_pdf, args = sys.argv[1], sys.argv[2:]
    name = args[args.index("--title") + 1] if "--title" in args else "IphoneFM Rev A"
    if "--pcb" in args:
        tmp = out_pdf + ".json"
        subprocess.run([KICAD_PY, "-u", __file__, "--collect", args[args.index("--pcb") + 1], tmp], check=True,
                       capture_output=True)
        data = json.load(open(tmp))
        os.remove(tmp)
    else:
        from kipy import KiCad
        data = collect_kipy(KiCad().get_board())
    with PdfPages(out_pdf) as pdf:
        page(pdf, data, "F", f"{name}: assembly drawing, top side")
        page(pdf, data, "B", f"{name}: assembly drawing, bottom side (seen from below)")
    print("written", out_pdf)
