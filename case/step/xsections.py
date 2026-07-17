"""Cross-sections of metal-case-right.stl along all 3 axes, one plane every 10 mm."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from render_compare import load_stl

t = load_stl("metal-case-right.stl")
p = t.reshape(-1, 3)
mn, mx = p.min(0), p.max(0)

def section(axis, c):
    k = {'x': 0, 'y': 1, 'z': 2}[axis]
    segs = []
    for tri in t:
        cs = tri[:, k]
        if cs.min() <= c <= cs.max():
            pts = []
            for a, b in ((0, 1), (1, 2), (2, 0)):
                za, zb = tri[a, k], tri[b, k]
                if (za - c) * (zb - c) < 0:
                    u = (c - za) / (zb - za); pts.append(tri[a] + u * (tri[b] - tri[a]))
            if len(pts) == 2:
                segs.append((pts[0], pts[1]))
    return segs

# for each axis, the two in-plane axes to plot
plane = {'x': (1, 2, 'Y', 'Z'), 'y': (0, 2, 'X', 'Z'), 'z': (0, 1, 'X', 'Y')}

for axis in ('x', 'y', 'z'):
    ai, bi, an, bn = plane[axis]
    k = {'x': 0, 'y': 1, 'z': 2}[axis]
    lo, hi = mn[k], mx[k]
    # planes every 10 mm, offset so we avoid exact face coincidence
    start = np.floor(lo / 10) * 10 + 10
    cuts = np.arange(start, hi, 10.0)
    n = len(cuts)
    cols = 3; rows = int(np.ceil(n / cols))
    fig, axs = plt.subplots(rows, cols, figsize=(cols * 6, rows * 3.4))
    axs = np.array(axs).reshape(-1)
    for i, c in enumerate(cuts):
        ax = axs[i]
        for A, B in section(axis, float(c)):
            ax.plot([A[ai], B[ai]], [A[bi], B[bi]], 'k-', lw=0.5)
        ax.set_aspect('equal'); ax.set_title(f"{axis.upper()} = {c:.0f} mm", fontsize=10)
        ax.set_xlim(mn[ai], mx[ai]); ax.set_ylim(mn[bi], mx[bi])
        ax.set_xlabel(an, fontsize=8); ax.set_ylabel(bn, fontsize=8)
        ax.tick_params(labelsize=7); ax.grid(True, lw=0.2)
    for j in range(n, len(axs)):
        axs[j].axis('off')
    fig.suptitle(f"metal-case-right — cross-sections along {axis.upper()} (every 10 mm)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(f"xsections_{axis}.png", dpi=95)
    print(f"wrote xsections_{axis}.png  ({n} planes)")
