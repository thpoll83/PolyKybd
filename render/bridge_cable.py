"""The USB-C bridge cable between the halves, for the Blender scene.

Each half has its bridge port, USB2 (HRO TYPE-C-31-M-12 on B.Cu), on its
inner edge at board y 86.16, facing the other half. The halves sit ~50 mm
apart, less than two straight plugs need, so the cable uses 90 deg plugs whose
cable leaves towards the BACK, and the cable lies on the desk in a U behind
the keyboard (decided with the designer, 2026-10-06).

Per half, in the half's own frame (mm, parented to the half, so it follows
the splay), built from the board file and the fitted key frame
(textured_parts.fit):
- the nickel plug shell, 8.25 x 2.4 mm (USB-C), from 6.65 mm inside the
  receptacle mouth out to the overmold,
- the overmold, 9 mm along the plug axis x 22.5 mm x 6.5 mm (inside the USB-IF
  12.35 x 6.5 mm envelope across the plug), its face against the case wall,
  found from the case mesh, rounded 1.5 mm,
- a tapered strain relief at its back end.
Then one braided cable in world space (metres), 3.6 mm across, from one strain
relief to the other: back from each plug, down onto the desk within ~30 mm,
and a U behind the keyboard. Its uv runs around (u) and along (v) the cable
and carries textures/braid.png (gen_textures.py) as colour and bump.
"""
import math
import os
import re

import bmesh
import bpy
import mathutils
import numpy as np

import textured_parts

PCB = 1.6062
SHELL_W, SHELL_H, SHELL_IN = 8.25, 2.4, 6.65      # USB-C plug shell; depth into the receptacle
RECEPT_H = 3.26                                   # receptacle shell height, hanging under B.Cu
MOLD_T, MOLD_FRONT, MOLD_BACK, MOLD_H, MOLD_R = 9.0, 6.5, 16.0, 6.5, 1.5
RELIEF_L, RELIEF_R0 = 9.0, 2.6
CABLE_R = 1.8
BRAID_MM = 6.0                                    # one braid tile along the cable


def footprint_at(board, ref):
    t = open(board, encoding="utf-8").read()
    i = t.find(f'"Reference" "{ref}"')
    s = t.rfind("(footprint ", 0, i)
    m = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", t[s:i])
    return float(m.group(1)), float(m.group(2)), float(m.group(3) or 0)


def _role_points(root, role):
    inv = root.matrix_world.inverted()
    pts = []
    for o in root.children_recursive:
        if o.type == "MESH" and o.active_material and o.active_material.get("pk_role") == role:
            m = np.array(inv @ o.matrix_world)
            co = np.empty(len(o.data.vertices) * 3)
            o.data.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            pts.append(co @ m[:3, :3].T + m[:3, 3])
    return np.concatenate(pts)


