"""One printed part (a case half or the spacer) alone on the white studio cove.

    blender -b --python render/case_parts.py -- <part.stl> <out.png> <samples> <width> \
        [elev_deg] [azim_deg] [lens_mm] [fill]

For the docs' Case & Spacer page, which showed viewer screenshots in flat
pink and blue on black. The part takes the hero scene's "case PLA" look
(materials.py) unless PK_PART_RGB="r,g,b" sets another base colour, and the
cove, light linking and AgX look come from studio.py, so it sits in the same
studio as the keyboard renders.

- `elev_deg` (default 35) is the camera's height above the desk, `azim_deg`
  (default -20) its bearing from straight in front, negative = from the left.
- `fill` (default 0.82) is the share of the frame the part fills: its width
  or its height, whichever binds first.

The STL is in millimetres and the scene in metres. The part is centred on
the origin with its bottom on the floor.
"""
import math
import os
import sys

import bpy
import mathutils

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import materials  # noqa: E402
import studio  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
stl, out, samples, width = argv[0], argv[1], int(argv[2]), int(argv[3])
elev = float(argv[4]) if len(argv) > 4 else 35.0
azim = float(argv[5]) if len(argv) > 5 else -20.0
lens = float(argv[6]) if len(argv) > 6 else 50.0
fill = float(argv[7]) if len(argv) > 7 else 0.82

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

bpy.ops.wm.stl_import(filepath=stl, global_scale=0.001)
part = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = part
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))

# centre it, bottom on the floor
bb = [part.matrix_world @ mathutils.Vector(c) for c in part.bound_box]
lo = mathutils.Vector([min(v[i] for v in bb) for i in range(3)])
hi = mathutils.Vector([max(v[i] for v in bb) for i in range(3)])
part.location -= mathutils.Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
size = hi - lo

# the case colour from materials.ROLES, so a part matches the keyboard renders
role = next(r for r in materials.ROLES if r[0] == "case PLA")
m = bpy.data.materials.new("case PLA")
m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]
for k, v in role[3].items():
    b.inputs[k].default_value = v
if os.environ.get("PK_PART_RGB"):
    rgb = [float(c) for c in os.environ["PK_PART_RGB"].split(",")]
    b.inputs["Base Color"].default_value = (*rgb, 1)
part.data.materials.clear()
part.data.materials.append(m)

target = bpy.data.objects.new("target", None)
target.location = (0, 0, size.z / 2)
sc.collection.objects.link(target)

# camera: bearing and height around the target, distance from the frame fill
cd = bpy.data.cameras.new("cam")
cd.lens = lens
cd.clip_start = 0.005
cam = bpy.data.objects.new("cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
c = cam.constraints.new("TRACK_TO")
c.target = target
c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
fov = 2 * math.atan(cd.sensor_width / 2 / lens)
dist = (max(size.x, size.y) / fill) / 2 / math.tan(fov / 2)
a, e = math.radians(azim), math.radians(elev)
cam.location = target.location + mathutils.Vector((
    dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e)))

sc.render.resolution_x = width
sc.render.resolution_y = int(width * 9 / 16)

# fit: the part's projected box fills `fill` of the frame's width or height,
# whichever binds first, and sits in its centre (a flat spacer seen from 45
# deg is taller in frame than its width suggests)
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
corners = [mathutils.Vector((x, y, z)) for x in (-size.x / 2, size.x / 2)
           for y in (-size.y / 2, size.y / 2) for z in (0, size.z)]
for _ in range(6):
    bpy.context.view_layer.update()
    p = [world_to_camera_view(sc, cam, v) for v in corners]
    xs, ys = [q.x for q in p], [q.y for q in p]
    span = max((max(xs) - min(xs)) / fill, (max(ys) - min(ys)) / fill)
    off = mathutils.Vector(((max(xs) + min(xs)) / 2 - 0.5, (max(ys) + min(ys)) / 2 - 0.5))
    # move the target by the frame offset (in metres at the target), then scale the distance
    view_w = 2 * (cam.location - target.location).length * math.tan(fov / 2)
    m3 = cam.matrix_world.to_3x3()
    shift = m3 @ mathutils.Vector((off.x * view_w, off.y * view_w * 9 / 16, 0))
    target.location += shift
    cam.location += shift
    cam.location = target.location + (cam.location - target.location) * span

import lighting  # noqa: E402
lighting.studio(sc, target)
# PK_FILL scales the two side fills: at 1 they light floor, walls and ribs evenly,
# and the part reads flat; lower lets the overhead key light model it
for o in sc.objects:
    if o.type == "LIGHT" and o.name.startswith("fill"):
        o.data.energy *= float(os.environ.get("PK_FILL", 1.0))
studio.cove(sc)
studio.white_look(sc)
# PK_LOOK picks another AgX look and PK_EXPOSURE (stops) darkens or brightens:
# the false-colour parts read pastel at the white studio's defaults
if os.environ.get("PK_LOOK"):
    sc.view_settings.look = os.environ["PK_LOOK"]
sc.view_settings.exposure = float(os.environ.get("PK_EXPOSURE", 0.0))

sc.render.engine = "CYCLES"
sc.cycles.samples = samples
sc.cycles.use_denoising = True
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("wrote", out, "size mm", tuple(round(v * 1000, 1) for v in size))
