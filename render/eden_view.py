"""Both halves from above at night: the layers of the Eden boot-animation video.

    blender -b render/out/hero.blend --python render/eden_view.py -- out samples width pass

`pass` picks the layer. eden_video.py adds them up per frame, which is exact
because light adds: a render of a sum of light sources is the sum of the
renders of each source.

- preview  everything at once, the rainbow frozen at t = 0 (for framing); PNG
- base     what is lit when the key LEDs are off: the indicator LEDs; EXR
- ambient  a dim room light alone (one soft area light), scaled per frame; EXR
- w, c1, s1  the key LEDs' light (emitter squares, cap glow, case glow) in
           white, weighted by 1, (1 + cos a) / 2 and (1 + sin a) / 2 of the
           rainbow's phase a over x. Any rainbow position is a sum of these
           three, to its first harmonic; EXR
- uv, id   which keycap screen pixel each image pixel sees through the glass:
           the screens emit their own coordinates (uv: R = u, G = v; id: R =
           the atlas cell), B = 1, and everything else is black. The glass is
           pure refraction, so one sample per pixel gives the exact answer, and
           B carries what the glass lets through. Rendered at twice `width`; EXR

The camera looks straight down (PK_ELEV, degrees above the horizon, default
90) through PK_LENS mm (default 50) and frames both halves' displays with
PK_MARGIN room (default 1.15). The look is the docs' RGB close-up: PK_PROFILE,
PK_DENT, PK_GLOW, PK_CASE_GLOW="strength", PK_FLEX, PK_EMIT, PK_POWER_LED,
PK_CASE_LEDS, PK_HIDE_ROLES as in closeup_view.py.
"""
import json
import math
import os
import sys
import tempfile

import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_cable  # noqa: E402
import keymatch  # noqa: E402
import materials  # noqa: E402
import profile  # noqa: E402
import rgb  # noqa: E402
import screens  # noqa: E402
import studio  # noqa: E402
import textured_parts  # noqa: E402

a = sys.argv[sys.argv.index("--") + 1:]
out, samples, width, PASS = os.path.abspath(a[0]), int(a[1]), int(a[2]), a[3]
LIGHT_PASSES = ("w", "c1", "s1")
STATUS_ID = 126                                   # id-pass cells of the status panels (126 left, 127 right)
MAP_PASSES = ("uv", "id")
assert PASS in ("preview", "base", "ambient") + LIGHT_PASSES + MAP_PASSES, PASS
# QMK's CYCLE_LEFT_RIGHT spreads hue = led x (0..224 of 256) across the board
HUE_SPAN = 224 / 256
env = os.environ.get

sc = bpy.context.scene
materials.tag(bpy)
halves = []
for side in ("left", "right"):
    root = bpy.data.objects[f"split72_{side}.wrl"]
    board = os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{side}.kicad_pcb")
    textured_parts.add(root, textured_parts.board_keys(board))
    halves.append((side, root, board))
materials.apply(bpy)
if PASS in MAP_PASSES:
    # the code atlas: every cell of screens_layer0.json holds its own pixel
    # coordinates (uv) or its cell number (id)
    ref = json.load(open(os.path.join(screens.TEX, "screens_layer0.json"), encoding="utf-8"))
    (aw, ah), (cw, ch) = ref["size"], ref["cell"]
    img = np.zeros((ah, aw, 3), np.float32)
    labels = sorted(ref["keys"])
    for n, label in enumerate(labels):
        x, y = ref["keys"][label]
        if PASS == "uv":
            img[y:y + ch, x:x + cw, 0] = ((np.arange(cw) + 0.5) / cw)[None, :]
            img[y:y + ch, x:x + cw, 1] = ((np.arange(ch) + 0.5) / ch)[:, None]
        else:
            img[y:y + ch, x:x + cw, 0] = (n + 0.5) / 128
        img[y:y + ch, x:x + cw, 2] = 1.0
    tmp = tempfile.mkdtemp()
    name = f"eden_{PASS}"
    json.dump({**ref, "labels": labels}, open(os.path.join(tmp, name + ".json"), "w"))
    import OpenImageIO as oiio                    # Blender's bundled copy
    for ext, data in ((".png", (img * 255).astype(np.uint8)), (".exr", img)):
        o = oiio.ImageOutput.create(name + ext)
        o.open(os.path.join(tmp, name + ext),
               oiio.ImageSpec(aw, ah, 3, oiio.UINT8 if ext == ".png" else oiio.FLOAT))
        o.write_image(data)
        o.close()
    # screens.keys() loads <atlas>.png; its material is then pointed at the
    # float EXR (below), so the 8-bit copy only has to exist
    im = bpy.data.images.load(os.path.join(tmp, name + ".exr"))
    im.name = name
    tex, screens.TEX = screens.TEX, tmp
    for side, root, board in halves:
        screens.keys(root, board, side, strength=1.0, atlas_name=name)
    screens.TEX = tex                             # the status quads load a real panel image;
    for side, root, board in halves:              # their material is replaced below
        screens.status(root, side, strength=1.0)
