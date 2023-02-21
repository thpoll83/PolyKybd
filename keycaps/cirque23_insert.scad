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
text_size = 3.5;

surf_offset = 0.001;
diameter = 23;
cutout_x = 17-0.15;
cutout_y = 14-0.15;

pcb_thickness = 1.8;
connector_x = 9+0.25;
connector_y = 3+0.25;

module cirque_insert() {
    union() {
        difference() {
            union() {
                cube_rounded_xy(cutout_x, cutout_y, pcb_thickness, 1.5);    
                translate([0,2,pcb_thickness]) 
                    cylinder(d=diameter+1, h=2, center=true, $fn=128);
                translate([0,2,pcb_thickness]) 
                    male_metric_thread(d=diameter+2, pitch=0.75, length=2, center = true);            
            }
            //cutout for pcb parts
            translate([0,0,0.5]) cube_rounded_xy(cutout_x-1, cutout_y-1, pcb_thickness, 1.5);
            translate([0,5,1.3]) cube_rounded_xy(connector_x, connector_x, pcb_thickness, 1.5);    
            
            //cable connector
            translate([0,-5.3,0]) cube([connector_x,connector_y,pcb_thickness*10], center=true);
            
            //pcb space
            translate([0,2,pcb_thickness+0.5]) cylinder(d=diameter+0.5, h=2, center=true, $fn=128);
        }
        //revision text
        translate([-5.9,0,-0.3]) rotate([0,0,90]) linear_extrude(height = 0.3) {
            text(revision, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
        }
    }
    
    //screw cap
    union() {
        translate([0,2,10])
        difference(){
            cylinder(r2=(diameter+3)/2, r1=(diameter+5.25)/2, h=3.1, center=true, $fn=128);
            cylinder(d=diameter+2.25, h=4, center=true, $fn=128);
       }
       
       //stop ring
       translate([0,2,11.35])
        difference(){
            cylinder(d=diameter+2.25, h=0.4, center=true, $fn=128);
            cylinder(d=diameter-0.25, h=4, center=true, $fn=128);
       }
       
       //thread
       translate([0,2,10])
                        female_metric_thread(d=diameter+1.5, pitch=0.75, length=2.5, center = true);  
    }   
}


cirque_insert();
/*
for ( i = [0 : 3] ){
    translate([0.5-(disp_x+1)*i,0,0.5]) rotate([0,-90,0]) cylinder(r=0.35, h=2, $fn=64);
    translate([0.5-(disp_x+1)*i,24,0.5]) rotate([0,-90,0]) cylinder(r=0.35, h=2, $fn=64);
    translate([-(disp_x+1)*(i+1),0,0]) disp_holder();
}
*/