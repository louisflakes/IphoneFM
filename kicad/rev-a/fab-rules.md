# Rev A fab and assembly rules

The board-house numbers the Rev A layout is built against. Fab rules override every book figure in [docs/pcb-design-workflow.md](../../docs/pcb-design-workflow.md) [HHG p15, p63–65; BAC p4, p11]. Filled in by steps 0.3–0.6 of [kicad-build-procedure.md](../../design/rev-a/kicad-build-procedure.md).

## JLCPCB PCB capabilities, 2-layer FR-4 (step 0.3)

Source: [JLCPCB Rigid PCB Manufacturing Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), read 2026-10-21 (the page shows no revision date). Figures are for 1–2 layer boards, 1.6 mm, 1 oz outer copper, unless marked otherwise. The key rows were read twice and agree.

### Traces and copper

| Item | JLC minimum | Notes |
|---|---|---|
| Track width / spacing | 0.10 / 0.10 mm (4 / 4 mil) | Width tolerance ±20% |
| Pad to track | 0.10 mm | |
| SMD pad to pad (different nets) | 0.15 mm | |
| Smallest SMD pad | 0.25 × 0.25 mm | |

### Vias and plated holes

| Item | JLC minimum | Notes |
|---|---|---|
| Via hole / via pad | 0.15 / 0.25 mm | Preferred hole 0.2 mm or larger; pad 0.15 mm larger than the hole preferred |
| Drill range | 0.15–6.3 mm | |
| PTH annular ring | 0.18 mm absolute, 0.25 mm recommended | General table: ≥ 0.20 mm |
| Recommended PTH hole | ≥ 0.5 mm | Avoids mask or tin in the hole |
| Hole size tolerance | +0.13 / −0.08 mm | Position ±0.075 mm |
| Via hole to via hole | 0.2 mm | |
| Pad hole to pad hole | 0.45 mm | |
| Via hole to track | 0.2 mm | |
| PTH to track | 0.28 mm, 0.35 mm recommended | |
| NPTH to track | 0.2 mm | |

### Non-plated holes and slots

| Item | JLC minimum |
|---|---|
| NPTH | 0.50 mm |
| Plated slot width | 0.5 mm, length at least 2× width; tolerance +0.13 / −0.08 mm |
| Non-plated slot width | 1.0 mm; tolerance ±0.2 mm |

These matter for J1's shell slots (0.6 mm plated) and its two Ø0.6 mm locating holes, and for SW1's two Ø0.85 mm post holes.

### Solder mask

| Item | JLC figure |
|---|---|
| Mask opening | 1:1 with the pad; keep ≥ 0.09 mm from a neighbouring trace |
| Mask bridge, 1 oz | 0.10 mm (green and other colours), 0.13 mm (black, white) |

### Silkscreen

| Item | JLC minimum |
|---|---|
| Line width | 0.15 mm |
| Text height | 1.0 mm (40 mil), width:height about 1:6 |
| Pad to silkscreen | 0.15 mm |

The workflow's own rule is lines at least 0.25 mm [BAC p13; KHA p149], which is stricter.

### Outline and board

| Item | JLC figure |
|---|---|
| Copper to routed edge | ≥ 0.2 mm |
| Routed edge tolerance | ±0.2 mm (±0.1 mm high precision) |
| Thickness tolerance at 1.6 mm | ±10% (1.44–1.76 mm) |

The workflow's own floor is 0.5 mm from copper to edge [HHG p105, p113; conflict C3], which is stricter than JLC's 0.2 mm.

## JLCPCB assembly rules (step 0.4)

To do.

## Our design rules (step 0.5)

To do.

## 50 Ω line for the antenna path (step 0.6)

To do.
