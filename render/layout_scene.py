"""A test render of a keyboard layout that has no KiCad board yet.

    blender -b --python render/layout_scene.py -- LAYOUT_KEYS.json LEGENDS.png out.png \
        [samples] [width] [joined|apart] [elevation_deg]

LAYOUT_KEYS.json and LEGENDS.png come from docs/layout_study/export_layout_e.py.
Every key is a copy of the real 1U key (SW_K_2: switch, socket, display carrier, display,
flex cable, outer cap) as key_scene.py imports it. For a wider key the walls of the outer
cap and of the display carrier move out in x (vertices beyond STRETCH_FROM), so the
corner radii, the display pocket and the stem hole stay as they are; the display stays
1U, centred. Each display shows its legend from LEGENDS.png
(one 72x40 cell per key). The case and plate are plain extrusions of each half's outline,
flush at the split line: the plate (z 3.4 to 5.0 mm, like the real one, no switch holes)
PLATE_MARGIN wider than the keys on the outer edges, the case 4 mm wider than the plate.

`joined` renders the halves touching; `apart` moves the right half 60 mm away and
turns each half 8 degrees. Saves out.blend next to the PNG.

PK_PLATE_ART=mask.png renders the plate as a PCB: black solder mask with the mask image
(white = silkscreen, exported by docs/layout_study/plate_trace_tool.html) on top.
"""
import json
import math
import os
import sys

import addon_utils
import bmesh
import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import key_scene  # noqa: E402
import keymatch  # noqa: E402
import materials  # noqa: E402
import screens  # noqa: E402
import textured_parts  # noqa: E402
from meshmerge import merge_by_material  # noqa: E402

U = 19.05
PLATE_MARGIN = 5.0                     # mm of plate outside the keys on the outer edges
CASE_MARGIN = PLATE_MARGIN + 4.0       # the case rim is 4 mm wide around the plate
CASE_Z0, CASE_Z1 = -9.0, 3.4           # case body; the plate sits on it
PLATE_Z0, PLATE_Z1 = 3.4, 5.0
STRETCH = ("outercap", "keycap_stem")  # model files that grow with the key width
# Only vertices this far from the key centre move when a part is stretched: the cap and
# carrier walls (6.5 to 9 mm) move out, the display pocket (+-6.04 mm) and the MX stem
# hole stay 1:1 in the middle.
STRETCH_FROM = 6.5

argv = sys.argv[sys.argv.index("--") + 1:]
keys_path, legends_path, out = (os.path.abspath(a) for a in argv[:3])
samples = int(argv[3]) if len(argv) > 3 else 32
width = int(argv[4]) if len(argv) > 4 else 1600
mode = argv[5] if len(argv) > 5 else "joined"
elev = float(argv[6]) if len(argv) > 6 else 32.0

data = json.load(open(keys_path, encoding="utf-8"))
KEYS, CUT = data["keys"], data["cut"]
CW, CH = data["cell"]
ROWS = "ntcsb"
W = max(k["x"] + k["w"] for k in KEYS)           # layout width in U
NROWS = max(k["row"] for k in KEYS) + 1


def template():
    """The 1U key at the origin, textured, merged to a few meshes per material.

    The VRML importer makes hundreds of objects per key; copying those 72 times
    kept Blender busy for more than 10 minutes before the render started."""
    root = bpy.data.objects.new("key template", None)
    bpy.context.scene.collection.objects.link(root)
    for path, off, scale, rot in key_scene.key_models():
        key_scene.import_model(path, off, scale, rot).parent = root
    materials.tag(bpy)
    textured_parts.add(root, [(0.0, 0.0, 0.0)])
    bpy.context.view_layer.update()

    def grows(o):
        while o.parent and o.parent != root:
            o = o.parent
        return o.name.startswith(STRETCH)
    textured = [o for o in root.children if o.type == "MESH"]      # decal + flex, with uv
    parts = [o for o in root.children_recursive if o.type == "MESH" and o not in textured]
    out = textured[:]
    groups = {True: [], False: []}
    for o in parts:
        groups[grows(o)].append(o)
    for flag, objs in groups.items():
        for m in merge_by_material(objs):
            m["pk_stretch"] = flag
            out.append(m)
    for o in [o for o in root.children_recursive if o.type != "MESH"]:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in out:
        o.parent = root
    return root, out


