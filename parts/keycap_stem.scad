
revision = "v3";
text_font = "Liberation Mono:style=Bold";
text_size = 3;
text_height = 0.3;

surface_offset = 0.001;
stem_x = 15.5;
stem_y = 15.475;
stem_height = 5.65;
stem_top_bottom_ratio = 0.87;

inside_x = 13.3;
inside_y = 13.3;
inside_hight = 3;

mx_cylinder = 5.5;
mx_cross = 4.35;
mx_cross_width = 1.4;
mx_cross_fillet = 0.3;

disp_x = 12.2;
disp_y = 12.1;
disp_height = 1.1;
disp_y_center_offset = 1.345;
cable_stem_x = 9.0;
cable_stem_y = 2.12;
cable_thickness = 0.5;

module sector(radius, angles, fn = 24) {
    r = radius / cos(180 / fn);
    step = -360 / fn;

    points = concat([[0, 0]],
        [for(a = [angles[0] : step : angles[1] - 360]) 
            [r * cos(a), r * sin(a)]
        ],
        [[r * cos(angles[1]), r * sin(angles[1])]]
    );

    difference() {
        circle(radius, $fn = fn);
        polygon(points);
    }
}

module arc(radius, angles, width = 1, fn = 50) {
    difference() {
        sector(radius + width, angles, fn);
        sector(radius, angles, fn);
    }
} 


module display() {
    color([0.1,0.1,0.1,0.95]) translate([0,disp_y_center_offset-0.4,stem_height-disp_height+surface_offset])
                    linear_extrude(height = disp_height-0.2, scale = 1)
                        square([disp_x, disp_y-1], center = true);
    
