import sys, subprocess
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

# ---- geometry, from the led_* parameters (x measured from the board outline) --
case_wall_thickness, pcb_clearance, pcb_edge_width = 1.5, 0.15, 1.4
case_bottom_thickness, pcb_edge_height = 2, 9.5
led_pocket_depth, led_ledge_keep = 1.0, 0.5
led_insert_gap, led_window_gap, led_boss_lip = 0.12, 0.25, 0.6

OUT = -(case_wall_thickness + pcb_clearance)        # -1.65, outer wall face
IN_LO = (pcb_edge_width - pcb_clearance)            # +1.25, ledge inner face
IN_HI = -pcb_clearance                              # -0.15, wall above the PCB
PCB_Z = case_bottom_thickness + pcb_edge_height     # 11.5, ledge top / PCB
WZ0, WZ1 = pcb_edge_height - 0.1, pcb_edge_height - 0.1 + 2.20   # window 9.4..11.6
PK_X0, PK_Z1 = IN_LO - led_pocket_depth, PCB_Z - led_ledge_keep  # 0.25, 11.0
LIP_X = OUT + led_boss_lip
g, gw = led_insert_gap, led_window_gap

FL_TOP = PK_Z1 - g            # 10.88  flange
BO_TOP = WZ1 - gw             # 11.35  boss body
LP_TOP = WZ1 - g              # 11.48  boss lip
STEP = BO_TOP - FL_TOP        # 0.47
for k, v in [('flange top', FL_TOP), ('boss body top', BO_TOP), ('boss lip top', LP_TOP),
             ('step', STEP), ('window left open if shaved', WZ1 - FL_TOP)]:
    print(f'  {k:28s} {v:.3f}')

f = Fig(1500, 1000)
f.title('The top of the insert: what the 0.47 mm step is',
        'Section through D5, looking along the wall. Everything above the flange is the only thing',
        'closing the top of the window — the pocket cannot follow it up without eating the PCB ledge.')

def draw(A, shaved):
    # wall, with the ledge stepping back above the PCB
    f.poly([A((OUT, 9.0)), A((IN_LO, 9.0)), A((IN_LO, PCB_Z)), A((IN_HI, PCB_Z)),
            A((IN_HI, 12.6)), A((OUT, 12.6))], C.BOX, C.DIM, sw=2)
    # the PCB sitting on the ledge
    f.poly([A((IN_HI, PCB_Z)), A((2.6, PCB_Z)), A((2.6, PCB_Z + 0.9)), A((IN_HI, PCB_Z + 0.9))],
           C.MUT, C.DIM, sw=1.5)
    # cavity: window through the wall, pocket in the ledge
    f.poly([A((OUT, WZ0)), A((IN_LO, WZ0)), A((IN_LO, WZ1)), A((OUT, WZ1))],
           C.BG, C.MUT, sw=1.5, dash='4 3')
    f.poly([A((PK_X0, 9.0)), A((IN_LO, 9.0)), A((IN_LO, PK_Z1)), A((PK_X0, PK_Z1))],
           C.BG, C.BLU, sw=2, dash='5 3')
    top = FL_TOP if shaved else None
    # boss: lip at g, body at gw, optionally cut flat at the flange top
    bt = min(BO_TOP, top) if top else BO_TOP
    lt = min(LP_TOP, top) if top else LP_TOP
    f.poly([A((OUT, WZ0 + g)), A((LIP_X, WZ0 + g)), A((LIP_X, WZ0 + gw)), A((IN_LO, WZ0 + gw)),
            A((IN_LO, bt)), A((LIP_X, bt)), A((LIP_X, lt)), A((OUT, lt))],
           C.GRN, C.GRN, sw=2, op=.45)
    # flange
    f.poly([A((PK_X0 + g, 9.0)), A((IN_LO, 9.0)), A((IN_LO, FL_TOP)), A((PK_X0 + g, FL_TOP))],
           C.GRN, C.GRN, sw=2, op=.45)
    if shaved:
        f.poly([A((OUT, FL_TOP)), A((IN_LO, FL_TOP)), A((IN_LO, WZ1)), A((OUT, WZ1))],
               C.RED, C.RED, sw=2, op=.35)

SC = 117
# ---- panel A ----
f.panel(40, 160, 690, 700, 'A — as built',
        'green = insert, blue dashed = pocket, grey dashed = the window')
A = Fig.frame(scale=SC, ox=280, oy=1874)
draw(A, False)
XL = A((1.45, 0))[0] + 24
# A 0.02 mm gap is 2 px, so the labels have to be fanned apart and leadered
# rather than placed at their own height.
prev = -1e9
for lbl, z, col, x_at in [('ledge top / PCB  11.50', PCB_Z, C.DIM, IN_HI),
                          ('boss lip   11.48', LP_TOP, C.GRN, LIP_X),
                          ('boss body  11.35', BO_TOP, C.GRN, IN_LO),
                          ('pocket top  11.00', PK_Z1, C.BLU, PK_X0),
                          ('flange top  10.88', FL_TOP, C.GRN, PK_X0 + g)]:
    y = A((0, z))[1]
    ly = max(y, prev + 26); prev = ly
    f.leader((A((x_at, z))[0] + 4, y), (XL - 6, ly), col)
    f.txt(XL, ly + 5, lbl, 13, col)
f.txt(62, 250, f'the step is {STEP:.2f} mm, and it is inside the wall —', 15, C.GRN)
f.txt(62, 272, 'nobody ever sees it. The pocket stops 0.5 mm below', 15, C.GRN)
f.txt(62, 294, 'the ledge top so the board keeps its 1.25 mm of support.', 15, C.GRN)

# ---- panel B ----
f.panel(760, 160, 700, 700, 'B — shaved flat to the flange',
        'what the 0.47 mm costs if it comes off')
B = Fig.frame(scale=SC, ox=1000, oy=1874)
draw(B, True)
f.txt(782, 250, f'{WZ1 - FL_TOP:.2f} × 2.8 mm of the window is left open,', 15, C.RED)
f.txt(782, 272, 'straight through 2.9 mm of wall to the LED behind —', 15, C.RED)
f.txt(782, 294, 'which is the opening the insert exists to close.', 15, C.RED)
f.txt(782, 326, 'The other way round — raising the FLANGE to meet the', 15, C.AMB)
f.txt(782, 348, 'boss — needs the pocket at 11.47, leaving 0.25 mm of', 15, C.AMB)
f.txt(782, 370, 'ledge under the board: a standing rib well under the', 15, C.AMB)
f.txt(782, 392, '0.8 mm the print service allows.', 15, C.AMB)

f.footer('Flange 0.88 mm thick in a 1.0 mm pocket; ledge 1.25 mm wide, so flange + remaining ledge cannot both',
         'clear 0.8 mm — that is what fixes the pocket top at 11.0 and leaves the step. Derived from the led_*',
         'parameters in case/case_polykybd_split72_lr.scad; regenerate with RoHS/led-insert-top.py.')
f.save(f'{REPO}/RoHS/led-insert-top.svg'); f.png()
print('figure written')