def stretched(obj, extra, cache):
    """obj's mesh (in the key's frame) with its outer vertices moved +-extra/2 mm in x."""
    key = (obj.data.name, extra)
    if key not in cache:
        me = obj.data.copy()
        co = np.empty(len(me.vertices) * 3, dtype=np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        outer = np.abs(co[:, 0]) > STRETCH_FROM
        co[outer, 0] += np.sign(co[outer, 0]) * extra / 2
        me.vertices.foreach_set("co", co.ravel())
        me.update()
        cache[key] = me
    return cache[key]


def outline(half, margin):
    """Polygon (mm, y up) of one half: the cut is a staircase, outer edges get `margin`."""
    stairs = []
    for i, r in enumerate(ROWS[:NROWS]):
        x = CUT[r] * U
        y0 = -i * U + (margin if i == 0 else 0)
        y1 = -(i + 1) * U - (margin if i == NROWS - 1 else 0)
        stairs += [(x, y0), (x, y1)]
    if half == "left":
        pts = [(-margin, margin)] + stairs + [(-margin, -NROWS * U - margin)]
    else:
        xr = W * U + margin
        pts = [(xr, margin), (xr, -NROWS * U - margin)] + stairs[::-1]
    # drop repeated points where two rows share a cut x
    clean = []
    for p in pts:
        if not clean or (abs(clean[-1][0] - p[0]) > 1e-6 or abs(clean[-1][1] - p[1]) > 1e-6):
            clean.append(p)
    return clean


def prism(name, poly, z0, z1, rgb, parent, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in poly]
    f = bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=[f])
    if f.normal.z > 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z = z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    if bevel:
        mod = ob.modifiers.new("bevel", "BEVEL")
        mod.width, mod.segments, mod.limit_method = bevel, 3, "ANGLE"
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    me.materials.append(mat)
    return ob


