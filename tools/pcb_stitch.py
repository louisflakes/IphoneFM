"""Step 6.2: ground stitching vias between the two pours, on a grid: 3 mm across the board and 1.5 mm inside the RF
zones (RF_BOTTOM_POLYS), where the ground under and beside the 50 ohm lines matters most [AN383 p15-16; ADI "Ground
Planes"; BAC p22]. A site is kept only where both pours' fills cover the whole via with 0.1 mm to spare, it clears
every other net's copper by 0.2 mm, holes by 0.5 mm (hole to hole) and other vias by 0.8 mm centre to centre.
Run after the pours are filled.
Usage (from the repository root, board open in KiCad): python tools/pcb_stitch.py [list] | lay [--dry-run]"""
import math
import sys

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, "tools")
from pcb_freeroute import RF_BOTTOM_POLYS
from pcb_plan import Plan, main

VIA_R, DRILL_R = 0.3, 0.15
BOARD = (12.7, 59.56, 59.15, 130.96)


def fills(board):
    """Filled ground polygons per layer (3 = F.Cu, 34 = B.Cu) as shapely geometry."""
    out = {3: [], 34: []}
    for z in board.get_zones():
        if z.is_rule_area() or not z.proto.filled_polygons:
            continue
        for lp in z.proto.filled_polygons:
            for poly in lp.shapes.polygons:
                ring = [(n.point.x_nm / 1e6, n.point.y_nm / 1e6) for n in poly.outline.nodes]
                holes = [[(n.point.x_nm / 1e6, n.point.y_nm / 1e6) for n in h.nodes] for h in poly.holes]
                if len(ring) >= 3:
                    out[lp.layer].append(Polygon(ring, holes))
    return {k: unary_union(v) for k, v in out.items()}


def build():
    from kipy import KiCad
    from pcb_astar import board_copper
    board = KiCad().get_board()
    copper = board_copper(board.get_as_string())
    f = fills(board)
    both = f[3].intersection(f[34]).buffer(-(VIA_R + 0.1))
    rf = unary_union([Polygon(p) for p in RF_BOTTOM_POLYS])
    others = []
    for k, n, l, g, _ in copper:
        if n == "GND":
            continue
        if k == "pad":
            x, y, hw, hh, sh, _ = g
            others.append(Point(x, y).buffer(hw) if sh == "circle" else box(x - hw, y - hh, x + hw, y + hh))
        elif k == "track":
            from shapely.geometry import LineString
            others.append(LineString([g[:2], g[2:4]]).buffer(g[4]))
        else:
            others.append(Point(g[0], g[1]).buffer(g[2]))
    keep_out = unary_union(others).buffer(0.2 + VIA_R)
    holes = [(g[0], g[1], g[3] if k == "via" else g[5]) for k, n, l, g, _ in copper
             if k == "via" or (k == "pad" and g[5] > 0)]
    vias = [(g[0], g[1]) for k, n, l, g, _ in copper if k == "via"]
    P = Plan()
    for pitch, region in ((1.5, rf), (3.0, None)):
        x = BOARD[0] + pitch / 2
        while x < BOARD[2]:
            y = BOARD[1] + pitch / 2
            while y < BOARD[3]:
                pt = Point(x, y)
                inside_rf = rf.contains(pt)
                if (region is None and not inside_rf) or (region is not None and inside_rf):
                    if both.contains(pt) and not keep_out.contains(pt) and \
                            all(math.hypot(x - hx, y - hy) >= DRILL_R + hr + 0.5 for hx, hy, hr in holes) and \
                            all(math.hypot(x - vx, y - vy) >= 0.8 for vx, vy in vias):
                        P.via("GND", round(x, 3), round(y, 3))
                        vias.append((x, y))
                        holes.append((x, y, DRILL_R))
                y += pitch
            x += pitch
    return P


def plan(copper=None):
    return build().copper()


if __name__ == "__main__":
    PL = build()
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print(f"{len(PL.vias)} stitching vias")
    else:
        main(PL, "Phase 6.2: ground stitching vias")
