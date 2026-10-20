# Plan C passive packages and land patterns

Body sizes and recommended reflow land patterns for every passive and for Y2, each from the manufacturer's own document (files in [`docs/datasheets/plan-c/`](../../docs/datasheets/README.md)). Read from the page images, 2026-10-19.
ICs, connectors, switches, Y1, D1 and D2 are not covered here; their package drawings are in their own datasheets.

Terms used below (all mm):
- **Pad L** is along the part's long axis and **pad W** is across it.
- **Gap** is the distance between the inner edges of the two pads.
- **Pitch** is the distance between the two pad centres.

Where a maker gives a range, **Drawn as** uses the midpoint.

## Bodies

| Part(s) | Size | L × W × T | Terminal | Source |
|---|---|---|---|---|
| Murata GRM155 / GRM1555, all 13 values in the BOM, and GJM1555C1H6R0CB01D (C14) | 0402 | 1.0 ±0.05 × 0.5 ±0.05 × 0.5 ±0.05 | 0.15–0.35 | Murata product page per part; GJM spec sheet p2 |
| Murata BLM15GA750SN1D (FB1) | 0402 | 1.0 ±0.05 × 0.5 ±0.05 × 0.5 ±0.05 | 0.25 ±0.1 | BLM15G reference spec p2 |
| Yageo RC0402FR-07… | 0402 | 1.00 ±0.05 × 0.50 ±0.05 × 0.35 ±0.05 | I1 0.20 ±0.10, I2 0.25 ±0.10 | R_Yageo_RC_L_V14 p4, Table 1 |
| Panasonic ERJ-2RKF… | 0402 | 1.00 ±0.05 × 0.50 ±0.05 × 0.35 ±0.05 | a 0.20 ±0.10, b 0.25 ±0.05 | R_Panasonic_ERJ_precision p4 |
| TDK C1608X7R1C105K080AC | 0603 | 1.60 ±0.10 × 0.80 ±0.10 × 0.80 ±0.10 | B ≥ 0.20, G ≥ 0.30 | TDK product page |
| Murata GRM188R71A225KE15D | 0603 | 1.6 ±0.1 × 0.8 ±0.1 × 0.8 ±0.1 | 0.2–0.5 | Murata product page |
| Murata GRM21BR71C475KE51L | 0805 | 2.0 ±0.15 × 1.25 ±0.15 × 1.25 ±0.15 | 0.2–0.7 | Murata product page |
| Yageo CC0805KRX5R7BB106 | 0805 | 2.0 ±0.20 × 1.25 ±0.20 × 0.85 ±0.10 (class EA) | L2/L3 0.25–0.75, L4 ≥ 0.7 | MLCC_Yageo_CC_X5R_V32 p3, p6, p8 |
| Coilcraft 0805CS-101XJRC, -331XJRC | 0805 | 2.29 max × 1.73 max × 1.52 max | E 1.27 (wraps 0.38 at each end) | L_Coilcraft_0805CS p2 |
| KEMET T491A106K010AT, T491A156K006AT | A, 3216-18 | 3.2 ±0.2 × 1.6 ±0.2 × 1.6 ±0.2 | F 1.2 ±0.1, S 0.80 +0.2/−0.3 | Tant_KEMET_T491 p4 |
| Epson TSX-3225 16.0000MF09Z-AC0 (Y2) | 4-pad SMD | 3.2 ±0.15 × 2.5 ±0.15 × 0.6 max | 4 pads | Y2_Epson_TSX-3225 p1 |

- **CC0805 thickness:** 10 µF at 16 V comes in class EA (0.85 mm) or EB (1.25 mm) (p6). EB ships only on blister tape, but our part's "R" packing code means paper tape (p2, p8), so it is EA. DigiKey lists 1.45 mm max, which is wrong for this part.
- **0805CS height:** add 0.152 mm for solder (p2 note).

## Land patterns (reflow)

