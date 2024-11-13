pcb_outline = "poly_kb_wave_right2-OUTLINE.svg";
drill_holes = "poly_kb_wave_right2-SCREW.svg";
standoffs_pos = "poly_kb_wave_right2-STANDOFF.svg";
led_holes = "poly_kb_wave_right2-LED.svg";
switch_holes = "poly_kb_wave_right2-SW.svg";
usb_port_holes = "poly_kb_wave_right2-USB.svg";
usb_clearance = "poly_kb_wave_right2-USB-extra.svg";
wedge_shape = "poly_kb_wave_right2-WD.svg";
nuts_ins = "poly_kb_wave_right2-NutsInserts.svg";
nuts = "poly_kb_wave_right2-Nuts.svg";
austria = "at.svg";
designed = "diat.svg";
edelweiss = "edelweiss.svg";

case_height = 17.5;
case_wall_thickness = 1.5;
case_bottom_thickness = 2;
pcb_clearance = 0.15;
pcb_edge_height = 9.5;
pcb_edge_width = 1.4;
stand_off_extra_radius = 2.3;

text_font = "Arial:style=Bold Italic";
text_size = 12;
text_height = 0.2;
revision = "";
name = "PolyKybd";
model_name = "Split72";

module standoffs(file)
{
    //bottom support ring
    linear_extrude(height = 4, scale = 1) offset(r = stand_off_extra_radius + 2, $fn = 50)
        import(file = file, dpi = 300);

    //middle support ring
    linear_extrude(height = 7, scale = 1) offset(r = stand_off_extra_radius + 1.2, $fn = 50)
        import(file = file, dpi = 300);
    difference()
    {
        linear_extrude(height = pcb_edge_height + case_bottom_thickness, scale = 1)
            offset(r = stand_off_extra_radius + 0.5, $fn = 50) import(file = file, dpi = 300);

        // actual holes
        linear_extrude(height = pcb_edge_height + case_bottom_thickness, scale = 1) offset(r = -0.5, $fn = 50)
            import(file = file, dpi = 300);
        
        translate([ 0, 0, 10.5 ]) linear_extrude(height = 1, scale = 1) import(file = file, dpi = 300);
    }
}

module nuts_inserts(file1, file2)
{
    color([ 1, 0, 0 ]) translate([ 2.6, 9.25, 8.1 ])
    {
        linear_extrude(height = 2.55, scale = 1)
            offset(r = 0.025, $fn = 50)
                import(file = file1, dpi = 300);
        translate([ 0, 0, -0.4 ])
            linear_extrude(height = 1, scale = 1)
                import(file = file2, dpi = 300);
    }
}

module standoffs_holes(file)
{
    // actual holes
    translate([ 0, 0, pcb_edge_height - 2.2 ]) linear_extrude(height = 2.2, scale = 1) offset(r = -0.225, $fn = 50)
        import(file = file, dpi = 300);
}

module pcb_standoffs(file)
{
    linear_extrude(height = 4, scale = 1) offset(r = stand_off_extra_radius + 2, $fn = 50)
        import(file = file, dpi = 300);
    linear_extrude(height = 7, scale = 1) offset(r = stand_off_extra_radius + 1, $fn = 50)
        import(file = file, dpi = 300);
    linear_extrude(height = pcb_edge_height + case_bottom_thickness, scale = 1)
        offset(r = stand_off_extra_radius - 0.6, $fn = 50) import(file = file, dpi = 300);
    linear_extrude(height = pcb_edge_height + case_bottom_thickness + 1.5, scale = 1) offset(r = -0.7, $fn = 50)
        import(file = file, dpi = 300);
}

