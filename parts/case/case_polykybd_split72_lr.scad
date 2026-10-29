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
// The insert is a top hat: a boss filling the window flush with the outer face,
// and a flange sitting in a local pocket where the wall is thinned to make room.
// led_fit_from picks which face that pocket is cut into - "inside" by default,
// which leaves the outer surface untouched.
//
// The case pocket and the insert are generated from the SAME modules below, so
// they cannot drift apart. `led_inserts.scad` builds the printable parts.
led_insert = true;         // cut the pocket; set false for the pre-insert case
led_fit_from = "inside";   // which face the flange sits in: "inside" | "outside".
                           // INSIDE leaves the outer surface exactly as it was
                           // designed and tested - the only thing visible is the
                           // window itself, filled flush, with no seam ring round
                           // it and nothing for a blade to engage. The pocket is
                           // cut into the PCB ledge instead, so it must stop short
                           // of the ledge top (led_ledge_keep).
                           // OUTSIDE is kept because it is better against the load
                           // that actually occurs: pressure from outside seats the
                           // flange on the pocket floor instead of pushing the part
                           // into the cavity. Fitted from the inside only the bond
                           // resists that, which is one more reason the bond is not
                           // optional.
led_slot_r = 0.9;          // grows the imported slot. !! The SVG paths are LINES, but
                           // OpenSCAD imports them with a ~1.0 mm stroke, not zero width,
                           // so the window comes out 1.0 + 2*0.9 = 2.8 mm wide, not 1.8.
                           // Measure the import before quoting a window size.
led_pocket_depth = 1.0;    // how much thinner the wall gets, i.e. flange thickness
led_pocket_overlap = 3.5;  // the CASE cavity, in plan. >= 3.1 so the D5 and D6
                           // pockets merge into one recess rather than leaving a
                           // thin rib of ledge between them.
led_flange_overlap = 2.4;  // the PART's flange, in plan. Smaller than the cavity so
                           // that three IDENTICAL parts can be used: D5 and D6 are
                           // only 5.2 mm apart edge to edge, so a flange grown by
                           // led_pocket_overlap would have its neighbour's inside it.
                           // 2.4 leaves 0.4 mm between the two flanges, and the rest
                           // of the merged pocket is simply more bond gap.
led_pocket_down = 2.0;     // and below it
led_ledge_keep = 0.5;      // inside fit only: height of PCB ledge left at FULL
                           // width above the pocket. The ledge is what the board
                           // rests on and it is only 1.25 mm wide, so the pocket
                           // must not run up into it.
// Two clearances, because they are not the same problem. The flange's edge is
// ON the outer surface, so its gap is a seam the user can see - keep it tight.
// The boss is buried in the wall where nothing is visible, so it gets the
// margin that actually lets the part go in: it travels the full 2.9 mm wall
// thickness, and it is the only feature that can bind on the way.
led_insert_gap = 0.12;     // EVERY VISIBLE SEAM, per face: the flange in its
                           // pocket, and the boss's lip where it meets the outer
                           // face. If a printed part is too tight to push home,
                           // this is the number to raise - it is also the only
                           // one anybody can see.
                           // 0.12, not 0.10, because ONE part serves all three
                           // windows and D1's slot sits 3.4 deg off square to its
                           // wall: at 0.10 the shared part fouled that cavity by
                           // 0.0062 mm3, about 13 um on one diagonal. 0.12 clears
                           // it for 20 um of extra seam. (A 0.0001 mm3 residue is
                           // left at ANY gap - it does not shrink at 0.13 or 0.15,
                           // so it is CGAL noise on the coincident faces, not a
                           // fit problem. Don't chase it.)
led_window_gap = 0.25;     // the BURIED clearance, per face: the rest of the boss
                           // inside the wall, behind the lip. Also what keeps the
                           // boss (z 9.65 .. 11.35) clear of the PCB underside at
                           // 11.5 rather than touching it.
