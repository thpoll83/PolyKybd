"""The per-key RGB LEDs lit, for a night shot like the docs' rgb-keycaps-closeup.

`leds(root, board, hues)` puts a small coloured point light on every
XL-3030RGBC (WS2812B) footprint of the board, in the board frame that
textured_parts.fit() finds, so each light sits on the PCB under its switch.
The colour follows the LED's x across the half: a hue gradient, as an RGB
matrix gradient effect lays one across the board.

`night(sc)` turns the studio off: a black world, the studio lights and the
cove gone, and a black floor under the board.
`clear_case()` makes the printed case clear resin, as on the photo's board.
"""
import colorsys
import os
import math
import re

import bpy
import mathutils
import numpy as np

import textured_parts

LED_Z = 0.9          # mm above the PCB's key frame: the 3030 package's top face


def board_leds(board):
    """[(x, y_up)] of every XL-3030RGBC footprint, y flipped to point up."""
    t = open(board, encoding="utf-8").read()
    return [(float(m.group(1)), -float(m.group(2))) for m in re.finditer(
        r'\n\t\(footprint "poly_kb:XL-3030RGBC-WS2812B"\n\t\t\(layer "F\.Cu"\)\n'
        r'(?:\t\t[^\n]*\n)*?\t\t\(at ([-\d.]+) ([-\d.]+)', t)]


def leds(root, board, hues, energy=0.02, radius=0.0012):
    """One point light per LED; hues = (left, right) in degrees across x."""
    (tx, ty), dz = textured_parts.fit(root, textured_parts.board_keys(board))
    pts = board_leds(board)
    xs = np.array([p[0] for p in pts])
    x0, x1 = xs.min(), xs.max()
    for i, (x, y) in enumerate(pts):
        h = hues[0] + (hues[1] - hues[0]) * (x - x0) / (x1 - x0)
        d = bpy.data.lights.new(f"led {i}", "POINT")
        d.color = colorsys.hsv_to_rgb((h % 360) / 360, 1.0, 1.0)
        d.energy = energy
        d.shadow_soft_size = radius
        o = bpy.data.objects.new(f"led {i}", d)
        o.location = root.matrix_world @ mathutils.Vector((x + tx, y + ty, LED_Z + dz))
        bpy.context.scene.collection.objects.link(o)
    return len(pts)


def night(sc):
    for o in [o for o in sc.objects if o.type == "LIGHT" and not o.name.startswith("led ")]:
        bpy.data.objects.remove(o)
    floor = bpy.data.materials.get("floor")
    if floor:
        floor.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1)
    w = sc.world
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = os.environ.get("PK_LOOK", "AgX - Base Contrast")


