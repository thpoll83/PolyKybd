"""The keyboard at work: both halves on a desk, a few things around it, a room behind.

    python3 render/workspace_assets.py                  # once: the Poly Haven assets
    blender -b render/out/hero.blend --python render/workspace_scene.py -- \
        office out.png [width] [samples]

Scenes are in workspace_scenes.py (office, front_desk, planning). The room is a
Poly Haven HDRI: it lights the scene and stands behind it, out of focus; the floor
plane catches the desk's shadow on it. The desk and the props are Poly Haven models
(CC0) at their real size, the front desk's counter is built here. The keyboard is
hero.blend's with its displays on (screens.py: the default layer and both status
panels), the bridge cable and a host cable over the desk's back edge to the floor; it
is lifted onto the desk top as one group.
"""
import math
import os
import sys

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bridge_cable  # noqa: E402
import materials  # noqa: E402
import screens  # noqa: E402
import textured_parts  # noqa: E402
from workspace_scenes import SCENES  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
NAME, OUT = argv[0], argv[1]
WIDTH = int(argv[2]) if len(argv) > 2 else 1600
SAMPLES = int(argv[3]) if len(argv) > 3 else 128
S = SCENES[NAME]
ASSETS = os.path.join(HERE, "out", "assets", "polyhaven")
sc = bpy.context.scene
root_l = bpy.data.objects["split72_left.wrl"]
root_r = bpy.data.objects["split72_right.wrl"]


