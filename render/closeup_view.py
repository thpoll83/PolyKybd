"""A close-up of a block of the left half's keys, lit from a legend atlas.

    blender -b render/out/hero.blend --python render/closeup_view.py -- \
        out.png samples width atlas fx fy dist elev yaw lens [fstop]

`atlas` names textures/<atlas>.png/.json (export_screens.py, overlay_atlas.py);
fx, fy place the camera target as fractions of the left half's display decals'
bounding box (x from the left, y from the front); dist is in metres, elev and
yaw in degrees, lens in mm, fstop > 0 turns on depth of field. PK_STRENGTH sets
the legends' emission (6 saturates to white at close range; 3 keeps the
LIT_TINT visible), PK_STATUS the status-panel suffix (_l1), PK_BORDER a crop.
The docs' overlays close-up: screens_gimp_l1 0.47 0.58 0.145 50 0 55, strength 3.
"""
import bpy, sys, os, math, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import materials, lighting, screens, studio, textured_parts, bridge_cable
a = sys.argv[sys.argv.index("--") + 1:]
out, samples, width, atlas = os.path.abspath(a[0]), int(a[1]), int(a[2]), a[3]
fx, fy, dist, elev, yaw, lens = map(float, a[4:10])
aperture = float(a[10]) if len(a) > 10 else 0.0


sc = bpy.context.scene
materials.tag(bpy)
root = bpy.data.objects["split72_left.wrl"]
board = os.path.join(textured_parts.REPO, "poly_kybd", "poly_kybd_split72_left.kicad_pcb")
textured_parts.add(root, textured_parts.board_keys(board))
materials.apply(bpy)
print("lit", screens.keys(root, board, "left", strength=float(os.environ.get("PK_STRENGTH", 6.0)), atlas_name=atlas), screens.status(root, "left", suffix=os.environ.get("PK_STATUS", "")))
materials.scene_settings(sc)
tgt = bpy.data.objects.get("target")
lighting.studio(sc, tgt, 1.0)
studio.splay(-2, right=-9)
right = bpy.data.objects["split72_right.wrl"]
for o in [right] + list(right.children_recursive):
    o.hide_render = True
bridge_cable.remove()
bpy.context.view_layer.update()
dec = next(o for o in root.children_recursive if o.name.endswith("display decals"))
ws = [dec.matrix_world @ v.co for v in dec.data.vertices]
lo = mathutils.Vector([min(w[i] for w in ws) for i in range(3)])
hi = mathutils.Vector([max(w[i] for w in ws) for i in range(3)])
print("decals bbox", lo, hi)
tgt.location = (lo.x + fx * (hi.x - lo.x), lo.y + fy * (hi.y - lo.y), hi.z)
cam = sc.camera
cam.data.lens = lens
cam.data.clip_start = 0.005          # the default 0.1 m cuts the front keys at this distance
e, y = math.radians(elev), math.radians(yaw)
cam.location = tgt.location + mathutils.Vector((dist * math.cos(e) * math.sin(y), -dist * math.cos(e) * math.cos(y), dist * math.sin(e)))
cam.data.dof.use_dof = aperture > 0
if aperture > 0:
    cam.data.dof.focus_object = tgt
    cam.data.dof.aperture_fstop = aperture
studio.cove(sc)
studio.flag(sc)
studio.white_look(sc)
sc.cycles.filter_width = 1.0
sc.cycles.samples = samples
sc.render.resolution_x, sc.render.resolution_y = width, int(round(width * 9 / 16))
sc.render.resolution_percentage = 100
sc.render.filepath = out
border = os.environ.get("PK_BORDER")
if border:
    x0, y0, x1, y1 = (float(v) for v in border.split(","))
    sc.render.use_border, sc.render.use_crop_to_border = True, True
    sc.render.border_min_x, sc.render.border_max_x = x0, x1
    sc.render.border_min_y, sc.render.border_max_y = 1 - y1, 1 - y0
bpy.ops.render.render(write_still=True)
