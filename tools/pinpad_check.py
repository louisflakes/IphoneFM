"""Step 2.3 check: every symbol pin number on the Rev A schematic has a pad of the same number on the footprint chosen
for that part in kicad/rev-a/footprints.md, and no pad is left without a pin; also lists pad numbers used more than once.
Run from the repository root: python tools/pinpad_check.py"""
import sys, json, re, collections
sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid
K = r"C:/Users/jakep/AppData/Local/Programs/KiCad/10.0/share/kicad/footprints/"
P = "kicad/rev-a/IphoneFM.pretty/"
FP = {"J1": P + "USB_C_Receptacle_HRO_TYPE-C-31-M-12_2020", "U1": K + "Package_DFN_QFN.pretty/QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
      "U2": P + "TI_NJK0036A_WQFN-36-1EP_6x6mm_P0.5mm_EP4.6x4.6mm", "U3": K + "Package_TO_SOT_SMD.pretty/SOT-23-5",
      "U4": K + "Package_DFN_QFN.pretty/SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm", "U5": K + "Package_TO_SOT_SMD.pretty/SOT-363_SC-70-6",
      "U6": K + "Package_TO_SOT_SMD.pretty/SOT-23-6", "U7": K + "Package_DFN_QFN.pretty/QFN-24-1EP_4x4mm_P0.5mm_EP2.75x2.75mm",
      "Y2": K + "Oscillator.pretty/Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm", "D1": P + "LED_RGB_XINGLIGHT_XL-1615RGBC_1.6x1.5mm",
      "D3": K + "Package_SON.pretty/Texas_DPY0002A_0.6x1mm_P0.65mm", "D4": K + "Package_SON.pretty/Texas_DPY0002A_0.6x1mm_P0.65mm",
      "D5": K + "Diode_SMD.pretty/D_SOD-882", "J2": K + "Connector_Coaxial.pretty/SMA_BAT_Wireless_BWSMA-KWE-Z001",
      "SW1": P + "SW_SPDT_Shouhan_MSK12C02_Tabs4", "SW2": K + "Button_Switch_SMD.pretty/SW_SPST_EVQP7A",
      "SW3": P + "SW_DIP_SPSTx06_Side_CK_TDP06H1SBD1_W7.62mm_P1.27mm"}
for r in ("RV1", "RV2", "RV3"): FP[r] = P + "Potentiometer_Alps_RK10J_Reflow_Thumbwheel_14mm"
net = json.load(open("design/rev-a/netlist.json", encoding="utf-8")); parts = net["parts"] if "parts" in net else net
SIZE = {"0402": "1005", "0603": "1608", "0805": "2012"}
for p in parts:
    r = p["ref"]
    if r in FP: continue
    pk = p.get("package", "")
    sz = next((s for s in SIZE if s in pk), None)
    if r.startswith("R"): FP[r] = K + f"Resistor_SMD.pretty/R_{sz}_{SIZE[sz]}Metric"
    elif r.startswith("C"): FP[r] = K + f"Capacitor_SMD.pretty/C_{sz}_{SIZE[sz]}Metric"
    elif r.startswith(("L", "FB")): FP[r] = K + f"Inductor_SMD.pretty/L_{sz}_{SIZE[sz]}Metric"
    elif r.startswith("TP"): FP[r] = K + "TestPoint.pretty/TestPoint_Pad_D1.5mm"
sch = sexpr(open("kicad/rev-a/IphoneFM.kicad_sch", encoding="utf-8").read())
libs = {s[1]: s for s in kids(kid(sch, "lib_symbols"), "symbol")}
def pins(sym):
    out = []
    for sub in kids(sym, "symbol"):
        out += [kid(pp, "number")[1] for pp in kids(sub, "pin")]
    return out
res = collections.OrderedDict()
for s in kids(sch, "symbol"):
    lib = kid(s, "lib_id")[1]
    ref = next((pr[2] for pr in kids(s, "property") if pr[1] == "Reference"), None)
    if not ref or ref.startswith("#"): continue
    if ref not in FP: res[ref] = ("NO FOOTPRINT", lib, [], []); continue
    sp = pins(libs[lib]); fp = sexpr(open(FP[ref] + ".kicad_mod", encoding="utf-8").read())
    pads = [p[1] for p in kids(fp, "pad") if p[1] != ""]
    res[ref] = (FP[ref].split("/")[-1], lib, sp, pads)
bad = 0
groups = collections.defaultdict(list)
for ref, (fpn, lib, sp, pads) in res.items():
    ms = sorted(set(sp) - set(pads), key=str); xp = sorted(set(pads) - set(sp), key=str)
    if fpn == "NO FOOTPRINT" or ms or xp:
        bad += 1; print(f"{ref:5} {fpn}\n      symbol pins without a pad: {ms}\n      pads without a symbol pin: {xp}\n      pad numbers: {collections.Counter(pads)}")
    else:
        groups[fpn].append(ref)
print("\nOK:", {k: len(v) for k, v in groups.items()})
print("symbols checked:", len(res), " with mismatches:", bad)
print()
for r in [r for r in res if len(set(res[r][3])) < len(res[r][3])]:
    fpn, lib, sp, pads = res[r]
    c1, c2 = collections.Counter(sp), collections.Counter(pads)
    print(r, "symbol pins used twice or more:", {k: v for k, v in c1.items() if v > 1}, "| pads used twice or more:", {k: v for k, v in c2.items() if v > 1})
