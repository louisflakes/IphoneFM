# Analog FM rendition: sourcing check

For about 6 boards, **fully assembled by JLCPCB, with no hand soldering**. Stock checked 2026-10-20 with the JLCPCB and DigiKey APIs. Datasheets are in [docs/datasheets/analog-fm/](../../docs/datasheets/analog-fm/) unless noted.

## Rules

1. **A part is a candidate until its primary datasheet is saved and checked.** Only then is it "checked".
2. **Deep stock.** Commodity parts need thousands in stock at JLC. A specialist chip with only one maker may have less, but it needs a second route: JLC global sourcing from a distributor with healthy stock.
3. **Package must suit JLC Economic assembly (0402 or larger).** Pick a part that fits, rather than upgrading the assembly service.
4. **JLC library first, global sourcing second.** Global sourcing: JLC buys the part for the assembly order, in 9–20 business days, non-cancellable ([JLC help article 60](https://jlcpcb.com/help/article/60-how-to-use-jlcpcb-global-sourcing-parts-service)). JLC wave-solders through-hole parts in the same order ([assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)).
5. **Price is not a criterion.**

## 1. Parts carried over from Plan C

These were checked against their datasheets in Plan C ([bom.md](../plan-c/bom.md), datasheets in `docs/datasheets/plan-c/`).

| Ref | Part | JLC stock | Second route | Status |
|---|---|---|---|---|
| U1 | ST STM32U535CEU6 | 1 | **Global sourcing**: DigiKey 1,394, tray, MOQ 1 | Checked (Plan C) |
| U3 | Diodes AP2112K-3.3TRG1 | C51118, 17,891 | — | Checked (Plan C) |
| U5 | pSemi PE42421SCAA-Z | C470893, 677 | DigiKey 128,343 | Checked (Plan C). Only one maker |
| U6 | ST USBLC6-2SC6 | C7519, 43,433 | — | Checked (Plan C) |
| SW2 | Panasonic EVQ-P7J01P (BOOT button only now) | C2828254, 9,729 | — | Checked (Plan C) |
| D3, D4 | TI TPD1E05U06DPYR | C436349, 75,628 | — | Checked (Plan C) |
| Y1 | Abracon ABS07-32.768KHZ-7-T | C276424, 6,180 | — | **Removed** (bom.md chain 3): U4's reference clock now comes from a U1 timer (32,787 Hz) running off Y2 |
| FB1 | Murata BLM15GA750SN1D | C113009, 18,883 | — | Checked (Plan C) |

## 2. Replacements for Plan C parts

| Ref | Was | Now | JLC stock | Datasheet check | Status |
|---|---|---|---|---|---|
| U4 | Si4704-D60-GUR (reel only, 2,500) | **Skyworks SI4705-D60-GM** | C1526114, 48; DigiKey 470, tray, MOQ 1 | Same datasheet as the Si4704, which lists the Si4705-D60-GM as the QFN part with RDS (Si4704/05-D60 Rev 1.2 p28). QFN supply: VA 2.7–5.5 V (p1), so 3.3 V is fine. Digital audio out (p1). Pin numbers change from SSOP to QFN (p29) | Checked. Only one maker |
| J1 | GCT USB4105-GF-A (JLC 0) | **Korean Hroparts TYPE-C-31-M-12** | C165948, 343,739 | 16-pin USB 2.0. CC1 A5, CC2 B5, D+ A6/B6, D− A7/B7, VBUS A4/A9/B4/B9, SBU A8/B8. 5 A, 20 V, −30 to +80 °C. Shell legs go in plated slots (drawing, p1) | Checked |
| J2 | TE CONSMA002-G (JLC 0) | **BAT Wireless BWSMA-KWE-Z001** | C496551, 130,101 | SMA, 0–6 GHz, 50 Ω, right angle with the thread parallel to the board. Footprint: 5.1 mm square, Ø1.4 holes (same as Plan C's TE part). The part code says "K (hole)" and the material list says "Socket", so the centre contact is a standard SMA female socket that takes the ANT500 plug (p3, p4, p6). One sentence on p3 says "internal pin", which contradicts the drawing; confirm on the first board | Checked, one doc conflict |
| SW1 | Same Sky SLW-158562 (not at JLC) | **Shou Han MSK12C02** | C431540, 196,431 | SPDT (pins 1–2–3, 2 common), side-operated, SMD with mounting tabs. 12 V DC, 50 mA, ≤ 100 mΩ, −20 to +70 °C, 10,000 cycles, 1.6 mm travel (drawing, p1). Plan C used one pole only. The vendor's text spec (p4) says "1 pole, 1 throw"; the drawing shows three contacts | Checked, one doc conflict |
| D1 | Broadcom ASCB-WTF0 (JLC 0) | **XINGLIGHT XL-1615RGBC-RF** | C965840, 577,998 | Common anode on pin 2; R pin 1, G pin 3, B pin 4 (p8). IF 20 mA max per colour, VF up to 2.4 V red and 3.4 V green/blue at 20 mA, reverse voltage 5 V (p3–4). Plan C's anodes-to-VBUS circuit works unchanged; unlike the Broadcom part, reverse bias at unplug is allowed | Checked |
| D5 | TI TPD1E0B04DPLR (0201) | **Semtech RClamp0521PATCT** | C117554, 91,372 | Bidirectional ("electrically symmetrical"), 0.30–0.50 pF, 5 V stand-off, IEC 61000-4-2 level 4. SLP1006P2 package: 1.0 × 0.6 mm, 0402-sized (p1–2, p4, p6). 0.5 pF is about 3.2 kΩ at 100 MHz, negligible on a 50 Ω line | Checked. Fallback: TPD1E0B04DPYR, the same TI part in 0402 (C1975594, 638; datasheet already in plan-c) |
| L1 | Coilcraft 0805CS-151XJRC (JLC 7) | **Murata LQW18ANR15G00D** | C113131, 25,337 | 150 nH ±2%, Q ≥ 32 at 150 MHz, self-resonance ≥ 1.4 GHz, 160 mA, 0603 wirewound (spec JELF243A-0024 p3–4) | Checked. Value may change with the receiver redesign |
| FL1 L ×2 | Coilcraft 0805CS-101XJRC (JLC 75) | **Murata LQW18ANR10G00D** | C98088, 43,979 | 100 nH ±2%, Q ≥ 34 at 150 MHz, self-resonance ≥ 1.8 GHz, 220 mA (p3–4) | Checked |

**Passives** from Plan C: at JLC, most exact part numbers are stocked. These are not:

| Part | JLC |
|---|---|
| Murata GRM1555C1H330JA01D (33 pF C0G) | Stock 0 |
| Murata GRM1555C1H560JA01D (56 pF C0G) | Stock 0 |
| Yageo CC0805KRX5R7BB106 (10 µF X5R) | Stock 0 |
| TDK C1608X7R1C105K080AC (1 µF X7R) | 157 in stock, minimum buy 206 |

Each gets a deeply stocked JLC part with the same value, dielectric, voltage and size. Those replacements will be picked and checked when each block's BOM is written.

**Dropped with the LV2285:** U2 LV2285VB, D2 SVC710, Y2 16 MHz crystal, SW3 (tuning moves to the dials), and the U2 support parts in bom.md chain 2.

## 3. New parts

Frequency hold and modulation: **TI LMX2571 synthesizer with its internal VCO** (decided 2026-10-21, option D2 in [modulation-strategies.md](modulation-strategies.md)). The MCU streams the stereo signal to it as frequency steps over I²S. The earlier picks for the ADF4002 PLL, the discrete oscillator and the lock gate are kept below, struck through, for the record.

| Block | Part | JLC stock | Datasheet check | Status |
|---|---|---|---|---|
| Synthesizer (PLL, VCO, modulation) | **TI LMX2571NJKR** | C440388, 139; DigiKey 1,244 (NJKR) and 1,386 (NJKT), cut tape, MOQ 1 | SNAS654A (`PLL_TI_LMX2571_SNAS654A.pdf`). Internal VCO 4300–5376 MHz, output 10–1344 MHz, about −18 to +3 dBm programmable (p6, p42). OSCin 10–150 MHz, MULT up to ×6, f_PD up to 130 MHz (p5, p11). Arbitrary-level FSK over I²S (up to 100 MHz clock, 17 clocks per frame) for analog FM (p10, p13; TI SNAA309). Output auto-mute until lock, on at reset (p23). Integrated LDOs on one 3.3 V supply; VcpExt needs 3.3 V or 5 V even in synthesizer mode (p54). Logic high ≥ 1.4 V (p6). 39 mA typical (p1). WQFN-36, 6 × 6 mm. Deviation headroom ±100 kHz on all 100 US channels with f_PD 40 or 100 MHz (modulation-strategies.md) | Checked. Only one maker |
| ~~PLL~~ | ~~Analog Devices ADF4002BRUZ~~ | | Replaced by the LMX2571 (an analog loop can't give flat audio down to 10 Hz) | Dropped |
| Reference (U1 clock, LMX2571 OSCin; U4 via a U1 timer) | YXC OT322520MJBA4SL (YSO110TR family) | C725987, 4,055 | 20 MHz CMOS, 1.8–3.3 V. Output ≥ 90% VDD high and ≤ 10% VDD low, 4 ns edges, 5 mA max at 3.3 V. Pin 1 tri-state (high or floating = on), 2 GND, 3 OUT, 4 VDD (p1–2, p4). The datasheet covers the whole family; the worst family grade (±20 ppm tolerance, ±50 ppm over temperature) is about ±7.6 kHz at 108 MHz, small against a 200 kHz channel | Checked |
| ~~Oscillator, buffer~~ | ~~onsemi MMBTH10LT1G~~ | | Not needed with the LMX2571's internal VCO | Dropped |
| ~~Varactor~~ | ~~Toshiba 1SV322~~ (and 1SV281 before it) | | Not needed with the LMX2571's internal VCO | Dropped |
| Tuning dials ×3 | **Alps RK10J11R0A0H thumbwheel potentiometer** (chosen by the user 2026-10-20) | C470766, 913; DigiKey stocks the RK10J family | 10 kΩ, single element, taper 3B, ±30%, 270° ±10° rotation, 0.5–10 mN·m torque, 10,000 cycles, −10 to +60 °C, 20 V DC max. 14 mm knurled wheel, 2.5 mm tall, lying flat on the board; reflow, surface mount (`POT_Alps_RK10J.pdf` p1–3). No detents. Each wheel is wired as a divider from 3V3 to GND, with the wiper going to an MCU ADC pin. Firmware splits the 270° travel into 10 zones of 27° with a dead band at each boundary; the 3B taper is mapped by a calibration table. Digits are marked on the case after assembly | Checked. Rejected: Diptronics RM3AF/RV4AF (screwdriver-slot, not a thumbwheel); BIWIN R9310R0H-X (100 in stock); APEM SMC pushwheels (panel-mounted and wired, so JLC can't assemble them); RK10J11E0034 (through hole, rated for manual soldering only, p1); RK10J11R001Y (audio taper) |

### Adjustable RF output power (added 2026-10-21)

RF power is set after the synthesizer and is independent of deviation. The chain is: LMX2571 RFoutTx → 100 pF → attenuator → FL1 → DC block → RF switch → SMA. The LMX2571's own output-power setting (about −18 to +3 dBm, p42) adds about 20 dB of firmware control.

| Block | Part | JLC stock | Datasheet check | Status |
|---|---|---|---|---|
| Step attenuator | **pSemi PE43711B-Z** | C470929, 1,737 | 9 kHz–6 GHz, 50 Ω, 7 bits, 0–31.75 dB in 0.25 dB steps, about 1.5 dB loss at the 0 dB setting (DOC-84940-8 p1, p4). VDD 2.3–5.5 V, so it runs from 3.3 V. +28 dBm max input (p3). **Direct parallel mode:** P/S tied low and LE tied high; the control pins then set the state live, "ideal for manual control… using hardwire, switches, or jumpers" (p8). Bits D6–D0 = 16, 8, 4, 2, 1, 0.5, 0.25 dB (Table 4, p6). Floating pins at power-up give minimum attenuation (p8), so every line has a defined level. QFN-24, 4 × 4 mm | Checked. Same maker as U5 |
| Power setting | **C&K TDP06H1SBD1**, 6-position half-pitch side-actuated SMD DIP switch, extended actuators (chosen 2026-10-21 so the levers face out the board edge) | JLC C221994, 0 → **global sourcing**: DigiKey 1,180, tube, MOQ 1 | SPST ×6, 1.27 mm pitch, body 8.74 × 6.0 mm, 4.1 mm tall, gull wing; pads 8.89 mm apart. 24 V DC / 25 mA switching, ≤ 100 mΩ, 1,000-cycle life (fine for a bench setting), −40 to +85 °C, 4.9 N max operating force. Process-sealed for SMT soldering (`SW_CK_TDP_series.pdf` p1–3). Switches 1–6 drive D6–D1 (16, 8, 4, 2, 1, 0.5 dB, labelled on the silkscreen), giving 0–31.5 dB in 0.5 dB steps. D0 (0.25 dB) is tied low on the board. Each switch connects its line to 3V3 | Checked. Replaces the top-actuated Kangshen DSHP06TSGER (C3293146, 14,596), kept as the in-stock fallback. Rejected: Shou Han 2.54-6P TPCB piano DIP (7 mm tall) |
| DIP pull-downs ×6 | Yageo RC0402FR-0710KL, 10 kΩ | C60490, 5,416,054 | One per attenuator control line, so an off switch reads low. 0.33 mA when on, well inside the switch rating | Plan C part |
| ~~Buffer lock-gate~~ | ~~onsemi MMBT3904LT1G~~ | | Replaced by the LMX2571's output auto-mute (p23) plus firmware lock monitoring | Dropped |

**Height check:** the DIP switch (4.1 mm) is lower than the SMA jack (9.5 mm tall with its axis 6.4 mm up, J2 drawing p6), the tallest part, so it doesn't set the enclosure height. It is taller than the USB-C socket (3.26 mm, J1 drawing) and the thumbwheels (2.5 mm, `POT_Alps_RK10J.pdf` p2). It sits at the board edge with its levers facing out, like the slider; the enclosure needs a slot there.


