"""Exact convex hull of a point set as a build123d Solid.

OpenSCAD's `hull()` is the one operation in `keycap_stem.scad` that has no direct
build123d equivalent (the case recipe says the same about the case shell).  Here it
is applied only to POLYHEDRA -- two tapered boxes plus three 0.3 mm print tabs -- and
the convex hull of polyhedra is itself a polyhedron with PLANAR faces.  So this is an
exact reproduction, not an approximation: hull the vertices, merge the coplanar
simplices scipy hands back into single n-gons, and sew the faces into a solid.

Merging matters.  Leaving scipy's triangulation alone would export a hull made of
~60 triangles -- readable to a machine, but exactly the "facet noise" appearance the
whole exercise exists to remove, and it would put spurious edges on the drawing.
"""
import numpy as np
from scipy.spatial import ConvexHull
from build123d import Face, Shell, Solid, Vector

# Coplanarity binning.  The hull faces here are metres apart in orientation (the
# tightest pair is the tab ramp against the 11.6 deg body draft), so a coarse bin is
# safe and keeps float noise from splitting one face into two.
_NORMAL_DEC = 6
_OFFSET_DEC = 6


def hull_solid(points):
    """Convex hull of `points` (N x 3) as a build123d Solid with merged planar faces."""
    pts = np.asarray(points, dtype=float)
    hull = ConvexHull(pts)

    groups = {}
    for eq, simplex in zip(hull.equations, hull.simplices):
        n = eq[:3] / np.linalg.norm(eq[:3])
        key = (tuple(np.round(n, _NORMAL_DEC)), round(float(eq[3]), _OFFSET_DEC))
        groups.setdefault(key, [set(), n]) [0].update(int(i) for i in simplex)

    faces = []
    for (_, _off), (idx, normal) in groups.items():
        ring = _ccw_ring(pts[sorted(idx)], normal)
        faces.append(Face(_wire(ring)))
    return Solid(Shell(faces))


def _wire(ring):
    from build123d import Polyline, Wire
    return Wire(Polyline(*[tuple(p) for p in ring], close=True))


def _ccw_ring(verts, normal):
    """Order the coplanar vertices of one (convex) hull face into a ring.

    Convexity is what makes the cheap version correct: sorting by angle about the
    centroid in the face plane cannot skip or cross, so no edge-walking is needed.
    Dropping any vertex that is collinear with its neighbours keeps the exported face
    free of the seam edges the triangulation introduced.
    """
    c = verts.mean(axis=0)
    n = np.asarray(normal, dtype=float)
    u = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(u, n)) > 0.9:
        u = np.array([0.0, 1.0, 0.0])
    u = u - np.dot(u, n) * n
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    d = verts - c
    ring = verts[np.argsort(np.arctan2(d @ v, d @ u))]

    keep = []
    m = len(ring)
    for i in range(m):
        a, b, cc = ring[i - 1], ring[i], ring[(i + 1) % m]
        if np.linalg.norm(np.cross(b - a, cc - b)) > 1e-9:
            keep.append(b)
    return np.array(keep)
