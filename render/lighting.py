"""Even studio lighting for the full-keyboard scene.

The first scene lit the boards with three small area lights from the front
left, front right and back, so the picture darkened towards its left and right
edges. This replaces them with
- one large soft overhead light that covers both halves,
- two broad fills from the left and the right at board height,
- a dim uniform world, so no surface falls to black,
all aimed at the scene's "target" empty. Energies are in watts for a scene in
metres; `scale` multiplies them all.
"""
import bpy


def studio(sc, target, scale=1.0):
    for o in [o for o in sc.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(o)

    def area(name, loc, energy, size_x, size_y, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, "AREA")
        d.shape = "RECTANGLE"
        d.size, d.size_y = size_x, size_y
        d.energy = energy * scale
        d.color = color
        o = bpy.data.objects.new(name, d)
        o.location = loc
        sc.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = target
        return o

    area("overhead", (0.0, -0.15, 0.9), 18, 1.6, 1.0)
    area("fill left", (-0.9, -0.35, 0.35), 5.4, 0.8, 0.6, (0.95, 0.97, 1.0))
    area("fill right", (0.9, -0.35, 0.35), 5.4, 0.8, 0.6, (0.95, 0.97, 1.0))
    # the rim sits high: at 32 deg (its old place) every flat cap top
    # mirrored it into the camera, see studio.flag()
    area("rim", (0.0, 0.55, 1.0), 3, 1.4, 0.4, (1.0, 0.95, 0.9))
    w = sc.world or bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
