"""The pictures on the workspace scenes' monitors (render/textures/workspace/).

    python3 render/workspace_screens.py

Drawn with Pillow at 2560 x 1440, generic on purpose (no product's look or name):
- screen_code.jpg: a dark code editor on the firmware's process_record_user()
  (../qmk_firmware/keyboards/polykybd/poly_keymap.c), coloured by token,
- screen_calendar.jpg: a reception's day planner, five rooms by the hour,
- screen_sheet.jpg: a spreadsheet, quarterly figures with a chart; screen_mail.jpg: an inbox
  beside an open message,
- screen_plan.jpg: a CAD floor plan, walls, doors, rooms with their areas, dimensions,
- screen_design.jpg: a vector illustration app with a poster in progress,
- screen_game.jpg: a made-up synthwave racing game with its HUD,
- ruler.jpg: a steel rule's millimetre scale, poster_road.jpg: the game's road as a poster,
- the office wall: cork.jpg (a pinboard's cork), paper_layout.jpg (a keymap sketch),
  paper_sprint.jpg (a week's task list), paper_chart.jpg (a bar chart printout),
  paper_month.jpg (a month calendar), photo_keyboard.jpg (a print of the docs page's
  photo), sticky_<colour>.jpg (sticky notes), clock_face.jpg (a wall clock's dial),
  print_<name>.jpg (photo prints of pictures from polykybd-docs/src/assets, DOC_PRINTS),
  paper_schematic.jpg (the left half's schematic on A4).
wall_scuff.png: rub marks and scratches where cables go down behind a desk;
notepad_writing.png: pen notes for the notepad's top page, some struck through
(transparent, laid over the pad as a decal); mat_topo.jpg: a desk mat's print, topographic contour lines on charcoal.
The calendar's photo is a crop of Poly Haven's bell_park_pier (CC0): a lake and hills at dusk,
fetched by workspace_assets.py.
screen_polykybd_org.jpg is the docs site's front page (a Chromium screenshot of
polykybd-docs/dist, served locally) and is not made here.
"""
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
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


def sheet_full():
    """A spreadsheet app at 3840 x 2160 (a 30-inch 4K panel at 100 % scaling, so the
    type is as small as on a real one): ribbon, formula bar, a budget table by month
    with totals, two charts beside it, sheet tabs at the bottom."""
    import random
    rnd = random.Random(8)
    W4, H4 = 3840, 2160
    im = Image.new("RGB", (W4, H4), (255, 255, 255))
    d = ImageDraw.Draw(im)
    green = (33, 115, 70)
    f, fb = font(SANS, 24), font(BOLD, 24)
    d.rectangle((0, 0, W4, 56), fill=green)
    d.text((30, 12), "Budget 2026.xlsx  -  Saved", font=font(BOLD, 28), fill=(255, 255, 255))
    for k, t in enumerate(["File", "Home", "Insert", "Page Layout", "Formulas", "Data", "Review", "View", "Help"]):
        d.text((700 + k * 210, 15), t, font=font(SANS, 26), fill=(230, 245, 235))
    d.rectangle((0, 56, W4, 150), fill=(243, 243, 243))
    for k in range(34):
        x = 30 + k * 88
        d.rounded_rectangle((x, 72, x + 66, 134), 6, fill=(230, 230, 230), outline=(208, 208, 208))
    d.rectangle((0, 150, W4, 196), fill=(255, 255, 255))
    d.text((30, 160), "P26", font=f, fill=(60, 60, 60))
    d.text((170, 160), "fx   =SUM(P4:P25)", font=font(MONO, 24), fill=(60, 60, 60))
    d.line((0, 196, W4, 196), fill=(200, 200, 200), width=2)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    head = ["Cost centre"] + months + ["Total", "Plan", "Δ %"]
    cw = [250] + [118] * 12 + [140, 140, 100]
    x0, y0, rh = 56, 236, 40
    xs = [x0]
    for w_ in cw:
        xs.append(xs[-1] + w_)
    d.rectangle((0, 196, W4, 236), fill=(240, 240, 240))
    for i in range(len(cw) + 6):
        xc = xs[i] if i < len(xs) else xs[-1] + (i - len(xs) + 1) * 118
        d.text((xc + 50, 202), chr(65 + i), font=font(SANS, 22), fill=(100, 100, 100))
    names = ["Hardware", "Software licences", "Cloud services", "Office supplies", "Furniture", "Travel",
             "Training", "Conferences", "Facilities", "Cleaning", "Energy", "Marketing", "Print", "Contractors",
             "Recruiting", "Shipping", "Insurance", "Phones", "Catering", "Team events", "Misc."]
    nrows = (H4 - 60 - y0) // rh
    for r in range(nrows):
        y = y0 + r * rh
        d.rectangle((0, y, x0, y + rh), fill=(240, 240, 240))
        d.text((10, y + 8), str(r + 1), font=font(SANS, 20), fill=(110, 110, 110))
        d.line((x0, y + rh, 2300, y + rh), fill=(228, 228, 228), width=1)
    for xv in xs:
        d.line((xv, y0, xv, y0 + nrows * rh), fill=(228, 228, 228), width=1)
    d.text((xs[0] + 10, y0 + 8), "Department budget 2026, EUR", font=font(BOLD, 26), fill=(30, 30, 30))
    for i, t in enumerate(head):
        d.rectangle((xs[i], y0 + 2 * rh, xs[i + 1], y0 + 3 * rh), fill=(226, 239, 218))
        d.text((xs[i] + 10, y0 + 2 * rh + 8), t, font=fb, fill=(30, 30, 30))

    def num(i, y, v, bold=False, col=(30, 30, 30)):
        t = v if isinstance(v, str) else f"{v:,}"
        ff = fb if bold else f
        d.text((xs[i + 1] - 10 - d.textlength(t, font=ff), y), t, font=ff, fill=col)
    tot = [0] * 14
    for r, n in enumerate(names):
        y = y0 + (r + 3) * rh + 8
        vals = [rnd.randint(2, 48) * 50 for _ in range(12)]
        plan_ = int(sum(vals) * rnd.uniform(0.85, 1.15) / 100) * 100
        d.text((xs[0] + 10, y), n, font=f, fill=(30, 30, 30))
        for k, v in enumerate(vals + [sum(vals), plan_]):
            num(k + 1, y, v)
            tot[k] += v
        pct = (sum(vals) / plan_ - 1) * 100
        num(15, y, f"{pct:+.1f}", col=(40, 140, 60) if pct <= 0 else (200, 50, 40))
    y = y0 + (len(names) + 3) * rh
    d.rectangle((xs[0], y, xs[-1], y + rh), fill=(245, 245, 245))
    d.text((xs[0] + 10, y + 8), "Total", font=fb, fill=(30, 30, 30))
    for k, v in enumerate(tot):
        num(k + 1, y + 8, v, bold=True)
    d.rectangle((xs[13], y, xs[14], y + rh), outline=green, width=3)
    cx0 = 2420                                                     # two charts to the right
    for c, (title, ty) in enumerate((("Spend by month", 260), ("Top cost centres", 1180))):
        cy0, cy1 = ty, ty + 820
        d.rectangle((cx0, cy0, W4 - 80, cy1), fill=(255, 255, 255), outline=(200, 200, 200), width=2)
        d.text((cx0 + 24, cy0 + 16), title, font=font(BOLD, 28), fill=(40, 40, 40))
        if c == 0:
            mx = max(tot[:12])
            for k in range(12):
                bh = (cy1 - cy0 - 150) * tot[k] / mx
                bx = cx0 + 70 + k * 108
                d.rectangle((bx, cy1 - 56 - bh, bx + 70, cy1 - 56), fill=(68, 114, 196))
                d.text((bx + 12, cy1 - 46), months[k], font=font(SANS, 20), fill=(80, 80, 80))
        else:
            for k in range(8):
                bw = rnd.randint(300, 1100)
                yy = cy0 + 90 + k * 86
                d.text((cx0 + 30, yy + 10), names[k], font=font(SANS, 22), fill=(60, 60, 60))
                d.rectangle((cx0 + 280, yy, cx0 + 280 + bw, yy + 52), fill=(237, 125, 49))
    d.rectangle((0, H4 - 50, W4, H4), fill=(240, 240, 240))
    for k, t in enumerate(["Summary", "By month", "Travel", "Plan vs. actual", "+"]):
        x = 30 + k * 240
        if k == 0:
            d.rectangle((x - 10, H4 - 50, x + 200, H4), fill=(255, 255, 255))
        d.text((x, H4 - 40), t, font=fb if k == 0 else f, fill=green if k == 0 else (90, 90, 90))
    return im


