"""The assembly video: the left half built part by part on the white studio floor,
then the camera pulls back to both halves and the USB cables plug in.

    blender -b render/out/assembly.blend --python render/assembly_video.py -- \
        out_dir width samples [first last | stills f1,f2,...]

assembly.blend comes from assembly_scene.py: the left half as one object per part,
each with pk_kind and pk_side. This keyframes everything and renders frames as
PNG into out_dir (frame_0001.png ...); ffmpeg makes the video. The plan, in
seconds at 25 fps (STAGES below):

  0.0  the bare PCB comes down, bottom side up (already on its way at frame 1)
  2.5  the bottom side, in waves left to right: passives, then the chips and
       connectors, then the 36 hot-swap sockets
 12.5  the board turns over
 14.5  the top side: the key LEDs and the rest of the parts
 18.0  the plate with its diffuser, the status display, the screws
 21.5  the switches, row by row; the keycap stems; the displays with their
       flex cables; the keycaps
 34.0  the case comes up from below, the lids drop in, the board settles
 39.0  the camera pulls back to both halves, the right half sliding in beside the
       left one; the bridge cable drops into place,
       the host cable plugs in; hold until 47 s

Every part comes from its own side of the board (pk_side), from 40 to 110 mm
away, a little off to the side and turned, and eases onto its place in 0.5 to
1.1 s. Before its start it is hidden.
"""
import math
import os
import sys

import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_cable  # noqa: E402
import lighting  # noqa: E402
import materials  # noqa: E402
import studio  # noqa: E402
import textured_parts  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, WIDTH, SAMPLES = argv[0], int(argv[1]), int(argv[2])
FPS = 25
END = 47.0
sc = bpy.context.scene
root = bpy.data.objects["split72_left.wrl"]
right = bpy.data.objects["split72_right.wrl"]
parts = [o for o in root.children if o.get("pk_kind")]
rng = np.random.default_rng(7)


def f(sec):
    return int(round(sec * FPS)) + 1


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def lib(o):
    return o.get("pk_lib", "").split(":")[-1]


# ---- which part when ----------------------------------------------------------
def wave(objs, t0, t1, key=lambda o: o["pk_x"], jitter=0.25):
    """Start times spread over [t0, t1] by `key` (default: left to right), each
    nudged by up to `jitter` s so a row does not land as one."""
    if not objs:
        return {}
    k = np.array([key(o) for o in objs], float)
    u = (k - k.min()) / max(k.max() - k.min(), 1e-9)
    return {o: t0 + (t1 - t0) * ui + rng.uniform(0, jitter) for o, ui in zip(objs, u)}


PASSIVE = ("C_", "R_", "D_SOD", "CP_EIA", "L_0805", "LED_0805")
kind = lambda o: o["pk_kind"]
below = [o for o in parts if kind(o) == "comp" and o["pk_side"] < 0]
above = [o for o in parts if kind(o) == "comp" and o["pk_side"] > 0]
row = lambda o: -o["pk_y"] * 10 + o["pk_x"] * 0.01        # top row first, then left to right
start = {}
start.update(wave([o for o in parts if kind(o) == "pcb"], -0.6, -0.6, jitter=0))   # coming in at frame 1
start.update(wave([o for o in below if lib(o).startswith(PASSIVE)], 2.5, 7.0))
start.update(wave([o for o in below if not lib(o).startswith(PASSIVE)], 7.3, 9.5))
start.update(wave([o for o in parts if kind(o) == "socket"], 9.6, 11.6, key=row))
start.update(wave(above, 14.5, 17.2))
start.update(wave([o for o in parts if kind(o) == "plate"], 18.0, 18.0, jitter=0))
start.update(wave([o for o in parts if kind(o) == "diffuser"], 18.9, 18.9, jitter=0))
start.update(wave([o for o in parts if kind(o) == "status"], 19.6, 19.6, jitter=0))
start.update(wave([o for o in parts if kind(o) == "screw"], 20.2, 20.9, jitter=0.1))
start.update(wave([o for o in parts if kind(o) == "switch"], 21.5, 25.0, key=row))
start.update(wave([o for o in parts if kind(o) == "kstem"], 25.4, 26.8, key=row))
disp = wave([o for o in parts if kind(o) == "display"], 27.2, 29.6, key=row)
start.update(disp)
by_ref = {o["pk_ref"]: t for o, t in disp.items()}
for o in parts:                                    # a display's decal and flex come with it
    if kind(o) in ("display_decal", "flex"):
        start[o] = by_ref.get(o["pk_ref"], 28.0) + (0.0 if kind(o) == "display_decal" else -0.15)
