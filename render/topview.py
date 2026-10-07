"""Top-down, orthographic render of both halves plus the image position of
every display, for PolyKybdHost's layout editor (a "real view" background).

    blender -b render/out/hero.blend --python render/topview.py -- out.png [width] [samples] [kle.json]

Writes out.png and out.json. The json gives, for each of the 72 key displays,
the 72x40 active area as four image-pixel corners in the OLED's own order
(top-left, top-right, bottom-right, bottom-left, so pixel (0, 0) of the
framebuffer is the first corner, legends upright when read from the front),
plus the key's KLE matrix label ("row,col", the label PolyKybdHost's
polykybd-split72.json uses), its board reference and side. The two status
displays are listed separately. Image pixels: origin top-left, x right, y down.

The halves are not splayed (splay 0), the camera looks straight down, so the
picture lines up with the KLE layout up to one scale and offset per half.
Seen from straight above, every flat cap top and the plate mirror what is
directly overhead, so the black card goes there (studio.flag() follows the
camera) and the overhead softbox is hidden from reflections; the card casts
no shadow, so the floor stays evenly lit. The plate is flat as well and
mirrors the same card, so the card glows white, light-linked to the plate
alone: the plate reads silver while the caps still see black.

Matrix labels: each board key is matched to the nearest KLE key after fitting
that half's KLE keys (19.05 mm per U) to the board by a translation; the
largest residual is printed and stored. The two KLE keys with no display
(74 keys, 72 OLEDs) stay unmatched.
"""
import json
import math
import os
import sys

import bpy
import mathutils
import numpy as np
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lighting  # noqa: E402
import materials  # noqa: E402
import studio  # noqa: E402
import textured_parts  # noqa: E402
import bridge_cable  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
width = int(argv[1]) if len(argv) > 1 else 3200
samples = int(argv[2]) if len(argv) > 2 else 96
kle_path = argv[3] if len(argv) > 3 else os.path.join(
    textured_parts.REPO, "..", "PolyKybdHost", "polyhost", "res", "polykybd-split72.json")
if not os.path.exists(kle_path):
    raise SystemExit(f"topview.py needs PolyKybdHost's KLE layout for the matrix labels: {kle_path} "
                     "is missing. Check PolyKybdHost out next to this repo, or pass the file as "
                     "the 4th argument (polyhost/res/polykybd-split72.json).")
U = 19.05
PLATE_SKY = 1.0                             # emission the plate mirrors: 3 reads white, 1.0 silver

# display active area inside the decal (gen_textures.display_front: 12.2 x 11.0 mm
# image, active 9.2 x 5.1 mm at x 1.5, 1.35 mm below the image top; image bottom =
# key -y = the cable side)
A_U0, A_U1 = 1.5 / 12.2, 10.7 / 12.2
A_V0, A_V1 = 1 - 6.45 / 11.0, 1 - 1.35 / 11.0


def kle_keys(path):
    """[(label, cx, cy)] key centres in U, KLE frame (y down), rotations applied."""
    rows = json.load(open(path, encoding="utf-8"))
    keys = []
    r = rx = ry = 0.0
    x = y = 0.0
    for row in rows:
        if not isinstance(row, list):
            continue
        w = h = 1.0
        for item in row:
            if isinstance(item, dict):
                if "r" in item:
                    r = item["r"]
                if "rx" in item:
                    rx = item["rx"]
                    x, y = rx, ry
                if "ry" in item:
                    ry = item["ry"]
                    x, y = rx, ry
                x += item.get("x", 0)
                y += item.get("y", 0)
                w, h = item.get("w", w), item.get("h", h)
                continue
            cx, cy = x + w / 2, y + h / 2
            a = math.radians(r)
            dx, dy = cx - rx, cy - ry
            keys.append((item.split("\n")[0], rx + dx * math.cos(a) - dy * math.sin(a),
                         ry + dx * math.sin(a) + dy * math.cos(a)))
            x += w
            w = h = 1.0
        y += 1
        x = rx
    return keys


def board_refs(board):
    """Reference of every key footprint, in textured_parts.board_keys() order."""
    import re
    t = open(board, encoding="utf-8").read()
    refs = []
    for m in re.finditer(r'\n\t\(footprint "poly_kb:Kailh_socket_MX_Indicators"\n\t\t\(layer "F\.Cu"\)\n', t):
        e = t.find("\n\t)\n", m.start())
        r = re.search(r'"Reference" "([^"]+)"', t[m.start():e])
        refs.append(r.group(1) if r else None)
    return refs


def match(board_xy, kle):
    """Board key centres (KiCad mm, y down) -> KLE labels, by translation fit."""
    pts = np.array([[k[1] * U, k[2] * U] for k in kle])
    t = board_xy.mean(0) - pts.mean(0)
    for _ in range(5):
        d = ((board_xy[:, None] - (pts + t)[None]) ** 2).sum(-1)
        near = d.argmin(1)
        t = (board_xy - pts[near]).mean(0)
    d = ((board_xy[:, None] - (pts + t)[None]) ** 2).sum(-1)
    near = d.argmin(1)
    resid = np.sqrt(d[np.arange(len(near)), near]).max()
    assert len(set(near)) == len(near), "two board keys matched one KLE key"
    return [kle[i][0] for i in near], resid


sc = bpy.context.scene
materials.tag(bpy)
halves = []
for side in ("left", "right"):
    root = bpy.data.objects[f"split72_{side}.wrl"]
    board = os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{side}.kicad_pcb")
    textured_parts.add(root, textured_parts.board_keys(board))
    halves.append((side, root, board))
