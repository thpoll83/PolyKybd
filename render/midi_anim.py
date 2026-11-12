"""The MIDI video with a moving camera: every frame rendered in Cycles.

    PK_EMIT=... (the Eden video's look, as for eden_view.py) \\
    blender -b render/out/hero.blend --python render/midi_anim.py -- <frame dir> <samples> <width> [fps]

midi_video.py builds its frames in 2D from layers rendered once, which needs a camera
that does not move. Here the camera flies, so each frame is a render of its own:

- the scene is eden_view.py's, built in its "preview" pass (the LEDs, the glow in the
  caps and the case, the indicator LEDs) with PK_NO_SHOT, plus the dim room light that
  midi_video.py adds at PK_AMBIENT (default 0.07) of the ambient pass;
- the performance is midi_video.py's (the same notes, presses, pedal and OCT 3): each
  key is pushed down by its travel at that moment (eden_view.press), and the screens'
  atlas texture is rewritten per frame, a held key's cell inverted;
- the rainbow moves as on the board (QMK's CYCLE_LEFT_RIGHT at Eden's speed), at
  PK_RAINBOW (default 0.5) of its level;
- the camera follows SHOTS: an orbit, a low flight over the keys looking where it goes,
  pans, and at the end a zoom in (the fade to black is added when the video is made).

Frames are written as <frame dir>/00000.png ...; a frame that exists is skipped, so a
stopped run resumes. PK_FRAMES="first,last" renders a part; PK_STEP=n every n-th frame
(a quick preview). Make the video with midi_anim_video.sh.
"""
import colorsys
import json
import math
import os
import runpy
import sys

import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
a = sys.argv[sys.argv.index("--") + 1:]
frame_dir, samples, width = os.path.abspath(a[0]), int(a[1]), int(a[2])
fps = int(a[3]) if len(a) > 3 else 25
env = os.environ.get
os.makedirs(frame_dir, exist_ok=True)

# the scene: eden_view.py's preview pass, without its own render
os.environ["PK_NO_SHOT"] = "1"
os.environ["PK_LEGENDS"] = "screens_layer8,_l8"
sys.argv = [sys.argv[0], "--", os.path.join(frame_dir, "scene.png"), str(samples), str(width), "preview"]
g = runpy.run_path(os.path.join(HERE, "eden_view.py"), run_name="eden_view")
import midi_video as mv  # noqa: E402  (the performance; numpy only at import)
import screens  # noqa: E402

sc = bpy.context.scene
cam, tgt = sc.camera, bpy.data.objects["target"]
press, unpress, halves = g["press"], g["unpress"], g["halves"]
X0, X1, HUE_SPAN = g["X0"], g["X1"], g["HUE_SPAN"]
lo, hi = g["BOARD_BOX"]
centre = (lo + hi) / 2

# the room: no studio light, only the dim ambient light of midi_video.py
for o in [o for o in sc.objects if o.type == "LIGHT"]:
    bpy.data.objects.remove(o)
d = bpy.data.lights.new("ambient", "AREA")
d.shape, d.size = "DISK", 1.2
d.energy = 40.0 * float(env("PK_AMBIENT", 0.07))
d.color = (0.85, 0.9, 1.0)
amb = bpy.data.objects.new("ambient", d)
sc.collection.objects.link(amb)
amb.location = (-0.35, -0.55, 0.9)
amb.rotation_euler = (mathutils.Vector((0, 0, 0)) - amb.location).to_track_quat("-Z", "Y").to_euler()

# the screens (eden_view.py adds them with PK_LEGENDS, before the key profile re-poses
# the displays): the MIDI layer's legends and status panels, lit as in the stills
img = bpy.data.images.get("screens_layer8.png") or next(i for i in bpy.data.images if i.name.startswith("screens_layer8"))
AW, AH = img.size


def atlas(name):
    from PIL import Image as PImage
    px = np.asarray(PImage.open(os.path.join(screens.TEX, name + ".png")).convert("RGB"), np.float32) / 255
    cells = json.load(open(os.path.join(screens.TEX, name + ".json"), encoding="utf-8"))["keys"]
    return px, cells


ATLASES = {name: atlas(name) for _, name in mv.STATES}

# the rainbow: emitter colours and the glow's hue ramp, moved per frame
RAINBOW = float(env("PK_RAINBOW", 0.5))
emitters = [o for o in sc.objects if o.name.startswith("led emitter")]
emit_x = [sum(v.co.x for v in o.data.vertices) / len(o.data.vertices) for o in emitters]
emit_x = [(o.matrix_world @ mathutils.Vector((x, 0, 0))).x for o, x in zip(emitters, emit_x)]
for o in emitters:
    em = o.active_material.node_tree.nodes["Emission"]
    em.inputs["Strength"].default_value *= RAINBOW
ramps = []
for m in bpy.data.materials:
    if m.get("pk_role") in ("keycap glass", "case PLA") and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "MAP_RANGE" and abs(n.inputs["To Max"].default_value - HUE_SPAN) < 1e-6:
                ramps.append(n)
            if n.type == "EMISSION" and any(l.to_socket.name == "Volume" for l in n.outputs[0].links):
                n.inputs["Strength"].default_value *= RAINBOW
HUE_PER_MS = mv.HUE_PER_MS


