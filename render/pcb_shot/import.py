"""Import a .pcb3d into a fresh scene and save it.

    PCB2BLENDER=<checkout> blender-5.1 -b --python render/pcb_shot/import.py -- in.pcb3d out.blend

Takes about 3 minutes for one split72 half. The add-on is registered from the
checkout rather than installed, so nothing outside this run changes.
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
sys.path.insert(0, os.environ.get("PCB2BLENDER", "/tmp/pcb2blender"))
import pcb2blender_importer  # noqa: E402

pcb2blender_importer.register()
bpy.ops.wm.read_homefile(use_empty=True)
print("import", bpy.ops.pcb2blender.import_pcb3d(
    filepath=argv[0], add_solder_joints="SMART", texture_dpi=1016.0,
    center_boards=True, enhance_materials=True, merge_materials=True))
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