module tentingHole()
{
    /*
    difference()
    {
        cylinder(h = 10, r1 = 2.98, r2 = 2.98, center = false, $fn = 64);
        union()
        {
            cylinder(h = 10, r1 = 2.5, r2 = 2.5, center = false, $fn = 64);
            cube([ 0.5, 10, 10 ], true);
            cube([ 10, 0.5, 10 ], true);
        }
    }*/
    //translate([ 0, 0, 2 ]) cylinder(h = 3, r1 = 2.98, r2 = 2.98, center = false, $fn = 64);
    cylinder(h = 10, r1 = 0.5, r2 = 0.25, center = false, $fn = 64);
    //cylinder(h = 1, r1 = 4.8, r2 = 4.85, center = false, $fn = 64);
}

module tentingHoles()
{
    translate([ 0, 0, 6 ]) rotate([ 90, 0, 110 ]) tentingHole();
    translate([ 40, 91.5, 6 ]) rotate([ 90, 0, 0 ]) tentingHole();
    translate([ 160, 89, 6 ]) rotate([ 90, 0, 0 ]) tentingHole();
    
    translate([17,83.5,0]) cylinder(r=3.25, h=0.5, center = false, $fn = 64);
    translate([167,80,0]) cylinder(r=3.25, h=0.5, center = false, $fn = 64);
    translate([175.5,7,0]) cylinder(r=3.25, h=0.5, center = false, $fn = 64);
    translate([11,-10,0]) cylinder(r=3.25, h=0.5, center = false, $fn = 64);
}

module branding(mirror_text)
{
    if (mirror_text)
    {
        translate([ 92, 85, 0 ]) mirror(v = [ 1, 0, 0 ]) linear_extrude(height = text_height)
        {
            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 56, 77, 0 ]) mirror(v = [ 1, 0, 0 ]) linear_extrude(height = text_height)
        {
            text(model_name, size = 5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 178, 89.8, 0 ]) mirror(v = [ 1, 0, 0 ]) linear_extrude(height = text_height)
        {
            text("Limit", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 181, 98, 0 ]) mirror(v = [ 1, 0, 0 ]) linear_extrude(height = text_height)
        {
            text("V", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 171, 127, 0 ]) mirror(v = [ 1, 0, 0 ]) rotate([0,0,90]) linear_extrude(height = text_height)
        {
            text("Power", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 5, 84, 0 ]) mirror(v = [ 1, 0, 0 ]) linear_extrude(height = text_height)
        {
            text("Boot", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 5.5, 91.5, 0 ]) mirror(v = [ 1, 0, 0 ]) linear_extrude(height = text_height)
        {
            text("Reset", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 178, 89.8, 0 ]) 
        {
            linear_extrude(height = text_height, scale = 1) offset(r = 0, $fn = 50)
                import(file = austria, dpi = 300);
        }
    }
    else
    {
        translate([ 92, 85, 0 ]) linear_extrude(height = text_height)
        {
            text(name, size = text_size, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 128, 77, 0 ]) linear_extrude(height = text_height)
        {
            text(model_name, size = 5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 178, 89.8, 0 ]) linear_extrude(height = text_height)
        {
            text("Limit", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 181, 98, 0 ]) linear_extrude(height = text_height)
        {
            text("V", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 171, 127, 0 ]) rotate([0,0,90]) linear_extrude(height = text_height)
        {
            text("Power", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 5, 84, 0 ]) linear_extrude(height = text_height)
        {
            text("Boot", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 5.5, 91.5, 0 ]) linear_extrude(height = text_height)
        {
            text("Reset", size = 2.5, font = text_font, halign = "center", valign = "center", $fn = 50);
        }
        translate([ 88, 189.8, -20 ]) 
        {
             linear_extrude(height = 40, scale = 1)offset(r = 0, $fn = 50) scale([1,1,1]) 
                import(file = austria, dpi = 300);
        }
    }
}

