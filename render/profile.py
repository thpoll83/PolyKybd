"""Re-pose the keycaps to a stem profile other than the one the board exports.

The board's 3D models carry one flat stem (keycap_stem_r7*.wrl, the R3
geometry) on every key. A profile changes what keycap_stem.scad's mx_stem()
does above the switch: the upper body, and with it the display and the clear
cap, is turned by `angle` about the stem's x axis through its origin and then
lifted by `extra_len` (translate([0,0,extra_len]) rotate([angle,0,0])). The
stem origin is the footprint's model offset, z 12 on the board.

So per key this rotates and lifts the whole cap, display face, stem and legend
decals (all of them sit from z 11.6 up, nothing else of the key's parts is
moved). The flex cable is left as it is; inside the cap it is hidden.
"""
import math

import bpy
import mathutils
import numpy as np

import textured_parts

# (angle deg, extra_len mm), from parts/keycap_stem/variants/*_10p.scad
STEMS = {"S1": (5, 0.5), "S": (-7, 1.5), "S5": (10, 2.5),
         "R1": (5, 0.5), "R2": (-5, 1), "R3": (0, 0), "R4": (5, 1.5), "R5": (10, 4)}
PROFILES = {
    "stepped": ("S1", "S", "S", "S", "S5"),        # front row .. back row (sculpted)
    "stepped-uniform": ("S",) * 5,
    "curved": ("R1", "R2", "R3", "R4", "R5"),
}
ROLES = {"keycap glass", "display face", "stem"}
PIVOT_Z = 12.0                  # the stem model's offset on every key footprint
SOCKET_H = 3.4                  # mm of stem above its base that grips the switch stem (top at z 16.2)
REACH = 13.0                    # mm from a key's centre that still belongs to it (a 1.25U cap reaches 11.3)


def rows(keys):
    """Row per key, 0 = front.

    Unrotated keys are grouped into columns by x gaps over 7 mm, not by
    rounding x: the 1.25U bottom-left key sits 4.8 mm right of the keys
    above it, and rounding gave it a column of its own and the back-row
    profile. Within a column, rows count from the top (row 4), so a short
    column ends above the front row. A rotated (thumb) key is front row if
    it sits below the unrotated front row's mean y, otherwise row 1: the
    thumb cluster's upper pair is not the front row. That gives the docs'
    7 / 22 / 7 split per half for the stepped profile."""
    out = [0] * len(keys)
    flat = sorted((i for i, (x, y, r) in enumerate(keys) if abs(r) < 1), key=lambda i: keys[i][0])
    cols, last = [], None
    for i in flat:
        if last is None or keys[i][0] - last > 7.0:
            cols.append([])
        cols[-1].append(i)
        last = keys[i][0]
    for c in cols:
        c.sort(key=lambda i: keys[i][1])
        for n, i in enumerate(c):
            out[i] = 4 - (len(c) - 1 - n) if len(c) < 5 else n
    front = [keys[i][1] for i in flat if out[i] == 0]
    front_y = sum(front) / len(front) if front else float("inf")
    for i, (x, y, r) in enumerate(keys):
        if abs(r) >= 1:
            out[i] = 0 if y < front_y else 1
    return out


def apply(root, board, profile):
    keys = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, keys)
    row = rows(keys)
    names = PROFILES[profile]
    print("profile", profile, {s: sum(names[r] == s for r in row) for s in set(names)})
    centres = np.array([[x + tx, y + ty] for x, y, r in keys])
    pivot_z = PIVOT_Z + dz
    xf = []
    for (x, y, r), rw, c in zip(keys, row, centres):
        a, lift = STEMS[names[rw]]
        axis = mathutils.Vector((math.cos(math.radians(r)), math.sin(math.radians(r)), 0))
        R = np.array(mathutils.Matrix.Rotation(math.radians(a), 3, axis))
        xf.append((R, np.array([c[0], c[1], pivot_z]), lift))
    bpy.context.view_layer.update()     # a decal parented this run has a stale matrix_world
    inv = root.matrix_world.inverted()
    moved = 0
    for o in root.children_recursive:
        if o.type != "MESH":
            continue
        role = o.active_material.get("pk_role") if o.active_material else None
        if role not in ROLES and "decal" not in o.name and "legends" not in o.name:
            continue
        m = np.array(inv @ o.matrix_world)
        mi = np.linalg.inv(m)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        p = co @ m[:3, :3].T + m[:3, 3]
        d = ((p[:, None, :2] - centres[None]) ** 2).sum(-1)
        k = d.argmin(1)
        sel = d[np.arange(len(p)), k] < REACH ** 2
        # the stem's socket stays on the switch: in mx_stem() only the body
        # above it turns and lifts, and the cylinder between them stretches.
        # Blend the move in over the socket's height instead of moving it all.
        blend = (np.clip((p[:, 2] - pivot_z) / SOCKET_H, 0, 1) if role == "stem"
                 else np.ones(len(p)))
        for i, (R, piv, lift) in enumerate(xf):
            s = sel & (k == i)
            if s.any():
                moved_to = (p[s] - piv) @ R.T + piv + (0, 0, lift)
                p[s] = p[s] + blend[s, None] * (moved_to - p[s])
        moved += int(sel.sum())
        co = p @ mi[:3, :3].T + mi[:3, 3]
        o.data.vertices.foreach_set("co", co.ravel())
        o.data.update()
    print("profile moved", moved, "vertices")


