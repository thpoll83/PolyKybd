"""Rebuild the saved keyboard scene from blender_scene.py's import checkpoint.

    blender -b render/out/hero_imported.blend --python render/rebuild_scene.py [-- render/out/hero.png]

Runs the rest of blender_scene.py on the checkpoint, without the render: the
display decals and flex cables from the current textured_parts.py and
flex_cable.py, the placement, materials, lights and camera, then saves
hero.blend (next to the given PNG). photo_view.py and topview.py load that
file, and textured_parts.add() keeps the parts a saved scene already has, so
after a change to flex_cable.py or to the decal geometry they render the old
parts until this runs (add() prints a WARNING when the scene's flex has a
different vertex count; a route change that keeps the count is not caught). It
takes about a minute instead of blender_scene.py's ~25-minute import."""
import os, sys, bpy
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blender_scene.py")
src = open(p).read()
a = src.index("materials.tag(bpy)")
b = src.index("t=time.time(); bpy.ops.render.render")
body = src[a:b]
out = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else os.path.join(os.path.dirname(p), "out", "hero.png")
samples, res = 64, 1600
pre = src[:src.index("halves=[imp(left),imp(right)]")]
pre = pre.replace("bpy.ops.wm.read_factory_settings(use_empty=True)", "")
pre = pre.replace("argv=sys.argv[sys.argv.index('--')+1:]\nleft, right, out, samples, res = argv[0], argv[1], argv[2], int(argv[3]), int(argv[4])", "")
g = {"__file__": p, "__name__": "__main__", "out": out, "samples": samples, "res": res}
exec(compile(pre, p, "exec"), g)
g["halves"] = [(bpy.data.objects[f"split72_{s}.wrl"], None) for s in ("left", "right")]
print("ROOTS", [r.name for r, _ in g["halves"]], [r.get("pk_textured") for r, _ in g["halves"]])
exec(compile(body, p, "exec"), g)
print("REBUILT")
