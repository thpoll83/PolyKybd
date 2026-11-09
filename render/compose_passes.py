"""Mix closeup_view.py's light groups (PK_PASSES) into the final image, with the
settings of the close-up tuning page, so the result is what the page showed.

    <blender>/4.1/python/bin/python3.11 render/compose_passes.py passes_dir out.png '<settings json>' [square]

passes_dir holds Combined_{studio,floor,sheen,legends}0001.exr and mat0001.exr
(the cutting mat's mask); the settings are the page's "Copy settings" line:
exposure (stops), contrast, saturation, warmth (-1..1), studio, floor, sheen and
glow (multipliers), hue (degrees, + = bluer), haze (amount), radius (haze size in
px at the page's 810 px), matBright, matHue, matSat (the mat alone), edge and
edgeRadius (the letters' light on their caps' edges, from the capedge mask), and
dust, dustSeed. `square`
crops the centre square, as the page shows it.

The maths is the tuning page's own (the "POLY KYBD Close-up Tuner" artifact): the
four layers scaled and summed in linear light, the letters turned about the grey
axis, the mat turned, saturated and scaled under its mask, a haze from a blur of
the letters, then Blender's AgX (inset matrix, log2 encoding, sigmoid, outset)
with a contrast and saturation look applied to the encoded values. On the same
layers it matches the page to 2/255 on average (the page's layers are 8 bit).
"""
import json
import sys

import numpy as np
import OpenImageIO as oiio

M = np.array([[0.842479062253094, 0.0423282422610123, 0.0423756549057051],
              [0.0784335999999992, 0.878468636469772, 0.0784336],
              [0.0792237451477643, 0.0791661274605434, 0.879142973793104]])
MI = np.array([[1.19687900512017, -0.0528968517574562, -0.0529716355144438],
               [-0.0980208811401368, 1.15190312990417, -0.0980434501171241],
               [-0.0990297440797205, -0.0989611768448433, 1.15107367264116]])
MN, MX = -12.47393, 4.026069
PAGE_W = 810                                   # the page's picture width: haze radius is in its pixels


def read(path):
    return oiio.ImageBuf(path).get_pixels(oiio.FLOAT)[..., :3].astype(np.float32)


def hue_matrix(deg):
    """Rotation about the grey axis, as the page's hueMatrix(); rows act on (r, g, b)."""
    t = np.radians(deg)
    c, s, k, q = np.cos(t), np.sin(t), 1 / 3, np.sqrt(1 / 3)
    return np.array([[c + (1 - c) * k, (1 - c) * k - q * s, (1 - c) * k + q * s],
                     [(1 - c) * k + q * s, c + (1 - c) * k, (1 - c) * k - q * s],
                     [(1 - c) * k - q * s, (1 - c) * k + q * s, c + (1 - c) * k]])


def box3(a, r):
    """Three box blurs of radius r along both axes: the page's blur()."""
    for _ in range(3):
        for axis in (1, 0):
            pad = [(0, 0)] * 3
            pad[axis] = (r + 1, r)
            p = np.pad(a, pad, mode="edge")
            c = np.cumsum(p, axis=axis, dtype=np.float64)
            hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
            a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def add_dust(lin, mk, amount, seed):
    """A 2D dust layer: about 900 * amount specks per 810 x 810 px (scaled to the image),
    1 to 4 px across at that scale (most small), a few dozen fibres, each a pale grey that
    takes its brightness from the surface around it, so a speck reads in light and
    stays faint in shadow."""
    rng = np.random.default_rng(seed)
    h, w = lin.shape[:2]
    k = min(h, w) / PAGE_W
    n = int(900 * amount * (h * w) / (PAGE_W * PAGE_W))
    cov = np.zeros((h, w), np.float32)
    ys, xs = rng.uniform(0, h, n), rng.uniform(0, w, n)
    rs = k * (0.5 + 1.6 * rng.uniform(0, 1, n) ** 3)
    al = rng.uniform(0.35, 0.9, n)
    for y, x, r, a in zip(ys, xs, rs, al):
        y0, y1, x0, x1 = int(max(0, y - 3 * r - 1)), int(min(h, y + 3 * r + 2)), int(max(0, x - 3 * r - 1)), int(min(w, x + 3 * r + 2))
        yy, xx = np.mgrid[y0:y1, x0:x1]
        cov[y0:y1, x0:x1] = np.maximum(cov[y0:y1, x0:x1], a * np.exp(-((yy - y) ** 2 + (xx - x) ** 2) / (2 * r * r)))
    for _ in range(int(40 * amount * (h * w) / (PAGE_W * PAGE_W))):    # fibres: thin bent strokes
        y, x = rng.uniform(0, h), rng.uniform(0, w)
        ang, ln, a = rng.uniform(0, np.pi), k * rng.uniform(4, 14), rng.uniform(0.2, 0.5)
        for t in np.linspace(0, 1, int(ln * 2) + 2):
            ang += rng.normal(0, 0.15)
            yy, xx = int(y + np.sin(ang) * ln * t), int(x + np.cos(ang) * ln * t)
            if 0 <= yy < h and 0 <= xx < w:
                cov[yy, xx] = max(cov[yy, xx], a)
    if mk is not None:
        cov *= (1 - mk[..., 0]) ** 2
    near = box3(lin.mean(-1, keepdims=True), max(1, int(3 * k)))[..., 0]   # the surface's light around a speck
    # pale grey fluff, lighter than the surface under it (0.25 linear above 0.6 of the light
    # around it), so it reads on dark caps and in shadows as on the photo's plate
    tone = (0.6 * near + 0.25)[..., None] * np.array([0.92, 0.9, 0.86], np.float32)
    return lin * (1 - cov[..., None]) + tone * cov[..., None]