def _keep_small_parts_opaque(span=100.0):
    """The case, the status display holder and the lids share one source
    colour, so the import merges them into one mesh with one material. On
    the photographed board only the case is clear: give every piece of that
    mesh narrower than `span` mm (the lid, the holder) an opaque copy of the
    material, before clear_case() changes it. The VRML gives each triangle
    its own corners, so the pieces are found after welding them."""
    import bmesh
    for o in [o for o in bpy.data.objects if o.type == "MESH" and o.active_material
              and o.active_material.get("pk_role") == "case PLA"]:
        mat = o.active_material
        # in world metres, then mm: the parent chain ends at a splay pivot,
        # not at the board root, so no ancestor's frame is the board's
        M = np.array(o.matrix_world) * np.array([[1000], [1000], [1000], [1]])
        bm = bmesh.new()
        bm.from_mesh(o.data)
        # 10 um: the VRML's 0.1-inch coordinates round apart by more than 1 um,
        # and at 1 um nothing welded, so every triangle counted as a small part
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01 / np.linalg.norm(M[:3, 0]))
        seen, small, sizes = set(), [], []
        for f0 in bm.faces:
            if f0 in seen:
                continue
            part, todo = [], [f0]
            seen.add(f0)
            while todo:
                f = todo.pop()
                part.append(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g not in seen:
                            seen.add(g)
                            todo.append(g)
            co = np.array([v.co[:] for f in part for v in f.verts]) @ M[:3, :3].T
            sizes.append((round(float(np.ptp(co[:, 0]))), round(float(np.ptp(co[:, 1]))), len(part)))
            if np.ptp(co[:, 0]) < span and np.ptp(co[:, 1]) < span:
                small.append(part)
        if small:
            opaque = mat.copy()
            opaque.name = mat.name + " opaque"
            opaque["pk_role"] = "case PLA opaque"
            o.data.materials.append(opaque)
            idx = len(o.data.materials) - 1
            for part in small:
                for f in part:
                    f.material_index = idx
        bm.to_mesh(o.data)
        bm.free()
        o.data.set_sharp_from_angle(angle=math.radians(30))
        print("case parts kept opaque:", len(small), "of", len(sizes), sorted(sizes, key=lambda t: -t[2])[:6])


def clear_case():
    """Only the case: the lid and the display holder stay opaque print."""
    _keep_small_parts_opaque()
    for m in bpy.data.materials:
        if m.get("pk_role") == "case PLA":
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (1, 1, 1, 1)
            b.inputs["Transmission Weight"].default_value = 1.0
            b.inputs["Roughness"].default_value = 0.05
            b.inputs["IOR"].default_value = 1.5
            b.inputs["Specular IOR Level"].default_value = 0.5


def _hue_colour(nt, x0, x1, hues):
    """A colour node: the hue gradient over world x from x0 (hues[0]) to x1."""
    n = nt.nodes
    geo = n.new("ShaderNodeNewGeometry")
    sep = n.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = x0, x1
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = hues[0] / 360, hues[1] / 360
    nt.links.new(sep.outputs["X"], mr.inputs["Value"])
    wrap = n.new("ShaderNodeMath")
    wrap.operation = "FRACT"
    nt.links.new(mr.outputs["Result"], wrap.inputs[0])
    col = n.new("ShaderNodeCombineColor")
    col.mode = "HSV"
    col.inputs[1].default_value = col.inputs[2].default_value = 1.0
    nt.links.new(wrap.outputs[0], col.inputs[0])
    return col.outputs[0]


def glow(role, x0, x1, hues, strength):
    """Volume emission in every material of `role`, coloured by the gradient:
    light trapped in clear plastic. A wall seen edge-on holds a longer path
    than one seen face-on, so the rims glow brightest, as on the photo."""
    for m in bpy.data.materials:
        if m.get("pk_role") != role:
            continue
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = strength
        nt.links.new(_hue_colour(nt, x0, x1, hues), em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs["Volume"])


def led_span(root, board):
    """World x of the leftmost and rightmost LED."""
    (tx, ty), dz = textured_parts.fit(root, textured_parts.board_keys(board))
    xs = [(root.matrix_world @ mathutils.Vector((x + tx, y + ty, 0))).x for x, y in board_leds(board)]
    return min(xs), max(xs)



def led_points(root, board, hues, z):
    """World position and colour of every LED, raised z mm above the PCB."""
    (tx, ty), dz = textured_parts.fit(root, textured_parts.board_keys(board))
    pts = board_leds(board)
    xs = np.array([p[0] for p in pts])
    x0, x1 = xs.min(), xs.max()
    pos = np.array([tuple(root.matrix_world @ mathutils.Vector((x + tx, y + ty, z + dz))) for x, y in pts])
    cols = np.array([colorsys.hsv_to_rgb(((hues[0] + (hues[1] - hues[0]) * (x - x0) / (x1 - x0)) % 360) / 360, 1, 1)
                     for x, y in pts])
    return pos, cols


def glow_from_leds(root, board, role, hues, radius, strength, z=8.0):
    """Surface emission on `role` that fades with distance from each key's
    own LED: per vertex, the nearest LED's colour weighted by
    (1 / (1 + (d / radius)^2))^2, stored as the colour attribute "led" and added
    to the material's surface shader, weighted by the square of Layer Weight's
    Facing so edge-on faces (the rims) carry it. The even glow() stays
    underneath; this puts the light where the LED is and lets the far corners
    fall off."""
    pos, cols = led_points(root, board, hues, z)
    for o in root.children_recursive:
        if o.type != "MESH" or not o.active_material or o.active_material.get("pk_role") != role:
            continue
        mw = np.array(o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        w = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        d2 = ((w[:, None, :] - pos[None]) ** 2).sum(-1)
        k = d2.argmin(1)
        wt = (1.0 / (1.0 + d2[np.arange(len(w)), k] / radius ** 2)) ** 2
        rgb = cols[k] * wt[:, None]
        attr = o.data.color_attributes.get("led") or o.data.color_attributes.new("led", "FLOAT_COLOR", "POINT")
        attr.data.foreach_set("color", np.hstack([rgb, np.ones((len(w), 1))]).ravel())
    for m in bpy.data.materials:
        if m.get("pk_role") != role:
            continue
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "led"
        # edge-on faces carry it, as the rims of a lit clear cap do
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.5
        sq = nt.nodes.new("ShaderNodeMath")
        sq.operation = "MULTIPLY"
        nt.links.new(lw.outputs["Facing"], sq.inputs[0])
        nt.links.new(lw.outputs["Facing"], sq.inputs[1])
        k = nt.nodes.new("ShaderNodeMath")
        k.operation = "MULTIPLY"
        k.inputs[1].default_value = strength
        nt.links.new(sq.outputs[0], k.inputs[0])
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(at.outputs["Color"], em.inputs["Color"])
        nt.links.new(k.outputs[0], em.inputs["Strength"])
        old = out.inputs["Surface"].links[0].from_socket
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(old, add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], out.inputs["Surface"])


def emitters(root, board, hues, strength, size=3.0, z=4.4):
    """A 3x3 mm emissive square over every LED footprint, facing up, in the
    LED's colour: the light source for a physically lit render, where the
    light reaches the caps only by refraction through the switch and the cap
    (no glow() or glow_from_leds()).

    It sits `z` mm above the PCB, in the plate opening where the frosted
    diffuser frame is: on the board it is that frame which glows. The bare
    LED (LED_Z) lies under the plate, and from there almost nothing reaches
    the caps in Cycles (image mean 5.9 against 30 here); the frame itself is
    hidden for these renders, because its frosted resin traps the light."""
    pos, cols = led_points(root, board, hues, z)
    h = size / 2000
    for i, (p, c) in enumerate(zip(pos, cols)):
        me = bpy.data.meshes.new(f"led emitter {i}")
        me.from_pydata([(p[0] - h, p[1] - h, p[2]), (p[0] + h, p[1] - h, p[2]),
                        (p[0] + h, p[1] + h, p[2]), (p[0] - h, p[1] + h, p[2])], [], [(0, 1, 2, 3)])
        m = bpy.data.materials.new(f"led emitter {i}")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*c, 1)
        em.inputs["Strength"].default_value = strength
        nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
        me.materials.append(m)
        o = bpy.data.objects.new(f"led emitter {i}", me)
        bpy.context.scene.collection.objects.link(o)
    return len(pos)


