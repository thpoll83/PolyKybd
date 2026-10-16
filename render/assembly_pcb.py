"""The assembly scene's board and soldered parts from pcb2blender, as on the PCB shot.

    PCB2BLENDER=<checkout> blender-5.1 -b --python render/assembly_pcb.py -- \
        render/out/assembly.blend render/out/pcb_left.blend render/out/left.pcb3d render/out/assembly_pcb.blend

assembly_scene.py's board ("PCB:pcb") and its components and hot-swap sockets come
from the VRML, which flattens the board's layers into flat colour. This replaces them
with pcb_shot's board: pcb2blender's import of the same half (pcb_shot/import.py),
given pcb_shot/look.py's look (the Rev.2 colours, the purple mask, the flex slots,
the hot-swap solder). The board is parented to the half's root in its frame, and
each component carries pk_ref (its KiCad reference, from <pcb3d>.parts.json),
pk_kind, pk_side and pk_unit (0.001: it moves in metres, the root's parts in mm).
The solder joints stay on the board: paste on the pads before the parts come. It
also gives the RGB LEDs the XL-3030's size and matte white, adds the spacer (not on
the board) and swaps the keycap stems for today's (render/models/).
Needs Blender 5.1 (pcb2blender's importer), with the add-on registered before the
scenes open, or its materials render white.
"""
import json
import os
import sys

import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:]
scene, pcb_blend, pcb3d, out = argv
sys.path.insert(0, os.environ.get("PCB2BLENDER", "/tmp/pcb2blender"))
sys.path.insert(0, os.path.join(HERE, "pcb_shot"))
sys.path.insert(0, HERE)
import pcb2blender_importer  # noqa: E402

pcb2blender_importer.register()
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(scene))
import look  # noqa: E402

root = bpy.data.objects["split72_left.wrl"]
CX, CY = 120.408, 93.556          # assembly_parts.fit() on the left half: root mm = (x - CX, -(y - CY))
with bpy.data.libraries.load(os.path.abspath(pcb_blend), link=False) as (src, dst):
    dst.objects = list(src.objects)
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
bpy.context.view_layer.update()                     # world matrices of the appended objects, for the slot fit
pcb = next(o for o in dst.objects if o.name.startswith("PCB_") and o.parent is None)
board, ox, oy = look.prepare(pcb, os.path.abspath(pcb3d))
print("board", board.name, "pad offset", round(ox, 6), round(oy, 6))

# the board's local metres -> the root's mm: x = (lx - ox) * 1000 - CX, y = (ly - oy) * 1000 + CY
old = {o["pk_ref"]: o for o in root.children if o.get("pk_kind") in ("comp", "socket")}
check = {r: o.matrix_world.translation.copy() for r, o in old.items()}
pcb.parent = root
pcb.matrix_parent_inverse.identity()
pcb.rotation_euler = (0, 0, 0)
pcb.scale = (1000.0,) * 3
pcb.location = (-ox * 1000 - CX, -oy * 1000 + CY, 0.0)
pcb["pk_kind"], pcb["pk_ref"], pcb["pk_side"], pcb["pk_lib"] = "pcb", "PCB", 1, "PCB"
pcb["pk_x"], pcb["pk_y"] = 0.0, 0.0
bpy.context.view_layer.update()

parts = json.load(open(os.path.splitext(os.path.abspath(pcb3d))[0] + ".parts.json"))
refs = list(parts)
P = np.array([parts[r]["position"] for r in refs])                     # KiCad mm
back = np.array([parts[r]["back"] for r in refs])
named, worst = 0, 0.0
for o in pcb.children:
    if o.type != "MESH" or o.name.startswith(("SOLDER_", "mark ")):
        continue
    lx, ly, lz = o.location
    x, y = (lx - ox) * 1000, -(ly - oy) * 1000
    d = np.hypot(P[:, 0] - x, P[:, 1] - y)
    j = int(d.argmin())
    worst = max(worst, float(d[j]))
    ref, p = refs[j], parts[refs[j]]
    kind = "socket" if p["footprint"].startswith("Kailh_socket") else "comp"
    o["pk_ref"], o["pk_kind"], o["pk_lib"] = ref, kind, p["footprint"]
    # the side from where the part IS, not from its origin: a hot-swap socket's origin sits
    # on the front copper while its body hangs below the board
    zc = sum((o.matrix_local @ mathutils.Vector(c)).z for c in o.bound_box) / 8
    o["pk_side"] = 1 if zc > 0 else -1
    o["pk_x"], o["pk_y"] = x - CX, -(y - CY)
    o["pk_unit"] = 0.001
    named += 1
print("named", named, "parts; worst distance to its footprint %.2f mm" % worst)

# the same parts in both scenes should sit within a part's size of each other
errs = []
for o in pcb.children:
    r = o.get("pk_ref")
    if r in check and o.get("pk_kind") == "comp":
        errs.append((o.matrix_world.translation - check[r]).xy.length * 1000)
if errs:
    print("against the VRML parts: median %.2f mm, 90%% %.2f mm (n=%d)" % (np.median(errs), np.percentile(errs, 90), len(errs)))
