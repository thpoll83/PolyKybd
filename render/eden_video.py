"""The Eden boot-animation video from eden_view.py's layers.

    /tmp/blender-4.1.1-linux-x64/4.1/python/bin/python3.11 render/eden_video.py \
        <layer dir> <out.mp4> [fps]

<layer dir> holds eden_view.py's base.exr, w.exr, c1.exr, s1.exr, uv.exr and
id.exr. Run it with Blender's bundled Python: it brings OpenImageIO (EXR),
PyOpenColorIO (Blender's own AgX), numpy and Pillow.

Each frame is built from the layers:

- the key LEDs' light at time t is a1 * W + a2 * Cos + a3 * Sin per colour
  channel, where Cos = 2 * c1 - w and Sin = 2 * s1 - w are the light at the
  weights cos and sin of the rainbow's phase, and (a1, a2, a3) is the
  least-squares fit of that channel of QMK's CYCLE_LEFT_RIGHT rainbow (hue =
  led x - speed * t) to 1, cos and sin. It is scaled by the firmware's
  startup_anim_rainbow_level() curve, so the rainbow fades out as on the board;
- every keycap screen's pixels come from PolyKybdHost's tools/fw_anim_sim.py,
  the port of startup_anim.c, looked up through the uv and id maps (B = what
  the glass lets through), at the maps' double resolution and then averaged
  down, plus a soft bloom;
- the sum goes through Blender's AgX view with PK_LOOK (default "AgX - High
  Contrast"), as the stills do, then to H.264 with ffmpeg.
"""
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np
import OpenImageIO as oiio
import PyOpenColorIO as ocio
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, "..", "PolyKybdHost", "tools")
sys.path.insert(0, TOOLS)
from fw_anim_sim import FwSim, mp_to_half_idx  # noqa: E402

