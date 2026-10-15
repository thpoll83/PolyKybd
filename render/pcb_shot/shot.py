"""Render the imported board socket side up, as a product shot.

    PCB2BLENDER=<checkout> PK_HDRI=<studio .hdr> blender-5.1 -b --python render/pcb_shot/shot.py -- \
        out.png <samples> <width> <scene.blend> [<board.pcb3d>: cut the slots, mark the parts]

The scene is import.py's .blend. Lighting is a studio HDRI (Poly Haven's CC0
studio_small_09, 2k) for the fill and the reflections, plus one area key for
clean directional shadows; camera rays see a flat light grey instead of the
HDRI. The view transform is Khronos PBR Neutral, which keeps base colours as
authored: AgX turned the mask and the parts pastel. Under PBR Neutral a
bright highlight clips rather than rolls off, so the light levels are low and
exposure is left at 0. Every setting below has a PK_* override.
"""
import math
import os
import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
out, samples, width = argv[0], int(argv[1]), int(argv[2])
env = os.environ.get
# pcb2blender's materials use node types its add-on defines: register it, then
# open the scene, or every material renders white
sys.path.insert(0, env("PCB2BLENDER", "/tmp/pcb2blender"))
import pcb2blender_importer  # noqa: E402

pcb2blender_importer.register()
bpy.ops.wm.open_mainfile(filepath=argv[3])
sc = bpy.context.scene
pcb = next(o for o in bpy.data.objects if o.name.startswith("PCB_") and o.parent is None)   # PCB_left / PCB_right

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import look  # noqa: E402

board, ox, oy = look.prepare(pcb, argv[4] if len(argv) > 4 else None)

