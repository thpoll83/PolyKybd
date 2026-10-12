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
BLOOM = float(os.environ.get("PK_BLOOM", 0.14))
STATUS_ID = 126
STATUS_GAIN = float(os.environ.get("PK_STATUS_GAIN", 0.3))
STATUS_BLOOM = float(os.environ.get("PK_STATUS_BLOOM", 0.14))
# an OLED pixel is a lit square with a thin dark seam around it: this share of its pitch is lit
PIXEL_FILL = float(os.environ.get("PK_PIXEL_FILL", 0.86))
OW, OH, SW, SH = 72, 40, 128, 64
sys.path.insert(0, HERE)
import keymatch  # noqa: E402
# the cell numbers eden_view.py's map passes wrote: the exported atlas plus every KLE key it left out
LABELS = sorted(keymatch.code_atlas(
    json.load(open(os.path.join(HERE, "textures", "screens_layer0.json"), encoding="utf-8")),
    os.path.join(HERE, "..", "..", "PolyKybdHost", "polyhost", "res", "polykybd-split72.json")))


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


def pixel_grid(u, v, status):
    """Per map pixel: how much of it an OLED pixel's lit square covers, so the seams
    between the panel's pixels show where the camera resolves them (a close-up) and
    average out where it cannot (a wide shot, which would otherwise moire). Normalised
    to a mean of 1, so the grid does not change a screen's overall brightness."""
    out = np.ones(u.shape, np.float32)
    for coord, n_key, n_status, axis in ((u, OW, SW, 1), (v, OH, SH, 0)):
        p = coord * np.where(status, n_status, n_key)
        f = p - np.floor(p)
        fp = np.hypot(*np.gradient(p))                # OLED pixels per map pixel
        sharp = np.clip((PIXEL_FILL / 2 - np.abs(f - 0.5)) / np.maximum(fp, 1e-3) + 0.5, 0, 1)
        w = np.clip((fp - 0.25) / 0.5, 0, 1)          # unresolved: the average, no pattern
        out *= (sharp * (1 - w) + PIXEL_FILL * w) / PIXEL_FILL
    return out


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
        self.cell = np.where(seen, np.floor(idm[..., 0] / b * 128), -1).astype(np.int16)
        u = uv[..., 0] / np.maximum(uv[..., 2], 1e-6)
        v = uv[..., 1] / np.maximum(uv[..., 2], 1e-6)
        # int16 indices: at 2048 px the maps are 4096 wide, and int64 tables cost 75 MB each
        self.kx, self.ky = (np.clip(u * OW, 0, OW - 1).astype(np.int16), np.clip(v * OH, 0, OH - 1).astype(np.int16))
        self.sx, self.sy = (np.clip(u * SW, 0, SW - 1).astype(np.int16), np.clip(v * SH, 0, SH - 1).astype(np.int16))
        self.trans = np.where(seen, uv[..., 2], 0.0).astype(np.float32)
        self.trans *= pixel_grid(u, v, self.cell >= STATUS_ID)
        del uv, idm, u, v, b, seen
        # per cell, the pixels that show it
        # (int32: at 2048 px a 1.7x menu shot's int64 indices alone would cost ~450 MB)
        self.where = {c: tuple(i.astype(np.int32) for i in np.nonzero(self.cell == c))
                      for c in np.unique(self.cell) if c >= 0}
        ys, xs = np.nonzero(self.cell >= 0)          # every key and status pixel, for a pan
        self.keys_box = (xs.min() / 2, ys.min() / 2, xs.max() / 2, ys.max() / 2) if len(ys) else None

    def pan_box(self, u, room=1.12):
        """A 16:9 crop as tall as the key rows (plus `room`), u = 0 at the left end of
        the board, 1 at the right end."""
        x0, y0, x1, y1 = self.keys_box
        h = min(self.H, (y1 - y0) * room)
        w = min(self.W, h * self.W / self.H)
        h = w * self.H / self.W
        cy = min(max((y0 + y1) / 2, h / 2), self.H - h / 2)
        lo, hi = max(0, x0 - 0.04 * w), min(self.W, x1 + 0.04 * w) - w
        x = lo + (max(hi, lo) - lo) * u
        return (int(round(x)), int(round(cy - h / 2)), int(round(x + w)), int(round(cy + h / 2)))

    def screens(self, keys, status):
        """keys {label: (40, 72)}, status [left, right] (64, 128) -> (keycaps, status panels)
        lit at image size."""
        lit = np.zeros(self.cell.shape, np.float32)
        slit = np.zeros(self.cell.shape, np.float32)
        for c, (yy, xx) in self.where.items():
            if c >= STATUS_ID:
                s = status[c - STATUS_ID]
                if s is not None:
                    slit[yy, xx] = s[self.sy[yy, xx], self.sx[yy, xx]]
            elif c < len(LABELS) and LABELS[c] in keys:
                lit[yy, xx] = keys[LABELS[c]][self.ky[yy, xx], self.kx[yy, xx]]
        down = lambda a: (a * self.trans).reshape(self.H, 2, self.W, 2).mean((1, 3))
        return down(lit), down(slit)

    def frame(self, keys, status, ambient, cpu, extra=None):
        lin = self.base + self.ambient * ambient
        if extra is not None:
            lin = lin + extra
        scr, sscr = self.screens(keys, status)
        r = max(1, self.W // 320)
        lin = lin + (scr + BLOOM * blur(scr, r))[..., None] * LIT_TINT * SCREEN
        # the status panels: an OLED behind no glass, so far less glow than a keycap
        lin = lin + (sscr + STATUS_BLOOM * blur(sscr, r))[..., None] * LIT_TINT * SCREEN * STATUS_GAIN
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


CHAPTERS = ["Eden, the lit key and the board reveal", "Shift", "The languages",
            "The Lang menu", "The emoji menu", "The Intl accents, finale, idle"]
PREFIX = [("E", 0), ("C1", 0), ("C2", 1), ("C3", 1), ("C4", 2), ("T1", 3), ("T2", 3), ("T3", 3),
          ("T4", 4), ("T5", 4), ("T6", 4), ("I", 5), ("F", 5), ("Z", 5)]


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
PRESS_RELEASE = PRESS_HIT + PRESS_HOLD + (PRESS_DOWN + PRESS_UP) // 2   # the display turns back
REWIND_PRE = 200                                 # the board view after a close-up starts this long before the press
# a key pressed in place (no close-up): the scene ends just after the hit and the next
# one, which shows what the press did, carries the release
INPLACE_TAIL = 80                                # >= 2 frames past the hit, or no frame lands on it
IDLE_DIM = 0.2                                   # what the keycaps keep once idle has dimmed them
SHOT_LIGHT = {s["name"]: s.get("light", s["name"])  # a press variant uses its parent's LED renders
              for s in json.load(open(os.path.join(HERE, "tutorial_shots.json"), encoding="utf-8"))}
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


def inplace(s):
    """A press seen from the scene's own camera, not a close-up."""
    return bool(s.get("press")) and not s["shot"].startswith("k_")


def duration(s, sim):
    """How long a scene holds on screen, ms (the preview's pacing, not the firmware's)."""
    if s.get("dur"):
        return s["dur"]
    if inplace(s):                               # a held key ends fully down
        return PRESS_AT + PRESS_DOWN + 100 if s.get("hold") else PRESS_HIT + INPLACE_TAIL
    if s["id"] == "E1":
        return 6500
    if s["id"] == "E2":
        return sim.TOTAL - 6500
    if s["id"] == "E3":
        return 2600                              # SA_TAIL_MS
    if s.get("press"):
        return PRESS_AT + PRESS_DOWN + PRESS_HOLD + PRESS_UP + 500
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
    """The whole video. With PK_JOBS > 1 (default: one per core, at most 16) the frames
    are split into that many runs of video_part(), one process each, and the pieces are
    joined without re-encoding."""
    jobs = int(os.environ.get("PK_JOBS", min(os.cpu_count() or 1, 16)))
    if os.environ.get("PK_FRAMES"):              # one part of a parallel run
        lo, hi = (int(v) for v in os.environ["PK_FRAMES"].split(":"))
        return video_part(layers, story, out, width, fps, lo, hi, threads=2)
    silent = out[:-4] + ".silent.mp4"
    if jobs <= 1:
        video_part(layers, story, silent, width, fps)
    else:
        video_parallel(layers, story, silent, width, fps, jobs)
    # the soundtrack: the same scene walk with no frames drawn, for the events' times
    events = []
    total = video_part(layers, story, os.devnull, width, fps, lo=1 << 30, events=events)
    import subprocess
    import tutorial_audio
    wav = out[:-4] + ".wav"
    tutorial_audio.write(events, total * 1000 / fps, wav)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(silent)
    print("wrote", out, "with sound,", total, "frames", round(total / fps, 1), "s")


def video_parallel(layers, story, out, width, fps, jobs):
    sys.path.insert(0, os.path.join(HERE, "..", "..", "PolyKybdHost", "tools"))
    from fw_anim_sim import FwSim
    import subprocess
    sim, meta = FwSim(), load_story(story)
    if os.environ.get("PK_SCENES"):
        meta = [s for s in meta if s["id"] in os.environ["PK_SCENES"].split(",")]
    total = sum(int(round(duration(s, sim) / (1000 / fps))) for s in meta)
    cuts = [total * i // jobs for i in range(jobs + 1)]
    parts = [f"{out}.part{i:02d}.mp4" for i in range(jobs)]
    print(f"{total} frames in {jobs} parts", flush=True)
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), "video", layers, story, part, str(width), str(fps)],
                              env=dict(os.environ, PK_FRAMES=f"{lo}:{hi}"))
             for part, lo, hi in zip(parts, cuts, cuts[1:])]
    if any(p.wait() != 0 for p in procs):
        raise SystemExit("a part failed: " + ", ".join(str(p.returncode) for p in procs))
    lst = out + ".parts.txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    "-movflags", "+faststart", out], check=True)
    for p in parts + [lst]:
        os.remove(p)