def clear_flex(dim, roughness):
    """The keycap display flex for the night shot: a clear amber film that
    neither reflects nor scatters, with copper traces that still shine. At its
    studio values (materials.FLEX_*: satin film, transmission 0.3) the film
    lit up the space under every cap far brighter than the photo shows. Film:
    full transmission, no specular, no coat, `roughness`; traces (the trace
    mask, where there is one) fully metallic. Base colour times `dim`."""
    for m in bpy.data.materials:
        if m.get("pk_role") not in ("flex cable", "flex textured"):
            continue
        nt = m.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        base = b.inputs["Base Color"]
        if dim != 1.0 and base.links:
            mul = nt.nodes.new("ShaderNodeMix")
            mul.data_type = "RGBA"
            mul.blend_type = "MULTIPLY"
            mul.inputs["Factor"].default_value = 1.0
            # the Mix node carries float, vector and colour sockets under the same names
            a, b_in = [i for i in mul.inputs if i.type == "RGBA"]
            nt.links.new(base.links[0].from_socket, a)
            b_in.default_value = (dim, dim, dim, 1)
            nt.links.new(next(o for o in mul.outputs if o.type == "RGBA"), base)
        elif dim != 1.0:
            c = base.default_value
            base.default_value = (c[0] * dim, c[1] * dim, c[2] * dim, c[3])
        for name, value in (("Transmission Weight", 1.0), ("Specular IOR Level", 0.0)):
            for l in list(b.inputs[name].links):
                nt.links.remove(l)
            b.inputs[name].default_value = value
        if not b.inputs["Coat Weight"].links:
            b.inputs["Coat Weight"].default_value = 0.0
        if "trace rough" in nt.nodes:
            # metallic overrides transmission, so the traces stay opaque copper
            nt.nodes["trace rough"].inputs["To Min"].default_value = roughness
            nt.nodes["trace metal"].inputs[1].default_value = 1.0
        else:
            b.inputs["Roughness"].default_value = roughness


