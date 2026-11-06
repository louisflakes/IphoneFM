# Rev B: where each passive comes from

Rev B keeps every Rev A passive except C39–C41 (the wheel ADC caps, gone with the wheels) and adds the front-panel parts marked Rev B below.

An audit of every passive and protection part on the board, made 2026-10-24 during Phase 5. Each part is in one of three groups:

1. **Required:** the part's datasheet, its evaluation board, or a standard says to fit it.
2. **From published designs:** the datasheet does not ask for it, but working designs with the same chip fit it. These parts close gaps found in reference-check.md.
3. **Our own choice:** a value or part that I picked. No datasheet or reference design asks for it.

Sources are given as in [bom.md](bom.md).

## 1. Required by a datasheet, an evaluation board or a standard

| Parts | What they do | Source |
|---|---|---|
| C3–C10 | U1 decoupling and 3V3 bulk, VCAP 4.7 µF, NRST 100 nF | STM32U545 DS14217 Figure 23 p127, Figure 37 p212 |
| C1, C2 (U3) | Regulator input and output capacitors | AP2112 DS39724 p1–2 |
| C11, C12 | Y2 supply bypass and bulk | YSO110TR / OT322520 data sheet |
| C13–C23 | U2 decoupling at every supply pin; VregVCO 2.2 µF (100 nF there is marked "incorrect") | LMX2571 p53–54, Figure 62 |
| C24, R5, C25 | U2 loop filter. Topology from the datasheet; values calculated for our VCO gain | LMX2571 Figure 62 p44 |
| C26 | DC block, U2 to U7 | LMX2571 Table 38 p42; PE43711 RF pins must be at 0 V DC |
| C27, R10–R15 | U7 supply bypass. Logic pins must not float: floating pins give minimum attenuation, which is full power at power-up | PE43711 p8, Table 9 |
| R16, R17 | U5 supply and control series resistors | PE42421 evaluation board p7 |
| C28–C30, L2, L3 | FL1 harmonic filter | Required to meet the harmonic targets; calculated in Plan C chain 12 |
| C32–C35, L1, FB1 | U4 decoupling, RF input coupling, antenna match, emissions filter | Si4705 Table 12 p18; AN383 p7, p9, Figure 23 p37 |
| R22–R24, C36 | Series resistors on U4's audio outputs, plus the DFS filter capacitor | Si4705 Table 12 (600 Ω, 2 kΩ, 2 kΩ; C9 2–5 pF) |
| C37, C38 | U4 GPO filter capacitors | AN383 p8, option 1 |
| R1, R2 | USB-C CC 5.1 kΩ pull-downs; without them a USB-C charger supplies no power | USB Type-C spec R2.5 Table 4-28 p246 |
| R3 | BOOT0 pull-down, so U1 starts from flash | ST boot rules; every reference design in reference-check.md fits one |
| R25–R27 | LED current limiting; values calculated from the LED's VF | XL-1615RGBC p3–4 |
| C42, C43 (Rev B) | U8 supply: 1 µF + 100 nF at VCC | IS31FL3236A typical application circuit p1 |
| R28 (Rev B) | U8 R_EXT: sets the segment current maximum, 7.6 mA with 10 kΩ | IS31FL3236A p10 (formula 2; 2 kΩ minimum); value is my choice within it |
| R29 (Rev B) | U8 SDB pull-down: display off until firmware runs | IS31FL3236A typical application circuit p1 (100 kΩ) |

## 2. From published designs (not in the datasheet)

| Part | Why | Who fits it |
|---|---|---|
| FB2 | Ferrite into VDDA. On this package VREF+ is bonded to VDDA, so supply noise moves the ADC readings | ST CAN-node reference design |
| FB3 | Ferrite into U4's supply | USB FM Radio (same Si4705 QFN) |
| C31 | 1 nF filter at U5's control pin | LoRaPP and Electronic Cats |
| D3–D5, U6 | ESD on CC1, CC2, USB D+/D−/VBUS and the antenna | Plan C chain 11; three published designs for the antenna position |

## 3. Our own choices

| Part | What it does | Why I fitted it | Honest assessment |
|---|---|---|---|
| R4, 33 Ω | Series termination, Y2 to U1 | Damps ringing on the clock line | Best guess. ST's Nucleo puts a series R and C on its external clock path; the datasheet does not ask for one. Harmless, and it can be tuned on the bench |
| R6–R8, 33 Ω | Series resistors on the three FSK I²S lines into U2 | They soften the edges of a stream that runs continuously next to the synthesizer | Best guess. TI's own LMX2571 EVM has series parts (R57–R60) on these lines. Nothing says they must sit at U1's pins, so they move away from U1 for routing room |
| R9, 10 kΩ | U2 CE pull-down | Keeps the transmitter off until firmware enables it, and while U1 is in reset | Design choice. It is a safety default: no carrier during reset or boot |
| R18, 100 kΩ | RF_MODE pull-down | Holds receive while the slider is between contacts | Design choice. It stops the line floating mid-throw |
| R30–R32, 10 kΩ (Rev B) | Pull-ups on the encoder's A, B and push contacts | U1's internal pull-ups would do; external ones set a known 0.33 mA contact current, under the 0.5 mA rating | Design choice. No filter capacitors: one across the contact would discharge through it; firmware debounces |
| C44, 10 µF (Rev B) | Reservoir at the digits' anodes | Keeps the segment current pulses (up to about 250 mA at 3 or 22 kHz) local, off the VBUS line to U3 | Design choice. Harmless; the datasheet shows only U8's own 1 µF + 0.1 µF |

**Summary:** most parts are required by a datasheet, an evaluation board or a standard. Four parts close gaps found in published designs. Four (R4, R6–R8) are my best guesses; they are harmless and their values can be tuned on the bench. Two (R9, R18) are deliberate safe defaults. No part on the board does nothing, and none is a placeholder.
