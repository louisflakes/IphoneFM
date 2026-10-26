"""Step 7.1: places every reference designator on the silkscreen of its own side, 1.0 mm high with a 0.15 mm stroke
(kicad/rev-a/fab-rules.md), at the nearest clear spot beside its part: outside every courtyard, 0.2 mm from exposed
copper (pads, via holes), 0.2 mm from other silkscreen (Board Setup) and 0.3 mm inside the board edge. Candidates run along the four sides
of the part's courtyard, level first, then upright (reading bottom to top); the parts with the fewest clear spots are
placed first. A reference with no clear spot is hidden on the silkscreen; it stays on the fab layer for the assembly
drawing.
Usage (from the repository root, board open in KiCad): python tools/pcb_silk_refs.py [list] | lay"""
import math
import sys

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polygonize, unary_union

BOARD = (12.7, 59.56, 59.15, 130.96)
EDGE_GAP, PAD_GAP, SILK_GAP, CRT_GAP = 0.3, 0.2, 0.2, 0.1
REF_GAP = 0.6       # between two references, so neighbouring labels read apart
GAPS = (0.1, 0.35, 0.7, 1.1, 1.6, 2.2)
SLIDE = [s * 0.25 for s in range(-12, 13)]


def mm(v):
    return v / 1e6


def shape_geom(c, courtyard=False):
    """A board shape as shapely geometry: lines at their stroke width, closed shapes as their area."""
    from kipy.board_types import BoardCircle, BoardPolygon, BoardRectangle, BoardSegment
    w = mm(c.attributes.stroke.width) if c.attributes.stroke.width else 0.05
    if isinstance(c, BoardSegment):
        a, b = (mm(c.start.x), mm(c.start.y)), (mm(c.end.x), mm(c.end.y))
        return LineString([a, b]) if courtyard else LineString([a, b]).buffer(w / 2)
    if isinstance(c, BoardRectangle):
        r = box(mm(c.top_left.x), mm(c.top_left.y), mm(c.bottom_right.x), mm(c.bottom_right.y))
        return r if courtyard else r.exterior.buffer(w / 2).union(r if c.attributes.fill.filled else Polygon())
    if isinstance(c, BoardCircle):
        p = Point(mm(c.center.x), mm(c.center.y)).buffer(mm(c.radius()))
        return p if courtyard else p.exterior.buffer(w / 2).union(p if c.attributes.fill.filled else Polygon())
    if isinstance(c, BoardPolygon):
        polys = [Polygon([(mm(n.point.x), mm(n.point.y)) for n in pw.outline.nodes]) for pw in c.polygons]
        return unary_union([p if courtyard or c.attributes.fill.filled else p.exterior.buffer(w / 2) for p in polys])
    if hasattr(c, "start") and hasattr(c, "end"):           # arc: sampled through its mid point
        pts = [(mm(c.start.x), mm(c.start.y)), (mm(c.mid.x), mm(c.mid.y)), (mm(c.end.x), mm(c.end.y))]
        return LineString(pts) if courtyard else LineString(pts).buffer(w / 2)
    return None


def collect(board):
    from kipy.board_types import BoardLayer, BoardShape, Pad, to_concrete_board_shape
    F, Bk = BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu
    SILK = {F: BoardLayer.BL_F_SilkS, Bk: BoardLayer.BL_B_SilkS}
    CRT = {F: BoardLayer.BL_F_CrtYd, Bk: BoardLayer.BL_B_CrtYd}
    fps = board.get_footprints()
    copper = {F: [], Bk: []}
    silk = {F: [], Bk: []}
    crt = {}
    pads = [it for f in fps for it in f.definition.items if isinstance(it, Pad)]
    for side in (F, Bk):
        for poly in board.get_pad_shapes_as_polygons(pads, side):
            if poly is None:
                continue
            copper[side].append(Polygon([(mm(n.point.x), mm(n.point.y)) for n in poly.outline.nodes]))
    for v in board.get_vias():
        for side in (F, Bk):
            copper[side].append(Point(mm(v.position.x), mm(v.position.y)).buffer(0.15))   # tented: only the hole
    for f in fps:
        ref = f.reference_field.text.value
        lines = []
        for it in f.definition.items:
            if not isinstance(it, BoardShape):
                continue
            c = to_concrete_board_shape(it)
            for side in (F, Bk):
                if c.layer == SILK[side]:
                    g = shape_geom(c)
                    if g is not None:
                        silk[side].append((ref, g))
                if c.layer == CRT[side]:
                    lines.append((side, shape_geom(c, courtyard=True)))
        for side in (F, Bk):
            parts = [g for s, g in lines if s == side]
            if not parts:
                continue
            areas = [g for g in parts if g.geom_type == "Polygon"]
            areas += list(polygonize(unary_union([g for g in parts if g.geom_type == "LineString"])))
            if areas:
                crt.setdefault(ref, {})[side] = unary_union(areas)
    return fps, copper, silk, crt, F, Bk


