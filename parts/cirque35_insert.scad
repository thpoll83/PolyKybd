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

revision = "r2";
text_font = "Liberation Mono:style=Bold";
text_size = 5;

surf_offset = 0.001;
diameter = 35;
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
                    translate([5,-5,-socket_extra_thickness/2]) cube_rounded_xy(cutout_x, cutout_y, pcb_thickness+socket_extra_thickness, 1.5);    
                    translate([0,2,pcb_thickness/2+cylinder_height/2]) 
                        cylinder(d1=diameter+2.8, d2=diameter+1.4, h=cylinder_height, center=true, $fn=128);
                    translate([5+cutout_x/2-0.35,-5,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([5-cutout_x/2+0.35,-5,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);  
                   
                    translate([5,cutout_y/2-5.35,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([5+cutout_x/2-2.2,-cutout_y/2+0.35-5,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                    translate([5-cutout_x/2+2.2,-cutout_y/2+0.35-5,-pcb_thickness/2-socket_extra_thickness/2+0.4]) sphere(r=socket_extra_thickness*0.4, $fn=100);
                }
                //cutout for pcb parts
                translate([5,-5,0.5]) cube_rounded_xy(cutout_x-1.5, cutout_y-1.5, pcb_thickness+socket_extra_thickness+10.75, 1.5);    
                
                //pcb space
                translate([0,2,pcb_thickness+1.8+5]) cylinder(d=diameter+0.5, h=2, center=true, $fn=128);
                translate([0,2,pcb_thickness+0.9+3.5]) cylinder(d=diameter-1.0, h=8, center=true, $fn=128);
                translate([0,-11.5,0]) cube([9,5,5], center=true);
            //revision text
            }
            
            translate([0,9,1.65]) linear_extrude(height = 0.3) {
                text(revision, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
            }

                     
        }
        translate([0,0,-5-pcb_thickness/2-socket_extra_thickness/2-0.51]) cube([100,100,10], center = true);
    }
}

//cirque_insert();
union() {
for ( i = [0 : 3] ){
    translate([-(39)*(i+1)-7.5,5.9,-5]) cylinder(r=0.75, h=5, $fn=64);
    translate([-(39)*(i+1),0,-1]) cirque_insert();
    //translate([-(45)*(i+1),0,-9]) rotate([180,0,0]) cirque_insert();
}
translate([-105, 5.9, -4.7]) rotate([0,90,0]) cylinder(r=0.9, h=119, $fn=64, center =true);
}//h=196