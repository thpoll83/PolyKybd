// Reset / boot button plungers (EMC-700).
//
// EMC report EMC-700 left +-8 kV ESD air discharge NOT RATED at the reset and
// boot openings - the points where the keyboard RESTARTED. Each opening is a
// 6.0 x 3.0 mm hole straight through 2.9 mm of side wall, two per half, so they
// are three times the area of a status-LED window and the biggest holes in the
// enclosure.
//
// Unlike the LED inserts these cannot be bonded shut: the buttons have to move.
// So each gets a rigid plunger that fills the hole on a sliding fit and is held
// in by two ears behind a counterbore in the PCB ledge. The switch's own return
// spring holds the ears against the shoulder, which is what puts the nose flush
// with the outer face - the nose length is not a free choice.
//
// ⚠️ The protection is DIMENSIONAL, not structural. A bonded insert leaves no
// gap at all; this leaves 0.12 mm of gap round an 18 mm perimeter, 2.9 mm deep,
// with a step and a corner on the two long sides. ~2.2 mm2 of slot against
// 18 mm2 of open window - a large improvement, not an elimination, and it is
// only as good as the print tolerance. See the note in the case file.
//
// The geometry comes from case_polykybd_split72_lr.scad, so the plunger and the
// hole it slides in can never drift apart - edit the btn_* parameters there.
// !! -D on the command line sets a variable in THIS file, not in a use<>'d one.
//
//   openscad -o ../export/case/btn_plungers.stl               btn_plungers.scad
//   openscad -o ../export/case/btn_plunger.stl -D 'part="one"' btn_plungers.scad
//
// FOUR per keyboard (two per half; both halves use the same part). Verify with
// parts/case/check_btn_plunger.py. Assemble from the INSIDE, before the board
// goes in - the ears are wider than the hole, so it cannot be fitted later.

use <case_polykybd_split72_lr.scad>

part = "pair";   // "pair" (one half's worth, as placed) | "one"

if (part == "pair") btn_plunger();
if (part == "one")
    intersection()
    {
        btn_plunger();
        // the lower of the two, isolated: the switch_holes SVG carries both, so
        // a single part is cut out of the pair rather than placed on its own
        translate([ 0, 0, -50 ]) linear_extrude(100)
            // ⚠️ 7.8 wide, not more: that is the pitch between the two, so a
            // wider window clips a slice off its neighbour and the part reads
            // 0.8 mm too wide.
            translate([ 183, 83.69 ]) square([ 20, 7.8 ], center = true);
    }
