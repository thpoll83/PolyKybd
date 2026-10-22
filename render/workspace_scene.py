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
S = dict(SCENES[NAME])
if os.environ.get("PK_OVERRIDE"):                 # a JSON dict over the scene's own entry, for look tests
    import json
    S.update(json.loads(os.environ["PK_OVERRIDE"]))
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
        parts_ = part if isinstance(part, (list, tuple)) else [part]      # several parts: one tree's bark and leaves
        keep = [o for o in new if any(o.name.startswith(p_) and (o.name == p_ or not o.name[len(p_):][:1].isalpha())
                                      for p_ in parts_)]
        keep += [c for k in keep for c in k.children_recursive]
        for o in [o for o in new if o not in keep]:
            bpy.data.objects.remove(o)
        new = keep
    tops = [o for o in new if o.parent is None or o.parent not in new]
    g = bpy.data.objects.new(f"{aid}:{part if isinstance(part, str) else 'parts' if part else 'all'}", None)
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
    """A right-hand mouse, 66 x 118 mm, 40 mm high: a sphere cut flat underneath and
    shaped by its own (unit) coordinates, its hump leaning left towards the thumb, in
    spec["color"] (default graphite). Dark seams split the two buttons from each other
    and from the palm rest; a rubber wheel 3 mm proud of the shell; two thumb buttons
    on the left flank; dark grips on both flanks; on a felt pad if pad."""
    shell = principled("mouse shell", spec.get("color", (0.03, 0.03, 0.032)), spec.get("rough", 0.45), coat=spec.get("coat", 0.2))
    shell.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = spec.get("specular", 0.5)
    rubber = principled("mouse wheel", (0.01, 0.01, 0.01), 0.7)
    seam_m = principled("mouse seam", (0.004, 0.004, 0.005), 0.8)
    side_m = principled("mouse side", spec.get("side", (0.02, 0.02, 0.022)), 0.5, coat=0.3)
    felt = principled("mouse pad", (0.025, 0.026, 0.03), 0.9)
    L, Wd, Hh = 0.059, 0.033, 0.040               # half length, half width, height

    def surface(ux, uy, uz):
        """Unit sphere point (z cut at -0.25) to the mouse: +y is the front."""
        h = Hh * (1 - 0.48 * max(0.0, uy) ** 1.3) * (1 - 0.18 * max(0.0, -uy - 0.3))   # hump at the back, low buttons
        w = Wd * (1 - 0.10 * uy) * (1 + 0.06 * ux) * (1 - 0.08 * math.exp(-((uy - 0.05) / 0.3) ** 2))  # a waist
        z = (uz + 0.25) / 1.25
        return ux * w - 0.006 * z * z, uy * L, z * h  # the top leans left, towards the thumb

    def on_top(ux, uy, up=0.0004):
        uz = math.sqrt(max(0.0, 1 - ux * ux - uy * uy))
        x, y, z = surface(ux, uy, uz)
        return mathutils.Vector((x, y, z + up))

    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1)
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
    nt2 = shell.node_tree                         # the grips: shell colour blended to the side colour
    tc = nt2.nodes.new("ShaderNodeTexCoord")      # where |x| > 25 mm and z < 18 mm, soft-edged
    xyz = nt2.nodes.new("ShaderNodeSeparateXYZ")
    nt2.links.new(tc.outputs["Object"], xyz.inputs[0])
    ax = nt2.nodes.new("ShaderNodeMath")
    ax.operation = "ABSOLUTE"
    nt2.links.new(xyz.outputs["X"], ax.inputs[0])
    mx, mz = nt2.nodes.new("ShaderNodeMapRange"), nt2.nodes.new("ShaderNodeMapRange")
    for m_, (a0, a1, src) in ((mx, (0.0235, 0.0255, ax.outputs[0])), (mz, (0.019, 0.017, xyz.outputs["Z"]))):
        m_.interpolation_type = "SMOOTHSTEP"
        m_.inputs["From Min"].default_value, m_.inputs["From Max"].default_value = a0, a1
        nt2.links.new(src, m_.inputs["Value"])
    both = nt2.nodes.new("ShaderNodeMath")
    both.operation = "MULTIPLY"
    nt2.links.new(mx.outputs[0], both.inputs[0])
    nt2.links.new(mz.outputs[0], both.inputs[1])
    mix = nt2.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt2.links.new(both.outputs[0], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*spec.get("color", (0.03, 0.03, 0.032)), 1)
    mix.inputs[7].default_value = (*spec.get("side", (0.02, 0.02, 0.022)), 1)
    bsdf = nt2.nodes["Principled BSDF"]
    nt2.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    body.data.materials.append(shell)
    for p in body.data.polygons:
        p.use_smooth = True
    body.modifiers.new("smooth", "SUBSURF").levels = 1

    def strip(name, pts, width):
        """A dark seam along pts on the shell, width wide."""
        me = bpy.data.meshes.new(name)
        verts = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            n = t.cross(mathutils.Vector((0, 0, 1)))
            if n.length < 1e-6:
                n = mathutils.Vector((1, 0, 0))
            n.normalize()
            verts += [p - n * width / 2, p + n * width / 2]
        me.from_pydata(verts, [], [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(pts) - 1)])
        me.materials.append(seam_m)
        o = bpy.data.objects.new(name, me)
        sc.collection.objects.link(o)
        return o

    seams = [strip("mouse seam middle", [on_top(0.0, 0.18 + 0.8 * i / 30, 0.0008) for i in range(31)], 0.0012),
             strip("mouse seam back", [on_top(-0.86 + 1.72 * i / 40, 0.18, 0.0008) for i in range(41)], 0.0012)]
    uy = 0.40                                     # the wheel, between the buttons
    _, wy, wz = surface(0.0, uy, math.sqrt(1 - uy * uy))
    r = 0.0075
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=0.0065)
    wheel = bpy.context.active_object
    wheel.name = "mouse wheel"
    wheel.rotation_euler.y = math.radians(90)
    wheel.location = (on_top(0.0, uy).x, wy, wz + 0.003 - r)
    wheel.data.materials.append(rubber)
    thumbs = []
    for k, (y0, y1) in enumerate(((-0.004, 0.012), (0.015, 0.030))):  # thumb buttons on the left flank
        x, _, z = surface(-0.97, 0.0, math.sqrt(1 - 0.97 ** 2))
        o = cube(f"mouse thumb button {k}", (x - 0.0012, y0, 0.017), (x + 0.002, y1, 0.0205), side_m, 0.0012)
        thumbs.append(o)
    g = bpy.data.objects.new("mouse", None)
    sc.collection.objects.link(g)
    parts = [body, wheel] + seams + thumbs
    for o in parts:
        o.parent = g
    if spec.get("pad", True):
        pad = cube("mouse pad", (-0.11, -0.09, -0.003), (0.11, 0.09, 0.0), felt, 0.002)
        pad.parent = g
        parts.append(pad)
    return g, parts


def tablet():
    """A pen tablet, 320 x 210 x 8 mm: a black slate with a matte active area and its
    pen lying across it."""
    slate = principled("tablet slate", (0.012, 0.012, 0.014), 0.35, coat=0.3)
    area = principled("tablet area", (0.03, 0.03, 0.034), 0.7)
    pen_m = principled("tablet pen", (0.02, 0.02, 0.022), 0.3)
    parts = [cube("tablet", (-0.16, -0.105, 0.0), (0.16, 0.105, 0.008), slate, 0.004),
             cube("tablet area", (-0.13, -0.085, 0.008), (0.14, 0.085, 0.0084), area, 0.0005)]
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0055, depth=0.155)
    pen = bpy.context.active_object
    pen.name = "tablet pen"
    pen.rotation_euler = (0, math.radians(90), math.radians(28))
    pen.location = (0.02, -0.02, 0.0084 + 0.0055)
    pen.data.materials.append(pen_m)
    parts.append(pen)
    g = bpy.data.objects.new("@tablet", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def black_desk():
    """A gaming desk, 1.6 x 0.8 m, top at 0.75 m: a black 25 mm top on a black steel
    frame with two T legs."""
    top_m = principled("desk black top", (0.018, 0.018, 0.02), 0.5, coat=0.1)
    steel = principled("desk black steel", (0.03, 0.03, 0.032), 0.4)
    steel.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
    parts = [cube("desk top", (-0.8, -0.4, 0.725), (0.8, 0.4, 0.75), top_m, 0.004)]
    for sx in (-1, 1):
        x = sx * 0.68
        parts += [cube("desk leg", (x - 0.03, -0.03, 0.04), (x + 0.03, 0.03, 0.725), steel, 0.004),
                  cube("desk foot", (x - 0.035, -0.36, 0.0), (x + 0.035, 0.36, 0.04), steel, 0.004)]
    parts.append(cube("desk rail", (-0.68, -0.025, 0.66), (0.68, 0.025, 0.71), steel, 0.004))
    g = bpy.data.objects.new("@black_desk", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def desk_mat(spec):
    """An extended desk mat under keyboard and mouse, 3 mm thick, in spec["color"] at
    spec["rough"] (felt 0.9, leather about 0.45) or printed with spec["image"], with a light strip around its edge
    glowing spec["glow"] if given (an RGB gamer's mat)."""
    if spec.get("image"):                          # a printed mat: render/textures/workspace/<image> on its top
        felt = image_material("desk mat", spec["image"], rough=spec.get("rough", 0.9))
    else:
        felt = principled("desk mat", spec.get("color", (0.02, 0.02, 0.024)), spec.get("rough", 0.9),
                          coat=spec.get("coat", 0.0))
    w, d, t = spec.get("w", 0.9), spec.get("d", 0.38), 0.003
    parts = [cube("desk mat", (-w / 2, -d / 2, 0.0), (w / 2, d / 2, t), felt, 0.002)]
    if spec.get("image"):                          # the print spans the top: uv from plan position
        me = parts[0].data
        lay = me.uv_layers.active
        for poly in me.polygons:
            for li, vi in zip(poly.loop_indices, poly.vertices):
                co = me.vertices[vi].co
                lay.data[li].uv = ((co.x + w / 2) / w, (co.y + d / 2) / d)
    if spec.get("glow"):
        lit = bpy.data.materials.new("desk mat glow")
        lit.use_nodes = True
        b = lit.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Color"].default_value = (*spec["glow"], 1)
        b.inputs["Emission Strength"].default_value = spec.get("strength", 6.0)
        e = 0.004
        parts += [cube("mat glow", (-w / 2, -d / 2 - e, 0.0), (w / 2, -d / 2, t * 0.9), lit, 0.0008),
                  cube("mat glow", (-w / 2, d / 2, 0.0), (w / 2, d / 2 + e, t * 0.9), lit, 0.0008),
                  cube("mat glow", (-w / 2 - e, -d / 2 - e, 0.0), (-w / 2, d / 2 + e, t * 0.9), lit, 0.0008),
                  cube("mat glow", (w / 2, -d / 2 - e, 0.0), (w / 2 + e, d / 2 + e, t * 0.9), lit, 0.0008)]
    g = bpy.data.objects.new("desk mat", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts, t


def image_material(name, image, rough=0.4, metal=0.0, tint=None):
    """A material showing render/textures/workspace/<image> as its colour."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt2 = m.node_tree
    b = nt2.nodes["Principled BSDF"]
    tex = nt2.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(HERE, "textures", "workspace", image), check_existing=True)
    nt2.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def uv_plane(name, lo, hi, z, mat):
    """A horizontal quad from lo to hi (x, y) at height z, its uv the whole image."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(lo[0], lo[1], z), (hi[0], lo[1], z), (hi[0], hi[1], z), (lo[0], hi[1], z)], [], [(0, 1, 2, 3)])
    lay = me.uv_layers.new(name="uv")
    for li, uv in zip(me.polygons[0].loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        lay.data[li].uv = uv
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    return o


def ruler():
    """A 300 mm steel rule, 28 mm wide and 1 mm thick, its scale on the top face."""
    steel = principled("ruler steel", (0.62, 0.63, 0.65), 0.3)
    steel.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    face = image_material("ruler face", "ruler.jpg", rough=0.32, metal=1.0)
    parts = [cube("ruler", (-0.155, -0.014, 0.0), (0.155, 0.014, 0.001), steel, 0.0003),
             uv_plane("ruler scale", (-0.155, -0.014), (0.155, 0.014), 0.00102, face)]
    g = bpy.data.objects.new("@ruler", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def set_square():
    """A 45 deg set square, 200 mm legs, 2.5 mm clear acrylic tinted green, with the
    triangular cut-out inside."""
    import bmesh
    acr = principled("set square", (0.75, 0.95, 0.85), 0.05)
    b = acr.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.49
    L, Li, t = 0.20, 0.11, 0.0025
    bm = bmesh.new()
    outer = [bm.verts.new(p) for p in ((0, 0, 0), (L, 0, 0), (0, L, 0))]
    off = 0.025
    inner = [bm.verts.new(p) for p in ((off, off, 0), (off + Li, off, 0), (off, off + Li, 0))]
    for i in range(3):                              # the band between the two triangles
        j = (i + 1) % 3
        bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
    ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    bmesh.ops.translate(bm, verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)], vec=(0, 0, t))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("set square")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(acr)
    o = bpy.data.objects.new("set square", me)
    sc.collection.objects.link(o)
    g = bpy.data.objects.new("@set_square", None)
    sc.collection.objects.link(g)
    o.parent = g
    return g, [o]


def mug(glaze=(0.85, 0.84, 0.80)):
    """A ceramic coffee mug, 82 mm across, 95 mm tall, 4 mm wall, coffee 20 mm below
    the rim, a D handle; glazed glaze."""
    import bmesh
    cer = principled(f"mug glaze {glaze}", glaze, 0.18, coat=0.4)
    cof = principled("coffee", (0.06, 0.025, 0.01), 0.05, coat=0.0)
    R, r, H = 0.041, 0.037, 0.095
    bm = bmesh.new()
    n = 48
    rings = []
    for (rad, z) in ((R * 0.94, 0.0), (R, 0.004), (R, H), (r, H), (r, 0.008), (0.0, 0.008)):
        rings.append([bm.verts.new((rad * math.cos(2 * math.pi * i / n), rad * math.sin(2 * math.pi * i / n), z))
                      for i in range(n)])
    for a, c in zip(rings, rings[1:]):                 # the lathe: base edge, wall, rim, inside, floor
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], c[j], c[i]))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("mug")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(cer)
    for p in me.polygons:
        p.use_smooth = True
    body = bpy.data.objects.new("mug", me)
    sc.collection.objects.link(body)
    body.modifiers.new("smooth", "SUBSURF").levels = 1
    pts = [(R - 0.002 + 0.024 * math.sin(math.pi * t), 0.0, 0.022 + 0.055 * t) for t in [i / 24 for i in range(25)]]
    handle = bridge_cable._tube("mug handle", pts, [0.0055] * len(pts), cer, ring=16)
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=r - 0.0004, fill_type="NGON", location=(0, 0, H - 0.02))
    coffee = bpy.context.active_object
    coffee.name = "coffee"
    coffee.data.materials.append(cof)
    g = bpy.data.objects.new("@mug", None)
    sc.collection.objects.link(g)
    for o in (body, handle, coffee):
        o.parent = g
    return g, [body, handle, coffee]


