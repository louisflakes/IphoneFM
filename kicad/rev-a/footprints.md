# Rev A footprints (Phase 2)

Each part's footprint source, chosen in the order step 2.1 sets: KiCad's own library, then the maker's own land pattern, then LCSC/EasyEDA. A KiCad footprint named for the exact part is preferred over a generic one. Nothing here is final until step 2.2 has compared its pads with the datasheet's land pattern; that column records the result.

**Follow up with the user at their 2.2 steps (asked 2026-10-22):** U4, whose KiCad footprint was drawn for a different Silicon Labs chip, and SW2, where KiCad has two Panasonic EVQ-P7 footprints and the right one must be confirmed.

Sources: **KiCad (part)** is a KiCad library footprint named for this part; **KiCad (generic)** is a KiCad footprint for the package, used only if its pads match the maker's land pattern; **Maker** is drawn from the land pattern in the maker's datasheet. No part needs LCSC/EasyEDA.

| Parts | Part number | Package | Source | Footprint | Datasheet land pattern | 2.2 check |
|---|---|---|---|---|---|---|
| J1 | HRO TYPE-C-31-M-12 | USB-C receptacle | KiCad (part), pads updated to the maker's 2020 layout | IphoneFM:USB_C_Receptacle_HRO_TYPE-C-31-M-12_2020 | J1_HRO_TYPE-C-31-M-12 p1 (2020-12-08) | Done 2026-10-22. KiCad's footprint follows HRO's 2015 drawing (archived copy in J1_HRO_TYPE-C-31-M-12_2015_superseded.pdf); HRO's 2020 drawing shortens the signal pads to 1.14 mm (0.50–1.64 mm behind the peg holes), moves the wide pads to ±2.40/±3.20 mm, makes the peg holes Ø0.60, the rear shell slots 0.6 × 1.4 mm in 0.9 × 1.7 pads and the front slot pads 0.9 × 2.0. The project copy (tools/fp_j1_hro2020.py) takes those values; outline, courtyard and 3D model are KiCad's. Board edge: 5.79 mm in front of the peg holes. Approved by the user |
| U1 | ST STM32U535CEU6 | UFQFPN-48 7 × 7, EP | KiCad (generic) | Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm | DS14217 (UFQFPN48 package section) | |
| U2 | TI LMX2571NJKR | WQFN-36 6 × 6, DAP (NJK) | Maker (no KiCad 6 × 6 QFN-36 matches TI's NJK yet) | to build from TI's NJK land pattern | SNAS654A (NJK0036A package section) | |
| U3 | Diodes AP2112K-3.3TRG1 | SOT-25 | KiCad (generic) | Package_TO_SOT_SMD:SOT-23-5 | DS39724 (SOT25 land pattern) | |
| U4 | Skyworks SI4705-D60-GM | QFN-20 3 × 3, 0.5 mm, EP | KiCad (generic) | Package_DFN_QFN:SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm (drawn for an EFM8 part: confirm pads and EP) | Si4704/05-D60 (PCB land pattern section) | |
| U5 | pSemi PE42421SCAA-Z | SC-70-6 | KiCad (generic) | Package_TO_SOT_SMD:SOT-363_SC-70-6 | PE42421 DOC-33214 (package drawing) | |
| U6 | ST USBLC6-2SC6 | SOT-23-6 | KiCad (generic) | Package_TO_SOT_SMD:SOT-23-6 | USBLC6-2 (footprint section) | |
| U7 | pSemi PE43711B-Z | QFN-24 4 × 4, EP | KiCad (generic), EP size to match | Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.x (the one whose EP matches) | PE43711 (land pattern) | |
| Y2 | YXC OT322520MJBA4SL | 3225 4-pad XO | KiCad (generic) | Oscillator:Oscillator_SMD_* 3.2 × 2.5 (the one whose pads match) | XO_YXC_OT322520MJBA4SL | |
| D1 | XINGLIGHT XL-1615RGBC-RF | 1615 RGB, 4-pad | Maker | to build from Xinglight's land pattern | XL-1615RGBC-RF | |
| D3, D4 | TI TPD1E05U06DPYR | X2SON-2 (DPY) | KiCad (part) | Package_SON:Texas_DPY0002A_0.6x1mm_P0.65mm | TPD1E05U06 (DPY land pattern) | |
| D5 | Semtech RCLAMP0521PATCT | SLP1006P2 | KiCad (generic) | Diode_SMD:D_SOD-882 (DFN1006-2) | RClamp0521P (land pattern) | |
| J2 | BAT Wireless BWSMA-KWE-Z001 | SMA, right angle, THT | KiCad (part) | Connector_Coaxial:SMA_BAT_Wireless_BWSMA-KWE-Z001 | J2_BAT_BWSMA-KWE-Z001 | |
| SW1 | Shou Han MSK12C02 | SMD slide switch, 4 tabs | KiCad (part) | Button_Switch_SMD:SW_SPDT_Shouhan_MSK12C02 | SW1_ShouHan_MSK12C02 | |
| SW2 | Panasonic EVQ-P7J01P | side-push SMD tactile | KiCad (part, EVQ-P7 series) | Button_Switch_SMD:SW_SPST_EVQP7A or _EVQP7C (whichever is the P7J's) | SW2-SW3_Panasonic_EVQP7 | |
| SW3 | C&K TDP06H1SBD1 | SMD DIP, 6 positions, 1.27 mm | Maker (KiCad's 1.27 mm DIPs are other makers' parts) | to build from C&K's land pattern, unless a KiCad one matches exactly | SW_CK_TDP_series | |
| RV1–RV3 | Alps RK10J11R0A0H | thumbwheel pot, reflow | Maker | to build from Alps' reflow land pattern | POT_Alps_RK10J p2–3 | |
| TP1–TP8 | — | test pad, top side | KiCad (generic) | TestPoint:TestPoint_Pad_D1.5mm | — (our own size) | |
| R (×27) | Yageo RC0402 / Panasonic ERJ-2R | 0402 | KiCad (generic, IPC) | Resistor_SMD:R_0402_1005Metric | R_Yageo_mounting, R_Panasonic_land_pattern | |
| C (×33 in 0402) | Samsung, Murata, Yageo | 0402 | KiCad (generic, IPC) | Capacitor_SMD:C_0402_1005Metric | Murata / Samsung catalogs | |
| C1, C2, C8, C23, C27 | Samsung CL10 | 0603 | KiCad (generic, IPC) | Capacitor_SMD:C_0603_1608Metric | Samsung catalog | |
| C3, C9, C12 | Samsung CL21, Murata GRM21 | 0805 | KiCad (generic, IPC) | Capacitor_SMD:C_0805_2012Metric | Samsung / Murata | |
| L1–L3 | Murata LQW18AN | 0603 | KiCad (generic, IPC) | Inductor_SMD:L_0603_1608Metric | L_Murata_LQW18AN | |
| FB1–FB3 | Murata BLM15 | 0402 | KiCad (generic, IPC) | Inductor_SMD:L_0402_1005Metric | FB_Murata_BLM15AG | |