for side, root, board in halves:
    if env("PK_DENT"):
        profile.dent(root, board, *[float(v) for v in env("PK_DENT").split(",")])
    if env("PK_PROFILE"):
        profile.apply(root, board, env("PK_PROFILE"))
materials.scene_settings(sc)
rgb.night(sc)
rgb.clear_case()
if env("PK_FLOOR"):                               # "grey,roughness": the desk the board sits on
    _g, _r = (float(v) for v in env("PK_FLOOR").split(","))
    _b = bpy.data.materials["floor"].node_tree.nodes["Principled BSDF"]
    _b.inputs["Base Color"].default_value = (_g, _g, _g * 1.05, 1)
    _b.inputs["Roughness"].default_value = _r
studio.splay(float(env("PK_SPLAY", -2)), right=float(env("PK_SPLAY_RIGHT", -9)))
# PK_CABLES="bridge+host" rebuilds the cables after the halves have moved (below);
# without it a bridge saved in the scene is kept as it was
bridge_cable.remove(keep_bridge=not env("PK_CABLES"))
bpy.context.view_layer.update()


def half_box(root):
    ws = [o.matrix_world @ mathutils.Vector(c) for o in [root] + list(root.children_recursive)
          if o.type == "MESH" and not o.hide_render for c in o.bound_box]
    return min(w.x for w in ws), max(w.x for w in ws)


if env("PK_GAP"):                 # mm between the halves' facing edges: move both pivots
    gap = half_box(halves[1][1])[0] - half_box(halves[0][1])[1]
    shift = (gap - float(env("PK_GAP")) / 1000) / 2
    for o in bpy.data.objects:
        if o.name.startswith("piv") and o.type == "EMPTY":
            o.location.x -= math.copysign(1.0, o.location.x) * shift   # shift < 0 widens the gap
    bpy.context.view_layer.update()
    print("eden gap", round(gap * 1000, 1), "->", round((half_box(halves[1][1])[0] - half_box(halves[0][1])[1]) * 1000, 1), "mm")
CABLES = env("PK_CABLES", "").split("+")
if "bridge" in CABLES:
    bridge_cable.add(sc, [(root, board) for _, root, board in halves])
if "host" in CABLES:
    bridge_cable.add_host(sc, halves[0][1], halves[0][2])
bpy.context.view_layer.update()
for o in sc.objects:
    if o.active_material and o.active_material.get("pk_role") in env("PK_HIDE_ROLES", "").split(","):
        o.hide_render = True

# the rainbow's phase runs over both halves' LEDs, left to right
spans = [rgb.led_span(root, board) for _, root, board in halves]
X0, X1 = min(s[0] for s in spans), max(s[1] for s in spans)


def phase(x):
    return 2 * math.pi * HUE_SPAN * (x - X0) / (X1 - X0)


def weight(x):
    """The LED light's colour at world x for this pass."""
    if PASS == "w":
        return (1.0, 1.0, 1.0)
    if PASS == "c1":
        return (0.5 + 0.5 * math.cos(phase(x)),) * 3
    if PASS == "s1":
        return (0.5 + 0.5 * math.sin(phase(x)),) * 3
    import colorsys
    return colorsys.hsv_to_rgb((HUE_SPAN * (x - X0) / (X1 - X0)) % 1.0, 1, 1)