bpy.data.batch_remove([o for o in root.children if o.get("pk_kind") in ("pcb", "comp", "socket") and o is not pcb])


# ---- the RGB LEDs: the board carries a stand-in (KiCad's PLCC4, 3.5 x 2.8 x 2.05 mm,
# metal) for the XL-3030RGBC, a matte white 3.0 x 3.0 x 0.8 mm package with a round
# clear window over the die. One mesh for all 36: a body with 0.12 mm rounded edges
# (so its outline catches the light) and a glossy lens disc just proud of its top.
import bmesh  # noqa: E402


def principled(name, rgb, rough, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    return m


led_body = principled("XL-3030 body", (0.62, 0.62, 0.60), 0.55)
led_lens = principled("XL-3030 lens", (0.42, 0.40, 0.34), 0.12, coat=0.6)
leds = [o for o in pcb.children if str(o.get("pk_lib", "")).startswith("XL-3030")]
if leds:
    bm = bmesh.new()
    mm = 1e-3
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = mathutils.Vector((v.co.x * 3.0 * mm, v.co.y * 3.0 * mm, (v.co.z + 0.5) * 0.8 * mm))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.12 * mm, segments=2, affect="EDGES", profile=0.5)
    for fc in bm.faces:
        fc.material_index = 0
    lens = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=1.1 * mm, radius2=1.1 * mm, depth=0.04 * mm)
    for v in lens["verts"]:
        v.co.z += 0.80 * mm
    for fc in {f for v in lens["verts"] for f in v.link_faces}:
        fc.material_index = 1
    me = bpy.data.meshes.new("XL-3030")
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(led_body)
    me.materials.append(led_lens)
    flip = 0
    for o in leds:
        lo = min(mathutils.Vector(c).z for c in o.bound_box)
        hi = max(mathutils.Vector(c).z for c in o.bound_box)
        o.data = me
        o.scale = (1.0, 1.0, 1.0)
        if abs(hi) < abs(lo):                     # the stand-in stood on its +z face: the top is -z
            o.scale = (1.0, 1.0, -1.0)
            flip += 1
    print("LEDs rebuilt as 3.0 x 3.0 x 0.8 mm with a lens:", len(leds), "flipped", flip)


def read_stl(path):
    import struct
    b = open(path, "rb").read()
    if b[:5] == b"solid" and b"facet" in b[:400]:          # ASCII (the diffuser-frame group)
        v = [float(x) for line in b.decode().splitlines() if line.strip().startswith("vertex")
             for x in line.split()[1:4]]
        return np.array(v).reshape(-1, 3, 3)
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def mesh_from_tris(name, tris, material):
    v = tris.reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], np.arange(len(v)).reshape(-1, 3).tolist())
    me.update()
    me.materials.append(material)
    return me


def local_verts(o):
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    m = np.array(o.matrix_local)
    return co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]


def nn_score(a, b, n=400):
    """Mean distance from a sample of a to its nearest point of b (mm)."""
    rng = np.random.default_rng(1)
    a = a[rng.choice(len(a), min(n, len(a)), replace=False)]
    b = b[rng.choice(len(b), min(4000, len(b)), replace=False)]
    return float(np.sqrt(((a[:, None] - b[None]) ** 2).sum(-1)).min(1).mean())


case_pla = next(m for m in bpy.data.materials if m.get("pk_role") == "case PLA")

# ---- the spacer (parts/export/case/spacer_diffuser_frame.stl, the one for a board
# with the diffuser frame): not on the board, so placed here on the PCB's top face,
# its outline fitted onto the plate's (both are the board outline); one part serves
# both halves, mirrored or not
plate = next(o for o in root.children if o.get("pk_kind") == "plate")
pv = local_verts(plate)
tris = read_stl(os.path.join(HERE, "..", "parts", "export", "case", "spacer_diffuser_frame.stl"))
best = None
for mirror in (1, -1):
    t = tris * np.array([mirror, 1, 1])
    v = t.reshape(-1, 3)
    shift = (pv[:, :2].min(0) + pv[:, :2].max(0)) / 2 - (v[:, :2].min(0) + v[:, :2].max(0)) / 2
    shift = np.array([shift[0], shift[1], 0.8 - v[:, 2].min()])     # on the PCB's top face
    sc_ = nn_score((v + shift)[:, :2], pv[:, :2])
    if best is None or sc_ < best[0]:
        best = (sc_, mirror, t + shift)
score, mirror, t = best
if mirror < 0:
    t = t[:, ::-1]                                                  # keep the faces wound outward
c = (t.reshape(-1, 3).min(0) + t.reshape(-1, 3).max(0)) / 2
spacer = bpy.data.objects.new("SPACER:spacer", mesh_from_tris("spacer", t - c, case_pla))
bpy.context.scene.collection.objects.link(spacer)
spacer.parent = root
spacer.location = tuple(c)
for k, v in dict(pk_kind="spacer", pk_ref="SPACER", pk_side=1, pk_lib="spacer", pk_x=float(c[0]), pk_y=float(c[1])).items():
    spacer[k] = v
