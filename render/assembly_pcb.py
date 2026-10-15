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
# metal) for the XL-3030RGBC, a matte white 3.0 x 3.0 x 0.8 mm package
led_white = bpy.data.materials.new("XL-3030 body")
led_white.use_nodes = True
lb = led_white.node_tree.nodes["Principled BSDF"]
lb.inputs["Base Color"].default_value = (0.82, 0.82, 0.80, 1)
lb.inputs["Roughness"].default_value = 0.6
done = set()
leds = [o for o in pcb.children if str(o.get("pk_lib", "")).startswith("XL-3030")]
for o in leds:
    d = o.dimensions / o.scale.x if o.scale.x else o.dimensions      # metres, local axes
    o.scale = (3.0e-3 / d.x, 3.0e-3 / d.y, 0.8e-3 / d.z)              # its origin is on the board
    if o.data.name not in done:
        done.add(o.data.name)
        for i in range(len(o.data.materials)):
            o.data.materials[i] = led_white
print("LEDs resized and made matte white:", len(leds))


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
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out), compress=True)
print("SAVED", out)
