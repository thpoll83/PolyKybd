"""The first-run tutorial video, from eden_view.py's per-shot layers and tutorial_story.py's screens.

    <blender dir>/4.1/python/bin/python3.11 render/tutorial_video.py storyboard <layers> <story.npz> <out dir>

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

    def frame(self, keys, status, ambient, cpu):
        lin = self.base + self.ambient * ambient
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


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "storyboard":
        storyboard(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(f"unknown mode {mode}")