led_boss_lip = 0.6;        // how deep the close-fitting lip runs in from the outer
                           // face. Fitted from the inside the boss IS the visible
                           // seam, so it cannot simply take led_window_gap; a short
                           // lip keeps the seam tight while the rest stays loose
                           // enough to push through 2.9 mm of wall. Set 0 for a
                           // plain boss. With led_fit_from = "outside" the flange
                           // covers this region, so the lip makes no difference.
led_tab_inset = 0.05;      // ⚠️ how far the web is held back from the flange's own
                           // faces. NOT cosmetic: at 0 the web's four faces are
                           // COPLANAR with the flange's, and the export comes out
                           // with 8 degenerate facets and 8 non-manifold edges per
                           // joint (40 on the six-up strip). OpenSCAD then refuses
                           // to boolean the imported mesh at all - which is how it
                           // was noticed. Keep it well above mesh tolerance.
led_score_t = 0.3;         // breakaway connection: the web runs the full height of
                           // the flange's end face (3.26 mm) and the V is cut into
                           // its two FACES, pinching the THICKNESS to this at
                           // mid-span - a PCB V-score, not a waisted bar. That is
                           // the axis you actually break about: the two parts fold
                           // towards each other and the thin ligament fails in
                           // tension. 1 mm is not available in this direction - the
                           // web is only as thick as the flange it sits on (0.88,
                           // less the inset) and the pocket has no room for more.
                           // At 0.3 the ligament is 3.26 x 0.3 = 0.98 mm2, slightly
                           // MORE than the 0.78 the full-thickness version left.
led_tab_len = 1.6;         // tab length, root to root

// --- the window itself --------------------------------------------------------
led_window_mode = "cone";  // "cone" (shipped) | "slot" (the as-tested opening)
                           // "slot" is the rectangular 2.8 x 2.2 window the EMC
                           // sample had: a stepped boss fills it, positioned by
                           // led_boss_lip and led_window_gap. "cone" replaces the
                           // boss with a truncated cone seated in a matching
                           // countersink, and shrinks the outer aperture.
led_cone_d = 1.6;          // the OUTER aperture, round. 2.0 mm2 against the
                           // slot's 6.2 - a third of the opening, which is a
                           // smaller ESD target as well as a smaller mark. Still
                           // a normal indicator dot, and the cone behind it
                           // funnels the LED into it rather than letting it
                           // spill sideways the way a straight slot does.
led_cone_gap = 0.08;       // the insert's clearance ON THE CONE, perpendicular.
                           // Its own number, not led_insert_gap, because a cone
                           // does not use a gap the way a parallel-sided boss
                           // does: there the gap sets the position and has to
                           // swallow the print tolerance sideways, here the taper
                           // centres the part and the tolerance comes out as a
                           // few hundredths of depth. So the gap is only a bond
                           // line - and since it is also what you SEE as a ring
                           // round the aperture, 0.08 beats the slot's 0.12.
led_cone_half_angle = 20;  // of the countersink. NOT a standard 41-45 deg
                           // countersink: that wide, the cone's base outgrows
                           // the flange it has to sit inside (3.96 mm tall) and
                           // leaves a knife edge round it. At 20 deg the base is
                           // 2.69 and the flange keeps 0.63 mm a side. Shallower
                           // is also a longer seam and a better light pipe.

// ============================================================================
//  Reset / boot buttons (EMC-700)
// ============================================================================
// The two service buttons are reached through a 6.0 x 3.0 mm rectangular hole in
// the side wall, two per half - three times the area of a status-LED window, and
// the points the report says made the board RESTART at +-8 kV. They cannot be
// plugged solid like the LEDs, because they have to move, so they get a rigid
// plunger retained by ears behind the wall.
//
// ⚠️ Read the trade honestly: a bonded insert's protection is STRUCTURAL (there
// is no gap), a plunger's is DIMENSIONAL (the gap is as long and as thin as the
// fit allows, and degrades with print tolerance). This turns an 18 mm2 open
// window into ~1.8 mm2 of 0.12 mm slot 2.9 mm deep, with a step and a corner on
// the two long sides. That is a large improvement and not an elimination.
//
// The switch is a Panasonic EVQPUC02K side-push: body 4.7 x 3.5 x 2.5, actuator
// 1.0 mm proud of the body, 0.25 mm travel, sitting on the UNDERSIDE of the
// board (SW2/SW3 in poly_kybd_split72_{left,right}.kicad_pcb). Its tip lands
// 0.53 mm outboard of the board edge, i.e. 0.38 mm INSIDE the wall - which is
// why the plunger needs a blind pocket in its back face rather than a flat one.
btn_insert = true;         // cut the counterbore; false = the pre-plunger case
btn_z0 = pcb_edge_height - 0.4;   // 9.1, where the case has always cut the hole
btn_h = 3.0;               // and how tall. Both MEASURED off the existing cut,
btn_r = 2.5;               // not chosen: the opening is offset(2.5) on a line
                           // the SVG imports with a ~1.0 mm stroke, so 6.0 wide.