layers, out = sys.argv[1], os.path.abspath(sys.argv[2])
fps = int(sys.argv[3]) if len(sys.argv) > 3 else 25
SCREEN = float(os.environ.get("PK_STRENGTH", 5.0))     # the screens' emission, as in the stills
LIT_TINT = np.array([0.70, 0.84, 1.0], np.float32)     # screens.LIT_TINT
BLOOM = float(os.environ.get("PK_BLOOM", 0.25))
HUE_SPAN = 224 / 256                                   # eden_view.HUE_SPAN
# QMK rgb_matrix: time = scale16by8(g_rgb_timer, qadd8(speed / 4, 1)), hue = x - time.
# Eden sets speed TRGB_RAINBOW_SPD = RGB_MATRIX_DEFAULT_SPD * 8 / 5 = 40, so the hue
# moves (40 / 4 + 1) / 256 hue units (of 256) per ms.
HUE_PER_MS = (40 // 4 + 1) / 256 / 256                 # in turns
INTRO_MS = 5000                                        # SA_INTRO_MS


def rainbow_level(el):
    """startup_anim_rainbow_level() / 255: full, then a linear fade to off."""
    a, b = INTRO_MS * 180 // 256, INTRO_MS * 240 // 256
    return 1.0 if el <= a else 0.0 if el >= b else 1.0 - (el - a) / (b - a)


def hsv_channels(h):
    """colorsys.hsv_to_rgb(h, 1, 1) for an array of hues in turns -> (n, 3)."""
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


THETA = np.linspace(0, 2 * math.pi * HUE_SPAN, 400)    # the phase over the LEDs' x
BASIS = np.stack([np.ones_like(THETA), np.cos(THETA), np.sin(THETA)], 1)


def coefficients(el):
    """(3 basis, 3 channels): the fit of the rainbow at time el to 1, cos, sin."""
    hue = THETA / (2 * math.pi) - HUE_PER_MS * el
    return np.linalg.lstsq(BASIS, hsv_channels(hue), rcond=None)[0]


def blur(a, r):
    """About a Gaussian of sigma r: three box passes of width 2r + 1 per axis."""
    for axis in (0, 1):
        for _ in range(3):
            pad = [(0, 0), (0, 0)]
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            a = (hi - lo) / (2 * r + 1)
    return a


def exr(path):
    return np.asarray(oiio.ImageBuf(path).get_pixels(oiio.FLOAT))[..., :3]


base, w, c1, s1 = (exr(os.path.join(layers, n + ".exr")) for n in ("base", "w", "c1", "s1"))
if os.path.exists(os.path.join(layers, "ambient.exr")):   # a dim room light, PK_AMBIENT times
    base = base + exr(os.path.join(layers, "ambient.exr")) * float(os.environ.get("PK_AMBIENT", 1.0))
cos_l, sin_l = 2 * c1 - w, 2 * s1 - w
uv, idm = exr(os.path.join(layers, "uv.exr")), exr(os.path.join(layers, "id.exr"))
H, W = base.shape[:2]
assert uv.shape[:2] == (2 * H, 2 * W), (uv.shape, base.shape)
labels = sorted(json.load(open(os.path.join(REPO, "render", "textures", "screens_layer0.json"),
                               encoding="utf-8"))["keys"])
seen = idm[..., 2] > 0.05                                # a screen through the glass
cell = np.clip(np.floor(idm[..., 0] / np.maximum(idm[..., 2], 1e-6) * 128), 0, len(labels) - 1).astype(int)
px = np.clip(np.floor(uv[..., 0] / np.maximum(uv[..., 2], 1e-6) * 72), 0, 71).astype(int)
py = np.clip(np.floor(uv[..., 1] / np.maximum(uv[..., 2], 1e-6) * 40), 0, 39).astype(int)
trans = np.where(seen, uv[..., 2], 0.0).astype(np.float32)
half_idx = mp_to_half_idx()
keys = [half_idx.get(lab) for lab in labels]
print(f"layers {W}x{H}, screen pixels {int(seen.sum())}, keys {sum(k is not None for k in keys)}")

cfg = ocio.Config.CreateFromFile("/tmp/blender-4.1.1-linux-x64/4.1/datafiles/colormanagement/config.ocio")
look = os.environ.get("PK_LOOK", "AgX - High Contrast")
grp = ocio.GroupTransform()
grp.appendTransform(ocio.LookTransform(src="Linear Rec.709", dst="Linear Rec.709", looks=look))
grp.appendTransform(ocio.DisplayViewTransform(src="Linear Rec.709", display="sRGB", view="AgX"))
cpu = cfg.getProcessor(grp).getDefaultCPUProcessor()

sim = FwSim()
step = 1000 / fps
times = [int(round(i * step)) for i in range(int(sim.TOTAL / step) + 1)]
if os.environ.get("PK_TIMES"):                    # stills at these ms (out.png -> out_t<ms>.png)
    times = [int(v) for v in os.environ["PK_TIMES"].split(",")]
tmp = tempfile.mkdtemp()
for n, el in enumerate(times):
    k = coefficients(el) * rainbow_level(el)
    lin = base + w * k[0] + cos_l * k[1] + sin_l * k[2]
    # the screens at double resolution: each image pixel's keycap pixel
    lit = np.zeros(seen.shape, np.float32)
    for ci, key in enumerate(keys):
        if key is None:
            continue
        bmp = sim.panel(key[0], key[1], el)
        if bmp is None:
            continue
        m = seen & (cell == ci)
        lit[m] = bmp[py[m], px[m]]
    scr = (lit * trans).reshape(H, 2, W, 2).mean((1, 3))
    glow = blur(scr, max(1, W // 320))
    lin = lin + (scr + BLOOM * glow)[..., None] * LIT_TINT * SCREEN
    img = np.ascontiguousarray(np.clip(lin, 0, None).astype(np.float32))
    cpu.applyRGB(img)
    frame = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    if os.environ.get("PK_ASPECT"):              # a wider frame: crop the height, centred on the board
        ch = int(round(W / float(os.environ["PK_ASPECT"]) / 2)) * 2
        y0 = int(np.clip(round(float(os.environ.get("PK_CROP_CY", 0.5)) * H - ch / 2), 0, H - ch))
        frame = frame.crop((0, y0, W, y0 + ch))
    frame.save(os.path.join(tmp, f"{n:05d}.png"))
    if n % 25 == 0:
        print(f"frame {n}/{len(times)} t={el} ms rainbow={rainbow_level(el):.2f}", flush=True)
if out.endswith(".png"):
    for n, el in enumerate(times):
        os.replace(os.path.join(tmp, f"{n:05d}.png"), out[:-4] + f"_t{el}.png")
    print("wrote", len(times), "stills")
    sys.exit(0)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "%05d.png"),
                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
print("wrote", out, len(times), "frames")
