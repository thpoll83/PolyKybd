import sys, subprocess, os, re
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

# Panel D is a render of the EXPORTED part, made here rather than by hand: a
# figure that depends on a build artefact someone made once cannot be redrawn
# when the part changes, and this one could not (the /tmp renders were gone the
# first time the part moved). Preview mode, not --render=cgal: the colour is the
# point, and with the CSG already resolved into an STL there is nothing left for
# OpenCSG to tint.
S = os.environ.get('WORK', '/tmp/btn-plunger-fig')
os.makedirs(S, exist_ok=True)
if not os.path.exists(f'{S}/pH.png') or os.environ.get('FORCE'):
    open(f'{S}/pH.scad', 'w').write(
        f'color("#3fb950") import("{REPO}/parts/export/case/btn_plungers.stl");\n')
    subprocess.run(['xvfb-run', '-a', 'openscad', '-o', f'{S}/pH.png',
                    '--imgsize=900,700', '--camera=183.6,87.6,9.3,62,0,300,44',
                    '--colorscheme=Tomorrow Night', f'{S}/pH.scad'],
                   check=True, capture_output=True)
    if os.path.getsize(f'{S}/pH.png') == 0:
        raise SystemExit('empty PNG - no display?')

# ---- geometry, READ from the case parameters -------------------------------
# Not restated: this drawing is what the CE file cites for the fit, and a second
# copy of the numbers is a copy that can disagree with the part.
_SRC = open(f'{REPO}/parts/case/case_polykybd_split72_lr.scad', encoding='utf-8').read()
def P(name):
    m = re.search(rf'^{name}\s*=\s*([-0-9.]+)\s*;', _SRC, re.M)
    if not m:
        raise SystemExit(f'{name} not found in the case file')
    return float(m.group(1))

wall, clr, ledge = P('case_wall_thickness'), P('pcb_clearance'), P('pcb_edge_width')
gap, ear, ear_t = P('btn_slide_gap'), P('btn_ear'), P('btn_ear_t')
under, sep = P('btn_under'), P('btn_sep')
br_t, br_h, post = P('btn_bridge_t'), P('btn_bridge_h'), P('btn_post')
cham, bar_gap = P('btn_chamfer'), P('btn_bar_gap')
tol, act_reach = P('btn_switch_tol'), P('btn_act_reach')
act_w = P('btn_act_w') + 2 * tol
import re as _re
_m = _re.search(r'^btn_c\s*=\s*\[\s*([-0-9.]+)\s*,\s*([-0-9.]+)', _SRC, _re.M)
C0, C1 = float(_m.group(1)), float(_m.group(2))
Z0 = P('pcb_edge_height') - 0.4        # btn_z0, an expression in the scad
HH = 3.0                                # btn_h
travel, act_reach = P('btn_travel'), P('btn_act_reach')
body_front, body_w, act_w = P('btn_body_front'), P('btn_body_w'), P('btn_act_w')
pcb_gap = P('btn_pcb_gap')
LEDGE = P('case_bottom_thickness') + P('pcb_edge_height')   # btn_ledge_top(), 11.5
CAP = LEDGE - pcb_gap        # how high anything inboard of the wall may be built

# x runs INWARD from the outer face, as in led-insert-section.py
OUT   = -(wall + clr)          # -1.65  outer face
IN_HI = -clr                   # -0.15  wall inner face = the shoulder
IN_LO =  ledge - clr           # +1.25  ledge inner face
BODY  = -body_front            # +0.47  switch body front face (x runs INWARD
ACT   = BODY - 1.0             # -0.53  here, so the sign of btn_body_front flips)
W     = 6.0                    # the opening, along the wall (offset(2.5) on a
CB    = W + 2 * ear            # ~1.0 mm stroke), and the counterbore
print(f'  opening {W} x 3.0, counterbore {CB}, wall {IN_LO - OUT:.2f}')
print(f'  nose {IN_HI - OUT:.2f} long, ears {ear_t} thick, pocket {act_reach} deep')
print(f'  actuator tip at {ACT:+.2f}, switch body front at {BODY:+.2f}, travel {travel}')
print(f'  gap area {2 * (W + 3.0) * gap:.2f} mm2 against {W * 3.0:.1f} mm2 open')

f = Fig(1540, 1620)
f.title('Reset / boot opening: the plunger that closes it',
        'Plan section through one button. EMC-700 left ±8 kV air discharge NOT RATED here — these are the points',
        'where it RESTARTED, and at 6.0 × 3.0 mm the biggest holes in the case. Both plungers of a half are ONE part.')


EXT = 4.8      # how much case to draw either side of the opening

