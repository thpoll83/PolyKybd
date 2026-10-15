"""The assembly scene's board and soldered parts from pcb2blender, as on the PCB shot.

    PCB2BLENDER=<checkout> blender-5.1 -b --python render/assembly_pcb.py -- \
        render/out/assembly.blend render/out/pcb_left.blend render/out/left.pcb3d render/out/assembly_pcb.blend

assembly_scene.py's board ("PCB:pcb") and its components and hot-swap sockets come
from the VRML, which flattens the board's layers into flat colour. This replaces them
with pcb_shot's board: pcb2blender's import of the same half (pcb_shot/import.py),
given pcb_shot/look.py's look (the Rev.2 colours, the purple mask, the flex slots,
the hot-swap solder). The board is parented to the half's root in its frame, and
each component carries pk_ref (its KiCad reference, from <pcb3d>.parts.json),
pk_kind, pk_side and pk_unit (0.001: it moves in metres, the root's parts in mm).
The solder joints stay on the board: paste on the pads before the parts come.
Needs Blender 5.1 (pcb2blender's importer), with the add-on registered before the
scenes open, or its materials render white.
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:]
scene, pcb_blend, pcb3d, out = argv
sys.path.insert(0, os.environ.get("PCB2BLENDER", "/tmp/pcb2blender"))
sys.path.insert(0, os.path.join(HERE, "pcb_shot"))
import pcb2blender_importer  # noqa: E402

pcb2blender_importer.register()
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(scene))
import look  # noqa: E402

root = bpy.data.objects["split72_left.wrl"]
CX, CY = 120.408, 93.556          # assembly_parts.fit() on the left half: root mm = (x - CX, -(y - CY))
with bpy.data.libraries.load(os.path.abspath(pcb_blend), link=False) as (src, dst):
    dst.objects = list(src.objects)
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()                     # world matrices of the appended objects, for the slot fit
pcb = next(o for o in dst.objects if o.name.startswith("PCB_") and o.parent is None)
board, ox, oy = look.prepare(pcb, os.path.abspath(pcb3d))
print("board", board.name, "pad offset", round(ox, 6), round(oy, 6))

# the board's local metres -> the root's mm: x = (lx - ox) * 1000 - CX, y = (ly - oy) * 1000 + CY
old = {o["pk_ref"]: o for o in root.children if o.get("pk_kind") in ("comp", "socket")}
check = {r: o.matrix_world.translation.copy() for r, o in old.items()}
pcb.parent = root
pcb.matrix_parent_inverse.identity()
pcb.rotation_euler = (0, 0, 0)
pcb.scale = (1000.0,) * 3
pcb.location = (-ox * 1000 - CX, -oy * 1000 + CY, 0.0)
pcb["pk_kind"], pcb["pk_ref"], pcb["pk_side"], pcb["pk_lib"] = "pcb", "PCB", 1, "PCB"
pcb["pk_x"], pcb["pk_y"] = 0.0, 0.0
bpy.context.view_layer.update()

parts = json.load(open(os.path.splitext(os.path.abspath(pcb3d))[0] + ".parts.json"))
refs = list(parts)
P = np.array([parts[r]["position"] for r in refs])                     # KiCad mm
back = np.array([parts[r]["back"] for r in refs])
named, worst = 0, 0.0
for o in pcb.children:
    if o.type != "MESH" or o.name.startswith(("SOLDER_", "mark ")):
        continue
    lx, ly, lz = o.location
    x, y = (lx - ox) * 1000, -(ly - oy) * 1000
    d = np.hypot(P[:, 0] - x, P[:, 1] - y)
    j = int(d.argmin())
    worst = max(worst, float(d[j]))
    ref, p = refs[j], parts[refs[j]]
    kind = "socket" if p["footprint"].startswith("Kailh_socket") else "comp"
    o["pk_ref"], o["pk_kind"], o["pk_lib"] = ref, kind, p["footprint"]
    o["pk_side"] = 1 if lz > 0 else -1
    o["pk_x"], o["pk_y"] = x - CX, -(y - CY)
    o["pk_unit"] = 0.001
    named += 1
print("named", named, "parts; worst distance to its footprint %.2f mm" % worst)

# the same parts in both scenes should sit within a part's size of each other
errs = []
for o in pcb.children:
    r = o.get("pk_ref")
    if r in check and o.get("pk_kind") == "comp":
        errs.append((o.matrix_world.translation - check[r]).xy.length * 1000)
if errs:
    print("against the VRML parts: median %.2f mm, 90%% %.2f mm (n=%d)" % (np.median(errs), np.percentile(errs, 90), len(errs)))
bpy.data.batch_remove([o for o in root.children if o.get("pk_kind") in ("pcb", "comp", "socket") and o is not pcb])
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out), compress=True)
print("SAVED", out)
