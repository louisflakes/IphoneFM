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
| U4_Skyworks_AN332_programming_guide.pdf | Skyworks AN332, Si47xx programming guide | [skyworksinc.com](https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/application-notes/AN332.pdf) | I²C address, digital audio |
| U5_PE42421_DOC-33214-1.03.pdf | pSemi PE42421, DOC-33214-1.03 | [psemi.com](https://www.psemi.com/pdf/datasheets/pe42421ds.pdf) | RF switch, eval board (p7) |
| U6_USBLC6-2_ST_Rev2.pdf | ST USBLC6-2, REV 2 (2005) | [mirror](https://www.danomsk.ru/upload/iblock/224/147401_7198d2f5ecc1d8bddd1f654c0b36a43b.pdf) | USB ESD (D+/D−/VBUS) |
| D3-D4_TPD1E05U06_TI.pdf | TI TPDxE05U06 | [ti.com](https://www.ti.com/lit/ds/symlink/tpd1e05u06.pdf) | CC ESD |
| D5_TPD1E0B04_TI.pdf | TI TPD1E0B04 | [ti.com](https://www.ti.com/lit/ds/symlink/tpd1e0b04.pdf) | Antenna ESD |
| D1_ASCB-WTF0_DS101.pdf | Broadcom ASCB-WTF0, ASCB-WTF0-DS101 | [broadcom.com](https://docs.broadcom.com/doc/ASCB-WTF0-DS) | RGB LED |
| D2_SVC710_ENA0605A.pdf | onsemi SVC710, ENA0605A | [mirror](https://www.nyang-tech.com/datasheet/2027636947/onsemi/SVC710-TL-E.pdf) | Varactor in the LV2285 VCO |
| Y1_Abracon_ABS07.pdf | Abracon ABS07 (revised 08-10-22) | [abracon.com](https://abracon.com/Resonators/ABS07.pdf) | 32.768 kHz crystal |
| J1_GCT_USB4105.pdf, J1_GCT_USB4105_drawing.pdf | GCT USB4105 spec and drawing | [gct.co](https://gct.co/files/drawings/usb4105.pdf) | USB-C receptacle pinout |
| J2_TE_CONREVSMA002-G_drawing.pdf | TE Linx CONREVSMA002-G drawing, rev A | Provided by the user | RP-SMA footprint, height |
| SW1_SameSky_SLW-158562-5A-RA-N-D.pdf | Same Sky SLW-158562-5A-RA-N-D (09/12/2024) | [sameskydevices.com](https://www.sameskydevices.com/product/resource/slw-158562-5a-ra-n-d.pdf) | TX/RX slider, 1.6 mm PCB note |
| SW2-SW3_SameSky_TS02.pdf | Same Sky TS02 series (11/03/2025) | [sameskydevices.com](https://www.sameskydevices.com/product/resource/ts02.pdf) | Buttons, LCR drawing (p3) |
| VCAP_Murata_GRM21BR71C475KE51_product_sheet.pdf | Murata product sheet, GRM21BR71C475KE51 | Provided by the user | VCAP cap voltage and tolerance |

## Specs and Apple documents (`specs/`)

| File | Document | Used for |
|---|---|---|
| Apple_Accessory_Design_Guidelines.pdf | Apple Accessory Design Guidelines | Current limits before/after enumeration, iPhone 17 Pro power |
| Apple_iPhone17Pro_dimensional_drawing.pdf | Apple iPhone 17 Pro dimensional drawing | Port keep-out and position |
| USB_Type-C_R2.5_Mar2026.pdf | USB Type-C Cable and Connector Spec R2.5 (March 2026) | Rd, CC voltages, SBU, cable wiring, attach rules |
| USB_Type-C_R2.0_Aug2019.pdf | USB Type-C Spec R2.0 (August 2019) | Earlier cross-check; superseded by R2.5 |
| USB_PD_R3.2_V1.2_2026-08-19.pdf | USB Power Delivery R3.2 V1.2 (2026-08-19) | vSafe5V range, VBUS ripple |

Web references not stored as files: [Apple TN3190 USB audio](https://developer.apple.com/documentation/technotes/tn3190-usb-audio-device-design-considerations), [47 CFR Part 15](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15) (§15.23, §15.203, §15.209, §15.239).

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
