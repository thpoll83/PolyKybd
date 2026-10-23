// Transparent ESD inserts for the status-LED windows (D1, D5, D6).
//
// EMC report EMC-700 left +-8 kV ESD air discharge NOT RATED at these openings.
// Each insert is bonded into its pocket so the opening does not exist on a
// shipped unit; being transparent, it also turns the slot into a light pipe for
// an LED that previously only showed at an angle.
//
// The geometry comes from case_polykybd_split72_lr.scad, so the insert and the
// pocket it fills can never drift apart - edit the led_* parameters there.
//
//   openscad -o ../export/case/led_insert_pair.stl  -D 'part="pair"'  led_inserts.scad
//   openscad -o ../export/case/led_insert_single.stl -D 'part="single"' led_inserts.scad
//
// Print in a clear resin. Two parts per half, four per keyboard.

use <case_polykybd_split72_lr.scad>

part = "both";   // "pair" (D6+D5) | "single" (D1) | "both"

if (part == "pair"   || part == "both") led_insert_pair();
if (part == "single" || part == "both") led_insert_single();
