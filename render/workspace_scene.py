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
    """A reception counter, 1.8 x 0.85 m, its worktop at 1.05 m: a white lacquer body,
    an oak-coloured worktop with a 25 mm lip over the front."""
    lacquer = principled("counter lacquer", (0.78, 0.78, 0.76), 0.25, coat=0.3)
    oak = principled("counter oak", (0.36, 0.22, 0.12), 0.45, coat=0.15)
    plinth = principled("counter plinth", (0.05, 0.05, 0.05), 0.6)
    parts = [cube("counter body", (-0.9, -0.40, 0.08), (0.9, 0.42, 1.02), lacquer),
             cube("counter plinth", (-0.88, -0.37, 0.0), (0.88, 0.40, 0.08), plinth),
             cube("counter top", (-0.92, -0.43, 1.02), (0.92, 0.43, 1.05), oak, bevel=0.004)]
    g = bpy.data.objects.new("@counter", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def mouse(spec):
    """A wireless mouse, 64 x 115 mm, 36 mm high at its back and lower over the buttons:
    a sphere cut flat underneath and shaped by its own (unit) coordinates, matte
    graphite, a rubber wheel 3 mm proud of the shell; on a felt pad if pad."""
    shell = principled("mouse shell", (0.03, 0.03, 0.032), 0.45, coat=0.2)
    rubber = principled("mouse wheel", (0.01, 0.01, 0.01), 0.7)
    felt = principled("mouse pad", (0.025, 0.026, 0.03), 0.9)
    L, Wd, Hh = 0.0575, 0.032, 0.036              # half length, half width, height

    def surface(ux, uy, uz):
        """Unit sphere point (z cut at -0.25) to the mouse: +y is the front."""
        h = Hh * (1 - 0.35 * max(0.0, uy))        # lower over the buttons
        w = Wd * (1 - 0.12 * uy)                  # a little narrower at the front
        return ux * w, uy * L, (uz + 0.25) / 1.25 * h

    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1)
    body = bpy.context.active_object
    body.name = "mouse body"
    import bmesh
    b = bmesh.new()
    b.from_mesh(body.data)
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, 0, -0.25),
                           plane_no=(0, 0, 1), clear_inner=True)
    for v in b.verts:
        v.co = surface(*v.co)
    bmesh.ops.edgeloop_fill(b, edges=[e for e in b.edges if e.is_boundary])
    b.to_mesh(body.data)
    b.free()
    body.data.materials.append(shell)
    for p in body.data.polygons:
        p.use_smooth = True
    body.modifiers.new("smooth", "SUBSURF").levels = 1
    uy = 0.42                                     # the wheel, between the buttons
    _, wy, wz = surface(0.0, uy, math.sqrt(1 - uy * uy))
    r = 0.0075
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=0.006)
    wheel = bpy.context.active_object
    wheel.name = "mouse wheel"
    wheel.rotation_euler.y = math.radians(90)
    wheel.location = (0, wy, wz + 0.003 - r)
    wheel.data.materials.append(rubber)
    g = bpy.data.objects.new("mouse", None)
    sc.collection.objects.link(g)
    parts = [body, wheel]
    for o in parts:
        o.parent = g
    if spec.get("pad", True):
        pad = cube("mouse pad", (-0.11, -0.09, -0.003), (0.11, 0.09, 0.0), felt, 0.002)
        pad.parent = g
        parts.append(pad)
    return g, parts


def screen_material(screen, glow):
    """A matte screen whose picture is light: black base colour and an anti-glare coat,
    so the room shows on it only as a soft sheen, and the picture
    (render/textures/workspace/<screen>) as emission."""
    img = bpy.data.images.load(os.path.join(HERE, "textures", "workspace", screen), check_existing=True)
    m = bpy.data.materials.new(f"screen {screen}")
    m.use_nodes = True
    nt2 = m.node_tree
    b = nt2.nodes["Principled BSDF"]
    tex = nt2.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt2.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
    b.inputs["Emission Strength"].default_value = glow
    b.inputs["Roughness"].default_value = 0.4       # an anti-glare coat: the room shows only as a soft sheen
    b.inputs["Specular IOR Level"].default_value = 0.15
    return m


