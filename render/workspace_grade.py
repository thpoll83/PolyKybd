"""Grade a workspace render without rendering it again: a linear EXR from
workspace_scene.py (PK_EXR=1) through the lens effects and the colour settings of
each variant, one PNG per variant.

    blender -b --factory-startup --python render/workspace_grade.py -- in.exr out_dir \\
        '[{"name": "F", "look": "AgX - High Contrast", "sat": 1.0, "contrast": 0}]'

A variant sets look (an AgX look), exposure, sat (Hue/Saturation node, 1 = as is),
contrast (Bright/Contrast node, -100..100), vignette (0..1) and glare (fog glow mix,
0..1); vignette 0.35 and glare 0.15 are the office's.
"""
import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, VARIANTS = argv[0], argv[1], json.loads(argv[2])
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
img = bpy.data.images.load(SRC)
sc.render.resolution_x, sc.render.resolution_y = img.size
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "AgX"
sc.use_nodes = True
ct = sc.node_tree
for v in VARIANTS:
    ct.nodes.clear()
    src = ct.nodes.new("CompositorNodeImage")
    src.image = img
    last = src.outputs["Image"]
    if v.get("glare", 0.15):
        gl = ct.nodes.new("CompositorNodeGlare")
        gl.glare_type, gl.quality, gl.threshold, gl.mix = "FOG_GLOW", "HIGH", 1.0, -1 + v.get("glare", 0.15)
        ct.links.new(last, gl.inputs["Image"])
        last = gl.outputs["Image"]
    if v.get("vignette", 0.35):
        el = ct.nodes.new("CompositorNodeEllipseMask")
        el.width, el.height = 0.95, 0.95
        bl = ct.nodes.new("CompositorNodeBlur")
        bl.filter_type, bl.use_relative = "FAST_GAUSS", True
        bl.factor_x = bl.factor_y = 40
        ct.links.new(el.outputs["Mask"], bl.inputs["Image"])
        mr = ct.nodes.new("CompositorNodeMapRange")
        mr.inputs["To Min"].default_value = 1.0 - v.get("vignette", 0.35)
        ct.links.new(bl.outputs["Image"], mr.inputs["Value"])
        mx = ct.nodes.new("CompositorNodeMixRGB")
        mx.blend_type = "MULTIPLY"
        ct.links.new(last, mx.inputs[1])
        ct.links.new(mr.outputs["Value"], mx.inputs[2])
        last = mx.outputs["Image"]
    hs = ct.nodes.new("CompositorNodeHueSat")
    hs.inputs["Saturation"].default_value = v.get("sat", 1.0)
    ct.links.new(last, hs.inputs["Image"])
    bc = ct.nodes.new("CompositorNodeBrightContrast")
    bc.inputs["Contrast"].default_value = v.get("contrast", 0)
    bc.inputs["Bright"].default_value = v.get("bright", 0)
    ct.links.new(hs.outputs["Image"], bc.inputs["Image"])
    comp = ct.nodes.new("CompositorNodeComposite")
    ct.links.new(bc.outputs["Image"], comp.inputs["Image"])
    sc.view_settings.look = v.get("look", "AgX - High Contrast")
    sc.view_settings.exposure = v.get("exposure", 0.0)
    sc.render.filepath = os.path.join(OUT, v["name"] + ".png")
    bpy.ops.render.render(write_still=True)
    print("GRADED", sc.render.filepath)