def clear_diffuser(roughness=0.15):
    """The LED diffuser frame, less frosted. At its studio roughness (0.45,
    transmission 0.85) a camera path almost never finds its way through the
    frame to a 3 mm LED, so a physically lit render (emitters()) went dark:
    with the frame hidden the caps lit up, with it in place 4x the LED power
    changed the image mean by 2%."""
    for m in bpy.data.materials:
        if m.get("pk_role") == "diffuser resin":
            b = m.node_tree.nodes["Principled BSDF"]
            b.inputs["Transmission Weight"].default_value = 1.0
            b.inputs["Roughness"].default_value = roughness



INDICATORS = {"D1": (1.0, 0.03, 0.01), "D5": (0.05, 1.0, 0.05), "D6": (1.0, 0.65, 0.0)}   # red, green, yellow 0805s


def indicator_leds(root, board, power, radius=float(os.environ.get("PK_INDICATOR_RADIUS", 0.002)), z=-2.0):
    """The three 0805 indicator LEDs on the back of a half's PCB (D1 red,
    D5 green, D6 yellow, by its inner edge): a point light each, `z` mm
    below the key frame, at `power` W, `radius` m in size (PK_INDICATOR_RADIUS:
    a larger source gives a softer, more diffuse glow at the same power). Under the PCB they light the clear
    case from inside, so their colours catch its edges."""
    t = open(board, encoding="utf-8").read()
    (tx, ty), dz = textured_parts.fit(root, textured_parts.board_keys(board))
    out = []
    for ref, colour in INDICATORS.items():
        i = t.index(f'(property "Reference" "{ref}"')
        s = t.rindex("\n\t(footprint ", 0, i)
        x, y = (float(v) for v in re.search(r"\(at ([-\d.]+) ([-\d.]+)", t[s:i]).groups())
        d = bpy.data.lights.new(f"{root.name} {ref}", "POINT")
        d.color, d.energy, d.shadow_soft_size = colour, power, radius
        o = bpy.data.objects.new(f"{root.name} {ref}", d)
        o.location = root.matrix_world @ mathutils.Vector((x + tx, -y + ty, z + dz))
        # the source itself is not seen: a visible sphere renders, out of
        # focus, as a hard-edged disc; only what it lights is
        o.visible_camera = False
        bpy.context.scene.collection.objects.link(o)
        haze = float(os.environ.get("PK_INDICATOR_HAZE", 0))
        if haze > 0 and ref == "D1":              # only the red power LED gets a glow of its own
            _haze(o.location, colour, haze, float(os.environ.get("PK_HAZE_RADIUS", 0.012)))
        out.append(ref)
    return out


