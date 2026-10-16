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

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, WIDTH, SAMPLES = argv[0], int(argv[1]), int(argv[2])
KEY = os.environ.get("PK_FPC_KEY", "SW_K_10")
FPS, FREEZE, FRAMES = 25, 35.9, 100
BEND = (15, 75)                                   # frames: straight until the first, plugged at the second
STEPS = 11
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
me = tail.data
co = np.array([v.co[:] for v in me.vertices]) + np.array(tail.location)   # root frame, mm
yz = co[:, 1:]

# the strip's centre line in y-z (its width runs along x): walk from the slot end
# (its highest point) in 0.3 mm steps, each step the mean of the points just ahead
p = yz[yz[:, 1].argmax()].copy()
d = np.array([0.0, -1.0])
line = [p.copy()]
for _ in range(400):
    rel = yz - p
    ahead = rel @ d
    near = np.linalg.norm(rel, axis=1)
    sel = (ahead > 0.15) & (ahead < 0.6) & (near < 0.8)
    if not sel.any():
        break
    q = yz[sel].mean(0)
    d = (q - p) / np.linalg.norm(q - p)
    p = p + d * 0.3
    line.append(p.copy())
line = np.array(line)
k = np.ones(5) / 5                                # smooth the walk, keep its ends
sm = np.c_[np.convolve(np.pad(line[:, 0], 2, mode="edge"), k, "valid"),
           np.convolve(np.pad(line[:, 1], 2, mode="edge"), k, "valid")]
seg = np.diff(sm, axis=0)
s = np.concatenate([[0], np.cumsum(np.linalg.norm(seg, axis=1))])
theta = np.unwrap(np.arctan2(seg[:, 1], seg[:, 0]))
theta = np.append(theta, theta[-1])
print(f"fpc test: {KEY} tail {s[-1]:.1f} mm along {len(sm)} points, turns {math.degrees(theta[-1] - theta[0]):.0f} deg")

# each vertex as (s, along, across) on the line
dist = ((yz[:, None, :] - sm[None]) ** 2).sum(-1)
idx = dist.argmin(1)
T = np.c_[np.cos(theta), np.sin(theta)]
N = np.c_[-T[:, 1], T[:, 0]]
rel = yz - sm[idx]
along = (rel * T[idx]).sum(1)
across = (rel * N[idx]).sum(1)


def shape(t):
    th = theta[0] + t * (theta - theta[0])
    ds = np.diff(s)
    c = np.vstack([sm[0], sm[0] + np.cumsum(np.c_[np.cos(th[:-1]), np.sin(th[:-1])] * ds[:, None], axis=0)])
    tt = np.c_[np.cos(th), np.sin(th)]
    nn = np.c_[-tt[:, 1], tt[:, 0]]
    out = co.copy()
    out[:, 1:] = c[idx] + along[:, None] * tt[idx] + across[:, None] * nn[idx]
    return out - np.array(tail.location)


end_err = np.linalg.norm(shape(1.0)[:, 1:] - (co - np.array(tail.location))[:, 1:], axis=1).max()
print(f"fpc test: the t=1 shape reproduces the model within {end_err:.3f} mm")
tail.shape_key_add(name="Basis")
keys = []
for i in range(STEPS):
    kb = tail.shape_key_add(name=f"t{i}")
    kb.data.foreach_set("co", shape(i / (STEPS - 1)).ravel())
    kb.slider_min = 0.0
    keys.append(kb)


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


for fr in range(1, FRAMES + 1):
    t = smooth((fr - BEND[0]) / (BEND[1] - BEND[0])) * (STEPS - 1)
    lo = min(int(t), STEPS - 2)
    w = t - lo
    for i, kb in enumerate(keys):
        kb.value = (1 - w) if i == lo else w if i == lo + 1 else 0.0
        kb.keyframe_insert("value", frame=fr)

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
