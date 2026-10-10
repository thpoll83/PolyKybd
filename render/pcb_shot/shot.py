"""Render the imported board socket side up, as a product shot.

    PCB2BLENDER=<checkout> PK_HDRI=<studio .hdr> blender-5.1 -b --python render/pcb_shot/shot.py -- \
        out.png <samples> <width> <scene.blend> [<board.pcb3d>: cut the slots, mark the parts]

The scene is import.py's .blend. Lighting is a studio HDRI (Poly Haven's CC0
studio_small_09, 2k) for the fill and the reflections, plus one area key for
clean directional shadows; camera rays see a flat light grey instead of the
HDRI. The view transform is Khronos PBR Neutral, which keeps base colours as
authored: AgX turned the mask and the parts pastel. Under PBR Neutral a
bright highlight clips rather than rolls off, so the light levels are low and
exposure is left at 0. Every setting below has a PK_* override.
"""
import math
import os
import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
out, samples, width = argv[0], int(argv[1]), int(argv[2])
env = os.environ.get
# pcb2blender's materials use node types its add-on defines: register it, then
# open the scene, or every material renders white
sys.path.insert(0, env("PCB2BLENDER", "/tmp/pcb2blender"))
import pcb2blender_importer  # noqa: E402

pcb2blender_importer.register()
bpy.ops.wm.open_mainfile(filepath=argv[3])
sc = bpy.context.scene
pcb = bpy.data.objects["PCB_left"]

# The stock models' colours, matched to the Rev.2 photo (sRGB samples in the
# comments; they are lit values, so the albedos sit a little below them).
# mat4cad reads the near-black plastics as mid grey and the Kailh contacts'
# gold as plastic. Keyed on the colour the import gives each material.
COLOR_MATCH = {
    (0.098, 0.098, 0.098): ("PLASTIC", (0.008, 0.0075, 0.007), env("PK_HS_BODY_VAR", "MATTE")),  # Kailh socket body: #292422, matte, no coat (below)
    (0.147, 0.144, 0.144): ("PLASTIC", (0.045, 0.045, 0.043)),    # IC, diode, SOT bodies: RP2040 #74756f
    (0.159, 0.159, 0.159): ("PLASTIC", (0.045, 0.045, 0.043)),    # crystal lid
    (0.08, 0.084, 0.093): ("PLASTIC", (0.012, 0.012, 0.013)),     # resistor bodies
    (0.078, 0.078, 0.089): ("PLASTIC", (0.012, 0.012, 0.013)),    # FH34 housing
    (0.296, 0.22, 0.138): ("PLASTIC", (0.25, 0.27, 0.30)),        # FH34 actuator: grey #aeb8c2
    # Kailh contacts: polished tin, #cec5bb. The model bends them from thin
    # sheet with gaps; matte or semi-matte metal read as a frosted glass box,
    # polished reads as the solid silver tab of the photo. PK_DEBUG_COLOR=r,g,b
    # paints one source colour red, to see which faces it covers.
    (0.956, 0.956, 0.965): ("METAL", tuple([float(env("PK_HS_GREY", 0.92))] * 3), env("PK_HS_VAR", "GLOSSY")),
    (0.376, 0.266, 0.212): ("PLASTIC", (0.17, 0.09, 0.045)),      # ceramic capacitors: dark brown
    (0.831, 0.68, 0.065): ("PLASTIC", (0.30, 0.18, 0.03)),        # tantalum body: #f8d973 in the photo, darker here
    (0.807, 0.423, 0.147): ("PLASTIC", (0.35, 0.16, 0.05)),       # tantalum polarity band
    # the contacts' gold insert: imported pale, it read as a cream frosted box
    (0.956, 0.896, 0.651): ("METAL", (0.80, 0.55, 0.17)),         # Kailh contact insert: gold #a98435
}
# The FH34 sockets share their housing colour with the 74HC595 bodies, so
# COLOR_MATCH cannot reach them: before it runs, their own copies take the photo's colours, a
# mid-grey housing (the photo's #7a7a77, darkened: the key light falls
# square on its top face) and a dark brown-grey actuator (#383433).
FH34 = {(0.078, 0.078, 0.089): (0.13, 0.13, 0.123), (0.296, 0.22, 0.138): (0.040, 0.034, 0.033)}
copies = {}
for o in pcb.children_recursive:
    if o.type != "MESH" or not o.name.startswith("FH34SRJ"):
        continue
    for slot in o.material_slots:
        m = slot.material
        n = m.node_tree.nodes.get("Mat4cad BSDF") if m and m.node_tree else None
        if n is None:
            continue
        src = next((k for k in FH34 if max(abs(a - b) for a, b in zip(k, n.inputs["Color"].default_value[:3])) < 0.004),
                   None)
        if src is None:
            continue
        if m.name not in copies:
            c = m.copy()
            c.node_tree.nodes["Mat4cad BSDF"].mat_base = "PLASTIC"
            c.node_tree.nodes["Mat4cad BSDF"].inputs["Color"].default_value = (*FH34[src], 1)
            copies[m.name] = c
        slot.material = copies[m.name]
