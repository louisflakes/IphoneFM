# BOM — main parts

## Sourcing rule (every part must pass all of these)

1. Active lifecycle (not obsolete, not NRND, not "discontinued" at LCSC)
2. Public datasheet with register / programming information
3. In stock at LCSC/JLCPCB (turnkey) **or** at an authorized distributor (DigiKey / Mouser) for consignment
4. No broker-only parts (eBay, AliExpress, Utsource-only = fail)

Recheck stock live before each gate. Never copy numbers from memory.

## Main ICs — verified 2026-10-18

| Role | Part | Source / PN | Stock (2026-10-18) | Price (1 / 100) | Assembly | Sourcing rule |
|---|---|---|---|---|---|---|
| MCU + USB | ESP32-S3-MINI-1-N8 | LCSC C2913206 | 3,882 | $4.76 / $3.38 | JLCPCB turnkey | ✅ Pass |
| DAC (USB audio → analog to transmitter) | PCM5102APWR | LCSC C107671 | 4,125 | $1.46 / $0.96 | JLCPCB turnkey (Extended) | ✅ Pass |
| FM transmit (primary candidate) | QN8027-SANC | LCSC C7422502 | **0 (out of stock)** | ref $0.65 | Footprint in JLCPCB library | ⚠️ Fails #3 today. Restock or authorized source needed. |
| FM transmit (fallback) | KT0803L | Not at LCSC / DigiKey / Mouser | brokers only | ~$0.70 | Consign | ❌ Fails #3 and #4 |
| FM receive / scan | Si4735-D60-GM (tray) | DigiKey | 1,488 | $5.06 / $3.81 | Consign | ✅ Pass |
| FM receive (reel version) | Si4735-D60-GMR | LCSC C2155662 | 0 | — | — | ❌ Out of stock |
| (rejected) FM transceiver | RDA5820NS | LCSC C167244 | Discontinued | — | — | ❌ Fails #1 |

## Open problem: the transmit chip

**Neither transmit chip passes the sourcing rule today.** This is the main blocker (see
`decisions.md` D-004). Options to evaluate at Gate 1:

- Watch for a QN8027 restock at LCSC/JLCPCB, or find an authorized distributor
- Search again for actively produced FM transmit ICs (including ones inside audio SoCs with open docs)
- Accept a consigned QN8027 from a broker (would mean changing rule #4; Jake decides)

## Key numbers for the transmit chips (from datasheets)

| | QN8027 | KT0803L |
|---|---|---|
| SNR | 65 dB | 66 dB |
| THD | 0.04 % | 0.3 % |
| Stereo separation | — | > 40 dB |
| RDS transmit | Yes | No |
| Package | MSOP-10 | SOP-16 |
| Input | Analog | Analog, 0.35 Vrms nominal, PGA −15 to +12 dB |
| Output power | programmable | 95.5–108 dBµV (RFGAIN), 112.5 dBµV with PA_BIAS |
| I²C address | — | 0x7C / 0x7D |

KT0803L notes: `RFGAIN[3:0]` is split across registers 0x01[7:6], 0x02[6], 0x13[7].
**`PA_CTRL` (0x13[2]) must stay 0** — the external-inductor mode can damage the chip.
75 µs pre-emphasis = `PHTCNST` 0.

## Si4735-D60 key numbers

1.1 µV sensitivity (50 Ω), 63 dB mono / 58 dB stereo S/N, ≥ 25 dB separation, I²S digital out,
RSSI/SNR per channel, RDS receive.
