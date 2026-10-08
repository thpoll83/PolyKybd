"""Turn the displays on: each key display's layer-0 legend and both status panels.

The pictures are export_screens.py's (the host layout editor's own drawing of
the default keymap). Each key gets a quad over its display's 72x40 active
area, 0.004 mm above the decal, textured from the atlas with the OLED pixel
(0, 0) at the active area's top-left as read from the front (the side away
from the flex cable), and its legend pixels emitting. Which board key gets
which legend comes from the KLE matrix labels, matched the way topview.py
does it. The status panels get the same over the top face of their "status
lcd" box.
"""
import json
import os

import bpy
import mathutils
import numpy as np

import keymatch
import materials
import textured_parts

TEX = os.path.join(textured_parts.HERE, "textures")
KLE = os.path.join(textured_parts.REPO, "..", "PolyKybdHost", "polyhost", "res", "polykybd-split72.json")
LIFT = 0.008                            # mm above the decal (which is 0.004 above the display)
# The lit pixels' colour: the panels' white has a faint blue cast, kept just short
# of noticeable. Multiplies the atlas colour, so black stays black.
LIT_TINT = (0.70, 0.84, 1.0, 1.0)


def _material(name, image, strength):
    """Glossy black glass whose lit pixels emit the image's colour."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m["pk_role"] = name
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(TEX, image), check_existing=True)
    # Closest: one OLED pixel stays one crisp square. Linear blended each pixel into
    # its neighbours, which read as a soft, out-of-focus display.
    tex.interpolation = "Closest"
    b.inputs["Base Color"].default_value = (0.002, 0.002, 0.003, 1)
    for k, v in materials.DISPLAY_GLASS.items():   # the same glass as the decal under it
        materials._set(b, k, v)
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type = "RGBA"
    tint.blend_type = "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    # the Mix node carries float, vector and colour sockets under the same names
    a, b_in = [i for i in tint.inputs if i.type == "RGBA"]
    b_in.default_value = LIT_TINT
    nt.links.new(tex.outputs["Color"], a)
    nt.links.new(next(o for o in tint.outputs if o.type == "RGBA"), b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    return m


def keys(root, board, side, strength=6.0, kle_path=KLE, atlas_name="screens_layer0"):
    """Lit legends on every key display of one half, from the atlas
    textures/<atlas_name>.png/.json (export_screens.py). Returns how many."""
    atlas = json.load(open(os.path.join(TEX, atlas_name + ".json"), encoding="utf-8"))
    (aw, ah), (cw, ch) = atlas["size"], atlas["cell"]
    kb = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, kb)
    kle = [k for k in keymatch.kle_keys(kle_path) if (int(k[0].split(",")[0]) < 5) == (side == "left")]
    labels, _ = keymatch.match(np.array([[x, -y] for x, y, _ in kb]), kle)
    X, Y0, Y1 = textured_parts.DISP_X, textured_parts.DISP_Y0, textured_parts.DISP_Y1
    z = textured_parts.DISP_TOP + dz + LIFT
    verts, tris, uv = [], [], []
    for (x, y, r), label in zip(kb, labels):
        cell = atlas["keys"].get(label)
        if cell is None:
            continue

        def corner(fu, fv):
            p = np.array([-X + 2 * X * fu, Y0 + (Y1 - Y0) * fv])
            xy = textured_parts._rot(p, r) + np.array([x, y]) + np.array([tx, ty])
            return (xy[0], xy[1], z)
        u0, u1 = cell[0] / aw, (cell[0] + cw) / aw
        v1, v0 = 1 - cell[1] / ah, 1 - (cell[1] + ch) / ah      # image rows run down
        base = len(verts)
        # OLED top-left, top-right, bottom-right, bottom-left (topview.py's order)
        verts += [corner(keymatch.A_U0, keymatch.A_V1), corner(keymatch.A_U1, keymatch.A_V1),
                  corner(keymatch.A_U1, keymatch.A_V0), corner(keymatch.A_U0, keymatch.A_V0)]
        uv += [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
        tris += [(base, base + 3, base + 2), (base, base + 2, base + 1)]
    textured_parts._mesh(root.name + " lit legends", verts, tris, uv,
                         _material("lit legends", atlas_name + ".png", strength), root)
    return len(verts) // 4


def status(root, side, strength=4.0, suffix=""):
    """The status panel's picture over the top face of the half's "status lcd" box,
    from textures/status_<side><suffix>.png (suffix "_l1" for layer 1)."""
    pts = textured_parts._display_points(root, "status lcd")
    top = pts[pts[:, 2] > pts[:, 2].max() - 1e-6]
    (x0, y0), (x1, y1), z = top[:, :2].min(0), top[:, :2].max(0), top[:, 2].max() + LIFT
    # the panel reads from the front, so its top row is the box's back (+y) edge
    verts = [(x0, y1, z), (x1, y1, z), (x1, y0, z), (x0, y0, z)]
    uv = [(0, 1), (1, 1), (1, 0), (0, 0)]
    textured_parts._mesh(root.name + " lit status", verts, [(0, 3, 2), (0, 2, 1)], uv,
                         _material(f"lit status {side}", f"status_{side}{suffix}.png", strength), root)
    return (x1 - x0, y1 - y0)
