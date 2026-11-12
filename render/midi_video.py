"""The MIDI layer video: both halves from above at night, playing Für Elise.

    <blender dir>/4.1/python/bin/python3.11 render/midi_video.py <layer dir> <out.mp4|out.wav|out.png> [fps]

<layer dir> holds eden_view.py's layers (base, ambient, w, c1, s1, uv, id), rendered
with the Eden video's settings (README, "The Eden intro video"). Run it with Blender's
bundled Python (OpenImageIO, PyOpenColorIO, numpy, Pillow).

- The keycap screens show the MIDI layer `_ML`: textures/screens_layer8.png and
  status_{left,right}_l8.png from export_screens.py. A key that is down shows its
  screen inverted, as the firmware draws a key event.
- The music is the opening (A section, played twice) of Beethoven's Für Elise, right
  hand only: every note of it is on a key of the MIDI layer at the start octave
  (C4..F5, with D#5 and G#4 on the black-key row), so each sound in the video is a key
  that goes down in the picture. The sound is a simple additive piano (partials with
  string inharmonicity and per-partial decay, two detuned strings, a hammer click and
  a damper on release) with a short reverb, plus a quiet switch click from
  audio/keys for every press.
- The backlight is the Eden video's CYCLE_LEFT_RIGHT rainbow at PK_RAINBOW (default
  0.5) of its level.

With an `.wav` output only the soundtrack is written; with `.png`, the stills at
PK_TIMES (ms). PK_ASPECT and PK_CROP_CY crop the frame as in eden_video.py; PK_WIDTH
scales it down; PK_START / PK_END (s) cut a part, for the GIF.
"""
import atexit
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
SR = 48000
env = os.environ.get

# --- the score -----------------------------------------------------------------------
# Für Elise, bars 1..8 with both endings, right hand. Durations in sixteenths, "r" a rest.
PICKUP = [("E5", 1), ("D#5", 1)]
BARS_1_7 = [
    ("E5", 1), ("D#5", 1), ("E5", 1), ("B4", 1), ("D5", 1), ("C5", 1),
    ("A4", 2), ("r", 1), ("C4", 1), ("E4", 1), ("A4", 1),
    ("B4", 2), ("r", 1), ("E4", 1), ("G#4", 1), ("B4", 1),
    ("C5", 2), ("r", 1), ("E4", 1), ("E5", 1), ("D#5", 1),
    ("E5", 1), ("D#5", 1), ("E5", 1), ("B4", 1), ("D5", 1), ("C5", 1),
    ("A4", 2), ("r", 1), ("C4", 1), ("E4", 1), ("A4", 1),
    ("B4", 2), ("r", 1), ("E4", 1), ("C5", 1), ("B4", 1),
]
ENDING_1 = [("A4", 2), ("r", 2), ("E5", 1), ("D#5", 1)]       # leads back to bar 1
ENDING_2 = [("A4", 6)]
SCORE = PICKUP + BARS_1_7 + ENDING_1 + BARS_1_7 + ENDING_2
SIXTEENTH = float(env("PK_SIXTEENTH", 0.19))                 # s
INTRO, OUTRO = 2.2, 2.4                                       # s of stillness around the music
# First the player presses OCT 3 (MI_OC2, left bottom row): the keys then play, and
# their legends name, one octave lower (C3..F4). PK_OCT_PRESS=0 leaves the octave alone.
OCT_KEY, OCT_AT, OCT_LEN = "4,3", 0.7, 0.25
OCT_SHIFT = -12 if env("PK_OCT_PRESS", "1") != "0" else 0

# the MIDI layer's note keys (split72 _ML, matrix "row,col") at the start octave
NOTE_KEY = {
    "C4": "2,1", "C#4": "1,2", "D4": "2,2", "D#4": "1,3", "E4": "2,3", "F4": "2,4",
    "F#4": "1,5", "G4": "2,5", "G#4": "6,2", "A4": "7,2", "A#4": "6,3", "B4": "7,3",
    "C5": "7,4", "C#5": "6,5", "D5": "7,5", "D#5": "6,6", "E5": "7,6", "F5": "7,7",
}
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_number(name):
    return NAMES.index(name[:-1]) + 12 * (int(name[-1]) + 1)


def events():
    """(note, start s, length s): every note of SCORE, with the last bar slowing down."""
    out, t = [], INTRO
    n_last = len(ENDING_2)
    for i, (note, d) in enumerate(SCORE):
        # a ritardando over the last two bars: up to 1.6 times slower
        left = sum(dd for _, dd in SCORE[i:])
        slow = 1.0 + 0.6 * max(0.0, 1.0 - left / 14.0) if i >= len(SCORE) - 12 - n_last else 1.0
        length = d * SIXTEENTH * slow
        if note != "r":
            out.append((note, t, length))
        t += length
    return out, t + OUTRO


