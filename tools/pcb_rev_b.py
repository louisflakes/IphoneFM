"""Rev B Phase B4: placement of the new front-panel parts on the Rev B board (a copy of Rev A's, placed and routed).
File edits with KiCad's own Python (the pcbnew module), for use while the Rev B board is NOT open in KiCad.
Each step loads kicad/rev-b/IphoneFM.kicad_pcb, changes it, refills the pours and saves it.

Usage (from the repository root):
  "%LOCALAPPDATA%/Programs/KiCad/10.0/bin/python.exe" tools/pcb_rev_b.py STEP [STEP ...]
Steps:
  rules    B4.1  U8's own clearance rule in IphoneFM.kicad_dru
  update   B4.2  bring the schematic across (as KiCad's Update PCB from Schematic): remove parts the schematic no
                 longer has and the tracks and vias left on nets it no longer has; swap changed footprints in place;
                 add new parts beside the board; every pad's net, value and fields from KiCad's exported netlist
  fixed    B4.3-B4.5  place and lock SW3, SW4 and DS1-DS4
  pullups  B4.7  R30-R32 at SW4's terminals
  u8       B4.6-B4.7  U8 above the display (spot B) with R28, R29, C42, C43 and C44
  tp2      B4.8  TP2 out from under DS1
  clear    B4.8  take up Rev A copper under the new parts, and what that leaves dangling; refill
"""
import os
import re
import subprocess
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from kicadcheck import sexpr, kids, kid, atom  # noqa: E402

BOARD = "kicad/rev-b/IphoneFM.kicad_pcb"
SCH = "kicad/rev-b/IphoneFM.kicad_sch"
REV_A = "kicad/rev-a/IphoneFM.kicad_pcb"   # read only
DRU = "kicad/rev-b/IphoneFM.kicad_dru"
LIB = "kicad/rev-b/IphoneFM.pretty"
CLI = os.path.join(os.path.dirname(sys.executable), "kicad-cli.exe")
NET = os.path.join(os.environ.get("TEMP", "."), "iphonefm-rev-b.net")
MM = 1e6
EDGE_X, EDGE_Y = 12.70, 59.56          # board's left and top edges (Rev A step 3.4)
EDGE_GAP = 0.51                        # copper to edge: our 0.50 mm rule (fab-rules.md) + 0.01, as Rev A 4.4

# B4.3-B4.5: the sketch's places (rev_b_front_sketch.py), in board coordinates
SW3_AT = (35.925, 64.51, -90)          # Rev A's SW3: pins 1-6 along the top row, pin 1 at the right, as Rev A
SW4_Y, SW4_ROT = 112.0, 90             # RV3's height; terminals (footprint +y) turned to face into the board
# digit tops (footprint -y) face the board's right edge. Pitch 8.3, not the sketch's 8.0: the B3 courtyards (body +0.35)
# keep our 0.3 mm courtyard gap (fab-rules.md); the display stays centred where the sketch has it (y 86.06)
DS_X, DS_PITCH, DS_ROT = 20.96, 8.3, -90
DS_Y0 = 86.06 - 1.5 * DS_PITCH


def mm(v):
    return pcbnew.FromMM(v)


def load():
    return pcbnew.LoadBoard(BOARD)


def save(board, fill=True):
    pcbnew.SaveBoard(BOARD, board)
    if fill:   # (this build can crash in board.Zones() after tracks are removed; step_clear fills in its own process)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(BOARD, board)


def step_fill():
    save(load())
    print("fill: pours refilled", flush=True)
    os._exit(0)


def netlist():
    """KiCad's own netlist of the Rev B sheet: {ref: comp info}, {(ref, pin): net}"""
    subprocess.run([CLI, "sch", "export", "netlist", "-o", NET, SCH], check=True, capture_output=True)
    root = sexpr(open(NET, encoding="utf-8").read())
    comps, pins = {}, {}
    for c in kids(kid(root, "components"), "comp"):
        fields = {}
        for f in kids(kid(c, "fields") or ["fields"], "field"):
            name = atom(f, "name")
            fields[name] = f[2] if len(f) > 2 and not isinstance(f[2], list) else ""
        comps[atom(c, "ref")] = {"value": atom(c, "value"), "footprint": atom(c, "footprint"),
                                 "uuid": atom(c, "tstamps"), "fields": fields}
    for n in kids(kid(root, "nets"), "net"):
        for node in kids(n, "node"):
            pins[(atom(node, "ref"), atom(node, "pin"))] = atom(n, "name")
    return comps, pins


