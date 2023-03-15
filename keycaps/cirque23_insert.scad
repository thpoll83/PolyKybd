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

revision = "r6";
text_font = "Liberation Mono:style=Bold";
text_size = 5;

surf_offset = 0.001;
diameter = 23;
cutout_x = 17-0.1;
cutout_y = 14-0.05;
cylinder_height = 2.5;

pcb_thickness = 1.3;
socket_extra_thickness = 1.4;
connector_x = 9+0.25;
connector_y = 3+0.25;

module cirque_insert() {
    difference() {
        union() {
            difference() {
                union() {
                    translate([0,0,-socket_extra_thickness/2]) cube_rounded_xy(cutout_x, cutout_y, pcb_thickness+socket_extra_thickness, 1.5);    
                    translate([0,2,pcb_thickness/2+cylinder_height/2]) 
                        cylinder(d=diameter+1.4, h=cylinder_height, center=true, $fn=128);
                    translate([cutout_x/2-0.35,0,-pcb_thickness/2-socket_extra_thickness/2-0.1]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([-cutout_x/2+0.35,0,-pcb_thickness/2-socket_extra_thickness/2-0.1]) sphere(r=socket_extra_thickness*0.4, $fn=100);  
                   
                    translate([0,cutout_y/2-0.35,-pcb_thickness/2-socket_extra_thickness/2-0.1]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([cutout_x/2-2.2,-cutout_y/2+0.35,-pcb_thickness/2-socket_extra_thickness/2-0.1]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([-cutout_x/2+2.2,-cutout_y/2+0.35,-pcb_thickness/2-socket_extra_thickness/2-0.1]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                }
                //cutout for pcb parts
                cube_rounded_xy(cutout_x-2, cutout_y-2, pcb_thickness+socket_extra_thickness, 1.5);
                //IC cutout
                //translate([0,5,0.5]) cube_rounded_xy(connector_x, connector_x/2+1, pcb_thickness/2, 1.5);    
                
                //cable connector
                translate([0,-5.4,0]) cube([connector_x,connector_y,pcb_thickness*10], center=true);
                
                //pcb space
                translate([0,2,pcb_thickness+1.8]) cylinder(d=diameter+0.5, h=2, center=true, $fn=128);
                translate([0,2,pcb_thickness+0.9]) cylinder(d=diameter-1.0, h=2, center=true, $fn=128);
            }
            //revision text
            translate([0,1,-socket_extra_thickness/2-0.5]) linear_extrude(height = 0.3) {
                text(revision, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
            }

                     
        }
        translate([0,0,-5-pcb_thickness/2-socket_extra_thickness/2-0.51]) cube([100,100,10], center = true);
    }
}

/*
cirque_insert();

for ( i = [0 : 7] ){
    translate([-8.4-(26)*i,-4,-1.45]) rotate([0,-90,0]) cylinder(r=0.75, h=9.2, $fn=64);
    translate([-(26)*(i+1),0,0]) cirque_insert();
}
*/

for ( i = [0 : 4] ){
    translate([-(26)*(i+1)-6,0,-8.5]) cylinder(r=0.75, h=8, $fn=64);
    translate([-(26)*(i+1),0,1]) cirque_insert();
    translate([-(26)*(i+1),0,-10]) rotate([180,0,0]) cirque_insert();
}
translate([-84, 0, -4.7]) rotate([0,90,0]) cylinder(r=0.75, h=105, $fn=64, center =true);
