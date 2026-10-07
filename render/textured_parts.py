"""Textured keycap displays and flex cables for the Blender scenes.

The VRML a board exports carries no texture coordinates, so per key this adds
- a decal on the display's top face with textures/display_front.png, and
- the flex cable rebuilt from poly_kybd/models/flex_cable.strip(), with its uv,
  textures/flex.png, replacing the imported cable;
both placed by the key's position and rotation from the board file.

Where an imported half sits relative to the board is fitted, not assumed: the
imported display meshes are grouped by key (nearest predicted centre) and the
translation is the mean offset of their box centres, which a key's rotation
does not move. The residual is printed; it should be well under 0.1 mm.
"""
import math
import os
import re
import sys

import bpy
import mathutils
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "poly_kybd", "models"))
from flex_cable import strip  # noqa: E402

S = 0.39 * 2.54                         # the display model's board scale (0.39 x 0.1 inch)
DISP_X = 6.1 * S                        # keycap_display.wrl: x +-6.1, y -4.61..6.5, top z 5.5
DISP_Y0, DISP_Y1 = -4.61 * S, 6.5 * S
DISP_TOP = 12 + 5.5 * S                 # offset z 12 on every key
DISP_CENTRE_Y = (DISP_Y0 + DISP_Y1) / 2


def board_keys(board):
    """[(x, y_up, rot_deg)] of every SW_K_* footprint, y flipped to point up."""
    t = open(board, encoding="utf-8").read()
    keys = []
    for m in re.finditer(r'\n\t\(footprint "poly_kb:Kailh_socket_MX_Indicators"\n\t\t\(layer "F\.Cu"\)\n'
                         r'(?:\t\t[^\n]*\n)*?\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', t):
        keys.append((float(m.group(1)), -float(m.group(2)), float(m.group(3) or 0)))
    return keys


def _rot(v, deg):
    a = math.radians(deg)
    return np.array([v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)])


def _display_points(root, role="display face"):
    inv = root.matrix_world.inverted()
    pts = []
    for o in root.children_recursive:
        if o.type == "MESH" and o.active_material and o.active_material.get("pk_role") == role:
            m = inv @ o.matrix_world
            co = np.empty(len(o.data.vertices) * 3)
            o.data.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            pts.append(co @ np.array(m)[:3, :3].T + np.array(m)[:3, 3])
    return np.concatenate(pts) if pts else np.zeros((0, 3))


def fit(root, keys):
    """Translation (tx, ty) and dz taking board key frames into root's frame."""
    pts = _display_points(root)
    if not len(pts):
        raise SystemExit(f"{root.name}: no display meshes to fit against")
    pred = np.array([[x, y] + _rot((0, DISP_CENTRE_Y), r) for x, y, r in keys])
    t = (pts[:, :2].min(0) + pts[:, :2].max(0)) / 2 - (pred.min(0) + pred.max(0)) / 2
    for _ in range(2):
        d = ((pts[:, None, :2] - (pred + t)[None]) ** 2).sum(-1)
        near = d.argmin(1)
        centres = np.array([(pts[near == k, :2].min(0) + pts[near == k, :2].max(0)) / 2
                            for k in range(len(keys))])
        t = (centres - pred).mean(0)
    resid = np.abs(centres - pred - t).max()
    dz = pts[:, 2].max() - DISP_TOP
    print(f"{root.name}: fitted {len(keys)} keys, residual {resid:.4f} mm, dz {dz:.4f}")
    return t, dz


def _image_material(name, image, roughness, coat=0.0, metallic_mask=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m["pk_role"] = name
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(HERE, "textures", image), check_existing=True)
    tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = roughness
    for n in ("Coat Weight", "Clearcoat"):
        if n in b.inputs:
            b.inputs[n].default_value = coat
    return m


def _mesh(name, verts, tris, uv, mat, parent):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", np.asarray(verts, dtype=np.float32).ravel())
    me.loops.add(len(tris) * 3)
    me.loops.foreach_set("vertex_index", np.asarray(tris, dtype=np.int32).ravel())
    me.polygons.add(len(tris))
    me.polygons.foreach_set("loop_start", np.arange(0, len(tris) * 3, 3, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(tris), 3, dtype=np.int32))
    me.update(calc_edges=True)
    layer = me.uv_layers.new(name="uv")
    layer.data.foreach_set("uv", np.asarray(uv, dtype=np.float32)[np.asarray(tris).ravel()].ravel())
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent          # parent's own units (mm), no parent inverse
    return ob


def add(root, keys):
    """Add the decals and textured cables to every key of `root`, remove the
    imported cables. Idempotent per root (marks root['pk_textured'])."""
    if root.get("pk_textured"):
        return
    t, dz = fit(root, keys)
    disp_mat = _image_material("display decal", "display_front.png", 0.04, coat=1.0)
    flex_mat = _image_material("flex textured", "flex.png", 0.22, coat=0.5)   # polyimide is glossy
    sv, stris, suv, _ = strip()
    suv = np.column_stack([suv[:, 0], 1.0 - suv[:, 1]])     # image top = display end
    dv, dtris, duv = [], [], []
    fv, ftris, fuv = [], [], []
    for x, y, r in keys:
        def place(p):
            xy = _rot(p[:2], r) + np.array([x, y]) + t
            return (xy[0], xy[1], p[2] + dz)
        quad = [(-DISP_X, DISP_Y0), (DISP_X, DISP_Y0), (DISP_X, DISP_Y1), (-DISP_X, DISP_Y1)]
        base = len(dv)
        dv += [place((qx, qy, DISP_TOP + 0.004)) for qx, qy in quad]
        dtris += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
        duv += [(0, 0), (1, 0), (1, 1), (0, 1)]
        base = len(fv)
        fv += [place(p) for p in sv]
        ftris += (stris + base).tolist()
        fuv += suv.tolist()
    for o in list(root.children_recursive):
        if o.type == "MESH" and o.active_material and o.active_material.get("pk_role") == "flex cable":
            bpy.data.objects.remove(o)
    _mesh(root.name + " display decals", dv, dtris, duv, disp_mat, root)
    _mesh(root.name + " flex cables", fv, ftris, fuv, flex_mat, root)
    root["pk_textured"] = True
