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

// one-piece LED diffuser frame — provides diffuser_frame_left_clearance(),
// which right_spacer() subtracts so its ribs are notched where the web crosses
use <../diffuser/diffuser_frame_left.scad>

case_height = 17.5;
case_wall_thickness = 1.5;
case_bottom_thickness = 2;
pcb_clearance = 0.15;
pcb_edge_height = 9.5;
pcb_edge_width = 1.4;
stand_off_extra_radius = 2.3;

// --- LED window inserts (EMC/ESD) -------------------------------------------
// The three status LEDs (D1, D5, D6 - all 0805 on the PCB underside) shine out
// through slots in the wall. EMC report EMC-700 left +-8 kV ESD air discharge at
// these openings NOT RATED, so each slot takes a bonded transparent insert and
// the opening stops existing on a shipped unit.
//
// The insert is a top hat fitted from OUTSIDE: a flange sitting flush in a local
// pocket (the wall is thinned there to make room), and a boss filling the
// remaining wall thickness. Pressure from outside seats it against the pocket
// floor rather than pushing it through.
//
// The case pocket and the insert are generated from the SAME modules below, so
// they cannot drift apart. `led_inserts.scad` builds the printable parts.
led_insert = true;         // cut the pocket; set false for the pre-insert case
led_slot_r = 0.9;          // the LED SVG holds zero-width lines; this makes the slot
led_pocket_depth = 1.0;    // how much thinner the wall gets, i.e. flange thickness
led_pocket_overlap = 3.5;  // in plan. >= 3.1 so D5 and D6 flanges merge into ONE part
led_pocket_down = 2.0;     // and below it
led_insert_gap = 0.10;     // bond gap, everywhere except the visible outer face

text_font = "Arial:style=Bold Italic";
text_size = 12;
text_height = 0.35;
revision = "r1.7";
spacer_revision = "r1.1";
name = "PolyKybd";
model_name = "Split72";

module standoffs(file)
{
    linear_extrude(height = 4, scale = 1) offset(r = stand_off_extra_radius + 2, $fn = 50)
        import(file = file, dpi = 300);

    linear_extrude(height = 7, scale = 1) offset(r = stand_off_extra_radius + 1.2, $fn = 50)
        import(file = file, dpi = 300);
    difference()
    {
        linear_extrude(height = pcb_edge_height + case_bottom_thickness, scale = 1)
            offset(r = stand_off_extra_radius + 0.5, $fn = 50) import(file = file, dpi = 300);

        // actual holes
        linear_extrude(height = pcb_edge_height + case_bottom_thickness, scale = 1) offset(r = 0.5, $fn = 50)
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
    difference()
    {
        cylinder(h = 10, r1 = 2.98, r2 = 2.98, center = false, $fn = 64);
        union()
        {
            cylinder(h = 10, r1 = 2.5, r2 = 2.5, center = false, $fn = 64);
            cube([ 0.5, 10, 10 ], true);
            cube([ 10, 0.5, 10 ], true);
        }
    }
    translate([ 0, 0, 2 ]) cylinder(h = 3, r1 = 2.98, r2 = 2.98, center = false, $fn = 64);
    cylinder(h = 10, r1 = 0.5, r2 = 0.25, center = false, $fn = 64);
    cylinder(h = 1, r1 = 4.8, r2 = 4.85, center = false, $fn = 64);
}

module tentingHoles()
{
    translate([ 0, 0, 6 ]) rotate([ 90, 0, 110 ]) tentingHole();
    translate([ 40, 91.5, 6 ]) rotate([ 90, 0, 0 ]) tentingHole();
    translate([ 160, 89, 6 ]) rotate([ 90, 0, 0 ]) tentingHole();
    
