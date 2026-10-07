"""Draw the keycap display and flex-cable textures (Pillow).

    python render/gen_textures.py        -> render/textures/{display_front,flex,braid}.png

(numpy + Pillow; Blender's bundled python has both.)

Both are drawn from a photo of the real part (FPT042000Z05_V2, 0.42" OLED):

- display_front.png covers the top face of keycap_display.wrl as placed on a
  key: 12.2 mm across (x) by 11.0 mm (y), the cable side at the BOTTOM of the
  image (-y on the key). Clear glass border, the black tape over the bond
  area on the cable side, then the active area: deep navy, unlit.
- flex.png is mapped by flex_cable.strip()'s uv: u across the 7.5 mm width,
  v along the strip from the display (top of the image) to the connector
  (bottom). Amber polyimide, 14 copper traces that fan out near the display,
  the part number, gold contact fingers at the connector end.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "textures"
PX_PER_MM = 80


def font(size):
    for f in ("DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


def mm(v):
    return int(round(v * PX_PER_MM))


def display_front():
    w, h = 12.2, 11.0
    im = Image.new("RGB", (mm(w), mm(h)), (150, 156, 160))         # glass edge, seen over the holder
    d = ImageDraw.Draw(im)
    d.rectangle([mm(0.25), mm(0.25), mm(w - 0.25), mm(h - 0.25)], fill=(70, 74, 78))  # glass body
    # black tape over the driver bond, cable side (bottom of the image)
    d.rectangle([mm(0.6), mm(h - 3.0), mm(w - 0.6), mm(h - 0.5)], fill=(14, 14, 15))
    # panel frame and the active area (72 x 40 px, ~9.2 x 5.1 mm), centred above the tape
    ax0, ay0 = (w - 9.2) / 2, 1.35
    d.rectangle([mm(ax0 - 0.55), mm(ay0 - 0.55), mm(ax0 + 9.2 + 0.55), mm(ay0 + 5.1 + 0.55)],
                fill=(10, 10, 12))
    d.rectangle([mm(ax0), mm(ay0), mm(ax0 + 9.2), mm(ay0 + 5.1)], fill=(14, 16, 40))
    # the faint printed lot number on the tape, as on the real part
    d.text((mm(w / 2), mm(h - 1.75)), "2305054", fill=(40, 40, 42), font=font(mm(0.7)), anchor="mm")
    return im.filter(ImageFilter.GaussianBlur(0.6))


def flex(length_mm):
    w = 7.5
    im = Image.new("RGB", (mm(w), mm(length_mm)), (196, 120, 18))   # polyimide
    d = ImageDraw.Draw(im)
    n, pitch = 14, 0.5
    fan_end = 3.0                                                   # traces fan out over the first 3 mm
    for i in range(n):
        x_conn = (w - (n - 1) * pitch) / 2 + i * pitch
        x_disp = 0.45 + i * (w - 0.9) / (n - 1)
        d.line([(mm(x_disp), 0), (mm(x_conn), mm(fan_end))], fill=(160, 88, 12), width=mm(0.11))
        d.line([(mm(x_conn), mm(fan_end)), (mm(x_conn), mm(length_mm))], fill=(160, 88, 12), width=mm(0.11))
        # gold fingers, the last 2.5 mm into the connector
        d.rectangle([mm(x_conn - 0.15), mm(length_mm - 2.5), mm(x_conn + 0.15), mm(length_mm)],
                    fill=(212, 178, 92))
    # part number along the strip, white print
    txt = Image.new("RGBA", (mm(length_mm * 0.6), mm(1.0)), (0, 0, 0, 0))
    ImageDraw.Draw(txt).text((0, 0), "FPT042000Z05_V2", fill=(245, 245, 240, 255), font=font(mm(0.7)))
    txt = txt.rotate(-90, expand=True)
    im.paste(txt, (mm(0.6), mm(length_mm * 0.35)), txt)
    return im.filter(ImageFilter.GaussianBlur(0.5))


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
    flex(length).save(OUT / "flex.png", optimize=True)
    braid().save(OUT / "braid.png", optimize=True)
    print(f"wrote textures, flex length {length:.2f} mm")


if __name__ == "__main__":
    main()
