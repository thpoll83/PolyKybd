"""Blender render of one preview_stems.scad row, for render_profiles.sh --blender.

    blender -b --python parts/keycap_stem/render_profiles_blender.py -- \
        <row.stl> <out.png> [samples]

The same picture as the OpenSCAD render (same camera, the coordinate axes,
cream background), with shading and shadows instead of OpenSCAD's flat preview
colours, where every cut face is green. render_profiles.sh exports the STL from
preview_stems.scad and calls this; run that, not this, so all four views share
the camera.

The camera is render_profiles.sh's CAM (gimbal 78,0,90 at 150 mm, so 12 deg
above level, looking along -x at the row's bounding-box centre), with no roll.
⚠️ The axes are the reference each stem angle is read against (NOTES.md): they
pass through the true origin, the stems' base, solid on the positive side and
dashed on the negative side, as OpenSCAD draws them. Never roll the camera or
turn the row to make it read better.

PK_RGB="r,g,b" sets the stem colour, PK_SHIFT_Y moves the frame (fraction of
the width).
"""
import math
import os
import sys

import bpy
import mathutils

a = sys.argv[sys.argv.index("--") + 1:]
stl, out = a[0], a[1]
samples = int(a[2]) if len(a) > 2 else 128

ELEV, LENS, DIST = 12.0, 31.4, 0.150          # deg, mm, m
WIDTH, HEIGHT = 1300, 430                      # render_profiles.sh SIZE
RGB = tuple(float(v) for v in os.environ.get("PK_RGB", "0.80,0.52,0.04").split(","))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.wm.stl_import(filepath=stl, global_scale=0.001)
row = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = row
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))
bb = [row.matrix_world @ mathutils.Vector(c) for c in row.bound_box]
centre = sum(bb, mathutils.Vector()) / 8

m = bpy.data.materials.new("stem PLA")
m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (*RGB, 1)
b.inputs["Roughness"].default_value = 0.55
row.data.materials.append(m)


def emission(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs[0])
    return mat


axis_mat = emission("axis", (0, 0, 0))


def segment(p0, p1, radius=0.00007):
    p0, p1 = mathutils.Vector(p0), mathutils.Vector(p1)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=radius, depth=(p1 - p0).length,
                                        location=(p0 + p1) / 2)
    c = bpy.context.object
    c.rotation_euler = (p1 - p0).to_track_quat("Z", "Y").to_euler()
    c.data.materials.append(axis_mat)


L, DASH, GAP = 0.4, 0.0012, 0.0012              # m
for axis in range(3):
    end = [0.0, 0.0, 0.0]
    end[axis] = L
    segment((0, 0, 0), end)
    t = 0.0
    while t < L:
        p0, p1 = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        p0[axis], p1[axis] = -t, -min(t + DASH, L)
        segment(p0, p1)
        t += DASH + GAP

cd = bpy.data.cameras.new("cam")
cd.lens = LENS
cd.clip_start = 0.001
cd.shift_y = float(os.environ.get("PK_SHIFT_Y", -0.03))
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
e = math.radians(ELEV)
cam.location = centre + mathutils.Vector((DIST * math.cos(e), 0, DIST * math.sin(e)))
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()

# the cream background only for camera rays; a dim white world lights the part,
# so the two suns give it the contrast
w = bpy.data.worlds.new("w")
w.use_nodes = True
nt = w.node_tree
bg = nt.nodes["Background"]
bg.inputs[0].default_value = (1, 1, 0.78, 1)
amb = nt.nodes.new("ShaderNodeBackground")
amb.inputs[1].default_value = 0.08
lp = nt.nodes.new("ShaderNodeLightPath")
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
nt.links.new(amb.outputs[0], mix.inputs[1])
nt.links.new(bg.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], nt.nodes["World Output"].inputs[0])
sc.world = w
for direction, energy in (((0.2, -0.3, 0.5), 4.5), ((0.4, 0.3, 0.2), 0.3)):
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy = energy
    ld.angle = math.radians(20)
    lo = bpy.data.objects.new("sun", ld)
    sc.collection.objects.link(lo)
    lo.rotation_euler = (-mathutils.Vector(direction)).to_track_quat("-Z", "Y").to_euler()

sc.render.engine = "CYCLES"
sc.cycles.samples = samples
sc.cycles.use_denoising = True
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = WIDTH, HEIGHT
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
