#!/usr/bin/env python3
"""Trace the plate mask (white = silkscreen) to an SVG in mm with potrace.

    python3 trace_svg.py MASK.png OUT.svg [px_per_mm]

The SVG origin is the plate's top-left corner (5 mm outside the top-left key), units mm,
for KiCad's SVG import onto the silkscreen layer.
"""
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

NOTICE = """<!-- Rongorongo Tablet B (Aruku-Kurenga), verso. Photograph Trocadero Museum, published in
     S.-C. Chauvet, L'ile de Paques et ses mysteres, 1935. CC BY-SA 3.0 (Wikimedia Commons,
     File:Rongorongo_B-v_Aruku-Kurenga.jpg). Traced for the PolyKybd split72s plate; this
     tracing is CC BY-SA 4.0, see ATTRIBUTION.md. Origin: plate top-left corner, units mm. -->"""


def main():
    mask, out = sys.argv[1], sys.argv[2]
    res = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
    if not res > 0:
        raise SystemExit(f"px_per_mm must be > 0, got {sys.argv[3]}")
    m = np.asarray(Image.open(mask).convert("L")) > 127
    with tempfile.TemporaryDirectory() as tmp:
        pbm, raw = f"{tmp}/mask.pbm", f"{tmp}/raw.svg"
        Image.fromarray(((~m) * 255).astype(np.uint8)).convert("1").save(pbm)   # potrace traces black
        subprocess.run(["potrace", "-s", "-t", "2", "-a", "1.0", "-O", "0.2", "-o", raw, pbm], check=True)
        g = re.search(r"(<g transform=.*</g>)", open(raw).read(), re.S).group(1)
    h, w = m.shape
    pw, ph = w / res, h / res
    open(out, "w", encoding="utf-8").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw:.3f}mm" height="{ph:.3f}mm" viewBox="0 0 {pw:.3f} {ph:.3f}">\n'
        f'{NOTICE}\n<g transform="scale({1 / res})" fill="#000">{g}</g>\n</svg>\n')
    print(f"{out}: {pw:.2f} x {ph:.2f} mm, {len(re.findall('<path', g))} paths")


if __name__ == "__main__":
    main()
