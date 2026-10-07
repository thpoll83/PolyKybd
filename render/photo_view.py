"""The keyboard from the viewpoint of images/PolyKybdSplit72p.jpg, on the white studio.

    blender -b render/out/hero.blend --python render/photo_view.py -- out.png [samples] [width] [gap] [turn] [elevation] [lens] [fill]

The reference photo looks at both halves from in front, about 40 deg above the
desk, with a normal lens; the halves sit a thumb's width apart, each turned so
its inner end comes forward (the left ~2 deg, the right ~9 deg),
the bridge cable hangs in a loop IN FRONT of them from its two 90 deg plugs,
and the host cable leaves the left half's back edge. This sets that up on a
saved scene (blender_scene.py's .blend) with the white cove instead of the
photo's purple desk, then renders at the photo's 1300 x 550 aspect.

`gap` is the distance between the halves' inner edges in m (blender_scene.py
uses 0.05), `turn` each half's turn in deg as "left,right" (negative: the inner
end forward), `elevation` the camera's angle
above the desk in deg, `lens` its focal length in mm, `fill` the share of the
frame's width the keyboard takes. Saves out.blend too.
"""
import math
import os
import sys

import bpy
import mathutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_cable  # noqa: E402
import lighting  # noqa: E402
import materials  # noqa: E402
import screens  # noqa: E402
import studio  # noqa: E402
import textured_parts  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
samples = int(argv[1]) if len(argv) > 1 else 128
width = int(argv[2]) if len(argv) > 2 else 2600
gap = float(argv[3]) if len(argv) > 3 else 0.035
# each half's turn, "left,right" in deg: negative brings its inner end forward.
# Measured on the photo's top edges (image slope = tan(turn) x sin(elevation)):
# the left half is turned ~2 deg, the right ~9 deg, both inner end forward.
turn = [float(v) for v in (argv[4] if len(argv) > 4 else "-2,-9").split(",")]
turn_left, turn_right = turn[0], turn[-1]
elevation = float(argv[5]) if len(argv) > 5 else 42.0
lens = float(argv[6]) if len(argv) > 6 else 35.0
fill = float(argv[7]) if len(argv) > 7 else 0.97
ASPECT = 550 / 1300                     # the reference photo
SCENE_GAP = 0.05                        # blender_scene.py's gap between the halves

sc = bpy.context.scene
materials.tag(bpy)
boards = {}
for side in ("left", "right"):
    root = bpy.data.objects[f"split72_{side}.wrl"]
    boards[side] = os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{side}.kicad_pcb")
    textured_parts.add(root, textured_parts.board_keys(boards[side]))
print("material roles", materials.apply(bpy))
# the displays on, as in the photo: layer 0's legends and both status panels
for side in ("left", "right"):
    root = bpy.data.objects[f"split72_{side}.wrl"]
    print(f"{side}: {screens.keys(root, boards[side], side)} legends lit, "
          f"status panel {screens.status(root, side)} mm")
materials.scene_settings(sc)
tgt = bpy.data.objects.get("target")
lighting.studio(sc, tgt, 1.0)

# the halves: turned, and moved apart to `gap`
studio.splay(turn_left, right=turn_right)
for o in bpy.data.objects:
    if o.name.startswith("piv") and o.type == "EMPTY":
        o.location.x = math.copysign(abs(o.location.x) + (gap - SCENE_GAP) / 2, o.location.x)
bpy.context.view_layer.update()

# camera: straight in front, `elevation` above the desk, framed on both halves
cam = sc.camera
cam.data.lens = lens
cam.data.dof.use_dof = False
studio.camera_elevation(sc, elevation)
lo = mathutils.Vector((1e9,) * 3)
hi = -lo
for o in sc.objects:
    if o.type == "MESH" and (o.name.startswith("split72") or o.parent and "split72" in o.parent.name):
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            lo = mathutils.Vector(map(min, lo, w))
            hi = mathutils.Vector(map(max, hi, w))
centre = (lo + hi) / 2
tgt.location = (centre.x, centre.y - 0.02, (lo.z + hi.z) / 2)
# distance: the keyboard's width filling `fill` of the frame, like the photo
fov = 2 * math.atan(36 / 2 / lens)                  # sensor width 36 mm (Blender default fit)
span = (hi.x - lo.x) / fill
dist = span / 2 / math.tan(fov / 2)
a = math.radians(elevation)
cam.location = tgt.location + mathutils.Vector((0, -dist * math.cos(a), dist * math.sin(a)))
cam.data.sensor_fit = "HORIZONTAL"

studio.cove(sc)
studio.flag(sc)                         # the caps' mirror direction, after the camera move
studio.white_look(sc)

# cables as in the photo: the bridge loop in front, the host cable back and a little to the left
bridge_cable.remove()
halves = [(bpy.data.objects[f"split72_{s}.wrl"], boards[s]) for s in ("left", "right")]
cable = bridge_cable.add(sc, halves, depth=0.036, lean=0.004, toward=-1.0, spread=0.012, clear=0.022)
best, inside, n = bridge_cable.clearance(cable)
print(f"bridge cable: closest to a case {best * 1000:.1f} mm, {inside} of {n} rings inside one")
bridge_cable.add_host(sc, bpy.data.objects["split72_left.wrl"], boards["left"],
                      end_y=0.62, drift=-0.24, turn=38.0)

sc.cycles.filter_width = 1.0
sc.cycles.samples = samples
sc.render.resolution_x, sc.render.resolution_y = width, int(round(width * ASPECT))
sc.render.resolution_percentage = 100
sc.render.filepath = out
# PK_BORDER="x0,y0,x1,y1" (fractions of the frame, y from the top) renders
# just that region at full resolution, for a quick look at a material
border = os.environ.get("PK_BORDER")
if border:
    x0, y0, x1, y1 = (float(v) for v in border.split(","))
    sc.render.use_border, sc.render.use_crop_to_border = True, True
    sc.render.border_min_x, sc.render.border_max_x = x0, x1
    sc.render.border_min_y, sc.render.border_max_y = 1 - y1, 1 - y0
else:
    bpy.ops.wm.save_as_mainfile(filepath=out.rsplit(".", 1)[0] + ".blend", compress=True)
bpy.ops.render.render(write_still=True)
