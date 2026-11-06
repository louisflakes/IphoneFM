"""Rev B Phase B2 (design/rev-b/build-procedure.md): the front panel on the Rev B schematic.
  1. Symbols, each from its maker's pin table, into the Rev B project library (kicad/rev-b/symbols):
     IS31FL3236A  Lumissil IS31FL3236A Rev. I (10/14/2024) p2-3, QFN-44 numbering (KiCad has only the 48-pin eTQFP);
                  pin types from p3 and the typical circuit p1 (OUTx are constant-current sinks: open collector)
     SIQ-02FVS3   Mitsumi SIQ series p3 (SIQ-02FVS3 circuit: A, B and the push switch S to common C; land pattern:
                  4 terminals, 4 side tabs and 2 angled tabs of the metal frame)
     GS3011AW-B   KiCad's Display_Character:KCSA02-105 (Kingbright, common anode), whose ten pins match Guangcai's
                  GS3011A/CX-X p3 one for one (E 1, D 2, CA 3, C 4, DP 5, B 6, A 7, CA 8, F 9, G 10), renamed with
                  Guangcai's description and datasheet
  2. Takes Rev A's wheels off the sheet (RV1-RV3, C39-C41) with their library symbol.
  3. Places SW4, U8 and DS1-DS4 where sch_layout.LAYOUT puts them, and R28-R32, C42-C44 where sch_place.MANUAL
     puts them. Existing parts keep their uuids (the board links to them).
Then run, with IPHONEFM_REV=rev-b: sch_layout, sch_fields, sch_power, sch_wire 3, sch_wire 9, sch_flags, sch_labels,
sch_noconnect, sch_notes, sch_pinids.
Usage: IPHONEFM_REV=rev-b python tools/sch_rev_b.py [--dry-run]"""
import json
import os
import re
import sys
import uuid

if os.environ.get("IPHONEFM_REV") != "rev-b":
    raise SystemExit("set IPHONEFM_REV=rev-b")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kicad_symbol import LIB as PROJECT_LIB, add_symbol  # noqa: E402
from kicadcheck import sexpr, kids, kid, atom  # noqa: E402
from sch_layout import LAYOUT  # noqa: E402
from sch_place import SCH, NETLIST, MANUAL, SMALL_R, block, embed_device  # noqa: E402
from sch_power import POWER_LIB, balanced  # noqa: E402

KICAD_SYMBOLS = os.path.dirname(POWER_LIB)
REMOVE = ["RV1", "RV2", "RV3", "C39", "C40", "C41"]
WHEEL_WIRES = [f"5e1c0003-0000-4000-8000-{n:012x}" for n in (0x5, 0x6, 0x7, 0x2a, 0x2b, 0x2c, 0x2f, 0x30)]
NEW_PASSIVES =["R28", "R29", "R30", "R31", "R32", "C42", "C43", "C44"]
DS_DATASHEET = "https://www.smddisplay.com/products_detail/18.html"
U8_DATASHEET = "https://www.lumissil.com/assets/pdf/core/IS31FL3236A_DS.pdf"
SW4_DATASHEET = "https://www.lcsc.com/datasheet/lcsc_datasheet_2207281230_Mitsumi-Electric-SIQ-02FVS3_C2925423.pdf"


def out_pin(k):
    """OUTk to its QFN-44 pin: OUT1, OUT2 are pins 43, 44; OUT3-OUT18 pins 1-16; OUT19-OUT36 pins 18-35 (Rev. I p3)"""
    return str(42 + k) if k <= 2 else str(k - 2) if k <= 18 else str(k - 1)