def draw(A, dx, show_dims):
    """dx = how far the plunger is pressed in."""
    # the pocket is cut to the furthest-OUT actuator, so at nominal there is
    # btn_switch_tol of slack before the actuator is even touched
    pock = IN_HI + act_reach + tol
    push = max(0.0, dx - tol)
    hw, hcb = W / 2, CB / 2
    # case: wall + ledge, with the opening and the counterbore cut out of it
    f.poly([A((OUT, -EXT)), A((IN_LO, -EXT)), A((IN_LO, -hcb)), A((IN_HI, -hcb)),
            A((IN_HI, -hw - cham)), A((IN_HI - cham, -hw)), A((OUT, -hw))],
           C.BOX, C.DIM, sw=2)
    f.poly([A((OUT, EXT)), A((IN_LO, EXT)), A((IN_LO, hcb)), A((IN_HI, hcb)),
            A((IN_HI, hw + cham)), A((IN_HI - cham, hw)), A((OUT, hw))],
           C.BOX, C.DIM, sw=2)
    # the switch: body, then the actuator sticking out of it
    f.poly([A((BODY, -body_w/2)), A((IN_LO + 2.6, -body_w/2)),
            A((IN_LO + 2.6, body_w/2)), A((BODY, body_w/2))], C.MUT, C.DIM, sw=1.5)
    f.poly([A((ACT + push, -0.8)), A((BODY, -0.8)), A((BODY, 0.8)),
            A((ACT + push, 0.8))], C.AMB, C.AMB, sw=1.5, op=.85)
    # the plunger: nose through the wall, two ears behind the shoulder
    g = gap
    nose_f, nose_b = OUT + dx, IN_HI + dx
    # ⚠️ every step needs BOTH of its corners. Jumping from the ear's inner edge
    # straight to the pocket draws a diagonal across the nose, which renders as a
    # pinched waist that is nowhere in the part.
    f.poly([A((nose_f, -hw + g)), A((nose_b - cham, -hw + g)),
            A((nose_b, -hw - cham + g)),
            A((nose_b, -hcb + g)), A((nose_b + ear_t, -hcb + g)),
            A((nose_b + ear_t, -body_w/2 - g)), A((nose_b, -body_w/2 - g)),
            A((nose_b, -act_w/2)), A((pock + dx, -act_w/2)),
            A((pock + dx, act_w/2)), A((nose_b, act_w/2)),
            A((nose_b, body_w/2 + g)), A((nose_b + ear_t, body_w/2 + g)),
            A((nose_b + ear_t, hcb - g)), A((nose_b, hcb - g)),
            A((nose_b, hw + cham - g)), A((nose_b - cham, hw - g)),
            A((nose_f, hw - g))],
           C.GRN, C.GRN, sw=2, op=.45)
    if show_dims:
        f.dim_h(A((OUT, 0))[0], A((IN_HI, 0))[0], 656, C.GRN, f'nose {IN_HI-OUT:.1f}')
        f.dim_h(A((IN_HI, 0))[0], A((IN_LO, 0))[0], 700, C.BLU,
                f'counterbore {IN_LO-IN_HI:.1f}')



def elevation(E):
    """Looking THROUGH the wall: y across, z up. This is the view the plan
    section cannot show - the pocket's z profile, and the bar sitting in it."""
    hw, hcb = W / 2, CB / 2
    lo, hi = C0 - hcb, C1 + hcb               # the merged pocket, end to end
    slot_t = Z0 - under + br_h + 2 * bar_gap  # top of the bar's slot
    f.poly([E((lo - 3.4, Z0 - under - 2.6)), E((hi + 3.4, Z0 - under - 2.6)),
            E((hi + 3.4, Z0 + HH + 2.2)), E((lo - 3.4, Z0 + HH + 2.2))],
           C.BOX, C.DIM, sw=2)
    # the pocket, and the island of case that makes the slot a slot
    f.poly([E((lo, Z0 - under)), E((hi, Z0 - under)),
            E((hi, Z0 + HH)), E((lo, Z0 + HH))], C.BG, C.BLU, sw=1.6, dash='5 3')
    f.poly([E((lo + post, slot_t)), E((hi - post, slot_t)),
            E((hi - post, Z0)), E((lo + post, Z0))], C.BOX, C.DIM, sw=1.6)
    # The EARS, behind the shoulder and therefore inboard of the wall: these are
    # what the board's seat caps. Drawn first and dimmer, with the noses over
    # them, because that is the order the eye needs to read the step.
    mid = (C0 + C1) / 2
    for a, b in ((lo + gap, mid - sep / 2), (mid + sep / 2, hi - gap)):
        f.poly([E((a, Z0 + gap)), E((b, Z0 + gap)), E((b, CAP)), E((a, CAP))],
               C.GRN, C.GRN, sw=1.6, op=.22)
    # the two noses in their holes - NOT capped: they are in the wall, which
    # carries on above the ledge, so they fill the opening to its full height
    for c in (C0, C1):
        f.poly([E((c - hw + gap, Z0 + gap)), E((c + hw - gap, Z0 + gap)),
                E((c + hw - gap, Z0 + HH - gap)), E((c - hw + gap, Z0 + HH - gap))],
               C.GRN, C.GRN, sw=2, op=.45)
    # The board on its ledge. A BAND, not a line: at 0.4 mm apart the seat and
    # the cap are 10 px apart at this scale, and two labelled lines there land
    # on top of each other and on the noses.
    f.poly([E((lo - 3.4, LEDGE)), E((hi + 3.4, LEDGE)),
            E((hi + 3.4, LEDGE + 1.6)), E((lo - 3.4, LEDGE + 1.6))],
           C.BLU, C.BLU, sw=1.6, op=.28)
    f.txt(*E((lo - 3.0, LEDGE + 1.05)), 'the board, on its ledge', 15, C.BLU)
    f.line(E((hi + 1.2, CAP)), E((hi + 1.2, LEDGE)), C.AMB, 2)
    for z in (CAP, LEDGE):
        f.line(E((hi + 0.9, z)), E((hi + 1.5, z)), C.AMB, 2)
    f.txt(*E((hi + 1.8, CAP + 0.05)), f'{pcb_gap}', 15, C.AMB, bold=True)
    # the bar in its slot, and the posts reaching down to it
    f.poly([E((lo + gap, Z0 - under + bar_gap)), E((hi - gap, Z0 - under + bar_gap)),
            E((hi - gap, Z0 - under + bar_gap + br_h)),
            E((lo + gap, Z0 - under + bar_gap + br_h))], C.GRN, C.GRN, sw=2, op=.45)
    for x0 in (lo + gap, hi - post - gap):
        f.poly([E((x0, Z0 - under + bar_gap)), E((x0 + post, Z0 - under + bar_gap)),
                E((x0 + post, CAP)), E((x0, CAP))],
               C.GRN, C.GRN, sw=2, op=.45)


