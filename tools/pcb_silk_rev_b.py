"""Rev B silkscreen (Rev A step 7.1 and the tag), by file edits with KiCad's own Python: the Rev B board is not open in
KiCad, and Rev A's tools (pcb_silk_refs.py, pcb_silk_edge.py, pcb_tag.py) work through KiCad's live API. Same rules:
  refs  Rev A's labelling: only the major parts carry their reference (ICs, connectors, switches, the digits, the
        crystal oscillator, the LED, the test pads), 1.0 mm high with a 0.15 mm stroke, at the nearest clear spot
        beside the part (outside every courtyard, 0.2 mm from exposed copper and via holes, 0.2 mm from other ink,
        0.6 mm from other references, 0.3 mm inside the edge), level first, then upright. The new passives' references
        are hidden on the silkscreen (fab layer only). Rev A's labels stay where they are unless they now clash.
  edge  every silkscreen line of a placed part cut back to 0.2 mm inside the board edge (plus half its width); lines
        and marks wholly outside removed. The library footprints are left as they are.
  tag   the board's tag ("CLAUDE / WAS HERE" over an FM wave, Rev A Phase 7) sat where U8 now is: moved, whole, to the
        nearest clear spot on the top pour by the same rules as a label.
Usage (from the repository root):
  "%LOCALAPPDATA%/Programs/KiCad/10.0/bin/python.exe" -u tools/pcb_silk_rev_b.py refs|edge|tag [lay]
"""
import os
import sys

import pcbnew
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

PCB = "kicad/rev-b/IphoneFM.kicad_pcb"
BOARD = (12.7, 59.56, 59.15, 130.96)
EDGE_GAP, PAD_GAP, SILK_GAP, CRT_GAP, REF_GAP = 0.3, 0.2, 0.2, 0.1, 0.6
GAPS = (0.1, 0.35, 0.7, 1.1, 1.6, 2.2)
SLIDE = [s * 0.25 for s in range(-12, 13)]
LABELLED = ("U", "J", "SW", "DS", "Y", "D1", "TP")
NEW = ("U8", "DS1", "DS2", "DS3", "DS4", "SW4", "SW3")        # labels to place; the rest keep Rev A's
TAG = ("CLAUDE", "WAS HERE")
MM, ERR = 1e6, pcbnew.FromMM(0.005)


def poly(ps):
    """SHAPE_POLY_SET -> shapely"""
    out = []
    for i in range(ps.OutlineCount()):
        ring = lambda c: [(c.CPoint(j).x / MM, c.CPoint(j).y / MM) for j in range(c.PointCount())]
        o = ring(ps.Outline(i))
        if len(o) >= 3:
            out.append(Polygon(o, [ring(ps.Hole(i, h)) for h in range(ps.HoleCount(i))]).buffer(0))
    return unary_union(out)


def ink(item, layer):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, 0, ERR, pcbnew.ERROR_INSIDE)
    return poly(ps)


def is_tag(d):
    """The tag's items: its two texts and the wave's segments (the only board-level silkscreen lines)."""
    return d.GetLayer() == pcbnew.F_SilkS and (d.GetClass() == "PCB_SHAPE" or
                                              (d.GetClass() == "PCB_TEXT" and d.GetText() in TAG))