btn_slide_gap = 0.12;      // per face. A SLIDING fit, so it cannot be bonded and
                           // cannot be closed up: this gap IS the remaining ESD
                           // path, and the same 0.12 the resin holds elsewhere.
btn_ear = 1.4;             // how far each retaining ear reaches past the opening
btn_ear_t = 0.8;           // and how thick it is, along the travel
btn_under = 2.6;           // how far the counterbore reaches BELOW the opening.
                           // Only downward: the opening's top is already 0.6 mm
                           // above the ledge, so growing it upward would cut the
                           // ledge the board rests on. Below it there is 7 mm of
                           // ledge, and that is where the bridge lives.
btn_c = [ 83.69, 91.49 ];  // the two button centres in y, MEASURED off the cut
                           // (the SVG lines at 47.60 and 55.40, flipped). Only y
                           // is needed - x comes from the wall bands - and y is
                           // unaffected by left_case()'s mirror, so one list
                           // serves both halves.
btn_sep = 1.0;             // the gap kept BETWEEN the two plungers. At btn_ear
                           // 1.4 the counterbore stadiums merge into one pocket,
                           // which is what makes room for the bridge - but the
                           // ears would merge with it and rigidly couple the two
                           // buttons, so they are cut apart again here.
                           // ⚠️ Reset and boot must work independently: pressing
                           // both AT ONCE is the RP2040 bootloader gesture.
btn_bridge = true;         // join the pair into one part, fitted in one go
btn_bridge_t = 0.8;        // the bridge section, along the travel ...
btn_bridge_h = 1.2;        // ... and in z. 0.8 is the print service's floor.
btn_post = 1.6;            // the bridge is attached ONLY at the two outer ends:
                           // that makes it a fixed-guided beam spanning 15.2 mm
                           // rather than the 0.44 mm between the plungers, which
                           // is the difference between a flexure and a weld.
btn_travel = 0.25;         // the switch's own, so the plunger never bottoms out
btn_act_reach = 0.38;      // how far the actuator pokes past the wall's inner
                           // face; the pocket that receives it is this deep
btn_act_w = 2.2;           // the pocket, generously oversized in both directions
btn_act_h = 1.8;           // - the switch's z is read off the board, not modelled
btn_body_w = 5.1;          // clearance the ears leave for the switch BODY (4.7)
btn_body_front = -0.47;    // and where that body starts, as an offset from the
                           // board outline: MEASURED off the footprint (body
                           // 210.83, board edge 211.298 on the right board), not
                           // the wall's inner face. ⚠️ Reserving the whole ledge
                           // depth instead reads as a 5.1 mm3 clash at full
                           // travel - the nose crossing a line the switch is not
                           // actually behind.


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
// the case and the insert that fills it are two views of one definition. `g`
// and `gw` are the clearances: 0 builds the cut, the led_*_gap values build the
// part that fits it.

function led_fit_inside() = led_fit_from == "inside";

// The two wall faces the flange can sit in, as offsets from the board outline
// (positive = outboard). Measured on the model, not assumed: below z = 11.5 the
// wall runs x -0.452 .. 2.448, above it only -0.452 .. 1.048.
function led_out_r() = case_wall_thickness + pcb_clearance;    // outer face
function led_in_r() = -(pcb_edge_width - pcb_clearance);       // ledge inner face
function led_hi_r() = pcb_clearance;                            // wall above the PCB
// ⚠️ SIGN: offset() grows OUTWARD, and above the board the wall stops 0.15 mm
// outboard of the outline (measured: x -0.452..1.048 above z 11.5, against
// -0.452..2.448 below it), so this is +pcb_clearance. Getting it negative puts
// the band 0.3 mm inboard and the relief below silently does nothing.

