import sys, subprocess, os
REPO = subprocess.run(['git','rev-parse','--show-toplevel'], cwd='/home/user/PolyKybd',
                      capture_output=True, text=True, check=True).stdout.strip()
sys.path.insert(0, f'{REPO}/.claude/skills/explain-geometry-figure')
from figlib import Fig, C

# Six 900x690 OpenSCAD renders of the parts on their own, each translated to the
# origin first (the modules build them in case coordinates). Build artefacts, not
# committed - point RENDERS at wherever they were made. Cameras, eye->centre:
#   pA pair   -30,-22,-10,0,0,0     pB pair    19,-34, 11,0,0,0
#   pC single -15, 21, -7,0,0,0     pD single  -8,-18,  7,0,0,0
#   pE plate  top, CENTRE=13.05,0,-0.05 DIST=90
#   pF plate  -26,-48,38,13.05,0,0
# The two parts sit on walls with DIFFERENT normals - the pair's outer face is
# -x, the single's is +y - so "from outside" is not the same camera for both.
S = os.environ.get('RENDERS', '/tmp/led-renders')

f = Fig(1540, 1230)
f.title('The ESD inserts on their own',
        'Two parts per half, four per keyboard, printed in clear resin. The boss fills the window flush with',
        'the case’s outer face; the flange behind it sits in a pocket cut into the PCB ledge.')

PW, PH = 486, 470
IW, IH = 450, 345
def put(col, row, img, label, note=''):
    px, py = 30 + col * 496, 160 + row * 490
    f.panel(px, py, PW, PH, label, note)
    f.image(f'{S}/{img}', px + 18, py + 78, IW, IH, clip=(px, py, PW, PH))

put(0, 0, 'pA.png', 'A — pair, from outside',
    'the two bosses, 2.0 mm proud of the flange')
put(1, 0, 'pB.png', 'B — pair, from inside',
    'the flange face that beds into the ledge pocket')
put(2, 0, 'pE.png', 'E — print plate, from above',
    'a whole keyboard’s set on a 0.9 mm breakaway spine')
put(0, 1, 'pC.png', 'C — single (D1), from outside',
    'one boss; D1 is round the corner on the next wall')
put(1, 1, 'pD.png', 'D — single (D1), from inside',
    'same arrangement, 9.6 mm long instead of 17.6')
put(2, 1, 'pF.png', 'F — print plate, 3/4',
    'laid flange-down; the parts snap apart at assembly')

f.footer('Pair (D5+D6)  17.60 × 2.90 × 4.00 mm, 72.9 mm³   ·   single (D1)  9.60 × 3.27 × 4.00 mm, 39.0 mm³',
         'Plate  29.50 × 17.64 × 3.27 mm, 236.2 mm³ of resin — the four parts plus 12.5 mm³ of spine and tabs.',
         'The spine meets each part on the flange edge, so the witness mark is never on a face that shows. Each',
         'part is one shell, verified to sit inside the cavity the case loses: export/case/led_inserts.stl.')
f.save(f'{REPO}/RoHS/led-insert-parts.svg'); f.png()
print('ok')