def step_rules():
    text = open(DRU, encoding="utf-8").read()
    if "U8 0.4 mm-pitch pins" in text:
        print("rules: U8 rule already there"); return
    text += """# Rev B step B4.1: U8 (IS31FL3236A, QFN-44 0.4 mm pitch, Lumissil's land pattern) has 0.15 mm of copper between
# neighbouring pins, under our 0.20 mm rule; JLC's minimum is 0.10 mm (fab-rules.md). Inside U8's courtyard, pads and
# the tracks leaving them keep 0.15 mm; everywhere else the 0.20 mm rule holds.
(rule "U8 0.4 mm-pitch pins"
	(condition "A.intersectsCourtyard('U8') && B.intersectsCourtyard('U8')")
	(constraint clearance (min 0.15mm)))
"""
    open(DRU, "w", encoding="utf-8", newline="\n").write(text)
    print("rules: U8 rule added")


def set_fields(fp, ref, c):
    fp.SetReference(ref)
    fp.SetValue(c["value"])
    for name, val in c["fields"].items():
        if name in ("Footprint",):
            continue
        fp.SetField(name, val)
    fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
    fp.SetSheetname("/")
    fp.SetSheetfile("IphoneFM.kicad_sch")


def get_net(board, name):
    net = board.FindNet(name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
    return net


def step_update():
    comps, pins = netlist()
    board = load()
    on_board = {fp.GetReference(): fp for fp in board.GetFootprints()}
    removed, swapped, added = [], [], []
    for ref, fp in on_board.items():
        if ref not in comps:
            board.Remove(fp); removed.append(ref)
    park = 0
    for ref, c in sorted(comps.items()):
        lib, name = c["footprint"].split(":")
        old = on_board.get(ref)
        if old is not None and old.GetFPIDAsString() == c["footprint"]:
            continue
        fp = pcbnew.FootprintLoad(LIB, name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        set_fields(fp, ref, c)
        if old is not None:   # swap in place, as KiCad's "update footprints" does; tracks are joined at B4.3
            fp.SetPosition(old.GetPosition()); fp.SetOrientation(old.GetOrientation())
            fp.SetLocked(old.IsLocked())
            board.Remove(old); swapped.append(ref)
        else:                  # beside the board's left edge, as Rev A step 4.1
            fp.SetPosition(pcbnew.VECTOR2I(mm(-12 + 16 * (park % 2)) - mm(10), mm(70 + 9 * (park // 2))))
            park += 1; added.append(ref)
        board.Add(fp)
    # every pad's net from the netlist (pads with no pin, such as unplated holes, have none)
    changed, changed_fields = 0, []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        c = comps.get(ref)
        if c and fp.GetValue() != c["value"]:
            fp.SetValue(c["value"])
        for name, val in (c["fields"].items() if c else ()):   # symbol fields onto the footprint, as KiCad's update
            if name not in ("Footprint", "Datasheet", "Description") and (not fp.HasField(name) or fp.GetFieldText(name) != val):
                fp.SetField(name, val); changed_fields.append(f"{ref}.{name}")
        for pad in fp.Pads():
            want = pins.get((ref, pad.GetNumber()), "")
            if pad.GetNetname() != want:
                pad.SetNet(get_net(board, want) if want else board.FindNet(""))
                changed += 1
    # tracks and vias left on nets the schematic no longer has
    live = set(pins.values())
    dead = [t for t in board.GetTracks() if t.GetNetname() and t.GetNetname() not in live]
    dead_nets = sorted({t.GetNetname() for t in dead})
    for t in dead:
        board.Remove(t)
    save(board)
    print(f"update: removed {removed}; swapped {swapped}; added {added}; {changed} pad nets set; "
          f"{len(dead)} tracks/vias removed on nets {dead_nets}; fields set {changed_fields}")


def place(board, ref, x, y, rot, lock=True):
    fp = board.FindFootprintByReference(ref)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.SetLocked(lock)
    return fp


def step_fixed():
    board = load()
    # B4.3 SW3: pins 1-6 keep Rev A's x positions (1.27 mm pitch both), so each track end on an old pad moves to the
    # new pad of the same number (same x, the new row's y)
    # (the old pads are read from Rev A's board, since B4.2 swapped the footprint)
    old = {p.GetNumber(): p.GetPosition() for p in pcbnew.LoadBoard(REV_A).FindFootprintByReference("SW3").Pads()}
    sw3 = place(board, "SW3", *SW3_AT)
    new = {p.GetNumber(): p.GetPosition() for p in sw3.Pads()}
    moved = 0
    for t in board.GetTracks():
        if t.GetClass() != "PCB_TRACK":
            continue
        for get, put in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
            for n, q in old.items():
                if get() == q and q != new[n]:
                    put(new[n]); moved += 1
    # B4.4 SW4: knob centre at RV3's height, moved in until its copper is EDGE_GAP from the left edge
    sw4 = place(board, "SW4", 30.0, SW4_Y, SW4_ROT)
    left = pcbnew.ToMM(min(p.GetBoundingBox().GetLeft() for p in sw4.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH))
    x4 = round(30.0 - (left - (EDGE_X + EDGE_GAP)) + 0.004, 2)
    place(board, "SW4", x4, SW4_Y, SW4_ROT)
    # B4.5 DS1-DS4, DS1 at the top: reading order with the phone's left edge down
    for i in range(4):
        place(board, f"DS{i + 1}", DS_X, DS_Y0 + i * DS_PITCH, DS_ROT)
    save(board)
    left = min(pcbnew.ToMM(p.GetBoundingBox().GetLeft()) for f in ("SW4", "DS1") for p in
               board.FindFootprintByReference(f).Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH)
    print(f"fixed: SW3 at {SW3_AT}, {moved} track ends joined to its new pads; SW4 knob centre ({x4}, {SW4_Y}) "
          f"{SW4_ROT} deg, wheel {7.25 - (x4 - EDGE_X):.2f} mm past the edge; DS1-DS4 at x {DS_X}; "
          f"nearest copper {left - EDGE_X:.3f} mm from the left edge")



def at_pin(board, ref, pin_ref, pin, gap=0.25):
    """Rev A step 4.13 (as pcb_local.py): a two-pad part straight out from a pin, the pad on the pin's net facing it.
    The pin's pad must face +x, -x, +y or -y from its footprint; the part stands off along that direction."""
    fp = board.FindFootprintByReference(ref)
    host = board.FindFootprintByReference(pin_ref)
    pad = next(p for p in host.Pads() if p.GetNumber() == pin)
    net = pad.GetNetname()
    c, hc = pad.GetPosition(), host.GetPosition()
    dx, dy = c.x - hc.x, c.y - hc.y
    out = (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1)
    half = pcbnew.ToMM(pad.GetBoundingBox().GetWidth() if out[1] == 0 else pad.GetBoundingBox().GetHeight()) / 2
    own = {p.GetNumber(): p for p in fp.Pads()}
    first = own["1"].GetNetname() == net          # pad 1 sits at the footprint's -x
    rot = {(1, 0): 0, (-1, 0): 180, (0, 1): -90, (0, -1): 90}[out] + (0 if first else 180)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(0, 0))
    reach = max(abs(pcbnew.ToMM(p.GetPosition().x if out[1] == 0 else p.GetPosition().y)) for p in fp.Pads())
    plen = pcbnew.ToMM(own["1"].GetBoundingBox().GetWidth() if out[1] == 0 else own["1"].GetBoundingBox().GetHeight()) / 2
    d = half + gap + plen + reach
    x, y = pcbnew.ToMM(c.x) + out[0] * d, pcbnew.ToMM(c.y) + out[1] * d
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    return x, y, rot


def step_pullups():
    """B4.7: R30-R32 straight out from SW4's terminals A, B and S (netlist.json local_to)"""
    board = load()
    # gap 0.95 mm: SW4's courtyard runs 0.45 mm past its terminals, and courtyards keep 0.3 mm apart
    done = [(r, *at_pin(board, r, "SW4", p, gap=0.95)) for r, p in (("R30", "1"), ("R31", "4"), ("R32", "2"))]
    save(board)
    print("pullups:", [(r, round(x, 2), round(y, 2), a) for r, x, y, a in done])


def crt(fp):
    """courtyard box in mm: (left, top, right, bottom)"""
    b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return tuple(pcbnew.ToMM(v) for v in (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()))


# B4.6: spot B (the user's choice, 2026-11-06), above the display left of H1. Turned 0 deg: the control pins (34-44:
# SDB, VCC, R_EXT, SDA, SCL) face the board's top edge and OUT1-OUT32 face left, down and right, toward the digits
U8_X, U8_ROT = 18.0, 0
GAP = 0.35   # between courtyards: the 0.3 mm rule plus a little (pcb_local.py)


def step_u8():
    """B4.6-B4.7: U8 with R28 (R_EXT), C43 (VCC) and R29 (SDB) in a row straight out from their pins, spread as Rev A
    step 4.13 (pcb_local.py), toward the top edge; U8 as high as that row's copper allows (EDGE_GAP), leaving the most
    room between U8 and DS1 for the outputs. C42 (VCC bulk) and C44 (display reservoir, B4.7) are too deep for the
    row and lie along the top edge to its right, above H1, on the way to the VBUS feed."""
    from pcb_local import spread
    board = load()
    u8 = place(board, "U8", U8_X, 65.0, U8_ROT)
    row = [("R28", "40"), ("C43", "38"), ("R29", "36")]
    pin_x = {r: pcbnew.ToMM(next(p for p in u8.Pads() if p.GetNumber() == n).GetPosition().x) for r, n in row}
    for r, n in row:
        at_pin(board, r, "U8", n)            # turn only: long axis at the pin, its pin-net pad toward U8
    width = [crt(board.FindFootprintByReference(r))[2] - crt(board.FindFootprintByReference(r))[0] for r, _ in row]
    xs = spread([pin_x[r] for r, _ in row], width)
    top = crt(u8)[1]
    for (r, _), x in zip(row, xs):
        fp = board.FindFootprintByReference(r)
        c = crt(fp)
        fp.SetPosition(fp.GetPosition() + pcbnew.VECTOR2I(mm(x - (c[0] + c[2]) / 2), mm(top - GAP - c[3])))
    # the whole group up (or down) until the row's highest copper is EDGE_GAP from the top edge
    group = [u8] + [board.FindFootprintByReference(r) for r, _ in row]
    high = min(pcbnew.ToMM(p.GetBoundingBox().GetTop()) for f in group[1:] for p in f.Pads())
    dy = (EDGE_Y + EDGE_GAP) - high
    for f in group:
        f.SetPosition(f.GetPosition() + pcbnew.VECTOR2I(0, mm(dy)))
    # C42 then C44 along the top edge right of the row, VBUS pad (1) toward U8, copper EDGE_GAP from the edge
    x = crt(board.FindFootprintByReference("R29"))[2] + GAP
    for r in ("C42", "C44"):
        fp = place(board, r, 0, 0, 0, lock=False)
        c = crt(fp)
        high = min(pcbnew.ToMM(p.GetBoundingBox().GetTop()) for p in fp.Pads())
        fp.SetPosition(pcbnew.VECTOR2I(mm(x - c[0]), mm(EDGE_Y + EDGE_GAP - high)))
        x += c[2] - c[0] + GAP
    for f in group:
        f.SetLocked(f.GetReference() == "U8")
    ds1, h1 = crt(board.FindFootprintByReference("DS1")), crt(board.FindFootprintByReference("H1"))
    u = crt(u8)
    c44 = crt(board.FindFootprintByReference("C44"))
    save(board)
    print(f"u8: U8 at ({U8_X}, {pcbnew.ToMM(u8.GetPosition().y):.3f}) {U8_ROT} deg; courtyard {ds1[1] - u[3]:.2f} mm above "
          f"DS1's, {h1[0] - u[2]:.2f} mm left of H1's; row " +
          ", ".join(f"{r} ({pcbnew.ToMM(board.FindFootprintByReference(r).GetPosition().x):.2f}, "
                    f"{pcbnew.ToMM(board.FindFootprintByReference(r).GetPosition().y):.2f})" for r in
                    ("R28", "C43", "R29", "C42", "C44")) +
          f"; C44 courtyard {h1[1] - c44[3]:.2f} mm above H1's")
    os._exit(0)


def step_tp2():
    """B4.8: TP2 (3V3) out from under DS1, into the space right of DS1 that spot A left free: below TP3 by the 3V3
    feed at x 32.2, courtyards GAP from DS1's and TP3's. Rev A's 3V3 run to SW3 starts at TP2's pad and passes over
    the via down to the feed (29.6, 69.3): that end is pulled back to the via, so the run to SW3 stays whole (were it
    left dangling, step_clear would take up the run and the via with it); B5 joins TP2 to the feed."""
    board = load()
    ds1, tp3 = crt(board.FindFootprintByReference("DS1")), crt(board.FindFootprintByReference("TP3"))
    tp2 = board.FindFootprintByReference("TP2")
    c, p = crt(tp2), tp2.GetPosition()
    net = tp2.Pads()[0].GetNetname()
    tracks = list(board.GetTracks())
    vias = [t.GetPosition() for t in tracks if t.GetClass() == "PCB_VIA" and t.GetNetname() == net]
    for t in tracks:
        if t.GetClass() != "PCB_TRACK":
            continue
        for get, put, far in ((t.GetStart, t.SetStart, t.GetEnd), (t.GetEnd, t.SetEnd, t.GetStart)):
            if get() == p:
                a, b = get(), far()
                on = [v for v in vias if (v.x - a.x) * (b.y - a.y) == (v.y - a.y) * (b.x - a.x)
                      and min(a.x, b.x) <= v.x <= max(a.x, b.x) and min(a.y, b.y) <= v.y <= max(a.y, b.y) and v != a]
                if not on:
                    sys.exit(f"tp2: no via on the track from TP2 toward {pcbnew.ToMM(b.x)}, {pcbnew.ToMM(b.y)}")
                v = min(on, key=lambda v: abs(v.x - a.x) + abs(v.y - a.y))
                put(v)
                print(f"tp2: track end pulled back from TP2's pad to the via at ({pcbnew.ToMM(v.x)}, {pcbnew.ToMM(v.y)})")
    x = ds1[2] + GAP + (pcbnew.ToMM(p.x) - c[0])
    y = tp3[3] + GAP + (pcbnew.ToMM(p.y) - c[1])
    tp2.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    save(board, fill=False)
    print(f"tp2: TP2 to ({x:.2f}, {y:.2f})", flush=True)
    os._exit(0)


NEW = {"SW3", "SW4", "U8", "R28", "R29", "R30", "R31", "R32", "C42", "C43", "C44", "DS1", "DS2", "DS3", "DS4"}
COPPER_CLASH = {"shorting_items", "clearance", "hole_clearance", "solder_mask_bridge", "tracks_crossing"}


def drc():
    out = os.path.join(os.environ.get("TEMP", "."), "iphonefm-rev-b-drc.json")
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "--severity-error", "--severity-warning", "-o", out, BOARD],
                   capture_output=True)
    import json
    return json.load(open(out, encoding="utf-8"))["violations"]


def move_with_tracks(board, ref, dx, dy):
    """Move a part and the track ends on its pads by (dx, dy) mm"""
    fp = board.FindFootprintByReference(ref)
    ends = {(p.GetPosition().x, p.GetPosition().y) for p in fp.Pads()}
    d = pcbnew.VECTOR2I(mm(dx), mm(dy))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_TRACK":
            if (t.GetStart().x, t.GetStart().y) in ends: t.SetStart(t.GetStart() + d)
            if (t.GetEnd().x, t.GetEnd().y) in ends: t.SetEnd(t.GetEnd() + d)
    fp.SetPosition(fp.GetPosition() + d)


def step_clear1():
    """One pass of step_clear, in its own process: after a save, this pcbnew build hands back bare SWIG pointers for
    the board's tracks, so each pass loads the board once, takes up what the saved board's DRC names, and saves."""
    v = drc()
    uu = set()
    for x in v:
        items = x["items"]
        new_part = any(any(f"of {r} " in i["description"] or i["description"].endswith(f"of {r}") for r in NEW)
                       for i in items)
        if x["type"] in COPPER_CLASH and new_part:
            uu |= {i["uuid"] for i in items if i["description"].startswith(("Track", "Via"))}
        if x["type"] in ("track_dangling", "via_dangling"):
            uu |= {i["uuid"] for i in items}
    board = load()
    # Rev A copper a new pad now touches takes that pad's net when KiCad rebuilds connectivity (a ground stub under
    # R31 became ENC_B): any track or via whose net differs from Rev A's is such a remnant
    was = {}
    reva = open(REV_A, encoding="utf-8").read()
    for m in re.finditer(r'\n\t\((?:segment|via|arc)\n(.*?)\n\t\)', reva, re.S):
        u, n = re.search(r'\(uuid "([^"]+)"\)', m.group(1)), re.search(r'\(net (?:\d+ )?"([^"]*)"\)', m.group(1))
        if u and n:
            was[u.group(1)] = n.group(1)
    for t in board.GetTracks():
        u = t.m_Uuid.AsString()
        if u in was and was[u] != t.GetNetname():
            uu.add(u)
    # and every via, and every top-layer track, inside a new part's courtyard (the wheels' ground stubs and the
    # stitching vias under the digits and the encoder); not SW3, whose tracks were joined to it at B4.3, and not
    # bottom-layer tracks, which pass under the parts' bodies as they did in Rev A
    boxes = []
    for fp in board.GetFootprints():
        if fp.GetReference() in NEW - {"SW3"} and pcbnew.ToMM(fp.GetPosition().x) > EDGE_X:
            b = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            boxes.append((b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()))
    inside = lambda p: any(x0 <= p.x <= x1 and y0 <= p.y <= y1 for x0, y0, x1, y1 in boxes)
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA" and inside(t.GetPosition()):
            uu.add(t.m_Uuid.AsString())
        elif t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu and (inside(t.GetStart()) or inside(t.GetEnd())):
            uu.add(t.m_Uuid.AsString())
    nets = []
    for t in list(board.GetTracks()):
        if t.m_Uuid.AsString() in uu:
            nets.append(t.GetNetname()); board.Remove(t)
    if nets:
        save(board, fill=False)
    print("PASS", len(nets), ",".join(sorted(set(nets))), flush=True)
    os._exit(0)   # this build can crash while Python tears the board down; the work is saved by then


def step_clear():
    """B4.8 (first part): take up the Rev A tracks and vias the new parts land on, then whatever that leaves dangling.
    Rev A's board had no dangling copper, so every dangling item afterwards is a remnant of a taken-up connection.
    TP4 moves 0.1 mm down, clear of SW4's courtyard."""
    count = lambda: len(re.findall(r"\n\t\((?:segment|via|arc)\n", open(BOARD, encoding="utf-8").read()))
    before = count()
    board = load()
    tp4 = board.FindFootprintByReference("TP4")
    if pcbnew.ToMM(tp4.GetPosition().y) < 121.05:
        move_with_tracks(board, "TP4", 0, 0.1)
        save(board)
    nets, rounds = set(), 0
    while True:
        for _ in range(3):   # a pass that crashes before saving (this build, now and then) is run again
            r = subprocess.run([sys.executable, __file__, "clear1"], capture_output=True, text=True)
            line = [l for l in r.stdout.splitlines() if l.startswith("PASS")]
            if line:
                break
        else:
            sys.exit(r.stdout + r.stderr)
        _, n, *names = line[0].split(" ")
        if n == "0":
            break
        rounds += 1; nets |= set(names[0].split(",")) if names else set()
    subprocess.run([sys.executable, __file__, "fill"], capture_output=True)
    print(f"clear: {before - count()} tracks/vias taken up in {rounds} passes; nets to re-route in B5: {sorted(nets)}")

if __name__ == "__main__":
    for s in sys.argv[1:]:
        globals()["step_" + s]()
