"""The assembly video: the left half built part by part on the white studio floor,
then the camera pulls back to both halves and the USB cables plug in.

    blender -b render/out/assembly.blend --python render/assembly_video.py -- \
        out_dir width samples [first last | stills f1,f2,...]

assembly_pcb.blend comes from assembly_scene.py, then assembly_pcb.py: the left half
as one object per part, each with pk_kind and pk_side, its board and soldered parts
pcb2blender's (render with PCB2BLENDER set, in Blender 5.1). This keyframes everything and renders frames as
PNG into out_dir (frame_0001.png ...); ffmpeg makes the video. The plan, in
seconds at 25 fps (the constants below), in the order of the assembly guide
(polykybd-docs, assembly/step-by-step):

  0.0  the bare PCB comes down, bottom side up (already on its way at frame 1)
  2.5  the bottom side, in waves left to right: passives, then the chips and
       connectors, then the 36 hot-swap sockets
 12.5  the board turns over, about its short axis (its front edge stays in front)
 14.5  the top side: the key LEDs and the rest of the parts
 17.8  the spacer
 19.6  the plate with the status display and its holder, down to 35 mm above the
       board; the diffuser slides in under it from the front and up into it; a
       second later both come down onto the spacer; the cover insert
 26.6  the switches, row by row; the keycap stems; the displays, each with its
       flex cable as one part; the keycaps
 40.0  once the clear keycaps cover the displays, the board turns over; row by row,
       each socket's flap opens, the display's flex tail bends over from straight out
       of its slot into the socket, and the flap closes (fpc_bend.py); the board
       turns back
 52.4  the case slides in on the desk under the floating board, which comes down
       into it; the four screws
 57.6  the camera pulls back to both halves, the right half sliding in beside the
       left one; the bridge cable comes down with its plugs out of the ports and
       they push in; the host cable slides in from far behind; hold until 67.4 s

Every part moves along its own side's axis only (pk_side: from above or from
below the board, 40 to 110 mm away), in 0.5 to 1.1 s, and keeps its orientation.
Before its start it is hidden.
"""
import math
import os
import sys

import bmesh
import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_cable  # noqa: E402
import fpc_bend  # noqa: E402
import lighting  # noqa: E402
import materials  # noqa: E402
import studio  # noqa: E402
import textured_parts  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, WIDTH, SAMPLES = argv[0], int(argv[1]), int(argv[2])
FPS = 25
END = 67.4
if os.environ.get("PCB2BLENDER"):                  # assembly_pcb.py's scene: its board materials need the add-on
    sys.path.insert(0, os.environ["PCB2BLENDER"])
    import pcb2blender_importer
    pcb2blender_importer.register()
    bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
sc = bpy.context.scene
root = bpy.data.objects["split72_left.wrl"]
right = bpy.data.objects["split72_right.wrl"]
parts = [o for o in root.children_recursive if o.get("pk_kind")]   # pcb2blender parts sit under the board
rng = np.random.default_rng(7)


def fcurves(o):
    """o's F-curves: the action's own in Blender 4.1, its slot's channel bag in 5.x."""
    act = o.animation_data.action
    if hasattr(act, "fcurves"):
        return act.fcurves
    from bpy_extras import anim_utils
    return anim_utils.action_get_channelbag_for_slot(act, o.animation_data.action_slot).fcurves


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
of = lambda *ks: [o for o in parts if kind(o) in ks]
below = [o for o in of("comp") if o["pk_side"] < 0]
above = [o for o in of("comp") if o["pk_side"] > 0]
row = lambda o: -o["pk_y"] * 10 + o["pk_x"] * 0.01        # top row first, then left to right

FLIP = (12.5, 14.3)               # the board turns over (it starts bottom side up)
LIFT = 40.0                       # mm the board floats until the case is under it
HOVER = 35.0                      # mm the plate waits above the board for its diffuser
PLATE_IN = (19.6, 21.0)           # plate, status display holder and display come down to HOVER
DIFF_IN = (20.8, 22.1, 22.6, 23.1)   # the diffuser slides in under the plate from the front, up through
                                     # the switch holes, then back into the round LED slots