print("material roles", materials.apply(bpy))
materials.scene_settings(sc)
bridge_cable.remove()                       # no cables in an editor picture
studio.splay(0)
tgt = bpy.data.objects.get("target")
lighting.studio(sc, tgt, 1.0)               # removes every light: before the cove adds its own
studio.cove(sc)
# hidden from reflections AND from transmission: a decal's coat mirrors it up
# through the clear cap, which is a transmission ray, and that path laid a
# white veil over every display
for name in ("overhead", "rim"):
    bpy.data.objects[name].visible_glossy = False
    bpy.data.objects[name].visible_transmission = False
studio.white_look(sc)
bpy.context.view_layer.update()

# frame the keyboard: everything but the studio
skip = {"cove", "flag"}
lo = mathutils.Vector((1e9,) * 3)
hi = -lo
for o in sc.objects:
    if o.type != "MESH" or o.name in skip or o.hide_render:
        continue
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        lo = mathutils.Vector(map(min, lo, w))
        hi = mathutils.Vector(map(max, hi, w))
cam = sc.camera
for c in list(cam.constraints):
    cam.constraints.remove(c)
cam.data.type = "ORTHO"
cam.data.dof.use_dof = False
margin = 1.06
span_x, span_y = (hi.x - lo.x) * margin, (hi.y - lo.y) * margin
cam.data.ortho_scale = max(span_x, span_y)
cam.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 1.0)
cam.rotation_euler = (0, 0, 0)
cam.data.clip_end = 5.0
sc.render.resolution_x = width
sc.render.resolution_y = int(round(width * span_y / span_x))
sc.render.resolution_percentage = 100
studio.flag(sc)                             # straight overhead now
flag = bpy.data.objects["flag"]
flag.visible_shadow = False                 # a mirror for the caps, not a shade
flag.visible_diffuse = False
# The plate is flat too, so it mirrors the same card and went dark. The card
# glows white instead, light-linked to the plate alone: the plate sees a
# white sky and reads as silver, every other object sees a black card.
sky = bpy.data.materials.new("plate sky")
sky.use_nodes = True
sky["pk_role"] = "studio"
nt = sky.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = PLATE_SKY
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
flag.data.materials.clear()
flag.data.materials.append(sky)
# the screw heads are flat metal too: without the sky they rendered black
METAL = ("plate aluminium", "screw steel")
plate_only = bpy.data.collections.new("plate only")
for o in sc.objects:
    if o.type == "MESH" and o.active_material and o.active_material.get("pk_role") in METAL:
        plate_only.objects.link(o)
flag.light_linking.receiver_collection = plate_only
sc.cycles.samples = samples
sc.cycles.filter_width = 1.0
bpy.context.view_layer.update()

W, H = sc.render.resolution_x, sc.render.resolution_y


def px(world):
    u, v, _ = world_to_camera_view(sc, cam, world)
    return [round(u * W, 2), round((1 - v) * H, 2)]


kle = kle_keys(kle_path)
data = {"image": os.path.basename(out), "size": [W, H],
        "pixel_origin": "top-left, x right, y down",
        "corner_order": "OLED top-left, top-right, bottom-right, bottom-left",
        "mm_per_px": round(cam.data.ortho_scale * 1000 / max(W, H), 5),
        "keys": [], "status_displays": []}
for side, root, board in halves:
    keys = textured_parts.board_keys(board)
    (tx, ty), dz = textured_parts.fit(root, keys)
    side_kle = [k for k in kle if (int(k[0].split(",")[0]) < 5) == (side == "left")]
    labels, resid = match(np.array([[x, -y] for x, y, _ in keys]), side_kle)
    print(f"{side}: KLE match, largest residual {resid:.2f} mm")
    data[f"kle_residual_mm_{side}"] = round(float(resid), 3)
    refs = board_refs(board)
    assert len(refs) == len(keys), (len(refs), len(keys))
    mw = root.matrix_world
    X, Y0, Y1, Z = textured_parts.DISP_X, textured_parts.DISP_Y0, textured_parts.DISP_Y1, textured_parts.DISP_TOP
    for (x, y, r), label, ref in zip(keys, labels, refs):
        def corner(fu, fv):
            p = np.array([-X + 2 * X * fu, Y0 + (Y1 - Y0) * fv])
            xy = textured_parts._rot(p, r) + np.array([x, y]) + np.array([tx, ty])
            return px(mw @ mathutils.Vector((xy[0], xy[1], Z + dz)))
        quad = [corner(A_U0, A_V1), corner(A_U1, A_V1), corner(A_U1, A_V0), corner(A_U0, A_V0)]
        cx = sum(q[0] for q in quad) / 4
        cy = sum(q[1] for q in quad) / 4
        data["keys"].append({"matrix": label, "side": side, "ref": ref, "rotation_deg": r,
                             "oled": quad, "center": [round(cx, 2), round(cy, 2)]})
    # status display: the top face of the "status lcd" box
    pts = textured_parts._display_points(root, "status lcd")
    top = pts[pts[:, 2] > pts[:, 2].max() - 1e-6]
    w = [mw @ mathutils.Vector(p) for p in top]
    sp = np.array([px(p) for p in w])
    xs, ys = sp[:, 0], sp[:, 1]
    data["status_displays"].append({"side": side, "size_px": [128, 64],
                                    "bbox": [round(xs.min(), 2), round(ys.min(), 2),
                                             round(xs.max(), 2), round(ys.max(), 2)]})

data["keys"].sort(key=lambda k: tuple(int(v) for v in k["matrix"].split(",")))
with open(out.rsplit(".", 1)[0] + ".json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1)
print(f"wrote {len(data['keys'])} key displays, {len(data['status_displays'])} status displays")
sc.render.filepath = out
bpy.ops.wm.save_as_mainfile(filepath=out.rsplit(".", 1)[0] + ".blend", compress=True)
bpy.ops.render.render(write_still=True)
