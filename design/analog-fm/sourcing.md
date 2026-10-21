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
| Y1 | Abracon ABS07-32.768KHZ-7-T | C276424, 6,180 | — | **Removed** (bom.md chain 3): U4's reference clock now comes from Y2 through U1's MCO |
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

Frequency hold: **PLL chip** (decided 2026-10-20), the method published FM PLL transmitters use.

| Block | Part | JLC stock | Datasheet check | Status |
|---|---|---|---|---|
| PLL | Analog Devices ADF4002BRUZ | C208290, 50; DigiKey 674, tube, MOQ 1 | ADF4002 Rev. D (`PLL_ADI_ADF4002.pdf`, provided by the user). RF input 5–400 MHz at −10 to 0 dBm, so the oscillator sample must be −10 to 0 dBm. Reference input 20–300 MHz, 0.8 V p-p to VDD, AC-coupled; a CMOS crystal oscillator can drive it. Phase detector up to 104 MHz. 14-bit R and 13-bit N counters: a 100 kHz comparison frequency gives every US channel (R = 200 from 20 MHz; N = 881–1079). Charge pump 625 µA–5 mA with RSET = 5.1 kΩ, linear from 0.5 V to VP − 0.5 V. VP can be 5 V, giving about 0.5–4.5 V of tuning. Logic input high ≥ 1.4 V, so it is fine from the 3.3 V MCU. 5–6 mA. TSSOP-16 (p1, p3, p6). **One caveat:** AVDD/DVDD is 2.7–3.3 V, and the AP2112's 3.3 V ±1.5% rail can reach 3.35 V. That is inside the 5.8 V absolute maximum (p5) but up to 50 mV over the operating range. The same thing was accepted for the RF switch in Plan C | Checked. Only one maker |
| PLL reference | YXC OT322520MJBA4SL (YSO110TR family) | C725987, 4,055 | 20 MHz CMOS, 1.8–3.3 V. Output ≥ 90% VDD high and ≤ 10% VDD low, 4 ns edges, 5 mA max at 3.3 V. Pin 1 tri-state (high or floating = on), 2 GND, 3 OUT, 4 VDD (p1–2, p4). The datasheet covers the whole family; the worst family grade (±20 ppm tolerance, ±50 ppm over temperature) is about ±7.6 kHz at 108 MHz, small against a 200 kHz channel | Checked |
| Oscillator, buffer | onsemi MMBTH10LT1G | C16204, 2,858 | VHF/UHF NPN. fT ≥ 650 MHz at 4 mA/10 V, Ccb ≤ 0.7 pF, VCEO 25 V (p1–2) | Checked |
| Varactor | Toshiba 1SV281(TPH3,F) | C146317, 10,132 | Made for VHF/UHF VCOs. 15–17 pF at 1 V, 7.3–8.7 pF at 4 V, ratio ≥ 1.8; 10 V max; rs 0.28 Ω at 470 MHz (p1–2). The band needs a 1.51× change in tank capacitance (108/88 squared). The PLL tunes 0.5–4.5 V from a 5 V charge-pump supply, so this works with some fixed capacitance in the tank. To be confirmed in the oscillator design | Checked |
| Tuning dials ×3 | **Alps RK10J11R0A0H thumbwheel potentiometer** (chosen by the user 2026-10-20) | C470766, 913; DigiKey stocks the RK10J family | 10 kΩ, single element, taper 3B, ±30%, 270° ±10° rotation, 0.5–10 mN·m torque, 10,000 cycles, −10 to +60 °C, 20 V DC max. 14 mm knurled wheel, 2.5 mm tall, lying flat on the board; reflow, surface mount (`POT_Alps_RK10J.pdf` p1–3). No detents. Each wheel is wired as a divider from 3V3 to GND, with the wiper going to an MCU ADC pin. Firmware splits the 270° travel into 10 zones of 27° with a dead band at each boundary; the 3B taper is mapped by a calibration table. Digits are marked on the case after assembly | Checked. Rejected: Diptronics RM3AF/RV4AF (screwdriver-slot, not a thumbwheel); BIWIN R9310R0H-X (100 in stock); APEM SMC pushwheels (panel-mounted and wired, so JLC can't assemble them); RK10J11E0034 (through hole, rated for manual soldering only, p1); RK10J11R001Y (audio taper) |

### Adjustable RF output power (added 2026-10-21)

RF power is set after the buffer and is independent of deviation, which stays in firmware. The chain is: buffer → attenuator → FL1 → DC block → RF switch → SMA.

| Block | Part | JLC stock | Datasheet check | Status |
|---|---|---|---|---|
| Step attenuator | **pSemi PE43711B-Z** | C470929, 1,737 | 9 kHz–6 GHz, 50 Ω, 7 bits, 0–31.75 dB in 0.25 dB steps, about 1.5 dB loss at the 0 dB setting (DOC-84940-8 p1, p4). VDD 2.3–5.5 V, so it runs from 3.3 V. +28 dBm max input (p3). **Direct parallel mode:** P/S tied low and LE tied high; the control pins then set the state live, "ideal for manual control… using hardwire, switches, or jumpers" (p8). Bits D6–D0 = 16, 8, 4, 2, 1, 0.5, 0.25 dB (Table 4, p6). Floating pins at power-up give minimum attenuation (p8), so every line has a defined level. QFN-24, 4 × 4 mm | Checked. Same maker as U5 |
| Power setting | **C&K TDP06H1SBD1**, 6-position half-pitch side-actuated SMD DIP switch, extended actuators (chosen 2026-10-21 so the levers face out the board edge) | JLC C221994, 0 → **global sourcing**: DigiKey 1,180, tube, MOQ 1 | SPST ×6, 1.27 mm pitch, body 8.74 × 6.0 mm, 4.1 mm tall, gull wing; pads 8.89 mm apart. 24 V DC / 25 mA switching, ≤ 100 mΩ, 1,000-cycle life (fine for a bench setting), −40 to +85 °C, 4.9 N max operating force. Process-sealed for SMT soldering (`SW_CK_TDP_series.pdf` p1–3). Switches 1–6 drive D6–D1 (16, 8, 4, 2, 1, 0.5 dB, labelled on the silkscreen), giving 0–31.5 dB in 0.5 dB steps. D0 (0.25 dB) is tied low on the board. Each switch connects its line to 3V3 | Checked. Replaces the top-actuated Kangshen DSHP06TSGER (C3293146, 14,596), kept as the in-stock fallback. Rejected: Shou Han 2.54-6P TPCB piano DIP (7 mm tall) |
| DIP pull-downs ×6 | Yageo RC0402FR-0710KL, 10 kΩ | C60490, 5,416,054 | One per attenuator control line, so an off switch reads low. 0.33 mA when on, well inside the switch rating | Plan C part |
| Buffer lock-gate | **onsemi MMBT3904LT1G** + 10 kΩ base resistor + 10 kΩ pull-up | C81464, 951,356 | NPN; collector on the buffer transistor's base bias node, emitter to GND. VCE(sat) ≤ 0.2 V at 10 mA, 40 V, 200 mA (p1–2). That is below the buffer's turn-on, so the buffer is off. The pull-up keeps the buffer muted from power-up until firmware sees PLL lock on the ADF4002 MUXOUT, and the MCU mutes it again while a thumbwheel moves. Exact bias values are set in the oscillator/buffer design | Checked |

**Height check:** the DIP switch (4.1 mm) is lower than the SMA jack (6 mm body, J2 drawing p6), the tallest part, so it doesn't set the enclosure height. It is taller than the USB-C socket (3.26 mm, J1 drawing) and the thumbwheels (2.5 mm, `POT_Alps_RK10J.pdf` p2). It sits at the board edge with its levers facing out, like the slider; the enclosure needs a slot there.

The MCU cannot count the carrier itself: its timer's external clock limit is fTIMxCLK/2 = 80 MHz (DS14217 Table 123, p243). The PLL chip makes that limit irrelevant.
