import sys, subprocess, os
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

# Six 900x690 OpenSCAD renders. Build artefacts, not committed - point RENDERS at
# wherever they were made. Each part is translated to the origin first; the frame
# panels are tinted where the full frame differs from one built without
# _inserts(), since OpenSCAD drops colour() under --render=cgal. Cameras:
#   pA insert -16,-12, 9,0,0,1.45     pB insert  16, 12, 9,0,0,1.45
#   pC chain  -14,-26,16,8.5,0,1.45   pD score   -3.2,-4.4,2.6,3.9,0,1.45
#   pE frame  top, CENTRE=1.3,8.6,0 DIST=520
#   pF corner -34,-48,30,-50,-26,0
S = os.environ.get('RENDERS', '/tmp/led-renders')

f = Fig(1540, 1230)
f.title('The ESD insert, and how six of them get printed',
        'ONE part, three per half. The boss fills the window flush with the case’s outer face; the flange',
        'behind it sits in a pocket cut into the PCB ledge. 7.4 × 4.0 × 2.9 mm, 31.3 mm³ of clear resin.')

PW, PH = 486, 470
IW, IH = 450, 345
def put(col, row, img, label, note=''):
    px, py = 30 + col * 496, 160 + row * 490
    f.panel(px, py, PW, PH, label, note)
    f.image(f'{S}/{img}', px + 18, py + 78, IW, IH, clip=(px, py, PW, PH))

put(0, 0, 'pA.png', 'A — the part, from outside',
    'the boss, 2.0 mm proud of the flange')
put(1, 0, 'pB.png', 'B — the part, from inside',
    'the flange face that beds into the ledge pocket')
put(2, 0, 'pC.png', 'C — three of them, chained',
    'one half’s worth, on V-scored tabs')
put(0, 1, 'pD.png', 'D — the V-score',
    'the section pinches to 0.6 mm, so it breaks there')
put(1, 1, 'pE.png', 'E — where they ride',
    'the right frame; the inserts are tinted green')
put(2, 1, 'pF.png', 'F — the anchor, close up',
    'off the outer rail’s bottom end')

f.footer('From frame r1.2 each diffuser frame carries its half’s three inserts: same clear resin, same print, and',
         'the frame’s bounding box does not change. The row sits flange-down with its flange face level with the',
         'web’s underside, which puts every V-score in the web plane. Snap them off before fitting the frame.',
         'export/case/led_inserts.stl is the standalone fallback — all six in a row, 52.2 × 4.0 × 2.9 mm.')
f.save(f'{REPO}/RoHS/led-insert-parts.svg'); f.png()
print('ok')
