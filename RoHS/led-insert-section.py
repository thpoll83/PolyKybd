import sys, subprocess
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

# ---- geometry, READ from the case parameters -------------------------------
# Not restated here. This drawing is the one the CE file cites for the fit, so a
# second copy of the numbers is a copy that can silently disagree with the part.
import re, math
_SRC = open(f'{REPO}/parts/case/case_polykybd_split72_lr.scad', encoding='utf-8').read()
def P(name):
    m = re.search(rf'^{name}\s*=\s*([-0-9.]+)\s*;', _SRC, re.M)
    if not m:
        raise SystemExit(f'{name} not found in the case file')
    return float(m.group(1))
def S(name):
    m = re.search(rf'^{name}\s*=\s*"([^"]*)"\s*;', _SRC, re.M)
    return m.group(1) if m else ''

case_wall_thickness, pcb_clearance = P('case_wall_thickness'), P('pcb_clearance')
pcb_edge_width = P('pcb_edge_width')
case_bottom_thickness, pcb_edge_height = P('case_bottom_thickness'), P('pcb_edge_height')
led_pocket_depth, led_pocket_overlap = P('led_pocket_depth'), P('led_pocket_overlap')
led_pocket_down, led_ledge_keep = P('led_pocket_down'), P('led_ledge_keep')
led_insert_gap, led_window_gap = P('led_insert_gap'), P('led_window_gap')
led_boss_lip = P('led_boss_lip')
led_window_mode = S('led_window_mode') or 'slot'
led_cone_d, led_cone_gap = P('led_cone_d'), P('led_cone_gap')
led_cone_half_angle = P('led_cone_half_angle')

OUT   = -(case_wall_thickness + pcb_clearance)      # outer wall face
IN_LO =  (pcb_edge_width - pcb_clearance)           # inner face of the PCB ledge
IN_HI = -pcb_clearance                              # inner face above the PCB
WALL_LO, WALL_HI = IN_LO - OUT, IN_HI - OUT
PCB_Z = case_bottom_thickness + pcb_edge_height     # PCB underside / ledge top
WZ0, WZ1 = pcb_edge_height - 0.1, pcb_edge_height - 0.1 + 2.20
REMAIN = WALL_LO - led_pocket_depth
LED_X = 4.553 - 1.1985                              # D5, inboard of the outline edge

def pocket(side):
    """(x0, x1, z0, z1) of the cavity the flange sits in."""
    z0 = WZ0 - led_pocket_down
    if side == 'inside':
        return IN_LO - led_pocket_depth, IN_LO, z0, PCB_Z - led_ledge_keep
    return OUT, OUT + led_pocket_depth, z0, PCB_Z

def flange(side):
    px0, px1, pz0, pz1 = pocket(side)
    g = led_insert_gap
    # flush with the open face, clearance at the floor
    x = (px0 + g, px1) if side == 'inside' else (px0, px1 - g)
    return x[0], x[1], pz0 + g, pz1 - g

for side in ('inside', 'outside'):
    print(f'  {side:8s} pocket {pocket(side)}  flange {flange(side)}')
print(f'  boss x {OUT} .. {IN_LO}  z {WZ0 + led_window_gap} .. {WZ1 - led_window_gap}')
print(f'  wall below the PCB {WALL_LO}, above {WALL_HI}, left under the pocket {REMAIN}')

f = Fig(1500, 1060)
f.title('Status-LED window: the ESD insert and the pocket that makes room for it',
        'Section through D5, on the window axis. EMC-700 left ±8 kV air discharge NOT RATED at these',
        'openings; the bonded insert means the opening does not exist on a shipped unit.')