def obstacles(board, skip_refs=(), skip_tag=False):
    """Top side: exposed copper and via holes (+0.2), courtyards (+0.1), footprint ink (+0.2), visible references."""
    copper, crt, silk, refs = [], [], [], {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) or p.GetDrillSizeX() > 0:
                copper.append(ink(p, pcbnew.F_Cu))
        c = fp.GetCourtyard(pcbnew.F_CrtYd)
        if c.OutlineCount():
            crt.append(poly(c))
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS:
                silk.append(ink(g, pcbnew.F_SilkS))
        f = fp.Reference()
        if f.IsVisible() and f.GetLayer() == pcbnew.F_SilkS and ref not in skip_refs:
            refs[ref] = ink(f, pcbnew.F_SilkS)
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            copper.append(box(0, 0, 0, 0).union(
                LineString([(t.GetPosition().x / MM, t.GetPosition().y / MM)] * 2).buffer(t.GetDrillValue() / MM / 2)))
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.F_SilkS and not (skip_tag and is_tag(d)):
            silk.append(ink(d, pcbnew.F_SilkS))
    inside = box(BOARD[0] + EDGE_GAP, BOARD[1] + EDGE_GAP, BOARD[2] - EDGE_GAP, BOARD[3] - EDGE_GAP)
    return dict(copper=unary_union(copper).buffer(PAD_GAP), crt=unary_union(crt).buffer(CRT_GAP),
                silk=unary_union(silk).buffer(SILK_GAP), refs=refs, inside=inside, crt_list=crt)


def step_refs(lay):
    board = pcbnew.LoadBoard(PCB)
    hide = [fp for fp in board.GetFootprints()
            if fp.GetReference() in ("R28", "R29", "R30", "R31", "R32", "C42", "C43", "C44")]
    for fp in hide:
        fp.Reference().SetVisible(False)
    ob = obstacles(board, skip_refs=NEW)
    fixed = unary_union(list(ob["refs"].values())).buffer(REF_GAP)
    cands = {}
    for ref in NEW:
        fp = board.FindFootprintByReference(ref)
        f = fp.Reference()
        f.SetVisible(True); f.SetLayer(pcbnew.F_SilkS)
        f.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.0), pcbnew.FromMM(1.0))); f.SetTextThickness(pcbnew.FromMM(0.15))
        f.SetKeepUpright(False)
        own = poly(fp.GetCourtyard(pcbnew.F_CrtYd))
        x0, y0, x1, y1 = own.bounds
        f.SetTextAngleDegrees(0); f.SetPosition(pcbnew.VECTOR2I(0, 0))
        dx0, dy0, dx1, dy1 = ink(f, pcbnew.F_SilkS).bounds
        out = []
        for ang in (0, 90):
            w, h = (dx1 - dx0, dy1 - dy0) if ang == 0 else (dy1 - dy0, dx1 - dx0)
            cx_off, cy_off = ((dx0 + dx1) / 2, (dy0 + dy1) / 2) if ang == 0 else ((dy0 + dy1) / 2, -(dx0 + dx1) / 2)
            for gap in GAPS:
                for sl in SLIDE:
                    for side in "NSWE":
                        if side in "NS":
                            cx, cy = (x0 + x1) / 2 + sl, (y0 - gap - h / 2 if side == "N" else y1 + gap + h / 2)
                        else:
                            cx, cy = (x0 - gap - w / 2 if side == "W" else x1 + gap + w / 2), (y0 + y1) / 2 + sl
                        bx = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                        if not ob["inside"].contains(bx) or bx.intersects(ob["copper"]) or \
                                bx.intersects(ob["crt"]) or bx.intersects(ob["silk"]) or bx.intersects(fixed):
                            continue
                        out.append((gap + 0.6 * abs(sl) + (0.8 if ang else 0), cx - cx_off, cy - cy_off, ang, bx))
        out.sort(key=lambda t: t[0])
        cands[ref] = out
    chosen, hidden = {}, []
    for ref in sorted(cands, key=lambda r: (len(cands[r]), r)):
        c = next((c for c in cands[ref] if not any(c[4].buffer(REF_GAP).intersects(o[4]) for o in chosen.values())),
                 None)
        if c is None:
            hidden.append(ref)
        else:
            chosen[ref] = c
    for ref, (_, x, y, ang, _) in chosen.items():
        f = board.FindFootprintByReference(ref).Reference()
        f.SetTextAngleDegrees(ang)
        f.SetPosition(pcbnew.VECTOR2I(round(x * MM), round(y * MM)))
        print(f"{ref}: ({x:.2f}, {y:.2f}) {ang} deg")
    for ref in hidden:
        board.FindFootprintByReference(ref).Reference().SetVisible(False)
    print(f"{len(chosen)} placed; hidden: {', '.join(hidden) or 'none'}; passives hidden: {len(hide)}")
    # Rev A labels that now clash with something new
    for ref, g in ob["refs"].items():
        if g.intersects(ob["copper"]) or g.intersects(ob["silk"]) or \
                any(g.intersects(c[4]) for c in chosen.values()):
            print("  clash, Rev A label:", ref)
    if lay:
        pcbnew.SaveBoard(PCB, board)
        print("saved")
    os._exit(0)


