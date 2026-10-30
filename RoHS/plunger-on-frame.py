"""The reset/boot plunger pair as it is DELIVERED: riding on the diffuser frame.

Self-contained -- it exports the pieces out of the generated frame, renders them
headless and composes the figure.  Artefacts go to $WORK and are reused.

    python3 RoHS/plunger-on-frame.py
    WORK=/tmp/pof FORCE=1 python3 RoHS/plunger-on-frame.py
"""
import os, re, subprocess, sys
from PIL import Image

REPO = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                      cwd=os.path.dirname(os.path.abspath(__file__)),
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

SIDE = 'left'
FRAME = f'{REPO}/parts/diffuser/diffuser_frame_{SIDE}.scad'
W = os.environ.get('WORK', '/tmp/plunger-on-frame')
FORCE = bool(os.environ.get('FORCE'))
os.makedirs(W, exist_ok=True)

src = open(FRAME, encoding='utf-8').read()
REV = re.search(r'^//\s+revision\s+(\S+)', src, re.M).group(1)
# The generator prints these into the module comment, so the figure cannot
# disagree with the part about how much room it actually has.
# ⚠️ SCOPED to the text above the plungers module. The insert row's comment
# carries the same sentence and comes first in the file, so an unscoped search
# captions the plunger with the LED row's clearance -- which it did, and the
# figure looked perfectly plausible with the wrong number on it.
_head = src[:src.index(f'module diffuser_frame_{SIDE}_plungers')]
CLR = float(re.findall(r'clearance to the rest of the frame: ([\d.]+) mm', _head)[-1])
OPEN = float(re.search(r'([\d.]+) mm of open lane here', _head).group(1))


def scad(name, body):
    out = f'{W}/{name}.stl'
    if os.path.exists(out) and not FORCE:
        return out
    open(f'{W}/{name}.scad', 'w').write(f'use <{FRAME}>\n{body}\n')
    print(f'  exporting {name} ...', flush=True)
    subprocess.run(['openscad', '-o', out, '--export-format', 'binstl',
                    f'{W}/{name}.scad'], check=True, capture_output=True)
    return out


def render(name, body, cam, size, ortho=False):
    """Preview mode, not --render=cgal: CGAL rendering returns ONE solid colour,
    and the whole point here is which part is which."""
    out = f'{W}/{name}.png'
    if os.path.exists(out) and not FORCE:
        return out
    open(f'{W}/{name}.scad', 'w').write(body)
    cmd = ['xvfb-run', '-a', 'openscad', '-o', out, f'--imgsize={size[0]},{size[1]}',
           '--colorscheme=Tomorrow Night']
    cmd += (['--viewall', '--autocenter'] if cam is None else [f'--camera={cam}'])
    if ortho:
        cmd.append('--projection=o')
    cmd.append(f'{W}/{name}.scad')
    print(f'  rendering {name} ...', flush=True)
    subprocess.run(cmd, check=True, capture_output=True)
    if os.path.getsize(out) == 0:
        raise SystemExit(f'{name}: empty PNG - no display?')
    return out


M = f'diffuser_frame_{SIDE}'
scad('base', f'difference() {{ union() {{ {M}_diffusers(); {M}_web(); }} {M}_revision(); }}')
scad('ins', f'{M}_inserts();')
scad('plg', f'{M}_plungers();')
scad('fitted', f'{M}_fitted();')

WHOLE = ('color("#8b949e") import("base.stl");\n'
         'color("#f0b429") import("ins.stl");\n'
         'color("#3fb950") import("plg.stl");\n')
FITTED = 'color("#8b949e") import("fitted.stl");\n'

render('top', WHOLE, None, (1500, 1000))
render('zoom', WHOLE, '-45,3,0.5,64,0,210,34', (1100, 820))
render('stub', FITTED, '-39.1,2.7,-0.4,72,0,205,7', (900, 700))


def content(path):
    im = Image.open(path).convert('RGB')
    px, (sw, sh) = im.load(), im.size
    bg = px[2, 2]
    x0, y0, x1, y1 = sw, sh, 0, 0
    for y in range(0, sh, 2):
        for x in range(0, sw, 2):
            q = px[x, y]
            if abs(q[0]-bg[0]) + abs(q[1]-bg[1]) + abs(q[2]-bg[2]) > 24:
                x0, y0 = min(x0, x), min(y0, y)
                x1, y1 = max(x1, x), max(y1, y)
    return im.size, (x0, y0, x1 - x0, y1 - y0)


f = Fig(1480, 1360)

def place(name, area):
    (sw, sh), (cx, cy, cw, ch) = content(f'{W}/{name}.png')
    ax, ay, aw, ah = area
    s = min(aw / cw, ah / ch)
    f.image(f'{W}/{name}.png', ax + (aw - cw*s)/2 - cx*s,
            ay + (ah - ch*s)/2 - cy*s, sw*s, sh*s, clip=area)

f.title(f'How the plunger pair is delivered: on the diffuser frame ({REV})',
        'Both EMC parts ride on the frame that was going to be printed anyway, on V-scored webs, and are snapped off before it is fitted.',
        'Frame and diffusers grey, the three status-LED window inserts amber, the reset/boot plunger pair green.')

f.panel(30, 150, 1420, 500, f'A — the {SIDE} frame as printed',
        'one plunger pair per frame: it already carries both of that half’s plungers')
place('top', (42, 224, 1396, 414))

f.panel(30, 670, 705, 380, 'B — the plunger in its lane',
        f'{CLR:.2f} mm to the rail it hangs on, {OPEN:.2f} mm of open lane around it')
place('zoom', (42, 744, 681, 294))

f.panel(745, 670, 705, 380, 'C — the frame as fitted',
        'carried parts snapped off; only the web’s root half stays on the rail')
place('stub', (757, 744, 681, 294))

f.footer('It lies on its BACK — travel axis into the web — so it is 2.5 mm tall and the frame’s height is unchanged at -1.00..2.70 mm.',
         'Stood on edge it would fit a narrower gap and add that to every layer of a 153 x 101 mm print.',
         'The lane is chosen by OPENNESS, not by clearance: every candidate sits the same distance from the rail it hangs on, so clearance ties',
         'and the choice falls through to the tiebreak. The generator refuses to emit a colliding one.',
         '✅ ONE part serves both halves. left_case() mirrors the right, so the left pocket is a mirror image — but the plunger has a mirror plane',
         'at the pair’s midline (0.01 mm³ of asymmetry against a 4.10 mm³ control), so it is achiral. Placed by rotate(), never mirror().',
         '⚠️ It therefore comes out in CLEAR resin, like the diffusers it shares the print with. parts/case/btn_plungers.scad stays as the',
         'standalone if the service buttons have to match the case — a visual call, not a technical one.')
f.save(f'{REPO}/RoHS/plunger-on-frame.svg')
f.png()
print('figure written')
