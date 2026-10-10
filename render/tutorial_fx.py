"""The tutorial's rings and key LEDs, ported from the firmware, for tutorial_video.py.

numpy only, so it runs under Blender's bundled Python. Sources, all in
qmk_firmware/keyboards/polykybd/:

- the ring: anim/focus_ring.c (poly_focus_overlay, focus_latch, focus_spark) over
  base/tutorial_plan.c's curves (tut_ripple_radius, tut_ring_width,
  tut_ripple_density, tut_sweep_radius, tut_dither). Drawn in BOARD units through
  each panel's geometry (startup_anim_geom.h, via PolyKybdHost's fw_anim_sim), so a
  ring crosses keycaps and its dither erodes on the board, not per key.
- the LEDs: anim/tutorial_rgb.c (tutorial_rgb_paint): the pointed key breathes in
  its hue, a sweep lights the keys under its band, a language name glows faintly,
  each fading out over TRGB_FALL_MS once no longer wanted. hue_val() caps every hue's
  luma at TRGB_LUMA_REF and hue_floor() keeps a dim mix from collapsing to a primary.

Times are ms; a key is its matrix label "r,c".
"""
import colorsys
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PK = os.path.abspath(os.path.join(HERE, "..", "..", "qmk_firmware", "keyboards", "polykybd"))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "PolyKybdHost", "tools")))
from fw_anim_sim import FwSim, mp_to_half_idx  # noqa: E402


def _defines(path):
    return {m.group(1): int(m.group(2)) for m in
            re.finditer(r"#define\s+(\w+)\s+(\d+)u?\b", open(path, encoding="utf-8").read())}


P = _defines(os.path.join(PK, "base", "tutorial_plan.h"))
R = _defines(os.path.join(PK, "anim", "tutorial_rgb.c"))
F = _defines(os.path.join(PK, "anim", "focus_ring.c"))
K_HUES = [21, 43, 64, 106, 128, 149, 191, 213, 234]   # tutorial_rgb.c k_hues
KEY_REACH = 41                                        # POLY_FOCUS_KEY_REACH
OW, OH = 72, 40


# ---- base/tutorial_plan.c ---------------------------------------------------------
def fade_contrast(p):
    return (p * p * (765 - 2 * p)) // 65025


def travel(p):
    q = 255 - p
    return ((65025 - q * q) * 255) // 65025


def ripple_radius(p):
    return P["TUT_RIPPLE_R0"] + ((P["TUT_RIPPLE_MAX_R"] - P["TUT_RIPPLE_R0"]) * travel(p)) // 255


def ring_width(p):
    return P["TUT_RING_W0"] - ((P["TUT_RING_W0"] - P["TUT_RING_W"]) * travel(p)) // 255


def ripple_density(p):
    r = ripple_radius(p)
    if r <= P["TUT_RIPPLE_SOLID_R"]:
        return 255
    if r >= P["TUT_RIPPLE_MAX_R"]:
        return 0
    span, left = P["TUT_RIPPLE_MAX_R"] - P["TUT_RIPPLE_SOLID_R"], P["TUT_RIPPLE_MAX_R"] - r
    return (255 * left * left) // (span * span)


def sweep_radius(p):
    return (P["TUT_SWEEP_MAX_R"] * travel(p)) // 255


def sweep_density(p):
    if p < 192:
        return 255
    left = 255 - p
    return (left * left * 255) // (63 * 63)


def dither(x, y):
    """tut_dither over arrays of board positions (uint32 wraparound as in C)."""
    x = np.asarray(x, np.int64) & 0xFFFF
    y = np.asarray(y, np.int64) & 0xFFFF
    h = ((x * 73856093) ^ (y * 19349663)) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return h & 0xFF


