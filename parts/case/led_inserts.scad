// Transparent ESD inserts for the status-LED windows (D1, D5, D6).
//
// EMC report EMC-700 left +-8 kV ESD air discharge NOT RATED at these openings.
// Each insert is bonded into its pocket so the opening does not exist on a
// shipped unit; being transparent, it also turns the slot into a light pipe for
// an LED that previously only showed at an angle.
//
// There is ONE part, used three times per half - the three windows are
// geometrically identical. It is fitted from the INSIDE: the boss fills the
// window flush with the outer face and the flange sits in a pocket cut into the
// PCB ledge, so the case's outer surface keeps the geometry that was tested.
// led_fit_from in the case file switches it back to an outer pocket.
//
// The geometry comes from case_polykybd_split72_lr.scad, so the insert and the
// pocket it fills can never drift apart - edit the led_* parameters there.
// !! -D on the command line sets a variable in THIS file, not in a use<>'d one,
// so -D 'led_fit_from="outside"' does nothing. Edit the case file to switch.
//
//   openscad -o ../export/case/led_inserts.stl                 led_inserts.scad
//   openscad -o ../export/case/led_insert.stl -D 'part="one"'  led_inserts.scad
//
// Print in a clear resin. Three per half, six per keyboard. The chained strip is
// the standalone print; the shipped arrangement hangs three off each diffuser
// frame, which is printed in the same material and the same job.

use <case_polykybd_split72_lr.scad>

part = "strip";  // "strip" (6, chained) | "one" | "three" (one half's worth)

if (part == "strip") led_insert_strip(6);
if (part == "three") led_insert_strip(3);
if (part == "one")   led_insert();
