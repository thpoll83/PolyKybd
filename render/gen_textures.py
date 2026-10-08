"""Make the keycap display and flex-cable textures (Pillow).

    python render/gen_textures.py        -> render/textures/{display_front,display_rim,flex,braid}.png

(numpy + Pillow; Blender's bundled python has both.)

Both come from a photo of the real part, FPT042000Z05_V2 0.42" OLED
(textures/source/oled_module_photo.jpg, a crop of the photo; the module
lies with its flex to the left, the display at the right):

- display_front.png covers the top face of keycap_display.wrl as placed on a
  key: 12.2 mm across (x) by 11.0 mm (y), the cable side at the BOTTOM of the
  image (-y on the key). It is the photo's module, turned so the cable side
  is down: glass, the dark active area, the striped sticker over the bond
  with its lot number, and the start of the black sticker over the flex.
  A 0.1 mm black seam is drawn round it, where the glass meets the key stem.
- display_front_top.png is the same with lighter glass, for topview.py.
- display_rim.png masks the glass's edge for materials.py's glass coat.
- flex.png is mapped by flex_cable.strip()'s uv: u across the 7.5 mm width,
  v along the strip from the display (top of the image) to the connector
  (bottom). It is the photo's flex, display end up.

⚠️ The photo is NOT evenly scaled: along the display 29.1 px/mm (the
module's 12.2 mm edge is 355 px), across it 24.3 px/mm (the active area's
5.1 mm is 124 px). Each is fitted on its own axis. keymatch.A_* centres the
active area in this photo's dark panel area, and the lit legends and the host
editor's display quads follow keymatch, so a different photo or a moved
box means re-measuring both.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "textures"
PX_PER_MM = 80
PHOTO = OUT / "source" / "oled_module_photo.jpg"
# boxes in PHOTO's pixels (x0, y0, x1, y1): the module (its flex-side edge
# at x0, the far edge at x1; y across), and the flex from the gold fingers
# to where it meets the module
MODULE_BOX = (1158, 24, 1425, 379)
FLEX_BOX = (12, 82, 1158, 322)
DARKEN = (1.2, 0.8)        # v' = 255 * DARKEN[1] * (v/255)^DARKEN[0]: the photo is lit bright
RIM = 0.3                   # mm: the display glass's cut edge, around the face
SEAM = 0.1                  # mm: the dark gap between the key stem and the glass, outside the rim


def mm(v):
    return int(round(v * PX_PER_MM))


def _photo(box, size_mm):
    """The photo box, turned so its right edge (towards the display's far
    end) is at the top, fitted to size_mm (w, h), darkened."""
    im = Image.open(PHOTO).convert("RGB").crop(box).transpose(Image.Transpose.ROTATE_90)
    im = im.resize((mm(size_mm[0]), mm(size_mm[1])), Image.LANCZOS)
    a = np.asarray(im, float) / 255
    # the photo's white background (beside the flex, at the box corners) is
    # the key stem on a key: near-white, unsaturated pixels go near black
    white = np.clip((a.min(2) - 0.78) / 0.1, 0, 1) * np.clip((0.12 - (a.max(2) - a.min(2))) / 0.06, 0, 1)
    a = DARKEN[1] * a ** DARKEN[0]
    a = a * (1 - white[..., None]) + 0.02 * white[..., None]
    return Image.fromarray((a * 255).clip(0, 255).astype("uint8"))


def display_rim():
    """Mask for display_front.png: white on the glass rim, black elsewhere.
    materials.py lays a glass coat over the rim from it."""
    w, h = 12.2, 11.0
    im = Image.new("L", (mm(w), mm(h)), 0)                          # the seam: no glass
    d = ImageDraw.Draw(im)
    d.rectangle([mm(SEAM), mm(SEAM), mm(w - SEAM), mm(h - SEAM)], fill=255)
    d.rectangle([mm(SEAM + RIM), mm(SEAM + RIM), mm(w - SEAM - RIM), mm(h - SEAM - RIM)], fill=0)
    return im.filter(ImageFilter.GaussianBlur(0.6))


STYLE = "drawn"             # "drawn" (traced from the photo, sharp) or "photo" (the photo itself)


def font(size, bold=True):
    for f in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _grain(im, amount, seed):
    """A little fine, even noise, so flat fills read as material, not paint."""
    rng = np.random.default_rng(seed)
    a = np.asarray(im, float)
    n = rng.normal(0, amount, a.shape[:2])[..., None]
    n = np.asarray(Image.fromarray(((n[..., 0] + 64).clip(0, 255)).astype("uint8")).filter(
        ImageFilter.GaussianBlur(1.2)), float)[..., None] - 64
    return Image.fromarray((a + n).clip(0, 255).astype("uint8"))


def _stripes(size_px, pitch, width, base, line, angle_down_right=True):
    """A fill of parallel diagonal stripes (the sticker's film)."""
    w, h = size_px
    im = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(im)
    for k in range(-h, w + h, pitch):
        if angle_down_right:
            d.line([(k, 0), (k + h, h)], fill=line, width=width)
        else:
            d.line([(k + h, 0), (k, h)], fill=line, width=width)
    return im


def _rounded_paste(im, tile, box, radius):
    mask = Image.new("L", tile.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, tile.width - 1, tile.height - 1], radius, fill=255)
    im.paste(tile, box[:2], mask.filter(ImageFilter.GaussianBlur(0.8)))


