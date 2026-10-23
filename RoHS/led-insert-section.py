import sys, subprocess
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

# ---- geometry, straight from the case parameters ---------------------------
case_wall_thickness, pcb_clearance, pcb_edge_width = 1.5, 0.15, 1.4
case_bottom_thickness, pcb_edge_height = 2, 9.5
led_pocket_depth, led_pocket_overlap, led_pocket_down, led_insert_gap = 1.0, 3.5, 2.0, 0.10

OUT   = -(case_wall_thickness + pcb_clearance)      # outer wall face
IN_LO =  (pcb_edge_width - pcb_clearance)           # inner face below the PCB
IN_HI = -pcb_clearance                              # inner face above the PCB
WALL_LO, WALL_HI = IN_LO - OUT, IN_HI - OUT
PCB_Z = case_bottom_thickness + pcb_edge_height     # PCB underside
WZ0, WZ1 = pcb_edge_height - 0.1, pcb_edge_height - 0.1 + 2.20
PK_X1 = OUT + led_pocket_depth
PK_Z0, PK_Z1 = WZ0 - led_pocket_down, PCB_Z
REMAIN = WALL_LO - led_pocket_depth
PATH = led_pocket_depth + led_pocket_overlap + REMAIN
LED_X = 4.553 - 1.1985                              # D5, inboard of the outline edge

for k, v in [('outer face', OUT), ('inner face below PCB', IN_LO), ('wall below PCB', WALL_LO),
             ('wall above PCB', WALL_HI), ('PCB underside z', PCB_Z), ('window z', (WZ0, WZ1)),
             ('pocket x1', PK_X1), ('pocket z', (PK_Z0, PK_Z1)), ('wall left under pocket', REMAIN),
             ('air path', PATH), ('D5 inboard of edge', LED_X)]:
    print(f'  {k:24s} {v}')

f = Fig(1500, 1000)
f.title('Status-LED window: the ESD insert and the pocket that makes room for it',
        'Section through D5. EMC-700 left ±8 kV air discharge NOT RATED at these openings;',
        'the bonded insert means the opening does not exist on a shipped unit.')

def draw(A, with_path):
    # wall body, below and above the PCB underside
    f.poly([A((OUT,6.6)),A((IN_LO,6.6)),A((IN_LO,PCB_Z)),A((IN_HI,PCB_Z)),
            A((IN_HI,13.2)),A((OUT,13.2))], C.BOX, C.DIM, sw=2)
    # the window through it
    f.poly([A((OUT,WZ0)),A((IN_LO,WZ0)),A((IN_LO,WZ1)),A((OUT,WZ1))], C.BG, C.MUT, sw=1.5, dash='4 3')
    # the pocket (wall thinned here)
    f.poly([A((OUT,PK_Z0)),A((PK_X1,PK_Z0)),A((PK_X1,PK_Z1)),A((OUT,PK_Z1))],
           C.BG, C.BLU, sw=2, dash='5 3')
    # the insert: flange in the pocket + boss through the window
    g = led_insert_gap
    f.poly([A((OUT,PK_Z0+g)),A((PK_X1-g,PK_Z0+g)),A((PK_X1-g,WZ0+g)),A((IN_LO,WZ0+g)),
            A((IN_LO,WZ1-g)),A((PK_X1-g,WZ1-g)),A((PK_X1-g,PK_Z1-g)),A((OUT,PK_Z1-g))],
           C.GRN, C.GRN, sw=2, op=.45)
    # PCB + the LED behind the window
    f.poly([A((IN_HI,PCB_Z)),A((5.0,PCB_Z)),A((5.0,PCB_Z+1.1)),A((IN_HI,PCB_Z+1.1))],
           C.MUT, C.DIM, sw=1.5)
    f.poly([A((LED_X-1.0,PCB_Z-0.9)),A((LED_X+1.0,PCB_Z-0.9)),A((LED_X+1.0,PCB_Z)),
            A((LED_X-1.0,PCB_Z))], C.AMB, C.AMB, sw=1.5, op=.8)
    if with_path:
        p = [A((OUT,PK_Z1-g)),A((PK_X1-g,PK_Z1-g)),A((PK_X1-g,WZ1-g)),A((IN_LO,WZ1-g))]
        for a,b in zip(p,p[1:]):
            f.line(a,b,C.RED,sw=4)
        f.dot(p[0],C.RED,5); f.dot(p[-1],C.RED,5)

# ---- panel A: dimensions ----
f.panel(40, 150, 690, 760, 'A — as built, with the insert bonded in',
        'green = insert, blue dashed = pocket, grey dashed = the original window')
SC=62
A = Fig.frame(scale=SC, ox=222, oy=1189)
draw(A, False)
f.dim_h(A((OUT,0))[0], A((IN_LO,0))[0], 856, C.FG, f'wall {WALL_LO:.1f} mm')
f.dim_h(A((OUT,0))[0], A((PK_X1,0))[0], 800, C.BLU, f'pocket {led_pocket_depth:.1f}')
# z callouts, leadered from the wall's inner face out to a clear column
XL = A((5.15, 0))[0]
for lbl, z, col, x_at in [('PCB underside 11.5', PCB_Z, C.DIM, IN_HI),
                          ('window bottom  9.4', WZ0, C.MUT, IN_LO),
                          ('pocket floor  7.4', PK_Z0, C.BLU, PK_X1)]:
    y = A((0, z))[1]
    f.leader((A((x_at, z))[0] + 4, y), (XL - 6, y), col)
    f.txt(XL, y + 5, lbl, 13, col)

# ---- panel B: the air path ----
f.panel(760, 150, 700, 760, 'B — the air path an 8 kV discharge must take',
        'and why the seam is bonded rather than merely fitted')
B = Fig.frame(scale=SC, ox=942, oy=1189)
draw(B, True)
f.txt(975, 806, f'pocket depth      {led_pocket_depth:.1f} mm', 17, C.RED)
f.txt(975, 830, f'+ flange overlap  {led_pocket_overlap:.1f} mm', 17, C.RED)
f.txt(975, 854, f'+ wall under it   {REMAIN:.1f} mm', 17, C.RED)
f.line((971,866),(1215,866), C.RED, 2)
f.txt(975, 892, f'= {PATH:.1f} mm of narrow gap', 19, C.RED, bold=True)
f.txt(975, 916, 'and the bond closes it entirely', 15, C.DIM)

f.footer('Derived from the led_* parameters in case/case_polykybd_split72_lr.scad — the pocket and the',
         'insert come from the same modules, so they cannot drift. Two parts per half: one spans D5+D6,',
         'one covers D1. Four per keyboard, printed in clear resin.')
f.save('<repo>/RoHS/led-insert-section.svg')
f.png()
print('figure written')
