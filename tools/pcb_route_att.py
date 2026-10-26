"""Phase 5, floorplan B3: the attenuator bus, U7's six control lines ATT_C0_5..ATT_C16 to their pull-downs R15..R10 and
SW3 on the top edge, planned as copper (tools/pcb_plan.py) and checked before it is laid. The lines carry static DC
levels, so length is free (placement-rules.md M4); what matters is that they cross nothing else.
  south  out of U7's east pins into six lanes, north, then north-east beside the receive line (0.76 mm off its
         centre, its west stitching vias left out there) and north again up to the receiver corner;
  hop    west in a staircase of vias south of the receiver bundle, under it on the bottom, north up the gap between
         REF20/CE's vias and the bundle, and up again in a staircase in the clear area west of the U4 corner
         (RST runs on top there, so the bottom is free);
  north  east above the bundle's turn, north between R15..R10 (each line takes its resistor on the way), west over
         H2 and under SW3's body into its pins.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_att.py place | lay [--dry-run]"""
import sys

sys.path.insert(0, "tools")
from pcb_plan import B, Plan, jog, main, turn

P = Plan()
W = 0.2
NETS = ["/ATT_C0_5", "/ATT_C1", "/ATT_C2", "/ATT_C4", "/ATT_C8", "/ATT_C16"]   # west to east in every lane group
PIN = {n: 24 - k for k, n in enumerate(NETS)}                                    # U7 pins 24 (C0_5) .. 19 (C16)
SW3_X = {n: 32.75 + 1.27 * k for k, n in enumerate(NETS)}                        # SW3 pins 6 .. 1
R_X = {n: 47.9 + 1.3 * k for k, n in enumerate(NETS)}                            # R15 .. R10
R_REF = {n: f"R{15 - k}" for k, n in enumerate(NETS)}

for n in NETS:
    P.place[R_REF[n]] = (R_X[n], 71.8, -90)       # 1.7 mm east of the group's spot: the lanes pass east of H2

# ---- south: U7 east pins -> lanes 46.6..48.6, north-east beside RX, north at 51.64..53.64
L1 = [46.6 + 0.4 * k for k in range(6)]
L2 = [51.57 + 0.4 * k for k in range(6)]
C = [160.2 + 0.566 * k for k in range(6)]                  # x + y of each diagonal beside the receive line
U7 = turn([(44.775, 116.55 + 0.5 * k) for k in range(6)], (1, 0), (0, -1), L1, 0.4, tips=0.4, min_exit=1.0)
# ---- the down staircase: rows west at 95.2 .. 92.2, each into its via
ROW_D = [95.5 - 0.6 * k for k in range(6)]   # 0.8 mm off SCK's diagonal (Clock class)
VD = [(51.05 - 0.6 * k, ROW_D[k]) for k in range(6)]
# ---- bottom: rows west, north up the gap at 43.8..45.8, jog west into the up staircase
L3 = [44.0 + 0.4 * k for k in range(6)]
VU = [(42.0 + 0.6 * k, 78.6 + 0.6 * k) for k in range(6)]
# ---- top north of the bundle: rows east at 73.0 .. 75.5, north between the resistors, west into SW3
ROW_E = [73.1 + 0.5 * k for k in range(6)]
L4 = [R_X[n] - 0.65 for n in NETS]
ROW_W = [64.6 - 0.5 * k for k in range(6)]

J = jog([(L3[k], 84.0) for k in range(6)], (0, -1), (-1, 0), [L3[k] - VU[k][0] for k in range(6)], 0.4)

for k, n in enumerate(NETS):
    s, b1, b2 = U7[k]
    y1 = C[k] - L1[k]                                        # where the lane turns north-east
    y2 = C[k] - L2[k]                                        # where it turns north again
    P.run(n, [s, b1, b2, (L1[k], y1), (L2[k], y2), (L2[k], ROW_D[k] + 0.4), (L2[k] - 0.4, ROW_D[k]), VD[k]])
    P.via(n, *VD[k])
    e = 2.57 - 0.434 * k                                     # concentric west->north turn into the gap
    P.run(n, [VD[k], (L3[k] + e, ROW_D[k]), (L3[k], ROW_D[k] - e)] + J[k] + [VU[k]], W, B)
    P.via(n, *VU[k])
    x, re, xl, rw, xs = VU[k][0], ROW_E[k], L4[k], ROW_W[k], SW3_X[n]
    P.run(n, [VU[k], (x, re + 0.4), (x + 0.4, re), (xl - 0.4, re), (xl, re - 0.4), (xl, 71.29)])
    P.run(n, [(xl, 71.29), (R_X[n], 71.29)])                                       # R*.1
    P.run(n, [(xl, 71.29), (xl, rw + 0.4), (xl - 0.4, rw), (xs + 0.4, rw), (xs, rw - 0.4), (xs, 60.7)])


def plan(copper=None):
    return P.copper()


if __name__ == "__main__":
    main(P, "Phase 5: attenuator bus")