start.update(wave([o for o in parts if kind(o) == "keycap"], 30.0, 33.4, key=row))
start.update(wave([o for o in parts if kind(o) == "case"], 34.0, 34.0, jitter=0))
start.update(wave([o for o in parts if kind(o) == "lid"], 35.4, 35.9, jitter=0.1))
missing = [o.name for o in parts if o not in start]
if missing:
    print("WARNING no start time for", len(missing), missing[:8])

FLIP = (12.5, 14.3)               # the board turns over (it starts bottom side up)
LIFT = 40.0                       # mm the board floats until the case is under it
SETTLE = (36.4, 37.8)             # the board, now in its case, comes down onto the desk


# ---- the fly-in ----------------------------------------------------------------
def fly(o, t):
    """o from its side of the board onto its place, starting at t s."""
    big = kind(o) in ("pcb", "plate", "case")
    dist = 70.0 if big else rng.uniform(40, 110)
    dur = 1.4 if big else rng.uniform(0.5, 1.1)
    side = o["pk_side"] if kind(o) != "pcb" else 1
    home = o.location.copy()
    off = mathutils.Vector((rng.uniform(-20, 20), rng.uniform(-20, 20), side * dist)) if not big \
        else mathutils.Vector((0, 0, side * dist))
    turn = mathutils.Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), rng.uniform(-0.8, 0.8))) \
        if not big else mathutils.Vector((0, 0, 0))
    if f(t) > 1:                                   # one already on its way at frame 1 stays visible
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=1)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f(t))
    n = max(2, int(dur * FPS))
    for i in range(n + 1):
        u = i / n
        e = 1 - (1 - u) ** 3                       # fast in, slow onto the surface
        o.location = home + off * (1 - e)
        o.rotation_euler = (turn * (1 - e)).to_tuple()
        o.keyframe_insert("location", frame=f(t) + i)
        o.keyframe_insert("rotation_euler", frame=f(t) + i)
    for fc in o.animation_data.action.fcurves:
        if fc.data_path == "hide_render":
            for k in fc.keyframe_points:
                k.interpolation = "CONSTANT"
    o.location = home


for o, t in start.items():
    fly(o, t)

# the right half, built already, waits 0.45 m off to the side (out of every close
# view) and slides in beside the left one while the camera pulls back
RIGHT_IN = (38.8, 41.4)
piv_r = right.parent
home_r = piv_r.location.copy()
for sec, away in ((0, 1), (RIGHT_IN[0], 1), (RIGHT_IN[1], 0)):
    piv_r.location = home_r + mathutils.Vector((0.45 * away, 0, 0))
    piv_r.keyframe_insert("location", frame=f(sec))
for k in piv_r.animation_data.action.fcurves[0].keyframe_points:
    k.interpolation = "BEZIER"
piv_r.location = home_r

# the board: bottom side up and lifted, turned over, then down into its case
base_loc, base_rot = root.location.copy(), root.rotation_euler.copy()
lift = mathutils.Vector((0, 0, LIFT / 1000))       # root is in the pivot's frame (metres)
for sec, flip, lifted in ((0, 1, 1), (FLIP[0], 1, 1), (FLIP[1], 0, 1), (SETTLE[0], 0, 1), (SETTLE[1], 0, 0)):
    root.rotation_euler = (base_rot.x + math.pi * flip, base_rot.y, base_rot.z)
    root.location = base_loc + lift * lifted
    root.keyframe_insert("rotation_euler", frame=f(sec))
    root.keyframe_insert("location", frame=f(sec))
for fc in root.animation_data.action.fcurves:
    for k in fc.keyframe_points:
        k.interpolation = "BEZIER"
        k.easing = "AUTO"

