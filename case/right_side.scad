pcb_outline = "poly_kb_wave_right_case-Edge_CutsMod.svg";
drill_holes = "poly_kb_wave_right_case-B_Cu.svg";
led_holes = "poly_kb_wave_right_case-LED.svg";
switch_holes = "poly_kb_wave_right_case-SWITCH.svg";
usb_port_holes = "poly_kb_wave_right_case-USB.svg";

debug_ports = "poly_kb_wave_right_debug.svg";


case_height = 17;
case_wall_thickness = 1.5;
case_bottom_thickness = 1.4;
pcb_clearance = 0.5;
pcb_edge_height = 9.5;
pcb_edge_width= 2.1;
stand_off_extra_radius = 2.3;

text_font = "Arial:style=Bold Italic";
text_size = 12;
text_height = 0.2;
revision = "r5";
name = "PolyKybd";
author = "Split";

module tentingHole(extra_space) {
    if(extra_space) {
        cylinder(h =10, r1 = 3, r2 = 3, center = false, $fn = 32);
    } else {
        cylinder(h =10, r1 = 2.85, r2 = 2.85, center = false, $fn = 32);
    }
    cylinder(h =1, r1 = 4.8, r2 = 4.85, center = false, $fn = 32);
}

module right_case(include_debug, fdm_print) {
    //with camfer
    difference() {
        union() {
            //basic case
            difference() {
                //case
                linear_extrude(height = case_height, scale=1)
                    offset(r=case_wall_thickness+pcb_clearance, $fn=50)
                        import(file = pcb_outline, dpi = 300);
                //space under pcb
                translate([0,0,case_bottom_thickness])
                linear_extrude(height = case_height, scale=1)
                    offset(r=-pcb_edge_width+pcb_clearance, $fn=50)
                        import(file = pcb_outline, dpi = 300);
                //pcb and above
                translate([0,0,case_bottom_thickness+pcb_edge_height])
                linear_extrude(height = case_height, scale=1)
                    offset(r=pcb_clearance, $fn=50)
                        import(file = pcb_outline, dpi = 300);
                
            }
            //text
            translate([140,130,case_bottom_thickness])
            linear_extrude(height = text_height) {
                            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 50);
            }
            translate([172,122,case_bottom_thickness])
            linear_extrude(height = text_height) {
                            text(author, size = 5, font = text_font, halign = "center", valign = "center", $fn = 50);
            }
            translate([220,100,case_bottom_thickness])
            linear_extrude(height = text_height) {
                            text(revision, size = 5, font = text_font, halign = "center", valign = "center", $fn = 16);
            }
            //stand offs
            linear_extrude(height = 4, scale=1)
                    offset(r=stand_off_extra_radius+2, $fn=50)
                        import(file = drill_holes, dpi = 300);
            linear_extrude(height = 6, scale=1)
                    offset(r=stand_off_extra_radius+1, $fn=50)
                        import(file = drill_holes, dpi = 300);
            difference() {
                 linear_extrude(height = pcb_edge_height+case_bottom_thickness, scale=1)
                    offset(r=stand_off_extra_radius, $fn=50)
                        import(file = drill_holes, dpi = 300);
                linear_extrude(height = pcb_edge_height+case_bottom_thickness, scale=1)
                        import(file = drill_holes, dpi = 300);
                

            } 
            
            //odd bottom part
            intersection() {
                translate([40,40,-9]) rotate([-19,0,6]) cube([200,50,20]);
                linear_extrude(height = case_height, scale=1)
                    import(file = pcb_outline, dpi = 300);
            }
        }
        //remove odd bottom part
        //difference() {
            translate([40,40,-9-case_bottom_thickness]) rotate([-19,0,6]) cube([200,50,20]);
        if(fdm_print) {
            translate([70,80,-3.65]) 
                for ( i = [0 : 20] ){
                    rotate([90-19,0,6]) translate([8*i-5.1,0,0]) cylinder(r1=2, r2=2, h=40, $fn=48);
                }
            }
        //}

        //text
        translate([140,130, text_height-0.01]) rotate([0,180,0])
            linear_extrude(height = text_height) {
                            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([108,122, text_height-0.01]) rotate([0,180,0])
            linear_extrude(height = text_height) {
                            text(author, size = 5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }

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
                import(file = usb_port_holes, dpi = 300);
        
        translate([50,90,6]) rotate([90,0,110]) tentingHole(fdm_print);
        translate([90,181.5,6]) rotate([90,0,0]) tentingHole(fdm_print);
        translate([210,179,6]) rotate([90,0,0]) tentingHole(fdm_print);
        
        //debug ports - remove if not needed
        if(include_debug) {
            translate([20,0,-5]) linear_extrude(height = 30, scale=1)
            offset(r=2, $fn=50) import(file = debug_ports, dpi = 300);
        }
        translate([0,0,-0.01])linear_extrude(height = 3.9, scale=1)
            offset(r=+1.65, $fn=50)
                import(file = drill_holes, dpi = 300);
    }
}

//spacer
module right_spacer() {
    spacer_height = 3;
    spacher_thickness = 2.5;
    shrink_radius = 0;//0.75;
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
                translate([47.5+92+2*19.05*i,0,0]) cube([spacher_thickness,200,spacer_height]);
            }
            translate([48+53,103.5,0]) cube([spacher_thickness,100,spacer_height]);
            translate([49.5+63.41,36,0]) rotate([0,0,10]) cube([spacher_thickness,68.6,spacer_height]);
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
right_case(false, false);