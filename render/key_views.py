"""One key from several angles, with its display lit: a material check.

    blender -b render/out/key.blend --python render/key_views.py -- outdir [samples] [width] [label]

Loads key_scene.py's saved scene, lights the display with one legend from
screens_layer0 (the key whose matrix label is `label`, default "2,1" for
KC_A), and renders the key from five directions into outdir/key_<view>.png:
front, front_left, side, top and low (a grazing look at the cap front).
Depth of field is stopped down so the whole key is sharp.
"""
import json
import math
import os
import sys

import bpy
import mathutils
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keymatch  # noqa: E402
import materials  # noqa: E402
import screens  # noqa: E402
import textured_parts  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
outdir = os.path.abspath(argv[0])
samples = int(argv[1]) if len(argv) > 1 else 96
width = int(argv[2]) if len(argv) > 2 else 1000
label = argv[3] if len(argv) > 3 else "2,1"
os.makedirs(outdir, exist_ok=True)

sc = bpy.context.scene
print("material roles", materials.apply(bpy))     # the saved scene predates any material change
root = next(o for o in bpy.data.objects if o.get("pk_textured"))
tgt = bpy.data.objects["target"]
cam = sc.camera

# the lit legend over the active area, as screens.keys() does for a board
atlas = json.load(open(os.path.join(screens.TEX, "screens_layer0.json"), encoding="utf-8"))
(aw, ah), (cw, ch) = atlas["size"], atlas["cell"]
cx, cy = atlas["keys"][label]
(tx, ty), dz = textured_parts.fit(root, [(0.0, 0.0, 0.0)])
X, Y0, Y1 = textured_parts.DISP_X, textured_parts.DISP_Y0, textured_parts.DISP_Y1
z = textured_parts.DISP_TOP + dz + screens.LIFT


def corner(fu, fv):
    return (-X + 2 * X * fu + tx, Y0 + (Y1 - Y0) * fv + ty, z)


verts = [corner(keymatch.A_U0, keymatch.A_V1), corner(keymatch.A_U1, keymatch.A_V1),
         corner(keymatch.A_U1, keymatch.A_V0), corner(keymatch.A_U0, keymatch.A_V0)]
u0, u1 = cx / aw, (cx + cw) / aw
v1, v0 = 1 - cy / ah, 1 - (cy + ch) / ah
textured_parts._mesh("lit legend", verts, [(0, 3, 2), (0, 2, 1)],
                     [(u0, v1), (u1, v1), (u1, v0), (u0, v0)],
                     screens._material("lit legends", "screens_layer0.png", 6.0), root)

cam.data.dof.aperture_fstop = 16
dist = (mathutils.Vector(cam.location) - tgt.location).length
VIEWS = {               # azimuth from the front (deg, + to the right), elevation (deg)
    "front": (0, 35), "front_left": (-40, 32), "side": (-90, 22), "top": (0, 88), "low": (12, 10)}
sc.cycles.samples = samples
sc.render.resolution_x, sc.render.resolution_y = width, int(width * 3 / 4)
for name, (az, el) in VIEWS.items():
    a, e = math.radians(az), math.radians(el)
    cam.location = tgt.location + dist * mathutils.Vector(
        (math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    sc.render.filepath = os.path.join(outdir, f"key_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)
