"""One key column of the left half seen from the side, for the docs' keycap
stem profile pictures (Keycap stems page).

    blender -b render/out/hero.blend --python render/profile_view.py -- \
        <out.png> <samples> <width> <profile|flat>

`profile` is one of profile.py's PROFILES (stepped, stepped-uniform, curved);
`flat` keeps the board's own R3 stems. The camera is orthographic and level,
so the plate is the horizontal reference each cap's angle reads against. The
front row is on the left.

Every mesh that reaches above the plate is cut down to the column's slab
(SLAB mm either side of its centre), so the other columns do not hide it; the
plate and the case stay whole, and the parts below the plate are left as they
are because the case wall in front hides them.

PK_COL picks the column among the five-key ones, 0 = outermost (default 2,
x -29 mm on the board). The stems are drawn in PK_STEM_RGB="r,g,b" (default an
orange) so the part the profile changes stands out from the grey switch and the
clear cap.
"""
import math
import os
import sys

import bmesh
import bpy
import mathutils
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lighting, materials, profile, studio, textured_parts, bridge_cable  # noqa: E402,E401

a = sys.argv[sys.argv.index("--") + 1:]
out, samples, width, prof = os.path.abspath(a[0]), int(a[1]), int(a[2]), a[3]
SLAB = 9.6                      # mm: a cap is 18 wide, the column pitch 19.05

sc = bpy.context.scene
materials.tag(bpy)
root = bpy.data.objects["split72_left.wrl"]
board = os.path.join(textured_parts.REPO, "poly_kybd", "poly_kybd_split72_left.kicad_pcb")
keys = textured_parts.board_keys(board)
textured_parts.add(root, keys)
materials.apply(bpy)
stem_rgb = tuple(float(v) for v in os.environ.get("PK_STEM_RGB", "0.80,0.25,0.03").split(","))
for mat in bpy.data.materials:
    if mat.get("pk_role") == "stem" and mat.use_nodes:
        b = mat.node_tree.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (*stem_rgb, 1)
if prof != "flat":
    profile.apply(root, board, prof)
materials.scene_settings(sc)
studio.splay(0, right=0)
other = bpy.data.objects["split72_right.wrl"]
for o in [other] + list(other.children_recursive):
    o.hide_render = True
bridge_cable.remove()
bpy.context.view_layer.update()

# the column, in the root's frame (mm)
(tx, ty), dz = textured_parts.fit(root, keys)
flat_keys = sorted((x + tx, y + ty) for x, y, r in keys if abs(r) < 1)
cols, last = [], None
for x, y in flat_keys:
    if last is None or x - last > 7:
        cols.append([])
    cols[-1].append((x, y))
    last = x
five = [c for c in cols if len(c) == 5]
col = five[int(os.environ.get("PK_COL", 2))]
cx = float(np.mean([x for x, y in col]))
y0, y1 = min(y for x, y in col), max(y for x, y in col)

inv = root.matrix_world.inverted()
plate = next(o for o in root.children_recursive
             if o.active_material and o.active_material.get("pk_role") == "plate aluminium")
plate_top = max((inv @ plate.matrix_world @ mathutils.Vector(c)).z for c in plate.bound_box)
KEEP = {"plate aluminium", "case PLA"}
cut = hidden = 0
for o in list(root.children_recursive):
    if o.type != "MESH" or o.hide_render:
        continue
    role = o.active_material.get("pk_role") if o.active_material else None
    if role in KEEP:
        continue
    m = inv @ o.matrix_world
    bb = [m @ mathutils.Vector(c) for c in o.bound_box]
    lo, hi = min(v.x for v in bb), max(v.x for v in bb)
    if max(v.z for v in bb) < plate_top - 0.5:
        continue                                    # below the plate: the case wall hides it
    if hi < cx - SLAB or lo > cx + SLAB:
        o.hide_render = True
        hidden += 1
        continue
    if lo >= cx - SLAB and hi <= cx + SLAB:
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    mn = np.array(m)
    gone = [f for f in bm.faces
            if abs((mn[0, :3] @ np.array(f.calc_center_median()) + mn[0, 3]) - cx) > SLAB]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(o.data)
    bm.free()
    cut += 1
print("column x", round(cx, 1), "cut", cut, "hidden", hidden)

tgt = bpy.data.objects.get("target")
lighting.studio(sc, tgt)
studio.cove(sc)
studio.white_look(sc)

# level orthographic camera on the +x side, looking at the column
mw = root.matrix_world
centre = mw @ mathutils.Vector((cx, (y0 + y1) / 2, plate_top + float(os.environ.get("PK_LIFT", 9.0))))
cam = sc.camera
cam.data.type = "ORTHO"
cam.data.ortho_scale = (y1 - y0 + 34.0) / 1000
cam.data.dof.use_dof = False
cam.data.clip_start = 0.001
cam.location = centre + mathutils.Vector((0.3, 0, 0))
cam.rotation_euler = mathutils.Vector((-1, 0, 0)).to_track_quat("-Z", "Y").to_euler()
for c in list(cam.constraints):
    cam.constraints.remove(c)

# a white backdrop behind the column, so the side view is not on the dark world
bd = bpy.data.meshes.new("backdrop")
bd.from_pydata([(0, -1, -1), (0, 1, -1), (0, 1, 1), (0, -1, 1)], [], [(0, 1, 2, 3)])
bo = bpy.data.objects.new("backdrop", bd)
sc.collection.objects.link(bo)
bo.location = mw @ mathutils.Vector((cx - 140.0, (y0 + y1) / 2, plate_top))
bm_ = bpy.data.materials.new("backdrop")
bm_.use_nodes = True
nt = bm_.node_tree
nt.nodes.remove(nt.nodes["Principled BSDF"])
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (1, 1, 1, 1)
em.inputs["Strength"].default_value = float(os.environ.get("PK_BACKDROP", 1.0))
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs[0])
bd.materials.append(bm_)

# the row's stem name above each key, in front of everything
case = next(o for o in root.children_recursive
            if o.active_material and o.active_material.get("pk_role") == "case PLA")
case_x = max((case.matrix_world @ mathutils.Vector(c)).x for c in case.bound_box)
names = profile.PROFILES[prof] if prof != "flat" else ("R3",) * 5
lab = bpy.data.materials.new("label")
lab.use_nodes = True
lab.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.06, 0.06, 0.06, 1)
for (x, y), name in zip(sorted(col, key=lambda k: k[1]), names):
    td = bpy.data.curves.new(f"label {name}", "FONT")
    td.body, td.size, td.align_x, td.align_y = name, 0.0042, "CENTER", "BOTTOM"
    t = bpy.data.objects.new(f"label {name}", td)
    sc.collection.objects.link(t)
    w = mw @ mathutils.Vector((cx, y, plate_top + 17.5))
    t.location = (case_x + 0.001, w.y, w.z)
    t.rotation_euler = (math.radians(90), 0, math.radians(90))
    td.materials.append(lab)

sc.cycles.samples = samples
sc.render.resolution_x, sc.render.resolution_y = width, int(round(width * 430 / 1300))
sc.render.resolution_percentage = 100
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
