// ===========================================================================
//  PolyKybd split72 — one-piece LED diffuser frame (left half)
//
//  GENERATED — do not edit the coordinates by hand.
//  Re-run:  python3 parts/tools/gen_diffuser_frame.py left
//
//  All 36 diffusers sit at their exact plate position and orientation, tied
//  together by a web UNDER the plate that routes through the solid material
//  between the switch openings.  The diffuser itself is parts/diffuser.scad's
//  diffuser() module, used unmodified — this file adds only the web.
//
//  ---------------------------------------------------------------------
//  revision   r1.0          generated 2026-07-31
//  source     poly_kybd/poly_kybd_split72_plate_left.kicad_pcb
//  diffusers  36
//  web        54 rungs + 30 rails + 5 routed links,
//             923 mm of 2.0 mm stem
//  clearance  >= 0.40 mm from every switch opening (checked per segment)
//
//  ASSEMBLY   Offer the frame up to the plate FROM BELOW so each diffuser
//             passes through its own switch opening, then slide it ~5.5 mm
//             away from the round side until every plug seats in its
//             half-round.  The top and bottom caps then trap the plate and
//             the switches block it sliding back, so no glue or snap fit is
//             needed.  4.5 mm is the minimum that clears (the 20-degree
//             rotated thumb key is the limiting one); below 4.0 mm it binds.
//             Do this BEFORE the plate meets the spacer — the slide needs the
//             space under the plate to be clear.
//
//  The spacer is notched for this web: see right_spacer() in
//  case/case_polykybd_split72_lr.scad.  One spacer serves both halves —
//  flip it over for the other one.
//  ---------------------------------------------------------------------
// ===========================================================================

use <diffuser.scad>

// The web hangs below the plate (plate underside is z = 0), co-planar with
// diffuser()'s bottom cap stack, which occupies z = -2*cap_thickness .. 0.
web_t  = 1.0;
stem_w = 2.0;

$fn = 64;

module _stem_left(a, b) {
    hull() {
        translate(a) circle(d = stem_w);
        translate(b) circle(d = stem_w);
    }
}

// Grown, open-topped copy of the web — the spacer subtracts this so its ribs
// are notched exactly where the web crosses them and keep full height elsewhere.
//
// lat and deep are SEPARATE on purpose.  `deep` sets how far into the spacer
// the notch reaches, so it must stay small or the ribs get cut clean through.
// `lat` sets how wide the notch is, and wants to be big enough that a rib the
// notch only partly overlaps is removed rather than left as a fragile fin.
module diffuser_frame_left_clearance(lat = 0.3, deep = 0.3, up = 6) {
    translate([0, 0, -web_t - deep])
        linear_extrude(web_t + deep + up)
            offset(r = lat) diffuser_frame_left_web_2d();
}