// z range of the slot through the wall (unchanged from the original cut)
function led_window_z0() = pcb_edge_height - 0.1;
function led_window_h() = 2.20;
// The pocket must not reach above the PCB underside: the wall is only
// case_wall_thickness there, and a pocket would leave it too thin to print.
// Fitted from the INSIDE it has to stop lower still, because that pocket is cut
// into the ledge the board rests on - hence led_ledge_keep.
function led_pocket_z1() = case_bottom_thickness + pcb_edge_height
                           - (led_fit_inside() ? led_ledge_keep : 0);
function led_pocket_z0() = led_window_z0() - led_pocket_down;

// Everything that needs a slice of wall asks for it by the two offsets that
// bound it, so there is one place where the wall's thickness is expressed.
module led_band_r(r_out, r_in)
{
    linear_extrude(height = case_height * 3, center = true) difference()
    {
        offset(r = r_out, $fn = 128) import(file = pcb_outline, dpi = 300);
        offset(r = r_in, $fn = 128) import(file = pcb_outline, dpi = 300);
    }
}

// The band `d` deep measured from whichever face the flange sits in, full height.
// `g` thins it on the FAR side, so the part stays flush with that face and the
// clearance ends up behind it where nothing can see it.
module led_wall_band(d, g = 0)
{
    if (led_fit_inside()) led_band_r(led_in_r() + d - g, led_in_r());
    else led_band_r(led_out_r(), led_out_r() - d + g);
}

// --- the conical boss ---------------------------------------------------------
// A cone cannot be built from led_band_r(): that offsets the board outline, which
// follows the wall but knows nothing about a particular window's axis. So the
// cone is built in the CANONICAL insert frame (outer face at z = 0, +z inward,
// the window's axis) and placed by led_place_d5/d6/d1 - the same transforms
// led_insert() inverts, so the part and the cut cannot disagree about where the
// axis is.
function led_cone_wall() = led_out_r() - led_hi_r();     // 1.50, the wall proper
function led_cone_thru() = led_out_r() - led_in_r();     // 2.90, wall + ledge
function led_cone_base_d() = led_cone_d + 2 * led_cone_wall() * tan(led_cone_half_angle);

// The cone seats in the WALL; behind it a plain cylinder passes through the PCB
// ledge to the flange. Running the cone the whole 2.9 mm instead would open it to
// 3.71 mm, against a flange only 3.96 mm tall - a knife-edge lip all round.
// `g` is the gap on the cone, `gw` the buried one on the cylinder, `over` the
// overshoot that keeps the CUT from ending exactly on the outer surface.
module led_cone_boss_local(g = 0, gw = 0, over = 0)
{
    // ⚠️ A gap measured PERPENDICULAR to a cone is a bigger one measured
    // radially: dr = g / cos(half angle). Shrinking the radius by g itself
    // leaves only g*cos = 0.94 g of bond line, and the part sits proud by the
    // difference. Same trap as measuring a countersink's diameter instead of
    // its depth.
    dr = g / cos(led_cone_half_angle);
    union()
    {
        translate([ 0, 0, -over ])
            cylinder(h = led_cone_wall() + over, $fn = 96,
                     d1 = led_cone_d - 2 * dr,
                     d2 = led_cone_base_d() - 2 * dr);
        translate([ 0, 0, led_cone_wall() ])
            cylinder(h = led_cone_thru() - led_cone_wall(), $fn = 96,
                     d = led_cone_base_d() - 2 * gw);
    }
}

module led_cone_boss(g = 0, gw = 0, over = 0)
{
    led_place_d5() led_cone_boss_local(g, gw, over);
    led_place_d6() led_cone_boss_local(g, gw, over);
    led_place_d1() led_cone_boss_local(g, gw, over);
}