# ---- studio, cables, camera -----------------------------------------------------
materials.scene_settings(sc)
tgt = bpy.data.objects.get("target")
lighting.studio(sc, tgt)
studio.cove(sc)
studio.white_look(sc)
bridge_cable.remove()
sc.frame_set(f(END))                               # the cables fit the halves where they end up
halves = [(r, os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{s}.kicad_pcb"))
          for r, s in ((root, "left"), (right, "right"))]
before = set(bpy.data.objects)
bridge_cable.add(sc, halves, depth=0.036, lean=0.004, toward=-1.0, spread=0.012, clear=0.022)
bridge = [o for o in bpy.data.objects if o not in before]
before = set(bpy.data.objects)
bridge_cable.add_host(sc, root, halves[0][1], end_y=0.62, drift=-0.24, turn=38.0)
host = [o for o in bpy.data.objects if o not in before]
CABLE_IN, HOST_IN = 41.5, 43.2
DROP = mathutils.Vector((0, 0, 0.06))              # the bridge cable drops 60 mm into place
PULL = root.matrix_world.to_3x3() @ mathutils.Vector((0, 15, 0))   # the host plug, 15 mm out of its port
for objs, t, world in ((bridge, CABLE_IN, DROP), (host, HOST_IN, PULL)):
    for o in objs:
        home = o.location.copy()
        d = o.parent.matrix_world.to_3x3().inverted() @ world if o.parent else world
        o.hide_render = True
        o.keyframe_insert("hide_render", frame=1)
        o.hide_render = False
        o.keyframe_insert("hide_render", frame=f(t))
        for u, e in ((0, 1.0), (0.7, 0.12), (1.0, 0.0)):
            o.location = home + d * e
            o.keyframe_insert("location", frame=f(t + u))
        o.location = home
        for fc in o.animation_data.action.fcurves:
            if fc.data_path == "hide_render":
                for k in fc.keyframe_points:
                    k.interpolation = "CONSTANT"

cam = sc.camera
cam.data.dof.use_dof = False
cam.data.lens = 50
bpy.context.view_layer.update()


def box(objs):
    lo = mathutils.Vector((1e9,) * 3)
    hi = -lo
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            lo = mathutils.Vector(map(min, lo, w))
            hi = mathutils.Vector(map(max, hi, w))
    return lo, hi


sc.frame_set(f(END))                               # everything in place, on the desk
lo, hi = box(parts)
left_c = (lo + hi) / 2
llo, lhi = lo, hi
rlo, rhi = box([o for o in right.children_recursive if o.type == "MESH"])
both_c = (mathutils.Vector(map(min, llo, rlo)) + mathutils.Vector(map(max, lhi, rhi))) / 2
both_w = max(lhi.x, rhi.x) - min(llo.x, rlo.x)
fov = 2 * math.atan(36 / 2 / cam.data.lens)


def view(centre, width, elev, azim, fill):
    """Camera position for `centre` with `width` m filling `fill` of the frame."""
    d = width / fill / 2 / math.tan(fov / 2)
    a, b = math.radians(elev), math.radians(azim)
    return centre + mathutils.Vector((d * math.cos(a) * math.sin(b), -d * math.cos(a) * math.cos(b), d * math.sin(a)))


lw = lhi.x - llo.x
lift_c = left_c + mathutils.Vector((0, 0, LIFT / 1000))
# (s, target, width, elevation, azimuth, fill)
SHOTS = [(0.0, lift_c, lw, 48, -18, 0.80), (2.5, lift_c, lw * 0.55, 52, -10, 0.85),
         (7.0, lift_c + mathutils.Vector((0.03, 0, 0)), lw * 0.55, 50, 4, 0.85), (11.8, lift_c, lw, 46, 10, 0.85),
         (14.5, lift_c, lw * 0.75, 50, 14, 0.85), (18.0, lift_c, lw, 40, 6, 0.80),
         (21.5, lift_c, lw, 36, -6, 0.82), (30.0, lift_c, lw, 32, -12, 0.82),
         (34.0, lift_c, lw, 30, -16, 0.78), (37.8, left_c, lw, 30, -12, 0.80),
         (39.0, left_c, lw, 30, -8, 0.82), (41.2, both_c, both_w, 33, 0, 0.95), (END, both_c, both_w, 33, 3, 0.95)]
for s, c, w, el, az, fill in SHOTS:
    tgt.location = c
    cam.location = view(c, w, el, az, fill)
    tgt.keyframe_insert("location", frame=f(s))
    cam.keyframe_insert("location", frame=f(s))
for o in (tgt, cam):
    for fc in o.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
            k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
studio.flag(sc)                                    # the caps' mirror card, for the closing view

sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, f(END)
sc.cycles.samples = SAMPLES
sc.render.resolution_x, sc.render.resolution_y = WIDTH, int(round(WIDTH * 9 / 16 / 2)) * 2
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
os.makedirs(OUT, exist_ok=True)
if len(argv) > 3 and argv[3] == "stills":
    frames = [int(x) for x in argv[4].split(",")]
elif len(argv) > 4:
    frames = list(range(int(argv[3]), int(argv[4]) + 1))
else:
    frames = list(range(sc.frame_start, sc.frame_end + 1))
print("ASSEMBLY", len(parts), "parts,", len(start), "timed,", sc.frame_end, "frames; rendering", len(frames))
for fr in frames:
    sc.frame_set(fr)
    sc.render.filepath = os.path.join(OUT, f"frame_{fr:04d}.png")
    if not os.path.exists(sc.render.filepath):
        bpy.ops.render.render(write_still=True)
print("DONE")
