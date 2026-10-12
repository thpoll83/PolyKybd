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
# the room light at its other places: ambient_m in the middle, ambient_r front right (the
# tutorial video walks it across during the languages); otherwise exactly the ambient pass
AMBIENT_X = {"ambient": -0.35, "ambient_m": 0.0, "ambient_r": 0.35}.get(PASS, -0.35)
if PASS in ("ambient_m", "ambient_r"):
    PASS = "ambient"
LIGHT_PASSES = ("w", "c1", "s1")
STATUS_ID = 126                                   # id-pass cells of the status panels (126 left, 127 right)
MAP_PASSES = ("uv", "id")
# led: the light of up to three single keys, one per colour channel (PK_LED_KEYS)
assert PASS in ("preview", "base", "ambient", "led") + LIGHT_PASSES + MAP_PASSES, PASS
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
    ref["keys"] = keymatch.code_atlas(ref, screens.KLE)
    (aw, ah), (cw, ch) = ref["size"], ref["cell"]
    # ⚠️ the uv atlas is SUPER times finer than the display: with one texel per display
    # pixel, every point inside a pixel read back that pixel's centre, so the compositor
    # could not tell where in a pixel it was and drew no pixel grid on the keycaps at all
    # (the status panels read their quad's own continuous uv and always had it)
    sup = int(env("PK_UV_SUPER", 8)) if PASS == "uv" else 1
    img = np.zeros((ah * sup, aw * sup, 3), np.float32)
    labels = sorted(ref["keys"])
    for n, label in enumerate(labels):
        x, y = ref["keys"][label]
        x, y, w_, h_ = x * sup, y * sup, cw * sup, ch * sup
        if PASS == "uv":
            img[y:y + h_, x:x + w_, 0] = ((np.arange(w_) + 0.5) / w_)[None, :]
            img[y:y + h_, x:x + w_, 1] = ((np.arange(h_) + 0.5) / h_)[:, None]
        else:
            img[y:y + h_, x:x + w_, 0] = (n + 0.5) / 128
        img[y:y + h_, x:x + w_, 2] = 1.0
    aw, ah = aw * sup, ah * sup
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
if env("PK_GPU", "").upper() not in ("", "NONE", "CPU"):
    # PK_GPU=OPTIX|CUDA|HIP|ONEAPI|METAL: render on every device of that kind; a machine
    # without one falls back to the CPU with a note rather than failing
    _prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        _prefs.compute_device_type = env("PK_GPU").upper()
        _prefs.get_devices()
        _gpus = [d for d in _prefs.devices if d.type == env("PK_GPU").upper()]
        for d in _prefs.devices:
            d.use = d in _gpus
        if _gpus:
            sc.cycles.device = "GPU"
        print("eden gpu", env("PK_GPU"), [d.name for d in _gpus] or "none found: CPU")
    except TypeError as e:
        print("eden gpu", env("PK_GPU"), "unsupported here:", e, "- CPU")
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
    # ⚠️ "".split(",") is [""], which matches every UNTAGGED mesh (the desk, the plate's
    # Rosetta silkscreen): an empty PK_HIDE_ROLES must hide nothing
    if o.active_material and o.active_material.get("pk_role") in [r for r in env("PK_HIDE_ROLES", "").split(",") if r]:
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


DIFF_GLOW = float(env("PK_DIFFUSER_GLOW", 0))   # >0: the diffuser frames are the key LEDs' light
DIFF_FALL = float(env("PK_DIFFUSER_FALL", 3.0))  # mm: how far the glow spreads from each LED in the resin


