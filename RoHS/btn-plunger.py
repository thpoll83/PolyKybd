import sys, subprocess, os, re
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

# Two 900x690 OpenSCAD renders of parts/case/btn_plungers.scad (part="one").
# Build artefacts, not committed - point RENDERS at wherever they were made.
#   pG outside  14,-17,11,0,0,0      pH inside  -14,-17,11,0,0,0
S = os.environ.get('RENDERS', '/tmp/btn-renders')

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
travel, act_reach = P('btn_travel'), P('btn_act_reach')
body_front, body_w, act_w = P('btn_body_front'), P('btn_body_w'), P('btn_act_w')

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

f = Fig(1540, 1340)
f.title('Reset / boot opening: the plunger that closes it',
        'Plan section through one button. EMC-700 left ±8 kV air discharge NOT RATED here — these are',
        'the points where the keyboard RESTARTED, and at 6.0 × 3.0 mm they are the biggest holes in the case.')


EXT = 4.8      # how much case to draw either side of the opening

def draw(A, dx, show_dims):
    """dx = how far the plunger is pressed in."""
    hw, hcb = W / 2, CB / 2
    # case: wall + ledge, with the opening and the counterbore cut out of it
    f.poly([A((OUT, -EXT)), A((IN_LO, -EXT)), A((IN_LO, -hcb)), A((IN_HI, -hcb)),
            A((IN_HI, -hw)), A((OUT, -hw))], C.BOX, C.DIM, sw=2)
    f.poly([A((OUT, EXT)), A((IN_LO, EXT)), A((IN_LO, hcb)), A((IN_HI, hcb)),
            A((IN_HI, hw)), A((OUT, hw))], C.BOX, C.DIM, sw=2)
    # the switch: body, then the actuator sticking out of it
    f.poly([A((BODY, -body_w/2)), A((IN_LO + 2.6, -body_w/2)),
            A((IN_LO + 2.6, body_w/2)), A((BODY, body_w/2))], C.MUT, C.DIM, sw=1.5)
    f.poly([A((ACT + dx, -0.8)), A((BODY, -0.8)), A((BODY, 0.8)), A((ACT + dx, 0.8))],
           C.AMB, C.AMB, sw=1.5, op=.85)
    # the plunger: nose through the wall, two ears behind the shoulder
    g = gap
    nose_f, nose_b = OUT + dx, IN_HI + dx
    # ⚠️ every step needs BOTH of its corners. Jumping from the ear's inner edge
    # straight to the pocket draws a diagonal across the nose, which renders as a
    # pinched waist that is nowhere in the part.
    f.poly([A((nose_f, -hw + g)), A((nose_b, -hw + g)),
            A((nose_b, -hcb + g)), A((nose_b + ear_t, -hcb + g)),
            A((nose_b + ear_t, -body_w/2 - g)), A((nose_b, -body_w/2 - g)),
            A((nose_b, -act_w/2)), A((ACT + dx, -act_w/2)),
            A((ACT + dx, act_w/2)), A((nose_b, act_w/2)),
            A((nose_b, body_w/2 + g)), A((nose_b + ear_t, body_w/2 + g)),
            A((nose_b + ear_t, hcb - g)), A((nose_b, hcb - g)),
            A((nose_b, hw - g)), A((nose_f, hw - g))],
           C.GRN, C.GRN, sw=2, op=.45)
    if show_dims:
        f.dim_h(A((OUT, 0))[0], A((IN_HI, 0))[0], 648, C.GRN, f'nose {IN_HI-OUT:.1f}')
        f.dim_h(A((IN_HI, 0))[0], A((IN_LO, 0))[0], 690, C.BLU,
                f'counterbore {IN_LO-IN_HI:.1f}')


SC = 40
f.panel(40, 170, 720, 540, 'A — at rest',
        'the switch spring holds the ears on the shoulder, so the nose is flush')
A = Fig.frame(scale=SC, ox=300, oy=430)
draw(A, 0.0, True)

f.panel(780, 170, 720, 540, f'B — pressed {travel} mm',
        'the switch stops it, not the case — the ears never reach the body')
B = Fig.frame(scale=SC, ox=1040, oy=430)
draw(B, travel, False)

f.panel(40, 730, 720, 390, 'C — the part, from outside', 'nose 6.0 × 3.0, the face you press')
f.image(f'{S}/pG.png', 70, 796, 660, 316, clip=(40, 730, 720, 390))
f.panel(780, 730, 720, 390, 'D — the part, from inside',
        'two ears, and the blind pocket the actuator pushes on')
f.image(f'{S}/pH.png', 810, 796, 660, 316, clip=(780, 730, 720, 390))

f.footer(f'The only path left is the sliding fit: {gap} mm per face, {2*(W+3.0)*gap:.1f} mm² of slot against '
         f'{W*3.0:.0f} mm² of open window, {IN_LO-OUT:.1f} mm deep,',
         f'with a {ear} mm step and a corner on each long side. The part is cut back by travel + {gap} mm where '
         'the switch body is, so the ear plate clears it at',
         'FULL travel and not just at rest — the one position a static check never sees.',
         'READ from the btn_* parameters in case/case_polykybd_split72_lr.scad — the plunger and the hole come from',
         'the same modules, so they cannot drift. Switch: Panasonic EVQPUC02K side-push on the board underside',
         '(SW2/SW3), actuator 1.0 mm proud of its body and landing 0.53 mm outboard of the board edge. FOUR per',
         'keyboard; fit from the inside before the board. ⚠️ Unlike the bonded LED inserts, the protection here is',
         'DIMENSIONAL — it is the gap, and it is only as good as the print tolerance. Verify with check_btn_plunger.py.')
f.save(f'{REPO}/RoHS/btn-plunger.svg'); f.png()
print('figure written')