module right_side_shrink_protection()
{
    intersection()
    {
        translate([ 0, 0, case_height - 1.2 ])
        {
            linear_extrude(height = 1.2, scale = 1) offset(r = pcb_clearance, $fn = 128)
                import(file = pcb_outline, dpi = 300);
        }
        /* translate([0,0,case_height-1.2 + 18]) {
             for ( y = [0 : 10] ){
                 for ( x = [0 : 10] ){
                     if(y%2==1) {
                         translate([9+x*18,y*16,0]) cylinder(r = 8.5, h = 3, center = true, $fn=32);
                     }else {
                         translate([x*18,y*16,0]) cylinder(r = 8.5, h = 3, center = true, $fn=32);
                     }
                 }
            }
        }]
        */
        union()
        {
            translate([ 0, 52, case_height - 1.2 ]) cube([ 300, 1.5, 10 ]);
            translate([ 0, 110, case_height - 1.2 ]) cube([ 300, 1.5, 10 ]);

            translate([ 30, 0, case_height - 1.2 ]) cube([ 1.5, 300, 10 ]);
            translate([ 100, 0, case_height - 1.2 ]) cube([ 1.5, 300, 10 ]);
            translate([ 160, 0, case_height - 1.2 ]) cube([ 1.5, 300, 10 ]);
        }
    }
}
module bottom_mp()
{
    translate([ 0, 0, -0.01 ]) linear_extrude(height = 5, scale = 1) offset(r = +1.48, $fn = 50)
        import(file = drill_holes, dpi = 300);
    translate([ 0, 0, -0.01 ]) linear_extrude(height = 5, scale = 1) offset(r = +1.48, $fn = 50)
        import(file = standoffs_pos, dpi = 300);
}

module infill(w, d, h, t)
{
    for (y = [0:10])
    {
        translate([ 0, y * 20, 0 ]) cube([ w, t, h ]);
        translate([ y * 20, 0, 0 ]) cube([ t, d, h ]);
    }
}


// spacer
module inner_walls()
{
    spacer_height = 8;
    spacer_thickness = 1.5;
    shrink_radius = 0.25; // 0.75;
    translate([ 0, 0, 1 ]) difference()
    {
        union()
        {
  
            for (i = [0:1])
            {
                translate([ 47.5 + 92 - 48 + 2 * 19.05 * i, -45, 0 ]) cube([ spacer_thickness, 200, spacer_height ]);
            }
            translate([ 53, 100.5 - 45, 0 ]) cube([ spacer_thickness, 100, spacer_height ]);
            translate([ 1.5 + 63.41, 36 - 48, 0 ]) rotate([ 0, 0, 10 ]) cube([ spacer_thickness, 68.6, spacer_height ]);
        }

        translate([ 0, 0, -1 ]) difference()
        {
            linear_extrude(height = spacer_height + 2, scale = 1) offset(r = 120) import(file = pcb_outline, dpi = 300);
            linear_extrude(height = spacer_height + 2, scale = 1) offset(r = -shrink_radius, $fn = 50)
                import(file = pcb_outline, dpi = 300);
        }
    }
}
module right_side_modular(mirror_text, fdm_print, with_shrink_protection, grid_infill = true)
{