def pulse_level(t, full=255):
    """tut_pulse_level(): eased between TUT_PULSE_FLOOR/255 and full."""
    half = P["TUT_PULSE_PERIOD_MS"] // 2
    ph = int(t) % P["TUT_PULSE_PERIOD_MS"]
    tri = ph if ph < half else P["TUT_PULSE_PERIOD_MS"] - ph
    ease = fade_contrast((tri * 255) // half)
    lo = (full * P["TUT_PULSE_FLOOR"]) // 255
    return lo + ((full - lo) * ease) // 255


# ---- the board ----------------------------------------------------------------------
class Board:
    """Every keycap pixel's board position, as poly_focus_overlay() computes it."""
    def __init__(self):
        sim = FwSim()
        ly, lx = np.mgrid[0:OH, 0:OW]
        dx, dy = lx - 36, ly - 20
        self.gx, self.gy, self.centre = {}, {}, {}
        for mp, hi in mp_to_half_idx().items():
            if hi is None:
                continue
            cx, cy, ang, valid = (int(v) for v in sim.GEOM[hi[0]][hi[1]])
            if not valid:
                continue
            if ang:
                cosv = int(sim._sin((ang + 64) & 0xFF)) - 128
                sinv = int(sim._sin(ang)) - 128
                self.gx[mp] = cx + ((dx * cosv - dy * sinv) >> 7)
                self.gy[mp] = cy + ((dx * sinv + dy * cosv) >> 7)
            else:
                self.gx[mp], self.gy[mp] = cx + dx, cy + dy
            self.centre[mp] = (cx, cy)
        self.dith = {mp: dither(self.gx[mp], self.gy[mp]) for mp in self.gx}

    def ripple(self, origin, el):
        """The small ring from key `origin`, el ms after it was struck: {key: mask}."""
        if el < 0 or el >= P["TUT_RIPPLE_MS"] or origin not in self.centre:
            return {}
        p = int(el * 255 // P["TUT_RIPPLE_MS"])
        r, w, dens = ripple_radius(p), ring_width(p), ripple_density(p)
        return self._band(self.centre[origin], r, w, dens)

    def sweep(self, origin, el, run_ms):
        """A board-sized front from `origin`: ({key: mask}, radius, density, band for the LEDs)."""
        if el < 0 or el >= run_ms or origin not in self.centre:
            return {}, None, 0, None
        p = int(el * 255 // run_ms)
        r, dens = sweep_radius(p), sweep_density(p)
        W, trail = F.get("POLY_FOCUS_SWEEP_W", 44), F.get("POLY_FOCUS_TRAIL", 80)
        masks = self._band(self.centre[origin], r, W, dens)
        # sparks behind the front (focus_spark), 2x2 board cells, re-rolled per tick
        cx, cy = self.centre[origin]
        inner = max(0, r - W)
        tin = max(0, inner - trail)
        span = inner * inner - tin * tin
        tick = int(el) // F.get("POLY_FOCUS_SPARK_TICK_MS", 90)
        if span > 0:
            for mp in self.gx:
                d2 = (self.gx[mp] - cx) ** 2 + (self.gy[mp] - cy) ** 2
                m = (d2 < inner * inner) & (d2 >= tin * tin)
                if not m.any():
                    continue
                dens_s = (F.get("POLY_FOCUS_SPARK_MAX", 12) * (d2 - tin * tin)) // span
                h = dither((self.gx[mp] >> 1) + tick * 37, (self.gy[mp] >> 1) + tick * 91)
                sp = m & (h < dens_s)
                if sp.any():
                    masks[mp] = masks.get(mp, np.zeros((OH, OW), bool)) | sp
        reach = r + KEY_REACH
        band = (cx, cy, reach * reach, max(0, r - W - KEY_REACH) ** 2, dens)
        return masks, r, dens, band

    def _band(self, c, r, w, dens):
        cx, cy = c
        outer2, inner2 = r * r, max(0, r - w) ** 2
        out = {}
        for mp in self.gx:
            d2 = (self.gx[mp] - cx) ** 2 + (self.gy[mp] - cy) ** 2
            m = (d2 <= outer2) & (d2 >= inner2) & (dens > self.dith[mp])
            if m.any():
                out[mp] = m
        return out

    def within(self, origin, mp, r):
        """Has a front of radius r from `origin` passed key `mp`'s centre?"""
        (ox, oy), (kx, ky) = self.centre[origin], self.centre[mp]
        return (kx - ox) ** 2 + (ky - oy) ** 2 <= r * r


# ---- anim/tutorial_rgb.c ---------------------------------------------------------------
SAT = R.get("TRGB_SAT", 220)


def hsv_rgb(h, v):
    """QMK hsv_to_rgb(h, TRGB_SAT, v) in 0..255 floats (close enough to its 8-bit maths)."""
    r, g, b = colorsys.hsv_to_rgb(h / 256, SAT / 255, v / 255)
    return np.array([r, g, b]) * 255


def hue_floor(h):
    c = hsv_rgb(h, 255)
    md = sum(c) - max(c) - min(c)
    return int(np.ceil(R["TRGB_MIN_CH"] * 255 / max(md, 1)))


def hue_val(h, val):
    c = hsv_rgb(h, 255)
    y = (54 * c[0] + 183 * c[1] + 19 * c[2]) / 256
    if y <= R["TRGB_LUMA_REF"]:
        return val
    v = int(round(val * R["TRGB_LUMA_REF"] / y))
    fl = hue_floor(h)
    return fl if (val and v < fl) else v


def glow_rgb(h, val, lvl):
    """set_glow(): the raw LED colour (0..255 per channel) at level lvl of peak val."""
    val = hue_val(h, val)
    v = val * lvl // 255
    if v < hue_floor(h):
        return np.zeros(3)
    return hsv_rgb(h, 255) * v / 255


def pulse_lvl(h, val, wave):
    val = hue_val(h, val)
    lo = min(255, (hue_floor(h) * 255 + val - 1) // val)
    return lo + ((255 - lo) * wave) // 255


class Leds:
    """Each key LED's level, hue and peak, advanced frame by frame like tutorial_rgb_paint()."""
    def __init__(self):
        self.lvl, self.hue, self.val = {}, {}, {}

    def step(self, now, dt, board, pointed=None, phase=0, sweep_band=None, sweep_hue=0,
             named=(), name_hue=0):
        """Advance one frame; returns {key: raw rgb 0..255}."""
        down = dt * 255 / R["TRGB_FALL_MS"]
        wave = pulse_level(now, 255)
        out = {}
        for mp in board.centre:
            target, hue, val = 0, self.hue.get(mp, 0), self.val.get(mp, 0)
            if sweep_band is not None:
                cx, cy, outer2, inner2, dens = sweep_band
                kx, ky = board.centre[mp]
                d2 = (kx - cx) ** 2 + (ky - cy) ** 2
                if inner2 <= d2 <= outer2:
                    target, hue, val = dens, sweep_hue, R["TRGB_SWEEP_VAL"]
            if mp == pointed:
                hue = K_HUES[(slot_of(mp) * 7 + phase * 3) % len(K_HUES)]
                target, val = pulse_lvl(hue, R["TRGB_PULSE_VAL"], wave), R["TRGB_PULSE_VAL"]
            elif mp in named:
                k = list(named).index(mp)
                kwave = pulse_level(now + k * R["TRGB_NAME_STAGGER_MS"], 255)
                target, hue, val = pulse_lvl(name_hue, R["TRGB_NAME_VAL"], kwave), name_hue, R["TRGB_NAME_VAL"]
            if target > 0:
                self.lvl[mp], self.hue[mp], self.val[mp] = target, hue, val
            else:
                self.lvl[mp] = max(0.0, self.lvl.get(mp, 0) - down)
            if self.lvl[mp] > 0 and self.val.get(mp):
                c = glow_rgb(self.hue[mp], self.val[mp], int(self.lvl[mp]))
                if c.any():
                    out[mp] = c
        return out


_HALF_IDX = None


def slot_of(mp):
    """TUT_SLOT(side, display index) for a key, as the firmware packs it."""
    global _HALF_IDX
    if _HALF_IDX is None:
        _HALF_IDX = mp_to_half_idx()
    hi = _HALF_IDX.get(mp)
    return ((0x80 if hi[0] == "R" else 0) | hi[1]) if hi else 0