print("FH34 copies", len(copies))

done = set()
for o in pcb.children_recursive:
    if o.type != "MESH":
        continue
    for m in o.data.materials:
        n = m.node_tree.nodes.get("Mat4cad BSDF") if m and m.use_nodes else None
        if n is None or m.name in done:
            continue
        done.add(m.name)
        src = tuple(round(x, 3) for x in n.inputs["Color"].default_value[:3])
        hit = next((v for k, v in COLOR_MATCH.items() if max(abs(a - b) for a, b in zip(k, src)) < 0.004), None)
        if hit and env("PK_DEBUG_COLOR") and src == tuple(float(v) for v in env("PK_DEBUG_COLOR").split(",")):
            hit = ("PLASTIC", (1.0, 0.0, 0.0))
        if hit:
            n.mat_base = hit[0]
            if hit[1]:
                n.inputs["Color"].default_value = (*hit[1], 1)
            if len(hit) > 2:
                n.mat_variant = hit[2]
            # mat4cad's matte plastic carries a glossy clear coat (0.1, roughness
            # 0.2) that lights every edge of the black hotswap body
            if src == (0.098, 0.098, 0.098):
                n.node_shader.inputs["Coat Weight"].default_value = 0.0
        # mat4cad rounds every edge's shading with a bevel node, 0.05 mm by
        # default: on a 1.6 x 0.8 mm capacitor that lights a wide rim along
        # each edge and corner. Set after the recolour, which resets it.
        for b in n.node_tree.nodes:
            if b.bl_idname == "ShaderNodeBevel":
                b.inputs["Radius"].default_value = float(env("PK_BEVEL", 0.015)) * 1e-3
print("recoloured", len(done), "materials")



def lin(h):
    return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4)) + (1.0,)


# the Rev.2 boards' redder purple, not pcb2blender's blue-violet preset (7448aa/3b2359).
# Set here: a custom stackup colour reaches the importer as 0..255 and renders white.
for m in bpy.data.materials:
    for n in (m.node_tree.nodes if m.use_nodes else []):
        if n.bl_idname == "ShaderNodeBsdfPcbSolderMask":
            n.soldermask = "CUSTOM"
            n.inputs["Light Color"].default_value = lin(env("PK_MASK_LIGHT", "9a55b0"))
            n.inputs["Dark Color"].default_value = lin(env("PK_MASK_DARK", "5a2a70"))
            n.inputs["Roughness"].default_value = float(env("PK_MASK_ROUGH", 0.4))
            print("mask set in", m.name)

