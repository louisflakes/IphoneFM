"""The footprint chosen for each Rev A part in kicad/rev-a/footprints.md, as file paths without the .kicad_mod
extension. footprint_map() gives each one's source (KiCad's library, or a project footprint built by a tools/fp_*.py
script); project_map() gives the copy the board uses, in kicad/rev-a/IphoneFM.pretty (made by fp_silk_trim.py).
Shared by pinpad_check.py, silk_check.py and fp_silk_trim.py; run from the repository root."""
import json

K = r"C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/share/kicad/footprints/"
P = "kicad/rev-a/IphoneFM.pretty/"
FIXED = {"J1": P + "USB_C_Receptacle_HRO_TYPE-C-31-M-12_2020", "U1": K + "Package_DFN_QFN.pretty/QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
         "U2": P + "TI_NJK0036A_WQFN-36-1EP_6x6mm_P0.5mm_EP4.6x4.6mm", "U3": K + "Package_TO_SOT_SMD.pretty/SOT-23-5",
         "U4": K + "Package_DFN_QFN.pretty/SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm", "U5": K + "Package_TO_SOT_SMD.pretty/SOT-363_SC-70-6",
         "U6": K + "Package_TO_SOT_SMD.pretty/SOT-23-6", "U7": K + "Package_DFN_QFN.pretty/QFN-24-1EP_4x4mm_P0.5mm_EP2.75x2.75mm",
         "Y2": K + "Oscillator.pretty/Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm", "D1": P + "LED_RGB_XINGLIGHT_XL-1615RGBC_1.6x1.5mm",
         "D3": K + "Package_SON.pretty/Texas_DPY0002A_0.6x1mm_P0.65mm", "D4": K + "Package_SON.pretty/Texas_DPY0002A_0.6x1mm_P0.65mm",
         "D5": K + "Diode_SMD.pretty/D_SOD-882", "J2": K + "Connector_Coaxial.pretty/SMA_BAT_Wireless_BWSMA-KWE-Z001",
         "SW1": P + "SW_SPDT_Shouhan_MSK12C02_Tabs4", "SW2": K + "Button_Switch_SMD.pretty/SW_SPST_EVQP7A",
         "SW3": P + "SW_DIP_SPSTx06_Side_CK_TDP06H1SBD1_W7.62mm_P1.27mm",
         "RV1": P + "Potentiometer_Alps_RK10J_Reflow_Thumbwheel_14mm", "RV2": P + "Potentiometer_Alps_RK10J_Reflow_Thumbwheel_14mm",
         "RV3": P + "Potentiometer_Alps_RK10J_Reflow_Thumbwheel_14mm"}
SIZE = {"0402": "1005", "0603": "1608", "0805": "2012"}


def footprint_map():
    fp = dict(FIXED)
    net = json.load(open("design/rev-a/netlist.json", encoding="utf-8"))
    for p in net["parts"] if "parts" in net else net:
        r = p["ref"]
        if r in fp:
            continue
        sz = next((s for s in SIZE if s in p.get("package", "")), None)
        if r.startswith("R"):
            fp[r] = K + f"Resistor_SMD.pretty/R_{sz}_{SIZE[sz]}Metric"
        elif r.startswith("C"):
            fp[r] = K + f"Capacitor_SMD.pretty/C_{sz}_{SIZE[sz]}Metric"
        elif r.startswith(("L", "FB")):
            fp[r] = K + f"Inductor_SMD.pretty/L_{sz}_{SIZE[sz]}Metric"
        elif r.startswith("TP"):
            fp[r] = K + "TestPoint.pretty/TestPoint_Pad_D1.5mm"
    return fp


def project_map():
    return {r: P + path.split("/")[-1] for r, path in footprint_map().items()}
