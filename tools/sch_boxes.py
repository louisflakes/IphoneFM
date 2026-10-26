"""Bounding boxes of every placed symbol on the Rev A schematic, in sheet millimetres (y down), from the symbols' own
graphics and pins in lib_symbols, turned and mirrored as placed. Used to mark parts on schematic pictures.
Usage: python tools/sch_boxes.py [REF ...]"""
import math
import sys

sys.path.insert(0, "tools")
from kicadcheck import kid, kids, sexpr

SCH = "kicad/rev-a/IphoneFM.kicad_sch"


def _points(sym):
    """Every graphic and pin point of a library symbol (all units), in its own frame (y up)."""
    pts = []
    for unit in kids(sym, "symbol") + [sym]:
        for it in unit[1:]:
            if not isinstance(it, list) or not it:
                continue
            tag = it[0]
            if tag == "rectangle":
                for k in ("start", "end"):
                    p = kid(it, k)
                    pts.append((float(p[1]), float(p[2])))
            elif tag in ("polyline", "bezier"):
                for xy in kids(kid(it, "pts"), "xy"):
                    pts.append((float(xy[1]), float(xy[2])))
            elif tag == "circle":
                c, r = kid(it, "center"), float(kid(it, "radius")[1])
                pts += [(float(c[1]) - r, float(c[2]) - r), (float(c[1]) + r, float(c[2]) + r)]
            elif tag == "arc":
                for k in ("start", "mid", "end"):
                    p = kid(it, k)
                    pts.append((float(p[1]), float(p[2])))
            elif tag == "pin":
                at, ln = kid(it, "at"), float(kid(it, "length")[1])
                x, y, a = float(at[1]), float(at[2]), math.radians(float(at[3]) if len(at) > 3 else 0)
                pts += [(x, y), (x + ln * math.cos(a), y + ln * math.sin(a))]
    return pts


def boxes():
    t = sexpr(open(SCH, encoding="utf-8").read())
    lib = {s[1]: _points(s) for s in kids(kid(t, "lib_symbols"), "symbol")}
    out = {}
    for s in kids(t, "symbol"):
        ref = next((p[2] for p in kids(s, "property") if p[1] == "Reference"), None)
        lid = kid(s, "lib_id")[1]
        if not ref or lid not in lib or not lib[lid]:
            continue
        at = kid(s, "at")
        X, Y, rot = float(at[1]), float(at[2]), math.radians(float(at[3]) if len(at) > 3 else 0)
        mir = kid(s, "mirror")
        xs, ys = [], []
        for x, y in lib[lid]:
            y = -y                                    # library y points up
            if mir and mir[1] == "y":
                x = -x
            if mir and mir[1] == "x":
                y = -y
            c, si = math.cos(rot), math.sin(rot)
            xs.append(X + x * c + y * si)
            ys.append(Y - x * si + y * c)
        out[ref] = (min(xs), min(ys), max(xs), max(ys))
    return out


if __name__ == "__main__":
    b = boxes()
    for r in sys.argv[1:] or sorted(b):
        print(r, [round(v, 2) for v in b[r]])
