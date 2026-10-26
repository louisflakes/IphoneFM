"""Phase 7, after the checks: the board's tag on the top silkscreen, in the open ground pour west of H1. "CLAUDE / WAS
HERE" over a frequency-modulated wave, the board's own job drawn as one line: a carrier whose cycles bunch and spread
as the audio pushes it. Text 1.2 mm high with a 0.18 mm stroke, the wave 0.25 mm wide (fab-rules.md: text 1.0 mm and
0.15 mm at least, lines 0.25 mm). Every line sits between the rows of the 3 mm stitching grid (y 61.06, 64.06, 67.06,
70.06), clear of the via holes.
Usage (from the repository root, board open in KiCad): python tools/pcb_tag.py [list] | lay"""
import math
import sys

X0, X1 = 14.0, 22.2          # the wave's span; the text is centred over it
WAVE_Y, AMP = 68.56, 0.85
TEXT = [("CLAUDE", 62.56), ("WAS HERE", 65.56)]
CARRIER, DEVIATION = 0.75, 0.33   # cycles per mm, and the swing either side
WIDTH, STEP = 0.25, 0.05


def wave():
    """The FM line as points: frequency CARRIER +- DEVIATION, one full swing of the audio over the span."""
    pts, phase, x = [], 0.0, X0
    while x <= X1 + 1e-9:
        pts.append((round(x, 4), round(WAVE_Y - AMP * math.sin(phase), 4)))
        f = CARRIER + DEVIATION * math.sin(2 * math.pi * (x - X0) / (X1 - X0))
        phase += 2 * math.pi * f * STEP
        x += STEP
    return pts


def items():
    from kipy.board_types import BoardLayer, BoardSegment, BoardText
    from kipy.proto.common.types import HorizontalAlignment
    from kipy.geometry import Vector2
    out = []
    pts = wave()
    for a, b in zip(pts, pts[1:]):
        s = BoardSegment()
        s.layer = BoardLayer.BL_F_SilkS
        s.start = Vector2.from_xy_mm(*a)
        s.end = Vector2.from_xy_mm(*b)
        s.attributes.stroke.width = round(WIDTH * 1e6)
        out.append(s)
    for value, y in TEXT:
        t = BoardText()
        t.value = value
        t.layer = BoardLayer.BL_F_SilkS
        t.position = Vector2.from_xy_mm((X0 + X1) / 2, y)
        t.attributes.size = Vector2.from_xy_mm(1.2, 1.2)
        t.attributes.stroke_width = round(0.18 * 1e6)
        t.attributes.horizontal_alignment = HorizontalAlignment.HA_CENTER
        out.append(t)
    return out


if __name__ == "__main__":
    print(f"{len(wave()) - 1} wave segments, {len(TEXT)} lines of text")
    if len(sys.argv) > 1 and sys.argv[1] == "lay":
        from kipy import KiCad
        board = KiCad().get_board()
        commit = board.begin_commit()
        board.create_items(items())
        board.push_commit(commit, "Phase 7: the tag")
        board.save()
        print("laid and saved")
