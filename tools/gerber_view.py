"""Step 8.4: reads the exported Gerber and drill files back with gerbonara (an independent Gerber reader, not KiCad) and
draws what the fab will see: the top and bottom as built (mask, silkscreen, copper, holes; the bottom seen from below),
and each file on its own,
with a summary of what was read from each (size, apertures, holes by size). Run on the files that will be uploaded.
Usage (from the repository root): python tools/gerber_view.py GERBER_DIR OUT_DIR"""
import collections
import os
import sys
import warnings

import io

import cairosvg
import numpy as np
from gerbonara import ExcellonFile, GerberFile, LayerStack
from PIL import Image

WIDTH = 1600
# colours: green mask over bare board and over copper, gold where the mask opens on copper, white ink, black holes
MASK, MASK_CU, GOLD, BARE, SILK, HOLE, EDGE = (22, 92, 52), (40, 130, 70), (212, 170, 60), (150, 140, 90),     (245, 245, 240), (15, 15, 15), (230, 230, 230)


def png(svg, path, bg="white"):
    cairosvg.svg2png(bytestring=str(svg).encode(), write_to=path, output_width=WIDTH, background_color=bg)


def coverage(layer, bounds):
    """The layer drawn black on white at the common bounds, as a boolean array (True where it puts something)."""
    data = cairosvg.svg2png(bytestring=str(layer.to_svg(force_bounds=bounds, fg="black", bg="white")).encode(),
                            output_width=WIDTH, background_color="white")
    return np.array(Image.open(io.BytesIO(data)).convert("L")) < 128


def built(stack, side, bounds, path):
    """One side as the fab builds it: mask colour, copper under it, the mask's openings, ink, holes, outline."""
    g = stack.graphic_layers
    cu, opening, silk = (coverage(g[(side, k)], bounds) for k in ("copper", "mask", "silk"))
    holes = np.zeros_like(cu)
    for d in stack.drill_layers:
        holes |= coverage(d, bounds)
    edge = coverage(g[("mechanical", "outline")], bounds)
    img = np.zeros(cu.shape + (3,), np.uint8)
    img[:] = MASK
    img[cu] = MASK_CU
    img[opening & ~cu] = BARE
    img[opening & cu] = GOLD
    img[silk & ~opening] = SILK
    img[holes] = HOLE
    img[edge] = EDGE
    im = Image.fromarray(img)
    (im.transpose(Image.FLIP_LEFT_RIGHT) if side == "bottom" else im).save(path)


if __name__ == "__main__":
    warnings.simplefilter("ignore")   # KiCad's G90 after the drill header and RoundRect's spare parameter: harmless
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    stack = LayerStack.open(src)
    bounds = stack.graphic_layers[("mechanical", "outline")].bounding_box()
    for side in ("top", "bottom"):
        built(stack, side, bounds, os.path.join(out, f"gerber-{side}.png"))
    print("layers found:", {k: os.path.basename(str(v.original_path)) for k, v in stack.graphic_layers.items()})
    print("drill files:", [os.path.basename(str(d.original_path)) for d in stack.drill_layers])
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if name.endswith(".drl"):
            f = ExcellonFile.open(p)
            holes = collections.Counter(round(o.tool.diameter, 3) for o in f.drills())
            slots = collections.Counter(round(o.tool.diameter, 3) for o in f.slots())
            print(f"{name}: holes {dict(sorted(holes.items()))}, slots {dict(sorted(slots.items()))}")
        elif name.endswith((".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo", ".gtp", ".gbp", ".gm1")):
            f = GerberFile.open(p)
            bb = f.bounding_box()
            if bb is None:
                print(f"{name}: empty")
                continue
            (x0, y0), (x1, y1) = bb
            print(f"{name}: {len(f.objects)} objects, extent {x1 - x0:.2f} x {y1 - y0:.2f} mm")
            png(f.to_svg(fg="black", bg="white"), os.path.join(out, name.replace(".", "_") + ".png"))