EVENTS, TOTAL = events()


def presses():
    """(key, down s, up s) of every key press: the octave key, then each note's key for
    80% of the note (at least 90 ms), so a repeated note shows the key come up between."""
    out = [(OCT_KEY, OCT_AT, OCT_AT + OCT_LEN)] if OCT_SHIFT else []
    return out + [(NOTE_KEY[n], s, s + max(0.09, 0.8 * d)) for n, s, d in EVENTS]


PRESSES = presses()


def held(t):
    """The keys down at time t."""
    return {k for k, a, b in PRESSES if a <= t < b}


def depths(t):
    """How far down each pressed key is, 0..1: 30 ms down, held, 50 ms back up."""
    out = {}
    for key, s, up_at in PRESSES:
        if s - 0.03 <= t < up_at + 0.05:
            x = min(1.0, (t - (s - 0.03)) / 0.03, (up_at + 0.05 - t) / 0.05)
            out[key] = max(out.get(key, 0.0), x)
    return out


def hull(p):
    """Indices of the convex hull of 2D points p (monotone chain)."""
    idx = sorted(range(len(p)), key=lambda i: (p[i][0], p[i][1]))

    def cross(o, a, b):
        return (p[a][0] - p[o][0]) * (p[b][1] - p[o][1]) - (p[a][1] - p[o][1]) * (p[b][0] - p[o][0])
    lo, hi = [], []
    for i in idx:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], i) <= 0:
            lo.pop()
        lo.append(i)
    for i in reversed(idx):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], i) <= 0:
            hi.pop()
        hi.append(i)
    return lo[:-1] + hi[:-1]


# --- the sound -----------------------------------------------------------------------
def piano_note(f0, length, vel=0.55, rng=None):
    """One note: additive partials with stiffness, per-partial decay, two strings."""
    tail = 1.2
    n = int((length + tail) * SR)
    t = np.arange(n) / SR
    B = 0.00035 * (f0 / 261.6) ** 0.5                 # inharmonicity, higher up the scale
    sig = np.zeros(n)
    for k in range(1, 18):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 11000:
            break
        amp = (vel ** (0.5 + 0.12 * k)) / k ** 1.15
        tau = 2.6 * (261.6 / f0) ** 0.35 / (1 + 0.45 * (k - 1))
        env_k = np.exp(-t / tau) * 0.75 + np.exp(-t / (tau * 0.18)) * 0.25
        for det in (-0.7, 0.7):                       # two strings, +-0.7 cent
            ph = rng.uniform(0, 2 * math.pi)
            sig += 0.5 * amp * env_k * np.sin(2 * math.pi * fk * 2 ** (det / 1200) * t + ph)
    att = np.minimum(1.0, t / 0.003)
    damp = np.where(t < length, 1.0, np.exp(-(t - length) / 0.28))   # the damper, softened by pedal
    hammer = rng.standard_normal(n) * np.exp(-t / 0.004) * 0.05 * vel
    return (sig * att + hammer) * damp


def felt_note(f0, length, vel=0.4, rng=None):
    """A felt piano: the hammer wrapped in felt, so few and quickly fading upper partials,
    a 12 ms attack, no hammer click and a long, quiet tail."""
    n = int((length + 1.8) * SR)
    t = np.arange(n) / SR
    B = 0.00025 * (f0 / 261.6) ** 0.5
    sig = np.zeros(n)
    for k in range(1, 9):
        fk = k * f0 * math.sqrt(1 + B * k * k)
        if fk > 6000:
            break
        amp = 0.62 ** (k - 1) / k ** 0.6
        tau = 3.2 * (261.6 / f0) ** 0.3 / (1 + 0.9 * (k - 1))
        env_k = np.exp(-t / tau)
        for det in (-0.5, 0.5):
            sig += 0.5 * amp * env_k * np.sin(2 * math.pi * fk * 2 ** (det / 1200) * t + rng.uniform(0, 2 * math.pi))
    att = 1 - np.exp(-t / 0.012)
    damp = np.where(t < length, 1.0, np.exp(-(t - length) / 0.45))
    return sig * att * damp * vel