def mail_full():
    """A mail client at 3840 x 2160 (30-inch 4K, 100 % scaling): folders, a long inbox
    list (some unread, one selected) and the open message beside it."""
    W4, H4 = 3840, 2160
    im = Image.new("RGB", (W4, H4), (255, 255, 255))
    d = ImageDraw.Draw(im)
    blue = (0, 95, 184)
    d.rectangle((0, 0, W4, 64), fill=blue)
    d.text((30, 14), "Mail", font=font(BOLD, 32), fill=(255, 255, 255))
    d.rounded_rectangle((1100, 12, 2400, 52), 20, fill=(230, 240, 250))
    d.text((1130, 18), "Search mail", font=font(SANS, 24), fill=(110, 120, 135))
    d.rectangle((0, 64, 330, H4), fill=(243, 245, 248))
    d.rounded_rectangle((24, 90, 300, 146), 10, fill=blue)
    d.text((70, 102), "New mail", font=font(BOLD, 26), fill=(255, 255, 255))
    folders = [("Inbox", "4"), ("Drafts", "1"), ("Sent", ""), ("Scheduled", ""), ("Archive", ""), ("Junk", "12"),
               ("Deleted", ""), ("", ""), ("Projects", ""), ("  Budget 2026", ""), ("  Office move", ""), ("Invoices", ""),
               ("Travel", ""), ("Newsletters", "7")]
    for k, (t, n) in enumerate(folders):
        y = 180 + k * 58
        if k == 0:
            d.rounded_rectangle((16, y - 10, 314, y + 42), 8, fill=(222, 232, 245))
        d.text((44, y), t, font=font(BOLD if k == 0 else SANS, 26), fill=(40, 44, 56))
        if n:
            d.text((280, y), n, font=font(BOLD, 24), fill=blue)
    mails = [("Anna Weber", "Re: Q4 budget draft", "Thanks, the numbers look good. One question on travel…", "09:41", True),
             ("IT Service Desk", "VPN certificate renewal", "Your certificate expires on Friday. Please…", "09:12", True),
             ("Facilities", "Desk move, 3rd floor", "The movers come on Tuesday at 8:00. Please pack…", "08:55", True),
             ("Marco Rossi", "Release review agenda", "Attached is the agenda for Thursday. Please add…", "08:30", True),
             ("Jonas K.", "Team lunch Thursday", "Table for 8 at 12:30 is booked. Who is in?", "Yesterday", False),
             ("Supplier GmbH", "Order 44812 shipped", "Your order of USB-C cables has shipped and will…", "Yesterday", False),
             ("Lena Hofmann", "Onboarding doc", "I added the new section on accounts. Can you…", "Yesterday", False),
             ("HR", "Holiday planning 2027", "Please enter your planned holidays by the end of…", "Tue", False),
             ("Calendar", "Accepted: Release review", "Marco accepted your invitation for Thu 14:00", "Mon", False),
             ("Sara Lind", "Photos from the offsite", "Here is the link to the album. Some great ones…", "Mon", False),
             ("Accounting", "Expense report approved", "Your report for September (EUR 214.80) was…", "Mon", False),
             ("Building", "Fire drill on Wednesday", "There will be a fire drill at 10:00. Please…", "Sun", False),
             ("Newsletter", "October update", "What's new this month: the new canteen menu…", "Sun", False),
             ("Tom B.", "Re: keyboard layouts", "The split one works great, my wrists thank you…", "Sat", False),
             ("Delivery", "Your parcel is on its way", "Expected delivery: Monday between 10 and 14…", "Fri", False),
             ("Anna Weber", "Q3 numbers", "Final numbers for Q3 are in the shared folder…", "Fri", False),
             ("IT Service Desk", "Patch day", "Updates will be installed tonight after 20:00…", "Thu", False)]
    x0, x1 = 330, 1500
    for k, (who, subj, prev, when, unread) in enumerate(mails):
        y = 80 + k * 120
        if y + 120 > H4:
            break
        if k == 0:
            d.rectangle((x0, y, x1, y + 120), fill=(222, 232, 245))
            d.rectangle((x0, y, x0 + 6, y + 120), fill=blue)
        d.text((x0 + 34, y + 12), who, font=font(BOLD if unread else SANS, 26), fill=(30, 34, 46))
        d.text((x1 - 30 - d.textlength(when, font=font(SANS, 22)), y + 16), when, font=font(SANS, 22), fill=(110, 116, 130))
        d.text((x0 + 34, y + 48), subj, font=font(BOLD if unread else SANS, 24), fill=blue if unread else (50, 54, 66))
        d.text((x0 + 34, y + 82), prev, font=font(SANS, 22), fill=(120, 126, 140))
        d.line((x0, y + 120, x1, y + 120), fill=(225, 228, 234), width=2)
    d.line((x1, 64, x1, H4), fill=(210, 214, 222), width=2)
    x = x1 + 80
    d.text((x, 110), "Re: Q4 budget draft", font=font(BOLD, 40), fill=(30, 34, 46))
    d.ellipse((x, 190, x + 70, 260), fill=(200, 120, 90))
    d.text((x + 18, 204), "AW", font=font(BOLD, 26), fill=(255, 255, 255))
    d.text((x + 96, 192), "Anna Weber", font=font(BOLD, 28), fill=(30, 34, 46))
    d.text((x + 96, 230), "to me, Marco Rossi  ·  Today 09:41", font=font(SANS, 22), fill=(110, 116, 130))
    body = ["Hi,", "", "thanks for the draft. The numbers look good overall.",
            "One question on travel: Q3 is about 20 % over plan,", "is that the trade fair in September?", "",
            "Could you add a short note to the summary sheet", "before Thursday's review? Marco will present the",
            "plan-vs-actual chart, so the notes should match it.", "", "Thanks,", "Anna", "",
            "———", "On Wed, Marco Rossi wrote:", "> Draft is in the shared folder, please have a look", "> before Friday."]
    for k, line in enumerate(body):
        d.text((x, 320 + k * 46), line, font=font(SANS, 28), fill=(40, 44, 56) if not line.startswith(">") else (110, 116, 130))
    d.rounded_rectangle((x, 1160, x + 280, 1220), 8, outline=(190, 196, 206), width=2)
    d.text((x + 26, 1174), "Budget 2026.xlsx", font=font(SANS, 24), fill=(33, 115, 70))
    for k, t in enumerate(["Reply", "Reply all", "Forward"]):
        bx = x + k * 220
        d.rounded_rectangle((bx, 1300, bx + 190, 1360), 10, fill=blue if k == 0 else (235, 238, 244))
        d.text((bx + 30, 1314), t, font=font(BOLD if k == 0 else SANS, 26), fill=(255, 255, 255) if k == 0 else (40, 44, 56))
    return im


def window(base, content, x, y, w, title, accent=(60, 64, 76)):
    """Paste content (an Image) onto base as an app window at (x, y), w wide: a soft drop
    shadow, a title bar with the title and three window buttons, a thin border."""
    from PIL import ImageFilter
    h = int(content.height * w / content.width)
    bar = 44
    sh = Image.new("L", base.size, 0)
    ImageDraw.Draw(sh).rectangle((x + 10, y + 18, x + w + 10, y + h + bar + 18), fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    base.paste((0, 0, 0), (0, 0), sh)
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w, y + bar), fill=accent)
    d.text((x + 20, y + 8), title, font=font(SANS, 24), fill=(240, 240, 240))
    for k, c in enumerate(("-", "o", "x")):
        d.text((x + w - 150 + k * 50, y + 6), c, font=font(SANS, 26), fill=(230, 230, 230))
    base.paste(content.convert("RGB").resize((w, h), Image.LANCZOS), (x, y + bar))
    d.rectangle((x, y, x + w, y + h + bar), outline=(120, 124, 134), width=2)
    return base