def dish(root, board, depth, half=7.6, top_band=0.05):
    """A concave top on every clear cap, `depth` mm deep at the centre.

    The cap model's top is a few large flat triangles, so the dish is put in
    the SHADING normal rather than the geometry: a spherical dish
    z = -depth (1 - r^2 / R^2) tilts its normal by 2 depth r / R^2 towards
    the centre, and that is linear in the offset from the centre, so a
    per-vertex offset ("dish", world metres, zero off the top face)
    interpolates it exactly across any triangle. The keycap glass material
    adds -2 depth / R^2 times that offset to its normal. R is `half`, the 1U
    top's half width. Call it before apply(): the offsets are taken with the
    tops still level, and a stem's tilt of at most 10 degrees leaves them
    close enough."""
    keys = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, keys)
    centres = np.array([[x + tx, y + ty] for x, y, r in keys])
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    rw = np.array(root.matrix_world)[:3, :3]
    for o in root.children_recursive:
        if o.type != "MESH" or not o.active_material or o.active_material.get("pk_role") != "keycap glass":
            continue
        m = np.array(inv @ o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        p = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        k = ((p[:, None, :2] - centres[None]) ** 2).sum(-1).argmin(1)
        top = p[:, 2] > p[:, 2].max() - top_band
        off = np.zeros_like(p)
        off[:, :2] = p[:, :2] - centres[k]
        off[~top] = 0
        off = off @ rw.T                # root frame mm -> world metres (the root's scale is mm -> m)
        attr = o.data.attributes.get("dish") or o.data.attributes.new("dish", "FLOAT_VECTOR", "POINT")
        attr.data.foreach_set("vector", off.ravel())
    s = -2 * (depth / 1000) / (half / 1000) ** 2
    for mat in bpy.data.materials:
        if mat.get("pk_role") != "keycap glass":
            continue
        nt = mat.node_tree
        b = nt.nodes["Principled BSDF"]
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "dish"
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        sc.inputs["Scale"].default_value = s
        nt.links.new(at.outputs["Vector"], sc.inputs[0])
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        add = nt.nodes.new("ShaderNodeVectorMath")
        add.operation = "ADD"
        nt.links.new(geo.outputs["Normal"], add.inputs[0])
        nt.links.new(sc.outputs[0], add.inputs[1])
        nrm = nt.nodes.new("ShaderNodeVectorMath")
        nrm.operation = "NORMALIZE"
        nt.links.new(add.outputs[0], nrm.inputs[0])
        nt.links.new(nrm.outputs[0], b.inputs["Normal"])
    print("dish", depth, "mm")


def _boundary_loop(edges):
    """Order boundary edges [(a, b)] into one closed loop of vertex indices."""
    nxt = {}
    for a, b in edges:
        nxt.setdefault(a, []).append(b)
        nxt.setdefault(b, []).append(a)
    start = edges[0][0]
    loop, prev, cur = [start], None, start
    while True:
        cand = [v for v in nxt[cur] if v != prev]
        if not cand:
            break
        prev, cur = cur, cand[0]
        if cur == start:
            break
        loop.append(cur)
    return loop


def _seg_dist(p, poly):
    """Distance from each point in p (N, 2) to the closed polyline poly (M, 2)."""
    a = poly
    b = np.roll(poly, -1, axis=0)
    ab = b - a
    t = np.clip(((p[:, None] - a[None]) * ab[None]).sum(-1) / (ab ** 2).sum(-1)[None], 0, 1)
    q = a[None] + t[..., None] * ab[None]
    return np.sqrt(((p[:, None] - q) ** 2).sum(-1)).min(1)


def _inside(p, poly):
    """Even-odd point-in-polygon test, vectorised."""
    x, y = p[:, 0][:, None], p[:, 1][:, None]
    x0, y0 = poly[:, 0][None], poly[:, 1][None]
    x1, y1 = np.roll(poly[:, 0], -1)[None], np.roll(poly[:, 1], -1)[None]
    c = ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-12) + x0)
    return c.sum(1) % 2 == 1