def bent_grid(name, w, h, z0, curve, y_off, mat, nx=64):
    """A w x h sheet in x-z facing the viewer (-y), from z0 to z0 + h, bent about a
    vertical axis `curve` m behind it (None: flat) so its edges come forward; its
    uv spans the sheet."""
    me = bpy.data.meshes.new(name)
    verts, faces, uvs = [], [], []
    for i in range(nx + 1):
        u = i / nx
        x = (u - 0.5) * w
        if curve:
            a = x / curve
            px, py = curve * math.sin(a), y_off - curve * (1 - math.cos(a))
        else:
            px, py = x, y_off
        verts += [(px, py, z0), (px, py, z0 + h)]
        uvs += [(u, 0.0), (u, 1.0)]
    for i in range(nx):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    me.from_pydata(verts, [], faces)
    lay = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        for li in poly.loop_indices:
            lay.data[li].uv = uvs[me.loops[li].vertex_index]
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    return o


def panel(screen, inches, aspect=(16, 9), curve=None, glow=1.6):
    """One display head, its screen's centre at the origin facing -y: the screen, a
    6 mm bezel and 20 mm chin around it (a 14 mm deep shell), a box behind for the
    electronics. Returns (head empty, objects, screen width, screen height)."""
    diag = inches * 0.0254
    sw, sh = diag * aspect[0] / math.hypot(*aspect), diag * aspect[1] / math.hypot(*aspect)
    shell = bpy.data.materials.get("monitor shell") or principled("monitor shell", (0.015, 0.015, 0.017), 0.4)
    head = bpy.data.objects.new("monitor head", None)
    sc.collection.objects.link(head)
    scr = bent_grid("monitor screen", sw, sh, -sh / 2, curve, -0.0008, screen_material(screen, glow))
    frame = bent_grid("monitor frame", sw + 0.012, sh + 0.026, -sh / 2 - 0.02, curve, 0.0072, shell)
    sol = frame.modifiers.new("depth", "SOLIDIFY")
    sol.thickness, sol.offset = 0.015, 0.0
    back = cube("monitor back", (-sw * 0.3, 0.014, -sh * 0.32), (sw * 0.3, 0.042, sh * 0.28), shell, 0.01)
    parts = [scr, frame, back]
    for o in parts:
        o.parent = head
    return head, parts, sw, sh