# socket side up: turn the board over about its long axis, lowest point on the floor
pcb.rotation_euler = (0, math.pi, 0)
bpy.context.view_layer.update()
objs = [pcb] + list(pcb.children_recursive)
pts = [o.matrix_world @ mathutils.Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
pcb.location -= mathutils.Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
bpy.context.view_layer.update()

# Part markings. The stock models carry none, and on the real board the
# RP2040, the flash, the inductors, the crystal and the shift registers show
# their laser marking clearly. The text is what these parts carry: part code
# and a date code. Placed on each body's top face, upright to the camera and
# never mirrored. Needs export.py's <board>.parts.json beside the .pcb3d.
MARKINGS = {                     # ref: (lines, text height in mm)
    "U10": ("RP2-B2\n21/24\nP64M15.00\nTTT", 0.85),
    "U9": ("25Q64ES\nBY2421", 0.32),
    "L1": ("2R2", 1.3), "L2": ("2R2", 1.3),
    "Y1": ("12.000\nTXC", 0.5),
    "U4": ("HC595\n2421", 0.42), "U5": ("HC595\n2421", 0.42), "U6": ("HC595\n2421", 0.42),
    "U7": ("HC595\n2421", 0.42), "U8": ("HC595\n2421", 0.42),
}
parts_json = os.path.splitext(argv[4])[0] + ".parts.json" if len(argv) > 4 else ""
if os.path.exists(parts_json):
    import json
    parts = json.load(open(parts_json))
    laser = bpy.data.materials.new("laser marking"); laser.use_nodes = True
    lb = laser.node_tree.nodes["Principled BSDF"]
    lb.inputs["Base Color"].default_value = (*[float(env("PK_MARK", 0.10))] * 3, 1)
    lb.inputs["Roughness"].default_value = 0.8
    bodies = []
    for o in pcb.children_recursive:
        if o.type == "MESH" and not o.name.startswith("SOLDER_"):
            pts = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
            bodies.append((o, sum((p for p in pts), mathutils.Vector()) / 8, max(p.z for p in pts)))
    for ref, (text, size) in MARKINGS.items():
        part = parts.get(ref)
        if not part:
            continue
        x, y = part["position"]
        at = board.matrix_world @ mathutils.Vector((x * 1e-3 + ox, -y * 1e-3 + oy, 0))
        body, centre, top = min(bodies, key=lambda b: (b[1].x - at.x) ** 2 + (b[1].y - at.y) ** 2)
        if (centre.xy - at.xy).length > 1.5e-3:
            print("marking: no body under", ref)
            continue
        cu = bpy.data.curves.new("mark " + ref, "FONT")
        cu.body, cu.size, cu.align_x, cu.align_y = text, size * 1e-3, "CENTER", "CENTER"
        cu.space_line = 1.05
        ob = bpy.data.objects.new("mark " + ref, cu)
        sc.collection.objects.link(ob)
        ob.data.materials.append(laser)
        angle = (-part["rotation"]) % 180.0          # along the part's edges, upright to the camera
        if angle > 90.0:
            angle -= 180.0
        ob.location = (at.x, at.y, top + 2e-5)
        ob.rotation_euler = (0, 0, math.radians(angle))
        print("marked", ref, body.name, "%.2f mm high" % ((top) * 1e3))

# floor
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
b = fm.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (*[float(env("PK_FLOOR", 0.75))] * 3, 1)
b.inputs["Roughness"].default_value = 0.55
floor.data.materials.append(fm)

# world: the studio HDRI lights and reflects; camera rays see a flat light grey
w = bpy.data.worlds.new("studio"); sc.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexEnvironment")
tex.image = bpy.data.images.load(env("PK_HDRI"))
mapping = nt.nodes.new("ShaderNodeMapping"); coord = nt.nodes.new("ShaderNodeTexCoord")
mapping.inputs["Rotation"].default_value = (0, 0, math.radians(float(env("PK_HDRI_ROT", 0))))
nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
hdr = nt.nodes.new("ShaderNodeBackground"); hdr.inputs["Strength"].default_value = float(env("PK_HDRI_STR", 0.15))
nt.links.new(tex.outputs["Color"], hdr.inputs["Color"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)
lp = nt.nodes.new("ShaderNodeLightPath"); mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
nt.links.new(hdr.outputs["Background"], mix.inputs[1]); nt.links.new(bg.outputs["Background"], mix.inputs[2])
o = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(mix.outputs[0], o.inputs["Surface"])

# one key light for clean, directional shadows
tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt); tgt.location = (0, 0, 0.003)
kd = bpy.data.lights.new("key", "AREA"); kd.size = float(env("PK_KEY_SIZE", 0.25)); kd.energy = float(env("PK_KEY", 12))
key = bpy.data.objects.new("key", kd); sc.collection.objects.link(key)
key.location = (-0.35, -0.30, 0.45); key.constraints.new("TRACK_TO").target = tgt

# camera
cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = float(env("PK_LENS", 24)); cd.clip_start = 0.01
elev, azim, dist = math.radians(float(env("PK_ELEV", 50))), math.radians(float(env("PK_AZIM", -8))), float(env("PK_DIST", 0.15))
cam.location = (dist * math.cos(elev) * math.sin(azim), -dist * math.cos(elev) * math.cos(azim), dist * math.sin(elev))
cam.constraints.new("TRACK_TO").target = tgt
cd.dof.use_dof = False                    # sharp to the last corner, like a focus-stacked product shot

sc.render.engine = "CYCLES"; sc.cycles.samples = samples; sc.cycles.use_denoising = True
sc.view_settings.view_transform = env("PK_VIEW", "Khronos PBR Neutral")   # keeps base colours, AgX pastels them
sc.view_settings.exposure = float(env("PK_EXPOSURE", 0))
if env("PK_LOOK"):
    sc.view_settings.look = env("PK_LOOK")
sc.render.resolution_x, sc.render.resolution_y = width, int(round(width * 0.62))
if env("PK_BORDER"):
    x0, y0, x1, y1 = (float(v) for v in env("PK_BORDER").split(","))
    sc.render.use_border, sc.render.use_crop_to_border = True, True
    sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = x0, y0, x1, y1
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