def ink(kicad, field):
    """The reference's ink box relative to its anchor, level (dx0, dy0, dx1, dy1)."""
    from kipy.common_types import Text
    t = Text(field.text.proto.text)
    t.proto.attributes.angle.value_degrees = 0
    t.proto.position.x_nm = 0
    t.proto.position.y_nm = 0
    geoms = []
    for cs in kicad.get_text_as_shapes(t):
        for s in cs.shapes:
            w = mm(s.attributes.stroke.width) / 2 if s.attributes.stroke.width else 0.075
            geoms.append(LineString([(mm(s.start.x), mm(s.start.y)), (mm(s.end.x), mm(s.end.y))]).buffer(w))
    return unary_union(geoms).bounds


def plan():
    from kipy import KiCad
    kicad = KiCad()
    board = kicad.get_board()
    fps, copper, silk, crt, F, Bk = collect(board)
    inside = box(BOARD[0] + EDGE_GAP, BOARD[1] + EDGE_GAP, BOARD[2] - EDGE_GAP, BOARD[3] - EDGE_GAP)
    static = {}
    for side in (F, Bk):
        static[side] = {
            "copper": unary_union(copper[side]).buffer(PAD_GAP),
            "crt": unary_union([c[side] for c in crt.values() if side in c]).buffer(CRT_GAP),
        }
    cands = {}
    for f in fps:
        ref = f.reference_field.text.value
        side = F if f.layer == F else Bk
        own = crt.get(ref, {}).get(side)
        if own is None:
            continue
        x0, y0, x1, y1 = own.bounds
        dx0, dy0, dx1, dy1 = ink(kicad, f.reference_field)
        others = unary_union([g for r, g in silk[side]]).buffer(SILK_GAP)
        out = []
        for ang in (0, 90):
            # ink box size and the anchor's offset from the box centre for this angle
            w, h = (dx1 - dx0, dy1 - dy0) if ang == 0 else (dy1 - dy0, dx1 - dx0)
            cx_off, cy_off = ((dx0 + dx1) / 2, (dy0 + dy1) / 2) if ang == 0 else ((dy0 + dy1) / 2, -(dx0 + dx1) / 2)
            for gi, gap in enumerate(GAPS):
                for sl in SLIDE:
                    for sidepos in ("N", "S", "W", "E"):
                        if sidepos in "NS":
                            cx = (x0 + x1) / 2 + sl
                            cy = y0 - gap - h / 2 if sidepos == "N" else y1 + gap + h / 2
                        else:
                            cy = (y0 + y1) / 2 + sl
                            cx = x0 - gap - w / 2 if sidepos == "W" else x1 + gap + w / 2
                        bx = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                        if not inside.contains(bx) or bx.intersects(static[side]["copper"]) or \
                                bx.intersects(static[side]["crt"]) or bx.intersects(others):
                            continue
                        score = gap + 0.6 * abs(sl) + (0.8 if ang else 0)
                        out.append((score, cx - cx_off, cy - cy_off, ang, bx))
        out.sort(key=lambda t: t[0])
        cands[ref] = (f, side, out)
    chosen = {}                                   # ref -> index into its candidate list

    def clash(ref, i, skip=()):
        side, bx = cands[ref][1], cands[ref][2][i][4].buffer(REF_GAP)
        return [r for r, j in chosen.items() if r != ref and r not in skip and cands[r][1] == side
                and bx.intersects(cands[r][2][j][4])]

    hidden = []
    for ref in sorted(cands, key=lambda r: (len(cands[r][2]), r)):
        i = next((i for i in range(len(cands[ref][2])) if not clash(ref, i)), None)
        if i is None:
            hidden.append(ref)
        else:
            chosen[ref] = i
    # repair: a hidden reference takes a spot held by one neighbour, if that neighbour has another clear spot
    for ref in list(hidden):
        for i in range(len(cands[ref][2])):
            c = clash(ref, i)
            if len(c) != 1:
                continue
            p = c[0]
            chosen[ref] = i
            k = next((k for k in range(len(cands[p][2])) if not clash(p, k)), None)
            if k is None:
                del chosen[ref]
                continue
            chosen[p] = k
            hidden.remove(ref)
            break
    placed = {r: (cands[r][0],) + tuple(cands[r][2][i][1:4]) for r, i in chosen.items()}
    return board, placed, hidden


def lay(board, placed, hidden):
    from kipy.geometry import Vector2
    fps = []
    for ref, (f, x, y, ang) in placed.items():
        fld = f.reference_field
        fld.text.position = Vector2.from_xy(round(x * 1e6), round(y * 1e6))
        fld.text.proto.text.attributes.angle.value_degrees = ang
        fld.visible = True
        f.reference_field = fld
        fps.append(f)
    for f in board.get_footprints():
        if f.reference_field.text.value in hidden:
            fld = f.reference_field
            fld.visible = False
            f.reference_field = fld
            fps.append(f)
    commit = board.begin_commit()
    board.update_items(fps)
    board.push_commit(commit, "Step 7.1: reference designators placed")
    board.save()


if __name__ == "__main__":
    B, P, H = plan()
    print(f"{len(P)} references placed; hidden on the silkscreen: {', '.join(sorted(H)) or 'none'}")
    if len(sys.argv) > 1 and sys.argv[1] == "lay":
        lay(B, P, H)
        print("laid and saved")
