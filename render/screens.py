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
# PK_TINT="r,g,b" overrides it, e.g. the stronger blue a phone photo shows
import os as _os
if _os.environ.get("PK_TINT"):
    LIT_TINT = (*[float(c) for c in _os.environ["PK_TINT"].split(",")], 1.0)


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
    lit = next(o for o in tint.outputs if o.type == "RGBA")
    # PK_PANEL_FLOOR="r,g,b": every panel pixel, lit or not, adds this colour, a
    # lit OLED's faint glow (the docs' idle close-up); off by default
    floor = os.environ.get("PK_PANEL_FLOOR")
    if floor:
        add = nt.nodes.new("ShaderNodeMix")
        add.data_type, add.blend_type = "RGBA", "ADD"
        add.inputs["Factor"].default_value = 1.0
        a2, b2 = [i for i in add.inputs if i.type == "RGBA"]
        b2.default_value = (*[float(c) for c in floor.split(",")], 1.0)
        nt.links.new(lit, a2)
        lit = next(o for o in add.outputs if o.type == "RGBA")
    # PK_RASTER=<fill>: the OLED's pixel grid, each pixel lit over `fill` of its pitch
    # (0.86 as tutorial_video.py's pixel_grid), dark gaps between; the atlas has one
    # texel per display pixel, so the grid is the texture's own texel grid
    raster = os.environ.get("PK_RASTER")           # "fill[,keep]": keep raises the emission by what the gaps
    if raster:                                     # take, so the display's mean brightness stays as without
        _rv = raster.split(",")                    # the grid (each axis keeps fill - 0.05 of its light)
        fill = float(_rv[0])
        if len(_rv) > 1 and _rv[1] == "keep":
            strength = strength / (fill - 0.05) ** 2
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["UV"], sep.inputs[0])
        mask = None
        for axis, n in (("X", tex.image.size[0]), ("Y", tex.image.size[1])):
            sc_ = nt.nodes.new("ShaderNodeMath"); sc_.operation = "MULTIPLY"; sc_.inputs[1].default_value = n
            nt.links.new(sep.outputs[axis], sc_.inputs[0])
            fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
            nt.links.new(sc_.outputs[0], fr.inputs[0])
            dc = nt.nodes.new("ShaderNodeMath"); dc.operation = "SUBTRACT"; dc.inputs[1].default_value = 0.5
            nt.links.new(fr.outputs[0], dc.inputs[0])
            ab = nt.nodes.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"
            nt.links.new(dc.outputs[0], ab.inputs[0])
            edge = nt.nodes.new("ShaderNodeMapRange")          # 1 inside the lit part, a soft 5% edge
            edge.inputs["From Min"].default_value = fill / 2 - 0.05
            edge.inputs["From Max"].default_value = fill / 2
            edge.inputs["To Min"].default_value, edge.inputs["To Max"].default_value = 1.0, 0.0
            nt.links.new(ab.outputs[0], edge.inputs["Value"])
            if mask is None:
                mask = edge
            else:
                mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
                nt.links.new(mask.outputs[0], mul.inputs[0]); nt.links.new(edge.outputs[0], mul.inputs[1])
                mask = mul
        gm = nt.nodes.new("ShaderNodeMix"); gm.data_type, gm.blend_type = "RGBA", "MULTIPLY"
        gm.inputs["Factor"].default_value = 1.0
        a3, b3 = [i for i in gm.inputs if i.type == "RGBA"]
        nt.links.new(lit, a3)
        nt.links.new(mask.outputs[0], b3)
        lit = next(o for o in gm.outputs if o.type == "RGBA")
    nt.links.new(lit, b.inputs["Emission Color"])
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
                         _material(f"lit legends {atlas_name}", atlas_name + ".png", strength), root)
    return len(verts) // 4