// The boss: the part of the insert that fills the window. In "slot" mode, two
// clearances along its length - a short lip at the outer face at `g`, the buried
// remainder at `gw`. In "cone" mode the taper IS the fit, so there is no lip to
// grade: `g` is the perpendicular gap on the cone and `gw` the buried one behind
// it. With both at 0 this is just the opening through the wall, which is what the
// case subtracts, so the cut and the part still come from one definition.
module led_boss(g = 0, gw = 0)
{
    // ⚠️ `g` only says cut-or-part here; the cone has its own gap (see
    // led_cone_gap). Passing led_insert_gap straight through would widen the
    // visible ring to 0.128 mm radially, since a perpendicular gap on a 20 deg
    // cone is 1.06x that measured across the aperture.
    if (led_window_mode == "cone") led_cone_boss(g > 0 ? led_cone_gap : 0, gw);
    else
    {
        intersection()
        {
            led_band_r(led_out_r(), led_out_r() - led_boss_lip);
            led_window_cut(g);
        }
        intersection()
        {
            led_band_r(led_out_r() - led_boss_lip, led_in_r());
            led_window_cut(gw);
        }
    }
}

// The opening itself, through the whole wall. This is what the case subtracts,
// so it is also what defines the shape the boss above has to match.
module led_window_cut(g = 0)
{
    if (led_window_mode == "cone") led_cone_boss(g, g, 0.05);
    else
        translate([ 0, 0, led_window_z0() + g ])
            linear_extrude(height = led_window_h() - 2 * g, scale = 1)
                offset(r = led_slot_r - g, $fn = 64) import(file = led_holes, dpi = 300);
}

// The local thinning of the wall that makes room for the flange.
module led_pocket_cut(g = 0, ov = led_pocket_overlap)
{
    intersection()
    {
        led_wall_band(led_pocket_depth, g);
        translate([ 0, 0, led_pocket_z0() + g ])
            linear_extrude(height = led_pocket_z1() - led_pocket_z0() - 2 * g, scale = 1)
                offset(r = led_slot_r + ov - g, $fn = 64)
                    import(file = led_holes, dpi = 300);
    }
}

// Both cuts together - what the case loses, and (with g) what the insert is.
// Where the PCB rests. Everything inboard of the wall above the board, above
// the pocket top, is the one slice of the boss that runs under the ledge the
// board sits on - and at the shipped numbers it passes 0.15 mm under it.
// Taking it off costs nothing: the window stays plugged for the 1.65 mm from
// the OUTER face inwards, so there is still no path from outside, and what is
// left behind is a blind recess on the inside. Only the part is relieved; the
// case's cut is untouched, which is why `relief` defaults off.
module led_ledge_relief(g = 0)
{
    intersection()
    {
        led_band_r(led_hi_r(), led_in_r());
        translate([ 0, 0, led_pocket_z1() - g ])
            linear_extrude(height = case_height * 2) square(600, center = true);
    }
}

