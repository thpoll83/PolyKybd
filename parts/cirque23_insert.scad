include <NopSCADlib/core.scad>
include <NopSCADlib/utils/thread.scad>

module cube_rounded_xy(x,y,z,r, center = true) {
    $fn=50;
    minkowski()
    {
      cube([x-2*r,y-2*r,z-r/4], center = center);
      cylinder(r=r,h=r/4);
    }
}

revision = "r1";
text_font = "Liberation Mono:style=Bold";
text_size = 5;

surf_offset = 0.001;
diameter = 23;
cutout_x = 17-0.1;
cutout_y = 14-0.05;
cylinder_height = 7.5;

pcb_thickness = 1.3;
socket_extra_thickness = 1.4;
connector_x = 9+0.25;
connector_y = 1;

module cirque_insert() {
    difference() {
        union() {
            difference() {
                union() {
                    translate([0,0,-socket_extra_thickness/2]) cube_rounded_xy(cutout_x, cutout_y, pcb_thickness+socket_extra_thickness, 1.5);    
                    translate([0,2,pcb_thickness/2+cylinder_height/2]) 
                        cylinder(d1=diameter+2.8, d2=diameter+1.4, h=cylinder_height, center=true, $fn=128);
                    translate([cutout_x/2-0.35,0,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([-cutout_x/2+0.35,0,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);  
                   
                    translate([0,cutout_y/2-0.35,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([cutout_x/2-2.2,-cutout_y/2+0.35,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([-cutout_x/2+2.2,-cutout_y/2+0.35,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                }
                //cutout for pcb parts
                translate([0,0,0.5]) cube_rounded_xy(cutout_x-1.5, cutout_y-1.5, pcb_thickness+socket_extra_thickness+10.75, 1.5);    
                
                //pcb space
                translate([0,2,pcb_thickness+1.8+5]) cylinder(d=diameter+0.5, h=2, center=true, $fn=128);
                translate([0,2,pcb_thickness+0.9+3.5]) cylinder(d=diameter-1.0, h=8, center=true, $fn=128);
            }
            //revision text
            translate([0,9,1.65]) linear_extrude(height = 0.3) {
                text(revision, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
            }

                     
        }
        translate([0,0,-5-pcb_thickness/2-socket_extra_thickness/2-0.51]) cube([100,100,10], center = true);
    }
}

cirque_insert();
/*
cirque_insert();

for ( i = [0 : 7] ){
    translate([-8.4-(26)*i,-4,-1.45]) rotate([0,-90,0]) cylinder(r=0.75, h=9.2, $fn=64);
    translate([-(26)*(i+1),0,0]) cirque_insert();
}
*/
/*
for ( i = [0 : 2] ){
    translate([-(28)*(i+1)-7.5,5.9,-9.5]) cylinder(r=0.75, h=10, $fn=64);
    translate([-(28)*(i+1),0,1]) cirque_insert();
    translate([-(28)*(i+1),0,-10]) rotate([180,0,0]) cirque_insert();
}
translate([-63.5, 5.9, -4.7]) rotate([0,90,0]) cylinder(r=0.75, h=56, $fn=64, center =true);
*/