"""The pictures on the workspace scenes' monitors (render/textures/workspace/).

    python3 render/workspace_screens.py

Drawn with Pillow at 2560 x 1440, generic on purpose (no product's look or name):
- screen_code.jpg: a dark code editor on the firmware's process_record_user()
  (../qmk_firmware/keyboards/polykybd/poly_keymap.c), coloured by token,
- screen_calendar.jpg: a reception's day planner, five rooms by the hour,
- screen_plan.jpg: a CAD floor plan, walls, doors, rooms with their areas, dimensions,
- screen_design.jpg: a vector illustration app with a poster in progress,
- screen_game.jpg: a made-up synthwave racing game with its HUD.
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


def design():
    """A vector illustration app: a dark frame, a canvas with a poster in progress (sun,
    hills, type), a layers list and a colour palette."""
    import math
    im = Image.new("RGB", (W, H), (38, 38, 42))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 60), fill=(28, 28, 31))
    d.text((24, 16), "File  Edit  Object  Type  Select  Effect  View  Window", font=font(SANS, 26), fill=(200, 200, 208))
    d.rectangle((0, 60, 84, H), fill=(30, 30, 34))
    for i in range(12):
        d.rounded_rectangle((18, 84 + i * 66, 66, 132 + i * 66), radius=8, fill=(52, 52, 58))
    d.rectangle((W - 460, 60, W, H), fill=(30, 30, 34))
    cx0, cy0, cx1, cy1 = 300, 140, W - 640, H - 120     # the artboard
    d.rectangle((cx0, cy0, cx1, cy1), fill=(250, 236, 214))
    sky = [(255, 196, 140), (250, 160, 130), (230, 120, 140)]
    hgt = (cy1 - cy0) * 0.62
    for i in range(int(hgt)):
        t = i / hgt
        c = tuple(int(sky[0][k] + (sky[2][k] - sky[0][k]) * t) for k in range(3))
        d.line((cx0, cy0 + i, cx1, cy0 + i), fill=c)
    sx, sy, r = (cx0 + cx1) // 2, int(cy0 + hgt * 0.62), 210
    d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(255, 238, 170))
    for j, (col, amp, base) in enumerate([((120, 80, 140), 60, 0.60), ((80, 60, 120), 80, 0.70), ((50, 40, 90), 50, 0.82)]):
        pts = [(cx0, cy1)]
        for x in range(cx0, cx1 + 1, 20):
            pts.append((x, cy0 + (cy1 - cy0) * base - amp * math.sin((x - cx0) / (170 + 40 * j) + j)))
        pts.append((cx1, cy1))
        d.polygon(pts, fill=col)
    d.text((cx0 + 90, cy1 - 230), "SUMMER", font=font(BOLD, 150), fill=(250, 236, 214))
    d.text((cx0 + 96, cy1 - 70), "open air  ·  friday", font=font(SANS, 44), fill=(250, 236, 214))
    d.rectangle((sx - r - 6, sy - r - 6, sx + r + 6, sy + r + 6), outline=(60, 140, 255), width=3)   # selection
    for qx, qy in ((sx - r - 6, sy - r - 6), (sx + r + 6, sy - r - 6), (sx - r - 6, sy + r + 6), (sx + r + 6, sy + r + 6)):
        d.rectangle((qx - 8, qy - 8, qx + 8, qy + 8), fill=(255, 255, 255), outline=(60, 140, 255), width=3)
    d.text((W - 430, 84), "Layers", font=font(BOLD, 30), fill=(220, 220, 228))
    for i, name in enumerate(["Type", "Sun", "Hills front", "Hills middle", "Hills back", "Sky", "Paper"]):
        y = 140 + i * 58
        d.rectangle((W - 440, y, W - 20, y + 50), fill=(52, 52, 60) if name == "Sun" else (36, 36, 40))
        d.text((W - 410, y + 10), name, font=font(SANS, 28), fill=(220, 220, 228))
    d.text((W - 430, 600), "Swatches", font=font(BOLD, 30), fill=(220, 220, 228))
    sw = [(255, 196, 140), (250, 160, 130), (230, 120, 140), (255, 238, 170), (120, 80, 140), (80, 60, 120),
          (50, 40, 90), (250, 236, 214), (60, 140, 255), (40, 40, 44), (120, 200, 160), (240, 90, 80)]
    for i, c in enumerate(sw):
        x, y = W - 430 + (i % 6) * 68, 660 + (i // 6) * 68
        d.rounded_rectangle((x, y, x + 56, y + 56), radius=8, fill=c)
    return im


def game():
    """A made-up racing game: a synthwave road to a striped sun, a neon grid, a speed
    gauge and a lap counter (no real game's look or name)."""
    import math
    im = Image.new("RGB", (W, H), (10, 6, 30))
    d = ImageDraw.Draw(im)
    hz = int(H * 0.52)
    for i in range(hz):                                  # the sky
        t = i / hz
        d.line((0, i, W, i), fill=(int(20 + 120 * t), int(8 + 20 * t), int(60 + 70 * t)))
    sx, sy, r = W // 2, hz - 40, 330
    for i in range(r * 2):                               # the striped sun
        y = sy - r + i
        if y > hz or (i > r * 0.9 and (i // 22) % 2):
            continue
        w = math.sqrt(max(0, r * r - (i - r) ** 2))
        t = i / (2 * r)
        d.line((sx - w, y, sx + w, y), fill=(255, int(220 - 140 * t), int(80 + 60 * t)))
    for k in range(9):                                   # mountains
        x0 = k * W / 8 - 160
        d.polygon([(x0, hz), (x0 + 160, hz - 90 - 50 * (k % 3)), (x0 + 320, hz)], fill=(40, 10, 70))
    d.rectangle((0, hz, W, H), fill=(14, 4, 34))
    for j in range(1, 24):                               # the grid, in perspective
        y = hz + (H - hz) * (j / 24) ** 1.8
        d.line((0, y, W, y), fill=(255, 40, 200), width=2)
    for k in range(-20, 21):
        d.line((sx + k * 30, hz, sx + k * 260, H), fill=(255, 40, 200), width=2)
    d.polygon([(sx - 40, hz), (sx + 40, hz), (sx + 700, H), (sx - 700, H)], fill=(24, 10, 44))
    for j in range(12):                                  # the road's centre line
        t0, t1 = j / 12, (j + 0.5) / 12
        y0, y1 = hz + (H - hz) * t0 ** 1.6, hz + (H - hz) * t1 ** 1.6
        d.polygon([(sx - 2 - 20 * t0, y0), (sx + 2 + 20 * t0, y0), (sx + 2 + 20 * t1, y1), (sx - 2 - 20 * t1, y1)],
                  fill=(255, 230, 120))
    car = [(sx - 230, H - 120), (sx + 230, H - 120), (sx + 190, H - 260), (sx - 190, H - 260)]
    d.polygon(car, fill=(30, 230, 255))
    d.rectangle((sx - 150, H - 330, sx + 150, H - 260), fill=(20, 140, 200))
    d.rectangle((sx - 220, H - 150, sx - 140, H - 120), fill=(255, 60, 90))
    d.rectangle((sx + 140, H - 150, sx + 220, H - 120), fill=(255, 60, 90))
    d.arc((W - 420, H - 420, W - 60, H - 60), 140, 400, fill=(80, 80, 120), width=24)        # gauge
    d.arc((W - 420, H - 420, W - 60, H - 60), 140, 330, fill=(30, 230, 255), width=24)
    d.text((W - 330, H - 280), "248", font=font(BOLD, 110), fill=(255, 255, 255))
    d.text((W - 300, H - 160), "km/h", font=font(SANS, 40), fill=(180, 180, 220))
    d.text((60, 50), "LAP 2/3", font=font(BOLD, 64), fill=(255, 255, 255))
    d.text((60, 130), "POS 1", font=font(BOLD, 64), fill=(255, 230, 120))
    d.text((W - 380, 50), "01:12.48", font=font(BOLD, 64), fill=(255, 255, 255))
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("screen_code.jpg", code), ("screen_calendar.jpg", calendar), ("screen_plan.jpg", plan),
                     ("screen_design.jpg", design), ("screen_game.jpg", game)):
        fn().save(os.path.join(OUT, name), quality=88)
        print("wrote", os.path.join("render", "textures", "workspace", name))