def monitors(spec):
    """The scene's screens, built facing the viewer (-y) around the origin on the desk
    top (z = 0). spec["style"]:
      stand      one panel on an aluminium neck and a 240 x 180 mm base,
      dual       two panels side by side, each on its stand, turned 12 deg inwards,
      ultrawide  one 34-inch 21:9 panel curved on a 1.5 m radius, a 300 x 200 mm base,
      arm        one panel on an arm from a pole clamped to the desk's back edge (the
                 pole stands `reach` m behind the screen; nothing else on the desk).
    Returns (group, objects, footprints): the footprints are what stands on the desk
    (bases, the pole), for the cables to go round."""
    style = spec.get("style", "stand")
    screens = spec.get("screens") or [spec["screen"]]
    glow = spec.get("glow", 1.6)
    alu = bpy.data.materials.get("monitor aluminium") or principled("monitor aluminium", (0.55, 0.56, 0.58), 0.35)
    alu.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    g = bpy.data.objects.new("monitor", None)
    sc.collection.objects.link(g)
    objs, feet = [], []
    tilt = math.radians(spec.get("tilt", 8))
    lift = spec.get("lift", 0.11)

    def on_stand(screen, inches, aspect, curve, x, turn, base_w=0.24, base_d=0.18):
        st = bpy.data.objects.new("monitor stand", None)
        sc.collection.objects.link(st)
        st.parent = g
        st.location = (x, 0, 0)
        st.rotation_euler.z = math.radians(turn)
        head, parts, sw, sh = panel(screen, inches, aspect, curve, glow)
        zc = lift + 0.02 + sh / 2
        head.parent = st
        head.location = (0, 0.012, zc)
        head.rotation_euler.x = -tilt              # the top leans back
        neck = cube("monitor neck", (-0.03, 0.045, 0.006), (0.03, 0.065, zc + 0.02), alu, 0.004)
        base = cube("monitor base", (-base_w / 2, -base_d / 2 + 0.02, 0.0), (base_w / 2, base_d / 2 + 0.02, 0.006), alu, 0.003)
        for o in (neck, base):
            o.parent = st
        objs.extend(parts + [neck, base])
        feet.append(base)
        return sw

    if style == "stand":
        on_stand(screens[0], spec.get("inches", 27), (16, 9), None, 0.0, 0.0)
    elif style == "dual":
        inches = spec.get("inches", 24)
        sw = inches * 0.0254 * 16 / math.hypot(16, 9)
        gap = sw / 2 + 0.012
        for k, side in enumerate((-1, 1)):
            on_stand(screens[k % len(screens)], inches, (16, 9), None,
                     side * gap * math.cos(math.radians(12)), -side * 12, base_w=0.2, base_d=0.16)
    elif style == "ultrawide":
        on_stand(screens[0], spec.get("inches", 34), (21, 9), 1.5, 0.0, 0.0, base_w=0.30, base_d=0.20)
    elif style == "arm":
        reach = spec.get("reach", 0.24)
        head, parts, sw, sh = panel(screens[0], spec.get("inches", 27), (16, 9), None, glow)
        zc = spec.get("height", 0.32)              # the screen's centre above the desk
        head.parent = g
        head.location = (0, 0.0, zc)
        head.rotation_euler.x = -tilt
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.016, depth=zc + 0.06)
        pole = bpy.context.active_object
        pole.name = "monitor pole"
        pole.location = (0, reach, (zc + 0.06) / 2)
        pole.data.materials.append(alu)
        clamp = cube("monitor clamp", (-0.035, reach - 0.035, -0.07), (0.035, reach + 0.05, 0.012), alu, 0.004)
        jaw = cube("monitor clamp jaw", (-0.03, reach + 0.03, -0.08), (0.03, reach + 0.055, -0.0), alu, 0.003)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.012, depth=reach - 0.03)
        arm = bpy.context.active_object
        arm.name = "monitor arm"
        arm.rotation_euler.x = math.radians(90)
        arm.location = (0, (reach + 0.03) / 2, zc)
        arm.data.materials.append(alu)
        plate = cube("monitor vesa", (-0.05, 0.035, zc - 0.05), (0.05, 0.045, zc + 0.05), alu, 0.003)
        for o in (pole, clamp, jaw, arm, plate):
            o.parent = g
        objs.extend(parts + [pole, clamp, jaw, arm, plate])
        feet.append(clamp)
    return g, objs, feet


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
    lo, hi = box(desk_objs)
    if S.get("desk_height"):
        desk.scale.z = S["desk_height"] / (hi.z - lo.z)
    if S.get("desk_depth"):
        desk.scale.y = S["desk_depth"] / (hi.y - lo.y)
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
# the screens, on the desk, before the host cable: the cable must pass beside what stands
avoid = []
mon = None
if S.get("monitor"):
    spec = S["monitor"]
    mon, mon_objs, feet = monitors(spec)
    if spec.get("style") == "arm":                 # the pole's clamp on the desk's back edge
        mon.location = (spec.get("x", 0.0), dhi.y - spec.get("reach", 0.24) - 0.035, top)
        mon.rotation_euler.z = math.radians(spec.get("turn", 0))
        bpy.context.view_layer.update()
    else:
        place(mon, mon_objs, (spec.get("x", 0.0), kb_y + spec["y"]), spec.get("turn", 0), base_z=top)
        flo, fhi = box(feet)
        if fhi.y > dhi.y - 0.06:                   # every base wholly on the desk, 60 mm inside the back edge
            mon.location.y -= fhi.y - (dhi.y - 0.06)
            print("monitor moved forward to keep its base 60 mm inside the desk's back edge")
    m = 0.02                                       # clearance around each base
    for ft in feet:
        lo2, hi2 = box([ft])
        avoid.append((lo2.x - m, hi2.x + m, lo2.y - m, hi2.y + m))   # world