def weight_node(nt):
    """weight() as shader nodes over the shading point's world x."""
    n = nt.nodes
    sep = n.new("ShaderNodeSeparateXYZ")
    nt.links.new(n.new("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
    if PASS == "w":
        rgbn = n.new("ShaderNodeRGB")
        rgbn.outputs[0].default_value = (1, 1, 1, 1)
        return rgbn.outputs[0]
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = X0, X1
    mr.clamp = False
    nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    if PASS == "preview":
        mr.inputs["To Max"].default_value = HUE_SPAN
        fr = n.new("ShaderNodeMath")
        fr.operation = "FRACT"
        nt.links.new(mr.outputs["Result"], fr.inputs[0])
        col = n.new("ShaderNodeCombineColor")
        col.mode = "HSV"
        col.inputs[1].default_value = col.inputs[2].default_value = 1.0
        nt.links.new(fr.outputs[0], col.inputs[0])
        return col.outputs[0]
    mr.inputs["To Max"].default_value = 2 * math.pi * HUE_SPAN
    tri = n.new("ShaderNodeMath")
    tri.operation = "COSINE" if PASS == "c1" else "SINE"
    nt.links.new(mr.outputs["Result"], tri.inputs[0])
    half = n.new("ShaderNodeMath")
    half.operation = "MULTIPLY_ADD"
    half.inputs[1].default_value = half.inputs[2].default_value = 0.5
    nt.links.new(tri.outputs[0], half.inputs[0])
    gray = n.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(half.outputs[0], gray.inputs[i])
    return gray.outputs[0]


def volume_glow(role, strength):
    """rgb.glow() with this pass's colour: light trapped in the clear plastic."""
    for m in bpy.data.materials:
        if m.get("pk_role") != role:
            continue
        nt = m.node_tree
        o = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = strength
        nt.links.new(weight_node(nt), em.inputs["Color"])
        nt.links.new(em.outputs[0], o.inputs["Volume"])


if PASS in ("preview",) + LIGHT_PASSES:
    for side, root, board in halves:
        rgb.emitters(root, board, (0, 0), float(env("PK_EMIT", 6000)), z=float(env("PK_EMIT_Z", 4.4)))
    for o in sc.objects:
        if o.name.startswith("led emitter"):
            x = sum(v.co.x for v in o.data.vertices) / len(o.data.vertices)
            o.active_material.node_tree.nodes["Emission"].inputs["Color"].default_value = (*weight(x), 1)
    if float(env("PK_GLOW", 15)) > 0:
        volume_glow("keycap glass", float(env("PK_GLOW", 15)))
    if env("PK_CASE_GLOW"):
        volume_glow("case PLA", float(env("PK_CASE_GLOW")))
if PASS in ("preview", "base") and env("PK_POWER_LED"):
    for side, root, board in halves:
        rgb.indicator_leds(root, board, float(env("PK_POWER_LED")))
        if env("PK_CASE_LEDS"):
            rgb.case_indicator_glow(root, board, float(env("PK_CASE_LEDS")))
if env("PK_FLEX"):
    rgb.clear_flex(*[float(v) for v in env("PK_FLEX").split(",")])
if PASS == "ambient":                             # a dim room: one soft light, nothing else
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    d = bpy.data.lights.new("ambient", "AREA")
    d.shape, d.size = "DISK", 1.2
    d.energy = 40.0                                # W; eden_video.py scales it (PK_AMBIENT)
    d.color = (0.85, 0.9, 1.0)                     # a cool room light
    o = bpy.data.objects.new("ambient", d)
    sc.collection.objects.link(o)
    o.location = (-0.35, -0.55, 0.9)               # above, front left: the caps catch it at an angle
    o.rotation_euler = (mathutils.Vector((0, 0, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()
if PASS in LIGHT_PASSES:                          # the LEDs' light only: no other source
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)

if PASS in MAP_PASSES:
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        nt = m.node_tree
        o = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if o is None:
            continue
        for s in ("Surface", "Volume"):
            for link in list(o.inputs[s].links):
                nt.links.remove(link)
        if m.get("pk_role") == "keycap glass":
            # pure refraction: one deterministic path through the cap
            rf = nt.nodes.new("ShaderNodeBsdfRefraction")
            rf.inputs["Roughness"].default_value = 0.0
            rf.inputs["IOR"].default_value = 1.49
            rf.inputs["Color"].default_value = (1, 1, 1, 1)
            nt.links.new(rf.outputs[0], o.inputs["Surface"])
        elif m.name.startswith("lit status "):
            # the 128x64 status panels: uv = the quad's own uv, top row at G = 0;
            # id = STATUS_ID + side, past every key cell
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Strength"].default_value = 1.0
            if PASS == "uv":
                sep = nt.nodes.new("ShaderNodeSeparateXYZ")
                nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["UV"], sep.inputs[0])
                inv = nt.nodes.new("ShaderNodeMath")
                inv.operation = "SUBTRACT"
                inv.inputs[0].default_value = 1.0
                nt.links.new(sep.outputs["Y"], inv.inputs[1])
                col = nt.nodes.new("ShaderNodeCombineColor")
                nt.links.new(sep.outputs["X"], col.inputs[0])
                nt.links.new(inv.outputs[0], col.inputs[1])
                col.inputs[2].default_value = 1.0
                nt.links.new(col.outputs[0], em.inputs["Color"])
            else:
                n = STATUS_ID + (m.name.endswith("right"))
                em.inputs["Color"].default_value = ((n + 0.5) / 128, 0, 1, 1)
            nt.links.new(em.outputs[0], o.inputs["Surface"])
        elif m.name.startswith("lit legends eden_"):
            tex = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
            tex.image = bpy.data.images[f"eden_{PASS}"]
            tex.image.colorspace_settings.name = "Non-Color"
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Strength"].default_value = 1.0
            nt.links.new(tex.outputs["Color"], em.inputs["Color"])
            nt.links.new(em.outputs[0], o.inputs["Surface"])
        else:
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Color"].default_value = (0, 0, 0, 1)
            nt.links.new(em.outputs[0], o.inputs["Surface"])
    sc.cycles.caustics_refractive = True
    sc.cycles.use_denoising = False
    sc.cycles.filter_width = 0.01
    sc.cycles.samples = 1
    sc.cycles.use_adaptive_sampling = False
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
else:
    sc.cycles.samples = samples
    sc.cycles.filter_width = 1.0

# frame both halves' displays from above, or the keys a shot names
def key_frames(root, board, side):
    """{matrix label: (x, y, rot)} in the half's own frame (mm), as screens.keys() places them."""
    kb = textured_parts.board_keys(board)
    (tx, ty), _dz = textured_parts.fit(root, kb)
    kle = [k for k in keymatch.kle_keys(screens.KLE) if (int(k[0].split(",")[0]) < 5) == (side == "left")]
    labels, _ = keymatch.match(np.array([[x, -y] for x, y, _ in kb]), kle)
    return {lab: (x + tx, y + ty, r, _dz) for (x, y, r), lab in zip(kb, labels)}


KEYS = {}
for side, root, board in halves:
    for lab, f in key_frames(root, board, side).items():
        KEYS[lab] = (root, f)
CAP = 9.0                                         # mm: half a keycap, the footprint a press moves


def footprint(lab):
    """The 4 corners of key `lab`'s cap, world space, at the display top."""
    root, (x, y, r, dz) = KEYS[lab]
    z = textured_parts.DISP_TOP + dz
    return [root.matrix_world @ mathutils.Vector((*(textured_parts._rot((u, v), r) + (x, y)), z))
            for u, v in ((-CAP, -CAP), (CAP, -CAP), (CAP, CAP), (-CAP, CAP))]


_pressed = []                                     # (mesh, original coords) to put back


def press(lab, depth_mm):
    """Push key `lab`'s cap stack down by depth_mm: every vertex of its half inside the
    cap's footprint and no lower than the cap glass's lowest point there."""
    root, (x, y, r, _dz) = KEYS[lab]
    inv = root.matrix_world.inverted()
    objs = [o for o in root.children_recursive if o.type == "MESH" and not o.hide_render]
    zmin = None
    sel = []
    for o in objs:
        m = np.array(inv @ o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        loc = co @ m[:3, :3].T + m[:3, 3]
        d = loc[:, :2] - (x, y)
        a = math.radians(-r)
        u = d[:, 0] * math.cos(a) - d[:, 1] * math.sin(a)
        v = d[:, 0] * math.sin(a) + d[:, 1] * math.cos(a)
        inside = (abs(u) < CAP) & (abs(v) < CAP)
        if not inside.any():
            continue
        if o.active_material and o.active_material.get("pk_role") == "keycap glass":
            z0 = loc[inside, 2].min()
            zmin = z0 if zmin is None else min(zmin, z0)
        sel.append((o, m, co, loc, inside))
    assert zmin is not None, f"no keycap glass under {lab}"
    for o, m, co, loc, inside in sel:
        mv = inside & (loc[:, 2] >= zmin - 0.05)
        if not mv.any():
            continue
        if o.data.users > 1:
            o.data = o.data.copy()
        _pressed.append((o.data, co.copy()))
        loc2 = loc.copy()
        loc2[mv, 2] -= depth_mm
        mi = np.linalg.inv(m)
        new = loc2 @ mi[:3, :3].T + mi[:3, 3]
        o.data.vertices.foreach_set("co", new.ravel())
        o.data.update()
    print("press", lab, depth_mm, "mm,", len(_pressed), "meshes")


def unpress():
    while _pressed:
        me, co = _pressed.pop()
        me.vertices.foreach_set("co", co.ravel())
        me.update()


lo = mathutils.Vector((1e9,) * 3)
hi = -lo
for o in sc.objects:
    if o.type == "MESH" and o.name.endswith("display decals"):
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            lo, hi = mathutils.Vector(map(min, lo, w)), mathutils.Vector(map(max, hi, w))
BOARD_BOX = (lo, hi)
tgt = bpy.data.objects["target"]
cam = sc.camera
cam.data.dof.use_dof = False
cam.data.clip_start = 0.005
# the map passes are exactly twice the light passes in both axes (eden_video.py asserts it)
scale = 2 if PASS in MAP_PASSES else 1
W, H = width * scale, int(round(width * 9 / 16)) * scale
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
EXT = ".png" if PASS == "preview" else ".exr"
if out.endswith(".exr") or (env("PK_SHOTS") and EXT == ".exr"):
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.exr_codec = "ZIP"


def shot(path, focus=None, elev=None, azim=0.0, lens=None, margin=None, presses=None, fstop=0):
    """Render one camera. focus = matrix labels to frame (default both halves);
    elev / azim in degrees (azim turns the camera around the target, 0 = from the
    front); presses = {label: mm}."""
    for lab, mm in (presses or {}).items():
        press(lab, mm)
    bpy.context.view_layer.update()
    if focus:
        pts = [p for lab in focus for p in footprint(lab)]
        lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
        hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
    else:
        lo, hi = BOARD_BOX
    aim = mathutils.Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z))
    tgt.matrix_world = mathutils.Matrix.Translation(aim)   # world space: the target may have a parent
    bpy.context.view_layer.update()
    cam.data.lens = float(lens or env("PK_LENS", 50))
    fov = 2 * math.atan(cam.data.sensor_width / 2 / cam.data.lens)
    m = float(margin or env("PK_MARGIN", 1.15))
    need = max((hi.x - lo.x) * m, (hi.y - lo.y) * m * W / H)
    dist = need / 2 / math.tan(fov / 2)
    e = math.radians(min(float(elev if elev is not None else env("PK_ELEV", 90)), 89.9))
    az = math.radians(float(azim))
    cam.location = aim + mathutils.Vector((dist * math.cos(e) * math.sin(az),
                                                    -dist * math.cos(e) * math.cos(az), dist * math.sin(e)))
    cam.data.dof.use_dof = fstop > 0
    if fstop > 0:
        cam.data.dof.focus_object = tgt
        cam.data.dof.aperture_fstop = fstop
    print("eden camera", PASS, os.path.basename(path), "dist", round(dist, 3), "elev", math.degrees(e), "frame", W, H)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    unpress()


if env("PK_SHOTS"):                               # out is a directory: <out>/<shot name>.exr per shot
    os.makedirs(out, exist_ok=True)
    only = set(env("PK_ONLY", "").split(",")) - {""}
    for s in json.load(open(env("PK_SHOTS"), encoding="utf-8")):
        if only and s["name"] not in only:
            continue
        shot(os.path.join(out, s["name"] + EXT), s.get("focus"), s.get("elev"), s.get("azim", 0.0),
             s.get("lens"), s.get("margin"), s.get("press"), s.get("fstop", 0))
else:
    shot(out)
