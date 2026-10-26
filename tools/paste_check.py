"""Step 2.5 check: each Rev A footprint's solder paste against its pads. Every soldered pad should get paste exactly its
own size (no paste margin or ratio at pad or footprint level); a centre pad may instead get separate paste windows,
which are reported with their coverage. Pads with no paste (test pads, through-hole) are listed.
Run from the repository root: python tools/paste_check.py"""
import sys

sys.path.insert(0, "tools")
from kicadcheck import sexpr, kids, kid
from rev_a_footprints import project_map


def margin(node):
    out = []
    for key in ("solder_paste_margin", "solder_paste_margin_ratio", "solder_paste_ratio"):
        k = kid(node, key)
        if k and float(k[1]) != 0:
            out.append(f"{key} {k[1]}")
    return out


def main():
    users = {}
    for ref, path in project_map().items():
        users.setdefault(path, []).append(ref)
    bad = 0
    for path, refs in users.items():
        name = path.split("/")[-1]
        fp = sexpr(open(path + ".kicad_mod", encoding="utf-8").read())
        notes, problems = [], margin(fp)
        pads = kids(fp, "pad")
        windows = [p for p in pads if p[1] == "" and kid(p, "layers")[1:] == ["F.Paste"]]
        one_to_one, no_paste = 0, []
        for p in pads:
            layers = kid(p, "layers")[1:]
            if p in windows:
                continue
            if "F.Paste" in layers:
                if p[2] != "smd":
                    problems.append(f"pad {p[1]} is {p[2]} but has paste")
                m = margin(p)
                if m:
                    problems.append(f"pad {p[1]}: {', '.join(m)}")
                else:
                    one_to_one += 1
            elif p[2] == "smd":
                no_paste.append(p)
        for p in no_paste:
            w, h = map(float, kid(p, "size")[1:3])
            if windows:
                area = sum(float(kid(q, "size")[1]) * float(kid(q, "size")[2]) for q in windows)
                notes.append(f"centre pad {p[1]} {w:g} x {h:g}: {len(windows)} paste windows, {100 * area / (w * h):.0f}% coverage")
            else:
                notes.append(f"pad {p[1]} {w:g} x {h:g}: no paste")
        tht = [p for p in pads if p[2] in ("thru_hole", "np_thru_hole")]
        if tht:
            notes.append(f"{len(tht)} through-hole pads or holes, no paste")
        bad += bool(problems)
        print(f"{name:52} {len(refs):3} parts | {one_to_one:3} pads 1:1 | {'; '.join(problems + notes) or '-'}")
    print("footprints with paste problems:", bad)


if __name__ == "__main__":
    main()