def plate_art_material(path):
    """Black solder mask with the mask image (white = silkscreen) on the plate top.

    The image covers the plate from its top-left corner (-PLATE_MARGIN, +PLATE_MARGIN in
    the key frame, y up) to the bottom-right, the way docs/layout_study/plate_trace_tool.html
    exports it; object coordinates (mm) are mapped onto it directly."""
    pw, ph = W * U + 2 * PLATE_MARGIN, NROWS * U + 2 * PLATE_MARGIN
    m = bpy.data.materials.new("plate art")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / pw, 1 / ph, 1)
    mp.inputs["Location"].default_value = (PLATE_MARGIN / pw, (NROWS * U + PLATE_MARGIN) / ph, 0)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"
    tex.extension = "CLIP"
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    col = nt.nodes.new("ShaderNodeMix")
    col.data_type = "RGBA"
    a_in, b_in = [i for i in col.inputs if i.type == "RGBA"]
    a_in.default_value = (0.010, 0.011, 0.013, 1)        # black solder mask
    b_in.default_value = (0.80, 0.78, 0.72, 1)           # white silkscreen
    nt.links.new(tex.outputs["Color"], col.inputs["Factor"])
    nt.links.new(next(o for o in col.outputs if o.type == "RGBA"), b.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")           # glossy mask, matte silk
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = 0.22, 0.65
    nt.links.new(tex.outputs["Color"], rough.inputs["Value"])
    nt.links.new(rough.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = 0.3
    return m


def legend_mesh(half_keys, parent, t, dz, mat):
    X, Y0, Y1 = textured_parts.DISP_X, textured_parts.DISP_Y0, textured_parts.DISP_Y1
    z = textured_parts.DISP_TOP + dz + screens.LIFT
    aw = CW * len(KEYS)
    verts, tris, uv = [], [], []
    for k, (cx, cy) in half_keys:
        def corner(fu, fv):
            return (-X + 2 * X * fu + t[0] + cx, Y0 + (Y1 - Y0) * fv + t[1] + cy, z)
        b = len(verts)
        verts += [corner(keymatch.A_U0, keymatch.A_V1), corner(keymatch.A_U1, keymatch.A_V1),
                  corner(keymatch.A_U1, keymatch.A_V0), corner(keymatch.A_U0, keymatch.A_V0)]
        tris += [(b, b + 3, b + 2), (b, b + 2, b + 1)]
        u0, u1 = k["cell"] * CW / aw, (k["cell"] + 1) * CW / aw
        uv += [(u0, 1), (u1, 1), (u1, 0), (u0, 0)]
    return textured_parts._mesh("legends", verts, tris, uv, mat, parent)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("io_scene_x3d")
    sc = bpy.context.scene
    troot, tparts = template()
    (tx, ty), dz = textured_parts.fit(troot, [(0.0, 0.0, 0.0)])

    board = bpy.data.objects.new("board", None)
    sc.collection.objects.link(board)
    halves = {}
    for h in ("left", "right"):
        e = bpy.data.objects.new(h, None)
        sc.collection.objects.link(e)
        e.parent = board
        halves[h] = e

    legend_mat = screens._material("lit legends", legends_path, 6.0)
    cache = {}
    placed = {"left": [], "right": []}
    for k in KEYS:
        cx = (k["x"] + k["w"] / 2) * U
        cy = -(k["row"] + 0.5) * U
        anchor = bpy.data.objects.new(f"key {k['label']}", None)
        sc.collection.objects.link(anchor)
        anchor.parent = halves[k["half"]]
        anchor.location = (cx, cy, 0)
        for o in tparts:
            c = o.copy()
            sc.collection.objects.link(c)
            c.parent = anchor
            if o.get("pk_stretch") and k["w"] != 1:
                c.data = stretched(o, (k["w"] - 1) * U, cache)
        placed[k["half"]].append((k, (cx, cy)))
    for h in ("left", "right"):
        legend_mesh(placed[h], halves[h], (tx, ty), dz, legend_mat)
        prism(f"case {h}", outline(h, CASE_MARGIN), CASE_Z0, CASE_Z1, (0.35, 0.35, 0.37), halves[h], 1.2)
        prism(f"plate {h}", outline(h, PLATE_MARGIN), PLATE_Z0, PLATE_Z1, (0.58, 0.59, 0.61), halves[h], 0.4)
    # remove the template and its parts; only the board stays at the top level
    for o in list(troot.children_recursive) + [troot]:
        bpy.data.objects.remove(o, do_unlink=True)

    materials.tag(bpy)
    print("material roles", materials.apply(bpy))
    # PK_PLATE_ART=mask.png: a PCB plate (black mask, silkscreen art) instead of aluminium.
    # Set after materials.apply(), which would otherwise re-style it by its colour.
    art = os.environ.get("PK_PLATE_ART")
    if art:
        pm = plate_art_material(os.path.abspath(art))
        for h in ("left", "right"):
            bpy.data.objects[f"plate {h}"].data.materials[0] = pm

    # centre the board, then split the halves for `apart`
    board.location = (-W * U / 2 * 0.001, NROWS * U / 2 * 0.001, 0)   # metres, the board scale is mm
    if mode == "apart":
        gap, turn = 60.0, 8.0
        for h, sign in (("left", -1), ("right", 1)):
            e = halves[h]
            # rotate each half about its inner bottom corner
            pivot = mathutils.Vector((CUT["b"] * U, -NROWS * U, 0))
            rot = mathutils.Matrix.Rotation(math.radians(sign * -turn), 4, "Z")
            e.matrix_local = (mathutils.Matrix.Translation(pivot + mathutils.Vector((sign * gap / 2, 0, 0)))
                              @ rot @ mathutils.Matrix.Translation(-pivot))
    board.scale = (0.001,) * 3

    floor = bpy.data.objects.new("floor", bpy.data.meshes.new("floor"))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2.0)
    bm.to_mesh(floor.data)
    sc.collection.objects.link(floor)
    floor.location = (0, 0, CASE_Z0 * 0.001)
    fm = bpy.data.materials.new("floor")
    fm.use_nodes = True
    fb = fm.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
    fb.inputs["Roughness"].default_value = 0.3
    floor.data.materials.append(fm)

    tgt = bpy.data.objects.new("target", None)
    tgt.location = (0, 0.005, 0.0)
    sc.collection.objects.link(tgt)

    import lighting
    import studio
    lighting.studio(sc, tgt)            # the hero scene's lights
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.025, 1)

    cd = bpy.data.cameras.new("cam")
    cd.lens = 50
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    dist = 0.50 if mode == "joined" else 0.58
    e_ = math.radians(elev)
    cam.location = (0.0, -dist * math.cos(e_), dist * math.sin(e_))
    cam.constraints.new("TRACK_TO").target = tgt
    bpy.context.view_layer.update()
    studio.flag(sc)                     # black card in the caps' mirror direction

    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    materials.scene_settings(sc)
    sc.render.resolution_x, sc.render.resolution_y = width, int(width * 9 / 16)
    sc.render.filepath = out
    sc.view_settings.view_transform = "AgX"
    bpy.ops.wm.save_as_mainfile(filepath=out.rsplit(".", 1)[0] + ".blend", compress=True)
    bpy.ops.render.render(write_still=True)


main()