LED_DY = 8.73                     # mm: each LED sits this far behind its switch's centre
PLATE_DOWN = (24.0, 25.4)         # a second's wait, then plate and diffuser come down together
FLIP_BACK = (40.0, 41.8)          # once the clear keycaps cover the displays, the board turns over again
PLUG = (42.2, 47.6)               # the flex tails plug into their sockets, row by row (starts)
FLAP_T, BEND_T = 0.4, 1.6         # s: a socket's flap opens, its tail bends in, the flap closes
FLAP_OPEN = math.radians(105)     # the FH34's back-flip actuator, fully open
FLIP_UP = (50.4, 52.2)            # and the board turns top side up for the case
CASE_IN = (52.4, 54.0)            # the case slides in on the desk from behind, under the floating board
SETTLE = (54.4, 55.8)             # the board comes down into it
RIGHT_IN = (57.6, 60.2)           # the right half slides in while the camera pulls back
BRIDGE_IN = (60.4, 61.2, 61.4, 62.1)   # the bridge cable drops, then its plugs push into the ports
HOST_IN = (62.6, 65.0)            # the host cable slides in from far behind

start = {}                        # parts that drop straight onto their place (fly)
start.update(wave(of("pcb"), -0.6, -0.6, jitter=0))  # coming in at frame 1
start.update(wave([o for o in below if lib(o).startswith(PASSIVE)], 2.5, 7.0))
start.update(wave([o for o in below if not lib(o).startswith(PASSIVE)], 7.3, 9.5))
start.update(wave(of("socket"), 9.6, 11.6, key=row))
start.update(wave(above, 14.5, 17.2))
start.update(wave(of("spacer"), 17.8, 17.8, jitter=0))
start.update(wave([o for o in of("lid") if o["pk_ref"] == "LID1"], 25.8, 25.8, jitter=0))  # the cover insert
start.update(wave(of("switch"), 26.6, 30.1, key=row))
start.update(wave(of("kstem"), 30.5, 31.9, key=row))
disp = wave(of("display"), 32.3, 34.7, key=row)
start.update(disp)
by_ref = {o["pk_ref"]: t for o, t in disp.items()}
for o in of("display_decal", "flex"):              # one part with its display: same start, same path
    start[o] = by_ref[o["pk_ref"]]
start.update(wave(of("keycap"), 35.1, 38.5, key=row))
start.update(wave(of("screw"), 56.2, 57.0, jitter=0.1))
plate_group = of("plate", "status") + [o for o in of("lid") if o["pk_ref"] == "LID0"]
diffuser = of("diffuser")
case = of("case")
missing = [o.name for o in parts if o not in start and o not in plate_group + diffuser + case]
if missing:
    print("WARNING no start time for", len(missing), missing[:8])


# ---- the motion ------------------------------------------------------------------
def ease_out(u):
    return 1 - (1 - min(max(u, 0.0), 1.0)) ** 3     # fast in, slow onto the surface


def show_from(o, t):
    """o hidden before t s (one already on its way at frame 1 stays visible)."""
    if f(t) <= 1:
        return
    o.hide_render = True
    o.keyframe_insert("hide_render", frame=1)
    o.hide_render = False
    o.keyframe_insert("hide_render", frame=f(t))
    for fc in fcurves(o):
        if fc.data_path == "hide_render":
            for k in fc.keyframe_points:
                k.interpolation = "CONSTANT"


def path(o, keys, world=False):
    """o along keys [(s, offset, ease)]: each offset (mm in the root's frame, or m
    in the world with world=True) reached at s with ease from the key before.
    Location only: a part keeps its own orientation all the way."""
    home = o.location.copy()
    if world:
        to_local = o.parent.matrix_world.to_3x3().inverted() if o.parent else mathutils.Matrix.Identity(3)
    else:
        to_local = mathutils.Matrix.Identity(3) * o.get("pk_unit", 1.0)   # a pcb2blender part moves in metres
    show_from(o, keys[0][0])
    prev = keys[0]
    o.location = home + to_local @ mathutils.Vector(prev[1])
    o.keyframe_insert("location", frame=f(prev[0]))
    for k in keys[1:]:
        a, b = f(prev[0]), f(k[0])
        for fr in range(a + 1, b + 1):
            e = k[2]((fr - a) / max(b - a, 1))
            off = mathutils.Vector(prev[1]).lerp(mathutils.Vector(k[1]), e)
            o.location = home + to_local @ off
            o.keyframe_insert("location", frame=fr)
        prev = k
    o.location = home


def fly(o, t, dist, dur):
    """o straight down (or up) its side's axis onto its place."""
    side = o["pk_side"] if kind(o) != "pcb" else 1
    path(o, [(t, (0, 0, side * dist), None), (t + dur, (0, 0, 0), ease_out)])


