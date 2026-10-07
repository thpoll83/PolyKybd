"""Convert a binary STL (mm) to a VRML 2.0 mesh KiCad can load as a 3D model.

    python poly_kybd/models/stl_to_wrl.py in.stl out.wrl [r g b]

KiCad's 3D viewer and its VRML/raytrace paths do not read STL. The output keeps
the STL's coordinates in mm, so the board must reference it with
scale 0.3937 (1/2.54): KiCad reads VRML models in 0.1-inch units.
"""
import struct
import sys

import numpy as np


def load_stl(path):
    data = open(path, "rb").read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        raise SystemExit(f"{path}: ASCII STL, convert it to binary first")
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.frombuffer(data[84:84 + 50 * n], dtype=np.dtype(
        [("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return rec["v"].reshape(-1, 3).astype(np.float64)


def write_wrl(dst, shapes, source):
    """Write [(vertices (N*3, 3) as triangle soup, (r, g, b)), ...] as one VRML file.

    Layout copied from the WRLs KiCad already loads here (outercap1u.wrl):
    its VRML2 parser silently drops a file that uses creaseAngle or
    specularColor, or puts nodes on one line."""
    with open(dst, "w", encoding="utf-8") as f:
        f.write("#VRML V2.0 utf8\n")
        f.write(f"# from {source} by stl_to_wrl.py, units mm\n\n")
        for v, rgb in shapes:
            v = np.asarray(v, dtype=np.float64).round(4)
            uniq, idx = np.unique(v, axis=0, return_inverse=True)
            faces = idx.reshape(-1, 3)
            faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2])
                          & (faces[:, 0] != faces[:, 2])]
            f.write("Shape {\nappearance Appearance {\nmaterial Material {\n")
            f.write(f"diffuseColor {rgb[0]} {rgb[1]} {rgb[2]}\nshininess 0.2\n}}\n}}\n")
            f.write("geometry IndexedFaceSet {\ncoord Coordinate {\npoint [\n")
            f.write(",\n".join(f"{x:.4f} {y:.4f} {z:.4f}" for x, y, z in uniq))
            f.write("\n]\n}\ncoordIndex [\n")
            f.write(",\n".join(f"{a},{b},{c},-1" for a, b, c in faces))
            f.write("\n]\n}\n}\n")
            print(f"{dst.name if hasattr(dst, 'name') else dst}: {len(uniq)} vertices, {len(faces)} faces")


def main():
    src, dst = sys.argv[1], sys.argv[2]
    rgb = [float(c) for c in sys.argv[3:6]] if len(sys.argv) >= 6 else [0.35, 0.35, 0.37]
    write_wrl(dst, [(load_stl(src), rgb)], src.split("/")[-1])


if __name__ == "__main__":
    main()