print("spacer: %s, outline %.2f mm from the plate's, z %.1f..%.1f mm"
      % ("mirrored" if mirror < 0 else "as exported", score, t[..., 2].min(), t[..., 2].max()))

# ---- the keycap stems: today's (render/models/, engraved as printed now) in place of
# the board's keycap_stem_r7*.wrl. The stem's frame onto the board's is found on one
# key by trying the 24 axis-aligned turns; then each key turns that by its own angle.
import itertools
new = {u: read_stl(os.path.join(HERE, "models", f"keycap_stem_R3_{u}.stl")) for u in ("1U", "1U25")}
turns = []
for perm in itertools.permutations(range(3)):
    for signs in itertools.product((1, -1), repeat=3):
        R = np.zeros((3, 3))
        for i, (j, s_) in enumerate(zip(perm, signs)):
            R[i, j] = s_
        if np.linalg.det(R) > 0:
            turns.append(R)
stems = [o for o in root.children if o.get("pk_kind") == "kstem"]


def placed(tris, R, ov):
    v = tris.reshape(-1, 3) @ R.T
    return v + ((ov.min(0) + ov.max(0)) / 2 - (v.min(0) + v.max(0)) / 2)


def rz(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])


import assembly_parts as ap
rot = {f["ref"]: f["rot"] for f in ap.footprints(os.path.join(HERE, "..", "poly_kybd", "poly_kybd_split72_left.kicad_pcb"))}
ref_key = next(o for o in stems if abs(rot.get(o["pk_ref"], 0)) < 1e-6)
ov = local_verts(ref_key)
u = "1U25" if np.ptp(ov[:, 0]) > 17.5 or np.ptp(ov[:, 1]) > 17.5 else "1U"
B = min(turns, key=lambda R: nn_score(placed(new[u], R, ov), ov))
print("stem frame fitted on", ref_key["pk_ref"], "%.3f mm" % nn_score(placed(new[u], B, ov), ov))
worst = 0.0
for o in stems:
    ov = local_verts(o)
    u = "1U25" if max(np.ptp(ov[:, 0]), np.ptp(ov[:, 1])) > 17.5 else "1U"
    a = rot.get(o["pk_ref"], 0.0)
    cands = [placed(new[u], rz(sg * a) @ B, ov) for sg in ((1, -1) if a else (1,))]
    scores = [nn_score(c_, ov) for c_ in cands]
    v = cands[int(np.argmin(scores))]
    worst = max(worst, min(scores))
    mats = list(o.data.materials)
    old_me = o.data
    me = mesh_from_tris(o.name, (v - np.array(o.location)).reshape(-1, 3, 3), mats[0])
    o.data = me
    bpy.data.meshes.remove(old_me)
print("stems replaced:", len(stems), "worst fit %.3f mm" % worst)

# ---- the flex cables, one per key by connection: assembly_scene.py split the textured
# flex mesh by each face's nearest key, which cut every loop under the board at the
# halfway line between keys (SW_K_10's own end, into J10, went to the key behind it,
# and it took the end of the key in front's). Weld the pieces, take each connected
# strip whole and give it to the key whose slot it comes down through (its top end).
flex = [o for o in root.children if o.get("pk_kind") == "flex"]
bm = bmesh.new()
for o in flex:
    me = o.data.copy()
    me.transform(o.matrix_basis)                  # into the root's frame (mm)
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bm.faces.ensure_lookup_table()
island = [-1] * len(bm.faces)
n_isl = 0
for f0 in bm.faces:
    if island[f0.index] >= 0:
        continue
    stack = [f0]
    island[f0.index] = n_isl
    while stack:
        fc = stack.pop()
        for e in fc.edges:
            for g in e.link_faces:
                if island[g.index] < 0:
                    island[g.index] = n_isl
                    stack.append(g)
    n_isl += 1
keys = np.array([(o["pk_x"], o["pk_y"]) for o in flex])
owner = {}
for i in range(n_isl):
    top = max((v for fc in bm.faces if island[fc.index] == i for v in fc.verts), key=lambda v: v.co.z)
    owner[i] = int(np.argmin(((keys - np.array(top.co[:2])) ** 2).sum(1)))
counts = np.bincount(list(owner.values()), minlength=len(flex))
print("flex strips:", n_isl, "for", len(flex), "keys; strips per key", sorted(set(counts.tolist())))
for j, o in enumerate(flex):
    mine = {i for i, k in owner.items() if k == j}
    b2 = bm.copy()
    b2.faces.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[fc for fc in b2.faces if island[fc.index] not in mine], context="FACES")
    lo = mathutils.Vector([min(v.co[i] for v in b2.verts) for i in range(3)])
    hi = mathutils.Vector([max(v.co[i] for v in b2.verts) for i in range(3)])
    c = (lo + hi) / 2
    bmesh.ops.translate(b2, verts=b2.verts, vec=-c)
    me = o.data
    b2.to_mesh(me)
    b2.free()
    o.matrix_basis = mathutils.Matrix.Translation(c)
bm.free()
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out), compress=True)
print("SAVED", out)
