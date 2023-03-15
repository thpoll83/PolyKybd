module cube_rounded_xy(x,y,z,r) {
    $fn=50;
    translate([r,r,0]) minkowski()
    {
      cube([x-2*r,y-2*r,z-r/4]);
      cylinder(r=r,h=r/4);
    }
}

revision = "r6";
text_font = "Liberation Mono:style=Bold";
text_size = 7;

surf_offset = 0.001;
disp_thickness = 1.6;
disp_emboss = 0.3;
disp_x = 27-0.05;
disp_y = 19.5+0.05;

cutout_y = 26-0.05;
cutout_thickness = 2.5;

pcb_thickness = 1.3;

lcd_x = 21.7;
lcd_y= 10.9;

module disp_holder(print_support, show_display) {
    
    if(show_display) {
        color([0.1,0.1,0.1, 0.8]) translate([0, 2-0.2, cutout_thickness-disp_thickness-disp_emboss]) cube([disp_x,disp_y,disp_thickness]);
        
        color([0.1,0.1,0.1]) translate([(disp_x-lcd_x)/2, 5, 2.15]) cube([lcd_x,lcd_y,0.1]);
    }
    
    color([0.2,0.2,0.2]) difference() {
        union() {
            cube_rounded_xy(disp_x, cutout_y, cutout_thickness, 1.25);    
            translate([0,-2,-0.2]) cube([disp_x,cutout_y+2*2,cutout_thickness-pcb_thickness+0.2]);
        }
        
        translate([-0.5, 2+disp_emboss/2, cutout_thickness-disp_thickness+surf_offset]) cube([disp_x+1,disp_y-disp_emboss*2,disp_thickness]);
        
        //display space
        translate([-0.5, 2-0.2, cutout_thickness-disp_thickness-disp_emboss]) cube([disp_x+1,disp_y,disp_thickness]);
        
        //flex cable cutout
        translate([(disp_x-17)/2,21,cutout_thickness-disp_thickness -0.3]) cube([17,10,1.3]);
        
        //tape cutout
        translate([(disp_x-8)/2,14,cutout_thickness-1]) cube_rounded_xy(8, 8, 1, 1);
        
        //revision text
        translate([disp_x/2,disp_y/2+2,0.3-surf_offset-0.2]) rotate([180,0,0]) linear_extrude(height = 0.3) {
            text(revision, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
        }
        
        //translate([-0.01,22.5,0]) cube([4.5,5.5,0.25]);
    }
    
    //distnace holders
    translate([26,-1,-1.701]) cylinder(r=0.75, h = 2.9, $fn=32);
    translate([1,-1,-1.701]) cylinder(r=0.75, h = 2.9, $fn=32);
    translate([26,27,-1.701]) cylinder(r=0.75, h = 2.9, $fn=32);
    translate([1,27,-1.701]) cylinder(r=0.75, h = 2.9, $fn=32);
    
    if(print_support) {
        translate([0,2-0.2,0]) //cylinder(r1=1,r2=1, h=pcb_thickness+disp_thickness-disp_emboss*2,$fn=30);
        cube([0.2,0.35,pcb_thickness+disp_thickness-disp_emboss*2], center = false);
        translate([disp_x-0.2,2-0.2,0]) //cylinder(r1=1,r2=1, h=pcb_thickness+disp_thickness-disp_emboss*2,$fn=30);
        cube([0.2,0.35,pcb_thickness+disp_thickness-disp_emboss*2], center = false);
    }
}

/*
disp_holder(false, false);

for ( i = [0 : 5] ){
    translate([0.5-(disp_x+1)*i-1,1,0.5]) rotate([0,-90,0]) cube([1,1.5,2], center=true);
    translate([0.5-(disp_x+1)*i-1,21.95,0.5]) rotate([0,-90,0]) cube([1,1.1,2], center=true);
    translate([-(disp_x+1)*(i+1),0,0]) disp_holder(false, false);
}
*/

for ( i = [0 : 4] ){
    translate([(disp_x+1)*i-6,0,-10]) cylinder(r=0.75, h=9, $fn=64);
    translate([(disp_x+1)*i-29,0,-2]) disp_holder(false, false);
    translate([(disp_x+1)*i-29,disp_y+7,-9.7]) rotate([180,0,0]) disp_holder(false, false);
}
translate([50, 0, -6]) rotate([0,90,0]) cylinder(r=0.75, h=112, $fn=64, center =true);