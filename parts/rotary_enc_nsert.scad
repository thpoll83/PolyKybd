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

pcb_thickness = 0.8;
socket_extra_thickness = 1.4;

module enc_insert() {
    difference() {
        union() {
            difference() {
                union() {
                    translate([0,0,-socket_extra_thickness/2]) cube_rounded_xy(cutout_x, cutout_y, pcb_thickness+socket_extra_thickness, 1.5);    
                    translate([0,0,pcb_thickness/2+0.5]) 
                    cube_rounded_xy(cutout_x+4, cutout_y+4, 1, 1.5);    
                    
                    translate([-cutout_x/2+0.35,0,-pcb_thickness/2-socket_extra_thickness/2+0.25]) sphere(r=socket_extra_thickness*0.45, $fn=100);  
                   
                    translate([-cutout_x/2+2.2,cutout_y/2-0.35,-pcb_thickness/2-socket_extra_thickness/2+0.25]) sphere(r=socket_extra_thickness*0.45, $fn=100);
                    translate([cutout_x/2-2.2,cutout_y/2-0.35,-pcb_thickness/2-socket_extra_thickness/2+0.25]) sphere(r=socket_extra_thickness*0.45, $fn=100);
                    translate([-cutout_x/2+2.2,-cutout_y/2+0.35,-pcb_thickness/2-socket_extra_thickness/2+0.25]) sphere(r=socket_extra_thickness*0.45, $fn=100);
                }
                //cutout for pcb parts
                translate([0,0,-1.5]) cube_rounded_xy(cutout_x-2, cutout_y-2, pcb_thickness+socket_extra_thickness, 1.5);

            }
            //revision text
            translate([-4,3,-0.1]) rotate([0,-180,0]) linear_extrude(height = 0.3) {
                text(revision, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
            }

                     
        }
        translate([0,0,-5-pcb_thickness/2-socket_extra_thickness/2-0.51]) cube([100,100,10], center = true);
         translate([1.65,-0.95,0]) cube_rounded_xy(13.7, 12.1, 10, 0.4); 
    }
}


//enc_insert();

for ( i = [0 : 4] ){
    translate([-(26)*(i+1)-6,0,-11]) cylinder(r=0.75, h=12.5, $fn=64);
    translate([-(26)*(i+1),0,0]) enc_insert();
    translate([-(26)*(i+1),0,-9.7]) rotate([180,0,0]) enc_insert();
}
translate([-84, 0, -5]) rotate([0,90,0]) cylinder(r=0.75, h=104, $fn=64, center =true);