def case_indicator_glow(root, board, strength, radius=12.0, z=-2.0):
    """The indicator LEDs' light in the clear case, as surface emission on the
    case's edge-on faces: per vertex, the sum over D1/D5/D6 of the LED's
    colour times (1 / (1 + (d / radius)^2))^2, d in mm, stored as the colour
    attribute "indicator" and added to the case material's surface. A point
    light inside a clear solid never reaches the camera in Cycles (shadow
    rays stop at glass), so indicator_leds() alone left the case dark."""
    t = open(board, encoding="utf-8").read()
    (tx, ty), dz = textured_parts.fit(root, textured_parts.board_keys(board))
    pos, cols = [], []
    for ref, colour in INDICATORS.items():
        i = t.index(f'(property "Reference" "{ref}"')
        s = t.rindex("\n\t(footprint ", 0, i)
        x, y = (float(v) for v in re.search(r"\(at ([-\d.]+) ([-\d.]+)", t[s:i]).groups())
        pos.append((x + tx, -y + ty, z + dz))
        cols.append(colour)
    pos, cols = np.array(pos), np.array(cols)
    inv = root.matrix_world.inverted()
    for o in root.children_recursive:
        if o.type != "MESH" or not o.active_material or o.active_material.get("pk_role") != "case PLA":
            continue
        m = np.array(inv @ o.matrix_world)
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get("co", co)
        p = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        w = (1.0 / (1.0 + ((p[:, None] - pos[None]) ** 2).sum(-1) / radius ** 2)) ** 2
        rgb = w @ cols
        a = o.data.color_attributes.get("indicator") or o.data.color_attributes.new("indicator", "FLOAT_COLOR", "POINT")
        a.data.foreach_set("color", np.hstack([rgb, np.ones((len(p), 1))]).ravel())
        mat = o.active_material
        if mat.get("pk_indicator"):
            continue
        mat["pk_indicator"] = 1
        nt = mat.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "indicator"
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.5
        k = nt.nodes.new("ShaderNodeMath")
        k.operation = "MULTIPLY"
        k.inputs[1].default_value = strength
        nt.links.new(lw.outputs["Facing"], k.inputs[0])
        em = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(at.outputs["Color"], em.inputs["Color"])
        nt.links.new(k.outputs[0], em.inputs["Strength"])
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(out.inputs["Surface"].links[0].from_socket, add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], out.inputs["Surface"])


def _haze(loc, colour, strength, radius):
    """A soft glow around a light: a sphere of volume emission whose density
    falls off smoothly to zero at `radius` m, so there is no edge to see."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=loc, segments=24, ring_count=12)
    o = bpy.context.active_object
    o.name = "indicator haze"
    m = bpy.data.materials.new("indicator haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    out = nt.nodes["Material Output"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    sc = nt.nodes.new("ShaderNodeMapping")
    sc.inputs["Scale"].default_value = (1 / radius,) * 3     # the gradient reaches 0 at the sphere: no edge
    nt.links.new(tc.outputs["Object"], sc.inputs["Vector"])
    nt.links.new(sc.outputs["Vector"], grad.inputs["Vector"])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0           # bright core, long soft tail
    nt.links.new(grad.outputs["Fac"], pw.inputs[0])
    k = nt.nodes.new("ShaderNodeMath")
    k.operation = "MULTIPLY"
    k.inputs[1].default_value = strength
    nt.links.new(pw.outputs[0], k.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*colour, 1)
    nt.links.new(k.outputs[0], em.inputs["Strength"])
    nt.links.new(em.outputs[0], out.inputs["Volume"])
    o.data.materials.append(m)
    return o