def dent_mesh(o, to_root, centres, depth, width=2.5, pitch=0.3, bowl=0.2):
    """Replace each flat cap top in mesh object `o` with a fine mesh pressed
    down into a shallow dent, `depth` mm at the middle: (1 - bowl) of it is
    taken over `width` mm from the edge (a smoothstep, the soft rim on all
    four sides), the remaining `bowl` as a gentle slope on to the middle, so
    the floor is not flat. It meets the model's rounded edge unchanged.

    The model's top is a fan of large flat triangles with no vertex inside
    6 mm of the centre, so it cannot be bent as it is. Per cap this deletes
    those faces, keeps the boundary they shared with the rounded edge, and
    re-fills the hole by a constrained Delaunay triangulation of that
    boundary plus a `pitch` mm grid of interior points; the glass stays a
    closed shell. to_root maps o's local coordinates to the frame `centres`
    (N, 2) are in, with z up and in mm."""
    import bmesh
    from mathutils.geometry import delaunay_2d_cdt
    M = np.array(to_root)
    Mi = np.linalg.inv(M)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    # the VRML gives every triangle its own corners: weld them, or every edge
    # reads as a boundary (1 um, in the mesh's own units)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001 / np.linalg.norm(M[:3, 0]))
    # every bmesh op renumbers v.index, so map vertices to rows of p once, by identity
    vl = list(bm.verts)
    vid = {v: i for i, v in enumerate(vl)}
    co = np.array([v.co[:] for v in vl])
    p = co @ M[:3, :3].T + M[:3, 3]
    ztop = p[:, 2].max()
    top = p[:, 2] > ztop - 0.005
    faces = [f for f in bm.faces if all(top[vid[v]] for v in f.verts)]
    key = {}
    for f in faces:
        c = p[[vid[v] for v in f.verts], :2].mean(0)
        key.setdefault(int(((centres - c) ** 2).sum(1).argmin()), []).append(f)
    made = 0
    for k, fs in key.items():
        fset = set(fs)
        edges = [(vid[e.verts[0]], vid[e.verts[1]]) for f in fs for e in f.edges
                 if sum(1 for lf in e.link_faces if lf in fset) == 1]
        loop = _boundary_loop(list(dict.fromkeys(edges)))
        poly = p[loop, :2]
        lo, hi = poly.min(0), poly.max(0)
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0], pitch), np.arange(lo[1], hi[1], pitch))
        g = np.stack([gx.ravel(), gy.ravel()], 1)
        g = g[_inside(g, poly)]
        g = g[_seg_dist(g, poly) > pitch * 0.6]
        pts = [tuple(v) for v in poly] + [tuple(v) for v in g]
        vo, _, fo, ov, _, _ = delaunay_2d_cdt(pts, [], [list(range(len(loop)))], 1, 1e-6)
        s = _seg_dist(np.array([v[:] for v in vo]), poly)
        t = np.clip(s / width, 0, 1)
        u = np.clip(s / s.max(), 0, 1)
        # most of the depth is taken in the soft rim, the rest as a gentle
        # slope on to the lowest point in the middle: no flat floor
        z = ztop - depth * ((1 - bowl) * t * t * (3 - 2 * t) + bowl * u * u * (3 - 2 * u))
        bmv = []
        for i, v in enumerate(vo):
            orig = ov[i]
            if orig and orig[0] < len(loop):
                bmv.append(vl[loop[orig[0]]])
            else:
                r = np.array([v[0], v[1], z[i], 1.0]) @ Mi.T
                bmv.append(bm.verts.new(r[:3]))
        mat = fs[0].material_index
        # face the way the faces being replaced face: the model's winding, not
        # an assumed outward +z (a glass shell with mixed windings goes dark)
        up = np.mean([(np.array(f.normal[:]) @ M[:3, :3].T)[2] for f in fs]) > 0
        bmesh.ops.delete(bm, geom=fs, context="FACES_ONLY")
        for f in fo:
            nf = bm.faces.new([bmv[i] for i in f])
            nf.smooth = True
            nf.normal_update()              # a new face has no normal until asked
            n = np.array(nf.normal[:]) @ M[:3, :3].T
            if (n[2] > 0) != up:
                nf.normal_flip()
            nf.material_index = mat
        made += len(fo)
    bm.to_mesh(o.data)
    bm.free()
    # welded, the cap's smooth flag now spans its corners too (unwelded, every
    # triangle shaded flat): keep edges sharper than 30 degrees hard
    o.data.set_sharp_from_angle(angle=math.radians(30))
    o.data.update()
    return len(key), made


def dent(root, board, depth, width=2.5, bowl=0.2):
    """dent_mesh() on every clear cap of a half, before apply()."""
    keys = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, keys)
    centres = np.array([[x + tx, y + ty] for x, y, r in keys])
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    for o in root.children_recursive:
        if o.type == "MESH" and o.active_material and o.active_material.get("pk_role") == "keycap glass":
            print("dent", o.name, dent_mesh(o, inv @ o.matrix_world, centres, depth, width, bowl=bowl))
