"""A copy of a split72 board as the fab delivers it, for pcb2blender's exporter.

    python3 render/pcb_shot/board_copy.py poly_kybd/poly_kybd_split72_left.kicad_pcb poly_kybd/_shot_left.kicad_pcb

Drops the 3D models of everything that is assembled later (switches, caps,
stems, displays, flex, plate, case, diffuser, screws), keeps the SMD parts,
the FPC sockets and the Kailh hotswap sockets, and sets the stackup: purple
mask, white silkscreen, ENIG. The real mask colour is set later in shot.py
(see there); "Purple" only selects pcb2blender's mask shader.

The copy must stay in poly_kybd/ beside a .kicad_pro of its own name, or
${KIPRJMOD} does not resolve and every model in poly_kybd/models/ drops
silently (see poly_kybd/models/README.md).
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
DROP = re.compile(r'keycap_|outercap|SW_Cherry|plate_split72|case_polykybd|diffuser_frame|'
                  r'status_display_holder|cover_insert|screw_M3')
s = open(src, encoding='utf-8').read()
out, i, dropped = [], 0, 0
while True:
    j = s.find('(model "', i)
    if j < 0:
        out.append(s[i:])
        break
    depth, k = 0, j
    while True:                                   # the matching close paren of this (model ...)
        c = s[k]
        depth += c == '('
        depth -= c == ')'
        k += 1
        if depth == 0:
            break
    name = s[j:j + 200].split('"')[1]
    if DROP.search(name):
        out.append(s[i:j])
        dropped += 1
    else:
        out.append(s[i:k])
    i = k
s = ''.join(out)
for typ, col in [('Top Solder Mask', 'Purple'), ('Bottom Solder Mask', 'Purple'),
                 ('Top Silk Screen', 'White'), ('Bottom Silk Screen', 'White')]:
    a = f'(type "{typ}")'
    assert s.count(a) == 1, a
    s = s.replace(a, a + f'\n\t\t\t\t(color "{col}")')
assert s.count('(copper_finish "None")') == 1
s = s.replace('(copper_finish "None")', '(copper_finish "ENIG")')
open(dst, 'w', encoding='utf-8').write(s)
print('dropped', dropped, 'assembly models')