def build_symbols():
    o = lambda k: (out_pin(k), f"OUT{k}", "open_collector")
    gap = [None] * 3  # three rows between digits, so the digit symbols wired straight across clear each other
    add_symbol("IS31FL3236A", {
        "right": [o(k) for k in range(1, 9)] + gap + [o(k) for k in range(9, 17)],  # DS1, DS2
        "left": [o(k) for k in range(17, 25)] + gap + [o(k) for k in range(25, 33)],  # DS3, DS4
        "top": [("38", "VCC", "power_in"), None, ("41", "SDA", "bidirectional"), None, ("42", "SCL", "input"), None,
                ("40", "R_EXT", "passive"), None, ("36", "SDB", "input")],
        "bottom": [("37", "AD", "input"), ("17", "GND", "power_in"), ("39", "GND", "power_in"), ("45", "EP", "power_in"), None]
                  + [o(k) for k in range(33, 37)],
    }, ref="U", datasheet=U8_DATASHEET,
        description="36-channel constant-current LED driver, I2C, 2.7-5.5 V, QFN-44 5x5 mm (Lumissil IS31FL3236A Rev. I)")
    add_symbol("SIQ-02FVS3", {
        "right": [("1", "A", "passive"), None, ("4", "B", "passive"), None, ("2", "S", "passive")],  # room for each net's name
        "left": [("3", "C", "passive")],
        "bottom": [(str(k), "Frame", "passive") for k in range(5, 11)],  # tabs numbered 5-10 after A, S, C, B
    }, ref="SW", datasheet=SW4_DATASHEET,
        description="Edge thumbwheel encoder, 15 detents, A/B to common C, push-in slide switch S to C (Mitsumi SIQ-02FVS3)")
    # GS3011AW-B: KiCad's KCSA02-105 drawing and pins, renamed
    lib = open(os.path.join(KICAD_SYMBOLS, "Display_Character.kicad_sym"), encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "KCSA02-105"\n', lib)
    blk = lib[m.start() + 1:balanced(lib, m.start() + 2)]
    blk = blk.replace('"KCSA02-105', '"GS3011AW-B')
    blk = blk.replace("(pin input line", "(pin passive line")  # LED anodes and cathodes, as KiCad's own LED symbols have them
    for key, val in (("Reference", "DS"), ("Value", "GS3011AW-B"), ("Footprint", ""), ("Datasheet", DS_DATASHEET),
                     ("Description", "0.3 in single-digit 7-segment display, white, black face, common anode (Guangcai GS3011A/CX-X)"),
                     ("ki_fp_filters", "")):
        blk = re.sub(r'(\(property "%s" )"[^"]*"' % key, lambda q: f'{q.group(1)}"{val}"', blk, count=1)
    text = open(PROJECT_LIB, encoding="utf-8").read()
    mm = re.search(r'\n\t\(symbol "GS3011AW-B"\n', text)
    if mm:
        text = text[:mm.start()] + text[balanced(text, mm.start() + 2):]
    k = text.rstrip().rfind(")")
    open(PROJECT_LIB, "w", encoding="utf-8", newline="\n").write(text[:k] + blk.rstrip("\n") + "\n" + ")\n")


def top_level(text, pattern):
    """Spans of the top-level items whose opening matches pattern"""
    spans = []
    for m in re.finditer(pattern, text):
        spans.append((m.start(), balanced(text, m.start() + 2)))  # from the newline before the item to its closing bracket
    return spans


def remove_parts(text, refs):
    for ref in refs:
        for a, b in top_level(text, r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\)'):
            if f'(property "Reference" "{ref}"\n' in text[a:b]:
                text = text[:a] + text[b:]
                break
        else:
            raise SystemExit(f"{ref} not on the sheet")
    return text


def lib_symbols_span(text):
    s = text.index("\t(lib_symbols")
    return s, balanced(text, s + 1)


def drop_lib_symbol(text, lib_id):
    s, e = lib_symbols_span(text)
    m = re.search(r'\n(\t{1,2})\(symbol "%s"\n' % re.escape(lib_id), text[s:e])  # the sheet's entries sit one tab in
    if m:
        a = s + m.start()
        text = text[:a] + text[balanced(text, a + 1 + len(m.group(1))):]
    return text


def embed_project(text, name):
    """Copy a symbol from the project library into the sheet's lib_symbols as IphoneFM:name (replacing an older copy)"""
    lib_id = f"IphoneFM:{name}"
    text = drop_lib_symbol(text, lib_id)
    lib = open(PROJECT_LIB, encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), lib)
    blk = lib[m.start() + 2:balanced(lib, m.start() + 2)].replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
    s, e = lib_symbols_span(text)
    return text[:e - 1] + "\t" + blk.replace("\n", "\n\t") + "\n" + text[e - 1:]