# Cut the plated slots. KiCad's VRML export, which pcb2blender builds the board
# from, cuts round drills only, so the 9.76 x 1.7 mm flex slots (each key's
# pad 3) arrive as solid board. The .pcb3d keeps every pad; a pad's position
# maps onto the board through the solder joints, which are named after their
# pads. Each slot becomes a capsule cutter, its walls gold like the ENIG pad.
if len(argv) > 4:
    import tomllib
    import zipfile
    with zipfile.ZipFile(argv[4]) as z:
        pads = {n[5:-5]: tomllib.loads(z.read(n).decode()) for n in z.namelist()
                if n.startswith("pads/") and n.endswith(".toml")}
    board = next(o for o in [pcb] + list(pcb.children) if o.type == "MESH" and o.name.startswith("PCB_"))
    inv = board.matrix_world.inverted()
    # offset from pad mm to the board's local metres, fitted on the solder joints
    fit = [(pads[o.name[7:]]["position"], inv @ o.matrix_world.translation) for o in pcb.children_recursive
           if o.name.startswith("SOLDER_") and o.name[7:] in pads]
    ox = sum(w.x - p[0] * 1e-3 for p, w in fit) / len(fit)
    oy = sum(w.y + p[1] * 1e-3 for p, w in fit) / len(fit)
    err = max(max(abs(w.x - (p[0] * 1e-3 + ox)), abs(w.y - (-p[1] * 1e-3 + oy))) for p, w in fit)
    print("slot fit on %d joints, worst %.3f mm" % (len(fit), err * 1e3))
    assert err < 1e-4, err
    slots = [p for p in pads.values() if p["drill_shape"] == "UNKNOWN" and p["drill_size"][0] != p["drill_size"][1]]
    import bmesh
    bm = bmesh.new()
    for p in slots:
        L, W = (v * 1e-3 for v in p["drill_size"])
        rot = -p["rotation"]                      # KiCad's y points down, the board's up
        if W > L:
            L, W = W, L
            rot += math.pi / 2
        r, half, seg = W / 2, (L - W) / 2, 12
        ring = [(half + r * math.cos(a), r * math.sin(a)) for a in [math.pi / 2 - math.pi * i / seg for i in range(seg + 1)]]
        ring += [(-half - r * math.cos(a), -r * math.sin(a)) for a in [math.pi / 2 - math.pi * i / seg for i in range(seg + 1)]]
        cx, cy = p["position"][0] * 1e-3 + ox, -p["position"][1] * 1e-3 + oy
        c, sn = math.cos(rot), math.sin(rot)
        verts = [[bm.verts.new((cx + x * c - y * sn, cy + x * sn + y * c, z)) for x, y in ring] for z in (-0.01, 0.01)]
        # ring runs clockwise from above: wind every face so its normal points out
        bm.faces.new(verts[0]); bm.faces.new(verts[1][::-1])
        for i in range(len(ring)):
            j = (i + 1) % len(ring)
            bm.faces.new((verts[0][j], verts[0][i], verts[1][i], verts[1][j]))
    me = bpy.data.meshes.new("slot cutters"); bm.to_mesh(me); bm.free()
    cutter = bpy.data.objects.new("slot cutters", me)
    sc.collection.objects.link(cutter)
    cutter.matrix_world = board.matrix_world
    plating = bpy.data.materials.new("slot plating"); plating.use_nodes = True
    pb = plating.node_tree.nodes["Principled BSDF"]
    # ENIG over the plated wall: the copper that reads around each slot's edge
    pb.inputs["Base Color"].default_value = (0.90, 0.62, 0.32, 1)
    pb.inputs["Metallic"].default_value = 1.0
    pb.inputs["Roughness"].default_value = float(env("PK_SLOT_ROUGH", 0.3))
    me.materials.append(plating)
    mod = board.modifiers.new("slots", "BOOLEAN")
    mod.operation, mod.object, mod.solver = "DIFFERENCE", cutter, "EXACT"
    mod.material_mode = "TRANSFER"
    bpy.context.view_layer.objects.active = board
    bpy.ops.object.modifier_apply(modifier="slots")
    bpy.data.objects.remove(cutter)
    print("cut", len(slots), "slots")

    # The Kailh hotswap pads carry no paste layer in the footprint, so the
    # importer's SMART mode gives them no solder joint and they render as bare
    # gold. The assembler does solder the socket's tabs to them; add the joints
    # here, placed the way the importer places its own: relative to its joint
    # on an FH34 socket pad, so parent, height and z-scale match. The FH34
    # sockets sit on the hotswap sockets' face; a joint from a part on the
    # other face puts every new joint under the board, out of sight.
    ref = next(o for o in pcb.children_recursive if o.name.startswith("SOLDER_FH34SRJ") and o.name[7:] in pads
               and pads[o.name[7:]]["pad_type"] == "SMD")
    rp = pads[ref.name[7:]]["position"]
    off = ref.location.xy - mathutils.Vector((rp[0], -rp[1])) * 1e-3
    # The importer also put joints in each socket's two switch-pin holes; the
    # switch plugs into the socket and is never soldered, and the joints show
    # through the socket's windows. Remove them.
    for o in [o for o in pcb.children_recursive if o.name.startswith("SOLDER_Kailh_")]:
        bpy.data.objects.remove(o)
    have = {o.name[7:] for o in pcb.children_recursive if o.name.startswith("SOLDER_")}
    solder = ref.data.materials[0]

    # Each socket's two inner contacts sit on pads under its black body, where
    # no solder shows; only the two outer tabs get a joint. Each joint is a
    # fillet: tin wets the land and climbs the tab's end and sides in a
    # concave arc, as a hand-soldered tab does. It is drawn in the socket's
    # own frame (the Kailh model's: x along the socket, y up, origin at the
    # 4 mm centre hole), where the model puts each outer tab, once seated
    # (below), 0.16 mm thick on its pad.
    TABS = ((4.90, 6.66, 4.12, 6.12), (-7.86, -6.10, 1.44, 3.44))   # x0, x1, y0, y1 in mm
    BODY = (-6.10, 4.90)       # the black body's x extent: no tin under it
    h_top, reach = float(env("PK_HS_SOLDER_H", 0.20)), float(env("PK_HS_SOLDER_REACH", 0.8))
    # and a convex bead over each tab's outer end, standing above the tab
    # (0.16 mm) the way the capacitors' joints stand against their ends: a
    # concave fillet alone vanishes at the full image's scale
    bead_h, bead_r = float(env("PK_HS_BEAD_H", 0.35)), float(env("PK_HS_BEAD_R", 0.7))

    def mid(t):
        return (t[0] + t[1]) / 2, (t[2] + t[3]) / 2

    def to_local(c, cs, sn, pos):
        dx, dy = pos[0] - c[0], -(pos[1] - c[1])          # KiCad y points down
        return dx * cs + dy * sn, -dx * sn + dy * cs

    def fillet_mesh(tab, lands):
        x0, x1, y0, y1 = tab
        # the end away from the body, 0.5 mm of it
        cx0, cx1 = (x1 - 0.5, x1) if x0 > 0 else (x0, x0 + 0.5)
        bx0, bx1 = min(l[0] for l in lands), max(l[1] for l in lands)
        by0, by1 = min(l[2] for l in lands), max(l[3] for l in lands)
        nx, ny = int((bx1 - bx0) / 0.04) + 1, int((by1 - by0) / 0.04) + 1
        verts, faces = [], []
        for i in range(nx + 1):
            for k in range(ny + 1):
                x, y = bx0 + (bx1 - bx0) * i / nx, by0 + (by1 - by0) * k / ny
                d = math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1))
                if (not any(l[0] <= x <= l[1] and l[2] <= y <= l[3] for l in lands)
                        or BODY[0] < x < BODY[1] or d >= reach):
                    z = 0.78                                 # sunk under the copper: no tin here
                else:
                    dc = math.hypot(max(cx0 - x, 0, x - cx1), max(y0 - y, 0, y - y1))
                    bead = bead_h * math.sqrt(max(0.0, 1 - (dc / bead_r) ** 2))
                    film = 0.10 if d == 0 else h_top * max(0.0, 1 - d / reach) ** 2
                    z = 0.835 + max(bead, film)              # film under the tab is out of sight
                verts.append((x * 1e-3, y * 1e-3, z * 1e-3))
        for i in range(nx):
            for k in range(ny):
                q = i * (ny + 1) + k
                faces.append((q, q + ny + 1, q + ny + 2, q + 1))
        me = bpy.data.meshes.new("hotswap fillet")
        me.from_pydata(verts, [], faces)
        me.polygons.foreach_set("use_smooth", [True] * len(faces))
        me.materials.append(solder)
        return me

    groups = {}
    for name, p in pads.items():
        if name.startswith("Kailh_"):
            groups.setdefault(name.rsplit("_", 1)[0], []).append((name, p))
    added, worst = 0, 0.0
    for g, members in groups.items():
        holes = [p for n, p in members if p["pad_type"] == "NPTH"]
        c = next(p["position"] for p in holes if abs(p["drill_size"][0] - 3.9878) < 0.01)
        # inner pads lie 6.1-6.7 mm from the centre hole, outer ones 7.4-8.1 mm
        outer = [p for n, p in members if p["pad_type"] == "SMD" and n not in have and not p["has_paste"]
                 and math.dist(c, p["position"]) > 7.0]
        if not outer:
            continue
        # the socket's rotation, from its two small holes 5.08 mm either side of
        # the centre: of the two directions, the one that puts the outer pads
        # on the model's tabs
        best = None
        for q in (p["position"] for p in holes if p["position"] != c):
            a = math.atan2(-(q[1] - c[1]), q[0] - c[0])
            loc = [to_local(c, math.cos(a), math.sin(a), p["position"]) for p in outer]
            err = sum(min(math.dist(l, mid(t)) for t in TABS) for l in loc)
            if best is None or err < best[0]:
                best = (err, a, loc)
        err, a, loc = best
        worst = max(worst, err / len(outer))
        for ti, t in enumerate(TABS):
            lands = [(lx - p["size"][0] / 2, lx + p["size"][0] / 2, ly - p["size"][1] / 2, ly + p["size"][1] / 2)
                     for p, (lx, ly) in zip(outer, loc)
                     if min(TABS, key=lambda u: math.dist((lx, ly), mid(u))) is t]
            if not lands:
                continue
            j = bpy.data.objects.new("SOLDER_%s_tab%d" % (g, ti), fillet_mesh(t, lands))
            sc.collection.objects.link(j)
            j.parent, j.matrix_parent_inverse = ref.parent, ref.matrix_parent_inverse.copy()
            j.location = (*(mathutils.Vector((c[0], -c[1])) * 1e-3 + off), ref.location.z)
            j.rotation_euler.z = a
            j.scale = ref.scale
            added += 1
    print("added", added, "hotswap solder fillets; worst pad-to-tab offset %.2f mm" % worst)
    # A hotswap pad's joint is broad, and at the importer's roughness 0.25 it
    # mirrors the dark studio and reads black. Hand-soldered tin is duller.
    for m in bpy.data.materials:
        for n in (m.node_tree.nodes if m.node_tree else ()):
            if n.bl_idname == "ShaderNodeBsdfSolder":
                n.inputs["Roughness"].default_value = float(env("PK_SOLDER_ROUGH", 0.45))
                # its grain, stretched over a fillet, reads as crumbs
                n.inputs["Texture Strength"].default_value = float(env("PK_SOLDER_GRAIN", 0.35))