    translate([17,83.5,0]) cylinder(r=3.25, h=0.65, center = false, $fn = 64);
    translate([167,80,0]) cylinder(r=3.25, h=0.65, center = false, $fn = 64);
    translate([175.5,7,0]) cylinder(r=3.25, h=0.65, center = false, $fn = 64);
    translate([11,-10,0]) cylinder(r=3.25, h=0.65, center = false, $fn = 64);
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
// --- LED window / insert geometry --------------------------------------------
// Everything derives from the same SVG and the same parameters, so the pocket in
// the case and the insert that fills it are two views of one definition. `g` is
// the bond gap: 0 builds the cut, led_insert_gap builds the part that fits it.

// z range of the slot through the wall (unchanged from the original cut)
function led_window_z0() = pcb_edge_height - 0.1;
function led_window_h() = 2.20;
// The pocket must not reach above the PCB underside: the wall is only
// case_wall_thickness there, and a pocket would leave it too thin to print.
function led_pocket_z1() = case_bottom_thickness + pcb_edge_height;
function led_pocket_z0() = led_window_z0() - led_pocket_down;

// The band of wall between the outer face and `d` inboard of it, full height.
module led_wall_band(d, g = 0)
{
    linear_extrude(height = case_height * 3, center = true) difference()
    {
        offset(r = case_wall_thickness + pcb_clearance, $fn = 128) import(file = pcb_outline, dpi = 300);
        offset(r = case_wall_thickness + pcb_clearance - d + g, $fn = 128)
            import(file = pcb_outline, dpi = 300);
    }
}

// The slot itself, through the whole wall.
module led_window_cut(g = 0)
{
    translate([ 0, 0, led_window_z0() + g ])
        linear_extrude(height = led_window_h() - 2 * g, scale = 1)
            offset(r = led_slot_r - g, $fn = 64) import(file = led_holes, dpi = 300);
}

// The local thinning of the wall that makes room for the flange.
module led_pocket_cut(g = 0)
{
    intersection()
    {
        led_wall_band(led_pocket_depth, g);
        translate([ 0, 0, led_pocket_z0() + g ])
            linear_extrude(height = led_pocket_z1() - led_pocket_z0() - 2 * g, scale = 1)
                offset(r = led_slot_r + led_pocket_overlap - g, $fn = 64)
                    import(file = led_holes, dpi = 300);
    }
}

// Both cuts together - what the case loses, and (with g) what the insert is.
module led_insert_solid(g = 0)
{
    union()
    {
        led_pocket_cut(g);
        intersection()
        {
            // the boss stops at the wall's inner face so it cannot foul the PCB
            led_wall_band(case_wall_thickness + pcb_clearance + pcb_edge_width, 0);
            led_window_cut(g);
        }
    }
}

// D5 and D6 sit 7.95 mm apart on one wall; D1 is round the corner on the next.
// So there are two parts per half, four per keyboard - not one, and not three.
//
// !! OpenSCAD's SVG import FLIPS Y. A coordinate read off the .svg or the KiCad
// board is NOT an OpenSCAD coordinate: openscad_y = led_svg_h - svg_y, x is
// unchanged. Verified by measuring the exported slot bbox (slots at svg y 41.2
// and 49.2 come out at y 97.89 and 89.89). led_region() does the conversion so
// the regions below can be written in the same coordinates as the drawing.
led_svg_h = 139.0904;  // height= of the *-LED.svg / *-OUTLINE.svg page

function led_y(svg_y) = led_svg_h - svg_y;

module led_region(x0, svg_y0, x1, svg_y1)
{
    translate([ x0, led_y(svg_y1), 0 ]) cube([ x1 - x0, svg_y1 - svg_y0, case_height * 3 ]);
}

// These boxes only pick which slots go in which part. They are regions, not
// dimensions - generous, and they do not need to track the SVG.
module led_insert_pair(g = led_insert_gap)   // D6 (svg y 41.2) + D5 (svg y 49.2)
{
    intersection() { led_insert_solid(g); led_region(-10, 36, 10, 55); }
}
module led_insert_single(g = led_insert_gap) // D1 (svg x 12.8)
{
    intersection() { led_insert_solid(g); led_region(4, -8, 22, 16); }
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
                    text(revision, size = 3, font = text_font, halign = "center", valign = "center", $fn = 16);
                }
            }
            else
            {
                translate([ 220 - 48, 55, case_bottom_thickness ]) linear_extrude(height = text_height)
                {
                    text(revision, size = 3, font = text_font, halign = "center", valign = "center", $fn = 16);
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
                cylinder(r = 0.9, h = 1, $fn = 32);
            }
            minkowski()
            {
                rotate([ 10, 0, 6 ]) translate([ 141, 91, -19 ]) cube([ 23, 24, 3.5 ]);
                cylinder(r = 0.9, h = 1, $fn = 32);
            }
        }
        //additional curb to grad legs
        rotate([ 10-3, 0, 6 ]) translate([ 16+23/2, 91, -20.5 ]) rotate([90,0,0])
        cylinder(h=30,r=10, center=true, $fn=128);
        rotate([ 10-3, 0, 6 ]) translate([ 141+23/2, 91, -20.5 ]) rotate([90,0,0])
        cylinder(h=30,r=10, center=true, $fn=128);
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

