"""Outline the camel-case "PolyKybd" wordmark (bold italic, 17 mm type) to one SVG path.

Uses Liberation Sans Bold Italic, which has Arial's metrics. On Debian/Ubuntu it is
the fonts-liberation package; pass another path as the first argument to use a
different face.
"""
import os, sys
import uharfbuzz as hb, pathops
from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.environ.get('TEE_OUT', os.path.dirname(HERE))
FP = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'
text = 'PolyKybd'; FS = 17.0; LS = 0.01 * FS   # size and letter spacing in mm
blob = hb.Blob.from_file_path(FP); font = hb.Font(hb.Face(blob))
buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(font, buf, {'kern': True, 'liga': True})
tt = TTFont(FP); gs = tt.getGlyphSet(); order = tt.getGlyphOrder(); s = FS / tt['head'].unitsPerEm
p = pathops.Path(); x = 0.0
for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
    gs[order[info.codepoint]].draw(TransformPen(p.getPen(glyphSet=gs), (s, 0, 0, -s, x + pos.x_offset * s, -pos.y_offset * s)))
    x += pos.x_advance * s + LS
p.simplify()
x0, y0, x1, y1 = p.bounds
sp = SVGPathPen(None, ntos=lambda v: ('%.3f' % v).rstrip('0').rstrip('.'))
q = pathops.Path(); p.draw(TransformPen(q.getPen(), (1, 0, 0, 1, -x0, -y0))); q.draw(sp)
w, h = x1 - x0, y1 - y0
open(os.path.join(OUT, 'polykybd-tee-2g-wordmark.svg'), 'w', encoding='utf-8').write(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.3f} {h:.3f}" width="{w:.3f}mm" height="{h:.3f}mm">
<title>PolyKybd wordmark, bold italic, outlined</title>
<path fill="#2f7bf6" d="{sp.getCommands()}"/>
</svg>
''')
print(f'{w:.1f} x {h:.1f} mm')