def chip(ref, lib_id, value, x, y, rot, mirror, sheet_uuid):
    m = f"\t\t(mirror {mirror})\n" if mirror else ""
    hidden = lambda k, v: f'\t\t(property "{k}" "{v}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)) (hide yes))\n\t\t)\n'
    return (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {x:.2f} {y:.2f} {rot})\n{m}\t\t(unit 1)\n\t\t(exclude_from_sim no)\n'
            f'\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t(property "Reference" "{ref}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)\n'
            f'\t\t(property "Value" "{value}"\n\t\t\t(at {x:.2f} {y:.2f} 0)\n\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)\n'
            + hidden("Footprint", "") + hidden("Datasheet", "~") +
            f'\t\t(instances\n\t\t\t(project "IphoneFM"\n\t\t\t\t(path "/{sheet_uuid}"\n\t\t\t\t\t(reference "{ref}") (unit 1)\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def main():
    build_symbols()
    text = open(SCH, encoding="utf-8").read()
    doc = json.load(open(NETLIST, encoding="utf-8"))
    by = {p["ref"]: p for p in doc["parts"]}
    sheet_uuid = atom(sexpr(text), "uuid")
    on_sheet = lambda r: f'(property "Reference" "{r}"\n' in text
    gone = [r for r in REMOVE if on_sheet(r)]
    text = remove_parts(text, gone)
    # chain 3's wires to the wheel caps: U1 PA3-PA5 out to C39-C41 and their ground bar. Chain 3 isn't rerouted (every
    # later chain's wires now cross its area), so these go by uuid; PA3-PA5 become lone pins that sch_labels names
    for a, b in reversed(top_level(text, r'\n\t\((?:wire|junction)\b')):
        if re.search(r'\(uuid "%s"\)' % "|".join(WHEEL_WIRES), text[a:b]):
            text = text[:a] + text[b:]
    text = drop_lib_symbol(text, "IphoneFM:RK10J11R0A0H")
    for name in ("IS31FL3236A", "SIQ-02FVS3", "GS3011AW-B"):
        text = embed_project(text, name)
    text = embed_device(text, SMALL_R)
    new = []
    chips = {"SW4": "IphoneFM:SIQ-02FVS3", "U8": "IphoneFM:IS31FL3236A",
             **{f"DS{d}": "IphoneFM:GS3011AW-B" for d in range(1, 5)}}
    for ref, lib_id in chips.items():
        if on_sheet(ref):
            continue
        x, y, rot, _ = LAYOUT[ref]
        mirror = "y" if str(rot).endswith("y") else None
        new.append(chip(ref, lib_id, by[ref]["value"], x, y, int(str(rot).rstrip("y")), mirror, sheet_uuid))
    for ref in NEW_PASSIVES:
        if on_sheet(ref):
            continue
        x, y, rot, *left = MANUAL[ref]
        new.append(block(ref, by[ref], x, y, rot, bool(left and left[0]), sheet_uuid))
    k = text.rindex("\t(sheet_instances")
    # Rev A's sheet joins U1 PB6 to the wire from C36 with a stub that sch_labels drew there; it is kept as a fixed
    # wire, so a sch_labels rerun sees one RX_FS_MCU island at U1 again
    if "5e1cb000-0000-4000-8000-000000000001" not in text:
        new.append('\t(wire\n\t\t(pts (xy 208.28 259.08) (xy 205.74 259.08))\n\t\t(stroke (width 0) (type default))\n'
                   '\t\t(uuid "5e1cb000-0000-4000-8000-000000000001")\n\t)\n')
    text = text[:k] + "".join(new) + text[k:]
    print(f"removed {', '.join(gone) or 'nothing'}; added {sum(1 for b in new if b.startswith(chr(9) + '(symbol'))} symbols")
    if "--dry-run" not in sys.argv:
        open(SCH, "w", encoding="utf-8", newline="\n").write(text)


if __name__ == "__main__":
    main()
