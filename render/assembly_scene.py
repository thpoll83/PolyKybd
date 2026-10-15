"""The assembly video's scene: hero.blend with its left half rebuilt as one object
per part, so each part can fly in on its own.

    blender -b render/out/hero.blend --python render/assembly_scene.py -- \
        render/out/split72_left.wrl render/out/assembly.blend

hero.blend holds the left half as ~25 meshes merged by material. This imports the
half's VRML again (about 10 minutes), gives every shape to its KiCad part
(assembly_parts.py) and builds one object per part and kind ("C12:comp",
"SW_K_7:switch", "SW_K_7:keycap", "PCB:pcb" ...), parented to the half's root in
the same frame, with its origin at its centre. Materials are hero.blend's own,
matched by role, else by colour. The display decals and textured flex cables
(textured_parts.py) are split per key the same way. The right half stays as it is.
Each object carries pk_ref, pk_kind and pk_side (+1 above the board, -1 below).
"""
import os
import sys
import time

import addon_utils
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assembly_parts as ap  # noqa: E402
import materials  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
wrl, out = argv[0], argv[1]
board = os.path.join(HERE, "..", "poly_kybd", "poly_kybd_split72_left.kicad_pcb")
root = bpy.data.objects["split72_left.wrl"]
old = [o for o in root.children_recursive if o.type == "MESH"]


def look(m):
    b = m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None
    return tuple(round(c, 3) for c in b.inputs["Base Color"].default_value[:3]) if b else None


# hero.blend's materials: by role, and the role-less ones by colour
by_role, by_look = {}, {}
for o in old:
    for m in o.data.materials:
        if m is None:
            continue
        r = m.get("pk_role") or ""
        if r:
            by_role.setdefault(r, m)
        else:
            by_look.setdefault(look(m), m)
print("hero materials:", sorted(by_role), len(by_look), "by colour")

addon_utils.enable("io_scene_x3d")
before = set(bpy.data.objects)
t0 = time.time()
bpy.ops.import_scene.x3d(filepath=wrl, axis_forward="Y", axis_up="Z")
new = [o for o in bpy.data.objects if o not in before]
print("imported", len(new), "in", round(time.time() - t0), "s")
bpy.context.view_layer.update()
meshes = [o for o in new if o.type == "MESH" and len(o.data.vertices) and len(o.data.polygons)]

# per shape: world vertices, its place, its role
verts, cen, lo, hi, roles, mats = [], [], [], [], [], []
for o in meshes:
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    mw = np.array(o.matrix_world, np.float32)
    w = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    verts.append(w)
    cen.append(w.mean(0)); lo.append(w.min(0)); hi.append(w.max(0))
    m = o.active_material
    b = m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None
    roles.append((materials.role_of(tuple(b.inputs["Base Color"].default_value[:3])) or "") if b else "")
    mats.append(m)
cen, lo, hi, roles = np.array(cen), np.array(lo), np.array(hi), np.array(roles)
fps = ap.footprints(board)
off = ap.fit(cen, roles, fps)
cls = ap.classify(cen, lo, hi, roles, fps, off)
print("fitted", np.round(off, 3), "classified in", round(time.time() - t0), "s")


def material_for(i):
    r = roles[i]
    if cls[i][1] == "lid" and "case PLA opaque" in by_role:
        return by_role["case PLA opaque"]
    if r and r in by_role:
        return by_role[r]
    return by_look.get(look(mats[i]), mats[i])


def build(name, pieces, props):
    """One object from [(world verts, loop vertex indices, loop totals, material)]:
    its origin at the centre, parented to the half's root (whose frame is the
    import's, in mm)."""
    allv = np.concatenate([p[0] for p in pieces])
    c = (allv.min(0) + allv.max(0)) / 2
    slots, vs, li, lt, mi, base = [], [], [], [], [], 0
    for v, l, t, m in pieces:
        if m not in slots:
            slots.append(m)
        vs.append(v - c); li.append(l + base); lt.append(t)
        mi.append(np.full(len(t), slots.index(m), np.int32))
        base += len(v)
    v, li, lt, mi = np.concatenate(vs), np.concatenate(li), np.concatenate(lt), np.concatenate(mi)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(v)); me.vertices.foreach_set("co", v.ravel())
    me.loops.add(len(li)); me.loops.foreach_set("vertex_index", li)
    me.polygons.add(len(lt))
    me.polygons.foreach_set("loop_start", np.concatenate(([0], np.cumsum(lt)[:-1])).astype(np.int32))
    me.polygons.foreach_set("loop_total", lt)
    me.update(calc_edges=True)
    for m in slots:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", mi)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = root
    ob.location = tuple(float(x) for x in c)
    for k, val in props.items():
        ob[k] = val
    return ob


groups = {}
for i, (g, k) in enumerate(cls):
    if g is not None:
        groups.setdefault((g, k), []).append(i)
fp_by_ref = {f["ref"]: f for f in fps}
made = 0
for (g, k), idx in groups.items():
    pieces = []
    for i in idx:
        me = meshes[i].data
        l = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", l)
        t = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_total", t)
        pieces.append((verts[i], l, t, material_for(i)))
    zc = float(np.mean([cen[i, 2] for i in idx]))
    f = fp_by_ref.get(g)
    build(f"{g}:{k}", pieces, dict(pk_ref=g, pk_kind=k, pk_side=1 if zc > 0 else -1,
                                   pk_lib=f["lib"] if f else g, pk_x=float(np.mean(cen[idx, 0])),
                                   pk_y=float(np.mean(cen[idx, 1]))))
    made += 1
print("built", made, "part objects in", round(time.time() - t0), "s")

# the decals and the textured flex cables: one piece per key, by face centre
keys = [(f["ref"], f["x"] - off[0], -(f["y"] - off[1])) for f in fps if ap.is_key(f)]
K = np.array([(x, y) for _, x, y in keys])
for o in old:
    kind = "display_decal" if o.name.endswith("display decals") else "flex" if o.name.endswith("flex cables") else None
    if kind is None:
        continue
    me = o.data
    v = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", v); v = v.reshape(-1, 3)
    l = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", l)
    t = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_total", t)
    st = np.empty(len(me.polygons), np.int32); me.polygons.foreach_get("loop_start", st)
    uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers[0].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    mw = np.array(o.matrix_basis, np.float32)          # its frame within the root
    v = v @ mw[:3, :3].T + mw[:3, 3]
    fc = np.array([v[l[s:s + n]].mean(0) for s, n in zip(st, t)])
    owner = np.sqrt(((fc[:, None, :2] - K[None]) ** 2).sum(-1)).argmin(1)
    for j, (ref, _, _) in enumerate(keys):
        faces = np.nonzero(owner == j)[0]
        if not len(faces):
            continue
        loops = np.concatenate([np.arange(st[f], st[f] + t[f]) for f in faces])
        used = np.unique(l[loops])
        remap = np.full(len(v), -1, np.int32); remap[used] = np.arange(len(used))
        ob = build(f"{ref}:{kind}", [(v[used], remap[l[loops]], t[faces], me.materials[0])],
                   dict(pk_ref=ref, pk_kind=kind, pk_side=1, pk_lib="key", pk_x=float(K[j, 0]), pk_y=float(K[j, 1])))
        lay = ob.data.uv_layers.new(name="uv")
        lay.data.foreach_set("uv", uv[loops].ravel())

bpy.data.batch_remove(new + old)
bpy.data.orphans_purge(do_recursive=True)
root["pk_assembly"] = True
print("parts:", len([o for o in root.children if o.get("pk_kind")]))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out), compress=True)
print("SAVED", out, round(time.time() - t0), "s")