    color([0,0,0]) translate([0,disp_y_center_offset+0.6,stem_height-0.2+surface_offset])
                    linear_extrude(height = 0.05, scale = 1)
                        square([10.2, 6.2], center = true);
}
module cable() {
        color([1,0.5,0.3]) union() {translate([-4,-disp_y/2+1.5,stem_height-2.5]) rotate([180,-90,0]) linear_extrude(8) {
            arc(2, [0,90], 0.05);
            translate([-5,2,0]) square([10, 0.05], center = true);
        }
    }
}
module mx_stem(u_size, angle = 0, extra_len=0, txt=revision) {
    difference() {
        union() {
            translate([0,0,extra_len]) rotate([angle,0,0]) difference() {
                //hollow keycap
                union() {
                    translate([(u_size-1)*2*5,0,0]) 
                        linear_extrude(height = stem_height, scale = stem_top_bottom_ratio)
                            square([stem_x, stem_y], center = true);              
                    translate([-(u_size-1)*2*5,0,0]) 
                        linear_extrude(height = stem_height, scale = stem_top_bottom_ratio)
                            square([stem_x, stem_y], center = true);
                }
                union() {
                    translate([(u_size-1)*2*5,0,-surface_offset])
                        linear_extrude(height = inside_hight, scale = stem_top_bottom_ratio)
                            square([inside_x, inside_y], center = true);
                    translate([-(u_size-1)*2*5,0,-surface_offset])
                        linear_extrude(height = inside_hight, scale = stem_top_bottom_ratio)
                            square([inside_x, inside_y], center = true);
                }
                //display cut-out
                translate([0,disp_y_center_offset,stem_height-disp_height+surface_offset])
                    linear_extrude(height = disp_height, scale = 1)
                        square([disp_x, disp_y], center = true);
                translate([0,disp_y_center_offset-disp_y/2-cable_stem_y/2+surface_offset,stem_height-disp_height+surface_offset])
                    linear_extrude(height = disp_height, scale = 1)
                        square([cable_stem_x, cable_stem_y], center = true);
                
                //FFC cutout
                translate([0,disp_y_center_offset-disp_y/2-cable_stem_y-cable_thickness/2+surface_offset*2,stem_height+surface_offset]) rotate([0,180,0])
                    linear_extrude(height = stem_height+surface_offset*2, scale = [1,7])
                        square([cable_stem_x, cable_thickness], center = true);
                translate([0,disp_y_center_offset-disp_y/2-cable_stem_y-0.05,stem_height-disp_height+surface_offset*2-1])
                    linear_extrude(height = 1, scale = [1,10])
                        square([cable_stem_x, 0.2], center = true);
                translate([0,-cable_stem_x/2,-surface_offset])
                        linear_extrude(height = inside_hight)
                            square([cable_stem_x, cable_stem_x], center = true);
               
                
                //revision text
                translate([0,disp_y/2-text_size/2,stem_height-disp_height-text_height+surface_offset*2])
                    rotate([0,0,0]) linear_extrude(height = text_height) {
                        text(txt, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
                    }
            }
            //stem
            union() {
                translate([0,0,0]) cylinder(r=mx_cylinder/2,h=stem_height-disp_height-1+extra_len, $fn = 128,center=false);
                translate([0,0,2.5+extra_len]) cylinder(r1=mx_cylinder/2, r2=mx_cylinder/2+1.2,h=1.4, $fn = 128,center=false);
            }
        }
        //cut out cross
        translate([0,0,-surface_offset])
            linear_extrude(height = stem_height*2, scale = 0.97) {
                offset(r = -mx_cross_fillet) {
                    union() {
                        square([mx_cross+mx_cross_fillet, mx_cross_width+mx_cross_fillet], center = true);
                        square([mx_cross_width+mx_cross_fillet, mx_cross+mx_cross_fillet], center = true);
                    }
                }
                
                translate([-mx_cross/3,0,0]) circle(d = (mx_cross_width-mx_cross_fillet)*1.1, $fn=64);
                translate([mx_cross/3,0,0]) circle(d = (mx_cross_width-mx_cross_fillet)*1.1, $fn=64);
                translate([0,-mx_cross/3,0]) circle(d = (mx_cross_width-mx_cross_fillet)*1.1, $fn=64);
                translate([0,mx_cross/3,0]) circle(d = (mx_cross_width-mx_cross_fillet)*1.1, $fn=64);
                
            }
        //camfer at bottom
        translate([0,0,-surface_offset])
            linear_extrude(height = mx_cross_fillet, scale = [mx_cross/(mx_cross+2*mx_cross_fillet)-0.011, mx_cross_width/(mx_cross_width+2*mx_cross_fillet)-0.07])
                square([mx_cross+mx_cross_fillet, mx_cross_width+mx_cross_fillet], center = true);
                translate([0,0,-surface_offset])
        linear_extrude(height = mx_cross_fillet, scale = [mx_cross_width/(mx_cross_width+2*mx_cross_fillet)-0.07,mx_cross/(mx_cross+2*mx_cross_fillet)-0.011])
                square([mx_cross_width+mx_cross_fillet,mx_cross+mx_cross_fillet], center = true);
    }
}

//mx_stem(u_size=1);
/*
display();
cable();
*/

//10p
module ten_connected_pieces_1U(angle = 0, extra_len=0, txt=revision) {
    union() {
        for ( i = [0 : 4] ){
            translate([i*22-5, 0, 6])rotate([-90,180,180]) mx_stem(u_size=1, angle = angle, extra_len=extra_len, txt=txt);
            translate([i*22-5, 0,-7]) rotate([90,0,0]) cylinder(r=0.75,h=6, $fn = 128,center=false);
            translate([i*22-5, 0, -11.9]) rotate([-90,0,180]) mx_stem(u_size=1, angle = angle, extra_len=extra_len, txt=txt);
            translate([i*22-5, 0,1.1]) rotate([90,0,0]) cylinder(r=0.75,h=6, $fn = 128,center=false);
            
            translate([i*22-5,0,1.5]) rotate([0,180,0]) cylinder(r=0.75,h=9, $fn = 128,center=false);
        }
        translate([-5,0,-3]) rotate([0,90,0]) cylinder(r=0.75,h=4.5*22-11, $fn = 128,center=false);
    }
}

module ten_connected_pieces_1U25(angle = 0, extra_len=0, txt=revision) {
    union() {
        for ( i = [0 : 4] ){
            translate([i*22-5, 0, 6])rotate([-90,180,180]) mx_stem(u_size=1.22, angle = angle, extra_len=extra_len, txt=txt);
            translate([i*22-5, 0,-7]) rotate([90,0,0]) cylinder(r=0.75,h=6, $fn = 128,center=false);
            translate([i*22-5, 0, -11.9]) rotate([-90,0,180]) mx_stem(u_size=1.22, angle = angle, extra_len=extra_len, txt=txt);
            translate([i*22-5, 0,1.1]) rotate([90,0,0]) cylinder(r=0.75,h=6, $fn = 128,center=false);
            
            translate([i*22-5,0,1.5]) rotate([0,180,0]) cylinder(r=0.75,h=9, $fn = 128,center=false);
        }
        translate([-5,0,-3]) rotate([0,90,0]) cylinder(r=0.75,h=4.5*22-11, $fn = 128,center=false);
    }
}

module ten_connected_pieces_1U5(angle = 0, extra_len=0, txt=revision) {
    union() {
        for ( i = [0 : 4] ){
            translate([i*27-5, 0, 6])rotate([-90,180,180]) mx_stem(u_size=1.47, angle = angle, extra_len=extra_len, txt=txt);
            translate([i*27-5, 0,-7]) rotate([90,0,0]) cylinder(r=0.75,h=6, $fn = 128,center=false);
            translate([i*27-5, 0, -11.9]) rotate([-90,0,180]) mx_stem(u_size=1.47, angle = angle, extra_len=extra_len, txt=txt);
            translate([i*27-5, 0,1.1]) rotate([90,0,0]) cylinder(r=0.75,h=6, $fn = 128,center=false);
            
            translate([i*27-5, 0,1.5]) rotate([0,180,0]) cylinder(r=0.75,h=9, $fn = 128,center=false);
        }
        translate([-5,0,-3]) rotate([0,90,0]) cylinder(r=0.75,h=4.5*27-11, $fn = 128,center=false);
    }
}

//ten_connected_pieces_1U(angle = -7, extra_len=1.5, txt=str("S ", revision));
ten_connected_pieces_1U25(angle = -7, extra_len=1.5, txt=str("S ", revision));

/*
translate([0,19.25*3,0]) mx_stem(u_size=1, angle = 10, extra_len=3, txt="R5r2");
translate([0,19.25*2,0]) mx_stem(u_size=1, angle = 5, extra_len=0.5, txt="R4r2");
translate([0,19.25,0]) mx_stem(u_size=1, txt="R3r2");
mx_stem(u_size=1, angle = -5, extra_len=0.5, txt="R2r2");
translate([0,-19.25,0]) mx_stem(u_size=1, angle = 5, extra_len=0.5, txt="R1r2");
*/
/*
rotate([0,0,0]){
translate([0,19.25*3,0]) mx_stem(u_size=1, angle = -5, extra_len=0.5, txt="R2r2");
translate([0,19.25*2,0]) mx_stem(u_size=1, angle = -5, extra_len=0.5, txt="R2r2");
translate([0,19.25,0]) mx_stem(u_size=1, angle = -5, extra_len=0.5, txt="R2r2");
mx_stem(u_size=1, angle = -5, extra_len=0.5, txt="R2r2");
translate([0,-19.25,0]) mx_stem(u_size=1, angle = -5, extra_len=0.5, txt="R2r2");
}
*/
/*
translate([0,19.25*3,0]) mx_stem(u_size=1, angle = 0, extra_len=0, txt="R3r3");
translate([0,19.25*2,0]) mx_stem(u_size=1, angle = 0, extra_len=0, txt="R3r3");
translate([0,19.25,0]) mx_stem(u_size=1, angle = 0, extra_len=0, txt="R3r3");
mx_stem(u_size=1, angle = 0, extra_len=0, txt="R3r3");
translate([0,-19.25,0]) mx_stem(u_size=1, angle = 0, extra_len=0, txt="R3r3");
*/
//color([0,0.5,0], 0.4) translate([0,0,-1]) cube([100,100,2], center=true);
