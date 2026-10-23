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
    'one insert spans both, flush in its pocket')
put(30,  660, 'C_t.png', 'C — D1 on the adjacent wall',
    'its own part, round the corner from the pair')
put(790, 660, 'D_t.png', 'D — cut through D5',
    'flange in its pocket, boss in the window with 0.25 mm all round')

f.footer('Window 2.8 × 2.2 mm through a 2.9 mm wall. Pocket 1.0 mm deep, 3.5 mm flange overlap, 1.9 mm of wall',
         'left under it. Clearance 0.10 mm at the flange (the visible seam) and 0.25 mm per face around the boss,',
         'which is what lets the part go in; the bond closes the seam. All four of a keyboard’s inserts print as',
         'one chained piece (export/case/led_inserts.stl) and snap apart at assembly.')
f.save(f'{REPO}/RoHS/led-insert-views.svg'); f.png()
print('ok')
