pcb_outline = "poly_kb_wave_right_case-Edge_CutsMod.svg";
drill_holes = "poly_kb_wave_right_case-B_Cu.svg";
led_holes = "poly_kb_wave_right_case-LED.svg";
switch_holes = "poly_kb_wave_right_case-SWITCH.svg";
usb_port_holes = "poly_kb_wave_right_case-USB.svg";


case_height = 17;
case_wall_thickness = 2;
case_bottom_thickness = 1.4;
pcb_edge_height = 9.5;
pcb_edge_width= 2;
stand_off_extra_radius = 2;

text_font = "Arial:style=Bold Italic";
text_size = 12;
text_height = 0.2;
revision = "r1";

module tentingHole() {
    cylinder(h =10, r1 = 2.3, r2 = 2.5, center = false, $fn = 32);
    cylinder(h =1, r1 = 3.5, r2 = 3.5, center = false, $fn = 32);
}

//with camfer
difference() {
    union() {
        //basic case
        difference() {
            linear_extrude(height = case_height, scale=1)
                offset(r=case_wall_thickness, $fn=50)
                    import(file = pcb_outline, dpi = 300);
            
            translate([0,0,case_bottom_thickness])
            linear_extrude(height = case_height, scale=1)
                offset(r=-pcb_edge_width, $fn=50)
                    import(file = pcb_outline, dpi = 300);
            
            translate([0,0,case_bottom_thickness+pcb_edge_height])
            linear_extrude(height = case_height, scale=1)
                import(file = pcb_outline, dpi = 300);
            
        }
        //text
        translate([140,130,case_bottom_thickness])
        linear_extrude(height = text_height) {
                        text("PolyKii", size = text_size, font = text_font, halign = "center", valign = "center", $fn = 16);
        }
        translate([164,122,case_bottom_thickness])
        linear_extrude(height = text_height) {
                        text("by thpoll", size = 4, font = text_font, halign = "center", valign = "center", $fn = 16);
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
    translate([40,40,-9-case_bottom_thickness]) rotate([-19,0,6]) cube([200,50,20]);

    //cut out LEDs
    translate([0,0,pcb_edge_height-1])
        linear_extrude(height = 1.5, scale=1)
            offset(r=0.8)
                import(file = led_holes, dpi = 300);
    
    //cut out Switches
    translate([0,0,pcb_edge_height-2.6])
        linear_extrude(height = 4, scale=1)
            offset(r=2)
                import(file = switch_holes, dpi = 300);
    
    //cut out USB
    translate([0,0,pcb_edge_height-2])
        linear_extrude(height = 3.5, scale=1)
            import(file = usb_port_holes, dpi = 300);
    
    translate([50,90,6]) rotate([90,0,110]) tentingHole();
    translate([90,181.5,6]) rotate([90,0,0]) tentingHole();
    translate([210,179,6]) rotate([90,0,0]) tentingHole();
}