        // cut out LEDs (and, with led_insert, the pocket the insert's flange sits in)
        led_window_cut();
        if (led_insert) led_pocket_cut();

        // cut out switch
        translate([ 0, 0, pcb_edge_height - 0.4 ]) linear_extrude(height = 3, scale = 1) offset(r = 2.5)
            import(file = switch_holes, dpi = 300);
    

        // cut out USB
        translate([ 0, 0, pcb_edge_height - 1.6 ]) linear_extrude(height = 4, scale = 1) offset(r = +0.4, $fn = 50)
            import(file = usb_port_holes, dpi = 300);

        translate([ 0, 0, case_bottom_thickness + pcb_edge_height - 4.5 ]) linear_extrude(height = 9, scale = 1)
            offset(r = 0.7, $fn = 50)
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
            rotate([ 15, 0, 6 ]) translate([ 15.25, 112.5, -27.75 ]) rotate([ 0, 90, 0 ])
                {
                    cylinder(r = 1.5, h = 25, $fn = 48);
                    //anchors
                    rotate([0,90,0]) translate([-1,0,0]) cylinder(r=0.5,h=4,$fn=24);
                    rotate([0,90,0]) translate([-25+1,0,0]) cylinder(r=0.5,h=4,$fn=24);
    
                    rotate([0,90,-90]) translate([-1,0,0]) cylinder(r=0.5,h=4,$fn=24);
                    rotate([0,90,-90]) translate([-25+1,0,0]) cylinder(r=0.5,h=4,$fn=24);
                }
            rotate([ 15, 0, 6 ]) translate([ 15.5, 105, -26.7 ]) rotate([ 0, 90, 0 ])
                cylinder(r = 0.6, h = 24.5, $fn = 48);
            
            rotate([ 15, 0, 6 ]) translate([ 140.25, 112.5, -27.75 ]) rotate([ 0, 90, 0 ])
                {
                    cylinder(r = 1.5, h = 25, $fn = 48);
                    //anchors
                    rotate([0,90,0]) translate([-1,0,0]) cylinder(r=0.5,h=4,$fn=24);
                    rotate([0,90,0]) translate([-25+1,0,0]) cylinder(r=0.5,h=4,$fn=24);
    
                    rotate([0,90,-90]) translate([-1,0,0]) cylinder(r=0.5,h=4,$fn=24);
                                    rotate([0,90,-90]) translate([-25+1,0,0]) cylinder(r=0.5,h=4,$fn=24);
                }
            rotate([ 15, 0, 6 ]) translate([ 140.5, 105, -26.7 ]) rotate([ 0, 90, 0 ])
                cylinder(r = 0.6, h = 24.5, $fn = 48);
        }

        translate([ 0, 0, -20 ]) cube([ 300, 300, 20 ]);

        //cube([300,127,60.5]);
        nuts_inserts(nuts_ins, nuts);
    }
}

