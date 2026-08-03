"""Tiny stdlib-only SVG builder for dimensioned explanatory figures.

No dependencies — import it from a throwaway script in the scratchpad, compute the
geometry there, draw with these helpers, then Fig.png() and LOOK at the result.

    import sys; sys.path.insert(0, '<skill dir>')
    from figlib import Fig, C

    f = Fig(1500, 960)
    f.title('What the vendor measured', 'the sub-heading')
    p = f.panel(40, 130, 660, 740, 'A — plan view', '⌀7.0 mm overall')
    m = f.frame(scale=88, ox=375, oy=660)        # mm -> px, y flipped
    f.poly([m(q) for q in outline], C.AMB, C.AMB, op=.45)
    f.save('/tmp/.../fig.svg'); f.png()
"""
import base64
import html
import subprocess


class C:
    """Palette — matches the GitHub-dark look the PolyKybd figures use."""
    BG = '#0d1117'
    BOX = '#21262d'
    FG = '#e6edf3'
    DIM = '#8b949e'          # secondary text
    MUT = '#3d4756'          # context geometry (dashed outlines)
    AMB = '#f0b429'          # the subject
    RED = '#f85149'          # the problem
    GRN = '#3fb950'          # the proposed fix
    BLU = '#58a6ff'          # zoom boxes / leaders


class Fig:
    def __init__(self, w, h, bg=C.BG, font='monospace'):
        self.w, self.h = w, h
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" '
                  f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
                  f'viewBox="0 0 {w} {h}" font-family="{font}">',
                  f'<rect width="{w}" height="{h}" fill="{bg}"/>']
        self._clip = 0
        self.path = None

    # ---- primitives --------------------------------------------------------
    def txt(self, x, y, s, size=17, fill=C.FG, anchor='start', bold=False):
        # Escaped, or a label with & or < silently produces invalid SVG -- and
        # labels are routinely built from filenames and measured values.
        w = 'bold' if bold else 'normal'
        s = html.escape(str(s), quote=False)
        self.o.append(f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
                      f'text-anchor="{anchor}" font-weight="{w}">{s}</text>')

    def line(self, a, b, col, sw=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" '
                      f'y2="{b[1]:.1f}" stroke="{col}" stroke-width="{sw}"{d}/>')

    def poly(self, pts, fill, stroke, sw=2, op=1.0, dash=None, close=True):
        d = 'M ' + ' L '.join(f'{p[0]:.2f},{p[1]:.2f}' for p in pts) + (' Z' if close else '')
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.o.append(f'<path d="{d}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" '
                      f'stroke-width="{sw}"{da}/>')

    def dot(self, p, col, r=3):
        self.o.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r}" fill="{col}"/>')

    def rect(self, x, y, w, h, stroke, fill='none', sw=2):
        self.o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                      f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def ellipse(self, cx, cy, rx, ry, stroke, sw=3):
        self.o.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" '
                      f'fill="none" stroke="{stroke}" stroke-width="{sw}"/>')

    # ---- structure ---------------------------------------------------------
    def title(self, main, sub=None, sub2=None, x=40):
        self.txt(x, 46, main, 26, C.FG, bold=True)
        if sub:
            self.txt(x, 76, sub, 17, C.DIM)
        if sub2:
            self.txt(x, 100, sub2, 17, C.DIM)

    def panel(self, x, y, w, h, label=None, note=None):
        self.rect(x, y, w, h, C.BOX, sw=1)
        if label:
            self.txt(x + 20, y + 32, label, 19, C.FG)
        if note:
            self.txt(x + 20, y + 56, note, 15, C.MUT)
        return (x, y, w, h)

    def footer(self, *lines, x=40, size=16):
        """Bottom notes, laid out upward from the canvas bottom."""
        for i, s in enumerate(reversed(lines)):
            self.txt(x, self.h - 22 - i * 24, s, size, C.DIM)

    @staticmethod
    def frame(scale, ox, oy):
        """Return a mm -> px mapper.  y is flipped (CAD up = screen up)."""
        return lambda p: (ox + p[0] * scale, oy - p[1] * scale)

    def leader(self, frm, to, col, sw=1.5, dash='3 3'):
        self.line(frm, to, col, sw, dash)

    def dim_h(self, x0, x1, y, col, label, size=20, tick=7):
        """Horizontal dimension bar with end ticks and a centred label below."""
        self.line((x0, y), (x1, y), col, 2.5)
        for x in (x0, x1):
            self.line((x, y - tick), (x, y + tick), col, 2.5)
        self.txt((x0 + x1) / 2, y + 34, label, size, col, anchor='middle', bold=True)

    # ---- raster ------------------------------------------------------------
    def image(self, png_path, x, y, w, h, clip=None):
        """Embed a PNG by value (base64).  Relative hrefs are fragile — don't.

        clip = (x, y, w, h) keeps a scaled-up render off the title/footer."""
        b64 = base64.b64encode(open(png_path, 'rb').read()).decode()
        cp = ''
        if clip:
            self._clip += 1
            cid = f'clip{self._clip}'
            self.o.append(f'<clipPath id="{cid}"><rect x="{clip[0]}" y="{clip[1]}" '
                          f'width="{clip[2]}" height="{clip[3]}"/></clipPath>')
            cp = f' clip-path="url(#{cid})"'
        self.o.append(f'<image{cp} x="{x:.1f}" y="{y:.1f}" width="{w:.0f}" height="{h:.0f}" '
                      f'xlink:href="data:image/png;base64,{b64}"/>')

    # ---- output ------------------------------------------------------------
    def save(self, path):
        open(path, 'w').write('\n'.join(self.o + ['</svg>']))
        self.path = path
        return path

    def png(self, out=None, width=None):
        """rsvg-convert the saved SVG.  Read the PNG back and LOOK at it."""
        out = out or self.path.rsplit('.', 1)[0] + '.png'
        subprocess.run(['rsvg-convert', '-w', str(width or self.w), self.path, '-o', out],
                       check=True)
        return out