ZERO = (0, 0, 0)
moves = {}                        # per group (a part, or a display with its decal and flex): distance, time
for o, t in start.items():
    g = o["pk_ref"] if kind(o) in ("display", "display_decal", "flex") else o.name
    if g not in moves:
        big = kind(o) in ("pcb", "spacer")
        moves[g] = (70.0, 1.4) if big else (rng.uniform(40, 110), rng.uniform(0.5, 1.1))
    fly(o, t, *moves[g])

# a flex cable's tail runs under the board to its socket. It is split off so it can
# bend (fpc_bend.py), but it comes down with its display from the start, straight out
# below the strip (the bend's t=0), so the whole flex threads down through its slot
tails = 0
for o in of("flex"):
    me = o.data
    z = np.array([o.location.z + v.co.z for v in me.vertices])
    under = [p.index for p in me.polygons if max(z[i] for i in p.vertices) < 0.0]
    if not under:
        continue
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    tail = o.copy()
    tail.data = me.copy()
    tail.animation_data_clear()
    tail.name = o.name + " tail"
    sc.collection.objects.link(tail)
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in under], context="FACES")
    bm.to_mesh(me)
    bm.free()
    bt = bmesh.new()
    bt.from_mesh(tail.data)
    bt.faces.ensure_lookup_table()
    drop = set(under)
    bmesh.ops.delete(bt, geom=[q for q in bt.faces if q.index not in drop], context="FACES")
    bt.to_mesh(tail.data)
    bt.free()
    fly(tail, start[o], *moves[o["pk_ref"]])     # with its display, the whole strip at once
    tail["pk_ref"] = o["pk_ref"]
    tails += 1
print("flex tails split off:", tails)

# ---- the flex tails into their sockets, with the board on its back --------------
# Each tail lands straight, out of its slot (fpc_bend.py's t=0). Once the board has
# turned over (FLIP_BACK), row by row: the socket's flap opens, the tail bends over
# into it, the flap closes. The flap is the FH34's actuator (the material
# pcb_shot/look.py gives (0.040, 0.034, 0.033)), cut out of the socket's mesh and
# hinged along local x on its edge away from the key switch (local -y), so it opens
# away from the switch.
ACTUATOR = (0.040, 0.034, 0.033)


def is_actuator(m):
    n = m.node_tree.nodes.get("Mat4cad BSDF") if m and m.node_tree else None
    return n is not None and max(abs(a - b) for a, b in zip(n.inputs["Color"].default_value[:3], ACTUATOR)) < 0.004


sockets = [o for o in bpy.data.objects["PCB_left"].children if o.name.startswith("FH34SRJ")]
cut = {}                                           # mesh -> (socket without the flap, flap mesh, hinge)
for o in sockets:
    me = o.data
    if me.name in cut:
        continue
    flap_i = {i for i, m in enumerate(me.materials) if is_actuator(m)}
    body, flap = me.copy(), me.copy()
    for m2, keep in ((body, False), (flap, True)):
        b = bmesh.new()
        b.from_mesh(m2)
        bmesh.ops.delete(b, geom=[q for q in b.faces if (q.material_index in flap_i) != keep], context="FACES")
        b.to_mesh(m2)
        b.free()
    v = np.array([x.co[:] for x in flap.vertices])
    hinge = mathutils.Vector((0.0, v[:, 1].min(), (v[:, 2].min() + v[:, 2].max()) / 2))
    flap.transform(mathutils.Matrix.Translation(-hinge))
    cut[me.name] = (body, flap, hinge)
flaps = {}
for o in sockets:
    body, flap, hinge = cut[o.data.name]
    o.data = body
    fo = bpy.data.objects.new(o.name + " flap", flap)
    sc.collection.objects.link(fo)
    fo.parent = o
    fo.location = hinge
    flaps[o] = fo
    if o in start:
        show_from(fo, start[o])
# which way opens: the flap's middle must swing away from the board (local +z)
probe = next(iter(flaps.values()))
mid = mathutils.Vector(np.array([x.co[:] for x in probe.data.vertices]).mean(0))
OPEN_SIGN = 1.0 if (mathutils.Matrix.Rotation(FLAP_OPEN, 3, "X") @ mid).z > mid.z else -1.0