module left_case()
{
    union()
    {
        mirror(v = [ 1, 0, 0 ])
        {
            // right_side_shrink_protection();
            right_side_modular(true, false, false, true);
        }
    }
}

module right_case()
{
    union()
    {
        // right_side_shrink_protection();
        right_side_modular(false, false, false, true);
    }
}

// spacer
//
// r1.1 (2026-07-31): notched for the one-piece LED diffuser frame
//     (parts/diffuser_frame_{left,right}.scad), and given an engraved revision.
//     The spacer carried no revision before this, so the shipped part up to now
//     is r1.0 and everything here is a single step to r1.1.
//
//     The frame's connecting web hangs 1.0 mm below the plate, i.e. in the top
//     1 mm of this spacer, and crossed the four inner ribs in 9 places (223
//     mm^3 of interference, measured).  Rather than deleting the ribs — which
//     are what stops a 182 x 129 mm ring from folding up during assembly — the
//     frame's own diffuser_frame_left_clearance() is subtracted, so each rib is
//     notched only where the web passes and keeps full height elsewhere.
//
//     The notch is 1.0 mm wider than the web sideways but only 0.3 mm deeper.
//     The two are SEPARATE parameters and must stay that way: depth has to be
//     small or the ribs get cut clean through over their whole height, while
//     width has to be generous or a rib the notch only partly overlaps survives
//     as a fin.  At 0.3 mm the rib at x=53 was left as a 50.5 mm run of 0.28 mm
//     wall; at 1.0 mm the notch spans 52.57..56.57, fully covering that rib's
//     53.00..54.80, so it is cleanly cut where the rail runs and keeps its
//     solid ends.  The same widening clears two ~3 mm 0.06 mm slivers off the
//     ribs at x=91.5 and x=129.6.
//
//     The notch is cut into BOTH faces with the same pattern.  This part is
//     otherwise a plain prism, which is why ONE printed spacer serves both
//     halves: flipping it over is the same as mirroring it, and the two plate
//     halves are exact mirror images.  Notching only the top would have put the
//     notch underneath when flipped and broken that.
//
//     The revision is ENGRAVED into the inner wall face rather than raised off
//     it: a sunk label adds no fragile protruding feature and cannot foul
//     anything during assembly.  It is on a vertical face, so it is invisible
//     from a top view — look at the inner side of the bottom wall.
//
//     spacer_height stays 3.8 mm: the plate top must sit 5.0 mm above the PCB
//     (3.8 + 1.2 mm plate) for MX plate-mount switches, and the web needs only
//     1.0 mm of the 3.8 mm gap, so there is nothing to gain by raising it.
//     spacer_thickness stays 1.8 mm — the current spacer is confirmed working
//     on hardware and the web comes no closer than 6.14 mm to the outline, so
//     there is nothing here that needs changing either.
//
// notch_diffuser_frame = false gives back the ORIGINAL part, unchanged: no
// notch on either face and no engraved revision, for builds with no frame.
module right_spacer(notch_diffuser_frame = true)
{
    spacer_height = 3.8;
    spacer_thickness = 1.8;
    shrink_radius = 0.25; // 0.75;

    // plate KiCad coords -> this file's coords (fitted against the plate
    // outline: mean nearest-neighbour distance 0.000 mm)
    frame_xy = [ 92.19, 71.79 ];

    // 1.0 mm sideways so a rib the notch only partly overlaps is removed
    // instead of surviving as a fin; 0.3 mm deep so ribs keep their height
    notch_lat  = 1.0;
    notch_deep = 0.3;