def diffuser_setup():
    """Per vertex of each half's diffuser frame: the nearest LED (its world xy) and a
    falloff 1 / (1 + (d / DIFF_FALL)^2)^2 from it, stored as the float attribute
    "led_fall". Returns [(mesh, nearest LED xy per vertex, falloff)] for the led pass."""
    out = []
    for side, root, board in halves:
        pos, _ = rgb.led_points(root, board, (0, 0), float(env("PK_EMIT_Z", 4.4)))
        for o in root.children_recursive:
            if o.type != "MESH" or not o.active_material or o.active_material.get("pk_role") != "diffuser resin":
                continue
            mw = np.array(o.matrix_world)
            co = np.empty(len(o.data.vertices) * 3)
            o.data.vertices.foreach_get("co", co)
            w = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
            d2 = ((w[:, None, :2] - pos[None, :, :2]) ** 2).sum(-1)
            near = d2.argmin(1)
            d = np.sqrt(d2[np.arange(len(w)), near]) * 1000
            fall = (1 / (1 + (d / DIFF_FALL) ** 2)) ** 2
            a = o.data.attributes.get("led_fall") or o.data.attributes.new("led_fall", "FLOAT", "POINT")
            a.data.foreach_set("value", fall.astype(np.float32))
            out.append((o, pos[near, :2], fall))
    return out


