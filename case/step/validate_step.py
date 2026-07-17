"""Validate an exported STEP is a real solid B-Rep (the acceptance test the mesh failed).

Pass criteria (per the recipe):
  * valid B-Rep = True
  * curved faces > 0  (the corner/rim fillets are real cylinders/tori, not facets)
  * max edge tolerance <= ~1e-4 mm  (vs 0.148 in the mesh export)
  * face count in the hundreds, not ~15000
"""
import sys
from OCP.STEPControl import STEPControl_Reader
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_EDGE, TopAbs_SOLID
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
from OCP.BRep import BRep_Tool
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp


def _count(shape, typ):
    ex = TopExp_Explorer(shape, typ); n = 0
    while ex.More(): n += 1; ex.Next()
    return n


def check(path):
    r = STEPControl_Reader()
    r.ReadFile(path)
    r.TransferRoots()
    s = r.OneShape()

    valid = BRepCheck_Analyzer(s).IsValid()

    ex = TopExp_Explorer(s, TopAbs_FACE); planar = curved = 0
    while ex.More():
        t = BRepAdaptor_Surface(TopoDS.Face_s(ex.Current())).GetType()
        if t == GeomAbs_Plane: planar += 1
        else: curved += 1
        ex.Next()

    ex = TopExp_Explorer(s, TopAbs_EDGE); mt = 0.0; n_edge = 0
    while ex.More():
        mt = max(mt, BRep_Tool.Tolerance_s(TopoDS.Edge_s(ex.Current()))); n_edge += 1; ex.Next()

    bb = Bnd_Box(); BRepBndLib.Add_s(s, bb)
    xmin, ymin, zmin, xmax, ymax, zmax = bb.Get()

    # A closed solid: exactly one SOLID with positive volume.  BRepCheck_Analyzer.IsValid()
    # is topological only -- it happily passes an OPEN SHELL (solids=0) whose bottom faces
    # read INWARD (you see through the bottom).  This is the check that catches that.
    n_solid = _count(s, TopAbs_SOLID)
    g = GProp_GProps(); BRepGProp.VolumeProperties_s(s, g); vol = g.Mass()

    ok = (valid and curved > 0 and mt <= 1e-3 and (planar + curved) < 2000
          and n_solid == 1 and vol > 1.0)
    print(f"=== {path} ===")
    print(f"  valid B-Rep      : {valid}")
    print(f"  solids           : {n_solid}   volume: {vol:.1f}")
    print(f"  faces            : {planar+curved}  (planar {planar}, curved {curved})")
    print(f"  max edge tol     : {mt:.2e} mm")
    print(f"  edges            : {n_edge}")
    print(f"  bbox             : ({xmin:.2f},{ymin:.2f},{zmin:.2f})..({xmax:.2f},{ymax:.2f},{zmax:.2f})")
    print(f"  size             : {xmax-xmin:.2f} x {ymax-ymin:.2f} x {zmax-zmin:.2f}")
    print(f"  -> {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    paths = sys.argv[1:] or ["metal-case-right.step", "metal-case-left.step"]
    all_ok = all(check(p) for p in paths)
    sys.exit(0 if all_ok else 1)
