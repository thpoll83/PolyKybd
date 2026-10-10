"""Headless pcb2blender export: a .kicad_pcb to a .pcb3d, without pcbnew's window.

    PCB2BLENDER=<pcb2blender checkout> python3 render/pcb_shot/export.py <board.kicad_pcb> <out.pcb3d>

Also writes <out>.parts.json: each footprint's place, for the part markings.

pcb2blender's exporter is a pcbnew action plugin. Two things stop it running
from a shell, and both are replaced here, leaving its own code untouched:
- its package __init__ imports wx for the dialog, so the two modules it needs
  are loaded under a bare package;
- it reads the open board with pcbnew.GetBoard() and writes the VRML with
  pcbnew.ExportVRML(), which needs the editor frame and, without one, returns
  having written nothing. kicad-cli takes the same options.
"""
import os
import subprocess
import sys
import types

P2B = os.environ.get("PCB2BLENDER", "/tmp/pcb2blender")
sys.path.insert(0, P2B)
import pcbnew  # noqa: E402

board = pcbnew.LoadBoard(sys.argv[1])
pcbnew.GetBoard = lambda: board


def export_vrml(path, mm_to_unit, unspecified, dnp, export_3d, relative, subdir, x, y):
    assert mm_to_unit == 0.001 and export_3d and relative
    cmd = ["kicad-cli", "pcb", "export", "vrml", "-f", "--units", "m", "--user-origin", "%gx%gmm" % (x, y),
           "--models-dir", str(subdir), "--models-relative",
           "-D", "KIPRJMOD=" + os.path.dirname(os.path.abspath(sys.argv[1])), "-o", str(path), sys.argv[1]]
    cmd += [] if unspecified else ["--no-unspecified"]
    cmd += [] if dnp else ["--no-dnp"]
    subprocess.run(cmd, check=True)
    return True


pcbnew.ExportVRML = export_vrml
pkg = types.ModuleType("pcb2blender_exporter")
pkg.__path__ = [os.path.join(P2B, "pcb2blender_exporter")]
sys.modules["pcb2blender_exporter"] = pkg
from pcb2blender_exporter.export import export_pcb3d, get_boarddefs  # noqa: E402

os.makedirs(os.path.dirname(os.path.abspath(sys.argv[2])), exist_ok=True)   # render/out/ is gitignored
defs, ignored = get_boarddefs(board)
export_pcb3d(sys.argv[2], defs)

# every footprint's place, for shot.py's part markings (position in mm as KiCad
# gives it, orientation in degrees, side)
import json  # noqa: E402

parts = {fp.GetReference(): {"value": fp.GetValue(), "footprint": str(fp.GetFPID().GetLibItemName()),
                             "mpn": fp.GetFieldText("MPN") if fp.HasFieldByName("MPN") else "",
                             "position": [pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)],
                             "rotation": fp.GetOrientationDegrees(), "back": fp.IsFlipped()}
         for fp in board.GetFootprints()}
with open(os.path.splitext(sys.argv[2])[0] + ".parts.json", "w") as f:
    json.dump(parts, f, indent=1)
print("exported", sys.argv[2])
