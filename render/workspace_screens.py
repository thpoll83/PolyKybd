"""The pictures on the workspace scenes' monitors (render/textures/workspace/).

    python3 render/workspace_screens.py

Drawn with Pillow at 2560 x 1440, generic on purpose (no product's look or name):
- screen_code.jpg: a dark code editor on the firmware's process_record_user()
  (../qmk_firmware/keyboards/polykybd/poly_keymap.c), coloured by token,
- screen_calendar.jpg: a reception's day planner, five rooms by the hour,
- screen_plan.jpg: a CAD floor plan, walls, doors, rooms with their areas, dimensions.
screen_polykybd_org.jpg is the docs site's front page (a Chromium screenshot of
polykybd-docs/dist, served locally) and is not made here.
"""
import os
import re

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "textures", "workspace")
W, H = 2560, 1440
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SRC = os.path.join(HERE, "..", "..", "qmk_firmware", "keyboards", "polykybd", "poly_keymap.c")


def font(path, size):
    return ImageFont.truetype(path, size)


def code():
    bg, panel, gutter = (30, 31, 40), (24, 25, 32), (110, 112, 128)
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 56), fill=(40, 41, 52))                      # title bar and tabs
    d.rectangle((0, 56, 380, H), fill=panel)                             # file tree
    tf = font(SANS, 26)
    for i, name in enumerate(["poly_keymap.c", "config.h", "rules.mk"]):
        x = 400 + i * 300
        d.rectangle((x, 8, x + 290, 56), fill=bg if i == 0 else (40, 41, 52))
        d.text((x + 24, 18), name, font=tf, fill=(220, 222, 235) if i == 0 else gutter)
    for i, name in enumerate(["keyboards", "  polykybd", "    base", "    lang", "    split72",
                              "    poly_keymap.c", "    polykybd.c", "    rules.mk", "  docs"]):
        d.text((24, 90 + i * 44), name, font=tf, fill=(220, 222, 235) if "keymap" in name else gutter)
    lines = open(SRC, encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines) if re.match(r"bool process_record_user\(", l))
    kw = r"\b(?:bool|return|if|else|switch|case|break|const|uint8_t|uint16_t|static|void|true|false|default)\b"
    f = font(MONO, 30)
    y, lh = 80, 42
    for n in range(start, min(start + 31, len(lines))):
        text = lines[n].replace("\t", "    ")
        d.text((420, y), f"{n + 1:5d}", font=f, fill=gutter)
        x = 560
        for tok in re.split(r"(//.*$|\"[^\"]*\"|" + kw + r"|\b[A-Z_][A-Z0-9_]{2,}\b|\w+(?=\())", text):
            if not tok:
                continue
            col = (205, 214, 244)
            if tok.startswith("//"):
                col = (108, 112, 134)
            elif tok.startswith('"'):
                col = (166, 227, 161)
            elif re.fullmatch(kw, tok):
                col = (203, 166, 247)
            elif re.fullmatch(r"[A-Z_][A-Z0-9_]{2,}", tok):
                col = (250, 179, 135)
            elif re.fullmatch(r"\w+", tok) and text[text.find(tok) + len(tok):][:1] == "(":
                col = (137, 180, 250)
            d.text((x, y), tok, font=f, fill=col)
            x += d.textlength(tok, font=f)
        y += lh
    d.rectangle((0, H - 44, W, H), fill=(60, 56, 140))                   # status bar
    d.text((24, H - 38), "PolyKybd  ·  main  ·  UTF-8  ·  C", font=font(SANS, 24), fill=(235, 235, 245))
    return im


def calendar():
    im = Image.new("RGB", (W, H), (246, 247, 250))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=(255, 255, 255))
    d.text((60, 30), "Reception  ·  Thursday", font=font(BOLD, 48), fill=(30, 34, 48))
    d.text((W - 520, 42), "Today    Week    Month", font=font(SANS, 32), fill=(110, 116, 132))
    rooms = ["Lobby desk", "Meeting room 1", "Meeting room 2", "Studio", "Visitors"]
    x0, y0, cw, rh = 230, 190, (W - 290) // 5, 112
    for i, r in enumerate(rooms):
        d.text((x0 + i * cw + 20, 135), r, font=font(BOLD, 30), fill=(60, 66, 84))
    for h in range(8, 19):
        y = y0 + (h - 8) * rh
        d.line((x0, y, W - 60, y), fill=(222, 225, 232), width=2)
        d.text((80, y - 16), f"{h:02d}:00", font=font(SANS, 28), fill=(130, 136, 150))
    events = [(0, 8.0, 9.0, "Front desk opens", (90, 143, 230)), (0, 12.0, 13.0, "Courier pick-up", (240, 170, 70)),
              (1, 9.0, 10.5, "Weekly planning", (120, 190, 120)), (1, 14.0, 15.5, "Client review", (200, 120, 200)),
              (2, 10.0, 11.0, "Interview", (90, 180, 200)), (2, 15.0, 17.0, "Workshop", (230, 120, 110)),
              (3, 8.5, 12.0, "Photo session", (160, 140, 230)), (4, 9.5, 10.0, "Visitor: delivery", (240, 170, 70)),
              (4, 13.0, 14.0, "Visitor: site tour", (120, 190, 120)), (3, 13.5, 16.0, "Model build", (90, 143, 230))]
    for col, a, b, title, rgb in events:
        x = x0 + col * cw + 10
        ya, yb = y0 + (a - 8) * rh + 4, y0 + (b - 8) * rh - 4
        d.rounded_rectangle((x, ya, x + cw - 20, yb), radius=14, fill=tuple(int(c * 0.35 + 255 * 0.65) for c in rgb),
                            outline=rgb, width=3)
        d.rectangle((x, ya, x + 8, yb), fill=rgb)
        d.text((x + 26, ya + 14), title, font=font(BOLD, 28), fill=(30, 34, 48))
        d.text((x + 26, ya + 52), f"{int(a):02d}:{int(a % 1 * 60):02d} – {int(b):02d}:{int(b % 1 * 60):02d}",
               font=font(SANS, 24), fill=(80, 86, 100))
    y = y0 + 6.4 * rh                                                    # now
    d.line((x0, y, W - 60, y), fill=(230, 70, 70), width=4)
    d.ellipse((x0 - 10, y - 10, x0 + 10, y + 10), fill=(230, 70, 70))
    return im


