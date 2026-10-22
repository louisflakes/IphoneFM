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

Sources, read 2026-10-21:
- [PCB Assembly Capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities) (no revision date on the page).
- [Terms and Conditions of JLCPCB Assembly Service](https://jlcpcb.com/help/article/Terms-and-Conditions-of-JLCPCB-Assembly-Service), updated 2026-09-09.
- [How to Add Edge Rails and Fiducials for PCB Assembly Orders](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order), updated 2026-09-09.

### The two assembly services

| | Economic PCBA | Standard PCBA | Rev A |
|---|---|---|---|
| Board size | single 10 × 10 to 470 × 500 mm | single 70 × 70 to 460 × 500 mm | 46.45 × 71.40 mm: Economic as a single board; Standard needs a panel or rails |
| Thickness | 0.8–1.6 mm | any | 1.6 mm |
| Quantity | 2–50 | 2–80,000 | about 6 |
| Smallest package | 0402 | 01005 | 0402 |
| Finest IC pitch | 0.4 mm | 0.35 mm | 0.5 mm |
| Sides | one side only, SMT or through-hole | one or both | top only |
| Edge rails, fiducials | not necessary | necessary | |
| Reflow | 255 ± 5 °C | 240 ± 5 °C | |

Rev A fits Economic on every line. Whether Economic takes our two global-sourcing parts (U1, SW3) and the through-hole J2 is confirmed at the quote, step 8.5.

### Rules that apply to every assembly order

| Rule | JLC wording | Source |
|---|---|---|
| Part body to board edge | "must be equal or greater than 2.5mm" | Terms |
| Part to part | No overlaps or "very small gap"; about 0.3 mm between bodies | Terms; JLC blog |
| Footprints | IPC-7351B "medium density" or "low density"; "High density is not supported" | Terms |
| Through-hole parts | Placement checked in the 3D production file | Terms |
| Rails | At least 5 mm wide; their purpose is "to increase the distance between components and the board edge"; JLC picks a rail method itself for boards under 70 × 70 mm | Rails article; Terms |
| Fiducials | 1 mm bare copper pad, 2 mm mask opening, three or four along the edges, at least 3.35 mm from the edge | Rails article |

### What this means for Rev A

Rev A puts parts at all four edges on purpose:
- **Left:** RV1–RV3 rims 2.9 mm past the edge; SW1's handle 0.9 mm past.
- **Right:** J2's barrel 7.45 mm past the edge.
- **Bottom:** J1 flush with the edge; SW2's knob 0.35 mm past.
- **Top:** SW3's levers 1.35 mm inside the edge.

So the 2.5 mm body-to-edge rule can't be met on the board itself; it has to come from rails. A rail along an edge with an overhanging part would hit that part. The plan:
- **Rails on the top and bottom edges only,** at least 5 mm wide, joined by mouse bites with JLC's 1.6–2 mm gap. Nothing on those edges overhangs by more than SW2's 0.35 mm.
- **Fiducials on the rails,** to JLC's size and spacing.
- **Left and right edges free,** for the wheels, SW1 and J2's barrel.

The plan is to confirm this with JLC at the quote: either they add these rails, or we panelize ourselves in phase 8.

Two more rules carry into later phases:
- **Phase 2 (footprints):** use IPC-7351B nominal (medium-density) footprints, which is what KiCad's library uses.
- **Phase 4 (placement):** keep at least 0.3 mm between part bodies; our own rule M11 already asks for 2 mm.

## Our design rules (step 0.5)

To do.

## 50 Ω line for the antenna path (step 0.6)

To do.
