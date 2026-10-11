"""The first-run tutorial video, from eden_view.py's per-shot layers and tutorial_story.py's screens.

    <blender dir>/4.1/python/bin/python3.11 render/tutorial_video.py storyboard <layers> <story.npz> <out dir>
    <blender dir>/4.1/python/bin/python3.11 render/tutorial_video.py video <layers> <story.npz> <out.mp4> [width] [fps]

<layers> holds one folder per pass (uv, id, ambient, base), each with one EXR per
camera shot (eden_view.py with PK_SHOTS). <story.npz> and its .json come from
tutorial_story.py. `storyboard` composites one still per scene and lays them out
on captioned contact sheets, one per chapter.

A frame is built as in eden_video.py: the light layers summed (the room light
scaled per scene, so it can come up after Eden), then every keycap pixel the
camera sees through the glass looked up through the uv and id maps, at the maps'
double resolution, averaged down and given a soft bloom; the status panels are
looked up the same way (id cells 126 and 127). Then Blender's AgX view.
"""
import json
import os
import sys

import numpy as np
import OpenImageIO as oiio
import PyOpenColorIO as ocio
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SCREEN = float(os.environ.get("PK_STRENGTH", 5.0))
LIT_TINT = np.array([0.70, 0.84, 1.0], np.float32)
BLOOM = float(os.environ.get("PK_BLOOM", 0.25))
STATUS_ID = 126
OW, OH, SW, SH = 72, 40, 128, 64
LABELS = sorted(json.load(open(os.path.join(HERE, "textures", "screens_layer0.json"), encoding="utf-8"))["keys"])


def exr(path):
    return np.asarray(oiio.ImageBuf(path).get_pixels(oiio.FLOAT))[..., :3]


def blur(a, r):
    for axis in (0, 1):
        for _ in range(3):
            pad = [(0, 0), (0, 0)]
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            a = (hi - lo) / (2 * r + 1)
    return a


class Shot:
    """One camera's layers, with its screen lookup precomputed."""
    def __init__(self, layers, name):
        self.base = exr(os.path.join(layers, "base", name + ".exr"))
        self.ambient = exr(os.path.join(layers, "ambient", name + ".exr"))
        uv, idm = exr(os.path.join(layers, "uv", name + ".exr")), exr(os.path.join(layers, "id", name + ".exr"))
        self.H, self.W = self.base.shape[:2]
        assert uv.shape[:2] == (2 * self.H, 2 * self.W), (name, uv.shape, self.base.shape)
        seen = idm[..., 2] > 0.05
        b = np.maximum(idm[..., 2], 1e-6)
        self.cell = np.where(seen, np.floor(idm[..., 0] / b * 128), -1).astype(int)
        u = uv[..., 0] / np.maximum(uv[..., 2], 1e-6)
        v = uv[..., 1] / np.maximum(uv[..., 2], 1e-6)
        self.kx, self.ky = np.clip((u * OW).astype(int), 0, OW - 1), np.clip((v * OH).astype(int), 0, OH - 1)
        self.sx, self.sy = np.clip((u * SW).astype(int), 0, SW - 1), np.clip((v * SH).astype(int), 0, SH - 1)
        self.trans = np.where(seen, uv[..., 2], 0.0).astype(np.float32)
        # per cell, the pixels that show it
        self.where = {c: np.nonzero(self.cell == c) for c in np.unique(self.cell) if c >= 0}

    def screens(self, keys, status):
        """keys {label: (40, 72)}, status [left, right] (64, 128) -> lit screens at image size."""
        lit = np.zeros(self.cell.shape, np.float32)
        for c, (yy, xx) in self.where.items():
            if c >= STATUS_ID:
                s = status[c - STATUS_ID]
                if s is not None:
                    lit[yy, xx] = s[self.sy[yy, xx], self.sx[yy, xx]]
            elif c < len(LABELS) and LABELS[c] in keys:
                lit[yy, xx] = keys[LABELS[c]][self.ky[yy, xx], self.kx[yy, xx]]
        return (lit * self.trans).reshape(self.H, 2, self.W, 2).mean((1, 3))

    def frame(self, keys, status, ambient, cpu, extra=None):
        lin = self.base + self.ambient * ambient
        if extra is not None:
            lin = lin + extra
        scr = self.screens(keys, status)
        lin = lin + (scr + BLOOM * blur(scr, max(1, self.W // 320)))[..., None] * LIT_TINT * SCREEN
        img = np.ascontiguousarray(np.clip(lin, 0, None).astype(np.float32))
        cpu.applyRGB(img)
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))


def agx():
    cfg_path = (os.environ.get("BLENDER_OCIO") or os.environ.get("OCIO")
                or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(sys.executable)))),
                                "datafiles", "colormanagement", "config.ocio"))
    cfg = ocio.Config.CreateFromFile(cfg_path)
    grp = ocio.GroupTransform()
    grp.appendTransform(ocio.LookTransform(src="Linear Rec.709", dst="Linear Rec.709",
                                           looks=os.environ.get("PK_LOOK", "AgX - High Contrast")))
    grp.appendTransform(ocio.DisplayViewTransform(src="Linear Rec.709", display="sRGB", view="AgX"))
    return cfg.getProcessor(grp).getDefaultCPUProcessor()