pcb = bpy.data.objects["PCB_left"]                 # each socket at home in the root's frame (its keys aside)
sock_at = {o: np.array((pcb.matrix_parent_inverse @ pcb.matrix_basis @ o.matrix_parent_inverse
                        @ o.matrix_basis).translation) for o in sockets}
tail_objs = [o for o in bpy.data.objects if o.name.endswith(":flex tail")]
plug_at = wave(tail_objs, PLUG[0], PLUG[1], key=lambda o: row(bpy.data.objects[o["pk_ref"] + ":flex"]), jitter=0.1)
worst = 0.0
for tail in tail_objs:
    keys, end, length, turn, yaw = fpc_bend.bend_keys(tail)
    sock = min(sockets, key=lambda q: np.linalg.norm(sock_at[q][:2] - end[:2]))
    worst = max(worst, float(np.linalg.norm(sock_at[sock][:2] - end[:2])))
    t = plug_at[tail]
    fpc_bend.drive(keys, f(t + FLAP_T), f(t + FLAP_T + BEND_T))
    fo = flaps[sock]
    for sec, a in ((0, 0), (t, 0), (t + FLAP_T, 1), (t + FLAP_T + BEND_T, 1), (t + 2 * FLAP_T + BEND_T, 0)):
        fo.rotation_euler = (OPEN_SIGN * FLAP_OPEN * a, 0, 0)
        fo.keyframe_insert("rotation_euler", frame=f(sec))
    fo.rotation_euler = (0, 0, 0)
print("SW_K_10 plugs at", round(plug_at[bpy.data.objects["SW_K_10:flex tail"]], 2), "s")
print(f"flex tails plugged: {len(tail_objs)}, ends within {worst:.1f} mm of their socket's origin; flaps open {OPEN_SIGN:+.0f}")

# the plate with the status display and its holder: down to HOVER, wait for the
# diffuser, then down together onto the spacer
for o in plate_group:
    path(o, [(PLATE_IN[0], (0, 0, 100), None), (PLATE_IN[1], (0, 0, HOVER), ease_out),
             (PLATE_DOWN[0], (0, 0, HOVER), smooth), (PLATE_DOWN[1], ZERO, smooth)])
# the diffuser from the front (the viewer's side, -y), 4.5 mm below its seat and LED_DY
# nearer the camera: its light pipes come up through the switch holes (their lips
# would not pass the round slots), then it slides back, away from the camera, so
# each pipe moves into its LED slot
for o in diffuser:
    low = HOVER - 4.5
    path(o, [(DIFF_IN[0], (0, -170, low), None), (DIFF_IN[1], (0, -LED_DY, low), ease_out),
             (DIFF_IN[2], (0, -LED_DY, HOVER), smooth), (DIFF_IN[3], (0, 0, HOVER), smooth),
             (PLATE_DOWN[0], (0, 0, HOVER), smooth), (PLATE_DOWN[1], ZERO, smooth)])
# the case on the desk, under the floating board, which then comes down into it
for o in case:
    path(o, [(CASE_IN[0], (0, 200, -LIFT), None), (CASE_IN[1], (0, 0, -LIFT), ease_out),
             (SETTLE[0], (0, 0, -LIFT), smooth), (SETTLE[1], ZERO, smooth)])

# the right half, built already, waits 0.45 m off to the side (out of every close
# view) and slides in beside the left one while the camera pulls back
piv_r = right.parent
home_r = piv_r.location.copy()
for sec, away in ((0, 1), (RIGHT_IN[0], 1), (RIGHT_IN[1], 0)):
    piv_r.location = home_r + mathutils.Vector((0.45 * away, 0, 0))
    piv_r.keyframe_insert("location", frame=f(sec))
for k in fcurves(piv_r)[0].keyframe_points:
    k.interpolation = "BEZIER"
piv_r.location = home_r

# the board: bottom side up and lifted, turned over, then down into its case. The
# settle is keyed every frame with the case's own curve, so the case stays put on the desk
base_loc, base_rot = root.location.copy(), root.rotation_euler.copy()
lift = mathutils.Vector((0, 0, LIFT / 1000))       # root is in the pivot's frame (metres)
for sec, flip in ((0, 1), (FLIP[0], 1), (FLIP[1], 0), (FLIP_BACK[0], 0), (FLIP_BACK[1], 1),
                  (FLIP_UP[0], 1), (FLIP_UP[1], 0)):
    root.rotation_euler = (base_rot.x, base_rot.y + math.pi * flip, base_rot.z)   # about the short axis: the front stays in front
    root.keyframe_insert("rotation_euler", frame=f(sec))