def diffuser_emission(color_socket_fn):
    """Emission on the diffuser material: color_socket_fn(nt) gives the colour,
    times "led_fall", times DIFF_GLOW."""
    for m in bpy.data.materials:
        if m.get("pk_role") != "diffuser resin":
            continue
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        att = nt.nodes.new("ShaderNodeAttribute")
        att.attribute_name = "led_fall"
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        a_in, b_in = [i for i in mul.inputs if i.type == "RGBA"]
        nt.links.new(color_socket_fn(nt), a_in)
        nt.links.new(att.outputs["Fac"], b_in)
        nt.links.new(next(o for o in mul.outputs if o.type == "RGBA"), b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = DIFF_GLOW


if PASS in ("preview",) + LIGHT_PASSES and DIFF_GLOW > 0:
    diffuser_setup()
    diffuser_emission(weight_node)
if PASS in ("preview",) + LIGHT_PASSES:
    for side, root, board in halves:
        if DIFF_GLOW > 0:
            break                                 # the frames carry the light; no emitter squares
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
    o.location = (AMBIENT_X, -0.55, 0.9)           # above, front left: the caps catch it at an angle
    o.rotation_euler = (mathutils.Vector((0, 0, 0)) - o.location).to_track_quat("-Z", "Y").to_euler()
if PASS not in MAP_PASSES and env("PK_SILK"):
    # the plate's Rosetta silkscreen and the board silk (untagged white meshes): PK_SILK =
    # "value,roughness,glow". A lower value and a rougher, less specular finish keep the
    # white from flaring in the room light; the glow (ambient pass only, so it rises and
    # falls with the room light) keeps it readable
    val, rough, glow = (float(v) for v in env("PK_SILK").split(","))
    for m in {o.active_material for o in sc.objects if o.type == "MESH" and o.active_material}:
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.use_nodes else None
        if m.get("pk_role") or b is None or min(b.inputs["Base Color"].default_value[:3]) < 0.9:
            continue
        b.inputs["Base Color"].default_value = (val, val, val, 1)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Specular IOR Level"].default_value = 0.15
        if "Coat Weight" in b.inputs:
            b.inputs["Coat Weight"].default_value = 0.0
        if PASS == "ambient" and glow > 0:
            b.inputs["Emission Color"].default_value = (1, 1, 1, 1)
            b.inputs["Emission Strength"].default_value = glow
        print("silk", m.name)
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
CAP = 9.0                                         # mm: half a 1U keycap (the camera's footprint)


def kle_sizes(path):
    """{matrix label: (w, h)} in U, from the KLE (keymatch.kle_keys() keeps only centres)."""
    out = {}
    for row in json.load(open(path, encoding="utf-8")):
        if not isinstance(row, list):
            continue
        w = h = 1.0
        for item in row:
            if isinstance(item, dict):
                w, h = item.get("w", w), item.get("h", h)
                continue
            out[item.split("\n")[0]] = (w, h)
            w = h = 1.0
    return out


SIZES = kle_sizes(screens.KLE)


def footprint(lab):
    """The 4 corners of key `lab`'s cap, world space, at the display top."""
    root, (x, y, r, dz) = KEYS[lab]
    z = textured_parts.DISP_TOP + dz
    return [root.matrix_world @ mathutils.Vector((*(textured_parts._rot((u, v), r) + (x, y)), z))
            for u, v in ((-CAP, -CAP), (CAP, -CAP), (CAP, CAP), (-CAP, CAP))]


_pressed = []                                     # (mesh, original coords) to put back


def press(lab, depth_mm):
    """Push key `lab`'s cap stack down by depth_mm: every vertex of its half inside the
    cap's footprint and no lower than the lowest point of its moving stack there."""
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
        # the whole cap: a 1.25U Shift is wider than CAP, and a press that moved only the
        # middle left its top face standing over the lowered display
        w_, h_ = SIZES.get(lab, (1.0, 1.0))
        inside = (abs(u) < w_ * 19.05 / 2 - 0.4) & (abs(v) < h_ * 19.05 / 2 - 0.4)
        if not inside.any():
            continue
        # the key's moving stack: the cap, its stem, the display and its decal. The cap
        # glass alone starts ABOVE the display (19.3 vs 17.3 mm on the left Shift), so
        # keying the press to the glass left the display behind and the cap came down
        # over it.
        if o.active_material and o.active_material.get("pk_role") in (
                "keycap glass", "stem", "display face", "display decal"):
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


if PASS == "led":
    # One key's LED per colour channel, everything else dark: PK_LED_KEYS="r,c;r,c;r,c"
    # (red;green;blue, "-" for none). The case and keycaps are near-neutral, so a
    # channel of the result is that key's white light to within their tint; the
    # tutorial video recolours and sums these per frame (tutorial_video.py).
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)
    chans = env("PK_LED_KEYS", "").split(";")
    want = {lab: i for i, lab in enumerate(chans) if lab and lab != "-"}
    centre = {lab: sum(footprint(lab), mathutils.Vector()) / 4 for lab in KEYS}
    want = {lab: ch for lab, ch in want.items() if lab in centre}   # the encoders have no key footprint
    if DIFF_GLOW > 0:
        # the frame glows around each lit key's LED, in that key's channel
        for o, near, fall in diffuser_setup():
            col = np.zeros((len(fall), 4), np.float32)
            col[:, 3] = 1
            for lab, ch in want.items():
                m = ((near[:, 0] - centre[lab].x) ** 2 + (near[:, 1] - centre[lab].y) ** 2) < 0.012 ** 2
                col[m, ch] = fall[m]
            a = o.data.color_attributes.get("led_rgb") or o.data.color_attributes.new("led_rgb", "FLOAT_COLOR", "POINT")
            a.data.foreach_set("color", col.ravel())

        def _led_col(nt):
            att = nt.nodes.new("ShaderNodeAttribute")
            att.attribute_name = "led_rgb"
            return att.outputs["Color"]
        for m in bpy.data.materials:
            if m.get("pk_role") == "diffuser resin":
                b = m.node_tree.nodes["Principled BSDF"]
                nt = m.node_tree
                nt.links.new(_led_col(nt), b.inputs["Emission Color"])
                b.inputs["Emission Strength"].default_value = DIFF_GLOW
    for side, root, board in halves:
        if DIFF_GLOW > 0:
            break
        rgb.emitters(root, board, (0, 0), float(env("PK_EMIT", 6000)), z=float(env("PK_EMIT_Z", 4.4)))
    kept = 0
    for o in [o for o in sc.objects if o.name.startswith("led emitter")]:
        c = o.matrix_world @ (sum((v.co for v in o.data.vertices), mathutils.Vector()) / len(o.data.vertices))
        lab = min(centre, key=lambda k: (centre[k].x - c.x) ** 2 + (centre[k].y - c.y) ** 2)
        if lab not in want or (centre[lab].xy - c.xy).length > 0.012:
            bpy.data.objects.remove(o)
            continue
        col = [0.0, 0.0, 0.0, 1.0]
        col[want[lab]] = 1.0
        o.active_material.node_tree.nodes["Emission"].inputs["Color"].default_value = col
        kept += 1
    print("led pass", want, "emitters kept", kept)
    # the light trapped in each lit key's clear cap, masked to that key
    glow = float(env("PK_GLOW", 15))
    for m in bpy.data.materials:
        if m.get("pk_role") != "keycap glass" or glow <= 0 or not want:
            continue
        nt = m.node_tree
        out_n = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        pos = nt.nodes.new("ShaderNodeNewGeometry").outputs["Position"]
        total = None
        for lab, ch in want.items():
            d = nt.nodes.new("ShaderNodeVectorMath")
            d.operation = "DISTANCE"
            nt.links.new(pos, d.inputs[0])
            d.inputs[1].default_value = (centre[lab].x, centre[lab].y, 0.0)
            # distance in xy only: project the position onto the floor plane first
            flat = nt.nodes.new("ShaderNodeVectorMath")
            flat.operation = "MULTIPLY"
            flat.inputs[1].default_value = (1.0, 1.0, 0.0)
            nt.links.new(pos, flat.inputs[0])
            nt.links.new(flat.outputs[0], d.inputs[0])
            lt = nt.nodes.new("ShaderNodeMath")
            lt.operation = "LESS_THAN"
            lt.inputs[1].default_value = CAP * 1.05 / 1000
            nt.links.new(d.outputs["Value"], lt.inputs[0])
            col = nt.nodes.new("ShaderNodeCombineColor")
            nt.links.new(lt.outputs[0], col.inputs[ch])
            if total is None:
                total = col.outputs[0]
            else:
                add = nt.nodes.new("ShaderNodeMix")
                add.data_type = "RGBA"
                add.blend_type = "ADD"
                add.inputs["Factor"].default_value = 1.0
                a_in, b_in = [i for i in add.inputs if i.type == "RGBA"]
                nt.links.new(total, a_in)
                nt.links.new(col.outputs[0], b_in)
                total = next(o for o in add.outputs if o.type == "RGBA")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = glow
        nt.links.new(total, em.inputs["Color"])
        nt.links.new(em.outputs[0], out_n.inputs["Volume"])

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