    // with camfer
    difference()
    {
        union()
        {
            // basic case
            difference()
            {
                // case
                linear_extrude(height = case_height, scale = 1)
                    offset(r = case_wall_thickness + pcb_clearance, $fn = 128) import(file = pcb_outline, dpi = 300);
                // space under pcb
                translate([ 0, 0, case_bottom_thickness ]) linear_extrude(height = case_height, scale = 1)
                    offset(r = -pcb_edge_width + pcb_clearance, $fn = 128) import(file = pcb_outline, dpi = 300);
                // pcb and above
                translate([ 0, 0, case_bottom_thickness + pcb_edge_height ])
                    linear_extrude(height = case_height, scale = 1) offset(r = pcb_clearance, $fn = 128)
                        import(file = pcb_outline, dpi = 300);
            }

            // grid 
            if(grid_infill) {
                intersection() {
                    translate([ 0, 0, case_bottom_thickness ]) linear_extrude(height = case_height, scale = 1)
                        offset(r = -pcb_edge_width + pcb_clearance, $fn = 128) import(file = pcb_outline, dpi = 300);
                    translate([ 100, -90, 0 ]) rotate([ 0, 0, 45 ]) infill(300, 300, 2.5, 1);
                }
            }
            
            inner_walls();

            // mark
            if (mirror_text)
            {
                translate([ 220 - 48, 55, case_bottom_thickness ]) mirror(v = [ 1, 0, 0 ])
                    linear_extrude(height = text_height)
                {
                    text(revision, size = 5, font = text_font, halign = "center", valign = "center", $fn = 16);
                }
            }
            else
            {
                translate([ 220 - 48, 55, case_bottom_thickness ]) linear_extrude(height = text_height)
                {
                    text(revision, size = 5, font = text_font, halign = "center", valign = "center", $fn = 16);
                }
            }

            // stand offs
            standoffs(drill_holes);
            pcb_standoffs(standoffs_pos);

            // bottom mount points
            intersection()
            {
                bottom_mp();
                cube([ 300, 40, 50 ]);
            }

            // wedge part
            intersection()
            {
                rotate([ -19, 0, 6 ]) translate([ 0, 0, case_bottom_thickness / 5 * 2 ])
                    linear_extrude(height = 10, scale = 1) import(file = wedge_shape, dpi = 300);

                linear_extrude(height = case_height, scale = 1) import(file = pcb_outline, dpi = 300);
            }

            // flip stand bays
            minkowski()
            {
                rotate([ 10, 0, 6 ]) translate([ 16, 91, -19 ]) cube([ 23, 24, 3.5 ]);
                cylinder(r = 1, h = 1, $fn = 32);
            }
            minkowski()
            {
                rotate([ 10, 0, 6 ]) translate([ 141, 91, -19 ]) cube([ 23, 24, 3.5 ]);
                cylinder(r = 1, h = 1, $fn = 32);
            }
        }
        // remove wedge bottom part
        rotate([ -19, 0, 6 ]) translate([ 0, 0, -case_bottom_thickness / 2 ]) linear_extrude(height = 10, scale = 1)
            import(file = wedge_shape, dpi = 300);
        if (fdm_print)
        {
            translate([ 70, 80, -3.65 ]) for (i = [0:20])
            {
                rotate([ 90 - 19, 0, 6 ]) translate([ 8 * i - 5.1, 0, 0 ]) cylinder(r1 = 2, r2 = 2, h = 40, $fn = 48);
            }
        }

        // bottom branding
        translate([ 92 * 2, 0, text_height - 0.01 ]) rotate([ 0, 180, 0 ]) branding(mirror_text);

        // cut out LEDs
        translate([ 0, 0, pcb_edge_height - 0.1 ]) linear_extrude(height = 2.20, scale = 1) offset(r = 0.9)
            import(file = led_holes, dpi = 300);

        // cut out switch
        translate([ 0, 0, pcb_edge_height - 0.4 ]) linear_extrude(height = 3, scale = 1) offset(r = 2.5)
            import(file = switch_holes, dpi = 300);
    

        // cut out USB
        translate([ 0, 0, pcb_edge_height - 1.6 ]) linear_extrude(height = 4, scale = 1) offset(r = +0.4, $fn = 50)
            import(file = usb_port_holes, dpi = 300);

        translate([ 0, 0, case_bottom_thickness + pcb_edge_height - 5 ]) linear_extrude(height = 10, scale = 1)
            import(file = usb_clearance, dpi = 300);

        // tenting holes
        translate([ 2.4, 45.3, 0 ]) tentingHoles();

        // check hole profile:
        // cube([11,320,100], center = true);

        standoffs_holes(drill_holes);

        // bottom mount points
        intersection()
        {
            bottom_mp();
            translate([ 0, 40, 0 ]) cube([ 300, 200, 50 ]);
        }

        // flip stand bays
        // translate([0,-2,0]) {
        rotate([ 12, 0, 6 ]) translate([ 16, 91, -31.1 + 6.75 ]) cube([ 23, 23, 5 ]);
        rotate([ 12, 0, 6 ]) translate([ 141, 91, -31.1 + 6.75 ]) cube([ 23, 23, 5 ]);

        //axis holder for flip stand bays
        translate([ 0, -2, 0 ])
        {
            rotate([ 15, 0, 6 ]) translate([ 14, 112.5, -27.75 ]) rotate([ 0, 90, 0 ])
                cylinder(r = 1.5, h = 27, $fn = 48);
            rotate([ 15, 0, 6 ]) translate([ 15.5, 105, -26.7 ]) rotate([ 0, 90, 0 ])
                cylinder(r = 0.6, h = 24.5, $fn = 48);
            rotate([ 15, 0, 6 ]) translate([ 139, 112.5, -27.75 ]) rotate([ 0, 90, 0 ])
                cylinder(r = 1.5, h = 27, $fn = 48);
            rotate([ 15, 0, 6 ]) translate([ 140.5, 105, -26.7 ]) rotate([ 0, 90, 0 ])
                cylinder(r = 0.6, h = 24.5, $fn = 48);
        }

        translate([ 0, 0, -20 ]) cube([ 300, 300, 20 ]);

        // cube([100,9.2,20.5]);
        //nuts_inserts(nuts_ins, nuts);
    }
}