    // Revision, embossed standing on the INNER face of the wall so it neither
    // touches the top/bottom faces (which must stay flat and symmetric — the
    // part is flipped over to serve the other half) nor the diffuser frame,
    // whose nearest stem edge is 6.14 mm inside the outline against this
    // text's 2.45 mm.  Placed on the longest straight run of the outline
    // (69.3 mm, 5 deg, inward normal (-0.09, +1.00), midpoint (96.7, 22.3)),
    // offset inward by shrink_radius + spacer_thickness to land on the wall.
    // rev_along slides the label along that edge into the clear 36.3 mm
    // stretch between the ribs at x=91.5 and x=129.6 — centred on the edge
    // midpoint it ran straight through the first of them.
    // The label is SUBTRACTED, so the anchor sits rev_depth back from the inner
    // face and the extrusion runs inward through it: that carves a rev_depth
    // pocket, and rev_over carries the cut past the face so it breaks through
    // cleanly instead of leaving a zero-thickness skin.
    rev_edge_ang = 5.0;
    rev_along    = 14.9;
    rev_depth    = 0.5;
    rev_over     = 0.3;
    rev_inset    = shrink_radius + spacer_thickness - rev_depth;
    rev_face     = [ 96.7 + cos(rev_edge_ang) * rev_along - 0.09 * rev_inset,
                     22.3 + sin(rev_edge_ang) * rev_along + 1.00 * rev_inset ];

    difference()
    {
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

    if (notch_diffuser_frame)
    {
        // top face
        translate([ frame_xy[0], frame_xy[1], 20 + spacer_height ])
            diffuser_frame_left_clearance(notch_lat, notch_deep);
        // bottom face, same pattern, so the part stays symmetric top-to-bottom
        translate([ frame_xy[0], frame_xy[1], 20 ]) mirror(v = [ 0, 0, 1 ])
            diffuser_frame_left_clearance(notch_lat, notch_deep);
    }

    // Revision, engraved into the inner wall face.  Gated on the same flag as
    // the notch: the revision identifies THIS design, so notch_diffuser_frame
    // = false has to give back the original part with nothing added or removed.
    if (notch_diffuser_frame)
        translate([ rev_face[0], rev_face[1], 20 + spacer_height / 2 ])
            rotate([ 0, 0, rev_edge_ang + 180 ]) rotate([ 90, 0, 0 ])
                linear_extrude(height = rev_depth + rev_over)
                    text(str("SPACER ", spacer_revision), size = 2.8,
                         font = text_font, halign = "center",
                         valign = "center", $fn = 32);
    }
}

//translate([5,0,0])  right_spacer();
translate([5,0,0]) right_case();
//translate([ -5, 0, 0 ]) left_case();
// n copies on one sprue, so a print service that bills per repeated part sees a
// single piece — the same reason the diffusers became one frame.  1.5 mm rods:
// two vertical posts, plus a short pin tying every copy to each post.  Snip the
// pins and clean the stubs after printing.
//
// The z figures have to track right_spacer(): it builds at z = 20 and is
// spacer_height tall.  They are repeated here because those are locals of that
// module and cannot be read from outside.
spacer_stack_pitch = 5;      // 3.8 mm part + 1.2 mm gap

module spacers_stacked(n = 4)
{
    part_h = 3.8;            // = spacer_height in right_spacer()
    z0     = 20;             // = the translate inside right_spacer()
    span   = (n - 1) * spacer_stack_pitch + part_h;

    for (s = [0:n - 1])
    {
        translate([ 0, 0, s * spacer_stack_pitch ]) right_spacer();

        // pin each copy to both posts, at its mid-height
        for (p = [[ 20, 15 ], [ 180, 125 ]])
            translate([ p[0], p[1], z0 + part_h / 2 + s * spacer_stack_pitch ])
                rotate([ 0, 90, 0 ]) cylinder(h = 5, r = 0.75, center = true, $fn = 32);
    }

    // the posts, spanning the whole stack
    for (p = [[ 22, 15 ], [ 178, 125 ]])
        translate([ p[0], p[1], z0 + span / 2 ])
            cylinder(h = span, r = 0.75, center = true, $fn = 32);
}

module spacers_4x() { spacers_stacked(4); }

//translate([5,0,0]) right_spacer();
//spacers_4x();