def epiano_note(f0, length, vel=0.5, rng=None):
    """An electric piano (tine and tone bar): a sine with a short, quiet 1:1 FM bark at
    the start, a bell partial at 14x that dies in 40 ms, and a slow tremolo-free decay."""
    n = int((length + 1.4) * SR)
    t = np.arange(n) / SR
    index = 1.3 * vel * np.exp(-t / 0.18)                  # brightness falls quickly
    body = np.sin(2 * math.pi * f0 * t + index * np.sin(2 * math.pi * f0 * t))
    bell = 0.12 * np.sin(2 * math.pi * f0 * 14.0 * t) * np.exp(-t / 0.04)
    env_ = np.exp(-t / (2.4 * (261.6 / f0) ** 0.3)) * (1 - np.exp(-t / 0.004))
    damp = np.where(t < length, 1.0, np.exp(-(t - length) / 0.3))
    return (body + bell) * env_ * damp * vel


TONES = {"piano": piano_note, "felt": felt_note, "epiano": epiano_note}


def read_wav(path):
    with wave.open(path) as w:
        ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), {2: np.int16, 4: np.int32}[sw]).astype(np.float64)
    data = data.reshape(-1, ch).mean(1) / (2 ** (8 * sw - 1))
    if sr != SR:                                      # linear resample
        x = np.arange(int(len(data) * SR / sr)) * sr / SR
        data = np.interp(x, np.arange(len(data)), data)
    return data