def step_edge(lay):
    board = pcbnew.LoadBoard(PCB)
    drop = []   # removed at the end: this pcbnew build hands back bare pointers for a footprint's items after a Remove
    for fp in list(board.GetFootprints()):
        cut = dropped = 0
        for g in list(fp.GraphicalItems()):
            if g.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS) or g.GetClass() != "PCB_SHAPE":
                continue
            m = 0.22 + g.GetWidth() / MM / 2
            inside = box(BOARD[0] + m, BOARD[1] + m, BOARD[2] - m, BOARD[3] - m)
            if g.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                line = LineString([(g.GetStart().x / MM, g.GetStart().y / MM), (g.GetEnd().x / MM, g.GetEnd().y / MM)])
                if inside.contains(line):
                    continue
                part = line.intersection(inside)
                if part.is_empty or part.length < 0.2 or part.geom_type != "LineString":
                    drop.append((fp, g)); dropped += 1
                    continue
                (ax, ay), (bx, by) = part.coords[0], part.coords[-1]
                g.SetStart(pcbnew.VECTOR2I(round(ax * MM), round(ay * MM)))
                g.SetEnd(pcbnew.VECTOR2I(round(bx * MM), round(by * MM)))
                cut += 1
            elif not inside.contains(ink(g, g.GetLayer())):
                drop.append((fp, g)); dropped += 1
        if cut or dropped:
            print(f"{fp.GetReference()}: {cut} lines cut back, {dropped} removed")
    for fp, g in drop:
        fp.Remove(g)
    if lay:
        pcbnew.SaveBoard(PCB, board)
        print("saved")
    os._exit(0)


def step_tag(lay):
    board = pcbnew.LoadBoard(PCB)
    items = [d for d in board.GetDrawings() if is_tag(d)]
    tag = unary_union([ink(d, pcbnew.F_SilkS) for d in items])
    ob = obstacles(board, skip_tag=True)
    refs = unary_union(list(ob["refs"].values())).buffer(REF_GAP)
    block = unary_union([ob["copper"], ob["crt"], ob["silk"], refs])
    x0, y0, x1, y1 = tag.bounds
    best = None
    for i in range(int((BOARD[2] - BOARD[0]) / 0.25)):
        for j in range(int((BOARD[3] - BOARD[1]) / 0.25)):
            dx, dy = BOARD[0] + i * 0.25 - x0, BOARD[1] + j * 0.25 - y0
            g = translate(tag, dx, dy)
            if not ob["inside"].contains(g) or g.intersects(block):
                continue
            d = (dx ** 2 + dy ** 2) ** 0.5
            if best is None or d < best[0]:
                best = (d, dx, dy)
    if best is None:
        sys.exit("tag: no clear spot")
    d, dx, dy = best
    print(f"tag: moved ({dx:+.2f}, {dy:+.2f}) mm to x {x0 + dx:.2f}-{x1 + dx:.2f}, y {y0 + dy:.2f}-{y1 + dy:.2f}")
    if lay:
        v = pcbnew.VECTOR2I(round(dx * MM), round(dy * MM))
        for it in items:
            it.Move(v)
        pcbnew.SaveBoard(PCB, board)
        print("saved")
    os._exit(0)


if __name__ == "__main__":
    globals()["step_" + sys.argv[1]](len(sys.argv) > 2 and sys.argv[2] == "lay")
