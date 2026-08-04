
pcb_thickness = 1.2;
// The flange above the plate is a STRAIGHT layer plus a CHAMFERED one, and the
// two are sized independently on purpose.  Thickening the flange from 1.0 to
// 1.5 mm (2026-08, after a resin printer refused the frame -- 1.5 mm is the
// "recommended" wall, not merely the minimum) must come out of the straight
// layer alone: the chamfer is a linear_extrude(scale=), so stretching it in z
// while its inward step stays fixed lays the chamfer angle down flatter.  Keep
// cap_chamfer at its original 0.5 mm and put every extra millimetre into
// cap_straight_top, and the chamfer is the same wedge it always was.
//
// The top is free to grow: it sits proud of the plate on the side away from the
// switch, under the keycap skirt, with millimetres to spare.
cap_chamfer      = 0.5;        // chamfer height -- ORIGINAL, do not stretch
cap_straight_top = 1.0;        // straight part, carries the extra thickness
// The BOTTOM is pinned to the frame's web thickness (1.0 mm, gen_diffuser_frame.py).
// It must not hang BELOW the web: the tapered layer's slope and the web's flat
// underside would then converge to a feather edge -- measured 0.305 mm at the
// thumb-link junctions, i.e. the same knife edge as the cap horns, in section
// instead of plan.  The web cannot grow to 1.5 to match, because the spacer is
// notched on BOTH faces so one printed part serves either half, and that would
// leave 3.8 - 2*(1.5+0.3) = 0.2 mm of rib.  So: bottom stack == web == 1.0 mm.
cap_thickness_bot = 0.5;       // -> 1.0 mm flange below the plate, flush with the web
cutout_diameter = 5;
cap_overlap = 1;

// The cap is circle(d=7) cut by a chord that sits ABOVE centre, so it is a
// MINOR segment and its two ends run out to a knife edge at x = +-3.4911.
// Everything past |x| = 3.3388 is under 0.8 mm and the last 0.15 mm is under
// 0.6 -- which is exactly what the print service measured and refused.  Square
// the ends off instead: at |x| = 3.0 the cap is still 1.553 mm deep, and it
// keeps 0.5 mm of overhang past the d=5 plug, which is what traps the plate.
cap_trim = 3.0;
// Lean of that cut, in the XY plane, degrees.  0 = a plain axis-aligned cut,
// i.e. subtract a box.  Positive leans the cut OUTWARD as it goes away from the
// chord, so the lip is kept out to a larger x wherever the cap is deep enough
// to afford it, and only the shallow strip along the chord is taken.
//
// 45 beats 0 on BOTH counts, which is why it is the default.  Measured by
// rasterising the profile and opening it with a disc (the same test a print
// service runs), area of cap that is thinner than 0.8 mm:
//     untrimmed  0.1132 mm²   of 17.495 mm² cap
//     0°         0.0916 mm²   of 16.552
//     45°        0.0476 mm²   of 17.278      <- half the thin area, 4.4% more lip
// An axis-aligned cut leaves a 90° corner against the chord and that corner is
// itself pinched; leaning it opens the corner to 135° and spends the cut on the
// shallow strip along the chord, which is the part that was thin to begin with.
cap_trim_angle = 45;

module cap_profile() {
    W = cutout_diameter + cap_overlap * 2;
    difference() {
        difference() {
            circle(d = W, $fn = 64);
            translate([0,-2.25 -cap_overlap]) square(W, center = true);
        }
        // pivot on the chord, at (cap_trim, 0.25), so the cut always starts
        // there and only its lean changes
        for (s = [1, -1]) scale([s, 1])
            translate([cap_trim, W/2 - 2.25 - cap_overlap])
                rotate(-cap_trim_angle)
                    translate([0, -2*W]) square([2*W, 4*W]);
    }
}

module diffuser() {
difference() {
    linear_extrude(pcb_thickness)
        union() {
            circle(d=cutout_diameter, $fn =64);
            translate([0,-0.5]) square([cutout_diameter,1], center = true);
        }
    translate([0,-1.66,0]) cube([cutout_diameter+1,2,pcb_thickness*2+0.5], center = true);
}

// The underside is ONE straight layer, not a straight + a tapered one.  A
// tapered rim sweeps its radius from 3.5 down to 3.15 mm over its height, so a
// web stem whose edge passes anywhere in that 0.35 mm band runs tangent to the
// slope at some z and leaves a wafer between the two surfaces -- 0.043 mm at
// the thumb links on the shipped frame, the thinnest thing on the whole part.
// A vertical rim has one radius, so a stem either clears it or merges with it.
// Nothing needs the chamfer here: this face points away from the plate, into
// the spacer gap, and the diffuser enters its opening from below plug-first.
translate([0,0,-2*cap_thickness_bot]) {
    linear_extrude(2*cap_thickness_bot) cap_profile();
}

translate([0,0,pcb_thickness+cap_straight_top]) {
    linear_extrude(cap_chamfer, scale = 0.9) cap_profile();
}

translate([0,0,pcb_thickness]) {
    linear_extrude(cap_straight_top) cap_profile();
}
}


module torus(r1=1, r2=2, angle=360, endstops=0, $fn=50){
    if(angle < 360){
        intersection(){
            rotate_extrude(convexity=10, $fn=$fn)
            translate([r2, 0, 0])
            circle(r=r1, $fn=$fn);
            
            color("blue")
            wedge(h=r1*3, r=r2*2, a=angle);
        }
    }else{
        rotate_extrude(convexity=10, $fn=$fn)
        translate([r2, 0, 0])
        circle(r=r1, $fn=$fn);
    }
    
    if(endstops && angle < 360){
        rotate([0,0,angle/2])
        translate([0,r2,0])
        sphere(r=r1);
        
        rotate([0,0,-angle/2])
        translate([0,r2,0])
        sphere(r=r1);
    }
}

module diffuser_cluster() {
    torus(0.5,24,$fn=128);
    for ( i = [0 : 18] ){
        rotate([0, 0, 360/18*i]) 
        translate([0,-21.5,-0.6]) {
            translate([0,0,0.6]) rotate([90,0,0]) cylinder(2.5, d = 1, $fn=32);
            diffuser();
        }
    }
}

union() {
rotate([-4, 0, 0]) diffuser_cluster();
rotate([4, 0, 0]) translate([0, -48,3.35]) diffuser_cluster();
rotate([-4, 0, 0]) translate([-48, 0,0]) diffuser_cluster();
rotate([4, 0, 0]) translate([-48, -48,3.35]) diffuser_cluster();
}