def puzzle_cube(seed=5):
    """A 57 mm puzzle cube, scrambled: a black body with 9 stickers a face, 16 mm
    squares 0.6 mm proud, in the six usual colours drawn at random (seeded)."""
    import random
    rnd = random.Random(seed)
    body_m = principled("cube body", (0.01, 0.01, 0.011), 0.35)
    cols = [(0.9, 0.9, 0.88), (0.95, 0.80, 0.05), (0.75, 0.05, 0.04), (0.95, 0.35, 0.02), (0.02, 0.20, 0.75), (0.02, 0.55, 0.15)]
    mats = [principled(f"cube sticker {i}", c, 0.25, coat=0.3) for i, c in enumerate(cols)]
    a, st, pitch = 0.0285, 0.0080, 0.019
    parts = [cube("puzzle cube", (-a, -a, 0.0), (a, a, 2 * a), body_m, 0.003)]
    for axis in range(3):
        for sign in (-1, 1):
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    c = [0.0, 0.0, a]
                    u, v = [k for k in range(3) if k != axis]
                    c[axis] += sign * (a + 0.0003)
                    c[u] += i * pitch
                    c[v] += j * pitch
                    lo, hi = list(c), list(c)
                    for k in (u, v):
                        lo[k] -= st
                        hi[k] += st
                    lo[axis] -= 0.0003
                    hi[axis] += 0.0003
                    parts.append(cube("sticker", lo, hi, rnd.choice(mats), 0.0012))
    g = bpy.data.objects.new("@puzzle_cube", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def paper_clips():
    """Three 32 mm gem clips, 0.9 mm steel wire, scattered at angles."""
    steel = principled("clip steel", (0.7, 0.71, 0.73), 0.25)
    steel.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0

    def clip_path():
        pts = []

        def line(a, b, n=6):
            for k in range(n):
                t = k / n
                pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))

        def arc(cx, cy, rr, a0, a1, n=10):
            for k in range(n):
                t = a0 + (a1 - a0) * k / n
                pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
        line((0.0, 0.006), (0.0, 0.026))
        arc(0.004, 0.026, 0.004, math.pi, 0.0)
        line((0.008, 0.026), (0.008, 0.003))
        arc(0.0045, 0.003, 0.0035, 0.0, -math.pi)
        line((0.001, 0.003), (0.001, 0.022))
        arc(0.0035, 0.022, 0.0025, math.pi, 0.0)
        line((0.006, 0.022), (0.006, 0.008))
        pts.append((0.006, 0.008))
        return pts
    parts = []
    for k, (dx, dy, turn) in enumerate(((0.0, 0.0, 20), (0.028, 0.012, -35), (0.012, 0.034, 70))):
        c, s_ = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        pts = [(dx + x * c - y * s_, dy + x * s_ + y * c, 0.00045) for x, y in clip_path()]
        parts.append(bridge_cable._tube(f"paper clip {k}", pts, [0.00045] * len(pts), steel, ring=8))
    g = bpy.data.objects.new("@clips", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def tint(objs, rgb, mode="MULTIPLY", f=1.0):
    """Multiply every material of objs (copies) by rgb: the yellow pad made ivory.
    mode="MIX" with f < 1 blends towards rgb instead: the grey desk made whiter."""
    done = {}
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            m = slot.material
            if m is None:
                continue
            if m.name not in done:
                c = m.copy()
                nt2 = c.node_tree
                b = next((n for n in nt2.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
                if b is not None:
                    inp = b.inputs["Base Color"]
                    mix = nt2.nodes.new("ShaderNodeMix")
                    mix.data_type = "RGBA"
                    mix.blend_type = mode
                    mix.inputs["Factor"].default_value = f
                    mix.inputs[7].default_value = (*rgb, 1)
                    if inp.is_linked:
                        nt2.links.new(inp.links[0].from_socket, mix.inputs[6])
                    else:
                        mix.inputs[6].default_value = inp.default_value
                    nt2.links.new(mix.outputs[2], inp)
                done[m.name] = c
            slot.material = done[m.name]


def usb_hub():
    """A four-port USB hub, 100 x 30 x 12 mm: an aluminium bar with a dark top, its
    ports on the front (-y), a blue power light, its cable leaving at the back (+y,
    the "cable" option of the prop draws it)."""
    alu = principled("hub body", (0.62, 0.63, 0.65), 0.3)
    alu.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    top = principled("hub top", (0.01, 0.01, 0.012), 0.15, coat=0.6)
    port = principled("hub port", (0.005, 0.005, 0.006), 0.6)
    tongue = principled("hub port tongue", (0.02, 0.15, 0.6), 0.4)
    led = bpy.data.materials.new("hub light")
    led.use_nodes = True
    lb = led.node_tree.nodes["Principled BSDF"]
    lb.inputs["Emission Color"].default_value = (0.1, 0.35, 1.0, 1)
    lb.inputs["Emission Strength"].default_value = 25.0
    parts = [cube("usb hub", (-0.05, -0.015, 0.0), (0.05, 0.015, 0.012), alu, 0.003),
             cube("hub top", (-0.047, -0.012, 0.0115), (0.047, 0.012, 0.0122), top, 0.001),
             cube("hub light", (0.040, -0.0153, 0.0055), (0.042, -0.0149, 0.0065), led, 0.0002)]
    for i in range(4):
        x = -0.034 + i * 0.020
        parts.append(cube("hub port", (x - 0.006, -0.0152, 0.0038), (x + 0.006, -0.0135, 0.0083), port, 0.0004))
        parts.append(cube("hub port tongue", (x - 0.005, -0.0150, 0.0050), (x + 0.005, -0.0138, 0.0068), tongue, 0.0002))
    g = bpy.data.objects.new("@usb_hub", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    g["pk_cable_at"] = (0.0, 0.015, 0.006)       # where its cable leaves, in its own frame
    return g, parts


def newtons_cradle():
    """A Newton's cradle, 180 x 110 x 150 mm: a black base, two steel frames, five
    19 mm steel balls each hung on a V of two threads; the left ball pulled out 35 deg."""
    steel = principled("cradle steel", (0.85, 0.86, 0.88), 0.08)
    steel.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    base_m = principled("cradle base", (0.015, 0.015, 0.016), 0.3, coat=0.5)
    thread = principled("cradle thread", (0.8, 0.8, 0.78), 0.6)
    parts = [cube("cradle base", (-0.09, -0.055, 0.0), (0.09, 0.055, 0.016), base_m, 0.004)]
    H, X, Y, rr = 0.15, 0.075, 0.04, 0.0022

    def rod(name, a, b, r, mat):
        a, b = mathutils.Vector(a), mathutils.Vector(b)
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=(b - a).length, location=(a + b) / 2)
        o = bpy.context.active_object
        o.name = name
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = (b - a).to_track_quat("Z", "Y")
        o.data.materials.append(mat)
        for p in o.data.polygons:
            p.use_smooth = True
        return o

    for y in (-Y, Y):                              # each frame: two posts and a top bar
        parts += [rod("cradle post", (-X, y, 0.016), (-X, y, H), rr, steel),
                  rod("cradle post", (X, y, 0.016), (X, y, H), rr, steel),
                  rod("cradle bar", (-X, y, H), (X, y, H), rr, steel)]
    R_, zc = 0.0095, 0.050
    for i in range(5):
        x = (i - 2) * 2 * R_ * 1.01
        pivot = mathutils.Vector((x, 0, H))
        ang = math.radians(-35) if i == 0 else 0.0
        rot = mathutils.Matrix.Rotation(ang, 3, "Y")
        c = pivot + rot @ (mathutils.Vector((x, 0, zc)) - pivot)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=R_, location=c)
        ball = bpy.context.active_object
        ball.name = "cradle ball"
        ball.data.materials.append(steel)
        for p in ball.data.polygons:
            p.use_smooth = True
        parts.append(ball)
        top_ball = c + mathutils.Vector((0, 0, R_ * 0.9))
        for y in (-Y, Y):
            parts.append(rod("cradle thread", (x, y, H), top_ball, 0.0003, thread))
    g = bpy.data.objects.new("@newtons_cradle", None)
    sc.collection.objects.link(g)
    for o in parts:
        o.parent = g
    return g, parts


def pot_soil(r=0.074):
    """Potting soil for a plant set in a pot: a dark, rough disc r m across, 10 mm thick."""
    soil = principled("pot soil", (0.035, 0.025, 0.018), 1.0)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=0.01, location=(0, 0, 0.005))
    o = bpy.context.active_object
    o.name = "pot soil"
    o.data.materials.append(soil)
    g = bpy.data.objects.new("@pot_soil", None)
    sc.collection.objects.link(g)
    o.parent = g
    return g, [o]


def spots(objs, amount):
    """Faint spots on a surface (objs' materials, copies): where a large noise rises past
    a threshold the colour darkens a few per cent, soft-edged, here and there."""
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if slot.material is None:
                continue
            m = slot.material.copy()
            nt2 = m.node_tree
            b = next((n for n in nt2.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
            if b is None:
                continue
            tc = nt2.nodes.new("ShaderNodeTexCoord")
            nz = nt2.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9.0
            nz.inputs["Detail"].default_value = 2.0
            nt2.links.new(tc.outputs["Object"], nz.inputs["Vector"])
            mr = nt2.nodes.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
            mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.60, 0.70
            mr.inputs["To Max"].default_value = amount
            nt2.links.new(nz.outputs["Fac"], mr.inputs["Value"])
            mix = nt2.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            nt2.links.new(mr.outputs[0], mix.inputs["Factor"])
            mix.inputs[7].default_value = (0.86, 0.83, 0.78, 1)
            inp = b.inputs["Base Color"]
            if inp.is_linked:
                nt2.links.new(inp.links[0].from_socket, mix.inputs[6])
            else:
                mix.inputs[6].default_value = inp.default_value
            nt2.links.new(mix.outputs[2], inp)
            slot.material = m


def grime(objs, amount, band=None, axes=("X", "Y")):
    """Handled edges on objs' materials (copies): the colour darkens towards the
    bounding box's sides, over the outer 8 %, broken up by noise. band=(axis, lo, hi)
    instead darkens where fingers hold a pen: from lo to hi of its length along axis
    (of the bounding box, 0..1), soft at both ends."""
    for o in objs:
        if o.type != "MESH":
            continue
        for slot in o.material_slots:
            if slot.material is None:
                continue
            m = slot.material.copy()
            nt2 = m.node_tree
            b = next((n for n in nt2.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
            if b is None:
                continue
            tc = nt2.nodes.new("ShaderNodeTexCoord")
            sep = nt2.nodes.new("ShaderNodeSeparateXYZ")
            nt2.links.new(tc.outputs["Generated"], sep.inputs[0])
            if band:
                ax, b0, b1 = band
                if ax == "auto":                    # the long axis, measured from the tip (the thin end)
                    vs = [v.co for v in o.data.vertices]
                    ext = [max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3)]
                    k = ext.index(max(ext))
                    ax = "XYZ"[k]
                    lo_k, hi_k = min(v[k] for v in vs), max(v[k] for v in vs)
                    others = [i for i in range(3) if i != k]
                    def spread(sel):
                        return sum(max(v[i] for v in sel) - min(v[i] for v in sel) for i in others) if sel else 0
                    near_lo = [v for v in vs if v[k] < lo_k + 0.06 * (hi_k - lo_k)]
                    near_hi = [v for v in vs if v[k] > hi_k - 0.06 * (hi_k - lo_k)]
                    if spread(near_hi) < spread(near_lo):
                        b0, b1 = 1 - b1, 1 - b0
                up = nt2.nodes.new("ShaderNodeMapRange"); up.interpolation_type = "SMOOTHSTEP"
                up.inputs["From Min"].default_value, up.inputs["From Max"].default_value = b0, b0 + 0.06
                dn = nt2.nodes.new("ShaderNodeMapRange"); dn.interpolation_type = "SMOOTHSTEP"
                dn.inputs["From Min"].default_value, dn.inputs["From Max"].default_value = b1, b1 - 0.06
                for mr_ in (up, dn):
                    nt2.links.new(sep.outputs[ax], mr_.inputs["Value"])
                bandm = nt2.nodes.new("ShaderNodeMath"); bandm.operation = "MULTIPLY"
                nt2.links.new(up.outputs[0], bandm.inputs[0]); nt2.links.new(dn.outputs[0], bandm.inputs[1])
            edge = None
            for axis in axes:
                lo_ = nt2.nodes.new("ShaderNodeMath"); lo_.operation = "PINGPONG"; lo_.inputs[1].default_value = 0.5
                nt2.links.new(sep.outputs[axis], lo_.inputs[0])     # distance to the nearer side, 0..0.5
                edge = lo_ if edge is None else edge
                if axis == axes[1]:
                    mn = nt2.nodes.new("ShaderNodeMath"); mn.operation = "MINIMUM"
                    nt2.links.new(prev.outputs[0], mn.inputs[0]); nt2.links.new(lo_.outputs[0], mn.inputs[1])
                    edge = mn
                prev = lo_
            mr = nt2.nodes.new("ShaderNodeMapRange")
            mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = 0.0, 0.08
            mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
            nt2.links.new(edge.outputs[0], mr.inputs["Value"])
            src = bandm if band else mr
            nz = nt2.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18.0; nz.inputs["Detail"].default_value = 6.0
            nt2.links.new(tc.outputs["Generated"], nz.inputs["Vector"])
            mul = nt2.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
            nzr = nt2.nodes.new("ShaderNodeMapRange")     # noise 0.3..0.7 to 0.25..1: patchy, never absent
            nzr.inputs["From Min"].default_value, nzr.inputs["From Max"].default_value = 0.3, 0.7
            nzr.inputs["To Min"].default_value = 0.25
            nt2.links.new(nz.outputs["Fac"], nzr.inputs["Value"])
            nt2.links.new(src.outputs[0], mul.inputs[0]); nt2.links.new(nzr.outputs[0], mul.inputs[1])
            mix = nt2.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            fac = nt2.nodes.new("ShaderNodeMath"); fac.operation = "MULTIPLY"
            fac.inputs[1].default_value = amount * (2.4 if band else 1.6)
            fac.use_clamp = True
            nt2.links.new(mul.outputs[0], fac.inputs[0]); nt2.links.new(fac.outputs[0], mix.inputs["Factor"])
            mix.inputs[7].default_value = (0.32, 0.27, 0.22, 1) if band else (0.55, 0.47, 0.38, 1)
            inp = b.inputs["Base Color"]
            if inp.is_linked:
                nt2.links.new(inp.links[0].from_socket, mix.inputs[6])
            else:
                mix.inputs[6].default_value = inp.default_value
            nt2.links.new(mix.outputs[2], inp)
            slot.material = m


BUILT = {"@puzzle_cube": lambda: puzzle_cube(), "@pot_soil": lambda: pot_soil(), "@usb_hub": lambda: usb_hub(),
         "@newtons_cradle": lambda: newtons_cradle(), "@clips": lambda: paper_clips(),
"@tablet": lambda: tablet(), "@ruler": lambda: ruler(), "@set_square": lambda: set_square(),
         "@mug": lambda: mug(), "@mug_dark": lambda: mug((0.05, 0.05, 0.055))}


def wall_texture(tx):
    """A wall material from a Poly Haven texture (workspace_assets.fetch_texture): colour,
    GL normal and roughness, laid over the wall's face (x, z) one tile per tx["tile"] m,
    its colour multiplied by tx["tint"]."""
    folder = os.path.join(ASSETS, tx["id"])
    m = bpy.data.materials.new(f"wall {tx['id']}")
    m.use_nodes = True
    nt2 = m.node_tree
    b = nt2.nodes["Principled BSDF"]
    tc = nt2.nodes.new("ShaderNodeTexCoord")
    sep = nt2.nodes.new("ShaderNodeSeparateXYZ")
    nt2.links.new(tc.outputs["Object"], sep.inputs[0])
    comb = nt2.nodes.new("ShaderNodeCombineXYZ")
    for src_, dst in (("X", "X"), ("Z", "Y")):
        mm = nt2.nodes.new("ShaderNodeMath"); mm.operation = "DIVIDE"; mm.inputs[1].default_value = tx.get("tile", 2.0)
        nt2.links.new(sep.outputs[src_], mm.inputs[0])
        nt2.links.new(mm.outputs[0], comb.inputs[dst])

    def tex(kind, colour):
        t = nt2.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(folder, f"{tx['id']}_{kind}_2k.jpg"), check_existing=True)
        if not colour:
            t.image.colorspace_settings.name = "Non-Color"
        nt2.links.new(comb.outputs[0], t.inputs["Vector"])
        return t
    diff = tex("diff", True)
    mix = nt2.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt2.links.new(diff.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (*tx.get("tint", (1.0, 1.0, 1.0)), 1)
    nt2.links.new(mix.outputs[2], b.inputs["Base Color"])
    nm = nt2.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = tx.get("bump", 1.0)
    nt2.links.new(tex("nor_gl", False).outputs["Color"], nm.inputs["Color"])
    nt2.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    nt2.links.new(tex("rough", False).outputs["Color"], b.inputs["Roughness"])
    return m


def wall(spec, y_wall, x_mid, top):
    """A painted wall behind the desk at y_wall: 3.6 x 2.6 m with a 60 mm skirting; an
    LED strip on it behind the screen (bias light, it lights the wall); a framed poster.
    Real geometry, so it takes the room's light and throws the strip's back onto the
    desk, which an HDRI behind the desk cannot."""
    paint = principled("wall paint", spec.get("color", (0.05, 0.055, 0.07)), 0.85)
    pn = paint.node_tree                          # rolled plaster: a fine bump and a faint blotchy tone
    tcw = pn.nodes.new("ShaderNodeTexCoord")
    nzw = pn.nodes.new("ShaderNodeTexNoise"); nzw.inputs["Scale"].default_value = 90.0; nzw.inputs["Detail"].default_value = 8.0
    pn.links.new(tcw.outputs["Object"], nzw.inputs["Vector"])
    bmp = pn.nodes.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.08
    pn.links.new(nzw.outputs["Fac"], bmp.inputs["Height"])
    pn.links.new(bmp.outputs["Normal"], pn.nodes["Principled BSDF"].inputs["Normal"])
    nzc = pn.nodes.new("ShaderNodeTexNoise"); nzc.inputs["Scale"].default_value = 2.5
    pn.links.new(tcw.outputs["Object"], nzc.inputs["Vector"])
    tone = pn.nodes.new("ShaderNodeMapRange")
    tone.inputs["To Min"].default_value, tone.inputs["To Max"].default_value = 0.93, 1.03
    pn.links.new(nzc.outputs["Fac"], tone.inputs["Value"])
    mulw = pn.nodes.new("ShaderNodeMix"); mulw.data_type = "RGBA"; mulw.blend_type = "MULTIPLY"
    mulw.inputs["Factor"].default_value = 1.0
    mulw.inputs[6].default_value = (*spec.get("color", (0.05, 0.055, 0.07)), 1)
    pn.links.new(tone.outputs[0], mulw.inputs[7])
    pn.links.new(mulw.outputs[2], pn.nodes["Principled BSDF"].inputs["Base Color"])
    skirt = principled("wall skirting", (0.03, 0.03, 0.035), 0.5)
    if spec.get("texture"):                       # a Poly Haven wall texture instead of the paint
        paint = wall_texture(spec["texture"])
    parts = [cube("wall", (x_mid - 1.8, y_wall, 0.0), (x_mid + 1.8, y_wall + 0.1, 2.6), paint, 0.0),
             cube("wall skirting", (x_mid - 1.8, y_wall - 0.012, 0.0), (x_mid + 1.8, y_wall, 0.06), skirt, 0.002)]
    if spec.get("led"):
        lit = bpy.data.materials.new("led strip")
        lit.use_nodes = True
        b = lit.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Color"].default_value = (*spec["led"], 1)
        b.inputs["Emission Strength"].default_value = spec.get("led_strength", 30.0)
        zl = top + spec.get("led_z", 0.62)
        w = spec.get("led_w", 1.2)
        parts.append(cube("led strip", (x_mid - w / 2, y_wall - 0.006, zl), (x_mid + w / 2, y_wall, zl + 0.008), lit, 0.001))
    if spec.get("poster"):
        px, pz, pw = spec.get("poster_x", -0.85), top + spec.get("poster_z", 0.5), spec.get("poster_w", 0.5)
        ph = pw * 1440 / 1120
        frame = principled("poster frame", (0.015, 0.015, 0.017), 0.4)
        art = image_material("poster", spec["poster"], rough=0.5)
        parts.append(cube("poster frame", (x_mid + px - pw / 2 - 0.02, y_wall - 0.02, pz - 0.02),
                          (x_mid + px + pw / 2 + 0.02, y_wall, pz + ph + 0.02), frame, 0.003))
        me = bpy.data.meshes.new("poster")
        y = y_wall - 0.0205
        me.from_pydata([(x_mid + px - pw / 2, y, pz), (x_mid + px + pw / 2, y, pz),
                        (x_mid + px + pw / 2, y, pz + ph), (x_mid + px - pw / 2, y, pz + ph)], [], [(0, 1, 2, 3)])
        lay = me.uv_layers.new(name="uv")
        for li, uv in zip(me.polygons[0].loop_indices, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            lay.data[li].uv = uv
        me.materials.append(art)
        po = bpy.data.objects.new("poster", me)
        sc.collection.objects.link(po)
        parts.append(po)
    for it in spec.get("items", []):
        parts += wall_item(it, y_wall, top)
    return parts


def sheet(name, img, px, pz, w, h, y, rot, bow, mat_rough=0.75, ny=10):
    """A sheet hanging from a pin at (px, pz) on a surface at y: w x h, turned rot deg in
    the wall's plane, its lower part curling bow m off the surface towards the viewer."""
    me = bpy.data.meshes.new(name)
    a = math.radians(rot)
    verts, uvs = [], []
    for j in range(ny + 1):
        v = j / ny                                         # 0 at the bottom, 1 at the top
        for u in (0.0, 1.0):
            lx, lz = (u - 0.5) * w, (v - 1.0) * h + 0.012  # the pin 12 mm below the top edge
            verts.append((px + lx * math.cos(a) - lz * math.sin(a), y - bow * (1 - v) ** 2,
                          pz + lx * math.sin(a) + lz * math.cos(a)))
            uvs.append((u, v))
    faces = [(2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2) for j in range(ny)]
    me.from_pydata(verts, [], faces)
    lay = me.uv_layers.new(name="uv")
    for f in me.polygons:
        for li, vi in zip(f.loop_indices, f.vertices):
            lay.data[li].uv = uvs[vi]
    me.materials.append(image_material(name, img, rough=mat_rough))
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    sol = o.modifiers.new("thickness", "SOLIDIFY")
    sol.thickness, sol.offset = 0.0003, 1.0
    return o


def wood(name, rgb, rough=0.5, grain=40.0):
    """Wood that has been used: a barely visible grain (a wave texture along x) and a few
    small shallow dents (the centres of large Voronoi cells, pressed in)."""
    m = principled(name, rgb, rough)
    nt2 = m.node_tree
    b = nt2.nodes["Principled BSDF"]
    tc = nt2.nodes.new("ShaderNodeTexCoord")
    wv = nt2.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = grain
    wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 3.0
    nt2.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    tone = nt2.nodes.new("ShaderNodeMapRange")
    tone.inputs["To Min"].default_value, tone.inputs["To Max"].default_value = 0.97, 1.01
    nt2.links.new(wv.outputs["Fac"], tone.inputs["Value"])
    mix = nt2.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs[6].default_value = (*rgb, 1)
    nt2.links.new(tone.outputs[0], mix.inputs[7])
    nt2.links.new(mix.outputs[2], b.inputs["Base Color"])
    vo = nt2.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 8.0
    nt2.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    dent = nt2.nodes.new("ShaderNodeMapRange")    # only the cells' centres: a sparse set of shallow dents
    dent.inputs["From Min"].default_value, dent.inputs["From Max"].default_value = 0.0, 0.05
    dent.inputs["To Min"].default_value, dent.inputs["To Max"].default_value = 0.0, 1.0
    nt2.links.new(vo.outputs["Distance"], dent.inputs["Value"])
    sk = nt2.nodes.new("ShaderNodeTexNoise"); sk.inputs["Scale"].default_value = 300.0
    nt2.links.new(tc.outputs["Object"], sk.inputs["Vector"])
    add = nt2.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = 0.0
    nt2.links.new(sk.outputs["Fac"], add.inputs[0]); nt2.links.new(dent.outputs[0], add.inputs[2])
    bm = nt2.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.15
    nt2.links.new(add.outputs[0], bm.inputs["Height"])
    nt2.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    return m


def lying_pin(name, x, y, z, rgb, turn):
    """A push pin lying on its side on a shelf: its head and its steel point."""
    head = principled(name, rgb, 0.25, coat=0.6)
    steel = principled("pin steel", (0.8, 0.8, 0.82), 0.2)
    steel.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    a = math.radians(turn)
    out = []
    for r, ln, off, mat in ((0.0045, 0.006, 0.0, head), (0.0004, 0.009, 0.0075, steel)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=ln,
                                            location=(x + off * math.cos(a), y + off * math.sin(a), z + 0.0045),
                                            rotation=(0, math.radians(90), a))
        o = bpy.context.active_object
        o.name = name
        o.data.materials.append(mat)
        out.append(o)
    return out


def pin(name, x, y, z, rgb):
    """A push pin: a glossy plastic head standing 6 mm off the surface."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.0045, depth=0.006, location=(x, y - 0.003, z),
                                        rotation=(math.pi / 2, 0, 0))
    o = bpy.context.active_object
    o.name = name
    m = o.modifiers.new("bevel", "BEVEL")
    m.width, m.segments = 0.0015, 3
    o.data.materials.append(principled(name, rgb, 0.25, coat=0.6))
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def disc(name, x, y, z, r, mat, n=96):
    """A round face at y facing the viewer, its uv the image's inscribed circle."""
    me = bpy.data.meshes.new(name)
    verts = [(x, y, z)] + [(x + r * math.cos(2 * math.pi * i / n), y, z + r * math.sin(2 * math.pi * i / n))
                           for i in range(n)]
    me.from_pydata(verts, [], [(0, i, i % n + 1) for i in range(1, n + 1)])
    lay = me.uv_layers.new(name="uv")
    for f in me.polygons:
        for li, vi in zip(f.loop_indices, f.vertices):
            lay.data[li].uv = (0.5, 0.5) if vi == 0 else (0.5 + 0.5 * (verts[vi][0] - x) / r,
                                                          0.5 + 0.5 * (verts[vi][2] - z) / r)
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    return o


def spine(name, x0, th, h, y, bulge, mat, n=12):
    """A book's spine label from x0 to x0 + th, 0 to h high, at y facing the viewer;
    bulge > 0 rounds it out towards the viewer like a cloth hardback's. uv: the image."""
    me = bpy.data.meshes.new(name)
    verts, uvs = [], []
    for j in (0, 1):
        for i in range(n + 1):
            u = i / n
            verts.append((x0 + u * th, y - bulge * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2)), j * h))
            uvs.append((u, j))
    faces = [(i, i + 1, n + 2 + i, n + 1 + i) for i in range(n)]
    me.from_pydata(verts, [], faces)
    lay = me.uv_layers.new(name="uv")
    for f in me.polygons:
        for li, vi in zip(f.loop_indices, f.vertices):
            lay.data[li].uv = uvs[vi]
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    for p_ in me.polygons:
        p_.use_smooth = True
    return o


def side_board(name, x, y0, y1, h, facing_right, mat):
    """A book's cover image on its side face at x, from y0 to y1 and 0 to h, facing +x
    (the front cover, read with the spine on its left) or -x (the back)."""
    me = bpy.data.meshes.new(name)
    if facing_right:
        verts, uv = [(x, y0, 0), (x, y1, 0), (x, y1, h), (x, y0, h)], [(0, 0), (1, 0), (1, 1), (0, 1)]
    else:
        verts, uv = [(x, y1, 0), (x, y0, 0), (x, y0, h), (x, y1, h)], [(0, 0), (1, 0), (1, 1), (0, 1)]
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    lay = me.uv_layers.new(name="uv")
    for li, vi in zip(me.polygons[0].loop_indices, me.polygons[0].vertices):
        lay.data[li].uv = uv[vi]
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    return o


def uv_plane_v(name, w, h, y, mat):
    """An upright quad facing the viewer (-y), from x 0 to w and z 0 to h at y, its uv
    the whole image: a book's spine label."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(0, y, 0), (w, y, 0), (w, y, h), (0, y, h)], [], [(0, 1, 2, 3)])
    lay = me.uv_layers.new(name="uv")
    for li, vi in zip(me.polygons[0].loop_indices, me.polygons[0].vertices):
        lay.data[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[vi]
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    return o


def wall_item(it, y_wall, top):
    """One thing on the wall; x is from the keyboard's centre, z from the desk top.
    kind "board": a cork pinboard w x h, with the sheets in it["sheets"] pinned to it
    (x, z of the pin relative to the board's centre); "sheet": a paper on the wall
    itself; "clock": a wall clock of radius r."""
    out = []
    x, z = it["x"], top + it["z"]
    if it["kind"] == "board":
        w, h = it["w"], it["h"]
        wood_m = wood("board frame", (0.30, 0.19, 0.10), 0.5)
        out.append(cube("board frame", (x - w / 2, y_wall - 0.022, z - h / 2), (x + w / 2, y_wall, z + h / 2), wood_m, 0.003))
        for k, (px_, pz_, col) in enumerate(it.get("loose_pins", [])):   # spare pins stuck in the cork
            out.append(pin(f"spare pin {k}", x + px_, y_wall - 0.0265, z + pz_, col))
        ck = cube("cork", (x - w / 2 + 0.02, y_wall - 0.026, z - h / 2 + 0.02),
                  (x + w / 2 - 0.02, y_wall - 0.02, z + h / 2 - 0.02), image_material("cork", "cork.jpg", rough=0.95), 0.001)
        cw, chh = w - 0.04, h - 0.04                 # the whole image across the face, at its real scale (a
        lay_c = ck.data.uv_layers.active             # cube's own uv crops a quarter and blows it up 4x)
        for poly in ck.data.polygons:
            for li, vi in zip(poly.loop_indices, poly.vertices):
                co = ck.data.vertices[vi].co
                lay_c.data[li].uv = (co.x / cw + 0.5, co.z / chh + 0.5)
        out.append(ck)
        for i, sh in enumerate(it.get("sheets", [])):
            out += hung(f"board sheet {i}", sh, x + sh["x"], y_wall - 0.0262 - 0.0004 * i, z + sh["z"])
    elif it["kind"] == "sheet":
        out += hung("wall sheet", it, x, y_wall - 0.0004, z)
    elif it["kind"] == "shelf":                   # a floating oak shelf w wide, things standing on it
        w, dp_ = it.get("w", 0.6), it.get("d", 0.2)
        oak = wood("shelf oak", (0.42, 0.28, 0.16), 0.5, grain=30.0)
        out.append(cube("shelf", (x - w / 2, y_wall - dp_, z - 0.028), (x + w / 2, y_wall, z), oak, 0.003))
        if it.get("books"):                       # a row of books from workspace_scenes.BOOKS, spines out
            from workspace_scenes import BOOKS
            bx = x - w / 2 + it.get("books_at", 0.03)
            prev_h = None
            for i, (title, author, cover, ink, hgt, th, style) in enumerate(BOOKS):
                dep = 0.16 + 0.01 * (i % 3)
                cm = principled(f"book cover {i}", cover, 0.55)
                pg = principled("book pages", (0.78, 0.73, 0.62), 0.85)   # aged paper, darker than new
                last = i == len(BOOKS) - 1
                lean = math.radians(it.get("lean", 9)) if last else 0.0
                x0 = -th if last else 0.0             # the leaning book pivots on its bottom-right corner
                curved = i % 3 == 0                   # a cloth hardback: its spine bulges
                bd = 0.0022                           # the boards, the spine strip, and the page block
                parts_b = [cube(f"book {i}", (x0, -dep, 0), (x0 + bd, 0, hgt), cm, 0.0008),   # between them,
                           cube(f"book pages {i}", (x0 + bd, -dep + 0.002, 0.003),          # 3 mm short of the
                                (x0 + th - bd, -0.003, hgt - 0.003), pg, 0.0006),            # boards' fore edge
                           cube(f"book board {i}", (x0 + th - bd, -dep, 0), (x0 + th, 0, hgt), cm, 0.0008),
                           cube(f"book back {i}", (x0, -dep, 0), (x0 + th, -dep + 0.002, hgt), cm, 0.0008)]
                sp = image_material(f"spine {i}", f"spine_{i}.jpg", rough=0.5)
                parts_b.append(spine(f"spine {i}", x0, th, hgt, -dep - 0.0004, th * 0.22 if curved else 0.0, sp))
                for side, img_ in ((x0 - 0.0004, f"back_{i}.jpg"), (x0 + th + 0.0004, f"cover_{i}.jpg")):
                    parts_b.append(side_board(f"book side {i}", side, -dep, 0.0, hgt, side > x0, image_material(
                        f"{img_}", img_, rough=0.55)))         # front cover on the right, back on the left
                grime([parts_b[0], parts_b[2], parts_b[3]], 0.9)   # rubbed cover corners
                grime(parts_b[1:2], 1.0)                # page tops: dusty, darker where they are pulled out
                grime(parts_b[4:], 0.8, axes=("X", "Z"))
                bg_ = bpy.data.objects.new(f"book {i}", None)
                sc.collection.objects.link(bg_)
                for o in parts_b:
                    o.parent = bg_
                if last:                               # leaning on its neighbour: its top-left corner touches it
                    bx += th * math.cos(lean) + hgt * math.sin(lean)
                bg_.location = (bx, y_wall - 0.01, z + (th * math.sin(lean) if last else 0.0))   # tilted, its
                # bottom-left corner swings down by th sin(lean): lifted so it rests on the shelf, not in it
                bg_.rotation_euler.y = -lean
                bx += 0.0 if last else th + 0.001 + (0.007 if i in (1, 4) else 0.0)
                out += parts_b
        for k, (dx, dy, col, turn) in enumerate(it.get("pins", [])):     # pins left lying on it
            out += lying_pin(f"shelf pin {k}", x + dx, y_wall - dp_ / 2 + dy, z, col, turn)
        for aid, part, dx, height, turn in it.get("things", []):
            g, objs = gltf(aid, part)
            place(g, objs, (x + dx, y_wall - dp_ / 2), turn, height, base_z=z)
            out += [o for o in objs if o.type == "MESH"]
    elif it["kind"] == "clock":
        r = it.get("r", 0.15)
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.035, location=(x, y_wall - 0.0175, z),
                                            rotation=(math.pi / 2, 0, 0), vertices=96)
        rim = bpy.context.active_object
        rim.name = "clock rim"
        m = rim.modifiers.new("bevel", "BEVEL")
        m.width, m.segments = 0.006, 4
        rim.data.materials.append(principled("clock rim", (0.02, 0.02, 0.022), 0.35))
        for p in rim.data.polygons:
            p.use_smooth = True
        out.append(rim)
        out.append(disc("clock face", x, y_wall - 0.0355, z, r * 0.9, image_material("clock face", "clock_face.jpg", rough=0.6)))
        glass = bpy.data.materials.new("clock glass")
        glass.use_nodes = True
        gb = glass.node_tree.nodes["Principled BSDF"]
        gb.inputs["Transmission Weight"].default_value = 1.0
        gb.inputs["Roughness"].default_value = 0.02
        out.append(disc("clock glass", x, y_wall - 0.0365, z, r * 0.92, glass))
    return out


def hung(name, sh, px, y, pz):
    """A sheet pinned at its top centre: sh["img"] at width w (its height from the
    image's aspect), turned rot deg, curling bow m; pin=(r, g, b) or None (taped flat)."""
    img = bpy.data.images.load(os.path.join(HERE, "textures", "workspace", sh["img"]), check_existing=True)
    w = sh["w"]
    h = w * img.size[1] / img.size[0]
    out = [sheet(name, sh["img"], px, pz, w, h, y, sh.get("rot", 0.0), sh.get("bow", 0.004))]
    if sh.get("dents"):                            # handled paper: soft dents and creases in the bump
        nt2 = out[0].data.materials[0].node_tree
        tcd = nt2.nodes.new("ShaderNodeTexCoord")
        vo = nt2.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "SMOOTH_F1"   # a few round dents,
        vo.inputs["Scale"].default_value = 4.0; vo.inputs["Smoothness"].default_value = 1.0   # soft-edged
        nt2.links.new(tcd.outputs["UV"], vo.inputs["Vector"])
        nz = nt2.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 1.0
        nt2.links.new(tcd.outputs["UV"], nz.inputs["Vector"])        # and a long, gentle waviness
        add = nt2.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = 0.35
        nt2.links.new(vo.outputs["Distance"], add.inputs[0]); nt2.links.new(nz.outputs["Fac"], add.inputs[2])
        bm = nt2.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = sh["dents"]
        nt2.links.new(add.outputs[0], bm.inputs["Height"])
        nt2.links.new(bm.outputs["Normal"], nt2.nodes["Principled BSDF"].inputs["Normal"])
    if sh.get("pages"):                            # a wall calendar: the months behind, a wire binding on top
        import random
        rnd = random.Random(len(name))
        n = sh["pages"]
        for k in range(1, n + 1):
            out.append(sheet(f"{name} page {k}", sh.get("back", "paper_back.jpg"), px + rnd.uniform(-0.0015, 0.0015),
                             pz, w, h + 0.0022 * k, y + 0.0007 * k, sh.get("rot", 0.0) + rnd.uniform(-0.5, 0.5),
                             sh.get("bow", 0.004) * (1 - 0.6 * k / n)))
        out += binding(name, px, y - 0.0012, pz + 0.012 - 0.004, w * 0.9, sh.get("rot", 0.0))
        out.append(pin(name + " pin", px, y - 0.004, pz + 0.018, sh.get("pin") or (0.2, 0.2, 0.22)))
        return out
    if sh.get("pin"):
        out.append(pin(name + " pin", px, y - 0.0003, pz, sh["pin"]))
    return out


def binding(name, px, y, pz, w, rot, pitch=0.0085):
    """A calendar's wire-o binding along a sheet's top edge: a dark steel loop every
    pitch m, each a ring standing through the pages, and the hanger bow in the middle."""
    wire = bpy.data.materials.get("binding wire") or principled("binding wire", (0.05, 0.05, 0.055), 0.3)
    wire.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    a = math.radians(rot)
    out = []
    n = int(w / pitch)
    for i in range(n + 1):
        lx = -w / 2 + i * w / n
        if abs(lx) < 0.012:                        # the gap for the hanger
            continue
        x, z = px + lx * math.cos(a), pz + lx * math.sin(a)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.0032, minor_radius=0.00045, major_segments=16, minor_segments=6,
                                         location=(x, y, z), rotation=(0, math.radians(90), 0))
        o = bpy.context.active_object
        o.name = f"{name} wire"
        o.data.materials.append(wire)
        out.append(o)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.008, minor_radius=0.0006, major_segments=24, minor_segments=6,
                                     location=(px, y - 0.001, pz + 0.004), rotation=(math.radians(90), 0, 0))
    o = bpy.context.active_object
    o.name = f"{name} hanger"
    o.data.materials.append(wire)
    out.append(o)
    return out


def screen_material(screen, glow, rough=0.4):
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
    b.inputs["Roughness"].default_value = rough     # 0.4 an anti-glare coat: the room shows only as a soft sheen
    b.inputs["Specular IOR Level"].default_value = 0.15 if rough >= 0.3 else 0.4
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


FINISH = {    # bezel at the sides and top, chin, shell depth (m); shell and stand colours
    "silver": dict(bezel=0.006, chin=0.020, depth=0.015, shell=(0.015, 0.015, 0.017), stand=(0.55, 0.56, 0.58), metal=1.0),
    "black": dict(bezel=0.013, chin=0.024, depth=0.040, shell=(0.0015, 0.0015, 0.0017), stand=(0.006, 0.006, 0.007), metal=0.3,
                  rough=0.75, base_t=0.016, neck_w=0.07),
}


def panel(screen, inches, aspect=(16, 9), curve=None, glow=1.6, finish="silver", notes=(), rough=0.4):
    """One display head, its screen's centre at the origin facing -y: the screen, a
    bezel and chin around it (FINISH: thin and silver-stood, or a black office monitor
    with a 13 mm bezel), a box behind for the electronics. Returns (head empty,
    objects, screen width, screen height). A white power light sits in the chin at the
    right; notes are sticky notes (u from -0.5 to 0.5 along the width, img, rot) stuck
    to the bottom bezel and hanging below it."""
    fin = FINISH[finish]
    diag = inches * 0.0254
    sw, sh = diag * aspect[0] / math.hypot(*aspect), diag * aspect[1] / math.hypot(*aspect)
    shell = bpy.data.materials.get(f"monitor shell {finish}") or principled(f"monitor shell {finish}", fin["shell"],
                                                                            fin.get("rough", 0.55))
    head = bpy.data.objects.new("monitor head", None)
    sc.collection.objects.link(head)
    scr = bent_grid("monitor screen", sw, sh, -sh / 2, curve, -0.0008, screen_material(screen, glow, rough))
    b, ch, dp = fin["bezel"], fin["chin"], fin["depth"]
    frame = bent_grid("monitor frame", sw + 2 * b, sh + b + ch, -sh / 2 - ch, curve, dp / 2 - 0.0003, shell)
    sol = frame.modifiers.new("depth", "SOLIDIFY")
    sol.thickness, sol.offset = dp, 0.0
    back = cube("monitor back", (-sw * 0.3, dp - 0.001, -sh * 0.32), (sw * 0.3, dp + 0.03, sh * 0.28), shell, 0.01)
    if curve is None:                              # the design details of a flat panel's front: a glossy
        gap_m = bpy.data.materials.get("monitor gap") or principled("monitor gap", (0.0005, 0.0005, 0.0006), 0.7)
        # matte: a glossy gap mirrored the bright wall above and read as a slit you could see through
        gw, gy0, gy1 = 0.0028, -0.0007, -0.0002    # black shadow-gap ring round the glass, a groove above
        ring = [((-sw / 2 - gw, -sh / 2 - gw), (sw / 2 + gw, -sh / 2)), ((-sw / 2 - gw, sh / 2), (sw / 2 + gw, sh / 2 + gw)),
                ((-sw / 2 - gw, -sh / 2), (-sw / 2, sh / 2)), ((sw / 2, -sh / 2), (sw / 2 + gw, sh / 2))]
        deco = [cube("monitor gap", (x0, gy0, z0), (x1, gy1, z1), gap_m, 0.0002) for (x0, z0), (x1, z1) in ring]
        deco.append(cube("monitor chin groove", (-sw / 2 - b + 0.004, gy0, -sh / 2 - gw - 0.0016),
                         (sw / 2 + b - 0.004, gy1, -sh / 2 - gw - 0.0008), gap_m, 0.0002))   # the chin, and a
        badge = principled("monitor badge", (0.18, 0.18, 0.19), 0.3)                    # small grey badge on it
        badge.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
        deco.append(cube("monitor badge", (-0.011, -0.0007, -sh / 2 - ch * 0.55 - 0.0018),
                         (0.011, -0.0003, -sh / 2 - ch * 0.55 + 0.0018), badge, 0.0008))
    else:
        deco = []
    led = bpy.data.materials.get("monitor power light")
    if led is None:
        led = bpy.data.materials.new("monitor power light")
        led.use_nodes = True
        lb = led.node_tree.nodes["Principled BSDF"]
        lb.inputs["Base Color"].default_value = (0.8, 0.85, 1.0, 1)
        lb.inputs["Emission Color"].default_value = (0.75, 0.85, 1.0, 1)
        lb.inputs["Emission Strength"].default_value = 12.0
    lz = -sh / 2 - ch * 0.45
    lx = sw / 2 - 0.03
    ly = -0.0004 - (curve - math.sqrt(curve * curve - lx * lx) if curve else 0.0)
    parts = deco + [scr, frame, back, cube("monitor power light", (lx - 0.0012, ly - 0.0006, lz - 0.0005),
                                    (lx + 0.0012, ly, lz + 0.0005), led, 0.0002)]
    for i, n in enumerate(notes):
        u, img, rot = n[:3]
        nx = u * sw
        ny = -0.0006 - (curve - math.sqrt(curve * curve - nx * nx) if curve else 0.0)
        im = bpy.data.images.load(os.path.join(HERE, "textures", "workspace", img), check_existing=True)
        w = n[3] if len(n) > 3 else 0.051
        parts.append(sheet(f"monitor note {i}", img, nx, -sh / 2 - ch * 0.25 - 0.012, w, w * im.size[1] / im.size[0],
                           ny, rot, 0.010))
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
    Returns (group, objects, blocks): one object list per screen and what holds it
    (panel and stand, or panel and arm), whose plan the cables go round, and the
    bases."""
    style = spec.get("style", "stand")
    screens = spec.get("screens") or [spec["screen"]]
    glow = spec.get("glow", 1.6)
    finish = spec.get("finish", "silver")
    fin = FINISH[finish]
    alu = principled(f"monitor stand {finish}", fin["stand"], 0.35 if finish == "silver" else 0.5)
    alu.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = fin["metal"]
    g = bpy.data.objects.new("monitor", None)
    sc.collection.objects.link(g)
    objs, blocks, feet = [], [], []
    tilt = math.radians(spec.get("tilt", 8))
    lift = spec.get("lift", 0.11)

    def on_stand(screen, inches, aspect, curve, x, turn, base_w=0.24, base_d=0.18, notes=()):
        st = bpy.data.objects.new("monitor stand", None)
        sc.collection.objects.link(st)
        st.parent = g
        st.location = (x, 0, 0)
        st.rotation_euler.z = math.radians(turn)
        head, parts, sw, sh = panel(screen, inches, aspect, curve, glow, finish, notes, spec.get("screen_rough", 0.4))
        zc = lift + 0.02 + sh / 2
        head.parent = st
        head.location = (0, 0.012 - (fin["depth"] - 0.015), zc)
        head.rotation_euler.x = -tilt              # the top leans back
        nw, bt = fin.get("neck_w", 0.06) / 2, fin.get("base_t", 0.006)
        neck = cube("monitor neck", (-nw, 0.042, bt), (nw, 0.067, zc + 0.02), alu, 0.004)
        base = cube("monitor base", (-base_w / 2, -base_d / 2 + 0.02, 0.0), (base_w / 2, base_d / 2 + 0.02, bt), alu,
                    min(0.006, bt / 2))
        for o in (neck, base):
            o.parent = st
        objs.extend(parts + [neck, base])
        blocks.append(parts + [neck, base])
        feet.append(base)
        return sw

    if style == "stand":
        on_stand(screens[0], spec.get("inches", 27), (16, 9), None, 0.0, 0.0, notes=spec.get("notes", ()))
    elif style == "dual":
        inches = spec.get("inches", 24)
        sw = inches * 0.0254 * 16 / math.hypot(16, 9)
        gap = sw / 2 + fin["bezel"] + spec.get("gap", 0.012) / 2   # from the middle to each screen's centre;
        # gap is between the two frames, so the bezels meet rather than cut into each other
        for k, side in enumerate((-1, 1)):
            on_stand(screens[k % len(screens)], inches, (16, 9), None,
                     side * gap * math.cos(math.radians(12)), -side * 12, base_w=0.30, base_d=0.23,
                     notes=[n[1:] for n in spec.get("notes", ()) if n[0] == k])
    elif style == "ultrawide":
        on_stand(screens[0], spec.get("inches", 34), (21, 9), 1.5, 0.0, 0.0, base_w=0.30, base_d=0.20,
                 notes=spec.get("notes", ()))
    elif style == "arm":
        reach = spec.get("reach", 0.24)
        head, parts, sw, sh = panel(screens[0], spec.get("inches", 27), (16, 9), None, glow, finish)
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
        blocks.append(parts + [pole, clamp, jaw, arm, plate])
    return g, objs, blocks, feet


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
LIGHTS = S.get("lights", [])                     # area lights, placed once the desk is known (below)
floor = bpy.data.objects["Plane"]
floor.is_shadow_catcher = True                   # the room's own floor, with the desk's shadow on it

# ---- the cables, while the keyboard still stands on z = 0 ----------------------------
if S["desk"] == "@counter":
    desk, desk_objs = counter()
elif S["desk"] == "@black_desk":
    desk, desk_objs = black_desk()
else:
    desk, desk_objs = gltf(S["desk"])
    lo, hi = box(desk_objs)
    if S.get("desk_height"):
        desk.scale.z = S["desk_height"] / (hi.z - lo.z)
    if S.get("desk_depth"):
        desk.scale.y = S["desk_depth"] / (hi.y - lo.y)
    if S.get("desk_width"):
        desk.scale.x = S["desk_width"] / (hi.x - lo.x)
if S.get("desk_color"):                            # (r, g, b, f): blend the desk's colours f towards rgb
    tint(desk_objs, S["desk_color"][:3], "MIX", S["desk_color"][3])
if S.get("desk_spots"):                            # faint marks of use: a few soft, slightly darker spots
    spots(desk_objs, S["desk_spots"])
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
    mon, mon_objs, blocks, feet = monitors(spec)
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
    m = 0.02                                       # clearance around each screen and its stand, in plan
    for bl in blocks:
        lo2, hi2 = box(bl)
        avoid.append((lo2.x - m, hi2.x + m, lo2.y - m, hi2.y + m))   # world


def cable_exit(rects, xs):
    """Where the cables leave over the back edge: in the widest gap between the screens
    (60 mm at least) or beside them, whichever the cables' starts xs reach with the
    least sideways run. No screens: None."""
    if not rects:
        return None
    iv = sorted((x0, x1) for x0, x1, _, _ in rects)
    merged = [list(iv[0])]
    for x0, x1 in iv[1:]:
        if x0 <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], x1)
        else:
            merged.append([x0, x1])
    cands = [merged[0][0] - 0.03, merged[-1][1] + 0.03]
    cands += [(a1 + b0) / 2 for (_, a1), (b0, _) in zip(merged, merged[1:]) if b0 - a1 >= 0.06]
    return min(cands, key=lambda c: sum(abs(c - x) for x in xs))


def ground(x, y):
    """How far above the desk top a cable lies at (x, y): on the mat its thickness,
    stepping down over 8 mm past the mat's edge (MAT_RECT, MAT_T set once it is built)."""
    if not MAT_RECT:
        return 0.0
    x0, x1, y0, y1 = MAT_RECT
    out = max(x0 - x, x - x1, y0 - y, y - y1, 0.0)
    t = min(1.0, out / 0.008)
    return MAT_T * (1 - (3 * t * t - 2 * t ** 3))


MAT_RECT, MAT_T = None, 0.0
CABLE_DROPS = []                                  # x of every cable going over the desk's back edge


def desk_cable(name, start, d0, x_exit, y_front, y_edge, z_desk, r, mat, v_scale=None, wobble=(0.006, 0.17, 0.0)):
    """A cable from start (its plug or the mouse's nose) along d0, across in front of
    the screens at y_front to x_exit, back to the desk's back edge and over it. It
    settles from the start's height onto the desk within 30 mm, and meanders sideways
    by wobble = (amplitude m, wavelength m, phase), faded in after the plug and out
    before the edge, so no two cables lie like rails."""
    d0 = mathutils.Vector((d0.x, d0.y, 0)).normalized()
    p1 = start + d0 * 0.03
    q = mathutils.Vector((x_exit, max(y_front, p1.y + 0.05), z_desk))
    k = (q.y - p1.y) * 0.55
    c = [p1, p1 + d0 * k, q - mathutils.Vector((0, k, 0)), q]
    plan = [start + d0 * (0.03 * i / 8) for i in range(8)]
    for i in range(80):
        t = i / 79
        plan.append((1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3])
    n = max(2, int((y_edge - 0.01 - q.y) / 0.01))
    plan += [mathutils.Vector((x_exit, q.y + (y_edge - 0.01 - q.y) * i / n, z_desk)) for i in range(1, n + 1)]
    runs = [0.0]
    for i in range(1, len(plan)):
        runs.append(runs[-1] + (mathutils.Vector((plan[i].x, plan[i].y)) - mathutils.Vector((plan[i - 1].x, plan[i - 1].y))).length)
    total = runs[-1]
    amp, lam, ph = wobble
    pts = []
    for i, (p, run) in enumerate(zip(plan, runs)):
        a, b = plan[max(i - 1, 0)], plan[min(i + 1, len(plan) - 1)]
        t = mathutils.Vector((b.x - a.x, b.y - a.y))
        nrm = mathutils.Vector((-t.y, t.x)).normalized() if t.length > 1e-9 else mathutils.Vector((0, 0))
        fade = min(1.0, max(0.0, (run - 0.04) / 0.06), max(0.0, (total - run - 0.02) / 0.08))
        off = nrm * (amp * fade * math.sin(2 * math.pi * run / lam + ph))
        kk = min(1.0, run / 0.03)
        zg = z_desk + ground(p.x + off.x, p.y + off.y)
        pts.append((p.x + off.x, p.y + off.y, zg + r + (start.z - zg - r) * (1 - (3 * kk * kk - 2 * kk ** 3))))
    o = bridge_cable._tube(name, pts, [r] * len(pts), mat, ring=16, v_scale=v_scale)
    over_edge(name + " drop", x_exit, y_edge, z_desk, z_desk, r, mat, v_scale)
    return o


def over_edge(name, x, y_edge, z_desk, drop, r, mat, v_scale=None):
    """A cable from the desk top over its back edge (at y_edge) and down `drop` m: a
    quarter turn of 12 mm radius, then straight down."""
    CABLE_DROPS.append(x)
    pts = [(x, y_edge - 0.01, z_desk + r)]
    for i in range(1, 13):
        a = math.pi / 2 * i / 12
        pts.append((x, y_edge + 0.012 * math.sin(a), z_desk + r - 0.012 * (1 - math.cos(a))))
    for i in range(1, 9):
        pts.append((x, y_edge + 0.012 + 0.002 * i, z_desk + r - 0.012 - (drop - 0.02) * i / 8))
    return bridge_cable._tube(name, pts, [r] * len(pts), mat, ring=16, v_scale=v_scale)


# ---- the keyboard onto the desk top, the props around it ----------------------
kb = bpy.data.objects.new("keyboard", None)
sc.collection.objects.link(kb)
mon_top = [mon] if mon else []
for o in [o for o in sc.objects if o.parent is None and o not in [kb, floor, desk] + mon_top and o.type != "CAMERA"
          and o not in desk_objs and o.name != "target"] + [bpy.data.objects["target"]]:
    mw = o.matrix_world.copy()
    o.parent = kb
    o.matrix_world = mw
mat_t, mat_rect = 0.0, None
if S.get("desk_mat"):                              # the mat first; keyboard, mouse and what is on it stand on it
    g, objs, mat_t = desk_mat(S["desk_mat"])
    place(g, objs, (S["desk_mat"].get("x", 0.0), kb_y + S["desk_mat"].get("y", 0.0)), 0, base_z=top)
    lo2, hi2 = box(objs[:1])
    mat_rect = (lo2.x, hi2.x, lo2.y, hi2.y)
    MAT_RECT, MAT_T = mat_rect, mat_t
kb.location = (0.0, kb_y, top + mat_t)
bpy.context.view_layer.update()
if S.get("wall"):            # the desk against a wall, 40 mm behind its back edge (built after the keyboard
    wall(S["wall"], dhi.y + 0.04, (dlo.x + dhi.x) / 2, top)   # group took the loose objects)
mouse_g = None
if S.get("mouse"):
    mouse_g, objs = mouse(dict(S["mouse"], pad=S["mouse"].get("pad", not S.get("desk_mat"))))
    place(mouse_g, objs, (S["mouse"]["x"], kb_y + S["mouse"]["y"]), S["mouse"].get("turn", 0), base_z=top + mat_t)

# both cables leave the same way: across in front of the screens to one exit (a gap
# between them, or beside them), then side by side straight back and over the edge
pa_l, da_l = bridge_cable.host_plug(root_l, halves[0][1])
for o in bpy.data.objects:
    if o.parent == root_l and "host" in o.name:
        o["pk_host"] = True
mw = root_l.matrix_world
start_k = mw @ pa_l
dir_k = (mw.to_3x3() @ da_l).normalized()
starts = [start_k.x]
wired = (S.get("mouse") or {}).get("wired")
if wired:
    nose = mouse_g.matrix_world @ mathutils.Vector((0, 0.0575, 0.006))
    starts.append(nose.x)
x_exit = cable_exit(avoid, starts)
y_front = (min(y0 for _, _, y0, _ in avoid) - 0.02) if avoid else start_k.y + 0.12
ye = dhi.y - 0.004
if x_exit is None:
    xk, xm = start_k.x - 0.10, (nose.x + 0.06 if wired else 0.0)
else:
    side = 1 if (wired and nose.x > start_k.x) else -1     # the mouse's cable on its own side of the pair
    xk, xm = x_exit - side * 0.026, x_exit + side * 0.026     # side by side, apart
host = desk_cable("host cable", start_k, dir_k, xk, y_front, ye, top, bridge_cable.CABLE_R / 1000,
                  bridge_cable._braid_material(), v_scale=bridge_cable.BRAID_MM / 1000)
host["pk_host"] = True
if wired:
    fwd = mouse_g.matrix_world.to_3x3() @ mathutils.Vector((0, 1, 0))
    desk_cable("mouse cable", nose, fwd, xm, y_front + 0.05, ye, top, 0.0016,
               principled("mouse cable", (0.02, 0.02, 0.022), 0.5), wobble=(0.009, 0.23, 1.9))
print(f"cables: exit {x_exit if x_exit is None else round(x_exit, 3)}, in front of the screens at y {y_front:.3f}")
placed = []                                        # (name, plan box) of what stands on the desk
for aid, part, x, y, turn, height, flat, *more in S["props"]:
    g, objs = BUILT[aid]() if aid in BUILT else gltf(aid, part)
    extra = more[0] if more else {}
    if extra.get("tint"):
        tint(objs, extra["tint"])
    if extra.get("hsv"):                           # (hue, sat, value) on its colour, coat (rough): a rubber duck
        hue_, sat_, val_, coat_ = extra["hsv"]       # its glTF orange, which AgX renders salmon, turned yellow
        for o in objs:
            for slot in (o.material_slots if o.type == "MESH" else []):
                nt2 = slot.material.node_tree
                b = next((n for n in nt2.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
                if b is None:
                    continue
                b.inputs["Specular Tint"].default_value = (1, 1, 1, 1)   # the import sets 1.58: a white haze
                b.inputs["Coat Weight"].default_value, b.inputs["Coat Roughness"].default_value = coat_, 0.15
                inp = b.inputs["Base Color"]
                hs = nt2.nodes.new("ShaderNodeHueSaturation")
                hs.inputs["Hue"].default_value, hs.inputs["Saturation"].default_value = hue_, sat_
                hs.inputs["Value"].default_value = val_
                if inp.is_linked:
                    nt2.links.new(inp.links[0].from_socket, hs.inputs["Color"])
                else:
                    hs.inputs["Color"].default_value = inp.default_value
                nt2.links.new(hs.outputs["Color"], inp)
    if extra.get("grime"):
        grime(objs, extra["grime"])
    if extra.get("grip"):                          # (axis, lo, hi, amount): where it is held
        grime(objs, extra["grip"][3], extra["grip"][:3])
    if extra.get("scale"):
        g.scale = [extra["scale"]] * 3
    if extra.get("at_back"):                         # y from the desk's back edge instead
        y = back_rel - y
    on_mat = mat_rect and mat_rect[0] < x < mat_rect[1] and mat_rect[2] < kb_y + y < mat_rect[3]
    floor_z = extra.get("z", 0.0) if extra.get("floor") else None     # floor=True: it stands on the floor
    place(g, objs, (x, kb_y + y), turn, height, flat,
          base_z=floor_z if floor_z is not None else top + (mat_t if on_mat else 0.0) + extra.get("z", 0.0),
          origin=extra.get("origin", False))
    if extra.get("page"):                          # (image, width, depth, curl m): its top page, peeling up
        img_, pw, pd, curl = extra["page"]           # at the bottom (near) edge
        lo3, hi3 = box(objs)
        pm = image_material(f"page {img_}", img_, rough=0.75)
        me = bpy.data.meshes.new("top page")
        ny_, nx_ = 24, 16
        verts_, uvs_ = [], []
        for j in range(ny_ + 1):
            v = j / ny_                               # 0 at the near edge, 1 at the far one
            for i_ in range(nx_ + 1):
                u = i_ / nx_
                e = abs(2 * u - 1)                    # 0 mid-page, 1 at a side: the corners curl first,
                reach = 0.10 + 0.20 * e ** 1.5        # further in and higher than the middle, the right
                weight = (0.25 + 0.75 * e ** 1.6) * (1.0 if u > 0.5 else 0.65)   # more than the left
                lift = curl * weight * max(0.0, (reach - v) / reach) ** 2.0
                verts_.append(((u - 0.5) * pw, (v - 0.5) * pd, lift))
                uvs_.append((u, v))
        w_ = nx_ + 1
        me.from_pydata(verts_, [], [(j * w_ + i_, j * w_ + i_ + 1, (j + 1) * w_ + i_ + 1, (j + 1) * w_ + i_)
                                    for j in range(ny_) for i_ in range(nx_)])
        lay_p = me.uv_layers.new(name="uv")
        for f in me.polygons:
            for li, vi in zip(f.loop_indices, f.vertices):
                lay_p.data[li].uv = uvs_[vi]
        me.materials.append(pm)
        pg_o = bpy.data.objects.new("top page", me)
        sc.collection.objects.link(pg_o)
        sol = pg_o.modifiers.new("thickness", "SOLIDIFY")
        sol.thickness, sol.offset = 0.0002, 1.0
        for p_ in me.polygons:
            p_.use_smooth = True
        pg_o.location = ((lo3.x + hi3.x) / 2, (lo3.y + hi3.y) / 2, hi3.z + 0.0002)
        pg_o.rotation_euler.z = math.radians(turn)
    if extra.get("decal"):                         # (image, width, depth): writing laid on its top
        img_, dw, dd = extra["decal"]
        lo3, hi3 = box(objs)
        dm = bpy.data.materials.new(f"decal {img_}")
        dm.use_nodes = True
        dn = dm.node_tree.nodes
        bs = dn["Principled BSDF"]
        tx = dn.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(os.path.join(HERE, "textures", "workspace", img_), check_existing=True)
        dm.node_tree.links.new(tx.outputs["Color"], bs.inputs["Base Color"])
        dm.node_tree.links.new(tx.outputs["Alpha"], bs.inputs["Alpha"])
        bs.inputs["Roughness"].default_value = 0.6
        dec = uv_plane(f"decal {img_}", (-dw / 2, -dd / 2), (dw / 2, dd / 2), 0.0, dm)
        dec.location = ((lo3.x + hi3.x) / 2, (lo3.y + hi3.y) / 2, hi3.z + 0.0003)
        dec.rotation_euler.z = math.radians(turn)
    if extra.get("cable"):                           # its own cable straight back and over the edge
        st = g.matrix_world @ mathutils.Vector(g["pk_cable_at"])
        bk = (g.matrix_world.to_3x3() @ mathutils.Vector((0, 1, 0))).normalized()
        xt, yf = st.x + extra["cable"].get("dx", 0.0), st.y + 0.06
        for foot in (feet if S.get("monitor") else []):   # round a monitor foot, never under it
            flo2, fhi2 = box([foot])
            if fhi2.y > yf and min(st.x, xt) < fhi2.x + 0.015 and max(st.x, xt) > flo2.x - 0.015:
                yf = min(yf, flo2.y - 0.02)
                xt = flo2.x - 0.03 if xt < (flo2.x + fhi2.x) / 2 else fhi2.x + 0.03
        desk_cable(f"{aid} cable", st, bk, xt, yf, ye, top,
                   extra["cable"].get("r", 0.0018), principled(f"{aid} cable", extra["cable"].get("color", (0.02, 0.02, 0.022)), 0.5),
                   wobble=(0.007, 0.21, 0.7))
    if not extra.get("on") and not extra.get("floor"):   # a cup on its saucer may overlap the saucer
        lo2, hi2 = box(objs)
        placed.append((part or aid, (lo2.x, hi2.x, lo2.y, hi2.y)))
lo2, hi2 = box([o for o in root_l.children_recursive if o.type == "MESH"] +
               [o for o in root_r.children_recursive if o.type == "MESH"])
placed.append(("keyboard", (lo2.x, hi2.x, lo2.y, hi2.y)))
if mouse_g:
    lo2, hi2 = box([o for o in mouse_g.children if o.type == "MESH"])
    placed.append(("mouse", (lo2.x, hi2.x, lo2.y, hi2.y)))
for i, (na, ra) in enumerate(placed):
    for nb, rb in placed[i + 1:] + [(f"screen {k}", r) for k, r in enumerate(avoid)]:
        if ra[0] < rb[1] and rb[0] < ra[1] and ra[2] < rb[3] and rb[2] < ra[3]:
            print(f"WARNING overlap in plan: {na} and {nb}")

for i, L in enumerate(LIGHTS):                    # e.g. a warm ceiling panel: (x, y) from the keyboard, z above the desk
    ld = bpy.data.lights.new(f"light {i}", "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = L.get("size", (1.0, 0.6))
    ld.energy = L["energy"]
    ld.color = L.get("color", (1.0, 1.0, 1.0))
    lo_ = bpy.data.objects.new(f"light {i}", ld)
    sc.collection.objects.link(lo_)
    lo_.location = (L["at"][0], kb_y + L["at"][1], top + L["at"][2])
    lo_.rotation_euler = [math.radians(v) for v in L.get("rot", (0, 0, 0))]

def monitor_cables(spec):
    """Two cables a monitor, power and signal: out of the bottom of its back box,
    down behind the neck in a curve, onto the desk 30 mm behind the stand (a side
    monitor's beside its base, on the outer side, where the camera sees them), then
    straight back and over the edge. spec: dict(color=(r, g, b))."""
    mat = principled("monitor cable", spec.get("color", (0.012, 0.012, 0.013)), 0.5)
    n = 0
    for back in [o for o in bpy.data.objects if o.name.startswith("monitor back")]:
        st = back.parent.parent
        vs = [v.co for v in back.data.vertices]
        ymax, zmin = max(v.y for v in vs), min(v.z for v in vs)
        stand_parts = [o for o in st.children if o.type == "MESH"]
        slo, shi = box(stand_parts)
        y_land = shi.y + 0.03
        cx = (slo.x + shi.x) / 2
        side = -1 if cx < -0.05 else (1 if cx > 0.05 else 0)   # a side stand's cables leave on its outer side
        x_out = (slo.x - 0.04 if side < 0 else shi.x + 0.04) if side else None
        for k, (dx, r) in enumerate(((-0.014, 0.0030), (0.014, 0.0024))):    # power, signal (DP/HDMI)
            p0 = back.matrix_world @ mathutils.Vector((dx, ymax - 0.012, zmin))
            lx = (x_out + side * 0.012 * k) if side else p0.x + dx * 0.6
            land = mathutils.Vector((lx, max(y_land, p0.y + 0.05) + 0.008 * k, top + r))
            c1 = p0 + mathutils.Vector((0, 0, -(p0.z - land.z) * 0.55))
            c2 = land - mathutils.Vector((0, 0.06, 0))
            pts = []
            for i in range(40):
                t = i / 39
                pts.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * land)
            m = max(2, int((ye - 0.01 - land.y) / 0.01))
            pts += [mathutils.Vector((land.x + 0.004 * math.sin(i * 0.7 + k), land.y + (ye - 0.01 - land.y) * i / m, land.z))
                    for i in range(1, m + 1)]
            bridge_cable._tube(f"monitor cable {n}", [tuple(p) for p in pts], [r] * len(pts), mat, ring=14)
            over_edge(f"monitor cable {n} drop", pts[-1].x, ye, top, top, r, mat)
            n += 1
    print(f"monitor cables: {n}")


for i, G in enumerate(S.get("glints", [])):     # a light only reflections see: a ceiling fixture's strip
    w_, h_ = G.get("size", (1.6, 0.12))          # in the screens, which a real ceiling light at this camera height
    gm = bpy.data.materials.new(f"glint {i}")    # cannot reach (the reflected rays leave the screens nearly level)
    gm.use_nodes = True
    gn = gm.node_tree.nodes
    gn.remove(gn["Principled BSDF"])
    em = gn.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*G.get("color", (1.0, 0.9, 0.75)), 1)
    tc_ = gn.new("ShaderNodeTexCoord")           # brightest in the middle, fading to nothing at both ends,
    sx = gn.new("ShaderNodeSeparateXYZ")         # with a slow ripple, so the streak is not one even bar
    gm.node_tree.links.new(tc_.outputs["UV"], sx.inputs[0])
    m1 = gn.new("ShaderNodeMath"); m1.operation = "MULTIPLY_ADD"
    m1.inputs[1].default_value, m1.inputs[2].default_value = 2.0, -1.0
    gm.node_tree.links.new(sx.outputs["X"], m1.inputs[0])
    m2 = gn.new("ShaderNodeMath"); m2.operation = "POWER"; m2.inputs[1].default_value = 2.0
    gm.node_tree.links.new(m1.outputs[0], m2.inputs[0])
    m3 = gn.new("ShaderNodeMath"); m3.operation = "SUBTRACT"; m3.inputs[0].default_value = 1.0
    gm.node_tree.links.new(m2.outputs[0], m3.inputs[1])
    nz = gn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0
    gm.node_tree.links.new(tc_.outputs["UV"], nz.inputs["Vector"])
    m4 = gn.new("ShaderNodeMath"); m4.operation = "MULTIPLY"
    gm.node_tree.links.new(m3.outputs[0], m4.inputs[0])
    gm.node_tree.links.new(nz.outputs["Fac"], m4.inputs[1])
    m5 = gn.new("ShaderNodeMath"); m5.operation = "MULTIPLY"; m5.inputs[1].default_value = G.get("strength", 6.0) * 2
    gm.node_tree.links.new(m4.outputs[0], m5.inputs[0])
    gm.node_tree.links.new(m5.outputs[0], em.inputs["Strength"])
    gm.node_tree.links.new(em.outputs[0], gn["Material Output"].inputs["Surface"])
    gme = bpy.data.meshes.new(f"glint {i}")
    cx_, cy_, cz_ = G["at"][0], kb_y + G["at"][1], top + G["at"][2]
    gme.from_pydata([(cx_ - w_ / 2, cy_, cz_ - h_ / 2), (cx_ + w_ / 2, cy_, cz_ - h_ / 2),
                     (cx_ + w_ / 2, cy_, cz_ + h_ / 2), (cx_ - w_ / 2, cy_, cz_ + h_ / 2)], [], [(0, 3, 2, 1)])
    guv = gme.uv_layers.new(name="uv")
    for li, vi in zip(gme.polygons[0].loop_indices, gme.polygons[0].vertices):
        guv.data[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[vi]
    gme.materials.append(gm)
    go = bpy.data.objects.new(f"glint {i}", gme)
    sc.collection.objects.link(go)
    go.visible_camera = False
    go.visible_diffuse = False
    go.visible_shadow = False

if S.get("monitor") and S["monitor"].get("cables"):
    monitor_cables(S["monitor"]["cables"] if isinstance(S["monitor"]["cables"], dict) else {})

if S.get("wall") and S["wall"].get("scuffs", True) and CABLE_DROPS:
    y_w = dhi.y + 0.04 - 0.0006                  # the wall rubbed where cables go down between desk and wall
    sm = bpy.data.materials.new("wall scuffs")
    sm.use_nodes = True
    sb = sm.node_tree.nodes["Principled BSDF"]
    stx = sm.node_tree.nodes.new("ShaderNodeTexImage")
    stx.image = bpy.data.images.load(os.path.join(HERE, "textures", "workspace", "wall_scuff.png"), check_existing=True)
    sm.node_tree.links.new(stx.outputs["Color"], sb.inputs["Base Color"])
    sm.node_tree.links.new(stx.outputs["Alpha"], sb.inputs["Alpha"])
    sb.inputs["Roughness"].default_value = 0.6
    xs = sorted(CABLE_DROPS)
    groups = [[xs[0]]]
    for xv in xs[1:]:
        (groups[-1] if xv - groups[-1][-1] < 0.06 else groups.append([xv]) or groups[-1]).append(xv)
    for i, gr in enumerate(groups):
        cx = sum(gr) / len(gr)
        wv, hv = 0.12 + (max(gr) - min(gr)), 0.16
        me = bpy.data.meshes.new(f"scuff {i}")
        me.from_pydata([(cx - wv / 2, y_w, top - 0.05), (cx + wv / 2, y_w, top - 0.05),
                        (cx + wv / 2, y_w, top - 0.05 + hv), (cx - wv / 2, y_w, top - 0.05 + hv)], [], [(0, 1, 2, 3)])
        uvl = me.uv_layers.new(name="uv")
        for li, vi in zip(me.polygons[0].loop_indices, me.polygons[0].vertices):
            uvl.data[li].uv = ((0, 0), (1, 0), (1, 1), (0, 1))[vi]
        me.materials.append(sm)
        so_ = bpy.data.objects.new(f"scuff {i}", me)
        sc.collection.objects.link(so_)
    print(f"scuffs: {len(groups)} at x {[round(sum(g_) / len(g_), 2) for g_ in groups]}")

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
sc.view_settings.look = S.get("look", "AgX - Base Contrast")
sc.view_settings.exposure = S.get("exposure", 0.0)
if S.get("sun"):                                  # a window's direct light: sharp shadows, from "from"
    su = S["sun"]
    sd = bpy.data.lights.new("sun", "SUN")
    sd.energy, sd.angle = su.get("strength", 3.0), math.radians(su.get("angle", 3.0))
    sd.color = su.get("color", (1.0, 0.97, 0.92))
    so = bpy.data.objects.new("sun", sd)
    sc.collection.objects.link(so)
    so.rotation_euler = (-mathutils.Vector(su["from"])).to_track_quat("-Z", "Y").to_euler()
RAW = os.environ.get("PK_EXR")                    # a linear EXR, no lens effects: workspace_grade.py grades it
if S.get("post") and not RAW:                     # the lens: a vignette, a soft glow round bright pixels
    po = S["post"]
    sc.use_nodes = True
    ct = sc.node_tree
    ct.nodes.clear()
    rl = ct.nodes.new("CompositorNodeRLayers")
    comp = ct.nodes.new("CompositorNodeComposite")
    last = rl.outputs["Image"]
    if po.get("glare"):
        gl = ct.nodes.new("CompositorNodeGlare")
        gl.glare_type, gl.quality, gl.threshold, gl.mix = "FOG_GLOW", "HIGH", 1.0, -1 + po["glare"]
        ct.links.new(last, gl.inputs["Image"])
        last = gl.outputs["Image"]
    if po.get("vignette"):
        el = ct.nodes.new("CompositorNodeEllipseMask")
        el.width, el.height = 0.95, 0.95
        bl = ct.nodes.new("CompositorNodeBlur")
        bl.filter_type, bl.use_relative = "FAST_GAUSS", True
        bl.factor_x = bl.factor_y = 40
        ct.links.new(el.outputs["Mask"], bl.inputs["Image"])
        mr = ct.nodes.new("CompositorNodeMapRange")
        mr.inputs["To Min"].default_value = 1.0 - po["vignette"]
        ct.links.new(bl.outputs["Image"], mr.inputs["Value"])
        mx = ct.nodes.new("CompositorNodeMixRGB")
        mx.blend_type = "MULTIPLY"
        ct.links.new(last, mx.inputs[1])
        ct.links.new(mr.outputs["Value"], mx.inputs[2])
        last = mx.outputs["Image"]
    if po.get("sat", 1.0) != 1.0:
        hs = ct.nodes.new("CompositorNodeHueSat")
        hs.inputs["Saturation"].default_value = po["sat"]
        ct.links.new(last, hs.inputs["Image"])
        last = hs.outputs["Image"]
    ct.links.new(last, comp.inputs["Image"])
sc.cycles.samples = SAMPLES
sc.render.resolution_x, sc.render.resolution_y = WIDTH, int(round(WIDTH * 9 / 16 / 2)) * 2
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
if RAW:
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
sc.render.filepath = os.path.abspath(OUT)
print(f"WORKSPACE {NAME}: desk top {top:.3f} m, keyboard {S['kb_from_front']} m from the front, "
      f"{len(S['props'])} props, rendering {sc.render.resolution_x} x {sc.render.resolution_y}")
if os.environ.get("PK_NO_RENDER"):                # build only, for a script after this one (a check view)
    print("BUILT", NAME)
else:
    bpy.ops.render.render(write_still=True)
    print("SAVED", OUT)