def draw(A, side):
    px0, px1, pz0, pz1 = pocket(side)
    fx0, fx1, fz0, fz1 = flange(side)
    gw = led_window_gap
    # wall body, below and above the PCB underside
    f.poly([A((OUT,6.6)),A((IN_LO,6.6)),A((IN_LO,PCB_Z)),A((IN_HI,PCB_Z)),
            A((IN_HI,13.2)),A((OUT,13.2))], C.BOX, C.DIM, sw=2)
    # the window through it, and the pocket
    f.poly([A((OUT,WZ0)),A((IN_LO,WZ0)),A((IN_LO,WZ1)),A((OUT,WZ1))], C.BG, C.MUT, sw=1.5, dash='4 3')
    f.poly([A((px0,pz0)),A((px1,pz0)),A((px1,pz1)),A((px0,pz1))], C.BG, C.BLU, sw=2, dash='5 3')
    # the insert: the boss through the window, and the flange in the pocket
    g, L = led_insert_gap, OUT + led_boss_lip
    if led_window_mode == 'cone':
        # A cone of revolution about the window's axis, so this section through
        # the axis is a plain trapezoid: Ø led_cone_d at the outer face opening
        # to Ø base at the WALL's inner face, then a cylinder through the ledge.
        # Only the wall is tapered - running the taper the whole 2.9 mm would
        # open it past the flange it has to sit inside.
        t = math.tan(math.radians(led_cone_half_angle))
        base = led_cone_d + 2 * (IN_HI - OUT) * t
        dr = led_cone_gap / math.cos(math.radians(led_cone_half_angle))
        mid = ((WZ0 - led_pocket_down) + WZ1) / 2          # led_insert_z_mid()
        r0, r1 = led_cone_d / 2 - dr, base / 2 - dr
        rc = base / 2 - led_window_gap
        cap = min(pz1 - g, mid + rc)
        # ⚠️ the dashed cut goes FIRST: f.poly fills, and C.BG over the green
        # cone paints it out - which looks exactly like a cone that failed to
        # draw rather than one that was covered.
        f.poly([A((OUT, mid - led_cone_d/2)), A((IN_HI, mid - base/2)),
                A((IN_LO, mid - base/2)), A((IN_LO, mid + base/2)),
                A((IN_HI, mid + base/2)), A((OUT, mid + led_cone_d/2))],
               C.BG, C.MUT, sw=1.5, dash='4 3')
        f.poly([A((OUT, mid - r0)), A((IN_HI, mid - r1)), A((IN_LO, mid - rc)),
                A((IN_LO, cap)), A((IN_HI, cap)), A((IN_HI, mid + r1)),
                A((OUT, mid + r0))],
               C.GRN, C.GRN, sw=2, op=.45)
    else:
        # The boss is relieved where it would otherwise run under the ledge the
        # board rests on (inboard of IN_HI, above the pocket top). On the outside
        # fit the pocket already reaches the ledge top, so the cap is above the
        # boss and the relief is a no-op - hence the min().
        cap = min(pz1 - g, WZ1 - gw)
        f.poly([A((OUT,WZ0+g)),A((L,WZ0+g)),A((L,WZ0+gw)),A((IN_LO,WZ0+gw)),
                A((IN_LO,cap)),A((IN_HI,cap)),A((IN_HI,WZ1-gw)),
                A((L,WZ1-gw)),A((L,WZ1-g)),A((OUT,WZ1-g))],
               C.GRN, C.GRN, sw=2, op=.45)
    f.poly([A((fx0,fz0)),A((fx1,fz0)),A((fx1,fz1)),A((fx0,fz1))], C.GRN, C.GRN, sw=2, op=.45)
    # PCB + the LED behind the window
    f.poly([A((IN_HI,PCB_Z)),A((5.0,PCB_Z)),A((5.0,PCB_Z+1.1)),A((IN_HI,PCB_Z+1.1))],
           C.MUT, C.DIM, sw=1.5)
    f.poly([A((LED_X-1.0,PCB_Z-0.9)),A((LED_X+1.0,PCB_Z-0.9)),A((LED_X+1.0,PCB_Z)),
            A((LED_X-1.0,PCB_Z))], C.AMB, C.AMB, sw=1.5, op=.8)

SC = 62
# ---- panel A: as built ----
f.panel(40, 150, 690, 790, 'A — as built: fitted from the INSIDE',
        'green = insert, blue dashed = pocket, grey dashed = the window')
A = Fig.frame(scale=SC, ox=222, oy=1189)
draw(A, 'inside')
f.txt(62, 242, 'the outer surface is untouched — no pocket, nothing', 15, C.GRN)
f.txt(62, 264, 'for a blade to engage. The cone seats on its own taper,', 15, C.GRN)
f.txt(62, 286, 'so the gap is only a bond line: 0.08 mm perpendicular,', 15, C.GRN)
f.txt(62, 308, '0.085 mm as the ring you see round the Ø1.6 aperture.', 15, C.GRN)
f.dim_h(A((OUT,0))[0], A((IN_LO,0))[0], 856, C.FG, f'wall {WALL_LO:.1f} mm')
px0, px1, _, pz1 = pocket('inside')
f.dim_h(A((px0,0))[0], A((px1,0))[0], 800, C.BLU, f'pocket {led_pocket_depth:.1f}')
XL = A((5.15, 0))[0]
for lbl, z, col, x_at in [('ledge top / PCB  11.5', PCB_Z, C.DIM, IN_HI),
                          ('pocket top  11.0', pz1, C.BLU, px0),
                          ('cone base  Ø2.69', ((WZ0 - led_pocket_down) + WZ1) / 2, C.MUT, IN_LO),
                          ('pocket floor  7.4', WZ0 - led_pocket_down, C.BLU, px0)]:
    y = A((0, z))[1]
    f.leader((A((x_at, z))[0] + 4, y), (XL - 6, y), col)
    f.txt(XL, y + 5, lbl, 13, col)

# ---- panel B: the alternative the code still carries ----
f.panel(760, 150, 700, 790, 'B — the alternative: led_fit_from = "outside"',
        'same modules, the pocket cut into the other face')
B = Fig.frame(scale=SC, ox=942, oy=1189)
draw(B, 'outside')
f.txt(782, 242, 'better against the load that actually happens:', 15, C.AMB)
f.txt(782, 264, 'pressure from outside seats the flange on the', 15, C.AMB)
f.txt(782, 286, 'pocket floor instead of pushing the part in —', 15, C.AMB)
f.txt(782, 308, 'but it puts a visible seam on the outer face.', 15, C.AMB)
f.txt(782, 856, 'Inside: only the bond resists a push from outside.', 15, C.RED)
f.txt(782, 878, 'Outside: only the bond resists a pull. Either way', 15, C.RED)
f.txt(782, 900, 'the bond is not optional — see the QC note.', 15, C.RED)

f.footer('READ from the led_* parameters in case/case_polykybd_split72_lr.scad — the pocket and the insert come',
         'from the same modules, so they cannot drift. 0.12 mm per face on the flange in its pocket, 0.08 mm on the',
         'cone, 0.25 mm for the buried cylinder behind it. The inside pocket stops 0.5 mm below the ledge',
         'top so the PCB keeps its full 1.25 mm of support. ONE part, three per half: the section is the same at',
         'D1, D5 and D6.')
f.save(f'{REPO}/RoHS/led-insert-section.svg')
f.png()
print('figure written')
