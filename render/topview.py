"""Top-down, orthographic render of both halves plus the image position of
every display, for PolyKybdHost's layout editor (a "real view" background).

    blender -b render/out/hero.blend --python render/topview.py -- out.png [width] [samples] [kle.json]

Writes out.png and out.json. The json gives, for each of the 72 key displays,
the 72x40 active area as four image-pixel corners in the OLED's own order
(top-left, top-right, bottom-right, bottom-left, so pixel (0, 0) of the
framebuffer is the first corner, legends upright when read from the front),
plus the key's KLE matrix label ("row,col", the label PolyKybdHost's
polykybd-split72.json uses), its board reference and side. The two status
displays are listed separately, and so is each expansion-port lid's outline
(the editor puts the labels of the two keys without a display there). Image
pixels: origin top-left, x right, y down.

The halves are not splayed (splay 0), the camera looks straight down, so the
picture lines up with the KLE layout up to one scale and offset per half.
Seen from straight above, every flat cap top and the plate mirror what is
directly overhead, so the black card goes there (studio.flag() follows the
camera) and the overhead softbox is hidden from reflections; the card casts
no shadow, so the floor stays evenly lit. The plate is flat as well and
mirrors the same card, so the card glows white, light-linked to the plate
alone: the plate reads silver while the caps still see black. The background
is pure white (the camera does not see the floor, and the transparent film is
composited onto white after the render), so the picture has no edge on a
white widget.

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


def lid(board):
    """Centre (x, y_up) and rotation of the expansion-port lid, from its model block.

    The lid (cover_insert.wrl) is a model on J39 whose frame centres the
    17 x 14 mm cut-out on the origin; its offset and z rotation place it."""
    import re
    t = open(board, encoding="utf-8").read()
    i = t.index("cover_insert.wrl")
    fp = t[t.rindex("\n\t(footprint ", 0, i):i]
    at = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", fp)
    x, y, r = float(at.group(1)), -float(at.group(2)), float(at.group(3) or 0)
    blk = t[i:t.index("\n\t\t)\n", i)]
    ox, oy = (float(v) for v in re.search(r"\(offset\s*\(xyz ([-\d.]+) ([-\d.]+)", blk).groups())
    rz = float(re.search(r"\(rotate\s*\(xyz [-\d.]+ [-\d.]+ ([-\d.]+)", blk).group(1))
    c = np.array([x, y]) + textured_parts._rot((ox, oy), r)
    return c, r + rz


LID_W, LID_H = 17.0, 14.0                   # cover_insert.scad's cut-out


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
# The editor shows this picture on a white widget, so the background must be
# exactly white: any grey reads as a box around the keyboard when zooming.
# The camera does not see the floor (it still bounces light onto the board),
# the film is transparent, and the white is put under it after the render
# (see onto_white); a white world would pass through AgX and come out light
# grey. The shadow comes from a second, cheap render with the floor as a
# shadow catcher (shadow_render): taken as it is, that floor is shaded all
# over by the big soft lights (edges at 150-220), so its border level counts
# as no shadow and the rest fades out towards the image edge.
bpy.data.objects["cove"].visible_camera = False
sc.render.film_transparent = True
sc.render.image_settings.color_mode = "RGBA"
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
margin = 1.25                               # room for the shadow to fade out to white
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
        "keys": [], "status_displays": [], "expansion_ports": []}
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
    # expansion-port lid: its outline in the image, corners as seen from above
    # (top-left first, clockwise), so the editor can put a label on it
    (lc, lr), lz = lid(board), Z + dz
    lquad = [px(mw @ mathutils.Vector((*(textured_parts._rot((u * LID_W / 2, v * LID_H / 2), lr) + lc
                                         + np.array([tx, ty])), lz)))
             for u, v in ((-1, 1), (1, 1), (1, -1), (-1, -1))]
    data["expansion_ports"].append({"side": side, "quad": lquad, "rotation_deg": round(lr, 3)})
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


SHADOW = 0.45       # how dark the strongest shadow gets, 0..1 of black over white
FADE = 0.10         # the outer fraction of the image over which the shadow fades out


def _pixels(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    return img, px


def shadow_render(path):
    """The floor's shadow alone, as a darkening 0..1 at the main render's size.

    A cheap second render (half size, few samples: the shadow is soft) with the
    floor as a shadow catcher; its alpha is the keyboard plus the shadow. The big
    soft lights also shade the whole floor evenly, so the level at the image
    border is taken as zero, and the rest is faded out towards the border, so the
    edge of the picture stays exactly white."""
    cove = bpy.data.objects["cove"]
    cove.visible_camera, cove.is_shadow_catcher = True, True
    samples, pct = sc.cycles.samples, sc.render.resolution_percentage
    sc.cycles.samples, sc.render.resolution_percentage = 32, 50
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    sc.cycles.samples, sc.render.resolution_percentage = samples, pct
    cove.visible_camera, cove.is_shadow_catcher = False, False
    img, px = _pixels(path)
    bpy.data.images.remove(img)
    a = px[:, :, 3]
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    base = np.percentile(border, 50)
    a = np.clip((a - base) / max(1e-6, 1.0 - base), 0.0, 1.0)
    a = np.repeat(np.repeat(a, 2, 0), 2, 1)[:H, :W]           # back to full size
    a = np.pad(a, ((0, H - a.shape[0]), (0, W - a.shape[1])), mode="edge")
    yy = np.minimum(np.arange(H), np.arange(H)[::-1])[:, None] / (H * FADE)
    xx = np.minimum(np.arange(W), np.arange(W)[::-1])[None, :] / (W * FADE)
    fade = np.clip(np.minimum(yy, xx), 0.0, 1.0)
    fade = fade * fade * (3 - 2 * fade)                         # smoothstep
    return a * fade * SHADOW


def onto_white(path, shadow):
    """Composite the transparent render onto white with the shadow, in display space.

    The PNG holds display-referred 8-bit values with straight alpha, so this is
    the plain over operator onto a background of white darkened by the shadow;
    a pixel far from the keyboard is exactly 255."""
    img, px = _pixels(path)
    a = px[:, :, 3:4]
    bg = (1.0 - shadow)[:, :, None]
    px[:, :, :3] = px[:, :, :3] * a + bg * (1.0 - a)
    px[:, :, 3] = 1.0
    img.pixels[:] = px.ravel()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


sc.render.filepath = out
bpy.ops.wm.save_as_mainfile(filepath=out.rsplit(".", 1)[0] + ".blend", compress=True)
bpy.ops.render.render(write_still=True)
onto_white(out, shadow_render(out.rsplit(".", 1)[0] + "_shadow.png"))