def compose(d, p):
    L = read(f"{d}/Combined_legends0001.exr")
    h, w = L.shape[:2]
    Lt = p["glow"] * (L @ hue_matrix(-p["hue"]).T)
    lin = (p["studio"] * read(f"{d}/Combined_studio0001.exr") + p["floor"] * read(f"{d}/Combined_floor0001.exr")
           + p["sheen"] * read(f"{d}/Combined_sheen0001.exr") + Lt)
    try:
        mk = read(f"{d}/mat0001.exr")[..., :1]
    except Exception:                          # layers from before the mat mask
        mk = None
    if mk is not None and any(p.get(k, dv) != dv for k, dv in (("matBright", 1), ("matHue", 0), ("matSat", 1))):
        t = lin @ hue_matrix(-p.get("matHue", 0)).T
        ml = (t * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
        adj = p.get("matBright", 1) * np.maximum(0, ml + (t - ml) * p.get("matSat", 1))
        lin = lin * (1 - mk) + adj * mk
    if p["haze"] > 0:                          # the page blurs a quarter-size copy; the same at this size
        q = 4 * max(1, round(min(h, w) / PAGE_W))
        hh, ww = h // q * q, w // q * q
        small = Lt[:hh, :ww].reshape(hh // q, q, ww // q, q, 3).mean((1, 3))
        r = max(1, round(p["radius"] * (min(h, w) / PAGE_W) / q / 1.7))
        hz = box3(small, r)
        hz = np.repeat(np.repeat(hz, q, 0), q, 1)
        lin[:hh, :ww] += p["haze"] * hz
    if p.get("edge", 0) > 0:                   # the light a lit display scatters into its cap, caught on the
        try:                                       # cap's bevelled edges and corners (the capedge mask), in the
            ce = read(f"{d}/capedge0001.exr")[..., :1]   # letters' own colour, fading with distance from them
        except Exception:
            ce = None
        if ce is not None:
            k = min(h, w) / PAGE_W
            q = 4 * max(1, round(k))
            hh, ww = h // q * q, w // q * q
            small = Lt[:hh, :ww].reshape(hh // q, q, ww // q, q, 3).mean((1, 3))
            near = box3(small, max(1, round(p.get("edgeRadius", 30) * k / q / 1.7)))
            near = np.repeat(np.repeat(near, q, 0), q, 1)
            lin[:hh, :ww] += p["edge"] * ce[:hh, :ww] ** 2 * near
    if p.get("dust", 0) > 0:                   # dust: soft specks and a few short fibres on the keyboard (not
        lin = add_dust(lin, mk, p["dust"], int(p.get("dustSeed", 7)))   # the mat), lit by the scene around them
    lin *= 2.0 ** p["exposure"] * np.array([1 + 0.12 * p["warmth"], 1.0, 1 - 0.12 * p["warmth"]], np.float32)
    v = np.maximum(lin, 1e-10) @ M
    x = (np.clip(np.log2(np.maximum(v, 1e-10)), MN, MX) - MN) / (MX - MN)
    x2 = x * x
    x4 = x2 * x2
    y = np.clip(15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232, 0, 1)
    y = np.clip(0.5 + (y - 0.5) * p["contrast"], 0, 1)
    lum = (y * np.array([0.2126, 0.7152, 0.0722])).sum(-1, keepdims=True)
    y = np.clip(lum + (y - lum) * p["saturation"], 0, 1)
    o = np.clip(y @ MI, 0, 1) ** 2.2
    return np.where(o <= 0.0031308, 12.92 * o, 1.055 * np.power(o, 1 / 2.4) - 0.055)


if __name__ == "__main__":
    d, out, settings = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
    img = compose(d, settings)
    if len(sys.argv) > 4 and sys.argv[4] == "square":
        h, w = img.shape[:2]
        img = img[:, (w - h) // 2:(w + h) // 2]
    h, w = img.shape[:2]
    buf = oiio.ImageBuf(oiio.ImageSpec(w, h, 3, oiio.UINT8))
    buf.set_pixels(oiio.ROI(0, w, 0, h, 0, 1, 0, 3), (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))
    buf.write(out)
    print("wrote", out, w, h)