SC = 40
f.panel(40, 170, 720, 580, 'A — at rest',
        'the spring holds the ears on the shoulder; the pocket is shared')
A = Fig.frame(scale=SC, ox=300, oy=430)
draw(A, 0.0, True)

f.panel(780, 170, 720, 580, f'B — pressed {travel + tol:.2f} mm',
        f'{tol} mm of slack for the switch, then its own {travel} mm of travel')
B = Fig.frame(scale=SC, ox=1040, oy=430)
draw(B, travel + tol, False)

f.panel(40, 790, 720, 430, 'C — elevation, through the wall',
        'the ears stop under the board; the bar drops into a slot along the bottom')
EL = Fig.frame(scale=25, ox=400 - 25 * (C0 + C1) / 2, oy=1225)
elevation(EL)
f.panel(780, 790, 720, 430, 'D — the pair, from inside',
        f'cut apart above, joined by a {post} mm-anchored beam below')
# Fit the render by its own INK box, not by its frame: OpenSCAD leaves a wide
# dark margin around a part this shape, and placing by the frame puts most of
# the panel's area into that margin.
def _place(path, area):
    from PIL import Image
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
    cw, ch = x1 - x0, y1 - y0
    ax, ay, aw, ah = area
    k = min(aw / cw, ah / ch)
    f.image(path, ax + (aw - cw*k)/2 - x0*k, ay + (ah - ch*k)/2 - y0*k,
            sw*k, sh*k, clip=(780, 866, 720, 348))

_place(f'{S}/pH.png', (800, 876, 680, 320))

f.footer(f'The only path left is the sliding fit: {gap} mm per face, {2*(W+3.0)*gap:.1f} mm² of slot against '
         f'{W*3.0:.0f} mm² of open window, {IN_LO-OUT:.1f} mm deep, with a {ear} mm step',
         f'and a corner on each long side. The board rests on a ledge {12.1 - LEDGE:.1f} mm below the top of the opening, so the '
         f'ears stop {pcb_gap} mm under its seat;',
         'the nose does not, because it is in the wall, which carries on above the ledge — and a notch at the top of the nose '
         'would widen that gap.',
         f'The part is cut back by travel + {tol} + {gap} mm where the switch body is, so the ear plate',
         f'clears it at FULL travel AND at either end of the switch\u2019s own \u00b1{tol} mm placement tolerance '
         '— positions a static check never sees.',
         f'The two plungers are cut {sep} mm apart above the bridge and the bridge touches them only at its two '
         f'ends, {post} mm each: that makes it a',
         f'13.4 mm flexure rather than a 1.0 mm weld, so pressing one costs ~0.16 N and puts ~0.16 N on the other '
         'against the ~2.5 N its switch needs.',
         'READ from the btn_* parameters in case/case_polykybd_split72_lr.scad — the plunger and the hole come from',
         'the same modules, so they cannot drift. Switch: Panasonic EVQPUC02K side-push on the board underside',
         '(SW2/SW3), actuator 1.0 mm proud of its body and landing 0.53 mm outboard of the board edge. TWO parts per',
         'keyboard, one per half, each carrying both of that half\u2019s plungers; fit from the inside,',
         f'before the board goes in. The pocket is cut to the furthest-out actuator, so the press runs through up '
         f'to {2*tol:.1f} mm of slack',
         f'first: {travel:.2f}–{travel + 2*tol:.2f} mm of plunger travel, not a flat {travel:.2f}. '
         'Unlike the bonded LED inserts, the protection here is',
         'DIMENSIONAL — it is the gap, and only as good as the print tolerance. Verify with check_btn_plunger.py.')
f.save(f'{REPO}/RoHS/btn-plunger.svg'); f.png()
print('figure written')
