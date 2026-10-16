"""A test for the assembly video: one key's display flex plugged into its socket on the
back of the board, before doing it for all 36.

    blender -b render/out/assembly_pcb.blend --python render/assembly_video.py \
        --python render/assembly_fpc_test.py -- out_dir width samples stills ,

assembly_video.py builds the scene and, given "stills ," renders nothing; this then
freezes it at FREEZE s (every display landed, no keycap yet), turns the board over and
animates KEY's flex tail: it sticks straight out of the slot, then bends over into its
loop until its end sits in its FH34 socket. The bend interpolates the strip's own
curvature along its length (theta_t(s) = theta(0) + t * (theta(s) - theta(0))), so
every in-between shape is the same strip bent less: no stretching, the root in the
slot never moves. 11 shape keys sample t, and the frames blend between neighbours.
Renders FRAMES frames as out_dir/fpc_NNNN.png.
"""
import math
import os
import sys

import bpy
import mathutils
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpc_bend  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, WIDTH, SAMPLES = argv[0], int(argv[1]), int(argv[2])
KEY = os.environ.get("PK_FPC_KEY", "SW_K_10")
FPS, FREEZE, FRAMES = 25, 35.9, 100
BEND = (15, 75)                                   # frames: straight until the first, plugged at the second
sc = bpy.context.scene
root = bpy.data.objects["split72_left.wrl"]

# freeze: every animated value stays as evaluated at FREEZE, then the keys go
sc.frame_set(int(round(FREEZE * FPS)) + 1)
for o in bpy.data.objects:
    if o.animation_data:
        loc, rot, hid = o.location.copy(), o.rotation_euler.copy(), o.hide_render
        o.animation_data_clear()
        o.location, o.rotation_euler, o.hide_render = loc, rot, hid
for o in root.children_recursive:
    if o.get("pk_kind") == "keycap":
        o.hide_render = True
root.rotation_euler.y += math.pi                  # the back side up, about the short axis as at the start
bpy.context.view_layer.update()

tail = bpy.data.objects[f"{KEY}:flex tail"]
tail.shape_key_clear()                             # assembly_video.py's own keys; the mesh stays the model
keys, end, length, turn, yaw = fpc_bend.bend_keys(tail)
print(f"fpc test: {KEY} tail {length:.1f} mm, turns {turn:.0f} deg, strip at {yaw:.0f} deg")
fpc_bend.drive(keys, BEND[0], BEND[1])
co = np.array([v.co[:] for v in tail.data.vertices]) + np.array(tail.location)

# the camera: three-quarter view over the key's socket, from the front and the side
cam, tgt = sc.camera, bpy.data.objects["target"]
for o in (cam, tgt):
    o.animation_data_clear()
centre = root.matrix_world @ mathutils.Vector((float(co[:, 0].mean()), 31.0, -2.0))
tgt.location = centre
cam.location = centre + mathutils.Vector((-0.055, -0.07, 0.06))
cam.data.clip_start = 0.002
cam.data.lens = 50

sc.render.resolution_x, sc.render.resolution_y = WIDTH, int(round(WIDTH * 9 / 16 / 2)) * 2
sc.cycles.samples = SAMPLES
os.makedirs(OUT, exist_ok=True)
only = os.environ.get("PK_FPC_FRAMES")            # "1,45,75": just those, for a look
for fr in [int(x) for x in only.split(",")] if only else range(1, FRAMES + 1):
    sc.frame_set(fr)
    sc.render.filepath = os.path.join(OUT, f"fpc_{fr:04d}.png")
    if not os.path.exists(sc.render.filepath):
        bpy.ops.render.render(write_still=True)
print("FPC TEST DONE")
