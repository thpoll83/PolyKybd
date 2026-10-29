"""The reset/boot plunger shown IN the case, from the real geometry.

Self-contained: it exports the four STLs it needs out of the case file, renders
them headless and composes the figure.  Build artefacts go to $WORK (default a
tmp dir) and are reused if already there - the case slice is a ~3 min CGAL
evaluation, so deleting them costs real time.

    python3 RoHS/btn-plunger-in-case.py            # build what is missing
    WORK=/tmp/btn FORCE=1 python3 ...              # rebuild everything
"""
import os, re, subprocess, sys
from PIL import Image

REPO = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                      cwd=os.path.dirname(os.path.abspath(__file__)),
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

CASE = f'{REPO}/parts/case/case_polykybd_split72_lr.scad'
W = os.environ.get('WORK', '/tmp/btn-in-case')
FORCE = bool(os.environ.get('FORCE'))
os.makedirs(W, exist_ok=True)

# ---- the parameters, READ from the case file -------------------------------
# A second copy of a number is a copy that can disagree with the part.
_SRC = open(CASE, encoding='utf-8').read()
def P(n):
    m = re.search(rf'^{n}\s*=\s*([-0-9.]+)\s*;', _SRC, re.M)
    if not m:
        raise SystemExit(f'{n} not found in the case file')
    return float(m.group(1))

gap, ear, ear_t = P('btn_slide_gap'), P('btn_ear'), P('btn_ear_t')
post, br_h, br_t = P('btn_post'), P('btn_bridge_h'), P('btn_bridge_t')
cham, tol = P('btn_chamfer'), P('btn_switch_tol')
_m = re.search(r'^btn_c\s*=\s*\[\s*([-0-9.]+)\s*,\s*([-0-9.]+)', _SRC, re.M)
C0 = float(_m.group(1))

# The buttons sit on the +x wall of the right half.  led_band_r()'s radial
# coordinate maps to x here as x = XR + r, with the outer face at r = 1.65.
XR = 183.198
def X(r): return XR + r


def scad(name, body):
    """Write a driver .scad beside the artefacts and CGAL-export it."""
    out = f'{W}/{name}.stl'
    if os.path.exists(out) and not FORCE:
        return out
    src = f'{W}/{name}.scad'
    open(src, 'w').write(f'use <{CASE}>\n{body}\n')
    print(f'  exporting {name} ...', flush=True)
    subprocess.run(['openscad', '-o', out, '--export-format', 'binstl', src],
                   check=True, capture_output=True)
    return out


def render(name, body, cam, size, ortho=False):
    """Preview-mode render of imported STLs.  Preview, not --render=cgal, so the
    explicit color() per part is honoured: there is no CSG left to tint."""
    out = f'{W}/{name}.png'
    if os.path.exists(out) and not FORCE:
        return out
    src = f'{W}/{name}.scad'
    open(src, 'w').write(body)
    cmd = ['xvfb-run', '-a', 'openscad', '-o', out,
           f'--imgsize={size[0]},{size[1]}', f'--camera={cam}',
           '--colorscheme=Tomorrow Night', src]
    if ortho:
        cmd.insert(-1, '--projection=o')
    print(f'  rendering {name} ...', flush=True)
    subprocess.run(cmd, check=True, capture_output=True)
    if os.path.getsize(out) == 0:
        raise SystemExit(f'{name}: empty PNG - no display?')
    return out


# ---- geometry ---------------------------------------------------------------
# A box around the two openings, and the same box cut on the left button's
# centreline for the section.
BOX = 'translate([174, 74, -1]) cube([14, 27, 19]);'
HALF = f'translate([170, 74, -1]) cube([20, {C0 - 74:.2f}, 19]);'
scad('slice_full', f'intersection() {{ right_case(); {BOX} }}')
scad('slice_cut', f'intersection() {{ right_case(); {BOX} {HALF} }}')
scad('plg_full', 'btn_plunger();')
scad('plg_cut', f'intersection() {{ btn_plunger(); {HALF} }}')

PAIR = ('color("#8b949e") import("slice_full.stl");\n'
        'color("#3fb950") import("plg_full.stl");\n')
