"""What the keycap screens and status panels show at each point of the first-run tutorial.

    ../PolyKybdHost/.venv/bin/python render/tutorial_screens.py <out dir>   # a contact sheet per state

Used by tutorial_video.py. Every function returns a Frame: {matrix "r,c": 72x40
float array (0 dark .. 1 lit)} for the keycaps, plus the two 128x64 status
panels. The legends come from PolyKybdHost's firmware-faithful demo renderers,
which read the firmware sources directly:

- base, Shift, Fn and Num: lang_demo.build_frame (oled_preview.render_key and the
  static legend table)
- the Lang menu: lang_layer_demo.build_frame (region tabs, flags)
- the emoji menu: emoji_demo.build_state in its pixel-exact gfx mode
- the Intl picker: intl_picker_demo's latin_ex_map, drawn through the same renderer
- the status lines: the strings of anim/tutorial.c and poly_keymap.c's
  tutorial_tour_line(), set in a bold sans (the firmware's status face is close)

Tutorial-only drawing (the focus ring, the dark keys, a language name spelled on
the keys) is composed here on top of those, from base/tutorial_plan.h's numbers.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HOST = os.path.abspath(os.path.join(REPO, "..", "PolyKybdHost"))
PK = os.path.abspath(os.path.join(REPO, "..", "qmk_firmware", "keyboards", "polykybd"))
sys.path.insert(0, os.path.join(HOST, "tools"))

import oled_preview as op  # noqa: E402
import lang_demo as ld  # noqa: E402
import lang_layer_demo as lld  # noqa: E402
import emoji_demo as ed  # noqa: E402
import intl_picker_demo as ipd  # noqa: E402
from gfx_font import load_all_fonts  # noqa: E402
from kle_render import KeyContent, KleRenderer  # noqa: E402

op.OVERSHOOT = 0
OW, OH = 72, 40
SW, SH = 128, 64
STATUS_FONT = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
CJK_FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
KEYMAP = os.path.join(PK, "split72", "keymaps", "default", "keymap.c")
MATRICES = ld.parse_layout_matrix(os.path.join(PK, "split72", "keyboard.json"))
NO_DISPLAY = {"3,7", "8,0"}                        # the encoders


class Frame:
    def __init__(self, keys=None, status=(None, None)):
        self.keys = keys or {}                     # mp -> (40, 72) float
        self.status = list(status)                 # [left, right] (64, 128) float or None

    def copy(self):
        return Frame(dict(self.keys), list(self.status))


def _arr(img):
    """A demo renderer's keycap (PIL L / 1 / RGB, 72x40) as floats 0..1."""
    if img is None:
        return None
    a = np.asarray(img.convert("L"), np.float32) / 255
    return (a > 0.5).astype(np.float32)


