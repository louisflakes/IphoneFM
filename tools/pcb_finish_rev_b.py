"""Rev B Phase B6: pours and stitching on the Rev B board, as Rev A Phase 6, by file edits with KiCad's own Python
(the Rev B board is not open in KiCad; Rev A's tools work through KiCad's live API).

Usage (from the repository root):
  "%LOCALAPPDATA%/Programs/KiCad/10.0/bin/python.exe" -u tools/pcb_finish_rev_b.py STEP
Steps:
  stitch   B6.2  Rev A's stitching grid (tools/pcb_stitch.py: 3 mm across the board, 1.5 mm inside the RF zones, the
                 same grid origin) wherever a site is free now: both pours' fills cover the via with 0.1 mm to spare,
                 0.2 mm from every other net's copper, 0.5 mm hole to hole, 0.8 mm between vias. One rule added for
                 Rev B: no via in a ground SMD pad (0.2 mm clear of it). Run after a fill.
  balance  B6.5  copper cover of each side (pours, tracks, pads) as a share of the board
"""
import math
import os
import sys

import pcbnew
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, os.path.dirname(__file__))
from pcb_astar import board_copper          # noqa: E402
from pcb_freeroute import RF_BOTTOM_POLYS   # noqa: E402
from pcb_stitch import BOARD as GRID, VIA_R, DRILL_R   # noqa: E402  (Rev A's grid and via)

PCB = "kicad/rev-b/IphoneFM.kicad_pcb"
VIA_SIZE, VIA_DRILL = 0.6, 0.3


def fills(board):
    """Filled copper of the ground pours per layer as shapely geometry."""
    out = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND":
            continue
        for layer in out:
            if not z.IsOnLayer(layer):
                continue
            ps = z.GetFilledPolysList(layer)
            for i in range(ps.OutlineCount()):
                ring = lambda c: [(pcbnew.ToMM(c.CPoint(j).x), pcbnew.ToMM(c.CPoint(j).y)) for j in range(c.PointCount())]
                outline = ring(ps.Outline(i))
                holes = [ring(ps.Hole(i, h)) for h in range(ps.HoleCount(i))]
                if len(outline) >= 3:
                    out[layer].append(Polygon(outline, holes).buffer(0))
    return {k: unary_union(v) for k, v in out.items()}


def step_stitch():
    board = pcbnew.LoadBoard(PCB)
    copper = board_copper(open(PCB, encoding="utf-8").read())
    f = fills(board)
    both = f[pcbnew.F_Cu].intersection(f[pcbnew.B_Cu]).buffer(-(VIA_R + 0.1))
    rf = unary_union([Polygon(p) for p in RF_BOTTOM_POLYS])
    others = []
    for k, n, l, g, name in copper:
        if n == "GND" and not (k == "pad" and g[5] == 0):   # ground tracks, vias and holes are free to touch
            continue
        if k == "pad":
            x, y, hw, hh, sh, _ = g
            others.append(Point(x, y).buffer(hw) if sh == "circle" else box(x - hw, y - hh, x + hw, y + hh))
        elif k == "track":
            others.append(LineString([g[:2], g[2:4]]).buffer(g[4]))
        else:
            others.append(Point(g[0], g[1]).buffer(g[2]))
    keep_out = unary_union(others).buffer(0.2 + VIA_R)
    holes = [(g[0], g[1], g[3] if k == "via" else g[5]) for k, n, l, g, _ in copper
             if k == "via" or (k == "pad" and g[5] > 0)]
    vias = [(g[0], g[1]) for k, n, l, g, _ in copper if k == "via"]
    gnd = board.FindNet("GND")
    new = []
    for pitch, in_rf in ((1.5, True), (3.0, False)):
        x = GRID[0] + pitch / 2
        while x < GRID[2]:
            y = GRID[1] + pitch / 2
            while y < GRID[3]:
                pt = Point(x, y)
                if rf.contains(pt) == in_rf and both.contains(pt) and not keep_out.contains(pt) and \
                        all(math.hypot(x - hx, y - hy) >= DRILL_R + hr + 0.5 for hx, hy, hr in holes) and \
                        all(math.hypot(x - vx, y - vy) >= 0.8 for vx, vy in vias):
                    v = pcbnew.PCB_VIA(board)
                    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(round(x, 3)), pcbnew.FromMM(round(y, 3))))
                    v.SetWidth(pcbnew.FromMM(VIA_SIZE)); v.SetDrill(pcbnew.FromMM(VIA_DRILL))
                    v.SetNet(gnd)
                    board.Add(v)
                    new.append((round(x, 3), round(y, 3)))
                    vias.append((x, y)); holes.append((x, y, DRILL_R))
                y += pitch
            x += pitch
    pcbnew.SaveBoard(PCB, board)
    print(f"stitch: {len(new)} vias added")
    for p in new:
        print("  ", p)
    os._exit(0)


def step_balance():
    board = pcbnew.LoadBoard(PCB)
    copper = board_copper(open(PCB, encoding="utf-8").read())
    f = fills(board)
    outline = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(outline, True)
    o = outline.Outline(0)
    area = Polygon([(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]).area
    for layer, name in ((pcbnew.F_Cu, "F.Cu"), (pcbnew.B_Cu, "B.Cu")):
        shapes = [f[layer]]
        for k, n, l, g, _ in copper:
            if name not in l:
                continue
            if k == "pad":
                x, y, hw, hh, sh, _ = g
                shapes.append(Point(x, y).buffer(hw) if sh == "circle" else box(x - hw, y - hh, x + hw, y + hh))
            elif k == "track":
                shapes.append(LineString([g[:2], g[2:4]]).buffer(g[4]))
            else:
                shapes.append(Point(g[0], g[1]).buffer(g[2]))
        print(f"{name}: {100 * unary_union(shapes).area / area:.0f}% of {area:.0f} mm2")
    os._exit(0)


if __name__ == "__main__":
    globals()["step_" + sys.argv[1]]()