def box(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ mathutils.Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return (mathutils.Vector([min(p[i] for p in pts) for i in range(3)]),
            mathutils.Vector([max(p[i] for p in pts) for i in range(3)]))


def gltf(aid, part=None):
    """Import a Poly Haven model (or one part of a set); returns its objects, with a
    new empty as their parent so the whole can be moved."""
    path = os.path.join(ASSETS, aid, f"{aid}_2k.gltf")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    if part:
        keep = [o for o in new if o.name.startswith(part) and (o.name == part or not o.name[len(part):][:1].isalpha())]
        keep += [c for k in keep for c in k.children_recursive]
        for o in [o for o in new if o not in keep]:
            bpy.data.objects.remove(o)
        new = keep
    tops = [o for o in new if o.parent is None or o.parent not in new]
    g = bpy.data.objects.new(f"{aid}:{part or 'all'}", None)
    sc.collection.objects.link(g)
    for o in tops:
        mw = o.matrix_world.copy()
        o.parent = g
        o.matrix_world = mw
    return g, [o for o in new]


def place(g, objs, at, turn=0.0, height=None, flat=False, base_z=0.0, origin=False):
    """g's footprint centred on `at` (x, y), its bottom on base_z, turned about z.
    origin=True puts the model's own origin on base_z and at (x, y) instead: a clamp
    lamp's origin is the desk top it clamps to, the clamp hangs below it."""
    if flat:                                       # a pen standing in the set's display: onto its side
        g.rotation_euler.x = math.radians(90)
    lo, hi = box(objs)
    if height:
        k = height / (hi.z - lo.z)
        g.scale = (k, k, k)
    g.rotation_euler.z = math.radians(turn)
    if origin:
        g.location = mathutils.Vector((at[0], at[1], base_z))
        bpy.context.view_layer.update()
        return
    lo, hi = box(objs)
    c = (lo + hi) / 2
    g.location += mathutils.Vector((at[0] - c.x, at[1] - c.y, base_z - lo.z))
    bpy.context.view_layer.update()


def principled(name, rgb, rough, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    return m


def cube(name, lo, hi, mat, bevel=0.003):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = [h - l for l, h in zip(lo, hi)]
    o.location = [(l + h) / 2 for l, h in zip(lo, hi)]
    bpy.ops.object.transform_apply(scale=True)
    m = o.modifiers.new("bevel", "BEVEL")
    m.width, m.segments = bevel, 3
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def counter():
    """A reception counter, 1.8 x 0.7 m, its worktop at 1.05 m: a white lacquer body,
    an oak-coloured worktop with a 25 mm lip over the front."""
    lacquer = principled("counter lacquer", (0.78, 0.78, 0.76), 0.25, coat=0.3)
    oak = principled("counter oak", (0.36, 0.22, 0.12), 0.45, coat=0.15)
    plinth = principled("counter plinth", (0.05, 0.05, 0.05), 0.6)
    parts = [cube("counter body", (-0.9, -0.33, 0.08), (0.9, 0.35, 1.02), lacquer),
             cube("counter plinth", (-0.88, -0.30, 0.0), (0.88, 0.33, 0.08), plinth),
             cube("counter top", (-0.92, -0.36, 1.02), (0.92, 0.36, 1.05), oak, bevel=0.004)]
    g = bpy.data.objects.new("@counter", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def monitor(spec):
    """A 27-inch class monitor: the panel (16:9, 6 mm bezel, 20 mm chin) tilted back
    `tilt` deg on an aluminium neck and base, the screen showing render/textures/
    workspace/<screen> as light. Built facing the viewer (-y), its base centred on
    the origin; returns the group and its objects."""
    diag = spec.get("inches", 27) * 0.0254
    sw, sh = diag * 16 / math.hypot(16, 9), diag * 9 / math.hypot(16, 9)
    lift, tilt = spec.get("lift", 0.11), math.radians(spec.get("tilt", 8))
    alu = principled("monitor aluminium", (0.55, 0.56, 0.58), 0.35)
    alu.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    shell = principled("monitor shell", (0.015, 0.015, 0.017), 0.4)
    glass = principled("monitor glass", (0.0, 0.0, 0.0), 0.12)
    img = bpy.data.images.load(os.path.join(HERE, "textures", "workspace", spec["screen"]))
    lit = bpy.data.materials.new("monitor screen")
    lit.use_nodes = True
    nt2 = lit.node_tree
    b = nt2.nodes["Principled BSDF"]
    tex = nt2.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt2.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    nt2.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Emission Strength"].default_value = spec.get("glow", 2.0)
    b.inputs["Roughness"].default_value = 0.15
    g = bpy.data.objects.new("monitor", None)
    sc.collection.objects.link(g)
    head = bpy.data.objects.new("monitor head", None)   # the panel's pivot, on the neck
    sc.collection.objects.link(head)
    head.parent = g
    z0 = lift + 0.02 + sh / 2                     # the screen's centre above the base
    head.location = (0, 0.012, z0)
    head.rotation_euler.x = -tilt                 # the top leans back, away from the viewer
    bz, bx = 0.006, 0.006
    parts = [cube("monitor panel", (-sw / 2 - bx, -0.004, -sh / 2 - 0.02), (sw / 2 + bx, 0.012, sh / 2 + bz), shell, 0.004),
             cube("monitor back", (-sw * 0.35, 0.012, -sh * 0.35), (sw * 0.35, 0.045, sh * 0.30), shell, 0.01),
             cube("monitor glass", (-sw / 2 - bx + 0.001, -0.0045, -sh / 2 - 0.019), (sw / 2 + bx - 0.001, -0.004, sh / 2 + bz - 0.001), glass, 0.0005)]
    bpy.ops.mesh.primitive_plane_add(size=1)
    scr = bpy.context.active_object
    scr.name = "monitor screen"
    scr.scale = (sw, sh, 1)
    scr.rotation_euler.x = math.radians(90)
    scr.location = (0, -0.0047, 0)
    scr.data.materials.append(lit)
    for o in parts + [scr]:
        o.parent = head
    neck = cube("monitor neck", (-0.03, 0.03, 0.006), (0.03, 0.05, z0 + 0.02), alu, 0.004)
    base = cube("monitor base", (-0.12, -0.07, 0.0), (0.12, 0.11, 0.006), alu, 0.003)
    for o in (neck, base):
        o.parent = g
    return g, parts + [scr, neck, base]


# ---- the room ------------------------------------------------------------------
for o in [o for o in sc.objects if o.type == "LIGHT"]:
    bpy.data.objects.remove(o)
w = sc.world
nt = w.node_tree
nt.nodes.clear()
env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(ASSETS, S["hdri"], f"{S['hdri']}_4k.hdr"))
mapping = nt.nodes.new("ShaderNodeMapping")
coord = nt.nodes.new("ShaderNodeTexCoord")
mapping.inputs["Rotation"].default_value[2] = math.radians(S["hdri_turn"])
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = S["hdri_strength"]
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
nt.links.new(env.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
floor = bpy.data.objects["Plane"]
floor.is_shadow_catcher = True                   # the room's own floor, with the desk's shadow on it

# ---- the cables, while the keyboard still stands on z = 0 ----------------------------
if S["desk"] == "@counter":
    desk, desk_objs = counter()
else:
    desk, desk_objs = gltf(S["desk"])
    if S.get("desk_height"):
        lo, hi = box(desk_objs)
        desk.scale.z = S["desk_height"] / (hi.z - lo.z)
lo, hi = box(desk_objs)
desk.location += mathutils.Vector((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z))
dlo, dhi = box(desk_objs)
top = dhi.z
kb_y = dlo.y + S["kb_from_front"]                 # the keyboard's centre on the desk
back_rel = dhi.y - kb_y                           # the desk's back edge, from the keyboard
bridge_cable.remove()
for r, side in ((root_l, "left"), (root_r, "right")):   # the legends and status panels lit
    board = os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{side}.kicad_pcb")
    k = S.get("legend_glow", 18.0)                 # well above the studio's 6: the room is daylight
    print(f"{side}: {screens.keys(r, board, side, strength=k)} legends lit, status panel {screens.status(r, side, strength=k * 0.7)}")
halves = [(r, os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{s}.kicad_pcb"))
          for r, s in ((root_l, "left"), (root_r, "right"))]
bridge_cable.add(sc, halves, depth=0.036, lean=0.004, toward=-1.0, spread=0.012, clear=0.022)
# the monitor, on the desk, before the host cable: the cable must pass beside its base
avoid = None
if S.get("monitor"):
    mon, mon_objs = monitor(S["monitor"])
    place(mon, mon_objs, (S["monitor"].get("x", 0.0), kb_y + S["monitor"]["y"]), S["monitor"].get("turn", 0),
          base_z=top)
    blo, bhi = box([o for o in mon_objs if o.name.startswith("monitor base")])
    m = 0.02                                       # clearance around the base
    avoid = (blo.x - m, bhi.x + m, blo.y - kb_y - m, bhi.y - kb_y + m)   # in the keyboard's frame, as the cable


def crosses(cable, rect):
    """Does the cable's plan pass over rect (x0, x1, y0, y1)?"""
    if rect is None:
        return False
    x0, x1, y0, y1 = rect
    return any(x0 < v.co.x < x1 and y0 < v.co.y < y1 for v in cable.data.vertices)


# the host cable: straight back from the port, then left of the monitor's base if it is
# in the way: swing further left in 30 mm steps until the plan is clear
for drift in [-0.10 - 0.03 * i for i in range(14)]:
    host = bridge_cable.add_host(sc, root_l, halves[0][1], end_y=back_rel - 0.004, drift=drift, turn=0.0)
    if not crosses(host, avoid):
        break
print(f"host cable: drift {drift:+.2f} m", "(clear of the monitor base)" if avoid else "")
# over the back edge and down to the floor: a quarter turn of 12 mm radius, then straight
me = host.data
end = max((v.co for v in me.vertices), key=lambda c: c.y)
r = bridge_cable.CABLE_R / 1000
x, y0 = end.x, back_rel - 0.004
pts = [(x, y0 - 0.01, r)]
for i in range(1, 13):
    a = math.pi / 2 * i / 12
    pts.append((x, y0 + 0.012 * math.sin(a), r - 0.012 * (1 - math.cos(a))))
for i in range(1, 9):
    pts.append((x, y0 + 0.012 + 0.002 * i, r - 0.012 - (top - 0.02) * i / 8))
drop = bridge_cable._tube("host cable drop", pts, [r] * len(pts), host.data.materials[0], ring=20,
                          v_scale=bridge_cable.BRAID_MM / 1000)
drop["pk_host"] = True

# ---- the keyboard onto the desk top, the props around it ----------------------
kb = bpy.data.objects.new("keyboard", None)
sc.collection.objects.link(kb)
mon_top = [mon] if avoid is not None else []
for o in [o for o in sc.objects if o.parent is None and o not in [kb, floor, desk] + mon_top and o.type != "CAMERA"
          and o not in desk_objs and o.name != "target"] + [bpy.data.objects["target"]]:
    mw = o.matrix_world.copy()
    o.parent = kb
    o.matrix_world = mw
kb.location = (0.0, kb_y, top)
bpy.context.view_layer.update()
for aid, part, x, y, turn, height, flat, *more in S["props"]:
    g, objs = gltf(aid, part)
    extra = more[0] if more else {}
    if extra.get("at_back"):                         # y from the desk's back edge instead
        y = back_rel - y
    place(g, objs, (x, kb_y + y), turn, height, flat, base_z=top, origin=extra.get("origin", False))

# ---- camera and render -----------------------------------------------------------
tgt = bpy.data.objects["target"]
cam = sc.camera
c = S["camera"]
aim = bpy.data.objects.new("aim", None)          # where the camera looks: above the keyboard, so the screen shows
sc.collection.objects.link(aim)
aim.location = tgt.matrix_world.translation + mathutils.Vector((0, c.get("aim_y", 0.0), c.get("aim_z", 0.0)))
focus = aim.location.copy()
e, a = math.radians(c["elev"]), math.radians(c["azim"])
d = c["distance"]
cam.matrix_world = mathutils.Matrix.Translation(focus + mathutils.Vector(
    (d * math.cos(e) * math.sin(a), -d * math.cos(e) * math.cos(a), d * math.sin(e))))
for k in list(cam.constraints):
    cam.constraints.remove(k)
tr = cam.constraints.new("TRACK_TO")
tr.target = aim
cam.data.lens = c["lens"]
cam.data.dof.use_dof = True
cam.data.dof.focus_object = tgt
cam.data.dof.aperture_fstop = c["fstop"]
cam.data.clip_start = 0.01
materials.scene_settings(sc)
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Base Contrast"
sc.cycles.samples = SAMPLES
sc.render.resolution_x, sc.render.resolution_y = WIDTH, int(round(WIDTH * 9 / 16 / 2)) * 2
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.abspath(OUT)
print(f"WORKSPACE {NAME}: desk top {top:.3f} m, keyboard {S['kb_from_front']} m from the front, "
      f"{len(S['props'])} props, rendering {sc.render.resolution_x} x {sc.render.resolution_y}")
bpy.ops.render.render(write_still=True)
print("SAVED", OUT)
