include <NopSCADlib/core.scad>
include <NopSCADlib/utils/thread.scad>

module cube_rounded_xy(x,y,z,r, center = true) {
    $fn=100;
    minkowski()
    {
      cube([x-2*r,y-2*r,z-r/4], center = center);
      cylinder(r=r,h=r/4);
    }
}

revision = "r1";
text_font = "Liberation Mono:style=Bold";
text_size = 5;

cutout_x = 13.8;
cutout_y = 13.8;

plate_thickness = 1.4;

module keyswitch_cap() {
    difference() {
        union() {
            difference() {
                union() {
                    translate([0,0,-plate_thickness/2]) cube_rounded_xy(cutout_x, cutout_y, plate_thickness*2+0.2, 1.5);    
                    translate([0,0,plate_thickness/2+0.5]) 
                    cube_rounded_xy(cutout_x+2, cutout_y+2, 1, 1.5);    
                    translate([cutout_x/2-0.35,0,-plate_thickness]) sphere(r=plate_thickness*0.5, $fn=100);
                    translate([-cutout_x/2+0.35,0,-plate_thickness]) sphere(r=plate_thickness*0.5, $fn=100);
                    translate([0,cutout_y/2-0.35,-plate_thickness]) sphere(r=plate_thickness*0.5, $fn=100);
                    translate([0,-cutout_y/2+0.35,-plate_thickness]) sphere(r=plate_thickness*0.5, $fn=100);

                }
                //hollow out
                translate([0,0,-1.5]) cube_rounded_xy(cutout_x-2, cutout_y-2, plate_thickness*2, 1.5);

            }
            //revision text
            translate([0,1,0.1]) rotate([0,-180,0]) linear_extrude(height = 0.3) {
                text(revision, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 32);
            }

                     
        }
        translate([0,0,-5-plate_thickness-0.6]) cube([100,100,10], center = true);
    }
}


keyswitch_cap();
