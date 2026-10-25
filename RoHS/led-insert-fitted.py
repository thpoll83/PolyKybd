import sys, subprocess
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C
import os

# Two 900x720 OpenSCAD renders of the same camera ('-32,93.9,16,-0.45,93.9,10.5'):
# v0 = the case alone, v1 = case + inserts, with v1_tint the second one tinted
# where it differs from the first. Build artefacts, not committed - point
# RENDERS at wherever they were made.
S = os.environ.get('RENDERS', '/tmp/led-renders')

f = Fig(1520, 1010)
f.title('Status-LED windows, from outside the case',
        'D5 and D6 on the left wall of the right half. Same camera in both panels;',
        'the inserts are tinted green — the render itself carries no colour.')

IW, IH = 712, 570
f.panel(30, 160, 722, 700, 'A — as the case is cut',
        'two open slots, straight through 2.9 mm of wall to the LEDs behind')
f.image(f'{S}/v0.png', 35, 235, IW, IH, clip=(30, 160, 722, 700))

f.panel(768, 160, 722, 700, 'B — with the insert bonded in',
        'the bosses fill them flush; the flange is behind the wall, out of sight')
f.image(f'{S}/v1_tint.png', 773, 235, IW, IH, clip=(768, 160, 722, 700))

f.footer('Window 2.8 × 2.2 mm through a 2.9 mm wall. Fitted from the inside, so the outer surface keeps the',
         'geometry that was tested and the only line on it is the boss itself, at 0.12 mm per face. 5.3 mm of air',
         'path through the seam before the bond closes it. Geometry from the led_* parameters in',
         'case/case_polykybd_split72_lr.scad — the pocket and the insert share the same modules.')
f.save(f'{REPO}/RoHS/led-insert-fitted.svg'); f.png()
print('ok')