def chat():
    """A team chat: channels on the left, a thread of short messages, a reply box."""
    im = Image.new("RGB", (1400, 1100), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 330, 1100), fill=(50, 48, 76))
    for k, t in enumerate(["# general", "# office-move", "# budget-2026", "# random", "", "Anna Weber", "Marco Rossi", "Jonas K."]):
        if k == 2:
            d.rectangle((0, 90 + k * 64 - 12, 330, 90 + k * 64 + 44), fill=(90, 86, 130))
        d.text((30, 90 + k * 64), t, font=font(BOLD if k == 2 else SANS, 28), fill=(235, 232, 245))
    d.text((370, 30), "# budget-2026", font=font(BOLD, 34), fill=(30, 30, 40))
    d.line((330, 90, 1400, 90), fill=(225, 225, 232), width=2)
    msgs = [("Marco Rossi", "10:02", "Review moved to 14:00 on Thursday", (90, 140, 210)),
            ("Anna Weber", "10:05", "ok! can someone check the travel line?", (200, 120, 90)),
            ("Jonas K.", "10:07", "Q3 is the trade fair, I'll add a note", (110, 170, 110)),
            ("Anna Weber", "10:08", "thanks :)", (200, 120, 90)),
            ("Lena Hofmann", "10:15", "who has the projector adapter?", (180, 110, 180))]
    for k, (who, t, msg, col) in enumerate(msgs):
        y = 130 + k * 170
        d.ellipse((370, y, 440, y + 70), fill=col)
        d.text((390, y + 16), who[0], font=font(BOLD, 32), fill=(255, 255, 255))
        d.text((470, y), who, font=font(BOLD, 28), fill=(30, 30, 40))
        d.text((470 + d.textlength(who, font=font(BOLD, 28)) + 20, y + 4), t, font=font(SANS, 24), fill=(130, 130, 140))
        d.text((470, y + 44), msg, font=font(SANS, 28), fill=(40, 40, 50))
    d.rounded_rectangle((370, 980, 1360, 1060), 12, outline=(200, 200, 210), width=2)
    d.text((400, 1004), "Message #budget-2026", font=font(SANS, 26), fill=(150, 150, 160))
    return im


