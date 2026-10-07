"""Re-render a saved scene with the current materials.py, without re-importing.

    blender -b scene.blend --python render/rerender.py -- out.png [samples] [width] [light] [exposure] [splay] [studio] [bridge] [fstop] [elevation]

blender_scene.py and key_scene.py both save a .blend next to their PNG. The
full keyboard takes ~25 minutes to import and merge; this re-applies the
ROLES table, sets the even studio lighting (lighting.py) scaled by `light`
(default 1) and sets the view
exposure in stops (default 0), then renders. Saves out.blend as well.
`splay` sets the angle of each half in degrees (blender_scene.py: 10);
`studio` "white" swaps the dark floor for studio.py's white cove and black
flag, "dark" keeps the scene's floor. `bridge` "bridge" adds the USB-C bridge
cable (bridge_cable.py) after the splay is set, "host" the host cable from
the left half's top-edge USB1, "bridge+host" both. `fstop` sets the camera
aperture; the default 0 turns depth of field off, so the whole keyboard is
sharp front to back, like a focus-stacked product photo. blender_scene.py's
f/4 at ~0.74 m keeps only ~50 mm sharp, less than the keyboard's depth, so
the front and back rows went soft; f/11 keeps ~140 mm.
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import materials  # noqa: E402
import textured_parts  # noqa: E402
import lighting  # noqa: E402
import studio  # noqa: E402
import bridge_cable  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out = os.path.abspath(argv[0])
samples = int(argv[1]) if len(argv) > 1 else 64
width = int(argv[2]) if len(argv) > 2 else 1600
light = float(argv[3]) if len(argv) > 3 else 1.0
exposure = float(argv[4]) if len(argv) > 4 else 0.0
splay = float(argv[5]) if len(argv) > 5 else None
look = argv[6] if len(argv) > 6 else "dark"
cables = argv[7].split("+") if len(argv) > 7 else []
bridge, host = "bridge" in cables, "host" in cables
fstop = float(argv[8]) if len(argv) > 8 else 0.0
elevation = float(argv[9]) if len(argv) > 9 else None

sc = bpy.context.scene
materials.tag(bpy)
for side in ("left", "right"):          # the halves blender_scene.py imported
    root = bpy.data.objects.get(f"split72_{side}.wrl")
    if root:
        board = os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{side}.kicad_pcb")
        textured_parts.add(root, textured_parts.board_keys(board))
print("material roles", materials.apply(bpy))
materials.scene_settings(sc)
tgt = bpy.data.objects.get("target") or bpy.data.objects.get("tgt")
lighting.studio(sc, tgt, light)
if splay is not None:
    studio.splay(splay)
if elevation is not None:
    studio.camera_elevation(sc, elevation)      # before the flag, which follows the camera
if look == "white":
    studio.cove(sc)
    studio.flag(sc)
    studio.white_look(sc)
bridge_cable.remove(keep_bridge=bridge, keep_host=host)   # a saved scene may carry them
if bridge:
    halves = [(bpy.data.objects[f"split72_{side}.wrl"],
               os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{side}.kicad_pcb"))
              for side in ("left", "right")]
    bridge_cable.add(sc, halves)
if host:
    bridge_cable.add_host(sc, bpy.data.objects["split72_left.wrl"],
                          os.path.join(textured_parts.REPO, "poly_kybd", "poly_kybd_split72_left.kicad_pcb"))
sc.view_settings.exposure = exposure
if sc.camera:
    sc.camera.data.dof.use_dof = fstop > 0
    if fstop > 0:
        sc.camera.data.dof.aperture_fstop = fstop
sc.cycles.filter_width = 1.0            # px; Blender's 1.5 softens fine edges
sc.cycles.samples = samples
aspect = sc.render.resolution_y / sc.render.resolution_x
sc.render.resolution_x, sc.render.resolution_y = width, int(width * aspect)
sc.render.filepath = out
bpy.ops.wm.save_as_mainfile(filepath=out.rsplit(".", 1)[0] + ".blend", compress=True)
bpy.ops.render.render(write_still=True)