for fc in fcurves(root):
    for k in fc.keyframe_points:
        k.interpolation = "BEZIER"
        k.easing = "AUTO"
root.location = base_loc + lift
root.keyframe_insert("location", frame=1)
a, b = f(SETTLE[0]), f(SETTLE[1])
for fr in range(a, b + 1):
    root.location = base_loc + lift * (1 - smooth((fr - a) / (b - a)))
    root.keyframe_insert("location", frame=fr)
root.location = base_loc

# ---- studio, cables, camera -----------------------------------------------------
materials.scene_settings(sc)
# the right half keeps the VRML board: its mask in pcb_shot/look.py's purple (9a55b0)
PCB_COLOUR = (0.323, 0.091, 0.434, 1)
for m in bpy.data.materials:
    if m.get("pk_role") == "solder mask":
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = PCB_COLOUR
tgt = bpy.data.objects.get("target")
# about 30% under the hero shots' lights: at full strength the matte white LEDs and
# the plate burn out to flat white (PK_LIGHT overrides, 1.0 = the hero shots)
lighting.studio(sc, tgt, scale=float(os.environ.get("PK_LIGHT", 0.7)))
# the board a little glossier than pcb_shot's (mask roughness 0.4 there)
for m in [o.active_material for o in bpy.data.objects if o.name == "PCB_left"]:
    for n in m.node_tree.nodes if m else []:
        trees = [n.node_tree] if n.bl_idname == "ShaderNodeGroup" and n.node_tree else []
        for q in [n] + [x for t in trees for x in t.nodes]:
            if q.bl_idname == "ShaderNodeBsdfPcbSolderMask":
                q.inputs["Roughness"].default_value = float(os.environ.get("PK_MASK_ROUGH", 0.22))
# the status display's 30-pin FPC socket (Hirose FH12): its housing is dark grey, not
# the model's white (mat4cad colours, as pcb_shot/look.py's FH34); its contacts stay
for o in parts:
    if not str(o.get("pk_lib", "")).startswith("Hirose_FH12"):
        continue
    for slot in o.material_slots:
        m = slot.material
        n = m.node_tree.nodes.get("Mat4cad BSDF") if m and m.node_tree else None
        if n is None:
            continue
        col = n.inputs["Color"].default_value[:3]
        print("FH12 material", m.name, n.mat_base, [round(c, 3) for c in col])
        if n.mat_base != "METAL":                  # housing and actuator; the contacts are METAL
            c = m.copy()
            grey = 0.035 if min(col) > 0.4 else 0.02      # the housing, the actuator a shade darker
            c.node_tree.nodes["Mat4cad BSDF"].inputs["Color"].default_value = (grey, grey, grey * 1.05, 1)
            slot.material = c
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
bpy.context.view_layer.update()

# the bridge cable comes down with both plugs pulled out of their ports along the plug
# axis, clear of the case walls, then the plugs push in sideways. The cable's ends
# follow through a shape key: "pulled" moves each end with its plug, fading out over
# 60 mm along the cable, so its U opens a little as the plugs go in.
DROP = 0.06                                        # m above the desk
plug_pull = {}
for r in (root, right):
    mine = [o for o in bridge if o.parent == r]
    shell = next(o for o in mine if o.name.endswith("plug shell"))
    xs = [v.co.x for v in shell.data.vertices]
    sx = 1.0 if sum(xs) > 0 else -1.0              # the port faces the other half
    pull = max(xs) - min(xs) + 1.0                 # mm: the whole shell out of the wall
    plug_pull[r] = (r.matrix_world.to_3x3() @ mathutils.Vector((sx * pull, 0, 0)), pull)
    pv = tuple(plug_pull[r][0])
    for o in mine:
        path(o, [(BRIDGE_IN[0], (pv[0], pv[1], pv[2] + DROP), None), (BRIDGE_IN[1], pv, ease_out),
                 (BRIDGE_IN[2], pv, smooth), (BRIDGE_IN[3], ZERO, smooth)], world=True)
