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
//   openscad -o ../export/case/btn_plungers.stl  btn_plungers.scad
//
// The two plungers of one half ship as ONE part, joined by a bridge along the
// bottom of the counterbore so they go in together - TWO of these per keyboard,
// not four loose pieces. The bridge is attached only at the two OUTER ends, so
// it spans 13.4 mm rather than the 1.0 mm between the plungers: that makes it a
// flexure, and pressing one button costs ~0.16 N of extra force while putting
// ~0.16 N on the other, against the ~2.5 N its switch needs. ⚠️ They MUST stay
// independent - pressing reset and boot at once is the RP2040 bootloader
// gesture - which is why the ears are cut apart even though the counterbore
// behind them is one pocket.
//
// Verify with parts/case/check_btn_plunger.py. Assemble from the INSIDE, before
// the board goes in - the ears are wider than the hole, so it cannot be fitted
// afterwards. Set btn_bridge = false in the case file for two loose plungers.

use <case_polykybd_split72_lr.scad>

// One option only, deliberately: cutting a single plunger out of the pair would
// sever the bridge and leave half of it hanging off a part that is not what gets
// printed. btn_bridge in the case file is the switch, not a selector here.
btn_plunger();
