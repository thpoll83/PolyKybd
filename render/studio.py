"""White-cove studio for the full-keyboard scene: splay, floor, flag, camera.

Used by rerender.py on a saved scene (blender_scene.py's .blend):

- `splay(deg)`: the halves are parented to two empties ("piv*") that
  blender_scene.py turned by +-10 deg about z; this sets them to +-deg.
- `cove()`: replaces the dark floor plane with a white seamless cove, a floor
  that curves up into a backdrop behind the keyboard, so the frame has no
  horizon line and the light falls off evenly.
- `flag()`: a matte black card ABOVE AND BEHIND the keyboard, out of frame.
  The camera looks down at about 33 deg, so a flat cap top mirrors whatever
  sits 33 deg up behind the keyboard; with a light or the white backdrop
  there, every cap shows a white patch and hides the display under it
  ("bright field"). With the card there the caps mirror black and the
  displays read through them ("dark field"), the way a product photographer
  shoots glass. The card is in no camera ray, so it never shows in the frame.

Sizes are metres; the keyboard sits at the origin, its front towards -y.
"""
import math

import bmesh
import bpy
import mathutils


def splay(deg, right=None):
    """Turn each half by deg: positive opens the halves towards the back (the
    inner ends move away, blender_scene.py's 10), negative brings the inner
    ends forward. `right` gives the right half its own angle.

    ⚠️ This was math.copysign(deg, x), which keeps only deg's SIZE: a negative
    angle turned the halves exactly like the positive one."""
    for o in bpy.data.objects:
        if o.name.startswith("piv") and o.type == "EMPTY":
            a = deg if o.location.x < 0 or right is None else right
            o.rotation_euler.z = math.radians(-math.copysign(1.0, o.location.x) * a)


def _material(name, rgb, roughness):
    if bpy.data.materials.get(name):        # fresh: an old one may carry glass settings
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    # a role materials.apply() does not know, so it leaves this alone: it
    # matches roles by colour, and the 0.9 floor reads as keycap glass
    m["pk_role"] = "studio"
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Specular IOR Level"].default_value = 0.3
    return m


def cove(sc, colour=(0.9, 0.9, 0.9), cove_light=80.0, back=0.7, radius=0.45, width=6.0, height=2.0):
    """Floor out to y=back, a quarter-circle of `radius` up into a wall."""
    for o in [o for o in sc.objects if o.type == "MESH" and (o.name.startswith("Plane") or o.name == "cove")]:
        bpy.data.objects.remove(o)
    prof = [(-3.0, 0.0), (back, 0.0)]
    n = 24
    for i in range(1, n + 1):
        a = -math.pi / 2 + (math.pi / 2) * i / n
        prof.append((back + radius * math.cos(a), radius + radius * math.sin(a)))
    prof.append((back + radius, height))
    bm = bmesh.new()
    rows = []
    for x in (-width / 2, width / 2):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new("cove")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new("cove", me)
    sc.collection.objects.link(o)
    me.materials.append(_material("cove white", colour, 0.55))
    # a light that reaches the cove and nothing else (Cycles light linking),
    # so the floor goes white without lifting the dark case with it
    coll = bpy.data.collections.get("cove only") or bpy.data.collections.new("cove only")
    if o.name not in coll.objects:
        coll.objects.link(o)
    ld = bpy.data.lights.get("cove light") or bpy.data.lights.new("cove light", "AREA")
    ld.shape, ld.size, ld.size_y, ld.energy = "RECTANGLE", 4.0, 3.0, cove_light
    lo = bpy.data.objects.get("cove light") or bpy.data.objects.new("cove light", ld)
    if lo.name not in sc.collection.objects:
        sc.collection.objects.link(lo)
    lo.location = (0.0, 0.3, 1.6)
    lo.light_linking.receiver_collection = coll
    # it lights only the cove, so nothing needs to see it: hidden from
    # reflections, it cannot show up as a white square on a cap top
    lo.visible_glossy = False
    lo.visible_transmission = False
    return o


def camera_elevation(sc, deg):
    """Raise or lower the camera around the target it tracks, keeping its
    distance and its bearing: deg above the desk (the import sets ~33)."""
    cam = sc.camera
    tgt = cam.constraints["Track To"].target.location if cam.constraints.get("Track To") else (0, 0, 0)
    v = cam.location - mathutils.Vector(tgt)
    flat = mathutils.Vector((v.x, v.y, 0))
    r, a = v.length, math.radians(deg)
    flat.normalize()
    cam.location = mathutils.Vector(tgt) + flat * (r * math.cos(a)) + mathutils.Vector((0, 0, r * math.sin(a)))


def flag(sc, distance=1.13, size=(2.0, 1.3)):
    """Black card facing the keyboard, in the cap tops' mirror direction:
    the view ray off a flat cap top leaves at the camera's own elevation,
    towards the side opposite the camera, so the card goes there."""
    cam = sc.camera.location
    d = mathutils.Vector((-cam.x, -cam.y, cam.z)).normalized() * distance
    centre = (d.x, d.y, d.z)
    old = bpy.data.objects.get("flag")
    if old:
        bpy.data.objects.remove(old)
    me = bpy.data.meshes.new("flag")
    w, h = size
    me.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("flag", me)
    o.location = centre
    # face the origin: tilt the card's normal (-y) down towards the keyboard
    o.rotation_euler.x = math.atan2(centre[2], centre[1])
    sc.collection.objects.link(o)
    me.materials.append(_material("flag black", (0.004, 0.004, 0.004), 0.9))
    o.visible_camera = False            # belt and braces: it is out of frame anyway
    return o


def white_look(sc):
    """AgX maps a lit white surface to light grey; the contrast look lifts
    the floor towards white and keeps the dark case dark."""
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