class Screens:
    def __init__(self, lang="en-US"):
        self.lang = lang
        named = op.load_named_glyphs(os.path.join(PK, "lang", "named_glyphs.h"))
        self.L = op.Lang(os.path.join(PK, "lang", "lang_lut.xlsx"), named)
        self.fonts = load_all_fonts(os.path.join(PK, "base", "fonts"))
        self.R = op.Renderer(self.fonts)
        self.static = ld.parse_static_text_map(os.path.join(PK, "keycode_helper.c"))
        self._layers = {}
        self._status_font = {s: ImageFont.truetype(STATUS_FONT, s) for s in (13, 15, 17)}
        # the Lang menu
        roles = lld.parse_ll_roles(KEYMAP)
        off, langs, labels, spp, nreg = lld.parse_lang_layer(os.path.join(PK, "lang_layer.c"),
                                                             os.path.join(PK, "lang_layer.h"))
        tiny = lld.load_one_font(os.path.join(PK, "base", "fonts", "nano_font.h"),
                                 "NotoSans_Regular_Nano_10px7b")
        cur = self.L.langs.index(lang) if lang in self.L.langs else -1
        self.ll_ctx = (dict(zip(MATRICES, roles)), off, langs, labels, spp, nreg, self.L, self.R,
                       self.fonts, tiny, op.Renderer([tiny]), self.static, cur)
        self.nreg = nreg
        # the emoji menu, pixel-exact
        self.emj_roles = dict(zip(MATRICES, ed.parse_emj_layer_roles(KEYMAP)))
        self.emj_cats = ed.parse_categories(os.path.join(PK, "emoji", "emoji_data.h"))
        self.emj_icons = ed.parse_tab_icons(os.path.join(PK, "emoji", "emoji_layer.c"))
        ed.ARROW_PREV, ed.ARROW_NEXT = chr(0x83), chr(0x84)
        kle = json.load(open(os.path.join(HOST, "polyhost", "res", "polykybd-split72.json"), encoding="utf-8"))
        self.kle = KleRenderer(kle, unit=72, glyphs=ed.GfxGlyphRenderer(os.path.join(PK, "base", "fonts")),
                               bezel=False, dither=False)
        # the Intl picker
        self.latin = ipd.parse_latin_ex_map(os.path.join(PK, "lang", "lang_lut.c"))

    # ---- whole layers --------------------------------------------------------
    def layer(self, name="_L0", shift=False):
        """A layer as the board draws it; `_______` keys show the base layer below."""
        key = (name, shift)
        if key not in self._layers:
            base = dict(zip(MATRICES, ld.parse_base_layer_keycodes(KEYMAP, "_L0")))
            toks = dict(zip(MATRICES, ld.parse_base_layer_keycodes(KEYMAP, name)))
            toks = {mp: (base[mp] if t in ("_______", "KC_TRNS") else t) for mp, t in toks.items()}
            fr = ld.build_frame(self.L, self.R, toks, self.lang, self.static, 0, shift=shift)
            self._layers[key] = {mp: _arr(getattr(c, "_oled", None)) for mp, c in fr.items()
                                 if getattr(c, "_oled", None) is not None and mp not in NO_DISPLAY}
        return Frame(dict(self._layers[key]))

    def lang_menu(self, region, page=0, flash=None):
        fr = lld.build_frame(self.ll_ctx, region, page, flash)
        return Frame({mp: _arr(getattr(c, "_oled", None)) for mp, c in fr.items()
                      if getattr(c, "_oled", None) is not None and mp not in NO_DISPLAY})

    def emoji_menu(self, cat, page=0):
        st = ed.build_state(self.emj_roles, self.emj_cats, self.emj_icons, cat, page)
        keys = {}
        for mp, c in st.items():
            if mp in NO_DISPLAY:
                continue
            img = self.kle._oled_buffer(c)
            if img is not None:
                keys[mp] = _arr(img)
        # the left base key keeps its legend (the static table)
        fr = self.layer("_EMJ")
        for mp, a in fr.keys.items():
            if self.emj_roles.get(mp, ("", 0))[0] not in ("tab", "slot", "prev", "next"):
                keys.setdefault(mp, a)
        return Frame(keys)

    def app(self, name, mod="plain"):
        """An app's shortcut overlay on the base layout, as PolyKybdHost sends it and the
        firmware draws it: the cells of res/overlays/<name>_template.mods.png (10 x 9
        cells of 72 x 40, one per keycode_to_mapping_idx(); im_converter.py's channels:
        A plain, R Ctrl, G Alt, B Shift) go OVER the key's own legend. update_displays()
        draws the legend, then copy_overlay_to_buffer() clears a courtyard around the
        icon (kdisp_clear_rowmajor_courtyard: every lit run grown by KDISP_CY_DEFAULT = 3
        px each way) and draws the icon, so letter and icon show together."""
        from polyhost.device.keys import KeyCode, keycode_to_mapping_idx
        a = np.asarray(Image.open(os.path.join(HOST, "polyhost", "res", "overlays",
                                               f"{name}_template.mods.png")).convert("RGBA"))
        ch = {"plain": 3, "ctrl": 0, "alt": 1, "shift": 2}[mod]
        alias = {"KC_ESC": "KC_ESCAPE", "KC_LCTL": "KC_LEFT_CTRL", "KC_LSFT": "KC_LEFT_SHIFT",
                 "KC_RSFT": "KC_RIGHT_SHIFT", "KC_BSPC": "KC_BACKSPACE", "KC_ENT": "KC_ENTER",
                 "KC_SPC": "KC_SPACE", "KC_LALT": "KC_LEFT_ALT", "KC_RALT": "KC_RIGHT_ALT",
                 "KC_LGUI": "KC_LEFT_GUI", "KC_RGUI": "KC_RIGHT_GUI", "KC_RCTL": "KC_RIGHT_CTRL"}
        fr = self.layer()
        for mp, tok in zip(MATRICES, ld.parse_base_layer_keycodes(KEYMAP, "_L0")):
            tok = alias.get(tok, tok)
            if tok not in KeyCode.__members__ or mp not in fr.keys:
                continue
            i = keycode_to_mapping_idx(KeyCode[tok])
            x, y = (i % 10) * OW, (i // 10) * OH
            if not 0 <= y <= a.shape[0] - OH:
                continue
            cell = (a[y:y + OH, x:x + OW, ch] > 127).astype(np.float32)
            if cell.any():
                court = cell.copy()                    # the 3 px square courtyard around the icon
                for ax in (0, 1):
                    court = np.maximum.reduce([np.roll(court, d, ax) for d in range(-3, 4)])
                fr.keys[mp] = np.maximum(fr.keys[mp] * (1 - court), cell)
        return fr

    def intl(self, letter=None, picker=False, chosen=None):
        """_ADDLANG1 held. Letters show their selected variation; with `picker` the
        number row shows `letter`'s variations (KC_LAT0..11)."""
        fr = self.layer("_ADDLANG1")
        rows = dict(zip(MATRICES, ld.parse_base_layer_keycodes(KEYMAP, "_ADDLANG1")))
        base = dict(zip(MATRICES, ld.parse_base_layer_keycodes(KEYMAP, "_L0")))
        chosen = chosen or {}
        for mp, tok in base.items():               # every letter shows its chosen variation
            if len(tok) == 4 and tok.startswith("KC_") and tok[3].isalpha():
                li = 26 + ord(tok[3].lower()) - ord("a")   # rows 26..51 are the lower case
                if self.latin[li]:
                    cp = self.latin[li][chosen.get(tok[3].lower(), 0)]
                    fr.keys[mp] = _arr(ipd.render_cps(self.R, [cp]))
        for mp, tok in rows.items():
            if not tok.startswith("KC_LAT") or tok in ("KC_LAT_REMAP",):
                continue
            if tok.startswith("KC_LAT_PAGE"):
                fr.keys.pop(mp, None)
                continue
            n = int(tok[6:])
            if picker and letter:
                vs = self.latin[26 + ord(letter) - ord("a")]
                fr.keys[mp] = _arr(ipd.render_cps(self.R, [vs[n]])) if n < len(vs) else None
                if fr.keys[mp] is None:
                    del fr.keys[mp]
            else:
                fr.keys.pop(mp, None)
        return fr

    # ---- tutorial drawing ------------------------------------------------------
    def status_line(self, left, right):
        """The tutorial's two halves of one sentence, one per status panel."""
        out = []
        for text in (left, right):
            if not text:
                out.append(None)
                continue
            img = Image.new("L", (SW, SH), 0)
            d = ImageDraw.Draw(img)
            f = self._status_font[17]
            for size in (17, 15, 13):
                f = self._status_font[size]
                if d.textlength(text, font=f) <= SW - 6:
                    break
            tb = d.textbbox((0, 0), text, font=f)
            d.text(((SW - (tb[2] - tb[0])) / 2 - tb[0], (SH - (tb[3] - tb[1])) / 2 - tb[1]), text, font=f, fill=255)
            out.append((np.asarray(img, np.float32) > 110).astype(np.float32))
        return out

    def capital(self, lang, kc):
        """tutorial_draw_key_letter(): the key's capital at legend size one tier up."""
        return _arr(op.render_key(self.L, self.R, lang, kc, shift=True, caps=False, size=1))

    def name_frame(self, entry, latin, native, native_lang=None, tiles=None):
        """TUT_LANG_NAME: the Latin name on one half, the native one on the other (sides
        swap item by item: native on the RIGHT for an even entry)."""
        native_side = "L" if entry & 1 else "R"
        keys = {}
        for side in ("L", "R"):
            if side == native_side and tiles is not None:
                units = tiles
            elif side == native_side:
                units = [self.capital(native_lang, "KC_" + ch) for ch in native]
            else:
                units = [self.capital("en-US", "KC_" + ch) for ch in latin.upper()]
            for u, mp in name_slots(side, len(units), name_top(len(units))).items():
                keys[mp] = units[u]
        return Frame(keys)

    def more_frame(self, scripts):
        """TUT_LANG_MORE / MORE2: the number on the left half, the word on the right, in the
        heavy splash face, on the middle row (tut_more_units)."""
        left = ("10 FUN" if scripts else str(len(self.L.langs)))
        right = "SCRIPTS" if scripts else "LAYOUTS"
        keys = {}
        for side, text in (("L", left), ("R", right)):
            for u, mp in name_slots(side, len(text), 0).items():
                if text[u] != " ":
                    keys[mp] = heavy(ord(text[u]))
        return Frame(keys)

    def letter_key(self, mp, shift=False):
        """One key's own base legend."""
        return self.layer("_L0", shift).keys.get(mp)

    def spelled(self, words, row_mps):
        """Big letters, one per key, along `row_mps` (a language name on the keys)."""
        f = ImageFont.truetype(STATUS_FONT, 30)
        cjk = ImageFont.truetype(CJK_FONT, 30) if os.path.exists(CJK_FONT) else f
        keys = {}
        for mp, ch in zip(row_mps, words):
            if ch == " ":
                continue
            img = Image.new("L", (OW, OH), 0)
            f_ = cjk if ord(ch) >= 0x2E80 else f
            d = ImageDraw.Draw(img)
            tb = d.textbbox((0, 0), ch, font=f_)
            d.text(((OW - (tb[2] - tb[0])) / 2 - tb[0], (OH - (tb[3] - tb[1])) / 2 - tb[1]), ch, font=f_, fill=255)
            keys[mp] = (np.asarray(img, np.float32) > 110).astype(np.float32)
        return keys


# ---- the language preview's name screens (poly_keymap.c, TUT_LANG_NAME / MORE) ---------
from fw_anim_sim import FwSim, mp_to_half_idx  # noqa: E402

_SIM = None


def _name_keys():
    """tut_name_keys_build(): per half, display rows 1 and 2, their (up to 7) keys by board x."""
    global _SIM
    _SIM = _SIM or FwSim()
    inv = {hi: mp for mp, hi in mp_to_half_idx().items() if hi}
    out = {}
    for side in ("L", "R"):
        rows = []
        for drow in (1, 2):
            ks = []
            for c in range(8):
                idx = drow * 8 + c
                g = _SIM.GEOM[side][idx]
                if int(g[3]) and (side, idx) in inv:
                    ks.append((int(g[0]), inv[(side, idx)]))
            rows.append([mp for _, mp in sorted(ks)][:7])
        out[side] = rows
    return out


def name_slots(side, n, top):
    """tut_name_slot_unit(): which key carries unit u (u -> mp), rows centred, the odd
    spare key toward the outer edge."""
    rows = _name_keys()[side]
    out = {}
    for r in (0, 1):
        first, count = (0, top) if r == 0 else (top, n - top)
        avail = len(rows[r])
        if count == 0 or count > avail:
            continue
        slack = avail - count
        start = (slack + 1) // 2 if side == "L" else slack // 2
        for k in range(count):
            out[first + k] = rows[r][start + k]
    return out


def name_top(n):
    return (n + 1) // 2 if n > 7 else 0


def name_tiles(tag):
    """A pre-rendered native name from anim/tutorial_names_gen.h (72x40 tiles, row-major,
    9 bytes per row, MSB first)."""
    import re
    t = open(os.path.join(PK, "anim", "tutorial_names_gen.h"), encoding="utf-8").read()
    m = re.search(r"TUT_NAME_TILES_" + tag + r"\[(\d+) \* 360\] = \{(.*?)\};", t, re.S)
    n = int(m.group(1))
    b = np.array([int(v, 16) for v in re.findall(r"0x[0-9A-Fa-f]{2}", m.group(2))], np.uint8)
    bits = np.unpackbits(b).reshape(n, OH, 72)
    return [bits[i].astype(np.float32) for i in range(n)]


_HEAVY = None


def heavy(cp):
    """tut_draw_heavy(): one character in the splash face, centred from its measured box."""
    global _HEAVY
    if _HEAVY is None:
        _HEAVY = lld.load_one_font(os.path.join(PK, "base", "fonts", "FreeSansBold24pt7b.h"), "FreeSansBold24pt7b")
    f = _HEAVY
    a = np.zeros((OH, OW), np.float32)
    if not (f.first <= cp <= f.last):
        return a
    g = f.glyphs[cp - f.first]
    pts = list(lld._glyph_pixels(f, g))
    if not pts:
        return a
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ox = (OW - (max(xs) - min(xs) + 1)) // 2 - min(xs)
    oy = (OH - (max(ys) - min(ys) + 1)) // 2 - min(ys)
    for x, y in pts:
        if 0 <= x + ox < OW and 0 <= y + oy < OH:
            a[y + oy, x + ox] = 1.0
    return a


def ring(a, cx, cy, r, w):
    """Draw a ring (centre and radius in this key's own pixels) into keycap array `a`."""
    yy, xx = np.mgrid[0:OH, 0:OW]
    d = np.hypot(xx - cx, yy - cy)
    m = np.abs(d - r) < w / 2
    a = a.copy()
    a[m] = 1.0
    return a


def contact_sheet(frame, path):
    """Every keycap by matrix position, left half then right, and both status panels."""
    img = Image.new("L", (16 * (OW + 4) + 24, 5 * (OH + 4) + SH + 8), 20)
    for mp, a in frame.keys.items():
        if a is None:
            continue
        r, c = (int(v) for v in mp.split(","))
        x = (c if r < 5 else 8 + c) * (OW + 4) + (0 if r < 5 else 24)
        img.paste(Image.fromarray((a * 255).astype(np.uint8)), (x, (r % 5) * (OH + 4)))
    for i, s in enumerate(frame.status):
        if s is not None:
            img.paste(Image.fromarray((s * 255).astype(np.uint8)), (i * (8 * (OW + 4) + 24) + 200, 5 * (OH + 4) + 4))
    img.save(path)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    S = Screens()
    for name, fr in (("base", S.layer()), ("shift", S.layer("_L0", True)), ("fn", S.layer("_FL")),
                     ("num", S.layer("_NL")), ("lang_eu", S.lang_menu(1)), ("emoji4", S.emoji_menu(4)),
                     ("intl", S.intl()), ("picker_e", S.intl("e", True))):
        fr.status = S.status_line("Press and hold", "SHIFT")
        contact_sheet(fr, os.path.join(out, name + ".png"))
        print(name, len(fr.keys), "keys")