# The Kailh model hangs 0.27 mm clear of the board: its contact tabs float
# over their pads. Seat it (the board's socket face is its local -z side).
for o in pcb.children_recursive:
    if o.name.startswith("SW_Hotswap_Kailh"):
        o.location.z += float(env("PK_HS_SEAT", 0.27)) * 1e-3

# socket side up: turn the board over about its long axis, lowest point on the floor
pcb.rotation_euler = (0, math.pi, 0)
bpy.context.view_layer.update()
objs = [pcb] + list(pcb.children_recursive)
pts = [o.matrix_world @ mathutils.Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
lo = mathutils.Vector([min(p[i] for p in pts) for i in range(3)])
hi = mathutils.Vector([max(p[i] for p in pts) for i in range(3)])
pcb.location -= mathutils.Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
bpy.context.view_layer.update()

# Part markings. The stock models carry none, and on the real board the
# RP2040, the flash, the inductors, the crystal and the shift registers show
# their laser marking clearly. The text is what these parts carry: part code
# and a date code. Placed on each body's top face, upright to the camera and
# never mirrored. Needs export.py's <board>.parts.json beside the .pcb3d.
MARKINGS = {                     # ref: (lines, text height in mm)
    "U10": ("RP2-B2\n21/24\nP64M15.00\nTTT", 0.85),
    "U9": ("25Q64ES\nBY2421", 0.32),
    "L1": ("2R2", 1.3), "L2": ("2R2", 1.3),
    "Y1": ("12.000\nTXC", 0.5),
    "U4": ("HC595\n2421", 0.42), "U5": ("HC595\n2421", 0.42), "U6": ("HC595\n2421", 0.42),
    "U7": ("HC595\n2421", 0.42), "U8": ("HC595\n2421", 0.42),
}
parts_json = os.path.splitext(argv[4])[0] + ".parts.json" if len(argv) > 4 else ""
if os.path.exists(parts_json):
    import json
    parts = json.load(open(parts_json))
    laser = bpy.data.materials.new("laser marking"); laser.use_nodes = True
    lb = laser.node_tree.nodes["Principled BSDF"]
    lb.inputs["Base Color"].default_value = (*[float(env("PK_MARK", 0.10))] * 3, 1)
    lb.inputs["Roughness"].default_value = 0.8
    bodies = []
    for o in pcb.children_recursive:
        if o.type == "MESH" and not o.name.startswith("SOLDER_"):
            pts = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
            bodies.append((o, sum((p for p in pts), mathutils.Vector()) / 8, max(p.z for p in pts)))
    for ref, (text, size) in MARKINGS.items():
        part = parts.get(ref)
        if not part:
            continue
        x, y = part["position"]
        at = board.matrix_world @ mathutils.Vector((x * 1e-3 + ox, -y * 1e-3 + oy, 0))
        body, centre, top = min(bodies, key=lambda b: (b[1].x - at.x) ** 2 + (b[1].y - at.y) ** 2)
        if (centre.xy - at.xy).length > 1.5e-3:
            print("marking: no body under", ref)
            continue
        cu = bpy.data.curves.new("mark " + ref, "FONT")
        cu.body, cu.size, cu.align_x, cu.align_y = text, size * 1e-3, "CENTER", "CENTER"
        cu.space_line = 1.05
        ob = bpy.data.objects.new("mark " + ref, cu)
        sc.collection.objects.link(ob)
        ob.data.materials.append(laser)
        angle = (-part["rotation"]) % 180.0          # along the part's edges, upright to the camera
        if angle > 90.0:
            angle -= 180.0
        ob.location = (at.x, at.y, top + 2e-5)
        ob.rotation_euler = (0, 0, math.radians(angle))
        print("marked", ref, body.name, "%.2f mm high" % ((top) * 1e3))

# floor
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
b = fm.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (*[float(env("PK_FLOOR", 0.75))] * 3, 1)
b.inputs["Roughness"].default_value = 0.55
floor.data.materials.append(fm)

# world: the studio HDRI lights and reflects; camera rays see a flat light grey
w = bpy.data.worlds.new("studio"); sc.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
tex = nt.nodes.new("ShaderNodeTexEnvironment")
tex.image = bpy.data.images.load(env("PK_HDRI"))
mapping = nt.nodes.new("ShaderNodeMapping"); coord = nt.nodes.new("ShaderNodeTexCoord")
mapping.inputs["Rotation"].default_value = (0, 0, math.radians(float(env("PK_HDRI_ROT", 0))))
nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
hdr = nt.nodes.new("ShaderNodeBackground"); hdr.inputs["Strength"].default_value = float(env("PK_HDRI_STR", 0.15))
nt.links.new(tex.outputs["Color"], hdr.inputs["Color"])
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)
lp = nt.nodes.new("ShaderNodeLightPath"); mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
nt.links.new(hdr.outputs["Background"], mix.inputs[1]); nt.links.new(bg.outputs["Background"], mix.inputs[2])
o = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(mix.outputs[0], o.inputs["Surface"])

