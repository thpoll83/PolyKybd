"""Generate the STEP models that neither the repo nor the KiCad 9 library has.

    python poly_kybd/models/gen_models.py        (build123d 0.12.0)

Each model is drawn in its footprint's own frame (KiCad's footprint X, with Y
flipped to point up, Z up from the board surface), so the board references it
with zero offset. Shapes are visual approximations: body outline, terminals and
height from the footprint and the part family, not a vendor model.

- DHVQFN-16-1EP_2.5x3.5mm_P0.5mm_EP1x2mm.step  74HC595BQ (Nexperia SOT763-1).
  KiCad's DHVQFN-16 footprint names this file, but the KiCad 9 3D library
  does not ship it. Frame: Package_DFN_QFN:DHVQFN-16-1EP_2.5x3.5mm_P0.5mm_EP1x2mm.
- FH34SRJ-14S-0.5SH_50_.step  Hirose FH34SRJ 14-pos FFC connector, back-flip
  actuator. Frame: poly_kb:FH34SRJ14S05SH50-Rev2 (body = its F.Fab outline,
  x +-4.5, y -1.375..1.525). The keys' connectors.
- FH34SRJ-12S-0.5SH_50_.step  the same in 12 positions (x +-4.0), for
  poly_kb:FH34SRJ12S05SH50-Rev2: J37, the status display's connector.
- screw_M3_pan_hex_2mm.step  M3 x 10 pan-head screw with a 2 mm hex socket
  and a 1.5 mm flat head with a rounded edge, for the 3 mm mounting holes. Head at z 0..1.5, shank
  down; the boards place z = 0 on the plate top (5.0 mm above the PCB top),
  so the shank runs through plate and PCB into the case's nut insert.
"""
import math
from pathlib import Path

from build123d import (Align, Axis, Box, Color, Compound, Cone, Cylinder, Location, RegularPolygon,
                       export_step, extrude, fillet)

HERE = Path(__file__).resolve().parent

BLACK = Color(0.08, 0.08, 0.09)
TIN = Color(0.80, 0.80, 0.82)
BROWN = Color(0.30, 0.22, 0.14)


def box(sx, sy, sz, x, y, z, color, label):
    """Axis-aligned box with its min corner at (x, y, z)."""
    b = Box(sx, sy, sz).moved(Location((x + sx / 2, y + sy / 2, z + sz / 2)))
    b.color = color
    b.label = label
    return b


def dhvqfn16():
    w, l, h = 2.5, 3.5, 0.85
    parts = [box(w, l, h - 0.02, -w / 2, -l / 2, 0.02, BLACK, "body")]
    tl, tw, tt = 0.40, 0.24, 0.05            # terminal length, width, thickness
    # pad centres from the KiCad footprint, Y flipped
    side = [(-1.25 + 0.5 * i) for i in range(6)]
    for y in side:                          # pins 2-7 (left), 10-15 (right)
        parts.append(box(tl, tw, tt, -w / 2, -y - tw / 2, 0, TIN, "pin"))
        parts.append(box(tl, tw, tt, w / 2 - tl, -y - tw / 2, 0, TIN, "pin"))
    for x in (-0.25, 0.25):                 # pins 1/16 (top), 8/9 (bottom)
        parts.append(box(tw, tl, tt, x - tw / 2, l / 2 - tl, 0, TIN, "pin"))
        parts.append(box(tw, tl, tt, x - tw / 2, -l / 2, 0, TIN, "pin"))
    parts.append(box(1.0, 2.0, tt, -0.5, -1.0, 0, TIN, "exposed pad"))
    dot = Cylinder(0.12, 0.02).moved(Location((-0.75, 1.3, h + 0.005)))
    dot.color = Color(0.35, 0.35, 0.37)
    dot.label = "pin 1"
    parts.append(dot)
    return Compound(children=parts, label="DHVQFN-16")


def fh34srj(n):
    # footprint frame, Y flipped: F.Fab y -1.525..1.375, leads (pads) centred
    # at y=+1.525, fitting nails at y=-0.975. The 12- and 14-position parts
    # differ only in width: the part is 2.5 mm wider than its outer leads,
    # the nails sit 0.25 mm inside its ends (FH34SRJ12S05SH50-Rev2 /
    # FH34SRJ14S05SH50-Rev2: pads +-2.75 / +-3.25, nails +-3.75 / +-4.25).
    lead0 = -(n - 1) * 0.25
    x1 = -lead0 + 1.25
    x0 = -x1
    parts = [
        box(2 * x1 - 0.8, 2.5, 0.70, x0 + 0.4, -1.525, 0, BLACK, "housing"),
        # back-flip actuator over the lead side, the full width of the part
        box(2 * x1, 1.0, 0.30, x0, 0.2, 0.70, BROWN, "actuator"),
        box(0.35, 1.0, 0.85, x0, 0.2, 0, BROWN, "actuator hinge"),
        box(0.35, 1.0, 0.85, x1 - 0.35, 0.2, 0, BROWN, "actuator hinge"),
    ]
    for i in range(n):                      # leads, 0.5 mm pitch
        x = lead0 + 0.5 * i
        parts.append(box(0.20, 0.75, 0.10, x - 0.10, 1.15, 0, TIN, "lead"))
    for x in (x0 + 0.25, x1 - 0.25):        # fitting nails
        parts.append(box(0.30, 0.70, 0.10, x - 0.15, -1.325, 0, TIN, "nail"))
        parts.append(box(0.30, 0.10, 0.60, x - 0.15, -1.325, 0, TIN, "nail"))
    return Compound(children=parts, label=f"FH34SRJ-{n}S-0.5SH(50)")


STEEL = Color(0.62, 0.63, 0.66)


def screw_m3():
    dk, k, d, length = 5.6, 1.5, 2.9, 10.0
    head = Cylinder(dk / 2, k).moved(Location((0, 0, k / 2)))
    # flat top, no dome: the top edge is rounded into the side, and a small
    # radius softens the bearing edge
    head = fillet(head.edges().group_by(Axis.Z)[-1], 0.6)
    head = fillet(head.edges().group_by(Axis.Z)[0], 0.2)
    # 2 mm hex socket (M3), 1.0 mm of hex above a 118 deg drill-point floor,
    # with a small chamfer at the mouth: a flat floor reflects the same light
    # as the head top and reads as a painted hexagon, not a hole
    s_hex, depth, chamfer = 2.0, 1.0, 0.15
    r_corner = s_hex / math.sqrt(3)
    recess = extrude(RegularPolygon(r_corner, 6), amount=depth + 1.0)
    head -= recess.moved(Location((0, 0, k - depth)))
    point = r_corner / math.tan(math.radians(59))
    head -= Cone(0, r_corner, point, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((0, 0, k - depth - point)))
    head -= Cone(r_corner, r_corner + chamfer, chamfer, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((0, 0, k - chamfer)))
    shank = Cylinder(d / 2, length).moved(Location((0, 0, -length / 2)))
    screw = head + shank
    screw.color = STEEL
    screw.label = "M3x10 pan head hex socket"
    return Compound(children=[screw], label="screw M3")


if __name__ == "__main__":
    for name, make in (
        ("DHVQFN-16-1EP_2.5x3.5mm_P0.5mm_EP1x2mm.step", dhvqfn16),
        ("FH34SRJ-14S-0.5SH_50_.step", lambda: fh34srj(14)),
        ("FH34SRJ-12S-0.5SH_50_.step", lambda: fh34srj(12)),
        ("screw_M3_pan_hex_2mm.step", screw_m3),
    ):
        export_step(make(), str(HERE / name))
        print("wrote", name)