def encoder(out, img, fps, threads):
    import subprocess
    return subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{img.width}x{img.height}", "-r", str(fps), "-i", "-",
                             "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p",
                             "-threads", str(threads), "-movflags", "+faststart", out], stdin=subprocess.PIPE)


def video_part(layers, story, out, width, fps, lo=0, hi=-1, threads=0, events=None):
    """Frames lo..hi-1 of the video (hi = -1: to the end). Every frame before `lo` is
    still stepped through, cheaply: the clock, the sweeps, the ripples and the LED fades
    carry state from frame to frame, so a part must replay them to start in the right place.
    events: a list to fill with what the soundtrack follows, at VIDEO time (ms from the first
    frame; the board's own clock rewinds after a close-up): ("scene", ms, id, dur),
    ("hit", ms, key, shot), ("sweep", ms, run, scene), ("cascade", ms, rows, named),
    ("appear", ms, key): a name key's legend arriving in its cascade."""
    ev = events if events is not None else []
    sys.path.insert(0, os.path.join(HERE, "..", "..", "PolyKybdHost", "tools"))
    sys.path.insert(0, HERE)
    from fw_anim_sim import FwSim, mp_to_half_idx
    import tutorial_fx as fx
    sim, half_idx = FwSim(), mp_to_half_idx()
    idle_sim = FwSim()
    idle_sim.idle = True                         # the Eden screensaver (sa_render_idle_frame)
    cpu = agx()
    meta = load_story(story)
    if os.environ.get("PK_SCENES"):              # a subset, for a quick check
        meta = [s for s in meta if s["id"] in os.environ["PK_SCENES"].split(",")]
    # the pan groups: each scene's start within its group's one long track
    pan_at, pan_span, acc = {}, {}, 0
    for s_ in meta:
        if s_.get("pan"):
            g_ = s_["pan"][0]
            if g_ not in pan_span:
                pan_span[g_] = [acc, 0]
            pan_at[s_["id"]] = acc
            pan_span[g_][1] = acc + duration(s_, sim) - pan_span[g_][0]
        acc += duration(s_, sim)
    board, leds, casc_row = fx.Board(), fx.Leds(), cascade_rows()
    stars = fx.Stars(sim)
    Z = np.zeros((OH, OW), np.float32)
    from collections import OrderedDict
    shots = OrderedDict()                        # a few cameras at a time: a 2048 px shot holds ~1 GB
    keep = int(os.environ.get("PK_SHOT_CACHE", 5))

    def shot(name):
        if name in shots:
            shots.move_to_end(name)
        else:
            while len(shots) >= keep:
                shots.popitem(last=False)
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
                    f = os.path.join(layers, f"led_{led_of[mp][0]}", SHOT_LIGHT.get(name, name) + ".exr")
                    if os.path.exists(f):
                        img = exr(f)[..., led_of[mp][1]]
                        if img.shape != sh.base.shape[:2]:   # rendered at a lower width: soft light
                            img = np.asarray(Image.fromarray(img.astype(np.float32), "F").resize(
                                (sh.base.shape[1], sh.base.shape[0]), Image.BILINEAR))
                        sh.led[mp] = img
            img = sh.led[mp]
            if img is None:
                continue
            add = img[..., None] * (np.asarray(c, np.float32) / RAINBOW_VAL)
            total = add if total is None else total + add
        return total

    def phase_of(sid):
        for p, v in (("C1", 3), ("C2.1", 7), ("C2.2", 10), ("C3", 11), ("C4", 15), ("T", 21), ("I", 21),
                     ("F", 21), ("Z", 21)):
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

    def press_levels(name, key):
        """(depth mm, shot) renders of `key` going down: a close-up's own depth variants,
        or the in-place variant <shot>_p<r>_<c>_<depth> of a wide shot"""
        if name.startswith("k_"):
            cand = [(d, name + a) for d, a in DEPTHS]
        else:
            cand = [(0.0, name)] + [(d, f"{name}_p{key.replace(',', '_')}{a}") for d, a in DEPTHS[1:]]
        return [(d, n) for d, n in cand if os.path.exists(os.path.join(layers, "base", n + ".exr"))]

    def light_frame(keys, status, ambient, name, rgbs, extra=None):
        sh = shot(name)
        ex = extra
        if rgbs is not None:
            ll = led_light(sh, name, rgbs)
            if ll is not None:
                ex = ll if ex is None else ex + ll
        return sh.frame(keys, status, ambient, cpu, ex)

    # frames go straight into ffmpeg: at 2048 px a PNG per frame would need ~18 GB of disk
    import subprocess
    enc, size = None, [None]
    out_h = int(round(width * 9 / 16 / 2)) * 2   # every shot is 16:9; a pan crop must not change the size

    def title_card(text, t, dur, fade=700):
        """White text on black in the middle, fading in and out."""
        w, h = width, out_h
        img = Image.new("RGB", (w, h), (0, 0, 0))
        d = ImageDraw.Draw(img)
        f = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf", max(12, w // 16))
        box = d.textbbox((0, 0), text, font=f)
        a = min(1.0, t / fade, (dur - t) / fade) if dur > 2 * fade else 1.0
        v = int(235 * smooth(a))
        d.text(((w - box[2] - box[0]) / 2, (h - box[3] - box[1]) / 2), text, font=f, fill=(v, v, v))
        return img
    step, n, prev = 1000 / fps, 0, None
    T = 0.0                                      # the board's own clock
    ripples, sweeps, fired = [], [], set()
    for si, s in enumerate(meta):
        dur = duration(s, sim)
        phase = phase_of(s["id"])
        nxt = meta[si + 1] if si + 1 < len(meta) else None
        # after a close-up press, go back to the press: the board view shows the
        # whole reaction (the ripple, the sweep repainting every key) from its start
        before, hit_at, release_at = None, None, None
        # an in-place press carries on into this scene: the key comes back up here
        carry = (prev["press"], duration(prev, sim)) if (prev is not None and inplace(prev) and not prev.get("hold")
                                                         and prev["shot"] == s["shot"]) else None
        if prev is not None and prev.get("press") and prev.get("_hit") is not None and s["shot"] != "status" \
                and prev["shot"].startswith("k_"):
            # back to just before the press: the old legends until the key lands, then the change
            T = prev["_hit"] - REWIND_PRE
            before, hit_at = prev["keys_img"], prev["_hit"]
            release_at = None if prev.get("hold") else prev["_hit"] - PRESS_HIT + PRESS_RELEASE
        T0 = T
        ev.append(("scene", n * step, s["id"], dur))
        if s.get("cascade"):
            ev.append(("cascade", n * step, s["cascade"], bool(s.get("named"))))
            for mp in s.get("named") or ():        # each name key's legend arriving
                ev.append(("appear", n * step + due(mp, s["cascade"]), mp))
        if s.get("sweep") and (s["id"], "sweep") not in fired:
            fired.add((s["id"], "sweep"))
            ev.append(("sweep", n * step, s["sweep"][1], s["id"]))
            sweeps.append(dict(origin=s["sweep"][0], start=T0, run=s["sweep"][1], scene=s["id"],
                               old=dict(prev["keys_img"]) if prev else {}, new=s["keys_img"]))
        for k in range(int(round(dur / step))):
            t = k * step
            T = T0 + t
            todo = n >= lo and (hi < 0 or n < hi)
            ambient = s["ambient"]
            extra, rgbs = None, None
            if s["id"] in ("E1", "E2"):
                if not todo:                       # Eden carries no state: nothing to replay
                    n += 1
                    continue
                el = t if s["id"] == "E1" else 6500 + t
                keys, status = eden_keys(el), [None, None]
                for mp, m in stars.keys(el).items():
                    keys[mp] = np.maximum(keys.get(mp, Z), m)
                sh = shot(s["shot"])
                if sh.rgb is not None:
                    c = rainbow(el)
                    extra = sh.rgb[0] * c[0] + sh.rgb[1] * c[1] + sh.rgb[2] * c[2]
            else:
                keys, status = dict(s["keys_img"]), list(s["status_img"])
                if s.get("saver") and todo:        # idle: the comet field, the status panels off
                    keys = {}
                    for mp, hx in half_idx.items():
                        b = idle_sim.panel(hx[0], hx[1], int(round(t))) if hx is not None else None
                        if b is not None:
                            keys[mp] = np.asarray(b, np.float32)
                    status = [None, None]
                if s["id"] in ("E3", "E3s"):       # the welcome tail: the stars still falling
                    tail = t + (1400 if s["id"] == "E3s" else 0)
                    keys = stars.keys(sim.TOTAL + tail)
                    ambient = 0.07 + (0.35 - 0.07) * smooth(tail / 2600)
                pressed = bool(s.get("press")) and t >= PRESS_HIT
                if s.get("press") and pressed and (s["id"], "hit") not in fired:
                    fired.add((s["id"], "hit"))
                    s["_hit"] = T0 + PRESS_HIT
                    ev.append(("hit", n * step, s["press"], s["shot"]))
                    if s.get("strike"):
                        ripples.append((s["press"], s["_hit"]))
                    if nxt is not None and nxt.get("sweep"):
                        fired.add((nxt["id"], "sweep"))
                        ev.append(("sweep", n * step, nxt["sweep"][1], nxt["id"]))
                        sweeps.append(dict(origin=nxt["sweep"][0], start=s["_hit"], run=nxt["sweep"][1],
                                           scene=s["id"], old=dict(s["keys_img"]), new=nxt["keys_img"]))
                point = s.get("point") if not pressed else None
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
                        and not prev.get("press") and prev["id"] not in ("E1", "E2") and not s.get("saver"):
                    a = t / FADE_MS
                    for mp in set(keys) | set(prev["keys_img"]):
                        keys[mp] = prev["keys_img"].get(mp, Z) * (1 - a) + keys.get(mp, Z) * a
                    status = [None if x is None and y is None else
                              (x if x is not None else np.zeros((SH, SW), np.float32)) * (1 - a) +
                              (y if y is not None else np.zeros((SH, SW), np.float32)) * a
                              for x, y in zip(prev["status_img"], status)]
                if before is not None and T < hit_at:
                    keys = dict(before)
                if s.get("fadein"):
                    f_ = min(1.0, t / s["fadein"])
                    keys = {mp: a * f_ for mp, a in keys.items()}
                # a pressed key's display inverts while it is down (the firmware's key-down
                # feedback); a held key (Shift, Intl, the armed Ctrl) stays inverted
                inv = set(s.get("held") or ())
                if s.get("press") and t >= PRESS_HIT and (s.get("hold") or t < PRESS_RELEASE):
                    inv.add(s["press"])
                if carry and carry[1] + t < PRESS_RELEASE:
                    inv.add(carry[0])
                if hit_at is not None and T >= hit_at and (release_at is None or T < release_at):
                    inv.add(prev["press"])
                if before is not None and T < hit_at:
                    inv -= {prev["press"]}
                for mp in inv:
                    if mp in board.centre:
                        keys[mp] = 1.0 - keys.get(mp, Z)
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
                if s["id"] not in ("E3", "E3s") and not s.get("saver"):
                    # a name's key lights with its legend: the cascade brings both
                    named = [mp for mp in s.get("named") or ()
                             if not s.get("cascade") or t >= due(mp, s["cascade"])]
                    rgbs = leds.step(T, step, board, pointed=point, phase=phase, sweep_band=band,
                                     sweep_hue=shue, named=named, name_hue=fx.K_HUES[0],
                                     glow=[tuple(g) for g in s.get("glow") or ()])
                if s.get("dim"):                   # idle engages: the keycaps, the panels and the LEDs dim
                    f_ = 1.0 - (1.0 - IDLE_DIM) * smooth(t / s["dim"])
                    keys = {mp: a * f_ for mp, a in keys.items()}
                    status = [x * f_ if x is not None else None for x in status]
                    if rgbs:
                        rgbs = {mp: c * f_ for mp, c in rgbs.items()}
            if not todo:
                n += 1
                continue
            if s.get("title"):                     # the closing card: no board at all
                img = title_card(s["title"], t, dur)
                if enc is None:
                    enc = encoder(out, img, fps, threads)
                enc.stdin.write(img.convert("RGB").tobytes())
                n += 1
                continue
            name, pkey, depth = s["shot"], s.get("press"), 0.0
            if pkey:
                depth = press_depth(min(t, PRESS_AT + PRESS_DOWN + PRESS_HOLD // 2)) if s.get("hold") else press_depth(t)
            elif carry:
                pkey, depth = carry[0], press_depth(carry[1] + t)
            levels = press_levels(name, pkey) if depth > 0 else []
            if len(levels) > 1:
                depth = min(depth, levels[-1][0])
                for (d0, a0), (d1, a1) in zip(levels, levels[1:]):
                    if depth <= d1:
                        f = (depth - d0) / (d1 - d0)
                        A = light_frame(keys, status, ambient, a0, rgbs, extra)
                        B = light_frame(keys, status, ambient, a1, rgbs, extra) if f > 0.02 else A
                        img = Image.blend(A, B, f)
                        break
            else:
                img = light_frame(keys, status, ambient, name, rgbs, extra)
            if s.get("pan"):                       # one slow track over the group, rows filling the frame
                g_, a_, b_ = s["pan"]
                g0, glen = pan_span[g_]
                u = smooth(min(max((pan_at[s["id"]] + t - g0) / glen, 0), 1))
                img = img.crop(shot(s["shot"]).pan_box(a_ + (b_ - a_) * u))
            img = img.resize((width, out_h), Image.LANCZOS)
            if s.get("fadeout") and t > dur - s["fadeout"]:
                img = Image.eval(img, lambda v, f_=smooth((dur - t) / s["fadeout"]): int(v * f_))
            size[0] = img.size
            if enc is None:
                enc = encoder(out, img, fps, threads)
            enc.stdin.write(img.convert("RGB").tobytes())
            n += 1
        prev = s
        if enc is not None:
            print(f"scene {s['id']:7s} {s['shot']:9s} {dur:5d} ms  -> {n} frames", flush=True)
        if hi >= 0 and n >= hi:
            break
    if enc is None:                              # nothing in range: an events-only pass
        return n
    enc.stdin.close()
    if enc.wait() != 0:
        raise SystemExit(f"ffmpeg failed ({enc.returncode})")
    done = (n if hi < 0 else min(n, hi)) - lo
    print("wrote", out, done, "frames", round(done / fps, 1), "s")
    return n


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "storyboard":
        storyboard(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "video":                        # video <layers> <story.npz> <out.mp4> [width] [fps]
        video(sys.argv[2], sys.argv[3], sys.argv[4], *(int(v) for v in sys.argv[5:7]))
    else:
        raise SystemExit(f"unknown mode {mode}")
