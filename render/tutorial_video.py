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
    for s in meta:
        if s["shot"] not in shots:
            shots[s["shot"]] = Shot(layers, s["shot"])
        img = shots[s["shot"]].frame(s["keys_img"], s["status_img"], s["ambient"], cpu)
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


PULSE_MS, PULSE_FLOOR = 1400, 24 / 255          # base/tutorial_plan.h TUT_PULSE_*
FADE_MS = 300                                    # screens cross-fade within one shot
PRESS_AT, PRESS_MS = 450, 350                    # a close-up: the key goes down here, this long


def duration(s, sim):
    """How long a scene holds on screen, ms (the preview's pacing, not the firmware's)."""
    if s["id"] == "E1":
        return 6500
    if s["id"] == "E2":
        return sim.TOTAL - 6500
    if s["id"] == "E3":
        return 2600                              # SA_TAIL_MS
    if s.get("press"):
        return 1400
    if s["id"].startswith("C4"):
        return 3000
    if s["id"] == "F":
        return 3500
    return 2200 if s.get("point") else 2400


def video(layers, story, out, width=320, fps=25):
    sys.path.insert(0, os.path.join(HERE, "..", "..", "PolyKybdHost", "tools"))
    from fw_anim_sim import FwSim, mp_to_half_idx
    sim, half_idx = FwSim(), mp_to_half_idx()
    cpu = agx()
    meta = load_story(story)
    if os.environ.get("PK_SCENES"):              # a subset, for a quick check
        meta = [s for s in meta if s["id"] in os.environ["PK_SCENES"].split(",")]
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

    tmp = os.path.join(out + ".frames")
    os.makedirs(tmp, exist_ok=True)
    step, n, prev = 1000 / fps, 0, None
    t0 = 0.0                                     # story time at the start of this scene
    for s in meta:
        dur = duration(s, sim)
        for k in range(int(round(dur / step))):
            t = k * step
            name = s["shot"]
            if s.get("press") and PRESS_AT <= t < PRESS_AT + PRESS_MS and \
                    os.path.exists(os.path.join(layers, "uv", name + "_dn.exr")):
                name += "_dn"
            sh = shot(name)
            ambient = s["ambient"]
            extra = None
            if s["id"] in ("E1", "E2"):
                el = t if s["id"] == "E1" else 6500 + t
                keys, status = eden_keys(el), [None, None]
                if sh.rgb is not None:
                    c = rainbow(el)
                    extra = sh.rgb[0] * c[0] + sh.rgb[1] * c[1] + sh.rgb[2] * c[2]
            else:
                keys, status = dict(s["keys_img"]), list(s["status_img"])
                if s["id"] == "E3":                # Eden's tail; the room light comes up
                    keys = eden_keys(sim.INTRO + sim.HOLD + t)
                    ambient = 0.07 + (0.35 - 0.07) * min(1.0, t / 2000)
                if s.get("point") in keys and not (s.get("press") and t >= PRESS_AT):
                    lv = PULSE_FLOOR + (1 - PULSE_FLOOR) * (0.5 - 0.5 * np.cos(2 * np.pi * t / PULSE_MS))
                    keys[s["point"]] = keys[s["point"]] * lv
                if prev is not None and prev["shot"] == s["shot"] and t < FADE_MS:
                    a = t / FADE_MS
                    for mp in set(keys) | set(prev["keys_img"]):
                        z = np.zeros((OH, OW), np.float32)
                        keys[mp] = prev["keys_img"].get(mp, z) * (1 - a) + keys.get(mp, z) * a
                    status = [None if x is None and y is None else
                              (x if x is not None else np.zeros((SH, SW), np.float32)) * (1 - a) +
                              (y if y is not None else np.zeros((SH, SW), np.float32)) * a
                              for x, y in zip(prev["status_img"], status)]
            img = sh.frame(keys, status, ambient, cpu, extra)
            img = img.resize((width, int(round(width * img.height / img.width / 2)) * 2), Image.LANCZOS)
            img.save(os.path.join(tmp, f"{n:05d}.png"))
            n += 1
        t0 += dur
        prev = s
        print(f"scene {s['id']:7s} {s['shot']:9s} {dur:5d} ms  -> {n} frames", flush=True)
    import subprocess
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%05d.png"),
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", out, n, "frames", round(t0 / 1000, 1), "s")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "storyboard":
        storyboard(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "video":                        # video <layers> <story.npz> <out.mp4> [width] [fps]
        video(sys.argv[2], sys.argv[3], sys.argv[4], *(int(v) for v in sys.argv[5:7]))
    else:
        raise SystemExit(f"unknown mode {mode}")
