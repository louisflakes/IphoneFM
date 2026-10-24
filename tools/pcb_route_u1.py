"""Phase 5: U1's connections laid by hand (pcb_astar.route), in order, each locked and seen by the next, live in the
board open in KiCad. Order follows the books: a part's own decoupling and local parts at its pins first [BAC p21-22;
HHG p40], then the short critical links (U2's MICROWIRE, I2S and reference) [LMX2571 p55], then the runs to the
connectors and controls, then the long runs over U2 to the right of the transmit line (U4, D1, U2's CE) [the user's
no-crossing choice, step 4.9]. A connection with no path is reported and skipped.
Usage (from the repository root, board open in KiCad): python tools/pcb_route_u1.py [--from N] [--only NET] [--dry-run]"""
import sys
import time

sys.path.insert(0, "tools")
from pcb_astar import route

S, P = 0.2, 0.3  # signal width; supply links at a pin (narrower than the 0.4 power class where they meet 0.25 mm pins)
# (net, from, to, width, layers, search margin mm)
PLAN = [
    # 1. U1's own parts at its pins
    ("3V3", "U1.24", "C3.1", P, "F", 4), ("3V3", "U1.24", "C4.1", P, "F", 4), ("3V3", "U1.36", "C5.1", P, "F", 4),
    ("3V3", "U1.48", "C6.1", P, "F", 4), ("3V3", "U1.1", "C6.1", P, "FB", 6),
    ("VDDA", "U1.9", "C7.1", P, "F", 4), ("VDDA", "U1.9", "C8.1", P, "F", 4), ("VDDA", "U1.9", "FB2.2", P, "F", 4),
    ("/VCAP", "U1.22", "C9.1", S, "F", 4), ("/NRST", "U1.7", "C10.1", S, "F", 4),
    ("/WHEEL1", "U1.12", "C39.1", S, "F", 4), ("/WHEEL2", "U1.13", "C40.1", S, "F", 4), ("/WHEEL3", "U1.15", "C41.1", S, "F", 4),
    ("/RX_FS_MCU", "U1.14", "C36.1", S, "F", 4), ("/BOOT0", "U1.44", "R3.1", S, "F", 4),
    ("/FSK_CLK_MCU", "U1.29", "R6.1", S, "F", 4), ("/FSK_FS_MCU", "U1.30", "R7.1", S, "F", 4), ("/FSK_DATA_MCU", "U1.31", "R8.1", S, "F", 4),
    # 2. short critical links to U2 and the reference
    ("/FSK_CLK", "R6.2", "U2.4", S, "FB", 10), ("/FSK_FS", "R7.2", "U2.7", S, "FB", 10), ("/FSK_DATA", "R8.2", "U2.6", S, "FB", 10),
    ("/LMX_DATA", "U1.28", "U2.12", S, "FB", 10), ("/LMX_CLK", "U1.26", "U2.11", S, "FB", 10),
    ("/LMX_LE", "U1.25", "U2.13", S, "FB", 10), ("/LMX_MUX", "U1.27", "U2.10", S, "FB", 10), ("/LMX_MUX", "U1.27", "TP5.1", S, "FB", 10),
    ("/REF20", "Y2.3", "R4.1", S, "F", 4), ("/REF20", "Y2.3", "U2.34", S, "FB", 10), ("/REF20_MCU", "R4.2", "U1.5", S, "FB", 10),
    # 3. connectors, controls and test pads
    ("/USB_DP", "U1.33", "U6.1", S, "FB", 10), ("/USB_DM", "U1.32", "U6.3", S, "FB", 10),
    ("/CC1", "U1.10", "R1.1", S, "FB", 10), ("/CC2", "U1.11", "R2.1", S, "FB", 10),
    ("/WHEEL1", "C39.1", "RV1.2", S, "FB", 10), ("/WHEEL2", "C40.1", "RV2.2", S, "FB", 10), ("/WHEEL3", "C41.1", "RV3.2", S, "FB", 10),
    ("/NRST", "C10.1", "TP6.1", S, "FB", 10), ("/SWCLK", "U1.37", "TP7.1", S, "FB", 10), ("/SWDIO", "U1.34", "TP8.1", S, "FB", 10),
    ("/BOOT0", "R3.1", "SW2.2", S, "FB", 15), ("/RF_MODE", "U1.18", "SW1.2", S, "FB", 15),
    # 4. long runs over U2, to the right of the transmit line
    ("/I2C_SCL", "U1.42", "U4.7", S, "FB", 40), ("/I2C_SDA", "U1.43", "U4.8", S, "FB", 40),
    ("/RX_RCLK", "U1.45", "U4.9", S, "FB", 40), ("/RX_SCK_MCU", "U1.39", "R24.2", S, "FB", 40),
    ("/RX_SD_MCU", "U1.41", "R22.2", S, "FB", 40), ("/RX_FS_MCU", "C36.1", "R23.2", S, "FB", 40),
    ("/RX_RST", "U1.16", "U4.5", S, "FB", 40), ("/LMX_CE", "U1.20", "U2.19", S, "FB", 40),
    ("/LED_R", "U1.40", "R25.1", S, "FB", 40), ("/LED_G", "U1.21", "R26.1", S, "FB", 40), ("/LED_B", "U1.19", "R27.1", S, "FB", 40),
]


def main():
    from kipy import KiCad
    board = KiCad().get_board()
    start = int(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    failed = []
    for k, (net, a, b, w, layers, margin) in enumerate(PLAN):
        if k < start or (only and net != only):
            continue
        t0 = time.time()
        res = route(board, net, a, b, w, layers, margin=margin, dry="--dry-run" in sys.argv)
        if res:
            runs, vias, length = res
            print(f"{k:2} ok   {net:14} {a:>7} -> {b:<7} {length:5.1f} mm  vias {len(vias)}  {''.join('FB'[l] for l, _ in runs)}  ({time.time() - t0:.0f} s)", flush=True)
        else:
            failed.append(f"{net} {a}->{b}")
            print(f"{k:2} FAIL {net:14} {a:>7} -> {b:<7} ({time.time() - t0:.0f} s)", flush=True)
    print("failed:", failed)


if __name__ == "__main__":
    main()