def toast(base, x, y, title, line):
    """A system notification card at (x, y)."""
    from PIL import ImageFilter
    w, h = 620, 150
    sh = Image.new("L", base.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((x + 6, y + 10, x + w + 6, y + h + 10), 14, fill=110)
    base.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((x, y, x + w, y + h), 14, fill=(250, 250, 252), outline=(210, 212, 220), width=2)
    d.rounded_rectangle((x + 24, y + 30, x + 94, y + 100), 12, fill=(0, 95, 184))
    d.text((x + 120, y + 30), title, font=font(BOLD, 28), fill=(30, 30, 40))
    d.text((x + 120, y + 76), line, font=font(SANS, 24), fill=(90, 92, 104))
    return base


def calculator():
    """A desktop calculator: a display with the running sum, a 4 x 5 key grid."""
    im = Image.new("RGB", (560, 820), (36, 38, 44))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 560, 200), fill=(28, 30, 34))
    d.text((40, 30), "2,450 + 1,725 =", font=font(SANS, 30), fill=(150, 154, 166))
    t = "4,175"
    d.text((520 - d.textlength(t, font=font(SANS, 84)), 80), t, font=font(SANS, 84), fill=(245, 245, 248))
    keys = ["C", "+/-", "%", "/", "7", "8", "9", "x", "4", "5", "6", "-", "1", "2", "3", "+", "0", ".", "<", "="]
    for k, key in enumerate(keys):
        cx, cy = 20 + (k % 4) * 132, 220 + (k // 4) * 118
        col = (240, 140, 40) if k % 4 == 3 else ((80, 84, 94) if k < 4 else (58, 61, 70))
        d.rounded_rectangle((cx, cy, cx + 118, cy + 104), 14, fill=col)
        d.text((cx + 59 - d.textlength(key, font=font(SANS, 40)) / 2, cy + 28), key, font=font(SANS, 40), fill=(245, 245, 248))
    return im


def screen_note(base, x, y, rgb, lines, rot):
    """An on-screen sticky note (a desktop notes app): a coloured square with a thin top
    bar, handwriting, a soft shadow, turned rot deg."""
    from PIL import ImageFilter
    n = Image.new("RGBA", (330, 330), (*rgb, 255))
    d = ImageDraw.Draw(n)
    d.rectangle((0, 0, 330, 28), fill=tuple(max(0, c - 30) for c in rgb) + (255,))
    d.text((298, -2), "x", font=font(SANS, 26), fill=(60, 60, 60))
    for k, line in enumerate(lines):
        d.text((24, 48 + k * 54), line, font=hand(46), fill=(40, 44, 70))
    n = n.rotate(rot, resample=Image.BICUBIC, expand=True)
    sh = Image.new("L", base.size, 0)
    sh.paste(n.getchannel("A").point(lambda v: v // 2), (x + 8, y + 12))
    base.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    base.paste(n, (x, y), n)
    return base


def taskbar(base, apps, active):
    """A generic Linux desktop panel along the bottom (56 px): an app menu, launcher icons
    (apps, the active one underlined), and tray icons with the clock on the right."""
    d = ImageDraw.Draw(base)
    W4, H4 = base.size
    y = H4 - 56
    d.rectangle((0, y, W4, H4), fill=(30, 32, 38))
    d.rounded_rectangle((16, y + 10, 52, y + 46), 8, fill=(70, 130, 220))
    d.text((70, y + 13), "Activities", font=font(SANS, 24), fill=(225, 228, 236))
    for k, col in enumerate(apps):
        x = 260 + k * 70
        d.rounded_rectangle((x, y + 8, x + 40, y + 48), 9, fill=col)
        if k == active:
            d.rectangle((x + 6, y + 51, x + 34, y + 54), fill=(225, 228, 236))
    for k in range(4):                                  # tray: network, volume, battery, bell
        x = W4 - 420 + k * 52
        d.ellipse((x, y + 16, x + 24, y + 40), outline=(200, 204, 212), width=3)
    d.text((W4 - 180, y + 6), "14:32", font=font(BOLD, 24), fill=(235, 238, 244))
    d.text((W4 - 180, y + 30), "Thu 22 Oct", font=font(SANS, 18), fill=(180, 184, 194))
    return base


APPS = [(33, 115, 70), (0, 95, 184), (50, 48, 76), (220, 110, 40), (120, 120, 130), (170, 40, 40), (90, 160, 90)]


def sheet():
    """The spreadsheet with a chat window over its lower right, a calculator at the lower
    left, a notification, and the desktop panel along the bottom."""
    im = sheet_full().resize((3840, 2104), Image.LANCZOS)
    full = Image.new("RGB", (3840, 2160))
    full.paste(im, (0, 0))
    window(full, chat(), 2280, 1060, 1300, "Chat - #budget-2026", accent=(50, 48, 76))
    window(full, calculator(), 140, 1180, 520, "Calculator", accent=(46, 48, 56))
    toast(full, 3150, 90, "Meeting in 10 min", "Release review, Room 2")
    return taskbar(full, APPS, 0)


def mail():
    """The mail client with a calendar window and a PDF open over it, three on-screen
    sticky notes at the right, and the desktop panel."""
    im = mail_full().resize((3840, 2104), Image.LANCZOS)
    full = Image.new("RGB", (3840, 2160))
    full.paste(im, (0, 0))
    window(full, calendar(), 1200, 1160, 1500, "Calendar - Thursday", accent=(0, 95, 184))
    window(full, paper_chart(), 2900, 420, 700, "Tickets_2026.pdf - 1 / 3", accent=(170, 40, 40))
    screen_note(full, 3060, 1330, (255, 236, 120), ["VPN cert", "renew Fri!"], 3)
    screen_note(full, 3430, 1250, (170, 225, 245), ["Q3 travel", "= trade fair"], -4)
    screen_note(full, 3360, 1640, (250, 175, 200), ["call Anna", "after 3"], 2)
    return taskbar(full, APPS, 1)


def reception_full():
    """A visitor-management app at 3840 x 2104: today's visitors as a table (time, name,
    company, host, badge, status), the rooms' day plan beside it."""
    W4, H4 = 3840, 2104
    im = Image.new("RGB", (W4, H4), (246, 247, 250))
    d = ImageDraw.Draw(im)
    teal = (0, 120, 130)
    d.rectangle((0, 0, W4, 64), fill=teal)
    d.text((30, 14), "Front Desk  -  Visitors", font=font(BOLD, 30), fill=(255, 255, 255))
    for k, t in enumerate(["Today", "Upcoming", "Deliveries", "Rooms", "Reports"]):
        d.text((900 + k * 230, 18), t, font=font(BOLD if k == 0 else SANS, 26), fill=(230, 245, 246))
    d.rounded_rectangle((30, 100, 330, 160), 10, fill=teal)
    d.text((62, 114), "+ Sign in visitor", font=font(BOLD, 24), fill=(255, 255, 255))
    cols = [("Time", 140), ("Visitor", 330), ("Company", 300), ("Host", 260), ("Badge", 130), ("Status", 220)]
    x0, y0, rh = 30, 200, 64
    xs = [x0]
    for _, w_ in cols:
        xs.append(xs[-1] + w_)
    d.rectangle((x0, y0, xs[-1], y0 + rh), fill=(226, 236, 238))
    for i, (t, _) in enumerate(cols):
        d.text((xs[i] + 14, y0 + 18), t, font=font(BOLD, 24), fill=(40, 44, 56))
    rows = [("08:30", "J. Meyer", "Courier", "Reception", "-", "Left"), ("09:00", "S. Patel", "Brightline", "Anna Weber", "V-104", "In"),
            ("09:15", "L. Novak", "Northwind", "Marco Rossi", "V-105", "In"), ("09:30", "Delivery", "Office supplies", "Facilities", "-", "Left"),
            ("10:00", "K. Ito", "Studio Ko", "Lena Hofmann", "V-106", "Waiting"), ("10:30", "M. Garcia", "Garcia & Co", "Anna Weber", "", "Expected"),
            ("11:00", "Interview", "", "HR", "", "Expected"), ("12:00", "Courier pick-up", "", "Reception", "", "Expected"),
            ("13:00", "T. Berg", "City Council", "Jonas K.", "", "Expected"), ("14:00", "Site tour (6)", "Partner school", "Facilities", "", "Expected"),
            ("15:30", "R. Okafor", "Brightline", "Marco Rossi", "", "Expected"), ("16:00", "Window cleaning", "CleanCo", "Facilities", "", "Expected")]
    stc = {"In": (40, 150, 80), "Left": (130, 134, 146), "Waiting": (220, 140, 30), "Expected": (60, 110, 200)}
    for r, row in enumerate(rows):
        y = y0 + (r + 1) * rh
        if r == 4:
            d.rectangle((x0, y, xs[-1], y + rh), fill=(255, 244, 222))
        d.line((x0, y + rh, xs[-1], y + rh), fill=(222, 225, 232), width=2)
        for i, t in enumerate(row):
            if i == 5:
                d.rounded_rectangle((xs[i] + 10, y + 12, xs[i] + 160, y + 52), 18, fill=stc[t])
                d.text((xs[i] + 30, y + 18), t, font=font(BOLD, 22), fill=(255, 255, 255))
            else:
                d.text((xs[i] + 14, y + 18), t, font=font(SANS, 24), fill=(40, 44, 56))
    plan_ = calendar().resize((3840 - xs[-1] - 90, int((3840 - xs[-1] - 90) * 1440 / 2560)), Image.LANCZOS)
    im.paste(plan_, (xs[-1] + 50, 100))
    d.text((x0, y0 + 14 * rh), "Deliveries today: 3   ·   Badges out: 3   ·   Parking: 2 of 6 free", font=font(SANS, 26), fill=(80, 86, 100))
    return im


def badge_dialog():
    """A small dialog: print a visitor badge, a badge preview, two buttons."""
    im = Image.new("RGB", (900, 620), (250, 250, 252))
    d = ImageDraw.Draw(im)
    d.text((40, 30), "Print visitor badge", font=font(BOLD, 34), fill=(30, 34, 46))
    d.rounded_rectangle((40, 100, 400, 520), 16, fill=(255, 255, 255), outline=(200, 204, 212), width=3)
    d.rectangle((40, 100, 400, 170), fill=(0, 64, 160))
    d.text((120, 116), "VISITOR", font=font(BOLD, 36), fill=(255, 255, 255))
    d.text((70, 220), "Kenji Ito", font=font(BOLD, 34), fill=(30, 34, 46))
    d.text((70, 270), "Studio Ko", font=font(SANS, 28), fill=(90, 94, 106))
    d.text((70, 330), "Host: Lena Hofmann", font=font(SANS, 24), fill=(90, 94, 106))
    d.text((70, 370), "V-106   22 Oct", font=font(SANS, 24), fill=(90, 94, 106))
    for k, (t, prim) in enumerate((("Print", True), ("Cancel", False))):
        d.rounded_rectangle((460, 400 + k * 90, 840, 470 + k * 90), 12, fill=(0, 120, 130) if prim else (232, 234, 240))
        d.text((600, 414 + k * 90), t, font=font(BOLD if prim else SANS, 30), fill=(255, 255, 255) if prim else (40, 44, 56))
    d.text((460, 120), "Printer: Badge-01", font=font(SANS, 24), fill=(90, 94, 106))
    d.text((460, 160), "Paper: 54 x 86 mm", font=font(SANS, 24), fill=(90, 94, 106))
    return im


def reception():
    """The front desk's screen: the visitor app, a badge dialog and a chat window over it,
    a notification, the desktop panel."""
    full = Image.new("RGB", (3840, 2160))
    full.paste(reception_full(), (0, 0))
    window(full, badge_dialog(), 600, 1180, 900, "Print badge", accent=(0, 120, 130))
    window(full, chat(), 2560, 1240, 1100, "Chat - #budget-2026", accent=(50, 48, 76))
    toast(full, 3150, 90, "Visitor arrived", "K. Ito for Lena Hofmann")
    return taskbar(full, APPS, 3)


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


def ruler():
    """A 300 mm steel rule's face, 3000 x 280 px (10 px a mm): brushed steel, a tick a
    millimetre (longer each 5 and 10), the centimetres numbered."""
    import random
    rnd = random.Random(3)
    im = Image.new("RGB", (3000, 280), (176, 178, 182))
    d = ImageDraw.Draw(im)
    for y in range(280):                                 # the brushing, along the rule
        v = 168 + rnd.randint(-10, 10)
        d.line((0, y, 3000, y), fill=(v, v + 2, v + 6))
    for mm in range(0, 301):
        x = 10 + mm * 9.93
        h = 120 if mm % 10 == 0 else 80 if mm % 5 == 0 else 50
        d.line((x, 0, x, h), fill=(25, 25, 28), width=3)
        if mm % 10 == 0 and mm:
            d.text((x - 14, 130), str(mm // 10), font=font(BOLD, 56), fill=(25, 25, 28))
    return im


def poster():
    """The gamer wall's poster: the racing game's road and sun, its HUD cropped off."""
    return game().crop((720, 0, 1840, 1440))


PAPER = (244, 242, 236)
INK = (40, 44, 60)


def cork():
    """A pinboard's cork, 4400 x 2000 px across a 0.76 x 0.36 m board (5.8 px a mm):
    granules of 0.3 to 1.5 mm in five shades over dark gaps, drawn largest first."""
    import random
    rnd = random.Random(5)
    W_, H_ = 4400, 2000
    im = Image.new("RGB", (W_, H_), (100, 68, 40))
    d = ImageDraw.Draw(im)
    shades = [(178, 128, 82), (160, 112, 70), (140, 96, 58), (196, 148, 100), (122, 82, 48)]
    for r_hi, n in ((9, 90000), (5, 260000), (3, 420000)):
        for _ in range(n):
            x, y, r = rnd.uniform(0, W_), rnd.uniform(0, H_), rnd.uniform(r_hi / 2, r_hi)
            pts = [(x + r * rnd.uniform(0.6, 1.0) * c, y + r * rnd.uniform(0.6, 1.0) * s_)
                   for c, s_ in ((1, 0), (0.5, 0.87), (-0.5, 0.87), (-1, 0), (-0.5, -0.87), (0.5, -0.87))]
            c0 = rnd.choice(shades)
            v = rnd.randint(-12, 12)
            d.polygon(pts, fill=(c0[0] + v, c0[1] + v, c0[2] + v // 2))
    return im


def paper_layout():
    """An A4 sheet, landscape: a split keyboard's layer sketched in pen, keys labelled."""
    im = Image.new("RGB", (1414, 1000), PAPER)
    d = ImageDraw.Draw(im)
    d.text((60, 40), "Layer 2  (nav + num)", font=font(BOLD, 44), fill=INK)
    labels = "1234567890" "←↓↑→" "HPEUD" "+-*/=" "()[]{}" "<>"
    k, i = 70, 0
    for half, x0 in ((0, 70), (1, 760)):
        for r in range(4):
            for c in range(6):
                x, y = x0 + c * (k + 8), 160 + r * (k + 8) + (abs(c - 2.5) < 1.5) * -14
                d.rounded_rectangle((x, y, x + k, y + k), 8, outline=INK, width=3)
                d.text((x + 20, y + 12), labels[i % len(labels)], font=font(SANS, 34), fill=(30, 70, 160))
                i += 1
    for j, line in enumerate(["- move arrows to the home row?", "- F-keys on Fn only", "- try it for a week"]):
        d.text((80, 520 + j * 70), line, font=font(SANS, 38), fill=(60, 60, 70))
    d.ellipse((900, 520, 1300, 760), outline=(200, 40, 40), width=5)
    d.text((960, 600), "ask the team", font=font(SANS, 40), fill=(200, 40, 40))
    return im


def paper_sprint():
    """An A4 sheet: a week's tasks in a table, some ticked."""
    im = Image.new("RGB", (1000, 1414), PAPER)
    d = ImageDraw.Draw(im)
    d.text((70, 60), "Week 42", font=font(BOLD, 64), fill=INK)
    tasks = ["Review layout feedback", "Order USB-C cables", "Q4 budget draft", "Team lunch (Thu)",
             "Update onboarding doc", "Call supplier", "Desk move, 3rd floor", "Backup check", "Plan offsite"]
    for i, t in enumerate(tasks):
        y = 200 + i * 120
        d.line((70, y + 90, 930, y + 90), fill=(190, 190, 195), width=2)
        d.rectangle((80, y + 20, 130, y + 70), outline=INK, width=4)
        if i in (0, 1, 3, 7):
            d.line((88, y + 45, 104, y + 64, 128, y + 14), fill=(30, 120, 60), width=7)
        d.text((160, y + 18), t, font=font(SANS, 44), fill=INK)
    return im


def paper_chart():
    """An A4 printout: a bar chart, quarterly numbers."""
    im = Image.new("RGB", (1000, 1414), PAPER)
    d = ImageDraw.Draw(im)
    d.text((70, 60), "Tickets closed", font=font(BOLD, 58), fill=INK)
    d.text((70, 140), "per month, 2026", font=font(SANS, 38), fill=(110, 110, 120))
    base, vals = 1150, [310, 420, 380, 520, 610, 560, 700, 760, 690]
    d.line((90, base, 940, base), fill=INK, width=4)
    for i, v in enumerate(vals):
        x = 110 + i * 92
        d.rectangle((x, base - v * 1.2, x + 62, base), fill=(52, 104, 180) if i < 8 else (230, 140, 40))
        d.text((x + 14, base + 20), "JFMAMJJAS"[i], font=font(SANS, 38), fill=INK)
    for j in range(1, 5):
        y = base - j * 200
        d.line((90, y, 940, y), fill=(210, 210, 215), width=2)
    return im


def paper_month():
    """A wall calendar's month page: a landscape photo above a grid, a few days marked.
    The photo is a crop of the bell_park_pier HDRI's tonemapped JPG, near its horizon where
    the equirectangular projection barely bends."""
    import workspace_assets
    im = Image.new("RGB", (1000, 1300), (250, 249, 245))
    d = ImageDraw.Draw(im)
    Image.MAX_IMAGE_PIXELS = None
    src = Image.open(workspace_assets.fetch_photo("bell_park_pier"))
    w, h = src.size
    cx = int(w * PHOTO_X)
    ph = src.crop((cx - int(w * 0.07), int(h * 0.405), cx + int(w * 0.07), int(h * 0.405) + int(w * 0.14 * 0.52)))
    im.paste(ph.resize((1000, 520), Image.LANCZOS), (0, 0))
    d.text((60, 560), "October", font=font(BOLD, 72), fill=INK)
    for i, n in enumerate("MTWTFSS"):
        d.text((80 + i * 128, 680), n, font=font(BOLD, 36), fill=(120, 120, 130))
    day, cells = 1, {}
    for r in range(5):
        for c in range(7):
            if r == 0 and c < 3 or day > 31:
                continue
            x, y = 70 + c * 128, 740 + r * 108
            d.rectangle((x, y, x + 120, y + 100), outline=(200, 200, 205), width=2)
            d.text((x + 10, y + 6), str(day), font=font(SANS, 34), fill=INK)
            if day in (9, 16, 23):
                d.ellipse((x + 4, y + 2, x + 70, y + 54), outline=(210, 40, 40), width=4)
            cells[day] = (x, y)
            day += 1
    scribble(im, cells)
    return im


def paper_rota():
    """A4 landscape, the front desk's rota for the week: three shifts a day, a
    colour per person, one shift swapped by hand."""
    im = Image.new("RGB", (1414, 1000), PAPER)
    d = ImageDraw.Draw(im)
    d.text((60, 50), "Front desk rota", font=font(BOLD, 60), fill=INK)
    d.text((60, 130), "Week 43  -  20 to 24 October", font=font(SANS, 34), fill=(110, 110, 120))
    who = {"Anna": (150, 200, 240), "Marco": (250, 200, 120), "Lea": (170, 220, 150), "Jonas": (240, 170, 190)}
    plan = [["Anna", "Anna", "Marco", "Anna", "Lea"], ["Marco", "Lea", "Lea", "Jonas", "Marco"],
            ["Jonas", "Jonas", "Anna", "Marco", "Jonas"]]
    x0, y0, cw, ch = 300, 230, 210, 200
    for c, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri"]):
        d.text((x0 + c * cw + 70, y0), day, font=font(BOLD, 36), fill=INK)
    for r, shift in enumerate(["7:30 - 12:00", "12:00 - 16:30", "16:30 - 19:00"]):
        y = y0 + 70 + r * ch
        d.text((60, y + 75), shift, font=font(SANS, 34), fill=INK)
        for c in range(5):
            x = x0 + c * cw
            d.rectangle((x + 6, y + 6, x + cw - 6, y + ch - 6), fill=who[plan[r][c]])
            d.text((x + 30, y + 75), plan[r][c], font=font(SANS, 38), fill=INK)
    x, y = x0 + 3 * cw, y0 + 70 + 2 * ch               # Thu evening: Marco crossed out, Lea written in
    d.line((x + 26, y + 98, x + 140, y + 98), fill=(200, 30, 30), width=6)
    layer = Image.new("RGBA", (200, 90), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((4, 0), "Lea!", font=hand(64, 650), fill=(200, 30, 30, 240))
    layer = layer.rotate(-5, resample=Image.BICUBIC)
    im.paste(layer, (x + 60, y + 112), layer)
    return im


def paper_phone():
    """A5 portrait: the internal phone list."""
    im = Image.new("RGB", (700, 1000), (252, 252, 250))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 700, 120), fill=(40, 90, 150))
    d.text((40, 32), "Extensions", font=font(BOLD, 52), fill=(255, 255, 255))
    rows = [("Reception", "100"), ("IT helpdesk", "214"), ("Facilities", "230"), ("HR", "305"),
            ("Accounts", "410"), ("Meeting rm 1", "501"), ("Meeting rm 2", "502"), ("Security", "999")]
    for i, (n, e) in enumerate(rows):
        y = 170 + i * 92
        d.text((40, y), n, font=font(SANS, 38), fill=INK)
        d.text((560, y), e, font=font(BOLD, 38), fill=INK)
        d.line((40, y + 68, 660, y + 68), fill=(210, 210, 215), width=2)
    d.text((40, 920), "Emergency  112", font=font(BOLD, 40), fill=(200, 30, 30))
    return im


def paper_desk_month():
    """A small tear-off month calendar: November, a bar on top, the 3rd circled."""
    im = Image.new("RGB", (800, 760), (253, 252, 249))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 800, 150), fill=(190, 60, 50))
    d.text((40, 30), "November 2026", font=font(BOLD, 64), fill=(255, 255, 255))
    for i, n in enumerate("MTWTFSS"):
        d.text((60 + i * 102, 180), n, font=font(BOLD, 34), fill=(120, 120, 130) if i < 5 else (190, 60, 50))
    day = 1
    for r in range(6):
        for c in range(7):
            if (r == 0 and c < 6) or day > 30:
                continue
            x, y = 50 + c * 102, 240 + r * 84
            d.text((x + 10, y), str(day), font=font(SANS, 38), fill=INK if c < 5 else (190, 60, 50))
            if day == 3:
                d.ellipse((x - 4, y - 8, x + 74, y + 56), outline=(30, 50, 140), width=4)
            day += 1
    return im


def paper_wifi():
    """A guest Wi-Fi card, the password partly handwritten over a printed blank."""
    im = Image.new("RGB", (900, 560), (252, 252, 250))
    d = ImageDraw.Draw(im)
    d.text((50, 40), "Guest Wi-Fi", font=font(BOLD, 64), fill=INK)
    d.text((50, 170), "Network", font=font(SANS, 36), fill=(120, 120, 130))
    d.text((300, 162), "Visitors", font=font(BOLD, 46), fill=INK)
    d.text((50, 280), "Password", font=font(SANS, 36), fill=(120, 120, 130))
    d.line((300, 350, 820, 350), fill=(180, 180, 185), width=3)
    d.text((310, 262), "welcome-2026", font=hand(70, 600), fill=(30, 50, 140))
    d.text((50, 440), "Ask at the desk if it does not connect.", font=font(SANS, 30), fill=(120, 120, 130))
    return im


def art_arches():
    """A large print for the lobby wall: mid-century arches and a sun in terracotta,
    sage, ochre and ink on warm paper, with a white margin."""
    im = Image.new("RGB", (1400, 1000), (246, 240, 228))
    d = ImageDraw.Draw(im)
    d.rectangle((70, 70, 1330, 930), fill=(236, 226, 206))
    d.ellipse((860, 150, 1120, 410), fill=(222, 160, 60))                     # the sun
    for (x0, w, col) in ((120, 420, (186, 92, 62)), (430, 360, (128, 150, 120)), (760, 300, (40, 52, 70)), (1010, 270, (196, 130, 90))):
        top_ = 930 - int(w * 1.25)
        d.rectangle((x0, top_ + w // 2, x0 + w, 930), fill=col)
        d.ellipse((x0, top_, x0 + w, top_ + w), fill=col)
    for k in range(5):                                                         # thin rings in the first arch
        r = 60 + k * 34
        d.arc((330 - r, 615 - r, 330 + r, 615 + r), 180, 360, fill=(246, 240, 228), width=8)
    d.rectangle((70, 900, 1330, 930), fill=(40, 52, 70))
    return im


SCRIBBLES = [  # (day, text, ink, tilt deg): pen notes in the calendar's day boxes
    (6, "dentist\n9:30", (30, 50, 140), 4), (9, "demo!", (200, 30, 30), -6), (13, "PCB\norder", (30, 50, 140), 3),
    (16, "ship\nv1.8", (200, 30, 30), -4), (20, "Mia's\nbday", (40, 110, 60), 6), (23, "team\nlunch", (30, 50, 140), -3),
    (28, "taxes", (30, 30, 35), 5), (30, "trip ->", (30, 50, 140), -2)]


HL = {"yellow": (255, 240, 60), "pink": (255, 120, 190), "green": (130, 240, 110), "orange": (255, 175, 60)}


def highlighted(fn, marks):
    """fn's sheet with highlighter strokes: marks = [(box, colour name)], each a
    translucent band multiplied onto the paper, its edges a little ragged."""
    import random
    from PIL import ImageChops

    def draw():
        im = fn()
        layer = Image.new("RGB", im.size, (255, 255, 255))
        d = ImageDraw.Draw(layer)
        rnd = random.Random(len(marks))
        for (x0, y0, x1, y1), col in marks:
            c = HL[col]
            top = [(x, y0 + rnd.randint(-3, 3)) for x in range(x0, x1 + 1, 24)]
            bot = [(x, y1 + rnd.randint(-3, 3)) for x in range(x1, x0 - 1, -24)]
            d.polygon(top + bot, fill=tuple(int(255 - (255 - v) * 0.75) for v in c))
        return ImageChops.multiply(im.convert("RGB"), layer)
    return draw


def worn(fn, seed, amount=1.0):
    """fn's sheet handled for a while: grime in two corners, a thumb smudge near an
    edge, a faint crease and a touch of yellowing (all multiplied, so ink stays)."""
    import math
    import random
    from PIL import ImageChops, ImageFilter

    def draw():
        im = fn().convert("RGB")
        w, h = im.size
        rnd = random.Random(seed)
        layer = Image.new("L", (w, h), 255)
        d = ImageDraw.Draw(layer)
        r = int(min(w, h) * 0.22)
        for cx, cy in rnd.sample([(0, 0), (w, 0), (0, h), (w, h)], 2):
            for k in range(r, 0, -6):
                v = int(255 - 38 * amount * (1 - k / r) ** 1.6)
                d.ellipse((cx - k, cy - k, cx + k, cy + k), fill=v)
        fx, fy = rnd.randint(int(w * 0.6), int(w * 0.9)), rnd.randint(int(h * 0.75), int(h * 0.95))
        for k in range(10):                        # a thumb print: faint ridges
            d.ellipse((fx - 40 + k * 3, fy - 55 + k * 4, fx + 40 - k * 3, fy + 55 - k * 4),
                      outline=int(255 - 14 * amount), width=2)
        a = rnd.uniform(-0.3, 0.3)
        y0 = h * rnd.uniform(0.4, 0.6)
        d.line((0, y0, w, y0 + w * math.tan(a)), fill=int(255 - 16 * amount), width=3)
        layer = layer.filter(ImageFilter.GaussianBlur(2.5))
        tint = Image.merge("RGB", (layer, layer.point(lambda v: int(v * 0.985)), layer.point(lambda v: int(v * 0.95))))
        return ImageChops.multiply(im, tint)
    return draw


NOTEPAD = [  # (text, struck through, ink)
    ("Mon - todo", False, (25, 35, 90)), ("macro for git commit", True, (25, 35, 90)),
    ("layer 3: arrows on HJKL?", False, (25, 35, 90)), ("order 2nd keycap set", True, (25, 35, 90)),
    ("ask IT about VPN", True, (25, 35, 90)), ("tenting angle 8 deg?", False, (25, 35, 90)),
    ("call back 14:00", False, (180, 30, 30))]


def notepad_page():
    """The notepad's top page (1400 x 1980 px): ivory paper, the pen notes written on it,
    handled at the edges."""
    def draw():
        im = Image.new("RGBA", (1400, 1980), (236, 226, 198, 255))
        im.alpha_composite(notepad_writing())
        return im.convert("RGB")
    return worn(draw, 23, 0.7)()


def wall_scuff():
    """Rub marks on a wall where cables go down behind a desk (800 x 1040 px,
    transparent; the desk top sits 60 % down): a grey smudge band along that line and
    short near-vertical scratches, densest right at it, thinning above and below."""
    import math
    import random
    from PIL import ImageFilter
    rnd = random.Random(31)
    w, h = 800, 1040
    edge = h * 0.60
    smudge = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(smudge)
    for _ in range(70):
        x, y = rnd.gauss(w / 2, w / 5), edge + rnd.gauss(0, h / 18)
        r = rnd.uniform(15, 45)
        d.ellipse((x - r * 0.7, y - r * 1.4, x + r * 0.7, y + r * 1.4), fill=rnd.randint(10, 24))
    smudge = smudge.filter(ImageFilter.GaussianBlur(18))
    im = Image.new("RGBA", (w, h), (60, 58, 55, 0))
    im.putalpha(smudge)
    d2 = ImageDraw.Draw(im)
    for _ in range(200):
        x = rnd.gauss(w / 2, w / 5)
        y = edge + rnd.gauss(0, h / 14) * (1.0 if rnd.random() < 0.8 else 2.2)
        ln, a = rnd.uniform(12, 70), math.radians(90 + rnd.gauss(0, 9))
        c = rnd.choice([(70, 68, 64), (90, 87, 82), (205, 203, 197)])
        d2.line((x, y - ln / 2 * math.sin(a), x + ln * math.cos(a), y + ln / 2 * math.sin(a)),
                fill=(*c, rnd.randint(40, 110)), width=rnd.choice([1, 1, 2, 2]))
    return im


from workspace_scenes import BOOKS  # noqa: E402  (the shelf's books: data shared with the scene)


SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
COND_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
PX = 7600                                           # texture pixels per metre of book


def _fit(path, text, size, width):
    while size > 8 and font(path, size).getlength(text) > width:
        size -= 2
    return font(path, size)


def _rgb(c):
    return tuple(int(v * 255) for v in c)


def book_spine(i):
    """Book i's spine (BOOKS) in one of four layouts after real spines: drawn lying
    (height along x), then turned to read top to bottom."""
    def draw():
        title, author, cover, ink, hgt, th, style = BOOKS[i]
        w, h = max(140, int(th * PX * 2.4)), int(hgt * PX)
        bg = _rgb(cover)
        im = Image.new("RGB", (h, w), bg)
        d = ImageDraw.Draw(im)
        if style == 2:                                 # stacked words across a thick spine: drawn upright
            im = Image.new("RGB", (w, h), bg)
            d = ImageDraw.Draw(im)
            y = int(h * 0.08)
            for word in title.upper().split():
                f = _fit(SERIF_B, word, int(w * 0.30), w * 0.86)
                d.text(((w - d.textlength(word, font=f)) / 2, y), word, font=f, fill=ink)
                y += int(f.size * 1.15)
            d.line((w * 0.2, y + 20, w * 0.8, y + 20), fill=ink, width=4)
            f = _fit(SERIF, author, int(w * 0.13), w * 0.9)
            d.text(((w - d.textlength(author, font=f)) / 2, h * 0.80), author, font=f, fill=ink)
            d.ellipse((w / 2 - w * 0.10, h * 0.87, w / 2 + w * 0.10, h * 0.87 + w * 0.20), outline=ink, width=4)
            return im
        if style == 1:                                 # serif title between colour bands
            band = tuple(max(0, v - 60) for v in bg)
            d.rectangle((0, 0, h * 0.10, w), fill=band)
            d.rectangle((h * 0.86, 0, h, w), fill=band)
            f = _fit(SERIF, title, int(w * 0.46), h * 0.46)
            d.text((h * 0.14, (w - f.size * 1.2) / 2), title, font=f, fill=ink)
            fa = _fit(SERIF, author, int(w * 0.30), h * 0.17)
            d.text((h * 0.84 - d.textlength(author, font=fa), (w - fa.size * 1.2) / 2), author, font=fa, fill=ink)
        elif style == 3:                               # condensed capitals, a rule, a series number
            f = _fit(COND_B, title.upper(), int(w * 0.52), h * 0.58)
            d.text((h * 0.06, (w - f.size * 1.2) / 2), title.upper(), font=f, fill=ink)
            x1 = h * 0.06 + d.textlength(title.upper(), font=f) + 30
            d.line((x1, w / 2, h * 0.80, w / 2), fill=ink, width=3)
            fn = font(BOLD, int(w * 0.36))
            d.rectangle((h * 0.84, w * 0.18, h * 0.96, w * 0.82), fill=ink)
            d.text((h * 0.865, w * 0.22), str(i + 3), font=fn, fill=bg)
        else:                                          # title down the spine, author and a mark below
            f = _fit(BOLD if i % 2 else SANS, title, int(w * 0.44), h * 0.56)
            d.text((h * 0.07, (w - f.size * 1.2) / 2), title, font=f, fill=ink)
            if author:
                fa = _fit(SANS, author, int(w * 0.30), h * 0.16)
                d.text((h * 0.72, (w - fa.size * 1.2) / 2), author, font=fa, fill=ink)
            d.polygon([(h * 0.95, w * 0.25), (h * 0.95, w * 0.75), (h * 0.91, w * 0.5)], fill=ink)
        return im.rotate(270, expand=True)             # read top to bottom, as English spines are
    return draw


COVER_ART = ["chip", "traces", "letters", "wave", "keys", "hand", "gear"]


def book_cover(i):
    """Book i's front cover: its colour, a simple graphic for the subject, the title
    and the author."""
    import math
    def draw():
        title, author, cover, ink, hgt, th, style = BOOKS[i]
        dep = 0.16 + 0.01 * (i % 3)
        w, h = int(dep * PX), int(hgt * PX)
        bg = _rgb(cover)
        im = Image.new("RGB", (w, h), bg)
        d = ImageDraw.Draw(im)
        art, lw = COVER_ART[i % len(COVER_ART)], 6
        cx, cy, r = w / 2, h * 0.58, w * 0.28
        if art == "chip":
            d.rectangle((cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6), outline=ink, width=lw)
            for k in range(-3, 4):
                for sx in (-1, 1):
                    d.line((cx + sx * r * 0.6, cy + k * r * 0.15, cx + sx * r, cy + k * r * 0.15), fill=ink, width=lw)
                    d.line((cx + k * r * 0.15, cy + sx * r * 0.6, cx + k * r * 0.15, cy + sx * r), fill=ink, width=lw)
        elif art == "traces":
            for k in range(7):
                y0 = cy - r + k * r / 3
                d.line((w * 0.1, y0, cx, y0, cx + r * 0.4, y0 - r * 0.4, w * 0.9, y0 - r * 0.4), fill=ink, width=lw)
                d.ellipse((w * 0.9 - 12, y0 - r * 0.4 - 12, w * 0.9 + 12, y0 - r * 0.4 + 12), fill=ink)
        elif art == "letters":
            f = font(SERIF_B, int(r * 1.6))
            d.text((cx - r * 1.1, cy - r), "Ag", font=f, fill=ink)
        elif art == "wave":
            pts = [(w * 0.1 + t * w * 0.8 / 200, cy + r * 0.6 * math.sin(t / 200 * 4 * math.pi) * math.exp(-t / 260))
                   for t in range(201)]
            d.line(pts, fill=ink, width=lw)
            d.line((w * 0.1, cy, w * 0.9, cy), fill=ink, width=2)
        elif art == "keys":
            for kx in range(4):
                for ky in range(3):
                    x0, y0 = cx - r + kx * r * 0.52, cy - r * 0.6 + ky * r * 0.52
                    d.rounded_rectangle((x0, y0, x0 + r * 0.44, y0 + r * 0.44), 10, outline=ink, width=lw)
        elif art == "hand":
            d.ellipse((cx - r, cy - r * 0.5, cx + r, cy + r * 1.1), outline=ink, width=lw)
            for k in range(4):
                d.rounded_rectangle((cx - r * 0.8 + k * r * 0.42, cy - r * 1.3, cx - r * 0.5 + k * r * 0.42, cy - r * 0.3),
                                    20, outline=ink, width=lw)
        else:
            for k in range(12):
                a = k * math.pi / 6
                d.line((cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a), cx + r * math.cos(a), cy + r * math.sin(a)),
                       fill=ink, width=lw * 3)
            d.ellipse((cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy + r * 0.7), outline=ink, width=lw * 2)
        ft = _fit(SERIF_B if style in (1, 2) else BOLD, title, int(w * 0.13), w * 0.84)
        d.text((w * 0.08, h * 0.08), title, font=ft, fill=ink)
        if author:
            fa = _fit(SANS, author, int(w * 0.06), w * 0.84)
            d.text((w * 0.08, h * 0.08 + ft.size * 1.4), author, font=fa, fill=ink)
        return im
    return draw


def book_back(i):
    """Book i's back cover: a blurb in small type, a barcode."""
    import random
    def draw():
        title, author, cover, ink, hgt, th, style = BOOKS[i]
        dep = 0.16 + 0.01 * (i % 3)
        w, h = int(dep * PX), int(hgt * PX)
        rnd = random.Random(i)
        im = Image.new("RGB", (w, h), _rgb(cover))
        d = ImageDraw.Draw(im)
        words = ("the a practical guide to every chapter builds on real examples from the bench with clear "
                 "figures and worked problems for engineers students and makers who want to understand "
                 "how and why it works in practice").split()
        f = font(SANS, int(w * 0.034))
        y = h * 0.12
        for _ in range(18):
            line = ""
            while True:                                  # words until the line would pass 80 % of the width
                nxt = (line + " " + rnd.choice(words)).strip()
                if d.textlength(nxt, font=f) > w * 0.8:
                    break
                line = nxt
            d.text((w * 0.1, y), line.strip().capitalize(), font=f, fill=ink)
            y += f.size * 1.5
        bx, by = w * 0.58, h * 0.82
        d.rectangle((bx - 10, by - 10, bx + w * 0.32 + 10, by + h * 0.10 + 10), fill=(250, 250, 248))
        x = bx
        while x < bx + w * 0.32:
            bw = rnd.choice([2, 3, 5, 7])
            d.rectangle((x, by, x + bw, by + h * 0.08), fill=(20, 20, 20))
            x += bw + rnd.choice([3, 4, 6])
        return im
    return draw


def notepad_writing():
    """Pen notes for the A4 pad (1400 x 1980 px, transparent): a list in a handwriting
    face, every line a little crooked, three struck through with a wobbly stroke."""
    import random
    rnd = random.Random(21)
    im = Image.new("RGBA", (1400, 1980), (0, 0, 0, 0))
    f = hand(96, 560)
    for i, (text, struck, ink) in enumerate(NOTEPAD):
        layer = Image.new("RGBA", (1300, 200), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.text((10, 30), text, font=f, fill=(*ink, 240))
        if struck:
            w = d.textlength(text, font=f)
            pts = [(x, 95 + rnd.uniform(-5, 5)) for x in range(0, int(w) + 30, 40)]
            d.line(pts, fill=(*ink, 230), width=7, joint="curve")
        layer = layer.rotate(rnd.uniform(-2.0, 2.0), resample=Image.BICUBIC)
        im.alpha_composite(layer, (110 + rnd.randint(-15, 15), 140 + i * 210))
    return im


def hand(size, weight=520):
    """Caveat, a handwriting face (SIL OFL), fetched by workspace_assets.py."""
    import workspace_assets
    f = ImageFont.truetype(workspace_assets.fetch_font("Caveat.ttf"), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def scribble(im, cells):
    """Pen notes on the calendar page: each text drawn on its own layer in a
    handwriting face, turned a few degrees and pasted into its day box."""
    f = hand(42, 600)
    for day, text, ink, tilt in SCRIBBLES:
        if day not in cells:
            continue
        x, y = cells[day]
        layer = Image.new("RGBA", (140, 100), (0, 0, 0, 0))
        ImageDraw.Draw(layer).multiline_text((6, 0), text, font=f, fill=(*ink, 235), spacing=-6)
        layer = layer.rotate(tilt, resample=Image.BICUBIC, expand=False)
        im.paste(layer, (x - 4, y + 18), layer)


def mat_topo():
    """A desk mat's print, 3040 x 1360 px (4 px a mm on a 760 x 340 mm mat): contour
    lines of a made-up terrain (a sum of sines), every fifth line heavier, light grey
    on charcoal. Plain Python at half size, then scaled up (the system numpy is not
    usable here, and nothing is installed outside a venv)."""
    import math
    w, h = 1520, 680
    s_ = 200.0
    def z(x, y):
        x, y = x / s_, y / s_
        return 9.0 * (math.sin(x * 0.9 + 0.3) * math.cos(y * 1.1) + 0.6 * math.sin(x * 1.7 - y * 1.3 + 1.0)
                      + 0.35 * math.cos(x * 2.9 + y * 2.3) + 0.2 * math.sin(x * 4.1 - y * 3.7 + 2.0))
    base, ink = (50, 52, 56), (140, 142, 147)
    im = Image.new("RGB", (w, h))
    px = im.load()
    for j in range(h):
        for i in range(w):
            v = z(i, j)
            gx, gy = z(i + 1, j) - v, z(i, j + 1) - v
            k = round(v)
            d = abs(v - k) / (math.hypot(gx, gy) + 1e-6)     # distance to the nearest line, in pixels
            major = k % 5 == 0
            a_ = max(0.0, min(1.0, 1.0 - (d - (0.9 if major else 0.35)))) * (1.0 if major else 0.6)
            px[i, j] = tuple(int(base[c] + (ink[c] - base[c]) * a_) for c in range(3))
    return im.resize((3040, 1360), Image.BICUBIC)


PHOTO_X = 0.85            # where across the panorama the calendar's crop is centred


def framed_print(path, size=(1300, 1000), border=50, bg=None, zoom=1.0):
    """A photo print: the image filling size minus a white border (zoom > 1 crops in)."""
    src = Image.open(path).convert("RGB")
    if bg:
        flat = Image.new("RGB", src.size, bg)
        flat.paste(src, (0, 0))
        src = flat
    iw, ih = size[0] - 2 * border, size[1] - 2 * border
    s_ = max(iw / src.width, ih / src.height) * zoom
    src = src.resize((int(src.width * s_), int(src.height * s_)), Image.LANCZOS)
    x0, y0 = (src.width - iw) // 2, (src.height - ih) // 2
    im = Image.new("RGB", size, (250, 250, 248))
    im.paste(src.crop((x0, y0, x0 + iw, y0 + ih)), (border, border))
    return im


DOCS = os.path.join(HERE, "..", "..", "polykybd-docs", "src", "assets")


DOC_PRINTS = {             # print name: (docs asset, print size in px, zoom)
    "pcb_rev33": ("assembly/pcb-render-rev3.3.jpg", (1300, 860), 1.0),
    "pcb_split42": ("firmware/split42-pcb-render.jpg", (1300, 1000), 1.15),
    "stems": ("assembly/keys-assembled.jpg", (1300, 1000), 1.0),
    "rgb": ("landing/rgb-both-halves.jpg", (1300, 1000), 1.0),
    "emoji": ("using/emoji-keycap.jpg", (1000, 1000), 1.1),
    "halves": ("assembly/split72-both-halves.jpg", (1300, 1000), 1.0),
    "displays": ("assembly/display-modules.jpg", (1300, 1000), 1.2),
    "greek": ("using/legends-greek.jpg", (1300, 1000), 1.0),
}


def doc_print(name):
    path, size, zoom = DOC_PRINTS[name]
    return lambda: framed_print(os.path.join(DOCS, path), size, zoom=zoom)


def paper_schematic():
    """The left half's schematic printed on A4 landscape, a margin all round."""
    return framed_print(os.path.join(DOCS, "schematics", "schematic_left.png"), (1414, 1000), 60, bg=(255, 255, 255))


def photo_keyboard():
    """A photo print: the keyboard picture from the docs page screenshot, white border."""
    src = Image.open(os.path.join(OUT, "screen_polykybd_org.jpg"))
    w, h = src.size
    ph = src.crop((int(w * 0.31), int(h * 0.665), int(w * 0.70), int(h * 0.99))).resize((1200, 900))
    im = Image.new("RGB", (1300, 1000), (250, 250, 248))
    im.paste(ph, (50, 50))
    return im


def sticky(rgb, lines, size=(760, 760)):
    def draw():
        im = Image.new("RGB", size, rgb)
        d = ImageDraw.Draw(im)
        for j, line in enumerate(lines):
            d.text((60, 70 + j * 130), line, font=hand(110), fill=(30, 40, 90))
        return im
    return draw


def clock_face():
    """A wall clock's dial, 1200 px square: ticks, numbers, hands at ten past ten."""
    import math
    im = Image.new("RGB", (1200, 1200), (248, 248, 245))
    d = ImageDraw.Draw(im)
    c = 600
    for m in range(60):
        a = math.radians(m * 6)
        r0 = 500 if m % 5 else 460
        d.line((c + r0 * math.sin(a), c - r0 * math.cos(a), c + 540 * math.sin(a), c - 540 * math.cos(a)),
               fill=(25, 25, 28), width=14 if m % 5 == 0 else 5)
    for h in range(1, 13):
        a = math.radians(h * 30)
        t = str(h)
        f = font(BOLD, 90)
        tw = d.textlength(t, font=f)
        d.text((c + 370 * math.sin(a) - tw / 2, c - 370 * math.cos(a) - 55), t, font=f, fill=(25, 25, 28))
    for ang, ln, wd in ((305, 280, 30), (60, 420, 20)):
        a = math.radians(ang)
        d.line((c, c, c + ln * math.sin(a), c - ln * math.cos(a)), fill=(20, 20, 22), width=wd)
    a = math.radians(200)
    d.line((c - 80 * math.sin(a), c + 80 * math.cos(a), c + 460 * math.sin(a), c - 460 * math.cos(a)),
           fill=(200, 30, 30), width=8)
    d.ellipse((c - 30, c - 30, c + 30, c + 30), fill=(20, 20, 22))
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in ((("screen_code.jpg", code), ("screen_calendar.jpg", calendar), ("screen_sheet.jpg", sheet), ("screen_reception.jpg", reception), ("screen_mail.jpg", mail), ("screen_plan.jpg", plan),
                     ("screen_design.jpg", design), ("screen_game.jpg", game), ("ruler.jpg", ruler),
                     ("poster_road.jpg", poster), ("cork.jpg", cork), ("paper_layout.jpg", worn(highlighted(paper_layout, [((70, 585, 430, 642), "green")]), 7)),
                     ("paper_sprint.jpg", worn(highlighted(paper_sprint, [((150, 454, 520, 512), "yellow"), ((150, 814, 470, 872), "pink")]), 3)), ("paper_chart.jpg", worn(paper_chart, 13)),
                     ("paper_month.jpg", worn(highlighted(paper_month, [((584, 958, 700, 1054), "yellow"), ((328, 1174, 444, 1270), "orange")]), 5, 0.7)), ("photo_keyboard.jpg", photo_keyboard),
                     ("sticky_yellow.jpg", sticky((250, 230, 110), ["pick up", "badges", "@ 9:30"])),
                     ("sticky_pink.jpg", sticky((248, 160, 190), ["call IT", "re: VPN"])),
                     ("sticky_blue.jpg", sticky((150, 210, 240), ["Fri:", "demo day!"])),
                     ("clock_face.jpg", clock_face), ("paper_schematic.jpg", worn(highlighted(paper_schematic, [((320, 300, 760, 345), "orange"), ((880, 620, 1180, 662), "yellow")]), 11)),
                     ("sticky_green.jpg", sticky((170, 230, 140), ["backup", "Friday"])),
                     ("sticky_orange.jpg", sticky((250, 180, 100), ["pw reset", "ext. 214"])),
                     ("mat_topo.jpg", mat_topo), ("notepad_writing.png", notepad_writing), ("notepad_page.jpg", notepad_page),
                     ("wall_scuff.png", wall_scuff),
                     ("paper_back.jpg", worn(lambda: Image.new("RGB", (500, 650), (240, 238, 232)), 17, 0.6)),
                     ("sticky_wide.jpg", sticky((250, 235, 120), ["release v1.8 - Thu"], (1140, 760))),
                     ("art_arches.jpg", art_arches), ("paper_rota.jpg", worn(paper_rota, 19)), ("paper_phone.jpg", worn(paper_phone, 23)),
                     ("paper_desk_month.jpg", worn(paper_desk_month, 29, 0.6)), ("paper_wifi.jpg", worn(paper_wifi, 31)),
                     ("sticky_courier.jpg", sticky((250, 230, 110), ["courier", "14:00", "-> Lea"])))
                     + tuple((f"print_{n}.jpg", doc_print(n)) for n in DOC_PRINTS)
                     + tuple((f"spine_{i}.jpg", book_spine(i)) for i in range(len(BOOKS)))
                     + tuple((f"cover_{i}.jpg", book_cover(i)) for i in range(len(BOOKS)))
                     + tuple((f"back_{i}.jpg", book_back(i)) for i in range(len(BOOKS)))):
        im_ = fn()
        im_.save(os.path.join(OUT, name), **({} if name.endswith(".png") else {"quality": 88}))
        print("wrote", os.path.join("render", "textures", "workspace", name))