module led_insert_solid(g = 0, gw = 0, ov = led_pocket_overlap, relief = false)
{
    difference()
    {
        union()
        {
            led_pocket_cut(g, ov);
            // The boss spans the whole wall, outer face to ledge inner face.
            led_boss(g, gw);
        }
        if (relief) led_ledge_relief(g);
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

// ONE part, used three times per half. The three windows are geometrically
// identical: both walls are dead straight over the flange's footprint (the left
// wall runs x = 2.448 from y 56.4 to 129.8, the top wall from (3.75, 131.07) to
// (70.54, 135.04)), the wall is 2.9 mm thick at all three, and the slots and the
// pocket come from the same parameters. So these three differ only by a rigid
// transform - which is what led_insert_congruence_test() below asserts.
module led_insert_d5() { intersection() { led_insert_solid(led_insert_gap, led_window_gap, led_flange_overlap, true); led_region(-10, 45, 10, 53); } }
module led_insert_d6() { intersection() { led_insert_solid(led_insert_gap, led_window_gap, led_flange_overlap, true); led_region(-10, 37, 10, 45); } }
module led_insert_d1() { intersection() { led_insert_solid(led_insert_gap, led_window_gap, led_flange_overlap, true); led_region(4, -8, 22, 16); } }


// --- the part on its own, and the chain it prints on ---------------------------
// There is ONE insert, used three times per half. The modules above build it in
// case coordinates; these lift it out of them so it can be printed, chained, or
// hung off the diffuser frame.
//
// These three are the LED centres in the SVG's own coordinates (the KiCad board
// offset by the Edge.Cuts bbox, (-28.0995, -26.395)).
led_d6 = [ 4.603, 41.203 ];
led_d5 = [ 4.553, 49.153 ];
led_d1 = [ 12.795, 9.597 ];

// Where the walls meet the board outline, in the SVG's coordinates.
led_edge_x = 1.1985;   // the x of the outline's straight left edge (D5/D6 wall)
led_edge_y = 6.234;    // the outline's front edge at D1's x (interpolated)

// D5's slot centre along its wall. MEASURED off the exported slot, not taken from
// led_d5: the User-layer slot sits 0.047 mm from the LED centre, and the SVG is
// what the geometry is built from.
led_d5_slot_y = 89.89;

function led_z_mid() = (led_pocket_z0() + led_pocket_z1()) / 2;
// The part's own mid-height: the flange starts at the pocket floor and the boss
// lip reaches the top of the window, so the two gaps cancel.
function led_insert_z_mid() = (led_pocket_z0() + led_window_z0() + led_window_h()) / 2;
// Half the part's length along its wall. The imported slot is a LINE with a
// ~1.0 mm stroke (see led_slot_r), so half of it is led_slot_half.
led_slot_half = 0.5;
function led_insert_half() = led_slot_half + led_slot_r + led_flange_overlap - led_insert_gap;
// The other two half-extents, as functions so a `use <>` in another part can
// reach them - `use` imports modules and functions but NOT variables.
function led_insert_half_h() = (led_window_z0() + led_window_h() - led_pocket_z0()) / 2 - led_insert_gap;
function led_insert_thk() = case_wall_thickness + pcb_edge_width;
function led_tab_l() = led_tab_len;

// The insert on its own: the OUTER (visible) face on z = 0, the flange face at
// z = 2.9, long axis along x, centred on the origin in x and y.
// ⚠️ The matrix is a ROTATION, not a mirror - det must be +1. A reflected insert
// looks perfectly right on a plate and fits nothing.
module led_insert()
{
    multmatrix([ [ 0, 1, 0, -led_d5_slot_y ],
                 [ 0, 0, 1, -led_insert_z_mid() ],
                 [ 1, 0, 0, led_out_r() - led_edge_x ],
                 [ 0, 0, 0, 1 ] ]) led_insert_d5();
}

// --- where the one part goes --------------------------------------------------
// Both walls are flat over the flange's footprint, so each location is a rigid
// transform of the same solid. These constants are MEASURED off the exported
// geometry rather than taken from led_d5/led_d6/led_d1 (the User-layer slots sit
// a few hundredths from the LED centres) and off the outline polygon, whose top
// wall runs (3.7466, 131.066) -> (70.5357, 135.035), i.e. 3.4009 deg.
led_c_d5 = [ 1.5943, 89.8904 ];   // part centroid at D5
led_c_d6 = [ 1.5943, 97.8904 ];   // D6 is a pure 8.0 mm translation of D5
led_c_d1 = [ 12.8025, 132.4597 ];
led_d1_wall_angle = -86.5991;     // the top wall relative to the left one

module led_place_d5() {
    multmatrix([ [ 0, 0, 1, led_edge_x - led_out_r() ],
                 [ 1, 0, 0, led_d5_slot_y ],
                 [ 0, 1, 0, led_insert_z_mid() ],
                 [ 0, 0, 0, 1 ] ]) children();
}
module led_place_d6() { translate([ 0, led_c_d6[1] - led_c_d5[1], 0 ]) led_place_d5() children(); }
module led_place_d1() {
    translate([ led_c_d1[0], led_c_d1[1], 0 ]) rotate([ 0, 0, led_d1_wall_angle ])
        translate([ -led_c_d5[0], -led_c_d5[1], 0 ]) led_place_d5() children();
}
// All three inserts where they belong, for a fit check or a render.
module led_inserts_in_place() {
    led_place_d5() led_insert();
    led_place_d6() led_insert();
    led_place_d1() led_insert();
}

// The breakaway connection: a web the full height of the flange's end face,
// V-scored on both FACES so its thickness pinches to led_score_t at mid-span -
// the same arrangement as a V-scored PCB panel. It snaps THERE and not at its
// root, and folding the two parts together is what breaks it. Runs along +x.
// `h` is the root height - the frame passes its rail width instead, see below.
module led_v_tab(l = led_tab_len, h = 0)
{
    led_v_tab_root(l, h);
    translate([ l, 0, 0 ]) rotate([ 0, 0, 180 ]) led_v_tab_root(l, h);
}
// One half of it: what stays behind on whatever the web was anchored to once the
// score has been broken. A carrier that models its own fitted state needs this -
// see diffuser_frame_<side>_fitted() in the generated frames.
module led_v_tab_root(l = led_tab_len, h = 0)
{
    hr = (h > 0 ? h : led_tab_h()) - 2 * led_tab_inset;
    hull()
    {
        led_tab_sec(hr, led_flange_t() - 2 * led_tab_inset);
        translate([ l / 2, 0, 0 ]) led_tab_sec(hr, led_score_t);
    }
}
module led_tab_sec(h, t) { cube([ 0.01, h, t ], center = true); }

// n inserts in a row, chained end to end. The tab lands on the flange's END face,
// which is buried in the pocket, so no witness mark is ever on a face that shows.
function led_strip_pitch() = 2 * led_insert_half() + led_tab_len;
// `dir` lays the row towards -x without MIRRORING anything: the insert is the
// same part on both halves, and a mirrored one fits nothing.
module led_insert_strip(n = 3, dir = 1)
{
    for (i = [0:n - 1]) translate([ dir * i * led_strip_pitch(), 0, 0 ]) led_insert();
    // ⚠️ GUARD THE RANGE. With n = 1 this is [0:-1], which OpenSCAD 2021.01 does
    // NOT treat as empty - it iterates {0, -1} and the single insert comes out
    // with a web hanging off BOTH ends (x -5.285..5.285 instead of ±3.68).
    if (n > 1) for (i = [0:n - 2])
        translate([ dir * (i * led_strip_pitch() + led_insert_half()), led_tab_y(), led_tab_z() ])
            rotate([ 0, 0, dir > 0 ? 0 : 180 ]) led_v_tab();
}
// The web sits ON the flange's end face - the only part of the end that is there
// for every insert - so it takes that face's centre, height and thickness.
function led_flange_t() = led_pocket_depth - led_insert_gap;
function led_tab_h() = led_pocket_z1() - led_pocket_z0() - 2 * led_insert_gap;
function led_tab_y() = (led_pocket_z0() + led_pocket_z1()) / 2 - led_insert_z_mid();
function led_tab_z() = led_insert_thk() - led_flange_t() / 2;

// ---------------------------------------------------------------------------
//  Reset / boot plunger geometry
// ---------------------------------------------------------------------------
// Everything rides on the same switch_holes SVG the opening has always been cut
// from, so both halves and both buttons come out of one definition and nothing
// is placed by hand. `g` shrinks a shape by the sliding gap, exactly as the
// led_* modules use it: 0 builds the cut, btn_slide_gap builds the part.
module btn_slot(r, h, g = 0, z0 = undef)
{
    zz = (z0 == undef) ? btn_z0 : z0;
    translate([ 0, 0, zz + g ])
        linear_extrude(height = h - 2 * g, scale = 1)
            offset(r = r - g, $fn = 64) import(file = switch_holes, dpi = 300);
}

// The hole through the wall: what the case has always cut.
module btn_opening(g = 0) { btn_slot(btn_r, btn_h, g); }

// The counterbore behind it, in the PCB ledge only: wider in plan AND extended
// downward by btn_under. At btn_ear 1.4 the two stadiums are 8.8 wide on a
// 7.8 pitch, so they MERGE into one pocket spanning both buttons - deliberate,
// because that pocket is what the bridge runs through.
module btn_counterbore(g = 0)
{
    intersection()
    {
        led_band_r(led_hi_r(), led_in_r());
        btn_slot(btn_r + btn_ear, btn_h + btn_under, g, btn_z0 - btn_under);
    }
}

// How far the merged pocket reaches either side of a button centre.
function btn_pocket_half() = 0.5 + btn_r + btn_ear;
function btn_mid() = (btn_c[0] + btn_c[1]) / 2;

// The slot that keeps the two plungers independent. Confined to the opening's
// own height: it must NOT reach the bridge below, which has to stay continuous.
module btn_sep_cut()
{
    translate([ 0, 0, btn_z0 - 0.3 ]) linear_extrude(height = btn_h + 0.6)
        translate([ 0, btn_mid() ]) square([ 600, btn_sep ], center = true);
}

// The bridge: one beam along the bottom of the merged pocket, well below the
// switch, joined to the plungers by posts at the two OUTER ends only.
module btn_bridge_beam(g = 0)
{
    intersection()
    {
        led_band_r(led_hi_r() - 0.2, led_hi_r() - 0.2 - btn_bridge_t);
        btn_counterbore(g);
        translate([ 0, 0, btn_z0 - btn_under + 0.4 ])
            linear_extrude(height = btn_bridge_h) square(600, center = true);
    }
}

module btn_bridge_posts(g = 0)
{
    intersection()
    {
        led_band_r(led_hi_r(), led_hi_r() - btn_ear_t);
        btn_counterbore(g);
        translate([ 0, 0, btn_z0 - btn_under ])
            linear_extrude(height = btn_h + btn_under)
                difference()
                {
                    square(600, center = true);
                    translate([ 0, btn_mid() ])
                        square([ 600, btn_c[1] - btn_c[0] + 2 * btn_pocket_half()
                                      - 2 * btn_post ], center = true);
                }
    }
}

// What the plunger has to keep clear of: the switch body, and the actuator.
// `extra` holds the cut back from the body's real front face. The PART is built
// with travel + a gap of it, so at full travel it still clears; a checker that
// wants the true envelope calls this with 0. ⚠️ Without that allowance the ear
// plate's bridge - the piece spanning the middle between the shoulder and the
// body - reads as a clean fit at rest and drives 0.25 mm into the switch when
// pressed, which is the one position nothing static would ever test.
module btn_switch_clear(extra = 0)
{
    intersection()
    {
        led_band_r(btn_body_front + extra, led_in_r() - 1);
        btn_slot((btn_body_w - 1.0) / 2, btn_h + 1, 0, btn_z0 - 0.5);
    }
}

// The plunger. Nose through the wall, two ears behind the shoulder, and a blind
// pocket in the nose's back face for the actuator. At rest the switch's own
// return spring holds the ears against the shoulder, which is what puts the nose
// flush with the outer face - so the nose length is not a free choice.
module btn_plunger(g = btn_slide_gap)
{
    difference()
    {
        union()
        {
            intersection() { led_band_r(led_out_r(), led_hi_r()); btn_opening(g); }
            difference()
            {
                intersection()
                {
                    led_band_r(led_hi_r(), led_hi_r() - btn_ear_t);
                    btn_counterbore(g);
                    // the ears stay at the opening's own height; the pocket's
                    // extension below them is for the bridge, not for material
                    btn_slot(btn_r + btn_ear, btn_h, g);
                }
                btn_switch_clear(btn_travel + btn_slide_gap);
            }
            if (btn_bridge) { btn_bridge_beam(g); btn_bridge_posts(g); }
        }
        if (btn_bridge) btn_sep_cut();
        // the actuator pocket, from the back face outward
        intersection()
        {
            led_band_r(led_hi_r() + btn_act_reach, led_in_r());
            btn_slot((btn_act_w - 1.0) / 2, btn_act_h, 0,
                     btn_z0 + (btn_h - btn_act_h) / 2);
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

        // cut out switch (and, with btn_insert, the counterbore the plunger's
        // retaining ears sit behind)
        btn_opening();
        if (btn_insert) btn_counterbore();
    

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