def _material(name, rgb, roughness, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m["pk_role"] = name
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = roughness
    b.inputs["Metallic"].default_value = metallic
    return m


def _braid_material():
    m = bpy.data.materials.get("braid") or bpy.data.materials.new("braid")
    m.use_nodes = True
    m["pk_role"] = "braid"
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(textured_parts.HERE, "textures", "braid.png"), check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"
    ramp = nt.nodes.new("ShaderNodeValToRGB")         # strand gaps black, strand crowns dark grey
    ramp.color_ramp.elements[0].color = (0.002, 0.002, 0.0025, 1)
    ramp.color_ramp.elements[1].color = (0.014, 0.014, 0.015, 1)
    nt.links.new(tex.outputs["Color"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = nt.nodes.new("ShaderNodeBump")
    # a deep weave: where the cable tilts towards the softbox (the host
    # cable's drop to the desk) the highlight must break up into strands, or
    # it reads as a smooth grey patch
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 0.0008
    nt.links.new(tex.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # glossy fibres: on the deep weave the highlights land as small sharp
    # points on the strand crowns, not as a broad grey sheet. No sheen: it
    # lifted the black sleeve to grey (0.2 read grey against the photo's cable)
    b.inputs["Roughness"].default_value = 0.32
    for k, v in (("Sheen Weight", 0.0), ("Sheen Roughness", 0.4)):
        if k in b.inputs:
            b.inputs[k].default_value = v
    # ...but the specular is kept to the surface facing the camera: the host
    # cable runs AWAY from it, and its flanks then mirror the bright white
    # backdrop behind the keyboard, so the black sleeve read grey (specular
    # off, it renders black; a grazing-only falloff left it grey). Specular
    # = 0.5 x (1 - facing)^3: full face-on, where the sharp highlights on
    # the strand crowns are, and a few percent across the flanks.
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    fall = nt.nodes.new("ShaderNodeMath")
    fall.operation = "POWER"
    fall.inputs[1].default_value = 3.0
    nt.links.new(inv.outputs["Value"], fall.inputs[0])
    spec = nt.nodes.new("ShaderNodeMath")
    spec.operation = "MULTIPLY"
    spec.inputs[1].default_value = 0.5
    nt.links.new(fall.outputs["Value"], spec.inputs[0])
    nt.links.new(spec.outputs["Value"], b.inputs["Specular IOR Level"])
    return m


def _box(name, lo, hi, radius, mat, parent):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    c = [(a + b) / 2 for a, b in zip(lo, hi)]
    s = [b - a for a, b in zip(lo, hi)]
    for v in bm.verts:
        v.co = mathutils.Vector([c[i] + v.co[i] * s[i] for i in range(3)])
    if radius > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=radius, segments=4, affect="EDGES", profile=0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    return o


def _tube(name, pts, radii, mat, parent=None, ring=20, v_scale=None, cap=True):
    """Tube along pts (N,3) with per-point radius; parallel-transport frames."""
    pts = np.asarray(pts, float)
    t = np.gradient(pts, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    n = np.cross(t[0], [0, 0, 1.0])
    if np.linalg.norm(n) < 1e-6:
        n = np.cross(t[0], [0, 1.0, 0])
    n /= np.linalg.norm(n)
    frames = []
    for i in range(len(pts)):
        if i:
            n = n - t[i] * np.dot(n, t[i])
            n /= np.linalg.norm(n)
        frames.append((n, np.cross(t[i], n)))
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    verts, uvs = [], []
    for i, (p, (a, b)) in enumerate(zip(pts, frames)):
        for k in range(ring + 1):                     # seam column duplicated for the uv
            ang = 2 * math.pi * k / ring
            verts.append(p + radii[i] * (math.cos(ang) * a + math.sin(ang) * b))
            uvs.append((2.0 * k / ring, s[i] / v_scale if v_scale else 0.0))
    faces = []
    w = ring + 1
    for i in range(len(pts) - 1):
        for k in range(ring):
            faces.append((i * w + k, i * w + k + 1, (i + 1) * w + k + 1, (i + 1) * w + k))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uv = me.uv_layers.new(name="uv")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
        poly.use_smooth = True
    if cap:
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.verts.ensure_lookup_table()
        for row in (0, len(pts) - 1):
            bmesh.ops.contextual_create(bm, geom=[bm.verts[row * w + k] for k in range(ring)])
        bm.to_mesh(me)
        bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    return o


def plug(root, board, toward=1.0):
    """Shell, overmold and strain relief on root's USB2; returns the cable's
    start point and direction, both in root's frame (mm). `toward` +1 turns
    the 90 deg plug's cable to the back of the board, -1 to the front."""
    keys = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, keys)
    x, y, _ = footprint_at(board, "USB2")
    edge_centre = np.mean([k[0] for k in keys])
    sx = 1.0 if x > edge_centre else -1.0             # outward along x, towards the other half
    mx, my = x + tx, -y + ty                          # the mouth (the footprint origin)
    zc = dz - PCB - RECEPT_H / 2
    # case wall: the case's outermost x within the plug's footprint
    case = _role_points(root, "case PLA")
    near = case[(np.abs(case[:, 1] - my) < MOLD_FRONT) & (np.abs(case[:, 2] - zc) < MOLD_H / 2)]
    face = (near[:, 0] * sx).max() * sx + sx * 0.3 if len(near) else mx + sx * 2.0
    nickel = _material("plug shell", (0.78, 0.78, 0.76), 0.22, metallic=1.0)
    tpe = _material("plug overmold", (0.012, 0.012, 0.014), 0.42)
    xs = sorted((mx - sx * SHELL_IN, face + sx * 0.5))
    _box(root.name + " plug shell", (xs[0], my - SHELL_W / 2, zc - SHELL_H / 2),
         (xs[1], my + SHELL_W / 2, zc + SHELL_H / 2), SHELL_H / 2 - 0.05, nickel, root)
    xs = sorted((face, face + sx * MOLD_T))
    ys = sorted((my - toward * MOLD_FRONT, my + toward * MOLD_BACK))
    _box(root.name + " plug overmold", (xs[0], ys[0], zc - MOLD_H / 2),
         (xs[1], ys[1], zc + MOLD_H / 2), MOLD_R, tpe, root)
    cx = face + sx * MOLD_T / 2
    y0 = my + toward * (MOLD_BACK - 0.5)
    n = 12
    pts = [(cx, y0 + toward * RELIEF_L * i / (n - 1), zc) for i in range(n)]
    radii = [RELIEF_R0 + (CABLE_R + 0.05 - RELIEF_R0) * (i / (n - 1)) ** 0.7 for i in range(n)]
    _tube(root.name + " strain relief", pts, radii, tpe, parent=root, ring=24)
    return (mathutils.Vector((cx, y0 + toward * (RELIEF_L - 0.3), zc)),
            mathutils.Vector((0, toward, 0)))


def remove(keep_bridge=False, keep_host=False):
    """Delete the cables and plugs a saved scene carries, except those kept."""
    for o in [o for o in bpy.data.objects
              if (o.get("pk_bridge") and not keep_bridge) or (o.get("pk_host") and not keep_host)]:
        bpy.data.objects.remove(o)


def _bezier(c, n):
    c = np.asarray(c, float)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3]


def _through(way, n):
    """A smooth (Catmull-Rom) curve through the waypoints, n points, as (n, 3)."""
    w = np.asarray(way, float)
    w = np.vstack([2 * w[0] - w[1], w, 2 * w[-1] - w[-2]])      # end tangents along the ends
    seg = len(w) - 3
    out = []
    for i in range(seg):
        p0, p1, p2, p3 = w[i], w[i + 1], w[i + 2], w[i + 3]
        for t in np.linspace(0, 1, max(2, n // seg), endpoint=(i == seg - 1)):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def _smooth(pts, sigma, keep):
    """Resample a plan-view path evenly and Gaussian-smooth it (sigma, m), so
    the waypoint spline loses its corners. Within `keep` (m) of either end the
    path is left as it is, and the smoothing fades in over the next sigma, so
    the cable still leaves each plug straight along its direction."""
    pts = np.asarray(pts, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    n = len(pts)
    u = np.linspace(0, s[-1], n)
    even = np.column_stack([np.interp(u, s, pts[:, k]) for k in range(3)])
    ds = u[1] - u[0]
    r = int(3 * sigma / ds)
    g = np.exp(-0.5 * (np.arange(-r, r + 1) * ds / sigma) ** 2)
    g /= g.sum()
    pad = np.concatenate([np.repeat(even[:1], r, 0), even, np.repeat(even[-1:], r, 0)])
    soft = np.column_stack([np.convolve(pad[:, k], g, mode="valid") for k in range(3)])
    end = np.minimum(u, s[-1] - u)
    w = np.clip((end - keep) / sigma, 0, 1)[:, None]
    w = w * w * (3 - 2 * w)
    return even * (1 - w) + soft * w


def add(sc, halves, depth=0.08, lean=0.010, toward=1.0, spread=0.0, clear=0.0):
    """halves: [(root, board path)] left then right. depth: how far (m) the U
    reaches past the plugs; lean: sideways offset of the U's bottom, so it
    does not look drawn with a ruler. toward: +1 the plugs turn the cable to
    the back and the U hangs behind the keyboard, -1 in front of it. spread:
    how far (m) each side of the U bulges outwards past its plug, so a loop
    between halves set close together stays a U and does not pinch into a V.
    clear: a straight run (m) from each plug along its direction before the
    U starts, so the cable leaves through the gap between the halves and
    clears their cases before it bulges outwards; without it a U close to
    the halves passes through the case corners in front of the plugs."""
    for o in [o for o in bpy.data.objects if o.get("pk_bridge")]:
        bpy.data.objects.remove(o)
    bpy.context.view_layer.update()
    ends = []
    for root, board in halves:
        before = set(bpy.data.objects.keys())
        p, d = plug(root, board, toward)
        for name in set(bpy.data.objects.keys()) - before:
            bpy.data.objects[name]["pk_bridge"] = True
        mw = root.matrix_world
        ends.append((mw @ p, (mw.to_3x3() @ d).normalized()))
    (pa, da), (pb, db) = ends
    r = CABLE_R / 1000
    lean_v = mathutils.Vector((lean, 0, 0))
    out = mathutils.Vector((1 if pb.x > pa.x else -1, 0, 0)) * spread       # a -> b
    if clear > 0:
        # one smooth curve through waypoints: straight out of each plug for
        # `clear`, bulging `spread` outwards, the bottom `depth` past that
        qa, qb = pa + da * clear, pb + db * clear
        fwd = (da + db).normalized()
        mid = (qa + qb) / 2 + fwd * depth + lean_v
        way = [pa, qa, qa + fwd * depth * 0.55 - out, mid, qb + fwd * depth * 0.55 + out, qb, pb]
        pts = _smooth(_through([tuple(v) for v in way], 400), sigma=0.012, keep=0.006)
    else:
        # plan view: one cubic U from the left plug to the right one
        c = [pa, pa + da * depth * 1.25 + lean_v - out, pb + db * depth * 1.4 + lean_v + out, pb]
        pts = _bezier([tuple(v) for v in c], 400)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1))])
    # height: leaves each plug level and settles on the desk within 30 mm.
    # ⚠️ MAXIMUM of the two lifts, each high only near its own plug: the
    # minimum (as this was) put BOTH ends on the desk, 8 mm below the plugs,
    # which a render shows as the cable cut off just past each strain relief.
    settle = 0.03
    def lift(z0, d):
        k = np.clip(d / settle, 0, 1)
        return r + (z0 - r) * (1 - (3 * k ** 2 - 2 * k ** 3))
    pts[:, 2] = np.maximum(lift(pa.z, s), lift(pb.z, s[-1] - s))
    pts[:, 2] = np.maximum(pts[:, 2], r)
    o = _tube("bridge cable", pts, [r] * len(pts), _braid_material(), ring=20, v_scale=BRAID_MM / 1000)
    o["pk_bridge"] = True
    print(f"bridge cable: {s[-1] * 1000:.0f} mm on the desk plan, ends at z {pa.z * 1000:.1f} / {pb.z * 1000:.1f} mm")
    return o


def clearance(cable, role="case PLA"):
    """The cable's closest approach (m) to any mesh of `role`, and how many of
    its centreline points sit closer than the cable's own radius: a cable
    routed through a case is hidden where it is inside, which reads in a render
    as the cable being cut."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    trees = []      # (tree in the object's own frame, world matrix, its inverse)
    for o in bpy.data.objects:
        if o.type == "MESH" and o.active_material and o.active_material.get("pk_role") == role:
            trees.append((BVHTree.FromObject(o, dg, deform=False), o.matrix_world,
                          o.matrix_world.inverted()))
    mw = cable.matrix_world
    pts = [mw @ v.co for v in cable.data.vertices]
    # the tube's rings (_tube: ring=20 around plus the duplicated seam vertex);
    # the centreline is the mean of each ring's 20
    w = 21
    centres = [sum(pts[i:i + w - 1], mathutils.Vector()) / (w - 1) for i in range(0, len(pts) - w + 1, w)]
    best, inside = 1e9, 0
    r = CABLE_R / 1000
    for c in centres:
        for t, m, inv in trees:
            hit = t.find_nearest(inv @ c)
            if hit[0] is None:
                continue
            d = ((m @ hit[0]) - c).length                # in world units (m)
            best = min(best, d)
            if d < r:
                inside += 1
                break
    return best, inside, len(centres)


HOST_MOLD = (12.0, 22.0, 6.5)                     # straight overmold: across, along, high (mm)


def host_plug(root, board, ref="USB1"):
    """A straight USB-C plug on root's top-edge port (USB1, mouth facing the
    back edge, +y in root's frame); returns the cable start in root's frame."""
    keys = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, keys)
    x, y, _ = footprint_at(board, ref)
    mx, my = x + tx, -y + ty
    zc = dz - PCB - RECEPT_H / 2
    w, length, h = HOST_MOLD
    case = _role_points(root, "case PLA")
    near = case[(np.abs(case[:, 0] - mx) < w / 2) & (np.abs(case[:, 2] - zc) < h / 2)]
    face = near[:, 1].max() + 0.3 if len(near) else my + 2.0
    nickel = _material("plug shell", (0.78, 0.78, 0.76), 0.22, metallic=1.0)
    tpe = _material("plug overmold", (0.012, 0.012, 0.014), 0.42)
    _box(root.name + " host plug shell", (mx - SHELL_W / 2, my - SHELL_IN, zc - SHELL_H / 2),
         (mx + SHELL_W / 2, face + 0.5, zc + SHELL_H / 2), SHELL_H / 2 - 0.05, nickel, root)
    _box(root.name + " host plug overmold", (mx - w / 2, face, zc - h / 2),
         (mx + w / 2, face + length, zc + h / 2), MOLD_R, tpe, root)
    y0 = face + length - 0.5
    n = 12
    pts = [(mx, y0 + RELIEF_L * i / (n - 1), zc) for i in range(n)]
    radii = [RELIEF_R0 + (CABLE_R + 0.05 - RELIEF_R0) * (i / (n - 1)) ** 0.7 for i in range(n)]
    _tube(root.name + " host strain relief", pts, radii, tpe, parent=root, ring=24)
    return mathutils.Vector((mx, y0 + RELIEF_L - 0.3, zc)), mathutils.Vector((0, 1, 0))


def add_host(sc, root, board, end_y=0.62, drift=-0.18, turn=30.0):
    """The host cable from root's USB1, back across the desk and out of frame
    (the frame's top edge meets the desk at about y = 0.4 m; the cove starts
    curving up at 0.7). One gentle arc to the left: it leaves the plug
    straight back and ends `drift` m to the side, heading `turn` deg left."""
    for o in [o for o in bpy.data.objects if o.get("pk_host")]:
        bpy.data.objects.remove(o)
    bpy.context.view_layer.update()
    before = set(bpy.data.objects.keys())
    p, d = host_plug(root, board)
    for name in set(bpy.data.objects.keys()) - before:
        bpy.data.objects[name]["pk_host"] = True
    mw = root.matrix_world
    pa, da = mw @ p, (mw.to_3x3() @ d).normalized()
    run = end_y - pa.y
    pb = mathutils.Vector((pa.x + drift, end_y, 0))
    t = math.radians(turn)
    end_dir = mathutils.Vector((-math.sin(t), math.cos(t), 0))   # left of straight back
    c = [pa, pa + da * run * 0.4, pb - end_dir * run * 0.4, pb]
    pts = _bezier([tuple(v) for v in c], 400)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1))])
    r = CABLE_R / 1000
    k = np.clip(s / 0.03, 0, 1)
    pts[:, 2] = r + (pa.z - r) * (1 - (3 * k ** 2 - 2 * k ** 3))
    o = _tube("host cable", pts, [r] * len(pts), _braid_material(), ring=20, v_scale=BRAID_MM / 1000)
    o["pk_host"] = True
    print(f"host cable: {s[-1] * 1000:.0f} mm on the desk plan, from z {pa.z * 1000:.1f} mm")
    return o
