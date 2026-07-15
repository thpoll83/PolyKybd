"""Render my STEP-derived STL next to the original OpenSCAD mesh, top + iso views."""
import struct, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def load_stl(path):
    with open(path, "rb") as f:
        head = f.read(80)
        if head[:5] == b"solid" and b"facet" in f.read(300):
            f.seek(0); return load_ascii(f)
        f.seek(80); n = struct.unpack("<I", f.read(4))[0]
        tris = np.empty((n, 3, 3), np.float32)
        for i in range(n):
            d = f.read(50)
            for v in range(3):
                tris[i, v] = struct.unpack("<fff", d[12 + v*12: 24 + v*12])
        return tris


def load_ascii(f):
    f.seek(0); tris = []; cur = []
    for line in f:
        line = line.split()
        if line[:1] == [b"vertex"]:
            cur.append([float(x) for x in line[1:4]])
            if len(cur) == 3: tris.append(cur); cur = []
    return np.array(tris, np.float32)


def add(ax, tris, color, elev, azim):
    ax.add_collection3d(Poly3DCollection(tris, facecolor=color, edgecolor="k",
                                         linewidths=0.05, alpha=1.0))
    p = tris.reshape(-1, 3)
    mn, mx = p.min(0), p.max(0)
    c = (mn + mx) / 2; r = (mx - mn).max() / 2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect((1, 1, 1)); ax.set_axis_off()


def main():
    mine = load_stl("metal-case-right.stl")
    orig = load_stl("../case_polykybd_split72_metal.stl")
    print("mine tris", len(mine), "orig tris", len(orig))
    fig = plt.figure(figsize=(16, 9))
    views = [("top", 90, -90), ("iso", 35, -60)]
    for col, (label, el, az) in enumerate(views):
        a1 = fig.add_subplot(2, 2, col+1, projection="3d")
        add(a1, orig, "#bbbbcc", el, az); a1.set_title(f"ORIGINAL mesh  ({label})")
        a2 = fig.add_subplot(2, 2, col+3, projection="3d")
        add(a2, mine, "#cc9966", el, az); a2.set_title(f"build123d STEP  ({label})")
    fig.tight_layout()
    fig.savefig("compare.png", dpi=110)
    print("wrote compare.png")


if __name__ == "__main__":
    main()
