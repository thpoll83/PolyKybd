module cube_rounded_xy(x,y,z,r) {
    $fn=50;
    translate([r,r,0]) minkowski()
    {
      cube([x-2*r,y-2*r,z-r/4]);
      cylinder(r=r,h=r/4);
    }
}

surf_offset = 0.001;
disp_thickness = 1.4;
disp_emboss = 0.15;
disp_x = 27;
disp_y = 19.5;

cutout_y = 26;
cutout_thickness = 2.5;

pcb_thickness = 1.2;

module disp_holder() {
    difference() {
        union() {
            cube_rounded_xy(disp_x, cutout_y, cutout_thickness, 1);    
            translate([0,-2,0]) cube([disp_x,cutout_y+2*2,cutout_thickness-pcb_thickness]);
        }
        //translate([-0.5, 2+disp_emboss, cutout_thickness-disp_emboss-surf_offset]) 
        //linear_extrude(height = disp_emboss+surf_offset*2, scale = [1,]) square([disp_x+1,disp_y-disp_emboss], center = false);
        
        translate([-0.5, 2+disp_emboss/2, cutout_thickness-disp_thickness+surf_offset]) cube([disp_x+1,disp_y-disp_emboss*2,disp_thickness]);
        translate([-0.5, 2, cutout_thickness-disp_thickness-disp_emboss]) cube([disp_x+1,disp_y,disp_thickness]);
        translate([(disp_x-16)/2,21,cutout_thickness-disp_thickness -0.1]) cube([16,10,1]);
        translate([(disp_x-8)/2,14,cutout_thickness-1]) cube_rounded_xy(8, 8, 1, 1);
    }
}


disp_holder();

for ( i = [0 : 3] ){
    translate([0.5-(disp_x+1)*i,0,0.5]) rotate([0,-90,0]) cylinder(r=0.35, h=2, $fn=64);
    translate([0.5-(disp_x+1)*i,24,0.5]) rotate([0,-90,0]) cylinder(r=0.35, h=2, $fn=64);
    translate([-(disp_x+1)*(i+1),0,0]) disp_holder();
}