| Part(s) | Published | Drawn as: pad L × W, gap, pitch | Source |
|---|---|---|---|
| Murata GRM155 / GRM1555 and GJM155 (body ±0.05, "within ±0.10" row) | a 0.3–0.5 (gap), b 0.35–0.45 (pad L), c 0.4–0.6 (pad W) | 0.40 × 0.50, 0.40, 0.80 | MLCC_Murata_C02E p278, Table 2 |
| Murata BLM15G | a 0.4 (gap), b 1.2 (outer), c 0.5 (pad W) | 0.40 × 0.50, 0.40, 0.80 | BLM15G reference spec p6, §12.1 |
| Yageo RC0402 | A 1.5 (outer), B 0.5 (gap), C 0.5 (pad L), D 0.6 (pad W); placement ±0.15 | 0.50 × 0.60, 0.50, 1.00 | R_Yageo_mounting_V10 p4, Table 1 |
| Panasonic ERJ-2RK (1005) | a 0.5–0.6 (gap), b 1.4–1.6 (outer), c 0.4–0.6 (pad W) | 0.475 × 0.50, 0.55, 1.025 | R_Panasonic_land_pattern p1 |
| TDK C1608 | PA, PB, PC each 0.60–0.80 | 0.70 × 0.70, 0.70, 1.40 | TDK product page |
| Murata GRM188 (body ±0.1, "within ±0.10" row) | a 0.6–0.8 (gap), b 0.6–0.7 (pad L), c 0.6–0.8 (pad W) | 0.65 × 0.70, 0.70, 1.35 | MLCC_Murata_C02E p278, Table 2 |
| Murata GRM21B (body ±0.15, "±0.15" row) | a 1.2 (gap), b 0.6–0.8 (pad L), c 1.2–1.4 (pad W) | 0.70 × 1.30, 1.20, 1.90 | MLCC_Murata_C02E p278, Table 2 |
| Yageo CC0805 | A 2.8, B 0.9 (gap), C 0.95 (pad L), D 1.4 (pad W), each ±0.25; occupied area F 3.2 × G 2.1 | 0.95 × 1.40, 0.90, 1.85 | MLCC_Yageo_general_data_V25 p11, Table 10 |
| Coilcraft 0805CS | I 1.02 (pad L), H 1.78 (pad W), J 0.76 (gap) | 1.02 × 1.78, 0.76, 1.78 | L_Coilcraft_0805CS p2 |
| KEMET T491A, density level B (nominal) | L 1.80 (pad L), W 1.23 (pad W), S 0.82 (gap); courtyard V1 4.92 × V2 2.30 | 1.80 × 1.23, 0.82, 2.62 | Tant_KEMET_T491 p15, Table 2 |
| Epson TSX-3225 | 4 pads 1.4 × 1.15; pitch 2.2 (long axis) × 1.6 | 1.40 × 1.15; pitch 2.2 × 1.6 | Y2_Epson_TSX-3225 p1 |

- **TDK:** PA, PB and PC share one range, so the result is the same whichever of gap, pad L and pad W each letter means.
- **KEMET:** level A (wave soldering, widest process window) and level C (densest) are also on p15. Level B is KEMET's choice for reflow.
- **Y2 grounding:** pads #2 and #4 are tied to the metal cover, and Epson says to connect them to ground. #1 and #3 are the crystal (p1).

## Where each package is used

| Package | BOM uses |
|---|---|
| 0402 Murata | Y1 load caps; U1 VDD, VDDA and NRST 100 nF; U2 pins 1/24 (1.5 nF), 6, 7, 8, 10 tank, 11, 12, 14, 16, 22; U4 C1, C2, C4, C9, C14, C15, C18 (C5 pad only); FL1 capacitors |
| 0402 Murata BLM15G | U4 FB1 |
| 0402 Yageo RC | All 0402 resistors except the four Panasonic ones |
| 0402 Panasonic ERJ-2RK | U4 R2, R3 (2 kΩ); D1 green and blue (390 Ω) |
| 0603 TDK 1 µF | U2 pins 1, 24 coupling; U1 VDDA; U3 CIN, COUT |
| 0603 Murata 2.2 µF | U2 pin 20 |
| 0805 Murata 4.7 µF | U1 VCAP |
| 0805 Yageo 10 µF | U1 VDD bulk |
| 0805CS | U2 #5 and FL1 (100 nH ×3); U2 #6 (330 nH) |
| T491A | U2 pin 4 (10 µF) and pin 8 loop filter (15 µF); polarized |
| TSX-3225 | Y2 |