# The switch is NOT modelled anywhere in the case file - only the envelope it
# must be kept out of is.  Drawn here from the EVQPUC02K datasheet box so the
# section reads, and coloured as context, not as geometry.
SECT = (f'color("#8b949e") import("slice_cut.stl");\n'
        f'color("#3fb950") import("plg_cut.stl");\n'
        f'color("#f0b429") {{\n'
        f'  translate([{X(-0.47) - 3.5:.3f}, {C0 - 2.35:.2f}, 9.35]) cube([3.5, 4.7, 2.5]);\n'
        f'  translate([{X(-0.47):.3f}, {C0 - 1.1:.2f}, 10.1]) cube([1.0, 2.2, 1.0]);\n'
        f'}}\n')
PART = 'color("#3fb950") import("plg_full.stl");\n'

render('pA', PAIR, '183,87.6,9.5,72,0,120,46', (1100, 760))
render('pB', PAIR, '183,87.6,9.5,72,0,300,48', (1100, 760))
render('pC', SECT, '182.5,83.0,9.6,88,0,183,17', (700, 560), ortho=True)
render('pD', PART, '183.6,87.6,9.3,62,0,300,44', (900, 700))


# ---- the figure -------------------------------------------------------------
def content(path):
    """The render's own ink box, so a panel is filled by the PART rather than by
    the dark margin OpenSCAD leaves around a thin slice."""
    im = Image.open(path).convert('RGB')
    px, (w, h) = im.load(), im.size
    bg = px[2, 2]
    x0, y0, x1, y1 = w, h, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            p = px[x, y]
            if abs(p[0]-bg[0]) + abs(p[1]-bg[1]) + abs(p[2]-bg[2]) > 24:
                x0, y0 = min(x0, x), min(y0, y)
                x1, y1 = max(x1, x), max(y1, y)
    return im.size, (x0, y0, x1 - x0, y1 - y0)


f = Fig(1480, 1300)

def place(name, area):
    (sw, sh), (cx, cy, cw, ch) = content(f'{W}/{name}.png')
    ax, ay, aw, ah = area
    s = min(aw / cw, ah / ch)
    f.image(f'{W}/{name}.png', ax + (aw - cw*s)/2 - cx*s,
            ay + (ah - ch*s)/2 - cy*s, sw*s, sh*s, clip=area)

f.title('The reset / boot plunger, fitted in the case',
        'Renders of the real geometry — the case sliced around the two switch openings (grey) with the plunger pair in place (green).',
        'Both come out of the same btn_* modules in parts/case/case_polykybd_split72_lr.scad, so the part and the hole cannot drift apart.')

f.panel(30, 150, 705, 500, 'A — from outside',
        f'the two noses sit flush in the wall, {gap} mm all round')
place('pA', (42, 224, 681, 414))

f.panel(745, 150, 705, 500, 'B — from inside',
        'ears on the shoulder, bar in its slot, posts at the two ends')
place('pB', (757, 224, 681, 414))

f.panel(30, 670, 705, 440, 'C — section on the left button centreline',
        'the switch (amber) drawn from its datasheet box, not modelled')
place('pC', (42, 744, 681, 354))

f.panel(745, 670, 705, 440, 'D — the part on its own',
        f'one part per half: two plungers, a {br_t} × {br_h} mm bar, {post} mm posts')
place('pD', (757, 744, 681, 354))

f.footer('Fitted from the inside before the board goes in: the bar drops into the slot along the bottom of the pocket',
         'and locates the part, then the two noses push out through the wall. The switch’s own return spring holds',
         'the ears against the shoulder, which is what keeps the noses flush with the outer face.',
         f'Pressing one plunger bends the {post} mm-anchored beam between them, so about 0.16 N reaches the other,',
         'against the ~2.5 N its own switch needs.',
         f'Unlike the bonded LED inserts the protection here is DIMENSIONAL: it is the {gap} mm sliding gap,',
         'and only as good as the print tolerance. Verified by parts/case/check_btn_plunger.py (12 checks).')
f.save(f'{REPO}/RoHS/btn-plunger-in-case.svg')
f.png()
print('figure written')
