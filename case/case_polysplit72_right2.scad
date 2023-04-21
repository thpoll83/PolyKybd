pcb_outline = "poly_kb_wave_right2-OUTLINE.svg";
drill_holes = "poly_kb_wave_right2-SCREW.svg";
standoffs_pos = "poly_kb_wave_right2-STANDOFF.svg";
led_holes = "poly_kb_wave_right2-LED.svg";
switch_holes = "poly_kb_wave_right2-SW.svg";
usb_port_holes = "poly_kb_wave_right2-USB.svg";
usb_clearance = "poly_kb_wave_right2-USB-extra.svg";
wedge_shape = "poly_kb_wave_right2-WD.svg";

case_height = 17;
case_wall_thickness = 1.5;
case_bottom_thickness = 1.4;
pcb_clearance = 0.25;
pcb_edge_height = 9.5;
pcb_edge_width= 2.1;
stand_off_extra_radius = 2.3;

text_font = "Arial:style=Bold Italic";
text_size = 12;
text_height = 0.2;
revision = "r7";
name = "PolyKybd";
model_name = "Split72";


module standoffs(file) {
    linear_extrude(height = 4, scale=1)
        offset(r=stand_off_extra_radius+2, $fn=50)
            import(file = file, dpi = 300);
    linear_extrude(height = 6, scale=1)
        offset(r=stand_off_extra_radius+1, $fn=50)
            import(file = file, dpi = 300);
    difference() {
         linear_extrude(height = pcb_edge_height+case_bottom_thickness, scale=1)
            offset(r=stand_off_extra_radius, $fn=50)
                import(file = file, dpi = 300);
        
        //actual holes
        linear_extrude(height = pcb_edge_height+case_bottom_thickness, scale=1)
            offset(r=-0.225, $fn=50)
                import(file = file, dpi = 300);
        translate([0,0,10.5])
            linear_extrude(height = 1, scale=1)
                import(file = file, dpi = 300);
    }
}

module pcb_standoffs(file) {
    linear_extrude(height = 4, scale=1)
        offset(r=stand_off_extra_radius+2, $fn=50)
            import(file = file, dpi = 300);
    linear_extrude(height = 6, scale=1)
        offset(r=stand_off_extra_radius+1, $fn=50)
            import(file = file, dpi = 300);
    linear_extrude(height = pcb_edge_height+case_bottom_thickness, scale=1)
            offset(r=stand_off_extra_radius-0.6, $fn=50)
                import(file = file, dpi = 300);
    linear_extrude(height = pcb_edge_height+case_bottom_thickness+1.5, scale=1)
            offset(r=-0.5, $fn=50)
                import(file = file, dpi = 300);
}

module tentingHole() {
    difference() { 
        cylinder(h =10, r1 = 2.98, r2 = 2.98, center = false, $fn = 64);
        union() {
            cylinder(h =10, r1 = 2.5, r2 = 2.5, center = false, $fn = 64);
            cube([0.5,10,10], true);
            cube([10,0.5,10], true);
        }
    }
    translate([0,0,2]) cylinder(h = 3, r1 = 2.98, r2 = 2.98, center = false, $fn = 64);
    cylinder(h =10, r1 = 0.25, r2 = 0.25, center = false, $fn = 64);
    cylinder(h =1, r1 = 4.8, r2 = 4.85, center = false, $fn = 64);
}

module tentingHoles() {
    translate([0,0,6]) rotate([90,0,110]) tentingHole();
    translate([40,91.5,6]) rotate([90,0,0]) tentingHole();
    translate([160,89,6]) rotate([90,0,0]) tentingHole();
}