module left_case()
{
    union()
    {
        mirror(v = [ 1, 0, 0 ])
        {
            // right_side_shrink_protection();
            right_side_modular(true, false, false, false);
        }
    }
}

module right_case()
{
    union()
    {
        // right_side_shrink_protection();
        right_side_modular(false, false, false, false);
    }
}

// spacer
module right_spacer()
{
    spacer_height = 3.8;
    spacer_thickness = 1.8;
    shrink_radius = 0.25; // 0.75;
    translate([ 0, 0, 20 ]) difference()
    {
        union()
        {
            difference()
            {
                linear_extrude(height = spacer_height, scale = 1) offset(r = -shrink_radius, $fn = 50)
                    import(file = pcb_outline, dpi = 300);
                translate([ 0, 0, -1 ]) linear_extrude(height = spacer_height + 2, scale = 1)
                    offset(r = -spacer_thickness - shrink_radius, $fn = 50) import(file = pcb_outline, dpi = 300);
            }
            for (i = [0:1])
            {
                translate([ 47.5 + 92 - 48 + 2 * 19.05 * i, -45, 0 ]) cube([ spacer_thickness, 200, spacer_height ]);
            }
            translate([ 53, 100.5 - 45, 0 ]) cube([ spacer_thickness, 100, spacer_height ]);
            translate([ 1.5 + 63.41, 36 - 48, 0 ]) rotate([ 0, 0, 10 ]) cube([ spacer_thickness, 68.6, spacer_height ]);
        }

        translate([ 0, 0, -1 ]) difference()
        {
            linear_extrude(height = spacer_height + 2, scale = 1) offset(r = 120) import(file = pcb_outline, dpi = 300);
            linear_extrude(height = spacer_height + 2, scale = 1) offset(r = -shrink_radius, $fn = 50)
                import(file = pcb_outline, dpi = 300);
        }
    }
}

//translate([5,0,0])  right_spacer();
translate([5,0,0]) right_case();
//translate([ -5, 0, 0 ]) left_case();
module spacers_4x() {
for(s = [0:3]) {
    translate([0,0,s*5]) right_spacer();
    translate([20,15,15*1.5+s*5]) rotate([0,90,0]) cylinder(h = 5, r = 0.75, center = true, $fn = 32);
    translate([180,125,15*1.5+s*5]) rotate([0,90,0]) cylinder(h = 5, r = 0.75, center = true, $fn = 32);
}
translate([22,15,15*2]) cylinder(h = 15, r = 0.75, center = true, $fn = 32);
translate([178,125,15*2]) cylinder(h = 15, r = 0.75, center = true, $fn = 32);
}

// translate([5,0,0]) right_spacer();
