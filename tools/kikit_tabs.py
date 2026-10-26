"""Step 8.3 (panel): a KiKit hook plugin that puts the break-off tabs where no part sits within 2 mm of the board edge
(courtyards, checked 2026-10-26): two on the top edge either side of SW3, one on the left edge above the wheels, two
on the right edge between R20/R21 and J2. The bottom edge has no 1.5 mm stretch clear of J1, SW1, SW2 and the
filter, so it gets none. Positions are in millimetres from the board's top-left corner.
Also adds the three top-side fiducials once the panel is built.
Used by tools/pcb_panel.sh: kikit panelize ... --plugin tools/kikit_tabs.py.Tabs"""
from kikit.annotations import TabAnnotation
from kikit.plugin import HookPlugin
from kikit.units import mm

# (edge, position along it in mm, width in mm)
TABS = [("top", 8.9, 3.0), ("top", 37.5, 3.0), ("left", 5.1, 3.0), ("right", 30.0, 3.0), ("right", 54.0, 3.0)]


class Tabs(HookPlugin):
    def afterLayout(self, panel, substrates):
        s = list(substrates)[0]
        x0, y0, x1, y1 = s.bounds()
        inward = {"top": (0, 1), "bottom": (0, -1), "left": (1, 0), "right": (-1, 0)}
        for edge, pos, width in TABS:
            if edge in ("top", "bottom"):
                origin = (x0 + pos * mm, y0 if edge == "top" else y1)
            else:
                origin = (x0 if edge == "left" else x1, y0 + pos * mm)
            s.annotations.append(TabAnnotation(None, origin, inward[edge], width * mm))

    def finish(self, panel):
        # three fiducials on the top rails, to JLC's size: 1 mm copper, 2 mm mask opening, the opening 3.35 mm from the
        # panel edge (centre 4.35 mm in); only the top side is assembled
        for i, pos in enumerate(panel.panelCorners(4.35 * mm, 4.35 * mm)[:3]):
            panel.addFiducial(pos, 1 * mm, 2 * mm, False, False, ref=f"FID{i + 1}")