def crosses(cable, rects, dy=0.0):
    """Does the cable's plan (shifted by dy in y) pass over any of rects (x0, x1, y0, y1)?"""
    return any(x0 < v.co.x < x1 and y0 < v.co.y + dy < y1
               for v in cable.data.vertices for x0, x1, y0, y1 in rects)


def over_edge(name, x, y_edge, z_desk, drop, r, mat, v_scale=None):
    """A cable from the desk top over its back edge (at y_edge) and down `drop` m: a
    quarter turn of 12 mm radius, then straight down."""
    pts = [(x, y_edge - 0.01, z_desk + r)]
    for i in range(1, 13):
        a = math.pi / 2 * i / 12
        pts.append((x, y_edge + 0.012 * math.sin(a), z_desk + r - 0.012 * (1 - math.cos(a))))
    for i in range(1, 9):
        pts.append((x, y_edge + 0.012 + 0.002 * i, z_desk + r - 0.012 - (drop - 0.02) * i / 8))
    return bridge_cable._tube(name, pts, [r] * len(pts), mat, ring=16, v_scale=v_scale)


# the host cable: straight back from the port, then left of the monitor's base if it is
# in the way: swing further left in 30 mm steps until the plan is clear
for drift in [-0.10 - 0.03 * i for i in range(14)]:
    host = bridge_cable.add_host(sc, root_l, halves[0][1], end_y=back_rel - 0.004, drift=drift, turn=0.0)
    if not crosses(host, avoid, dy=kb_y):          # the cable is built in the keyboard's frame
        break
print(f"host cable: drift {drift:+.2f} m", "(clear of the monitor base)" if avoid else "")
# over the back edge and down to the floor
end = max((v.co for v in host.data.vertices), key=lambda c: c.y)
drop = over_edge("host cable drop", end.x, back_rel - 0.004, 0.0, top, bridge_cable.CABLE_R / 1000,
                 host.data.materials[0], v_scale=bridge_cable.BRAID_MM / 1000)
drop["pk_host"] = True

# ---- the keyboard onto the desk top, the props around it ----------------------
kb = bpy.data.objects.new("keyboard", None)
sc.collection.objects.link(kb)
mon_top = [mon] if mon else []
for o in [o for o in sc.objects if o.parent is None and o not in [kb, floor, desk] + mon_top and o.type != "CAMERA"
          and o not in desk_objs and o.name != "target"] + [bpy.data.objects["target"]]:
    mw = o.matrix_world.copy()
    o.parent = kb
    o.matrix_world = mw
kb.location = (0.0, kb_y, top)
bpy.context.view_layer.update()
if S.get("mouse"):
    g, objs = mouse(S["mouse"])
    place(g, objs, (S["mouse"]["x"], kb_y + S["mouse"]["y"]), S["mouse"].get("turn", 0), base_z=top)
    if S["mouse"].get("wired"):
        # its cable from the nose, a little forward, then back across the desk to the
        # back edge, right of whatever stands there, and down over the edge
        nose = g.matrix_world @ mathutils.Vector((0, 0.0575, 0.006))
        fwd = (g.matrix_world.to_3x3() @ mathutils.Vector((0, 1, 0))).normalized()
        xe = nose.x + 0.06
        for x0, x1, y0, y1 in avoid:
            if x0 - 0.03 < xe < x1 + 0.03:
                xe = x1 + 0.03
        ye = dhi.y - 0.004
        c = [nose, nose + fwd * 0.06, mathutils.Vector((xe, ye - 0.16, top)), mathutils.Vector((xe, ye - 0.01, top))]
        rm = 0.0016
        pts = []
        for i in range(120):
            t = i / 119
            p = (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]
            k = min(1.0, (p - nose).length / 0.03)
            pts.append((p.x, p.y, top + rm + (nose.z - top - rm) * (1 - (3 * k * k - 2 * k ** 3))))
        rub = principled("mouse cable", (0.02, 0.02, 0.022), 0.5)
        bridge_cable._tube("mouse cable", pts, [rm] * len(pts), rub, ring=12)
        over_edge("mouse cable drop", xe, ye, top, top, rm, rub)
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
