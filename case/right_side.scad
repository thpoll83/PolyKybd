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
revision = "r3";
name = "PolyKii";
author = "thpoll";

module tentingHole() {
    cylinder(h =10, r1 = 2.6, r2 = 2.6, center = false, $fn = 32);
    cylinder(h =1, r1 = 4.2, r2 = 4.2, center = false, $fn = 32);
}

module right_case() {
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
                            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
            }
            translate([164,122,case_bottom_thickness])
            linear_extrude(height = text_height) {
                            text(author, size = 4, font = text_font, halign = "center", valign = "center", $fn = 16);
            }
            translate([220,100,case_bottom_thickness])
            linear_extrude(height = text_height) {
                            text(revision, size = 4, font = text_font, halign = "center", valign = "center", $fn = 16);
            }
            //stand offs
            linear_extrude(height = 4, scale=1)
                    offset(r=stand_off_extra_radius+2, $fn=50)
                        import(file = drill_holes, dpi = 300);
            difference() {
                 linear_extrude(height = pcb_edge_height+case_bottom_thickness, scale=1)
                    offset(r=stand_off_extra_radius, $fn=50)
                        import(file = drill_holes, dpi = 300);
                linear_extrude(height = pcb_edge_height+case_bottom_thickness, scale=1)
                    offset(r=-0.25, $fn=50)
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
            translate([70,80,-3.65]) 
                for ( i = [0 : 20] ){
                    rotate([90-19,0,6]) translate([8*i-5.1,0,0]) cylinder(r1=2, r2=2, h=40, $fn=48);
                }
        //}

        //text
        translate([140,130, 0]) rotate([0,180,0])
            linear_extrude(height = text_height) {
                            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
        }
        translate([116,122, 0]) rotate([0,180,0])
            linear_extrude(height = text_height) {
                            text(author, size = 4, font = text_font, halign = "center", valign = "center", $fn = 16);
        }

        //cut out LEDs
        translate([0,0,pcb_edge_height-2])
            linear_extrude(height = 3.5, scale=1)
                offset(r=0.65)
                    import(file = led_holes, dpi = 300);
        
        //cut out Switches
        translate([0,0,pcb_edge_height-2.4])
            linear_extrude(height = 4, scale=1)
                offset(r=2.5)
                    import(file = switch_holes, dpi = 300);
        
        //cut out USB
        translate([0,0,pcb_edge_height-2])
            linear_extrude(height = 3.5, scale=1)
                import(file = usb_port_holes, dpi = 300);
        
        translate([50,90,6]) rotate([90,0,110]) tentingHole();
        translate([90,181.5,6]) rotate([90,0,0]) tentingHole();
        translate([210,179,6]) rotate([90,0,0]) tentingHole();
        
        //debug ports - remove if not needed
        translate([20,0,-5]) linear_extrude(height = 30, scale=1)
            offset(r=2, $fn=50) import(file = debug_ports, dpi = 300);
    }
}

//spacer
module right_spacer() {
    spacer_height = 3;
    spacher_thickness =3;
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
                translate([49.5+92+2*19.05*i,0,0]) cube([spacher_thickness,200,spacer_height]);
            }
            translate([49.5+53,95,0]) cube([spacher_thickness,200,spacer_height]);
            translate([49.5+63.41,36,0]) rotate([0,0,10]) cube([spacher_thickness,60,spacer_height]);
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
right_case();