"""One PolyKybd key in Blender, for tuning materials fast.

    blender -b --python render/key_scene.py -- out.png [samples] [width] [angle|top]

Imports the six models of SW_K_2 (a 1U key on the left board) straight from
poly_kybd/models with the offsets, scales and rotations the board gives them,
adds a patch of PCB and of the aluminium plate with the 14 mm switch hole, and
renders a close-up. Materials come from materials.py, the same table the
full scene uses. Renders in about a minute on 4 CPUs at 64 samples, against
~25 minutes for the whole keyboard. Saves out.blend next to the PNG.
"""
import math
import os
import re
import sys

import addon_utils
import bmesh
import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import materials  # noqa: E402
import textured_parts  # noqa: E402

REPO = os.path.dirname(HERE)
BOARD = os.path.join(REPO, "poly_kybd", "poly_kybd_split72_left.kicad_pcb")
REF = "SW_K_2"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = os.path.abspath(argv[0] if argv else "key.png")
samples = int(argv[1]) if len(argv) > 1 else 64
width = int(argv[2]) if len(argv) > 2 else 1200
view = argv[3] if len(argv) > 3 else "angle"      # "angle" or "top"


def key_models():
    """(path, offset mm, scale, rotate deg) of every model on REF, read from the board."""
    t = open(BOARD, encoding="utf-8").read()
    i = t.index(f'(property "Reference" "{REF}"')
    s = t.rindex("\n\t(footprint ", 0, i)
    e = t.index("\n\t(footprint ", i)
    out = []
    for m in re.finditer(r'\(model "([^"]+)"(.*?)\n\t\t\)', t[s:e], re.S):
        vals = [tuple(float(v) for v in x.split()) for x in re.findall(r"\(xyz ([^)]*)\)", m.group(2))]
        path = m.group(1).replace("${KIPRJMOD}", os.path.join(REPO, "poly_kybd"))
        if path.endswith(".wrl"):           # the plate (.wrz) is built below instead
            out.append((path, *vals))
    return out


def import_model(path, offset, scale, rotate):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.x3d(filepath=path, axis_forward="Y", axis_up="Z")
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(os.path.basename(path), None)
    bpy.context.scene.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    # KiCad: VRML models are in 0.1 inch; offset in mm; rotations are applied
    # clockwise-positive (see poly_kybd/models/README.md, the lid angle)
    root.scale = tuple(2.54 * s for s in scale)
    root.rotation_mode = "XYZ"
    root.rotation_euler = tuple(-math.radians(r) for r in rotate)
    root.location = offset
    return root


def slab(name, size, z0, z1, rgb, hole=None):
    """A box from z0 to z1 (mm), optionally with a square hole through it."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size
        v.co.y *= size
        v.co.z = z0 if v.co.z < 0 else z1
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if hole:
        cut = bpy.data.objects.new(name + " hole", bpy.data.meshes.new(name + " hole"))
        bm2 = bmesh.new()
        bmesh.ops.create_cube(bm2, size=1.0)
        for v in bm2.verts:
            v.co.x *= hole
            v.co.y *= hole
            v.co.z = (z0 - 1) if v.co.z < 0 else (z1 + 1)
        bm2.to_mesh(cut.data)
        bpy.context.scene.collection.objects.link(cut)
        mod = ob.modifiers.new("hole", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cut
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier="hole")
        bpy.data.objects.remove(cut)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    me.materials.append(mat)
    return ob


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("io_scene_x3d")
    sc = bpy.context.scene
    world_root = bpy.data.objects.new("key", None)
    sc.collection.objects.link(world_root)
    for path, off, scale, rot in key_models():
        import_model(path, off, scale, rot).parent = world_root
    # PCB (green mask) and the aluminium plate patch, top 5.0 mm above the PCB
    slab("pcb", 40, -1.6, 0.0, (0.07, 0.2, 0.12)).parent = world_root
    slab("plate", 40, 3.4, 5.0, (0.58, 0.59, 0.61), hole=14.0).parent = world_root
    materials.tag(bpy)
    textured_parts.add(world_root, [(0.0, 0.0, 0.0)])   # the key sits at the origin, unrotated
    world_root.scale = (0.001,) * 3          # mm -> m
    print("material roles", materials.apply(bpy))

    # light + camera, close up from the front-left, slightly above
    tgt = bpy.data.objects.new("target", None)
    tgt.location = (0, 0, 0.010)
    sc.collection.objects.link(tgt)

    def area(name, loc, energy, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.size, d.color = energy, size, color
        o = bpy.data.objects.new(name, d)
        o.location = loc
        sc.collection.objects.link(o)
        o.constraints.new("TRACK_TO").target = tgt

    area("key", (-0.08, -0.10, 0.12), 2.0, 0.10)
    area("fill", (0.10, -0.06, 0.06), 0.7, 0.12, (0.85, 0.9, 1))
    area("rim", (0.0, 0.12, 0.08), 1.5, 0.08, (1, 0.9, 0.8))
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.015, 0.015, 0.02, 1)
    cd = bpy.data.cameras.new("cam")
    cd.lens = 85
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = (-0.05, -0.09, 0.07) if view == "angle" else (0.0, -0.004, 0.11)
    cam.constraints.new("TRACK_TO").target = tgt
    cd.dof.use_dof, cd.dof.focus_object, cd.dof.aperture_fstop = True, tgt, 5.6

    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    materials.scene_settings(sc)
    sc.render.resolution_x, sc.render.resolution_y = width, int(width * 3 / 4)
    sc.render.filepath = out
    sc.view_settings.view_transform = "AgX"
    bpy.ops.wm.save_as_mainfile(filepath=out.rsplit(".", 1)[0] + ".blend", compress=True)
    bpy.ops.render.render(write_still=True)


main()