def load_story(path):
    data = np.load(path)
    meta = json.load(open(path[:-4] + ".json", encoding="utf-8"))
    for n, s in enumerate(meta):
        k = data[f"k{n}"].astype(np.float32)
        s["keys_img"] = {mp: k[i] for i, mp in enumerate(s["keys"])}
        st = data[f"s{n}"].astype(np.float32)
        s["status_img"] = [st[i] if st[i].any() else None for i in range(2)]
    return meta


CHAPTERS = ["Eden and the three letters", "Shift and the Fn layer", "The board reveal and the languages",
            "The Lang menu", "The emoji menu", "Fn, Num, the Intl picker, finale"]
PREFIX = [("E", 0), ("C1", 0), ("C2", 1), ("C3", 1), ("C4", 2), ("T10", 5), ("T11", 5), ("T12", 5),
          ("T13", 5), ("T1", 3), ("T2", 3), ("T3", 3), ("T4", 4), ("T5", 4), ("T6", 4), ("T7", 5),
          ("T8", 5), ("T9", 5), ("F", 5)]


def chapter_of(sid):
    return next(n for p, n in sorted(PREFIX, key=lambda t: -len(t[0])) if sid.startswith(p))


def storyboard(layers, story, out, cols=3, pw=640):
    os.makedirs(out, exist_ok=True)
    cpu = agx()
    shots = {}
    meta = load_story(story)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    pages = [[] for _ in CHAPTERS]
    sys.path.insert(0, HERE)
    import tutorial_fx as fx
    board = fx.Board()
    for s in meta:
        if s["shot"] not in shots:
            shots[s["shot"]] = Shot(layers, s["shot"])
        keys = dict(s["keys_img"])
        if s.get("point"):                       # the ring 600 ms into its run
            for mp, m in board.ripple(s["point"], 600).items():
                keys[mp] = np.maximum(keys.get(mp, np.zeros((OH, OW), np.float32)), m)
        img = shots[s["shot"]].frame(keys, s["status_img"], s["ambient"], cpu)
        ph = int(pw * img.height / img.width)
        pages[chapter_of(s["id"])].append((s, img.resize((pw, ph), Image.LANCZOS)))
        print("scene", s["id"], s["shot"], flush=True)
    paths = []
    for n, panels in enumerate(pages):
        if not panels:
            continue
        ph = panels[0][1].height
        cap = 64
        rows = (len(panels) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (pw + 12) + 12, 48 + rows * (ph + cap + 12)), (18, 18, 22))
        d = ImageDraw.Draw(sheet)
        d.text((12, 10), f"{n + 1}. {CHAPTERS[n]}", font=big, fill=(240, 240, 240))
        for i, (s, img) in enumerate(panels):
            x, y = 12 + (i % cols) * (pw + 12), 48 + (i // cols) * (ph + cap + 12)
            sheet.paste(img, (x, y))
            tag = f"{s['id']}  [{s['shot']}]" + ("  PRESS" if s.get("press") else "")
            d.text((x, y + ph + 4), tag, font=bold, fill=(255, 200, 80) if s.get("press") else (150, 200, 255))
            d.text((x, y + ph + 22), s["caption"][:64], font=font, fill=(225, 225, 225))
            st = " | ".join(w for w in (s.get("status") or []) if w)
            if st:
                d.text((x, y + ph + 40), f"status: {st}", font=font, fill=(150, 150, 150))
        p = os.path.join(out, f"storyboard_{n + 1}.png")
        sheet.save(p)
        paths.append(p)
        print("wrote", p)
    return paths


# ---- the video -------------------------------------------------------------------
# Eden's rainbow, as eden_video.py builds it: QMK's CYCLE_LEFT_RIGHT fitted to 1, cos
# and sin of the phase over x, scaled by startup_anim_rainbow_level()
HUE_SPAN, HUE_PER_MS, INTRO_MS = 224 / 256, (40 // 4 + 1) / 256 / 256, 5000
THETA = np.linspace(0, 2 * np.pi * HUE_SPAN, 400)
BASIS = np.stack([np.ones_like(THETA), np.cos(THETA), np.sin(THETA)], 1)


def rainbow_level(el):
    a, b = INTRO_MS * 180 // 256, INTRO_MS * 240 // 256
    return 1.0 if el <= a else 0.0 if el >= b else 1.0 - (el - a) / (b - a)


def rainbow(el):
    h6 = ((THETA / (2 * np.pi) - HUE_PER_MS * el) % 1.0) * 6
    i, f = np.floor(h6).astype(int) % 6, h6 - np.floor(h6)
    one, zero, q = np.ones_like(f), np.zeros_like(f), 1 - f
    table = [(one, f, zero), (q, one, zero), (zero, one, f), (zero, q, one), (f, zero, one), (one, zero, q)]
    rgb = np.zeros((len(f), 3))
    for k, (r, g, b) in enumerate(table):
        m = i == k
        rgb[m] = np.stack([r[m], g[m], b[m]], 1)
    return np.linalg.lstsq(BASIS, rgb, rcond=None)[0] * rainbow_level(el)


RAINBOW_VAL = 20                                 # TRGB_RAINBOW_VAL: the raw LED value eden_view's light passes stand for
FADE_MS = 300                                    # screens cross-fade within one shot
# a close-up press: the key eases down from PRESS_AT, holds, and comes back up. The
# depth is sampled from four renders (0, 1.2, 2.4 and 3.5 mm) and blended between them.
PRESS_AT, PRESS_DOWN, PRESS_HOLD, PRESS_UP = 700, 220, 260, 320
PRESS_HIT = PRESS_AT + PRESS_DOWN // 2           # the switch actuates halfway down
DEPTHS = [(0.0, ""), (1.2, "_d1"), (2.4, "_d2"), (3.5, "_dn")]
TAP_AT, TAP_MS = 1300, 120                       # a key pressed in place: inverted this long
# anim/menu_cascade.c
CASC_MS, CASC_FADE_MS = 756, 152
CASC_DOT_MS, CASC_HALF_MS = CASC_FADE_MS // 3, CASC_FADE_MS * 2 // 3


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def press_depth(t):
    """The key's travel in mm, t ms into a close-up."""
    u = t - PRESS_AT
    if u < 0:
        return 0.0
    if u < PRESS_DOWN:
        return 3.5 * smooth(u / PRESS_DOWN)
    if u < PRESS_DOWN + PRESS_HOLD:
        return 3.5
    return 3.5 * (1 - smooth((u - PRESS_DOWN - PRESS_HOLD) / PRESS_UP))


def duration(s, sim):
    """How long a scene holds on screen, ms (the preview's pacing, not the firmware's)."""
    if s.get("dur"):
        return s["dur"]
    if s["id"] == "E1":
        return 6500
    if s["id"] == "E2":
        return sim.TOTAL - 6500
    if s["id"] == "E3":
        return 2600                              # SA_TAIL_MS
    if s.get("press"):
        return PRESS_AT + PRESS_DOWN + PRESS_HOLD + PRESS_UP + 500
    if s.get("tap"):
        return TAP_AT + 300
    if s["id"] == "F":
        return 3500
    if s.get("sweep") or s.get("cascade"):
        return 2800
    return 2200 if s.get("point") else 2600


def cascade_rows():
    """menu_cascade_rows.h: the PHYSICAL row of each display slot, per half."""
    import re
    t = open(os.path.join(HERE, "..", "..", "qmk_firmware", "keyboards", "polykybd", "anim",
                          "menu_cascade_rows.h"), encoding="utf-8").read()
    rows = {}
    for side in ("LEFT", "RIGHT"):
        body = re.search(r"CASC_ROW_" + side + r"\[40\]\s*=\s*\{(.*?)\};", t, re.S).group(1)
        rows[side[0]] = [int(v, 16) for v in re.findall(r"0x[0-9A-Fa-f]+", body)]
    return rows


def video(layers, story, out, width=640, fps=25):
    sys.path.insert(0, os.path.join(HERE, "..", "..", "PolyKybdHost", "tools"))
    sys.path.insert(0, HERE)
    from fw_anim_sim import FwSim, mp_to_half_idx
    import tutorial_fx as fx
    sim, half_idx = FwSim(), mp_to_half_idx()
    cpu = agx()
    meta = load_story(story)
    if os.environ.get("PK_SCENES"):              # a subset, for a quick check
        meta = [s for s in meta if s["id"] in os.environ["PK_SCENES"].split(",")]
    board, leds, casc_row = fx.Board(), fx.Leds(), cascade_rows()
    Z = np.zeros((OH, OW), np.float32)
    shots = {}

    def shot(name):
        if name not in shots:
            shots[name] = Shot(layers, name)
            sh = shots[name]
            sh.rgb = None
            if all(os.path.exists(os.path.join(layers, p, name + ".exr")) for p in ("w", "c1", "s1")):
                w = exr(os.path.join(layers, "w", name + ".exr"))
                c1, s1 = (exr(os.path.join(layers, p, name + ".exr")) for p in ("c1", "s1"))
                sh.rgb = (w, 2 * c1 - w, 2 * s1 - w)
        return shots[name]

    def eden_keys(t):
        keys = {}
        for mp, hi in half_idx.items():
            if hi is not None:
                b = sim.panel(hi[0], hi[1], int(round(t)))
                if b is not None:
                    keys[mp] = np.asarray(b, np.float32)
        return keys

    led_of = {}
    jobs = os.path.join(layers, "led_jobs.txt")
    if os.path.exists(jobs):
        for line in open(jobs, encoding="utf-8"):
            n_, keys_, _ = line.strip().split("|")
            for ch, mp in enumerate(keys_.split(";")):
                led_of[mp] = (int(n_), ch)

    def led_light(sh, name, rgbs):
        if not hasattr(sh, "led"):
            sh.led = {}
        total = None
        for mp, c in rgbs.items():
            if mp not in sh.led:
                sh.led[mp] = None
                if mp in led_of:
                    f = os.path.join(layers, f"led_{led_of[mp][0]}", name + ".exr")
                    if os.path.exists(f):
                        sh.led[mp] = exr(f)[..., led_of[mp][1]]
            img = sh.led[mp]
            if img is None:
                continue
            add = img[..., None] * (np.asarray(c, np.float32) / RAINBOW_VAL)
            total = add if total is None else total + add
        return total

    def phase_of(sid):
        for p, v in (("C1", 3), ("C2.1", 7), ("C2.2", 10), ("C3", 11), ("C4", 15), ("T", 21)):
            if sid.startswith(p):
                return v
        return 0

    def due(mp, rows):
        """menu_cascade.c due_ms(): when key `mp` appears, ms from the change; 0 = at once."""
        hi = half_idx.get(mp)
        if hi is None or mp not in board.centre:
            return 0
        dr = casc_row[hi[0]][hi[1]]
        if dr == 0 or dr == 0xFF or dr > rows:
            return 0
        x = min(max(board.centre[mp][0], 0), sim.BW)
        return 1 + (CASC_MS * ((dr - 1) * sim.BW + x)) // (rows * sim.BW)

    def cascaded(a, el):
        """One key's cascade frame, el ms after it was due: a dot, half size, then full, fading up."""
        if el < CASC_DOT_MS:
            out = Z.copy()
            out[19:21, 35:37] = 1.0
        elif el < CASC_HALF_MS:
            out = Z.copy()
            h = a[::2, ::2]
            out[10:30, 18:54] = h[:20, :36]
        else:
            out = a
        return out * min(1.0, el / CASC_FADE_MS)

    def light_frame(keys, status, ambient, name, rgbs, extra=None):
        sh = shot(name)
        ex = extra
        if rgbs is not None:
            ll = led_light(sh, name, rgbs)
            if ll is not None:
                ex = ll if ex is None else ex + ll
        return sh.frame(keys, status, ambient, cpu, ex)

    tmp = os.path.join(out + ".frames")
    os.makedirs(tmp, exist_ok=True)
    step, n, prev = 1000 / fps, 0, None
    T = 0.0                                      # the board's own clock
    ripples, sweeps, fired = [], [], set()
    for si, s in enumerate(meta):
        dur = duration(s, sim)
        phase = phase_of(s["id"])
        nxt = meta[si + 1] if si + 1 < len(meta) else None
        # after a close-up press, go back to the press: the board view shows the
        # whole reaction (the ripple, the sweep repainting every key) from its start
        if prev is not None and prev.get("press") and prev.get("_hit") is not None and s["shot"] != "status":
            T = prev["_hit"]
        T0 = T
        if s.get("sweep") and (s["id"], "sweep") not in fired:
            fired.add((s["id"], "sweep"))
            sweeps.append(dict(origin=s["sweep"][0], start=T0, run=s["sweep"][1], scene=s["id"],
                               old=dict(prev["keys_img"]) if prev else {}, new=s["keys_img"]))
        for k in range(int(round(dur / step))):
            t = k * step
            T = T0 + t
            ambient = s["ambient"]
            extra, rgbs = None, None
            if s["id"] in ("E1", "E2"):
                el = t if s["id"] == "E1" else 6500 + t
                keys, status = eden_keys(el), [None, None]
                sh = shot(s["shot"])
                if sh.rgb is not None:
                    c = rainbow(el)
                    extra = sh.rgb[0] * c[0] + sh.rgb[1] * c[1] + sh.rgb[2] * c[2]
            else:
                keys, status = dict(s["keys_img"]), list(s["status_img"])
                if s["id"] == "E3":
                    keys = {}
                    ambient = 0.07 + (0.35 - 0.07) * smooth(t / 2000)
                pressed = bool(s.get("press")) and t >= PRESS_HIT
                if s.get("press") and pressed and (s["id"], "hit") not in fired:
                    fired.add((s["id"], "hit"))
                    s["_hit"] = T0 + PRESS_HIT
                    if s.get("strike"):
                        ripples.append((s["press"], s["_hit"]))
                    if nxt is not None and nxt.get("sweep"):
                        fired.add((nxt["id"], "sweep"))
                        sweeps.append(dict(origin=nxt["sweep"][0], start=s["_hit"], run=nxt["sweep"][1],
                                           scene=s["id"], old=dict(s["keys_img"]), new=nxt["keys_img"]))
                point = s.get("point") if not pressed else None
                if s.get("tap") and t >= TAP_AT:
                    point = None
                if point and not s["id"].startswith("C1") and s["shot"] != "status":
                    j_ = int(t // fx.P["TUT_POINT_PERIOD_MS"])
                    if (s["id"], j_) not in fired:
                        fired.add((s["id"], j_))
                        ripples.append((point, T0 + j_ * fx.P["TUT_POINT_PERIOD_MS"]))
                # a menu change: its keys appear row by row, left to right
                if s.get("cascade"):
                    for mp in list(keys):
                        d = due(mp, s["cascade"])
                        if d:
                            keys[mp] = cascaded(keys[mp], t - d) if t >= d else Z
                elif prev is not None and prev["shot"] == s["shot"] and t < FADE_MS and not s.get("sweep") \
                        and not prev.get("tap"):
                    a = t / FADE_MS
                    for mp in set(keys) | set(prev["keys_img"]):
                        keys[mp] = prev["keys_img"].get(mp, Z) * (1 - a) + keys.get(mp, Z) * a
                    status = [None if x is None and y is None else
                              (x if x is not None else np.zeros((SH, SW), np.float32)) * (1 - a) +
                              (y if y is not None else np.zeros((SH, SW), np.float32)) * a
                              for x, y in zip(prev["status_img"], status)]
                band, shue = None, 0
                for sw in sweeps:
                    el = T - sw["start"]
                    if el < 0:
                        continue
                    if el >= sw["run"]:
                        if sw["scene"] == s["id"]:
                            keys = dict(sw["new"])
                        continue
                    masks, r, dens, bnd = board.sweep(sw["origin"], el, sw["run"])
                    if r is None:
                        continue
                    inside = {mp for mp in board.centre if board.within(sw["origin"], mp, r)}
                    keys = {mp: a for mp, a in sw["new"].items() if mp in inside} | \
                           {mp: a for mp, a in sw["old"].items() if mp not in inside}
                    for mp, m in masks.items():
                        keys[mp] = np.maximum(keys.get(mp, Z), m)
                    band = bnd
                    ox, oy = board.centre[sw["origin"]]
                    shue = fx.K_HUES[(ox * 3 + oy * 5 + phase) % len(fx.K_HUES)]
                sweeps = [sw for sw in sweeps if T - sw["start"] < sw["run"] + 5000]
                ripples = [(o, st) for o, st in ripples if 0 <= T - st < fx.P["TUT_RIPPLE_MS"] or T < st]
                for o, st in ripples:
                    for mp, m in board.ripple(o, T - st).items():
                        keys[mp] = np.maximum(keys.get(mp, Z), m)
                if point in keys:
                    keys[point] = keys[point] * (fx.pulse_level(t) / 255)
                if s.get("tap") and TAP_AT <= t < TAP_AT + TAP_MS:
                    keys[s["tap"]] = 1.0 - keys.get(s["tap"], Z)
                if s["id"] != "E3":
                    rgbs = leds.step(T, step, board, pointed=point, phase=phase, sweep_band=band,
                                     sweep_hue=shue, named=s.get("named") or (), name_hue=fx.K_HUES[0])
            name = s["shot"]
            depth = press_depth(t) if s.get("press") else 0.0
            if depth > 0 and os.path.exists(os.path.join(layers, "base", name + "_dn.exr")):
                levels = [(d, a) for d, a in DEPTHS if os.path.exists(os.path.join(layers, "base", name + a + ".exr"))]
                for (d0, a0), (d1, a1) in zip(levels, levels[1:]):
                    if depth <= d1:
                        f = (depth - d0) / (d1 - d0)
                        A = light_frame(keys, status, ambient, name + a0, rgbs, extra)
                        B = light_frame(keys, status, ambient, name + a1, rgbs, extra) if f > 0.02 else A
                        img = Image.blend(A, B, f)
                        break
            else:
                img = light_frame(keys, status, ambient, name, rgbs, extra)
            img = img.resize((width, int(round(width * img.height / img.width / 2)) * 2), Image.LANCZOS)
            img.save(os.path.join(tmp, f"{n:05d}.png"))
            n += 1
        prev = s
        print(f"scene {s['id']:7s} {s['shot']:9s} {dur:5d} ms  -> {n} frames", flush=True)
    import subprocess
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%05d.png"),
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", out, n, "frames", round(n / fps, 1), "s")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "storyboard":
        storyboard(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "video":                        # video <layers> <story.npz> <out.mp4> [width] [fps]
        video(sys.argv[2], sys.argv[3], sys.argv[4], *(int(v) for v in sys.argv[5:7]))
    else:
        raise SystemExit(f"unknown mode {mode}")
