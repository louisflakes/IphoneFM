"""Builds readable KiCad symbols from a datasheet pin table and writes them into the Rev A project library.
Pins are given per side in the order they should appear; the body is sized so pin names never overlap.
Usage (from Python):  from kicad_symbol import add_symbol;  add_symbol("LMX2571", {...})"""
import os
import re

LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kicad", "rev-a", "symbols", "IphoneFM.kicad_sym")
G = 2.54        # pin pitch, 100 mil (pin ends stay on the 50 mil grid)
CH = 1.27 * 0.8  # rough width of one 1.27 mm character


def _snap(v):
    return round(v / G) * G


def _font(hide=False):
    return f'(effects (font (size 1.27 1.27)){" (hide yes)" if hide else ""})'


def _prop(key, val, x, y, hide=False, justify=""):
    j = f" (justify {justify})" if justify else ""
    return f'\t\t(property "{key}" "{val}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)){j}{" (hide yes)" if hide else ""}))\n'


def build(name, sides, ref="U", description="", datasheet="", footprint=""):
    """sides: {"left": [(num, name, type), ...], "right": [...], "top": [...], "bottom": [...]}; None in a list leaves a gap"""
    L, R, T, B = (sides.get(k, []) for k in ("left", "right", "top", "bottom"))
    longest = lambda pins: max([len(p[1]) for p in pins if p] or [0])
    # height: side pins plus room for the vertical names of the top and bottom pins
    top_room = _snap(longest(T) * CH + 2 * G) if T else G
    bot_room = _snap(longest(B) * CH + 2 * G) if B else G
    rows = max(len(L), len(R), 1)
    height = top_room + (rows - 1) * G + bot_room
    # width: the wider of the two name columns side by side, or the top/bottom pin rows
    cols = max(len(T), len(B), 1)
    width = max(_snap((longest(L) + longest(R)) * CH + 4 * G), _snap((cols + 1) * G), 10 * G)
    width = _snap(width / 2) * 2
    x0, x1, y0, y1 = -width / 2, width / 2, height / 2, -height / 2
    y0, y1 = _snap(y0), _snap(y1)
    out = []
    def pin(num, nm, typ, x, y, ang):
        out.append(f'\t\t\t(pin {typ} line (at {x:.2f} {y:.2f} {ang}) (length {G}) (name "{nm}" {_font()}) (number "{num}" {_font()}))\n')
    for i, p in enumerate(L):
        if p: pin(*p, x0 - G, y0 - top_room - i * G, 0)
    for i, p in enumerate(R):
        if p: pin(*p, x1 + G, y0 - top_room - i * G, 180)
    start = -_snap((len(T) - 1) * G / 2)
    for i, p in enumerate(T):
        if p: pin(*p, start + i * G, y0 + G, 270)
    start = -_snap((len(B) - 1) * G / 2)
    for i, p in enumerate(B):
        if p: pin(*p, start + i * G, y1 - G, 90)
    s = f'\t(symbol "{name}"\n\t\t(pin_names (offset 1.016))\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
    s += _prop("Reference", ref, x0, y0 + 1.27 + (G if T else 0), justify="left bottom")
    s += _prop("Value", name, x0, y1 - 1.27 - (G if B else 0), justify="left top")
    s += _prop("Footprint", footprint, 0, 0, hide=True)
    s += _prop("Datasheet", datasheet, 0, 0, hide=True)
    s += _prop("Description", description, 0, 0, hide=True)
    s += f'\t\t(symbol "{name}_0_1"\n\t\t\t(rectangle (start {x0:.2f} {y0:.2f}) (end {x1:.2f} {y1:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))\n\t\t)\n'
    s += f'\t\t(symbol "{name}_1_1"\n' + "".join(out) + "\t\t)\n\t)\n"
    return s


def add_symbol(name, sides, **kw):
    """Write (or replace) one symbol in the project library"""
    os.makedirs(os.path.dirname(LIB), exist_ok=True)
    text = open(LIB, encoding="utf-8").read() if os.path.exists(LIB) else '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "iphonefm_tools")\n)\n'
    # drop an existing symbol of this name (balanced-paren scan)
    m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), text)
    if m:
        i, depth = m.start() + 1, 0
        for j in range(i, len(text)):
            depth += {"(": 1, ")": -1}.get(text[j], 0)
            if depth == 0:
                text = text[:m.start()] + text[j + 1:]
                break
    body = build(name, sides, **kw)
    k = text.rstrip().rfind(")")
    text = text[:k] + body + ")\n"
    open(LIB, "w", encoding="utf-8", newline="\n").write(text)
    return LIB
