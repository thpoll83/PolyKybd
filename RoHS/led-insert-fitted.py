import sys, subprocess
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C
S = '<renders>'

f = Fig(1520, 1010)
f.title('Status-LED windows, from outside the case',
        'D5 and D6 on the left wall of the right half. Same camera in both panels;',
        'the insert is tinted green — the render itself carries no colour.')

IW, IH = 712, 570
f.panel(30, 160, 722, 700, 'A — as the case is cut',
        'the pocket is an open recess, the two windows go straight through')
f.image(f'{S}/v0.png', 35, 235, IW, IH, clip=(30, 160, 722, 700))

f.panel(768, 160, 722, 700, 'B — with the insert bonded in',
        'flange flush in the pocket, bosses filling the windows')
f.image(f'{S}/v1_tint.png', 773, 235, IW, IH, clip=(768, 160, 722, 700))

f.footer('Window 1.8 × 2.2 mm through a 2.9 mm wall; pocket 1.0 mm deep with a 3.5 mm flange overlap, leaving',
         '1.9 mm of wall. 6.4 mm of air path through the seam before the bond closes it. Geometry from the led_*',
         'parameters in case/case_polykybd_split72_lr.scad — the pocket and the insert share the same modules.')
f.save(f'{REPO}/RoHS/led-insert-fitted.svg'); f.png()
print('ok')