def plan():
    im = Image.new("RGB", (W, H), (236, 238, 242))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 64), fill=(52, 58, 70))                        # menu bar
    d.text((24, 16), "File   Edit   View   Draw   Dimension   Layers   Window", font=font(SANS, 26), fill=(220, 224, 232))
    d.rectangle((0, 64, 90, H), fill=(62, 68, 80))                       # tool strip
    for i in range(14):
        d.rounded_rectangle((18, 90 + i * 70, 72, 144 + i * 70), radius=8, outline=(150, 156, 170), width=2)
    d.rectangle((W - 420, 64, W, H), fill=(248, 249, 251))               # layers panel
    d.text((W - 390, 90), "Layers", font=font(BOLD, 30), fill=(40, 44, 56))
    for i, (name, rgb) in enumerate([("Walls", (30, 30, 30)), ("Doors", (60, 120, 200)), ("Furniture", (120, 160, 90)),
                                      ("Dimensions", (200, 90, 60)), ("Text", (90, 90, 90))]):
        d.rectangle((W - 390, 150 + i * 56, W - 360, 180 + i * 56), fill=rgb)
        d.text((W - 340, 148 + i * 56), name, font=font(SANS, 28), fill=(60, 64, 76))
    s = 110                                                              # px per metre
    ox, oy = 260, 220
    wall = (28, 28, 30)

    def wl(x1, y1, x2, y2, t=0.24):
        d.rectangle((ox + min(x1, x2) * s - t * s / 2, oy + min(y1, y2) * s - t * s / 2,
                     ox + max(x1, x2) * s + t * s / 2, oy + max(y1, y2) * s + t * s / 2), fill=wall)
    wl(0, 0, 16, 0); wl(0, 9.5, 16, 9.5); wl(0, 0, 0, 9.5); wl(16, 0, 16, 9.5)
    wl(6, 0, 6, 5.5, 0.12); wl(6, 5.5, 16, 5.5, 0.12); wl(11, 0, 11, 5.5, 0.12); wl(6, 7.2, 6, 9.5, 0.12)
    for (cx, cy, r, a0, a1) in [(6, 6.3, 0.9, 270, 360), (8.2, 5.5, 0.9, 180, 270), (13.2, 5.5, 0.9, 180, 270)]:
        d.arc((ox + (cx - r) * s, oy + (cy - r) * s, ox + (cx + r) * s, oy + (cy + r) * s), a0, a1,
              fill=(60, 120, 200), width=3)
    for cx, cy, name, area in [(3, 4.7, "Studio", "57.0 m²"), (8.5, 2.7, "Office 1", "27.5 m²"),
                               (13.5, 2.7, "Office 2", "27.5 m²"), (11, 7.5, "Meeting", "40.0 m²")]:
        d.text((ox + cx * s - 80, oy + cy * s - 30), name, font=font(BOLD, 34), fill=(40, 44, 56))
        d.text((ox + cx * s - 70, oy + cy * s + 14), area, font=font(SANS, 28), fill=(90, 96, 110))
    for i in range(4):                                                   # desks in the studio
        d.rectangle((ox + (0.8 + i * 1.3) * s, oy + 1.0 * s, ox + (1.9 + i * 1.3) * s, oy + 1.8 * s),
                    outline=(120, 160, 90), width=3)
    d.ellipse((ox + 9.7 * s, oy + 6.6 * s, ox + 12.3 * s, oy + 8.4 * s), outline=(120, 160, 90), width=3)
    dim = (200, 90, 60)
    y = oy + 10.4 * s
    d.line((ox, y, ox + 16 * s, y), fill=dim, width=2)
    for x in (0, 6, 11, 16):
        d.line((ox + x * s, y - 14, ox + x * s, y + 14), fill=dim, width=2)
    for a, b, t in [(0, 6, "6.00"), (6, 11, "5.00"), (11, 16, "5.00")]:
        d.text((ox + (a + b) / 2 * s - 34, y - 46), t, font=font(SANS, 28), fill=dim)
    d.rectangle((0, H - 44, W, H), fill=(52, 58, 70))
    d.text((24, H - 38), "Model   Layout 1   Layout 2          1:100   Snap  Grid  Ortho", font=font(SANS, 24),
           fill=(220, 224, 232))
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("screen_code.jpg", code), ("screen_calendar.jpg", calendar), ("screen_plan.jpg", plan)):
        fn().save(os.path.join(OUT, name), quality=88)
        print("wrote", os.path.join("render", "textures", "workspace", name))