def soundtrack(path):
    rng = np.random.default_rng(7)
    out = np.zeros(int((TOTAL + 2) * SR))
    for note, s, d in EVENTS:
        f0 = 440 * 2 ** ((midi_number(note) + OCT_SHIFT - 69) / 12)
        x = TONES[env("PK_TONE", "felt")](f0, d * 1.15, rng=rng)
        i = int(s * SR)
        out[i:i + len(x)] += x[:len(out) - i]
    # a small room: exponentially decaying noise, darker as it decays
    ir_t = np.arange(int(1.6 * SR)) / SR
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.38)
    ir = np.convolve(ir, np.ones(24) / 24, mode="same")
    ir[0] = 0
    nfft = 1 << (len(out) + len(ir)).bit_length()
    wet = np.fft.irfft(np.fft.rfft(out, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(out)]
    mix = out + float(env("PK_REVERB", 0.22)) * wet / (np.abs(wet).max() + 1e-9) * np.abs(out).max()
    mix /= np.abs(mix).max()
    # the switches: a press as the key goes down, a release as it comes up
    click_level = float(env("PK_CLICK", 0))
    keys = os.path.join(HERE, "audio", "keys")
    down, up = read_wav(os.path.join(keys, "largekey_1.wav")), read_wav(os.path.join(keys, "largekey_up_1.wav"))
    for note, s, d in (EVENTS if click_level > 0 else []):
        for snd, at in ((down, s), (up, s + max(0.09, 0.8 * d))):
            i = int(at * SR)
            mix[i:i + len(snd)] += click_level * snd[:len(mix) - i] / (np.abs(snd).max() + 1e-9)
    mix = mix / np.abs(mix).max() * 0.89                 # -1 dBFS
    fade = int(0.5 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"wrote {path}: {len(EVENTS)} notes, {TOTAL:.1f} s")


# --- the picture ---------------------------------------------------------------------
# The rainbow and the blur are eden_video.py's (that script runs on import, so they are
# repeated here): QMK's CYCLE_LEFT_RIGHT at Eden's speed, fitted to 1, cos and sin.
HUE_SPAN = 224 / 256
HUE_PER_MS = (40 // 4 + 1) / 256 / 256
THETA = np.linspace(0, 2 * math.pi * HUE_SPAN, 400)
BASIS = np.stack([np.ones_like(THETA), np.cos(THETA), np.sin(THETA)], 1)


def hsv_channels(h):
    h6 = (h % 1.0) * 6
    i = np.floor(h6).astype(int) % 6
    f = h6 - np.floor(h6)
    q, t = 1 - f, f
    one, zero = np.ones_like(f), np.zeros_like(f)
    table = [(one, t, zero), (q, one, zero), (zero, one, t), (zero, q, one), (t, zero, one), (one, zero, q)]
    out = np.zeros((len(h), 3))
    for k, (r, g, b) in enumerate(table):
        m = i == k
        out[m] = np.stack([r[m], g[m], b[m]], 1)
    return out


def coefficients(el):
    hue = THETA / (2 * math.pi) - HUE_PER_MS * el
    return np.linalg.lstsq(BASIS, hsv_channels(hue), rcond=None)[0]


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


def frames(layers, out, fps):
    import OpenImageIO as oiio
    import PyOpenColorIO as ocio
    from PIL import Image

    # Two layouts of <layer dir>: <pass>.exr (one shot, every key up), or <pass>/up.exr and
    # <pass>/down.exr (eden_view.py with PK_SHOTS: the note keys pressed 3.5 mm in "down",
    # and PK_OUTLINES' <shot>.outlines.json with every key's outline in the picture)
    two = os.path.isdir(os.path.join(layers, "uv"))
    shots = ("up", "down") if two else ("",)

    def exr(name, shot):
        path = os.path.join(layers, name, shot + ".exr") if shot else os.path.join(layers, name + ".exr")
        return np.asarray(oiio.ImageBuf(path).get_pixels(oiio.FLOAT))[..., :3]

    labels = sorted(json.load(open(os.path.join(TEX, "screens_layer0.json"), encoding="utf-8"))["keys"])
    nk = len(labels)

    def load(shot):
        """A shot's light layers and its screen lookup."""
        base, w, c1, s1 = (exr(n, shot) for n in ("base", "w", "c1", "s1"))
        base = base + exr("ambient", shot) * float(env("PK_AMBIENT", 0.07))
        uv, idm = exr("uv", shot), exr("id", shot)
        H, W = base.shape[:2]
        assert uv.shape[:2] == (2 * H, 2 * W), (uv.shape, base.shape)
        seen = idm[..., 2] > 0.05
        raw = np.floor(idm[..., 0] / np.maximum(idm[..., 2], 1e-6) * 128).astype(int)
        u = uv[..., 0] / np.maximum(uv[..., 2], 1e-6)
        v = uv[..., 1] / np.maximum(uv[..., 2], 1e-6)
        # one stack of panels: the key cells 0..71, then the two status panels at 72, 73,
        # all on a 64 x 128 canvas so one fancy index draws every screen of a frame
        cell = np.full(seen.shape, -1)
        keym = seen & (raw >= 0) & (raw < nk)
        cell[keym] = raw[keym]
        for side, sid in ((0, 126), (1, 127)):
            cell[seen & (raw == sid)] = nk + side
        py = np.where(cell >= nk, np.clip(v * 64, 0, 63), np.clip(v * 40, 0, 39)).astype(int)
        px = np.where(cell >= nk, np.clip(u * 128, 0, 127), np.clip(u * 72, 0, 71)).astype(int)
        vis = cell >= 0
        return dict(base=base, w=w, cos=2 * c1 - w, sin=2 * s1 - w, H=H, W=W, vis=vis,
                    trans=np.where(seen, uv[..., 2], 0.0).astype(np.float32),
                    cidx=cell[vis], py=py[vis], px=px[vis])

    S = {sh: load(sh) for sh in shots}
    H, W = S[shots[0]]["H"], S[shots[0]]["W"]
    masks = {}
    if two:
        from PIL import ImageDraw
        outl = json.load(open(os.path.join(layers, "base", "down.outlines.json"), encoding="utf-8"))
        for key in {k for k, _, _ in PRESSES}:
            # the cap's outline: the hull of its top and lower footprints, feathered a pixel
            pts = np.array(outl[key])
            from_hull = pts[hull(pts)]
            m = Image.new("L", (W * 4, H * 4), 0)
            ImageDraw.Draw(m).polygon([tuple(p * 4) for p in from_hull], fill=255)
            m = np.asarray(m.resize((W, H), Image.BOX), np.float32) / 255
            masks[key] = blur(m, 1)

    def stack(name):
        """Every screen of the layer from one atlas (the status panels are the same)."""
        atlas = np.asarray(Image.open(os.path.join(TEX, name + ".png")).convert("L"), np.float32) / 255
        amap = json.load(open(os.path.join(TEX, name + ".json"), encoding="utf-8"))["keys"]
        out = np.zeros((nk + 2, 64, 128), np.float32)
        for i, lab in enumerate(labels):
            if lab in amap:
                x, y = amap[lab]
                out[i, :40, :72] = atlas[y:y + 40, x:x + 72]
        for side, sname in enumerate(("left", "right")):
            st = np.asarray(Image.open(os.path.join(TEX, f"status_{sname}_l8.png")).convert("L"), np.float32) / 255
            out[nk + side, :64, :128] = st[:64, :128]
        return out

    # the legends at the start octave, and after OCT 3 (export_screens.py with the dump's
    # configuration word set to octave index 4: midi_cfg_pack(4, 0, 127, 0) = 0x807F0004)
    legends = stack("screens_layer8")
    legends_after = stack("screens_layer8_oct3") if OCT_SHIFT else legends
    index = {lab: i for i, lab in enumerate(labels)}
    for key, _, _ in PRESSES:
        assert key in index, key

    cfg = ocio.Config.CreateFromFile(env("BLENDER_OCIO") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(sys.executable)))),
        "datafiles", "colormanagement", "config.ocio"))
    grp = ocio.GroupTransform()
    grp.appendTransform(ocio.LookTransform(src="Linear Rec.709", dst="Linear Rec.709",
                                           looks=env("PK_LOOK", "AgX - High Contrast")))
    grp.appendTransform(ocio.DisplayViewTransform(src="Linear Rec.709", display="sRGB", view="AgX"))
    cpu = cfg.getProcessor(grp).getDefaultCPUProcessor()

    screen = float(env("PK_STRENGTH", 5.0))
    bloom = float(env("PK_BLOOM", 0.25))
    tint = np.array([0.70, 0.84, 1.0], np.float32)
    rainbow = float(env("PK_RAINBOW", 0.5))
    width = int(env("PK_WIDTH", 0)) or None
    t0, t1 = float(env("PK_START", 0)), float(env("PK_END", TOTAL))
    if env("PK_TIMES"):
        times = [int(x) / 1000 for x in env("PK_TIMES").split(",")]
    else:
        times = [t0 + i / fps for i in range(int((t1 - t0) * fps))]
    tmp = tempfile.mkdtemp()
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    for n, t in enumerate(times):
        k = coefficients(t * 1000) * rainbow
        panels = (legends_after if t >= OCT_AT else legends).copy()
        for key in held(t):                            # a key event inverts its screen
            i = index[key]
            panels[i, :40, :72] = 1.0 - panels[i, :40, :72]
        out_lin = {}
        for sh in shots:
            L = S[sh]
            lin = L["base"] + L["w"] * k[0] + L["cos"] * k[1] + L["sin"] * k[2]
            lit = np.zeros(L["vis"].shape, np.float32)
            lit[L["vis"]] = panels[L["cidx"], L["py"], L["px"]]
            scr = (lit * L["trans"]).reshape(H, 2, W, 2).mean((1, 3))
            out_lin[sh] = (lin, scr)
        if two:
            # each key's travel: the up shot, the down shot inside its outline, or between
            m = np.zeros((H, W), np.float32)
            for key, d in depths(t).items():
                m = np.maximum(m, masks[key] * d)
            lin = out_lin["up"][0] * (1 - m[..., None]) + out_lin["down"][0] * m[..., None]
            scr = out_lin["up"][1] * (1 - m) + out_lin["down"][1] * m
        else:
            lin, scr = out_lin[""]
        glow = blur(scr, max(1, W // 320))
        lin = lin + (scr + bloom * glow)[..., None] * tint * screen
        img = np.ascontiguousarray(np.clip(lin, 0, None).astype(np.float32))
        cpu.applyRGB(img)
        frame = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
        if env("PK_ASPECT"):
            ch = int(round(W / float(env("PK_ASPECT")) / 2)) * 2
            y0 = int(np.clip(round(float(env("PK_CROP_CY", 0.5)) * H - ch / 2), 0, H - ch))
            frame = frame.crop((0, y0, W, y0 + ch))
        if width:
            frame = frame.resize((width, int(round(frame.height * width / frame.width / 2)) * 2), Image.LANCZOS)
        frame.save(os.path.join(tmp, f"{n:05d}.png"))
        if n % 50 == 0:
            print(f"frame {n}/{len(times)} t={t:.2f} s keys={sorted(held(t))}", flush=True)
    if out.endswith(".png"):
        for n, t in enumerate(times):
            os.replace(os.path.join(tmp, f"{n:05d}.png"), out[:-4] + f"_t{int(t * 1000)}.png")
        print("wrote", len(times), "stills")
        return
    if out.endswith(".gif"):
        pal = os.path.join(tmp, "pal.png")
        src = ["-framerate", str(fps), "-i", os.path.join(tmp, "%05d.png")]
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *src, "-vf", "palettegen=max_colors=128:stats_mode=diff",
                        pal], check=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *src, "-i", pal, "-lavfi",
                        "paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", "-loop", "0", out], check=True)
        print("wrote", out, len(times), "frames")
        return
    wav = os.path.join(tmp, "sound.wav")
    soundtrack(wav)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%05d.png"),
                    "-ss", str(t0), "-t", str(len(times) / fps), "-i", wav,
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("wrote", out, len(times), "frames")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0].endswith(".wav"):
        soundtrack(os.path.abspath(a[0]))
    else:
        frames(a[0], os.path.abspath(a[1]), int(a[2]) if len(a) > 2 else 25)
