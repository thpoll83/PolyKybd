"""Export a saved scene (blender_scene.py / key_scene.py .blend) as a web GLB.

    blender -b scene.blend --python render/export_web.py -- out.glb [max_tris] [art_px] [art_strength]

For <model-viewer> on the web page: keeps the materials as glTF PBR (the caps'
transmission becomes KHR_materials_transmission, the plate stays metallic, the
display and flex keep their textures) and simplifies the geometry until the
whole scene is under `max_tris` (default 120k) triangles:
0. the plate's Rosetta artwork (silkscreen geometry, ~650k triangles a
   plate) is drawn into one texture on the plate's top face and the geometry
   dropped; the main board's silkscreen, under the plate, is dropped,
   then untextured meshes joined per material (see meshmerge.py),
1. a planar dissolve on every mesh (lossless for the flat silkscreen art and
   the board, which are most of the triangles),
2. then a collapse decimate on the meshes still above their share.
Floor, lights and camera are not exported. No mesh compression: the artifact
viewer cannot fetch the Draco or meshopt decoders, so the budget is the size
control (about 30 bytes per triangle).
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshmerge import merge_by_material  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
budget = int(argv[1]) if len(argv) > 1 else 120_000
art_px = int(argv[2]) if len(argv) > 2 else 1536
art_strength = float(argv[3]) if len(argv) > 3 else 0.5


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.name not in ("Plane", "floor")]
for o in [o for o in bpy.context.scene.objects if o.type in ("LIGHT", "CAMERA") or o.name in ("Plane", "floor")]:
    o.hide_render = True
before = sum(tris(o) for o in meshes)

PLATE_SILK = (0.961, 0.961, 0.961)      # gen_plates.py keeps KiCad's white silk (the sockets are 0.961/0.965)
BOARD_SILK = (0.824, 0.820, 0.781)      # the main boards' silkscreen colour in the export


def colour(o):
    m = o.active_material
    if not m or not m.use_nodes or "Principled BSDF" not in m.node_tree.nodes:
        return None
    return tuple(m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3])


def near(c, ref, tol=0.004):
    return c is not None and all(abs(a - b) <= tol for a, b in zip(c, ref))


def bake_plate_art(meshes):
    """Rasterise the plate silkscreen into a texture on the plate, drop it.

    The silk sits on the plate top. The KiCad export also gives the hotswap
    sockets the same white, so only faces within 0.15 mm of a plate top count."""
    import bmesh
    import numpy as np
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise SystemExit("export_web.py needs Pillow in Blender's Python: "
                         "<blender>/<version>/python/bin/python3.* -m pip install pillow")
    plates = [o for o in meshes if o.active_material and o.active_material.get("pk_role") == "plate aluminium"]
    silk = [o for o in meshes if near(colour(o), PLATE_SILK)]
    for plate in plates:
        pw = np.array([plate.matrix_world @ v.co for v in plate.data.vertices])
        top = pw[:, 2].max()
        lo, hi = pw[:, :2].min(0), pw[:, :2].max(0)
        span = hi - lo
        w = art_px
        h = max(1, int(w * span[1] / span[0]))
        img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(img)
        drawn = 0
        for o in silk:
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bm.transform(o.matrix_world)
            kill = []
            for f in bm.faces:
                zs = [v.co.z for v in f.verts]
                xy = [(v.co.x, v.co.y) for v in f.verts]
                cx = sum(p[0] for p in xy) / len(xy)
                cy = sum(p[1] for p in xy) / len(xy)
                if abs(sum(zs) / len(zs) - top) < 0.00015 and lo[0] <= cx <= hi[0] and lo[1] <= cy <= hi[1]:
                    draw.polygon([((x - lo[0]) / span[0] * (w - 1), (1 - (y - lo[1]) / span[1]) * (h - 1))
                                  for x, y in xy], fill=255)
                    kill.append(f)
            drawn += len(kill)
            bmesh.ops.delete(bm, geom=kill, context="FACES")
            bm.transform(o.matrix_world.inverted())
            bm.to_mesh(o.data)
            bm.free()
        print(f"{plate.name}: {drawn} silkscreen faces drawn into a {w}x{h} texture")
        # the artwork is glyph text: at web size it reads as speckle, so it
        # is shown as a soft pattern instead: a third the resolution,
        # blurred, at `art_strength` of full silk
        from PIL import ImageFilter
        img = img.resize((max(1, w // 3), max(1, h // 3)), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.2))
        img = img.point(lambda v: int(v * art_strength))
        path = os.path.join(os.path.dirname(out) or ".", f"_art_{plate.name}.png")
        img.save(path)
        # texture the plate: aluminium where the mask is 0, white silk where 255,
        # planar uv over the plate's world-space footprint
        me = plate.data
        uv = me.uv_layers.new(name="art")
        co = np.array([plate.matrix_world @ v.co for v in me.vertices])
        loops = np.empty(len(me.loops), dtype=np.int32)
        me.loops.foreach_get("vertex_index", loops)
        uvs = np.column_stack([(co[loops, 0] - lo[0]) / span[0], (co[loops, 1] - lo[1]) / span[1]])
        uv.data.foreach_set("uv", uvs.astype(np.float32).ravel())
        mat = plate.active_material.copy()
        mat.name = plate.name + " art"
        plate.data.materials.clear()
        plate.data.materials.append(mat)
        nt = mat.node_tree
        b = nt.nodes["Principled BSDF"]
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(path)
        tex.image.colorspace_settings.name = "Non-Color"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["A"].default_value = b.inputs["Base Color"].default_value
        mix.inputs["B"].default_value = (0.92, 0.92, 0.9, 1)
        nt.links.new(tex.outputs["Color"], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
        # silk is not metal: metallic follows the inverse mask
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(tex.outputs["Color"], inv.inputs[1])
        nt.links.new(inv.outputs[0], b.inputs["Metallic"])
    gone = {o.name for o in meshes if near(colour(o), BOARD_SILK)}
    # take the names first: reading a removed object raises ReferenceError
    keep = [o.name for o in meshes if o.name not in gone]
    for name in gone:
        bpy.data.objects.remove(bpy.data.objects[name])
    return [bpy.data.objects[n] for n in keep]


meshes = bake_plate_art(meshes)
# join the untextured meshes per material (the single-key scene has ~2000
# small objects; the full scene is already merged). The textured decals and
# flex cables keep their own objects, since the merge drops uv.
textured = [o for o in meshes if o.data.uv_layers]
meshes = merge_by_material([o for o in meshes if not o.data.uv_layers]) + textured
print(f"merged into {len(meshes)} objects")


def apply_mod(o, kind, **kw):
    m = o.modifiers.new(kind, "DECIMATE")
    m.decimate_type = kind
    for k, v in kw.items():
        setattr(m, k, v)
    bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_apply(modifier=m.name)


for o in meshes:
    apply_mod(o, "DISSOLVE", angle_limit=math.radians(0.5), delimit={"MATERIAL", "UV"})
after_dissolve = sum(tris(o) for o in meshes)

total = after_dissolve
if total > budget:
    # shrink the big meshes proportionally; leave small ones (screws, decals) alone
    # the plates are left alone: collapsing them opens their switch holes
    # into slits that show the green board underneath
    big = [o for o in meshes if tris(o) > 2000 and not o.name.endswith(" art")
           and not (o.active_material and o.active_material.name.endswith(" art"))]
    small = total - sum(tris(o) for o in big)
    ratio = max(0.002, (budget - small) / max(1, total - small))
    for o in big:
        apply_mod(o, "COLLAPSE", ratio=ratio, use_collapse_triangulate=True)
final = sum(tris(o) for o in meshes)
print(f"triangles: {before} -> {after_dissolve} after planar dissolve -> {final}")
for o in sorted(meshes, key=tris, reverse=True)[:8]:
    print(f"  {o.name}: {tris(o)}")

bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True,
                          export_apply=True, export_yup=True, export_image_format="AUTO",
                          export_draco_mesh_compression_enable=False)
print("wrote", out)