FADE_FACE = 1.05            # mm of the fade on the display face (glass edge to its bottom edge)
FADE_LEN = 1.87             # mm: the whole fade, the face's part and then the flex's (2.8 faded too slowly)


def _fade(im, box, a0, a1, mask=None):
    """Black over box (mm: x0, y0, x1, y1), `a0` opaque at its top edge and
    `a1` at its bottom, so the flex beside the sticker sinks into shadow
    next to the display and comes out of it further along the strip. The
    same fade is taken out of `mask` (the copper mask), if given."""
    x0, y0, x1, y1 = (mm(v) for v in box)
    wpx, hpx = max(1, x1 - x0), max(1, y1 - y0)
    ramp = np.linspace(a0, a1, hpx)
    a = np.tile(ramp[:, None], (1, wpx))
    region = np.asarray(im.crop((x0, y0, x1, y1)), float)
    im.paste(Image.fromarray((region * (1 - a[..., None])).astype("uint8")), (x0, y0))
    if mask is not None:
        m = np.asarray(mask.crop((x0, y0, x1, y1)), float)
        mask.paste(Image.fromarray((m * (1 - a)).astype("uint8")), (x0, y0))


# The display face's light colours: glass cut edge, glass body, the light strip,
# the tan glue, the pads. The photo view's are calmer, matched to the photo.
# Seen from straight above (topview.py, the host editor's picture) the light
# reaches the displays only past the cap walls, and those colours read as one
# black square: the top view gets lighter ones, so the panel, the sticker and
# the pads stay readable.
FACE = {"edge": (74, 75, 77), "body": (30, 31, 33), "strip": (60, 60, 59),
        "glue": (80, 73, 62), "pad": (108, 108, 108), "panel": (14, 14, 20),
        "stripes": ((34, 34, 36), (24, 24, 26))}
FACE_TOP = {"edge": (168, 174, 178), "body": (80, 84, 88), "strip": (88, 88, 86),
            "glue": (125, 107, 78), "pad": (168, 168, 168), "panel": FACE["panel"],
            "stripes": FACE["stripes"]}