def driver_chips(root, board, side, kle_path=KLE):
    """The OLED driver chip on each display's glass ledge, below the image area: a glossy
    6.0 x 0.8 x 0.3 mm box centred across the panel, 7.0 to 7.8 mm from the panel's top
    edge (the panel is 12.2 x 11.0 mm, keymatch.A_*). On the real keyboard its flat top
    catches the room light as a short white streak under the image, inside the clear cap.
    Returns how many."""
    kb = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, kb)
    X, Y0, Y1 = textured_parts.DISP_X, textured_parts.DISP_Y0, textured_parts.DISP_Y1
    z0 = textured_parts.DISP_TOP + dz + LIFT       # on the glass, above the decal (units are mm here)
    z1 = z0 + 0.3
    fu0, fu1 = 3.1 / 12.2, 9.1 / 12.2
    fv0, fv1 = 1 - 7.8 / 11.0, 1 - 7.0 / 11.0
    verts, tris, uv = [], [], []
    for x, y, r in kb:
        def at(fu, fv, zz):
            p = np.array([-X + 2 * X * fu, Y0 + (Y1 - Y0) * fv])
            xy = textured_parts._rot(p, r) + np.array([x, y]) + np.array([tx, ty])
            return (xy[0], xy[1], zz)
        b = len(verts)
        verts += [at(fu0, fv0, z0), at(fu1, fv0, z0), at(fu1, fv1, z0), at(fu0, fv1, z0),
                  at(fu0, fv0, z1), at(fu1, fv0, z1), at(fu1, fv1, z1), at(fu0, fv1, z1)]
        for q in ((4, 5, 6, 7), (0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            tris += [(b + q[0], b + q[1], b + q[2]), (b + q[0], b + q[2], b + q[3])]
        uv += [(0.0, 0.0), (1.0, 0.0), (1.0, 0.0), (0.0, 0.0)] * 2     # u along the chip's length
    # The chip only ADDS light: a transparent body (whatever lies under it shows unchanged)
    # plus a glossy reflection and an optional glow, both faded out to the chip's ends by
    # (1 - (2u - 1)^2)^1.5 along its length. PK_CHIP_GLOSS="gain,roughness" (default
    # 0.3,0.4) sets the reflection; PK_CHIP_GLOW a grey glow on the top face for dark scenes,
    # where no light reaches the chip through the cap; PK_CHIP_FADE (default 1.5) the fade's
    # exponent.
    m = bpy.data.materials.get("driver chip") or bpy.data.materials.new("driver chip")
    m.use_nodes = True
    m["pk_role"] = "driver chip"
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sx = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sx.inputs[0])
    t = nt.nodes.new("ShaderNodeMath"); t.operation = "MULTIPLY_ADD"
    t.inputs[1].default_value, t.inputs[2].default_value = 2.0, -1.0
    nt.links.new(sx.outputs["X"], t.inputs[0])
    sq = nt.nodes.new("ShaderNodeMath"); sq.operation = "POWER"; sq.inputs[1].default_value = 2.0
    nt.links.new(t.outputs[0], sq.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt.links.new(sq.outputs[0], inv.inputs[1])
    fade = nt.nodes.new("ShaderNodeMath"); fade.operation = "POWER"
    fade.inputs[1].default_value = float(os.environ.get("PK_CHIP_FADE", 1.5))   # higher = a shorter mark
    nt.links.new(inv.outputs[0], fade.inputs[0])
    gain, rough = (float(v) for v in os.environ.get("PK_CHIP_GLOSS", "0.3,0.4").split(","))
    g = nt.nodes.new("ShaderNodeMath"); g.operation = "MULTIPLY"; g.inputs[1].default_value = gain
    nt.links.new(fade.outputs[0], g.inputs[0])
    if os.environ.get("PK_CHIP_TOP_ONLY"):          # reflect on the top face only: the side faces
        geo0 = nt.nodes.new("ShaderNodeNewGeometry")   # draw a bright edge along the image's bottom
        nz0 = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo0.outputs["Normal"], nz0.inputs[0])
        up0 = nt.nodes.new("ShaderNodeMath"); up0.operation = "GREATER_THAN"; up0.inputs[1].default_value = 0.5
        nt.links.new(nz0.outputs["Z"], up0.inputs[0])
        g2 = nt.nodes.new("ShaderNodeMath"); g2.operation = "MULTIPLY"
        nt.links.new(g.outputs[0], g2.inputs[0]); nt.links.new(up0.outputs[0], g2.inputs[1])
        g = g2
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = rough
    nt.links.new(g.outputs[0], gl.inputs["Color"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(gl.outputs[0], add.inputs[1])
    top = add
    glow = float(os.environ.get("PK_CHIP_GLOW", 0))
    if glow > 0:
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (0.75, 0.8, 0.9, 1)
        k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = glow
        nt.links.new(fade.outputs[0], k.inputs[0])
        # only the chip's top face glows: lit side faces read as a thicker band over the panel
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nz = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], nz.inputs[0])
        up = nt.nodes.new("ShaderNodeMath"); up.operation = "GREATER_THAN"; up.inputs[1].default_value = 0.5
        nt.links.new(nz.outputs["Z"], up.inputs[0])
        k2 = nt.nodes.new("ShaderNodeMath"); k2.operation = "MULTIPLY"
        nt.links.new(k.outputs[0], k2.inputs[0]); nt.links.new(up.outputs[0], k2.inputs[1])
        nt.links.new(k2.outputs[0], em.inputs["Strength"])
        add2 = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(add.outputs[0], add2.inputs[0]); nt.links.new(em.outputs[0], add2.inputs[1])
        top = add2
    nt.links.new(top.outputs[0], out.inputs["Surface"])
    textured_parts._mesh(root.name + " driver chips", verts, tris, uv, m, root)
    return len(kb)


def matrix_edge(root, board, side, strength=6.0, kle_path=KLE, atlas_name="screens_layer0"):
    """A thin line of light just below each lit display's pixel area: the edge of the OLED
    glass, which carries the panel's own light (the photos show it under every lit key and
    not under dark ones). Along its length its brightness follows the column sums of the
    key's lit pixels (blurred over about 2 px), so it is brightest under the legend and fades
    out to both sides, in the legend's colour. A 0.2 mm strip, 0.05 mm below the pixel area,
    across its width; named "... lit legends edge", so PK_PASSES counts it with the
    legends. Returns how many."""
    atlas = json.load(open(os.path.join(TEX, atlas_name + ".json"), encoding="utf-8"))
    (aw, ah), (cw, ch) = atlas["size"], atlas["cell"]
    img = bpy.data.images.load(os.path.join(TEX, atlas_name + ".png"), check_existing=True)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[::-1, :, :3]
    kb = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, kb)
    kle = [k for k in keymatch.kle_keys(kle_path) if (int(k[0].split(",")[0]) < 5) == (side == "left")]
    labels, _ = keymatch.match(np.array([[x, -y] for x, y, _ in kb]), kle)
    X, Y0, Y1 = textured_parts.DISP_X, textured_parts.DISP_Y0, textured_parts.DISP_Y1
    z = textured_parts.DISP_TOP + dz + LIFT
    # PK_EDGE_AT="from,to": mm below the active area (default 0.05,0.25). 0.35,0.55 puts it
    # under the dark panel window (which ends 0.3 mm below the active area), on its edge
    e0, e1 = (float(v) for v in os.environ.get("PK_EDGE_AT", "0.05,0.25").split(","))
    fv0, fv1 = keymatch.A_V0 - e1 / 11.0, keymatch.A_V0 - e0 / 11.0
    g = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2)
    g /= g.sum()
    keys, rows = [], []
    for (x, y, r), label in zip(kb, labels):
        cell = atlas["keys"].get(label)
        if cell is None:
            continue
        c = px[cell[1]:cell[1] + ch, cell[0]:cell[0] + cw] * np.array(LIT_TINT[:3])
        if c.max() <= 0.1:
            continue
        prof = np.stack([np.convolve(c[..., k].sum(0), g, mode="same") for k in range(3)], -1)   # (cw, 3)
        keys.append((x, y, r))
        rows.append(prof)
    if not rows:
        return 0
    rows = np.array(rows) / max(np.array(rows).max(), 1e-6)          # (n, cw, 3), the brightest column 1
    n = len(rows)
    tex = bpy.data.images.new(f"matrix edge {atlas_name}", cw, n, float_buffer=True)
    rgba = np.concatenate([rows, np.ones((n, cw, 1))], -1)
    tex.pixels.foreach_set(rgba.astype(np.float32).ravel())
    m = bpy.data.materials.new(f"matrix edge {atlas_name}")
    m.use_nodes = True
    nt = m.node_tree
    # only ADDS light: an opaque strip drew a black band under the image on light shots
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image, t.interpolation = tex, "Linear"
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(t.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = strength * 0.25
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    verts, tris, uv = [], [], []
    for i, (x, y, r) in enumerate(keys):
        def at(fu, fv):
            p = np.array([-X + 2 * X * fu, Y0 + (Y1 - Y0) * fv])
            xy = textured_parts._rot(p, r) + np.array([x, y]) + np.array([tx, ty])
            return (xy[0], xy[1], z)
        base = len(verts)
        verts += [at(keymatch.A_U0, fv0), at(keymatch.A_U1, fv0), at(keymatch.A_U1, fv1), at(keymatch.A_U0, fv1)]
        v = (i + 0.5) / n
        uv += [(0, v), (1, v), (1, v), (0, v)]
        tris += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    textured_parts._mesh(f"{root.name} lit legends edge", verts, tris, uv, m, root)
    return n


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
