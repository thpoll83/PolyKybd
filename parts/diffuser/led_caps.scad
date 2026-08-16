// SUPERSEDED -- the earlier generation of the LED diffuser, kept for reference.
// The part in use is diffuser.scad (+ the generated diffuser_frame_*.scad).
//
// Each cap here is a ~7 x 4.2 x 3.2 mm D-shaped light pipe with a flange on
// both faces, clipping through a 5 mm hole in a 1.2 mm PCB; the top level lays
// out 4 rings of 19 on a torus sprue.
//
// NOTE: this file defines diffuser(), diffuser_cluster() and torus(), the SAME
// module names as diffuser.scad next to it -- never `use <>` both from one file.

pcb_thickness = 1.2;
cap_thickness = 0.5; //will be doubled
cutout_diameter = 5;
cap_overlap = 1;

module diffuser() {
difference() {
    linear_extrude(pcb_thickness)
        union() {
            circle(d=cutout_diameter, $fn =64);
            translate([0,-0.5]) square([cutout_diameter,1], center = true);
        }
    translate([0,-1.66,0]) cube([cutout_diameter+1,2,pcb_thickness*2+0.5], center = true);
}

translate([0,0,-cap_thickness]) {
    linear_extrude(cap_thickness)
        difference() {
            circle(d=cutout_diameter+cap_overlap*2, $fn =64);
            translate([0,-2.25 -cap_overlap]) square(cutout_diameter+cap_overlap*2, center = true);
        }
}

translate([0,0,-cap_thickness]) {
    rotate([0,180,0]) {
    linear_extrude(cap_thickness, scale = 0.9)
        difference() {
            circle(d=cutout_diameter+cap_overlap*2, $fn =64);
            translate([0,-2.25 -cap_overlap]) square(cutout_diameter+cap_overlap*2, center = true);
        }
    }
}

translate([0,0,pcb_thickness+cap_thickness]) {
    linear_extrude(cap_thickness, scale = 0.9)
        difference() {
            circle(d=cutout_diameter+cap_overlap*2, $fn =64);
            translate([0,-2.25 -cap_overlap]) square(cutout_diameter+cap_overlap*2, center = true);
        }
}

translate([0,0,pcb_thickness]) {
    linear_extrude(cap_thickness)
        difference() {
            circle(d=cutout_diameter+cap_overlap*2, $fn =64);
            translate([0,-2.25 -cap_overlap]) square(cutout_diameter+cap_overlap*2, center = true);
        }
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