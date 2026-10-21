# Datasheets and specs

Every document the design was checked against. Page numbers cited in the [BOM](../../design/plan-c/bom.md), [decisions](../decisions.md) and the [wiring diagram](../../design/plan-c/wiring.html) refer to these files.
"Session download" means fetched during the design sessions; the original link was not kept.

## Plan C parts (`plan-c/`)

| File | Document | Source | Used for |
|---|---|---|---|
| U1_STM32U535_DS14217_Rev5.pdf | ST STM32U535 datasheet, DS14217 Rev 5 (May 2025) | [DigiKey copy](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8915/STM32U535CEU6QTR.pdf) | Pinout, power, clocks, I/O, ADC, timers |
| U1_ST_AN2606_bootloader_Rev61.pdf | ST AN2606 Rev 61, system memory boot mode | Session download (mirror) | ROM USB DFU, bootloader pins |
| U1_ST_UM3062_Nucleo-U545_Rev1.pdf | ST UM3062 Rev 1, Nucleo-U545 user manual | [kamami.pl copy](https://download.kamami.pl/p1189216-um3062-stm32u5-nucleo64-board-mb1841-stmicroelectronics.pdf) | VBAT tie, BOOT0 pull-down practice |
| U2_LV2285VB_ENA1494.pdf | onsemi/Sanyo LV2285VB, ENA1494 | [LCSC copy](https://datasheet.lcsc.com/datasheet/pdf/aaf9ba5a5acc70222fbd7624956da41a.pdf) | FM transmitter, application circuit (p4) |
| U3_AP2112_DS39724_Rev2-2.pdf | Diodes AP2112, DS39724 Rev 2-2 | [diodes.com](https://www.diodes.com/assets/Datasheets/AP2112.pdf) | 3.3 V regulator |
| U4_Si4704-05-D60_Rev1.2.pdf | Skyworks Si4704/05-D60 Rev 1.2 | [skyworksinc.com](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si4704-05-D60.pdf) | FM receiver, SSOP schematic and BOM (p17–18) |
| U4_Skyworks_AN383_antenna_layout.pdf | Skyworks AN383, Si47xx antenna, schematic, layout and design guidelines (207075A, Jan. 23, 2025) | [skyworksinc.com](https://www.skyworksinc.com/-/media/skyworks/sL/documents/public/application-notes/aN383.pdf) | Two-layer stackup and layout rules (p15–17), FMI front ends and matching inductor (§3–4, §7, Appendix A p50–54) |
| U4_Skyworks_AN332_programming_guide.pdf | Skyworks AN332, Si47xx programming guide | [skyworksinc.com](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN332.pdf) | I²C address, digital audio |
| U5_PE42421_DOC-33214-1.03.pdf | pSemi PE42421, DOC-33214-1.03 | [psemi.com](https://www.psemi.com/pdf/datasheets/pe42421ds.pdf) | RF switch, eval board (p7) |
| U6_USBLC6-2_ST_Rev2.pdf | ST USBLC6-2, REV 2 (2005) | [mirror](https://www.danomsk.ru/upload/iblock/224/147401_7198d2f5ecc1d8bddd1f654c0b36a43b.pdf) | USB ESD (D+/D−/VBUS) |
| D3-D4_TPD1E05U06_TI.pdf | TI TPDxE05U06 | [ti.com](https://www.ti.com/lit/ds/symlink/tpd1e05u06.pdf) | CC ESD |
| D5_TPD1E0B04_TI.pdf | TI TPD1E0B04 | [ti.com](https://www.ti.com/lit/ds/symlink/tpd1e0b04.pdf) | Antenna ESD |
| D1_ASCB-WTF0_DS101.pdf | Broadcom ASCB-WTF0, ASCB-WTF0-DS101 | [broadcom.com](https://docs.broadcom.com/doc/ASCB-WTF0-DS) | RGB LED |
| D2_SVC710_ENA0605A.pdf | onsemi SVC710, ENA0605A | [mirror](https://www.nyang-tech.com/datasheet/2027636947/onsemi/SVC710-TL-E.pdf) | Varactor in the LV2285 VCO |
| Y1_Abracon_ABS07.pdf | Abracon ABS07 (revised 08-10-22) | [abracon.com](https://abracon.com/Resonators/ABS07.pdf) | 32.768 kHz crystal |
| J1_GCT_USB4105.pdf, J1_GCT_USB4105_drawing.pdf | GCT USB4105 spec and drawing | [gct.co](https://gct.co/files/drawings/usb4105.pdf) | USB-C receptacle pinout |
| J2_TE_CONSMA002-G_drawing.pdf | TE Linx CONSMA002-G customer drawing C-CONSMA002-G, rev A | [te.com](https://www.te.com/en/product-CONSMA002-G.html) (saved via the user's Chrome) | SMA jack footprint (4 × Ø1.5 on 5.1 square, Ø1.4 centre), 15.20 long, 13.90 tall incl. 3.90 legs; −40 to +85 °C, 0.57 N·m max torque |
| J2_TE_CONREVSMA002-G_drawing.pdf | TE Linx CONREVSMA002-G drawing, rev A, superseded 2026-10-20 by CONSMA002-G | Provided by the user | RP-SMA footprint (identical to CONSMA002-G), height |
| SW1_SameSky_SLW-158562-5A-RA-N-D.pdf | Same Sky SLW-158562-5A-RA-N-D (09/12/2024) | [sameskydevices.com](https://www.sameskydevices.com/product/resource/slw-158562-5a-ra-n-d.pdf) | TX/RX slider, 1.6 mm PCB note |
| SW2-SW3_Panasonic_EVQP7_ANCTB21E.pdf | Panasonic side-operational SMD tactile switches, 3.5 × 2.9 mm, catalog ANCTB21E (2025-07) | [panasonic.com](https://api.pim.na.industrial.panasonic.com/file_stream/main/fileversion/245500) | Buttons EVQ-P7J01P: rating (p1), dimensions, circuit and land pattern (p2) |
| SW2-SW3_SameSky_TS02.pdf | Same Sky TS02 series (11/03/2025), superseded 2026-10-20 by the EVQ-P7 | [sameskydevices.com](https://www.sameskydevices.com/product/resource/ts02.pdf) | Buttons, LCR drawing (p3) |
| VCAP_Murata_GRM21BR71C475KE51_product_sheet.pdf | Murata product sheet, GRM21BR71C475KE51 | Provided by the user | VCAP cap voltage and tolerance |

### RF layout application notes (`plan-c/`)

Used by the [PCB design workflow](../pcb-design-workflow.md). AN383 is listed above under U4.

| File | Document | Source | Used for |
|---|---|---|---|
| Layout_ST_AN4169_sub-GHz_RF_layout.pdf | ST AN4169, PCB design guidelines for the SPIRIT1 transceiver (DocID023704 Rev 2, Feb. 2017) | [st.com](https://www.st.com/resource/en/application_note/an4169-pcb-design-guidelines-for-the-spirit1-transceiver-stmicroelectronics.pdf) (saved by the user) | Two- vs multi-layer RF boards (p5, p12), grounded coplanar lines (p6), decoupling and via parasitics (p7–8), RF capacitor/inductor choice (p8–9) |

### Passive packages and land patterns (`plan-c/`)

Used by the [package table](../../design/plan-c/packages.md).

| File | Document | Source | Used for |
|---|---|---|---|
| MLCC_Murata_C02E_catalog_Jan2021.pdf | Murata Chip Multilayer Ceramic Capacitors catalog C02E (Jan. 18, 2021) | [DigiKey copy](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/8942/490_Chip_Multilayer_CAT2021_MLCC.pdf) | GRM reflow land dimensions (Table 2, p278) |
| MLCC_Yageo_CC_X5R_V32.pdf | Yageo CC X5R 4–50 V product specification V.32 (Sep. 16, 2026) | [yageogroup.com](https://yageogroup.com/content/datasheet/asset/file/UPY-GPHC_X5R_4V-TO-50V) | CC0805 10 µF body and thickness class (p2, p6, p8) |
| MLCC_Yageo_general_data_V25.pdf | Yageo/Phycomp SMD MLCC general data V.25 (Mar. 4, 2020) | [DigiKey forum attachment](https://forum.digikey.com/t/yageo-smt-mlcc/36355) | CC reflow footprint (Table 10, p11) |
| R_Yageo_RC_L_V14.pdf | Yageo RC_L chip resistor product specification V.14 (Nov. 14, 2025) | [yageogroup.com](https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L) | RC0402 body (Table 1, p4) |
| R_Yageo_mounting_V10.pdf | Yageo/Phycomp chip resistor mounting V.10 (Feb. 13, 2018) | [Octopart copy](https://sigma.octopart.com/138820526/technical_drawing/Yageo-RC0402FR-1310KL.pdf) | RC reflow footprint (Table 1, p4) |
| R_Panasonic_ERJ_precision_AOA0000C304.pdf | Panasonic precision thick film chip resistors (29-May-25) | [industrial.panasonic.com](https://industrial.panasonic.com/cdbs/www-data/pdf/RDA0000/AOA0000C304.pdf) | ERJ-2RK body (p4) |
| R_Panasonic_land_pattern_DMM0000COL17.pdf | Panasonic surface mount resistors land pattern (24-Dec-25) | [industrial.panasonic.com](https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/DMM0000COL17.pdf) | ERJ 1005 land pattern (p1) |
| L_Coilcraft_0805CS_Doc100.pdf | Coilcraft 0805CS, Document 100 (revised 08/05/22) | [coilcraft.com](https://www.coilcraft.com/getmedia/dd5f20e4-1ff7-43df-8317-b693eb2dce3e/0805cs.pdf) | Body and recommended land pattern (p2) |
| Tant_KEMET_T491_T2005.pdf | KEMET T491 industrial MnO2, T2005 (2026-07-08) | [yageogroup.com](https://yageogroup.com/content/datasheet/asset/file/KEM_T2005_T491) | Case A body (p4), land dimensions (Table 2, p15) |
| Y2_Epson_TSX-3225.pdf | Epson FA-238V / FA-238 / TSX-3225 (Rev. Dec. 2015) | [DigiKey copy](https://media.digikey.com/pdf/Data%20Sheets/Epson%20PDFs/FA-238(V),TSX-3225_Series_Rev_Dec_2015.pdf) | Y2 body and recommended footprint (p1) |

## Specs and Apple documents (`specs/`)

| File | Document | Used for |
|---|---|---|
| Apple_Accessory_Design_Guidelines.pdf | Apple Accessory Design Guidelines | Current limits before/after enumeration, iPhone 17 Pro power |
| Apple_iPhone17Pro_dimensional_drawing.pdf | Apple iPhone 17 Pro dimensional drawing | Port keep-out and position |
| USB_Type-C_R2.5_Mar2026.pdf | USB Type-C Cable and Connector Spec R2.5 (March 2026) | Rd, CC voltages, SBU, cable wiring, attach rules |
| USB_Type-C_R2.0_Aug2019.pdf | USB Type-C Spec R2.0 (August 2019) | Earlier cross-check; superseded by R2.5 |
| USB_PD_R3.2_V1.2_2026-08-19.pdf | USB Power Delivery R3.2 V1.2 (2026-08-19) | vSafe5V range, VBUS ripple |

Web references not stored as files: Murata product pages for each GRM part (body size and tolerance, e.g. [GRM155R71C104KA88](https://pim.murata.com/en-us/pim/details/?partNum=GRM155R71C104KA88%23)), [TDK C1608X7R1C105K080AC product page](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1C105K080AC) (body and recommended land pattern), [Analog Devices (Maxim), PCB layout guidelines for RF & mixed-signal (Sep. 14, 2011)](https://www.analog.com/en/resources/technical-articles/pcbs-layout-guidelines-for-rf--mixedsignal.html) (RF layout rules), [Apple TN3190 USB audio](https://developer.apple.com/documentation/technotes/tn3190-usb-audio-device-design-considerations), [47 CFR Part 15](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15) (§15.23, §15.203, §15.209, §15.239).

## Archived plans (`archive/`)

| File | Document | Used in |
|---|---|---|
| PlanA_STM32F072_DS9826.pdf | ST STM32F072 datasheet, DS9826 | Plan A MCU (provided by the user via Google Drive) |
| PlanB_ATSAMD51_DS60001507.pdf | Microchip SAM D5x/E5x, DS60001507 | Plan B MCU |
| PCM2704C_TI.pdf | TI PCM2704C | Early USB audio DAC option |
| LV2282VA.pdf | onsemi LV2282VA | Early transmitter option |
| GCT_USB4110.pdf, GCT_USB4110_drawing.pdf | GCT USB4110 (plug) | Early connector option |

## Evaluated, not chosen (`alternates/`)

| File | Document | Why not chosen |
|---|---|---|
| STM32G0B1_DS13560_Rev4.pdf | ST STM32G0B1, DS13560 Rev 4 | USB packet memory only 1 KB |
| STM32L496_DS11585_Rev20.pdf | ST STM32L496, DS11585 Rev 20 | USB buffer 1.25 KB (provided by the user) |
| QBLP679E-RGB-3053.pdf | QT Brightek 5050 RGB LED | Specified only at 20 mA |
| XL-5050RGBC.pdf | XINGLIGHT 5050 RGB LED | Specified only at 20 mA |
| Wurth_452404020202_slide_switch.pdf | Würth WS-SLTV slide switch (provided by the user) | Top-actuated; replaced by a right-angle slider |

## Analog FM rendition (`analog-fm/`)

Saved 2026-10-20. LCSC copies come from LCSC's datasheet server (`datasheet.lcsc.com`), the copy JLCPCB links for each part.

| File | Document | Source | Used for |
|---|---|---|---|
| ESD_Semtech_RClamp0521P.pdf | Semtech RClamp0521PA | LCSC copy (C117554) | Antenna ESD (D5) |
| L_Murata_LQW18AN_JELF243A-0024.pdf | Murata LQW18AN reference spec JELF243A-0024AC-01 | [murata.com](https://pim.murata.com/asset/pim4/inductor/JELF243A-0024_PDF_INDUCTOR) | L1, FL1 inductors |
| Q_onsemi_MMBTH10LT1.pdf | onsemi MMBTH10L | LCSC copy (C16204) | Oscillator and buffer transistors |
| VAR_Toshiba_1SV281.pdf | Toshiba 1SV281 (2014-03-01) | LCSC copy (C146317) | VCO varactor |
| J1_HRO_TYPE-C-31-M-12.pdf | Korean Hroparts TYPE-C-31-M-12 drawing (2020-12-08) | LCSC copy (C165948) | USB-C receptacle |
| J2_BAT_BWSMA-KWE-Z001.pdf | BAT Wireless BWSMA-KWE-Z001 (July-2-2025-A01) | LCSC copy (C496551) | SMA jack |
| SW1_ShouHan_MSK12C02.pdf | Shou Han MSK12C02 drawing | LCSC copy (C431540) | TX/RX slide switch |
| D1_XINGLIGHT_XL-1615RGBC-RF.pdf | XINGLIGHT XL-1615RGBC-RF | LCSC copy (C965840) | RGB LED |
| XO_YXC_OT322520MJBA4SL.pdf | YXC YSO110TR family | LCSC copy (C725987) | 20 MHz PLL reference |
| ATT_pSemi_PE43711.pdf | pSemi PE43711 RF digital step attenuator, DOC-84940-8 (05/2026) | [psemi.com](https://www.psemi.com/pdf/datasheets/pe43711ds.pdf) | Adjustable TX power (direct parallel mode, p6, p8) |
| SW_CK_TDP_series.pdf | C&K TDP series side-actuated half-pitch DIP switches (rev. CM.06/17/25) | [littelfuse.com](https://www.littelfuse.com/assetdocs/littelfuse-c-k-dip-tdp-series-datasheet?assetguid=738f2d91-170d-4173-a51c-2c80edfa4e19) (saved via the user's Chrome) | RF power DIP switch (TDP06H1SBD1) |
| SW_kangshen_DSHP06TSGER.pdf | Kangshen DSHP06TSGER drawing (2017-03-24) | LCSC copy (C3293146) | Fallback RF power DIP switch (top-actuated) |
| SW_ShouHan_2.54-6P-TPCB.pdf | Shou Han 2.54-6P TPCB piano DIP drawing (2020-05-24), not used: 7 mm tall | LCSC copy (C6331173) | — |
| Q_onsemi_MMBT3904.pdf | onsemi MMBT3904L | LCSC copy (C81464) | Buffer lock-gate |
| C_Samsung_MLCC_catalog_2015_excerpt.pdf | Samsung Electro-Mechanics MLCC catalog (Nov. 2015): part numbering (p4–5) and standard capacitors | LCSC copy (C59782, C1713) | JLC replacements for Plan C capacitors |
| FB_Murata_BLM15AG_ENFA0018.pdf | Murata BLM15AG ferrite beads, spec ENFA0018 | [murata.com](https://pim.murata.com/asset/pim4/ferriteBeadInductortypefilter/ENFA0018_PDF_FERRITEBEADINDUCTORTYPEFILTER) | VDDA ferrite (BLM15AG601SN1D) |
| POT_Alps_RK10J.pdf | Alps RK10J/RK14J knob-type potentiometers (catalog p389–394) | LCSC copy (C351175) | Tuning thumbwheels (RK10J11R0A0H) |
| SW_Diptronics_RV4AF-10R-V-B.pdf | Diptronics R(H)(V)(M)(S) rotary coded switch series, not used: replaced by thumbwheels | LCSC copy (C82589) | — |
| PLL_ADI_ADF4002.pdf | Analog Devices ADF4002 Rev. D (2006–2015) | Provided by the user (analog.com resets scripted downloads) | PLL synthesizer |
| SW_BIWIN_R9310R0H-X.pdf | BIWIN R9 series (Oct. 2016), not used: low stock | LCSC copy (C3294689) | — |

