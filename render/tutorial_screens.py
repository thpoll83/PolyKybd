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

    def letter_key(self, mp, shift=False):
        """One key's own base legend."""
        return self.layer("_L0", shift).keys.get(mp)

    def spelled(self, words, row_mps):
        """Big letters, one per key, along `row_mps` (a language name on the keys)."""
        f = ImageFont.truetype(STATUS_FONT, 30)
        keys = {}
        for mp, ch in zip(row_mps, words):
            img = Image.new("L", (OW, OH), 0)
            d = ImageDraw.Draw(img)
            tb = d.textbbox((0, 0), ch, font=f)
            d.text(((OW - (tb[2] - tb[0])) / 2 - tb[0], (OH - (tb[3] - tb[1])) / 2 - tb[1]), ch, font=f, fill=255)
            keys[mp] = (np.asarray(img, np.float32) > 110).astype(np.float32)
        return keys


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
