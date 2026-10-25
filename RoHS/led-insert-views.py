import sys, subprocess
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C
import os

# The four 820x640 OpenSCAD renders. They are build artefacts, not committed, so
# point RENDERS at wherever they were made. To remake them: export the case and
# the inserts over the LED corner to reg_case.stl / reg_ins.stl, then for each
# view render the case ALONE and case+insert with the same camera and tint the
# pixels that differ (that marks where the insert is actually visible - OpenSCAD
# drops colour() under --render=cgal). D is a section: intersect with
# translate([-20,60,-5]) cube([60,29.89,30]) to cut at y = 89.89, through D5, and
# use camera '16,100,17,1,89.5,10'.
S = os.environ.get('RENDERS', '/tmp/led-renders')

f = Fig(1540, 1270)
f.title('Status-LED inserts in place — four views',
        'Right half, the corner where the two LED walls meet. The insert is tinted green;',
        'OpenSCAD drops colour in a CGAL render, so the tint marks where it is actually visible.')

PW, PH = 740, 470
IW, IH = 704, 374
def put(px, py, img, label, note):
    f.panel(px, py, PW, PH, label, note)
    f.image(f'{S}/{img}', px + 18, py + 78, IW, IH, clip=(px, py, PW, PH))

put(30,  160, 'A_t.png', 'A — the corner, from outside',
    'D1 on the near wall, D5+D6 round to the right')
put(790, 160, 'B_t.png', 'B — D5 and D6',
    'two of the three; each is the same part, 8.0 mm apart')
put(30,  660, 'C_t.png', 'C — D1 on the adjacent wall',
    'the third — identical, 33.2 mm round a 93.4° corner')
put(790, 660, 'D_t.png', 'D — cut through D5',
    'flange in the ledge pocket, boss filling the window')

f.footer('ONE part, three per half. Fitted from the INSIDE: the flange sits in a pocket cut into the PCB ledge and the',
         'outer surface keeps the geometry that was tested. Window 2.8 × 2.2 mm through a 2.9 mm wall; pocket 1.0 mm',
         'deep, 3.5 mm cavity overlap and 2.4 mm on the flange, stopping 0.5 mm below the ledge top so the board keeps',
         'its support. 0.12 mm per face where the seam shows, 0.25 mm buried. Three ride on each diffuser frame.')
f.save(f'{REPO}/RoHS/led-insert-views.svg'); f.png()
print('ok')