def display_front_drawn(face=FACE):
    """The module traced from the photo (mm, image top = the far end, cable
    side down) and drawn with sharp edges: the glass and its light cut edge,
    the dark panel with the active area, the light strip and tan corners
    below it, the black bond blocks with their pads, the striped sticker with
    the lot number, and the black sticker that goes on over the flex."""
    w, h = 12.2, 11.0
    im = Image.new("RGB", (mm(w), mm(h)), (5, 5, 5))                # key stem around the glass
    d = ImageDraw.Draw(im)
    R = lambda x0, y0, x1, y1: [mm(x0), mm(y0), mm(x1), mm(y1)]
    # orange flex tabs showing beside the flex sticker, below the glass, with
    # the traces running through them to the edge
    for x0, x1 in ((1.6, 2.3), (8.9, 10.4)):
        d.rectangle(R(x0, 9.6, x1, h), fill=(150, 92, 16))
    for x in (1.95, 9.25, 9.65, 10.05):
        d.rectangle(R(x - 0.08, 9.6, x + 0.08, h), fill=(112, 64, 8))
    # the glass: its cut edge reads light, the body dark
    d.rounded_rectangle(R(0.15, 0.15, 11.95, 9.95), mm(0.12), fill=face["edge"])
    d.rectangle(R(0.45, 0.45, 11.65, 9.65), fill=face["body"])
    # the dark panel area and the active area in it
    d.rounded_rectangle(R(0.55, 0.55, 11.75, 6.35), mm(0.25), fill=face["panel"])
    d.rectangle(R(0.6, 6.0, 11.7, 6.35), fill=(6, 6, 8))           # its darker bottom band
    d.rectangle(R(1.5, 1.0, 10.7, 6.1), fill=(8, 8, 14))           # keymatch.A_*: unlit, near black
    # the light strip below the panel, and the tan glue at its ends
    d.rectangle(R(0.55, 6.35, 11.75, 6.7), fill=face["strip"])
    for x0, x1 in ((0.2, 1.6), (11.0, 12.0)):
        d.rectangle(R(x0, 6.6, x1, 7.0), fill=face["glue"])
    # the black bond blocks either side, each with two light pads
    for x0, x1, dots in ((0.2, 1.85, ((0.95, 8.1), (1.35, 8.75))), (10.7, 11.95, ((10.95, 8.15), (11.5, 7.6)))):
        d.rectangle(R(x0, 7.0, x1, 9.1), fill=(10, 10, 11))
        for cx, cy in dots:
            d.ellipse(R(cx - 0.09, cy - 0.09, cx + 0.09, cy + 0.09), fill=face["pad"])
    # the striped sticker with the lot number
    sx0, sy0, sx1, sy1 = 1.95, 6.55, 11.0, 9.15
    tile = _stripes((mm(sx1 - sx0), mm(sy1 - sy0)), mm(0.42), max(1, mm(0.07)), *face["stripes"])
    td = ImageDraw.Draw(tile)
    td.text((tile.width // 2 - mm(0.3), mm(1.75)), "2305054", fill=(26, 26, 28), font=font(mm(0.9), bold=False), anchor="mm")
    _rounded_paste(im, tile, (mm(sx0), mm(sy0)), mm(0.3))
    # the black sticker over the flex, glossy, carrying on past the glass
    fl = Image.new("RGB", (mm(9.0 - 1.75), mm(h - 9.05)), (12, 12, 13))
    fd = ImageDraw.Draw(fl)
    fd.line([(mm(0.4), mm(0.35)), (mm(6.6), mm(0.55))], fill=(40, 40, 42), width=mm(0.12))  # a highlight
    im.paste(fl, (mm(1.75), mm(9.05)))
    # the flex beside it falls into shadow
    # black at the glass edge, fading along the strip; flex_drawn() carries on
    edge = 1 - FADE_FACE / FADE_LEN
    _fade(im, (1.4, 9.95, 1.75, h), 1.0, edge)       # below the glass
    _fade(im, (9.0, 9.95, 10.6, h), 1.0, edge)
    # the wire detail at its right end
    for k in range(5):
        x = 8.95 + k * 0.18
        d.line([(mm(x), mm(9.05)), (mm(x + 0.08), mm(9.45))], fill=(70, 70, 72), width=max(1, mm(0.05)))
    im = _grain(im, 3.0, 1)
    # the seam between the key stem and the glass
    d = ImageDraw.Draw(im)
    for k in range(mm(SEAM)):
        d.rectangle([k, k, im.width - 1 - k, im.height - 1 - k], outline=(5, 5, 5))
    return im.filter(ImageFilter.GaussianBlur(0.5))


def flex_drawn(length_mm):
    """The flex traced from the photo, display end up: the end of the black
    sticker, the traces fanning in to a row of pads, a second short fan, 14
    straight traces, the part number, "1" and "14", and the contact fingers."""
    w = 7.5
    base, trace, pad = (184, 120, 14), (150, 88, 8), (110, 64, 6)
    im = Image.new("RGB", (mm(w), mm(length_mm)), base)
    d = ImageDraw.Draw(im)
    L = length_mm
    n, pitch = 14, 0.5
    xs = [(w - (n - 1) * pitch) / 2 + i * pitch for i in range(n)]       # straight run
    fan_top = [0.6 + i * (w - 1.2) / (n - 1) for i in range(n - 2)] + [6.65, 7.05]   # last two beside the sticker
    pads_y, fan2_y = 4.0, 6.3
    mid = [x - 0.25 * (i >= n // 2) for i, x in enumerate(xs)]           # after the first fan
    mask = Image.new("L", im.size, 0)          # the copper: what materials.py makes shine
    md = ImageDraw.Draw(mask)
    tw = max(1, mm(0.14))                       # in the fans
    st0, st1 = 0.5, 6.4                         # the black sticker's end, across
    for i in range(n):
        # a trace beside the sticker is not covered by it, so it runs on to
        # the display end; the others come out from under the sticker
        top = 0.0 if not st0 <= fan_top[i] <= st1 else 1.7
        pts = [(fan_top[i], top), (fan_top[i], 2.2), (mid[i], pads_y - 0.4), (mid[i], pads_y),
               (mid[i], fan2_y - 1.2), (xs[i], fan2_y)]
        for dd, col in ((d, trace), (md, 255)):
            dd.line([(mm(x), mm(y)) for x, y in pts], fill=col, width=tw, joint="curve")
            # the straight run: wide traces, 0.3 mm on the 0.5 mm pitch
            dd.rectangle([mm(xs[i] - 0.15), mm(fan2_y), mm(xs[i] + 0.15), mm(L - 2.4)], fill=col)
    # the row of pads the first fan runs into
    d.line([(mm(0.4), mm(pads_y)), (mm(w - 0.4), mm(pads_y))], fill=pad, width=max(1, mm(0.1)))
    for x in mid:
        d.ellipse([mm(x - 0.1), mm(pads_y - 0.1), mm(x + 0.1), mm(pads_y + 0.1)], fill=(170, 120, 40))
    # the end of the black sticker
    d.rectangle([mm(0.5), 0, mm(6.4), mm(1.75)], fill=(12, 12, 13))
    d.line([(mm(0.9), mm(0.5)), (mm(6.0), mm(0.7))], fill=(40, 40, 42), width=mm(0.12))
    # the part number along the strip, and the pin numbers by the fingers
    txt = Image.new("RGBA", (mm(L * 0.5), mm(1.0)), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((0, 0), "FPT042000Z05_V2", fill=(240, 238, 230, 255), font=font(mm(0.75)))
    txt = txt.rotate(-90, expand=True)
    im.paste(txt, (mm(w - 1.6), mm(L * 0.42)), txt)
    for label, x in (("1", 0.35), ("14", 5.7)):
        d.text((mm(x), mm(L - 3.1)), label, fill=(240, 238, 230), font=font(mm(0.7)))
    # the contact fingers: a dark cover-lay edge, then plated pads
    d.rectangle([0, mm(L - 2.4), mm(w), mm(L - 2.1)], fill=(60, 36, 8))
    for x in xs:
        d.rectangle([mm(x - 0.17), mm(L - 2.1), mm(x + 0.17), mm(L)], fill=(168, 160, 132))
    md.rectangle([mm(0.5), 0, mm(6.4), mm(1.75)], fill=0)                # under the sticker
    # beside the sticker the flex falls into shadow
    # (display_front_drawn() starts it at the glass edge)
    edge = 1 - FADE_FACE / FADE_LEN
    _fade(im, (0, 0, 0.5, FADE_LEN - FADE_FACE), edge, 0.0, mask)
    _fade(im, (6.4, 0, w, FADE_LEN - FADE_FACE), edge, 0.0, mask)
    for x in xs:                                                         # the plated fingers shine too
        md.rectangle([mm(x - 0.17), mm(L - 2.1), mm(x + 0.17), mm(L)], fill=255)
    flex_drawn.mask = mask.filter(ImageFilter.GaussianBlur(0.5))
    return _grain(im, 4.0, 2).filter(ImageFilter.GaussianBlur(0.5))


def display_front(face=FACE):
    if STYLE == "drawn":
        return display_front_drawn(face)
    w, h = 12.2, 11.0
    im = _photo(MODULE_BOX, (w, h))
    # the thin black seam between the key stem and the glass, so the glass
    # reads as set into the stem
    d = ImageDraw.Draw(im)
    for k in range(mm(SEAM)):
        d.rectangle([k, k, im.width - 1 - k, im.height - 1 - k], outline=(5, 5, 5))
    return im


def flex(length_mm):
    if STYLE == "drawn":
        return flex_drawn(length_mm)
    return _photo(FLEX_BOX, (7.5, length_mm))


def braid(px=512, strands=4):
    """Tileable woven-sleeve height map for bridge_cable.py: two families of
    flat strands at +-45 deg, each made of fibres, crossing two-over-two.
    White = strand crown, black = the gaps between strands. One tile spans
    half the cable's circumference (u) by 6 mm of its length (v)."""
    import numpy as np
    u, v = np.meshgrid(np.arange(px) / px, np.arange(px) / px)
    i, j = (u + v) * strands, (u - v) * strands
    fa, fb = i % 1.0, j % 1.0

    def strand(f):                    # crown across the strand, plus 6 fibres
        return np.sin(np.pi * f) ** 0.6 * (0.8 + 0.2 * np.sin(np.pi * f * 6) ** 2)
    a_on_top = (np.floor(i) + np.floor(j)) % 2 == 0
    h = np.where(a_on_top, 0.35 + 0.65 * strand(fa), 0.35 + 0.65 * strand(fb))
    h *= 0.55 + 0.45 * np.minimum(np.sin(np.pi * fa), np.sin(np.pi * fb)) ** 0.25
    return Image.fromarray((h * 255).clip(0, 255).astype("uint8"), "L")


def main():
    import sys
    sys.path.insert(0, str(HERE.parent / "poly_kybd" / "models"))
    from flex_cable import strip
    *_, length = strip()
    OUT.mkdir(exist_ok=True)
    display_front().save(OUT / "display_front.png", optimize=True)
    display_front(FACE_TOP).save(OUT / "display_front_top.png", optimize=True)
    display_rim().save(OUT / "display_rim.png", optimize=True)
    flex(length).save(OUT / "flex.png", optimize=True)
    if STYLE == "drawn":
        flex_drawn.mask.save(OUT / "flex_traces.png", optimize=True)
    else:       # the drawn traces do not line up with the photo's
        (OUT / "flex_traces.png").unlink(missing_ok=True)
    braid().save(OUT / "braid.png", optimize=True)
    print(f"wrote textures, flex length {length:.2f} mm")


if __name__ == "__main__":
    main()