module branding(mirror_text) {
    if(mirror_text) {
        translate([92,85,0])
        mirror(v=[1,0,0]) linear_extrude(height = text_height) {
            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([56,77,0])
        mirror(v=[1,0,0]) linear_extrude(height = text_height) {
            text(model_name, size = 5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
    } else {
        translate([92,85,0])
        linear_extrude(height = text_height) {
            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([128,77,0])
        linear_extrude(height = text_height) {
            text(model_name, size = 5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
    }

}

module right_side_modular(mirror_text, fdm_print) {
    //with camfer
    difference() {
        union() {
            //basic case
            difference() {
                //case
                linear_extrude(height = case_height, scale=1)
                    offset(r=case_wall_thickness+pcb_clearance, $fn=128)
                        import(file = pcb_outline, dpi = 300);
                //space under pcb
                translate([0,0,case_bottom_thickness])
                linear_extrude(height = case_height, scale=1)
                    offset(r=-pcb_edge_width+pcb_clearance, $fn=128)
                        import(file = pcb_outline, dpi = 300);
                //pcb and above
                translate([0,0,case_bottom_thickness+pcb_edge_height])
                linear_extrude(height = case_height, scale=1)
                    offset(r=pcb_clearance, $fn=128)
                        import(file = pcb_outline, dpi = 300);
                
            }
            
            //branding inside
            translate([0, 0, case_bottom_thickness]) branding(mirror_text);

            //revision mark
            if(mirror_text) {
                translate([220-48,55,case_bottom_thickness])
                    mirror(v=[1,0,0]) linear_extrude(height = text_height) {
                        text(revision, size = 5, font = text_font, halign = "center", valign = "center", $fn = 16);
                }
            } else {
                translate([220-48,55,case_bottom_thickness])
                    linear_extrude(height = text_height) {
                        text(revision, size = 5, font = text_font, halign = "center", valign = "center", $fn = 16);
                }
            }
        
            //stand offs
            standoffs(drill_holes);
            pcb_standoffs(standoffs_pos);
            
            //wedge part
            intersection() {
                rotate([-19,0,6]) translate([0,0,case_bottom_thickness/2])
                    linear_extrude(height = 10, scale=1)
                        import(file = wedge_shape, dpi = 300);
                
                linear_extrude(height = case_height, scale=1)
                    import(file = pcb_outline, dpi = 300);
            }
        }
        //remove wedge bottom part
        rotate([-19,0,6]) translate([0,0,-case_bottom_thickness/2]) linear_extrude(height = 10, scale=1)                         import(file = wedge_shape, dpi = 300);
    if(fdm_print) {
        translate([70,80,-3.65]) 
            for ( i = [0 : 20] ){
                rotate([90-19,0,6]) translate([8*i-5.1,0,0]) cylinder(r1=2, r2=2, h=40, $fn=48);
            }
        }

        //bottom branding
        translate([92*2, 0, text_height-0.01]) rotate([0,180,0]) branding(mirror_text);
        //text
        /*translate([140,130, text_height-0.01]) rotate([0,180,0])
            linear_extrude(height = text_height) {
                            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([104,122, text_height-0.01]) rotate([0,180,0])
            linear_extrude(height = text_height) {
                            text(model_name, size = 5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }*/

        //cut out LEDs
        translate([0,0,pcb_edge_height-0.8])
            linear_extrude(height = 2.20, scale=1)
                offset(r=0.9)
                    import(file = led_holes, dpi = 300);
        
        //cut out Switches
        translate([0,0,pcb_edge_height-1])
            linear_extrude(height = 3, scale=1)
                offset(r=2.5)
                    import(file = switch_holes, dpi = 300);
        
        //cut out USB
        translate([0,0,pcb_edge_height-2.2])
            linear_extrude(height = 4, scale=1)
                offset(r=+0.4, $fn=50)
                    import(file = usb_port_holes, dpi = 300);
        
        translate([0,0,case_bottom_thickness+pcb_edge_height-5])
            linear_extrude(height = 10, scale=1)
                import(file = usb_clearance, dpi = 300);
        
        //tenting holes
        translate([2.4,45.3,0]) tentingHoles();
        
        //bottom mount points
        translate([0,0,-0.01]) linear_extrude(height = 5, scale=1)
            offset(r=+1.48, $fn=50)
                import(file = drill_holes, dpi = 300);
        translate([0,0,-0.01])linear_extrude(height = 5, scale=1)
            offset(r=+1.48, $fn=50)
                import(file = standoffs_pos, dpi = 300);
        
        //check hole profile:
        //cube([120,120,100], center = true);
    }
}

module left_case() {
    mirror(v=[1,0,0]) right_side_modular(true, false);
}

module right_case() {
    right_side_modular(false, false);
}

//spacer
module right_spacer() {
    spacer_height = 3.6;
    spacher_thickness = 2.5;
    shrink_radius = 0.25;//0.75;
    translate([0,0,20])
    difference() {
        union() {
            difference() {
                linear_extrude(height = spacer_height, scale=1)
                            offset(r=-shrink_radius, $fn=50)
                                import(file = pcb_outline, dpi = 300);
                translate([0,0,-1])
                linear_extrude(height = spacer_height+2, scale=1)
                            offset(r=-spacher_thickness-shrink_radius, $fn=50)
                                import(file = pcb_outline, dpi = 300);
            }
            for ( i = [0 : 1] ){
                translate([47.5+92-48+2*19.05*i,-45,0]) cube([spacher_thickness,200,spacer_height]);
            }
            translate([53,100.5-45,0]) cube([spacher_thickness,100,spacer_height]);
            translate([1.5+63.41,36-48,0]) rotate([0,0,10]) cube([spacher_thickness,68.6,spacer_height]);
        }
        
        translate([0,0,-1])
        difference() {
            linear_extrude(height = spacer_height+2, scale=1)
                    offset(r=120)
                        import(file = pcb_outline, dpi = 300);
            linear_extrude(height = spacer_height+2, scale=1)
                    offset(r=-shrink_radius, $fn=50)
                        import(file = pcb_outline, dpi = 300);
        }
    }
}

//right_spacer();
translate([5,0,0]) right_case();
translate([-5,0,0]) left_case();


//translate([5,0,0]) right_spacer();