module diffuser_frame_left_web_2d() {
    union() {
        _stem_left([-47.148, 52.601], [-37.623, 52.601]);  // rung
        _stem_left([-47.148, 33.551], [-37.623, 33.551]);  // rung
        _stem_left([-47.148, 14.500], [-37.623, 14.500]);  // rung
        _stem_left([-28.098, 52.601], [-37.623, 52.601]);  // rung
        _stem_left([-28.098, 52.601], [-18.573, 52.601]);  // rung
        _stem_left([-28.098, 33.551], [-37.623, 33.551]);  // rung
        _stem_left([-28.098, 33.551], [-18.573, 33.551]);  // rung
        _stem_left([-28.098, 14.500], [-37.623, 14.500]);  // rung
        _stem_left([-28.098, 14.500], [-18.573, 14.500]);  // rung
        _stem_left([-28.098, -4.549], [-37.623, -4.549]);  // rung
        _stem_left([-28.098, -4.549], [-18.573, -4.549]);  // rung
        _stem_left([-9.048, 54.982], [-18.573, 54.982]);  // rung
        _stem_left([-9.048, 54.982], [0.477, 54.982]);  // rung
        _stem_left([-9.048, 35.932], [-18.573, 35.932]);  // rung
        _stem_left([-9.048, 35.932], [0.477, 35.932]);  // rung
        _stem_left([-9.048, 16.882], [-18.573, 16.882]);  // rung
        _stem_left([-9.048, 16.882], [0.477, 16.882]);  // rung
        _stem_left([-9.048, -2.168], [-18.573, -2.168]);  // rung
        _stem_left([-9.048, -2.168], [0.477, -2.168]);  // rung
        _stem_left([10.002, 57.363], [0.477, 57.363]);  // rung
        _stem_left([10.002, 57.363], [19.527, 57.363]);  // rung
        _stem_left([10.002, 38.313], [0.477, 38.313]);  // rung
        _stem_left([10.002, 38.313], [19.527, 38.313]);  // rung
        _stem_left([10.002, 19.263], [0.477, 19.263]);  // rung
        _stem_left([10.002, 19.263], [19.527, 19.263]);  // rung
        _stem_left([10.002, 0.213], [0.477, 0.213]);  // rung
        _stem_left([10.002, 0.213], [19.527, 0.213]);  // rung
        _stem_left([10.002, -18.837], [0.477, -18.837]);  // rung
        _stem_left([10.002, -18.837], [19.527, -18.837]);  // rung
        _stem_left([29.052, 54.982], [19.527, 54.982]);  // rung
        _stem_left([29.052, 54.982], [38.577, 54.982]);  // rung
        _stem_left([29.052, 35.932], [19.527, 35.932]);  // rung
        _stem_left([29.052, 35.932], [38.577, 35.932]);  // rung
        _stem_left([29.052, 16.882], [19.527, 16.882]);  // rung
        _stem_left([29.052, 16.882], [38.577, 16.882]);  // rung
        _stem_left([29.052, -2.168], [19.527, -2.168]);  // rung
        _stem_left([29.052, -2.168], [38.577, -2.168]);  // rung
        _stem_left([29.052, -21.218], [19.527, -21.218]);  // rung
        _stem_left([29.052, -21.218], [38.577, -21.218]);  // rung
        _stem_left([48.102, 52.601], [38.577, 52.601]);  // rung
        _stem_left([48.102, 52.601], [57.627, 52.601]);  // rung
        _stem_left([48.102, 33.551], [38.577, 33.551]);  // rung
        _stem_left([48.102, 33.551], [57.627, 33.551]);  // rung
        _stem_left([48.102, 14.500], [38.577, 14.500]);  // rung
        _stem_left([48.102, 14.500], [57.627, 14.500]);  // rung
        _stem_left([48.102, -4.549], [38.577, -4.549]);  // rung
        _stem_left([48.102, -4.549], [57.627, -4.549]);  // rung
        _stem_left([48.102, -23.600], [38.577, -23.600]);  // rung
        _stem_left([48.102, -23.600], [57.627, -23.600]);  // rung
        _stem_left([67.152, -23.600], [57.627, -23.600]);  // rung
        _stem_left([71.914, 52.601], [57.627, 52.601]);  // rung
        _stem_left([71.914, 33.551], [57.627, 33.551]);  // rung
        _stem_left([71.914, 14.500], [57.627, 14.500]);  // rung
        _stem_left([71.914, -4.549], [57.627, -4.549]);  // rung
        _stem_left([-37.623, 52.601], [-37.623, 33.551]);  // rail
        _stem_left([-37.623, 33.551], [-37.623, 14.500]);  // rail
        _stem_left([-37.623, 14.500], [-37.623, -4.549]);  // rail
        _stem_left([-18.573, 54.982], [-18.573, 52.601]);  // rail
        _stem_left([-18.573, 35.932], [-18.573, 33.551]);  // rail
        _stem_left([-18.573, 16.882], [-18.573, 14.500]);  // rail
        _stem_left([-18.573, 14.500], [-18.573, -2.168]);  // rail
        _stem_left([-18.573, -2.168], [-18.573, -4.549]);  // rail
        _stem_left([0.477, 57.363], [0.477, 54.982]);  // rail
        _stem_left([0.477, 54.982], [0.477, 38.313]);  // rail
        _stem_left([0.477, 38.313], [0.477, 35.932]);  // rail
        _stem_left([0.477, 19.263], [0.477, 16.882]);  // rail
        _stem_left([0.477, 0.213], [0.477, -2.168]);  // rail
        _stem_left([0.477, -2.168], [0.477, -18.837]);  // rail
        _stem_left([19.527, 57.363], [19.527, 54.982]);  // rail
        _stem_left([19.527, 38.313], [19.527, 35.932]);  // rail
        _stem_left([19.527, 35.932], [19.527, 19.263]);  // rail
        _stem_left([19.527, 19.263], [19.527, 16.882]);  // rail
        _stem_left([19.527, 0.213], [19.527, -2.168]);  // rail
        _stem_left([19.527, -18.837], [19.527, -21.218]);  // rail
        _stem_left([38.577, 54.982], [38.577, 52.601]);  // rail
        _stem_left([38.577, 35.932], [38.577, 33.551]);  // rail
        _stem_left([38.577, 16.882], [38.577, 14.500]);  // rail
        _stem_left([38.577, 14.500], [38.577, -2.168]);  // rail
        _stem_left([38.577, -2.168], [38.577, -4.549]);  // rail
        _stem_left([38.577, -21.218], [38.577, -23.600]);  // rail
        _stem_left([57.627, 52.601], [57.627, 33.551]);  // rail
        _stem_left([57.627, 33.551], [57.627, 14.500]);  // rail
        _stem_left([57.627, 14.500], [57.627, -4.549]);  // rail
        _stem_left([57.627, -4.549], [57.627, -23.600]);  // rail
        _stem_left([-28.098, -4.549], [-30.500, -5.499]);  // link
        _stem_left([-30.500, -5.499], [-43.500, -5.999]);  // link
        _stem_left([-43.500, -5.999], [-48.000, -10.499]);  // link
        _stem_left([-48.000, -10.499], [-50.744, -10.495]);  // link
        _stem_left([-50.744, -10.495], [-53.000, -11.999]);  // link
        _stem_left([-53.000, -11.999], [-72.500, -17.499]);  // link
        _stem_left([-72.500, -17.499], [-75.168, -17.810]);  // link
        _stem_left([-28.098, -4.549], [-25.500, -5.499]);  // link
        _stem_left([-25.500, -5.499], [-20.000, -5.499]);  // link
        _stem_left([-20.000, -5.499], [-18.500, -8.499]);  // link
        _stem_left([-18.500, -8.499], [-19.000, -25.999]);  // link
        _stem_left([-19.000, -25.999], [-20.500, -27.499]);  // link
        _stem_left([-20.500, -27.499], [-21.181, -28.454]);  // link
        _stem_left([-21.181, -28.454], [-23.500, -29.499]);  // link
        _stem_left([-23.500, -29.499], [-42.500, -31.999]);  // link
        _stem_left([-42.500, -31.999], [-45.024, -32.205]);  // link
        _stem_left([-45.024, -32.205], [-47.500, -33.499]);  // link
        _stem_left([-47.500, -33.499], [-64.500, -37.999]);  // link
        _stem_left([-64.500, -37.999], [-67.086, -38.464]);  // link
    }
}