def set_rainbow(t):
    off = (HUE_PER_MS * t * 1000) % 1.0
    for o, x in zip(emitters, emit_x):
        h = (HUE_SPAN * (x - X0) / (X1 - X0) - off) % 1.0
        o.active_material.node_tree.nodes["Emission"].inputs["Color"].default_value = (*colorsys.hsv_to_rgb(h, 1, 1), 1)
    for n in ramps:
        n.inputs["To Min"].default_value = -off
        n.inputs["To Max"].default_value = HUE_SPAN - off


def set_screens(t):
    name = [n for at, n in mv.STATES if at <= t][-1]
    px, cells = ATLASES[name]
    px = px.copy()
    for key in mv.held(t):
        if key in cells:
            x, y = cells[key]
            px[y:y + 40, x:x + 72] = 1.0 - px[y:y + 40, x:x + 72]
    rgba = np.ones((AH, AW, 4), np.float32)
    rgba[:, :, :3] = px[::-1][:AH, :AW]                 # Blender's rows run up
    img.pixels.foreach_set(rgba.ravel())
    img.update()


# --- the camera ------------------------------------------------------------------------
W_BOARD = hi.x - lo.x
D_BOARD = hi.y - lo.y
TOP = hi.z


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def orbit(u, az0, az1, elev, dist, lens):
    az = math.radians(az0 + (az1 - az0) * ease(u))
    e = math.radians(elev)
    aim = mathutils.Vector((centre.x, centre.y, TOP))
    pos = aim + mathutils.Vector((dist * math.cos(e) * math.sin(az), -dist * math.cos(e) * math.cos(az), dist * math.sin(e)))
    return pos, aim, lens


def flyover(u, x0, x1, height, ahead, lens):
    """Low over the keys, looking where it goes (along -x when x1 < x0), a little down."""
    x = x0 + (x1 - x0) * ease(u)
    y = centre.y - 0.25 * D_BOARD
    pos = mathutils.Vector((x, y, TOP + height))
    dirn = math.copysign(1.0, x1 - x0)
    aim = mathutils.Vector((x + dirn * ahead, centre.y + 0.1 * D_BOARD, TOP - 0.01))
    return pos, aim, lens


def pan(u, x0, x1, elev, dist, lens, y_off=0.0):
    x = x0 + (x1 - x0) * ease(u)
    e = math.radians(elev)
    aim = mathutils.Vector((x, centre.y + y_off, TOP))
    pos = aim + mathutils.Vector((0, -dist * math.cos(e), dist * math.sin(e)))
    return pos, aim, lens


L, R = lo.x + 0.22 * W_BOARD, hi.x - 0.22 * W_BOARD     # the two halves' middles
END = mv.TOTAL
# (start s, function of u in 0..1): each shot runs to the next one's start (5..8 s)
SHOTS = [
    (0.0, lambda u: orbit(u, -55, 35, 38, 0.62, 40)),                  # around the centre, left to right
    (7.0, lambda u: flyover(u, hi.x + 0.03, lo.x - 0.03, 0.045, 0.12, 22)),   # low, right to left
    (13.5, lambda u: pan(u, L, centre.x, 62, 0.30, 45)),               # over the left half towards the middle
    (20.0, lambda u: pan(u, centre.x - 0.05, R + 0.03, 28, 0.32, 45, 0.02)),  # low along the front, to the right
    (26.5, lambda u: orbit(u, 30, -20, 55, 0.50, 45)),                 # around, back to the left
    (33.0, lambda u: pan(u, R, L, 70, 0.42, 40)),                      # high, right to left
    (39.5, lambda u: orbit(u, -10, 10, 50, 0.70 - 0.35 * ease(u), 40 + 30 * ease(u))),   # wide, then in
]


def camera(t):
    for k, (t0, f) in enumerate(SHOTS):
        t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else END
        if t < t1 or k == len(SHOTS) - 1:
            return f((t - t0) / max(1e-6, t1 - t0))


cam.data.dof.use_dof = False
cam.data.sensor_fit = "HORIZONTAL"
cam.data.clip_start = 0.002
aspect = float(env("PK_ASPECT", 2.35))
sc.render.resolution_x, sc.render.resolution_y = width, int(round(width / aspect / 2)) * 2
sc.render.resolution_percentage = 100
sc.cycles.samples = samples
sc.cycles.use_denoising = True
sc.render.use_persistent_data = True        # keep what did not change between frames
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"

first, last = 0, int(END * fps) - 1
if env("PK_FRAMES"):
    first, last = (int(v) for v in env("PK_FRAMES").split(","))
step = int(env("PK_STEP", 1))
pressed = {}
for n in range(first, last + 1, step):
    path = os.path.join(frame_dir, f"{n:05d}.png")
    if os.path.exists(path):
        continue
    t = n / fps
    pos, aim, lens = camera(t)
    cam.location = pos
    cam.rotation_euler = (aim - pos).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    # move the keys only when their travel changed: an untouched mesh keeps its BVH
    # (persistent data), and a rebuild costs seconds a frame
    want = {k: round(3.5 * dpt, 3) for k, dpt in mv.depths(t).items() if dpt > 0}
    if want != pressed:
        unpress()
        for key, mm in want.items():
            press(key, mm)
        pressed = want
    set_screens(t)
    set_rainbow(t)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"midi_anim frame {n} t={t:.2f}", flush=True)
