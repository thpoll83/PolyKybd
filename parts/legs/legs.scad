// PolyKybd Leg, based on:
// https://www.thingiverse.com/thing:2132775/files
// https://creativecommons.org/licenses/by-nc-sa/4.0/

// The knobs will require supports, and the round ends may need supports depending on the printer and material

//CUSTOMIZER VARIABLES

/* [Basic_Parameters] */

// Body width (not including nobs), in mm
body_width = 22.4;  // [10:0.1:80]

// Full length, in mm
full_length = 20.0;  // [10:0.1:80]

// Full height/thickness, in mm
full_height = 3.8;  // [2:0.1:20]

end_height = 0.5;  // [2:0.1:20]

// Interior height/thickness, in mm
interior_height = 1.7;  // [2:0.1:20]

// Top lip length, in mm
top_lip_length = 2.5;  // [0:0.1:20]

// Bottom lip length, in mm
bottom_lip_length = 9.0;  // [0:0.1:20]

// Arm width, in mm
arm_width = 3.5;  // [1:0.1:20]

// Arm gap width, in mm
arm_gap_width = 1.25;  // [0:0.1:20]

// Arm gap length, in mm
arm_gap_length = 11;  // [0:0.1:20]

// Knob diameter, in mm
knob_diameter = 3;  // [0:0.05:20]
knob_small_diameter = 2.75;

// Knob length, in mm
knob_length = 0.9;  // [0:0.05:20]

// Knob inset from end, in mm
knob_inset = full_height/2;  // [0:0.05:20]

// Font
text_font = "Arial:style=Bold Italic";

//CUSTOMIZER VARIABLES END



// Sanity checks

if ( (2*arm_gap_width + 2*arm_width) >= body_width)
{
    echo("<B>Error: Arms too wide for body</B>");
}

if ((top_lip_length + bottom_lip_length) > full_length)
{
    echo("<B>Error: Body too short</B>");
}


//keyboard_leg();
connected_8p();

// our object, flat on xy plane for easy STL generation
module connected_8p() {
union(){
keyboard_leg();

translate([body_width,-2,0]) rotate([0,0,180]) keyboard_leg();
for(i =[1 : 3]) {
    translate([i*29,0,0]) keyboard_leg();
    translate([i*29+body_width,-2,0]) rotate([0,0,180]) keyboard_leg();
    translate([i*29-6,1.9,1.9]) rotate([0,90,0])
              cylinder(6, 0.75, 0.75, $fn=32 );
    translate([i*29-6,-3.8,1.9]) rotate([0,90,0])
              cylinder(6, 0.75, 0.75, $fn=32 );
}

translate([-1.2, -1, 1.9])
intersection() {
rotate_extrude(convexity=10, $fn=128)
    translate([3, 0, 0])
        circle(r=0.75, $fn=32);
translate([-4.5,0,0])cube([10,10,10], center=true);
}

translate([4*29-5.4, -1, 1.9])
intersection() {
rotate_extrude(convexity=10, $fn=128)
    translate([3, 0, 0])
        circle(r=0.75, $fn=32);
translate([4.5,0,0])cube([10,10,10], center=true);
}
}
}

module keyboard_leg() { 
    
    knob_radius = knob_diameter / 2;
    round_diameter = full_height;
    round_radius = round_diameter / 2;
    interior_length = full_length - top_lip_length - bottom_lip_length;

    difference() {

        union() {
          
          // the main block
          //translate([0,round_radius,0])
            //cube([body_width,full_length-2*round_radius,full_height]);
          
          // round end on bottom of leg
            hull() {
          translate([0,full_length-round_radius,round_radius])
            rotate([0,90,0])
              cylinder(body_width, end_height/2, end_height/2, $fn=32 );
          
          // round end on top of leg
          translate([0,round_radius,round_radius])
            rotate([0,90,0])
              cylinder(body_width, round_radius, round_radius, $fn=32 );
            }
          // knobs on arms
          translate([-knob_length,knob_inset,full_height/2])
            rotate([0,90,0])
              cylinder(knob_length, knob_small_diameter/2, knob_radius, $fn=32 );
          translate([body_width,knob_inset,full_height/2])
            rotate([0,90,0])
              cylinder(knob_length, knob_radius, knob_small_diameter/2, $fn=32 );
        
            translate([0,knob_inset,full_height/2])
            rotate([-90,0,0]) {
              cylinder(h=3, r=0.6, $fn=32 );
              translate([0,0,3]) sphere(r=0.6,$fn=32);
            }
            translate([body_width,knob_inset,full_height/2])
            rotate([-90,0,0]) {
              cylinder(h=3, r=0.6, $fn=32 );
              translate([0,0,3]) sphere(r=0.6,$fn=32);
            }
            
          // notches on arms
          translate([0.1,knob_inset+7.9,full_height/2-0.25])
            rotate([0,90,0])
              sphere(0.3, $fn=32 );
          translate([body_width-0.1,knob_inset+7.9,full_height/2-0.25])
            rotate([0,90,0])
              sphere(0.3, $fn=32 );
        }

        // main block hollow interior
        hollow_height = full_height - interior_height;
        hollow_y = full_length - interior_length;
        hollow_width = body_width - 2*arm_width;
        translate([arm_width,top_lip_length,interior_height])
        hull(){
            translate([0.5,0,0.5])sphere(0.5, $fn=32);
            translate([hollow_width-0.5,0,0.5]) sphere(0.5, $fn=32);
            translate([0.5,interior_length,0.5]) sphere(0.5, $fn=32);
            translate([hollow_width-0.5,interior_length,0.5]) sphere(0.5, $fn=32);
            translate([0.5,0,hollow_height+2]) sphere(0.5, $fn=32);
            translate([hollow_width-0.5,0,hollow_height+2]) sphere(0.5, $fn=32);
            translate([0.5,interior_length,hollow_height+2]) sphere(0.5, $fn=32);
            translate([hollow_width-0.5,interior_length,hollow_height+2]) sphere(0.5, $fn=32);
        }
        //cube([hollow_width,interior_length,hollow_height+2]);
        
        // arm gaps
        translate([arm_width,-2,-1])
          cube([arm_gap_width,arm_gap_length+2,full_height+2]);
        translate([body_width - arm_width - arm_gap_width,-2,-1])
          cube([arm_gap_width,arm_gap_length+2,full_height+2]);
        /*
        translate([body_width/2,7,1.5])
        linear_extrude(height = 1)
        {
            text("r1", size = 4, font = text_font, halign = "center", valign = "center", $fn = 16);
        }
        */

    }
}
