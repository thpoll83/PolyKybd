#!/usr/bin/env python3
"""Build plate_trace_tool.html from plate_trace_tool.template.html.

    python3 make_trace_tool.py                       # -> plate_trace_tool.html, load the photo in the page
    python3 make_trace_tool.py --image PHOTO --out OUT.html   # embed a photo (keep its licence in mind)

The page places the layout E plate on a photo (move, rotate, scale, stretch), shows how
much of the plate lies on the tablet, traces the strokes (threshold over a blurred
background, grow/shrink, speck and hole removal, silk min width check) and exports the
mask PNG for potrace and the settings JSON.
"""
import argparse
import base64
import json
import mimetypes
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def script_safe(js):
    """JSON inside <script>: "</" would end the element (a file name such as "</script>.jpg")."""
    return js.replace("</", "<\\/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="photo to embed")
    ap.add_argument("--out", default=os.path.join(HERE, "plate_trace_tool.html"))
    ap.add_argument("--settings", help="settings JSON to use as the page defaults")
    a = ap.parse_args()
    d = json.load(open(os.path.join(HERE, "layout_e_keys.json"), encoding="utf-8"))
    layout = {"margin": 5.0, "cut": d["cut"],
              "keys": [{"x": k["x"], "w": k["w"], "row": k["row"], "half": k["half"]} for k in d["keys"]]}
    image = "null"
    if a.image:
        mime = mimetypes.guess_type(a.image)[0] or "image/jpeg"
        b64 = base64.b64encode(open(a.image, "rb").read()).decode()
        image = json.dumps({"src": f"data:{mime};base64,{b64}", "name": os.path.basename(a.image)})
    defaults = json.dumps(json.load(open(a.settings, encoding="utf-8"))) if a.settings else "null"
    t = open(os.path.join(HERE, "plate_trace_tool.template.html"), encoding="utf-8").read()
    t = (t.replace("/*LAYOUT*/null", script_safe(json.dumps(layout))).replace("/*IMAGE*/null", script_safe(image))
          .replace("/*DEFAULTS*/null", script_safe(defaults)))
    open(a.out, "w", encoding="utf-8").write(t)
    print(a.out, f"{len(t) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