def set_size(size=1.0):
    """A shot's resolution: `width` x 16:9, times its own size factor (a shot the video
    pans across is rendered larger and cropped), times 2 for the map passes."""
    global W, H
    w = int(round(width * size))
    W, H = w * scale, int(round(w * 9 / 16)) * scale
    sc.render.resolution_x, sc.render.resolution_y = W, H


set_size()
sc.render.resolution_percentage = 100
EXT = ".png" if PASS == "preview" else ".exr"
if out.endswith(".exr") or (env("PK_SHOTS") and EXT == ".exr"):
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    sc.render.image_settings.exr_codec = "ZIP"


def shot(path, focus=None, elev=None, azim=0.0, lens=None, margin=None, presses=None, fstop=0, size=1.0):
    """Render one camera. focus = matrix labels to frame (default both halves);
    elev / azim in degrees (azim turns the camera around the target, 0 = from the
    front); presses = {label: mm}; size scales the resolution."""
    set_size(size)
    for lab, mm in (presses or {}).items():
        press(lab, mm)
    bpy.context.view_layer.update()
    if focus == "status":                          # both status panels
        pts = []
        for side, root, board in halves:
            loc = textured_parts._display_points(root, "status lcd")
            pts += [root.matrix_world @ mathutils.Vector(tuple(v)) for v in loc]
        lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
        hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
    elif focus:
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
             s.get("lens"), s.get("margin"), s.get("press"), s.get("fstop", 0), s.get("size", 1.0))
else:
    shot(out)