print("bridge plugs pulled out", [round(p[1], 1) for p in plug_pull.values()], "mm")
cable = next(o for o in bridge if o.name.startswith("bridge cable"))
me = cable.data
co = np.array([v.co[:] for v in me.vertices])
ring = 21                                          # bridge_cable._tube: ring + 1 vertices a ring
n = len(co) // ring
cen = co[:n * ring].reshape(n, ring, 3).mean(1)
s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(cen, axis=0), axis=1))])
ends = [cable.matrix_world.inverted() @ (r.matrix_world @ mathutils.Vector((0, 0, 0))) for r in (root, right)]
# which end is the left plug's: the ring nearer the left half's centre
a_is_left = (mathutils.Vector(cen[0]) - ends[0]).length < (mathutils.Vector(cen[-1]) - ends[0]).length
da = np.array(plug_pull[root if a_is_left else right][0])
db = np.array(plug_pull[right if a_is_left else root][0])
fall = lambda d: 1 - np.array([smooth(x) for x in d / 0.06])
w = np.repeat(np.c_[fall(s), fall(s[-1] - s)], ring, axis=0)
cable.shape_key_add(name="Basis")
key = cable.shape_key_add(name="pulled")
moved = co.copy()
moved[:n * ring] += w[:, :1] * da + w[:, 1:] * db
key.data.foreach_set("co", moved.ravel())
path(cable, [(BRIDGE_IN[0], (0, 0, DROP), None), (BRIDGE_IN[1], ZERO, ease_out)], world=True)
for fr, v in ((1, 1.0), (f(BRIDGE_IN[2]), 1.0), (f(BRIDGE_IN[3]), 0.0)):
    key.value = v
    key.keyframe_insert("value", frame=fr)
key.value = 0.0

# the host cable slides in from 320 mm behind the keyboard (past the frame's top edge),
# slowing onto the port
HOST_FROM = root.matrix_world.to_3x3().normalized() @ mathutils.Vector((0, 0.32, 0))
for o in host:
    path(o, [(HOST_IN[0], HOST_FROM[:], None), (HOST_IN[1], (0, 0, 0), ease_out)], world=True)

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
# (s, target, width, elevation, azimuth, fill): one framing for the whole build (the
# 20 s view of the first draft), drifting a few degrees; then the pull-back to both halves
SHOTS = [(0.0, lift_c, lw, 40, -4, 0.74), (20.0, lift_c, lw, 40, 6, 0.74), (38.5, lift_c, lw, 38, 2, 0.74),
         (42.0, lift_c, lw, 50, 0, 0.86), (50.2, lift_c, lw, 50, 4, 0.86),      # closer and steeper for the sockets
         (52.4, lift_c, lw, 38, 2, 0.74),
         (55.8, left_c, lw, 36, -2, 0.76), (57.6, left_c, lw, 35, -4, 0.80),
         (60.2, both_c, both_w, 33, 0, 0.95), (END, both_c, both_w, 33, 3, 0.95)]
for s, c, w, el, az, fill in SHOTS:
    tgt.location = c
    cam.location = view(c, w, el, az, fill)
    tgt.keyframe_insert("location", frame=f(s))
    cam.keyframe_insert("location", frame=f(s))
for o in (tgt, cam):
    for fc in fcurves(o):
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
            k.handle_left_type = k.handle_right_type = "AUTO_CLAMPED"
studio.flag(sc)                                    # the caps' mirror card, for the closing view

if os.environ.get("PK_GPU", "").upper() not in ("", "NONE", "CPU"):
    # PK_GPU=OPTIX|CUDA|HIP|ONEAPI: every device of that kind (as eden_view.py); none found: the CPU
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = os.environ["PK_GPU"].upper()
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == os.environ["PK_GPU"].upper()]
        for d in prefs.devices:
            d.use = d in gpus
        if gpus:
            sc.cycles.device = "GPU"
        print("assembly gpu", os.environ["PK_GPU"], [d.name for d in gpus] or "none found: CPU")
    except TypeError as e:
        print("assembly gpu", os.environ["PK_GPU"], "unsupported here:", e, "- CPU")
# keep the scene's geometry between frames: only what moved is rebuilt. Same pixels
# (8 frames compared), 8.8 instead of 12 s a frame at 640 px on 4 threads
sc.render.use_persistent_data = True
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, f(END)
sc.cycles.samples = SAMPLES
sc.render.resolution_x, sc.render.resolution_y = WIDTH, int(round(WIDTH * 9 / 16 / 2)) * 2
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
os.makedirs(OUT, exist_ok=True)
if len(argv) > 3 and argv[3] == "stills":
    frames = [int(x) for x in argv[4].split(",") if x]          # "stills ," renders none (for a script after this one)
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