# one key light for clean, directional shadows
tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt); tgt.location = (0, 0, 0.003)
kd = bpy.data.lights.new("key", "AREA"); kd.size = float(env("PK_KEY_SIZE", 0.25)); kd.energy = float(env("PK_KEY", 12))
key = bpy.data.objects.new("key", kd); sc.collection.objects.link(key)
key.location = (-0.35, -0.30, 0.45); key.constraints.new("TRACK_TO").target = tgt

# camera
cd = bpy.data.cameras.new("cam"); cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = float(env("PK_LENS", 70)); cd.clip_start = 0.01
elev, azim, dist = math.radians(float(env("PK_ELEV", 42))), math.radians(float(env("PK_AZIM", -20))), float(env("PK_DIST", 0.45))
cam.location = (dist * math.cos(elev) * math.sin(azim), -dist * math.cos(elev) * math.cos(azim), dist * math.sin(elev))
cam.constraints.new("TRACK_TO").target = tgt
cd.dof.use_dof = False                    # sharp to the last corner, like a focus-stacked product shot

sc.render.engine = "CYCLES"; sc.cycles.samples = samples; sc.cycles.use_denoising = True
sc.view_settings.view_transform = env("PK_VIEW", "Khronos PBR Neutral")   # keeps base colours, AgX pastels them
sc.view_settings.exposure = float(env("PK_EXPOSURE", 0))
if env("PK_LOOK"):
    sc.view_settings.look = env("PK_LOOK")
sc.render.resolution_x, sc.render.resolution_y = width, int(round(width * 0.62))
if env("PK_BORDER"):
    x0, y0, x1, y1 = (float(v) for v in env("PK_BORDER").split(","))
    sc.render.use_border, sc.render.use_crop_to_border = True, True
    sc.render.border_min_x, sc.render.border_min_y, sc.render.border_max_x, sc.render.border_max_y = x0, y0, x1, y1
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