module diffuser_frame_left_web() { translate([0, 0, -web_t]) linear_extrude(web_t) diffuser_frame_left_web_2d(); }

module diffuser_frame_left_diffusers() {
    translate([-28.098, 31.651, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 0
    translate([29.052, -23.118, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 1
    translate([29.052, 34.032, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 2
    translate([-47.148, 50.701, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 3
    translate([29.052, -4.068, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 4
    translate([10.002, -20.737, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 5
    translate([-66.437, -40.249, 0]) rotate([0, 0, 20.00]) diffuser();  // LED 6
    translate([71.914, -6.449, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 7
    translate([-74.518, -19.596, 0]) rotate([0, 0, 20.00]) diffuser();  // LED 8
    translate([48.102, -25.500, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 9
    translate([71.914, 31.651, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 10
    translate([48.102, 50.701, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 11
    translate([-47.148, 31.651, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 12
    translate([-28.098, -6.449, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 13
    translate([-50.301, -12.343, 0]) rotate([0, 0, 13.50]) diffuser();  // LED 14
    translate([29.052, 53.082, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 15
    translate([-21.015, -30.347, 0]) rotate([0, 0, 5.00]) diffuser();  // LED 16
    translate([48.102, 31.651, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 17
    translate([-9.048, -4.068, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 18
    translate([-28.098, 12.600, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 19
    translate([-9.048, 34.032, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 20
    translate([10.002, 17.363, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 21
    translate([10.002, -1.687, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 22
    translate([-9.048, 14.982, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 23
    translate([67.152, -25.500, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 24
    translate([-47.148, 12.600, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 25
    translate([-44.581, -34.053, 0]) rotate([0, 0, 13.50]) diffuser();  // LED 26
    translate([71.914, 50.701, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 27
    translate([-9.048, 53.082, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 28
    translate([29.052, 14.982, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 29
    translate([48.102, -6.449, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 30
    translate([71.914, 12.600, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 31
    translate([10.002, 55.463, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 32
    translate([48.102, 12.600, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 33
    translate([-28.098, 50.701, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 34
    translate([10.002, 36.413, 0]) rotate([0, 0, 0.00]) diffuser();  // LED 35
}

module diffuser_frame_left() {
    union() {
        diffuser_frame_left_diffusers();
        diffuser_frame_left_web();
    }
}

diffuser_frame_left();
