// ===========================================================================
//  PolyKybd split72 — stacked LED diffuser frames for printing
//
//  n copies of one half on a single sprue, so a print service that bills per
//  repeated part sees one piece.  Same trick as the frame itself (36 diffusers
//  in one part) and as spacers_stacked() in case/case_polykybd_split72_lr.scad.
//
//  Sprue: vertical posts just beyond the ends of the two outermost rails, each
//  tied to every copy by a short pin.  The attachment points are deliberately
//  RAIL ENDS, not diffusers — a stub left on a diffuser would sit on the
//  optical surface the LED shines through.  The pins land at the web's own
//  height (z = -1 .. 0), because that is the only material at a rail; the
//  plugs and caps are above it.
//
//  Snip the pins and clean the stubs before fitting.  Note the copies are
//  suspended above one another with only the sprue between them, so the slicer
//  still has to support them — the sprue is what makes it ONE object, not what
//  holds it up.
// ===========================================================================

use <diffuser_frame_left.scad>
use <diffuser_frame_right.scad>

frame_stack_pitch = 5;      // 3.2 mm part + 1.8 mm gap

// These track diffuser_frame_*(): the part spans z = -1 .. 2.2, of which the
// web — the only thing present at a rail — is z = -1 .. 0.
frame_lo  = -1.0;
frame_h   =  3.2;
web_mid   = -0.5;

// The sprue must be the WEAKEST thing here, so it breaks at the gate and not
// at a 2.0 x 1.0 mm stem.  The pin is therefore thinner than the web it lands
// on (0.8 mm vs 1.0 mm) and sits entirely inside its thickness — z -0.9..-0.1
// against the web's -1..0, so nothing stands proud to catch or sand off.  The
// post is never cut, only discarded, so it just has to carry the stack.
post_r    = 0.60;           // 1.2 mm
pin_r     = 0.40;           // 0.8 mm — under the 1.0 mm web on purpose
sprue_gap = 4.0;            // how far beyond the rail end the post stands

// [ x, y on the web, outward direction ] in LEFT-frame coordinates.  The first
// four are the ends of the two outermost rails (x -37.623 and +57.627), which
// span most of the 153 x 101 mm footprint.  The fifth is a mid-span point on a
// thumb link: the thumb cluster hangs off the main field on 2 mm stems and
// would otherwise dangle unsupported through the whole stack.  That point is
// 12.68 mm from the nearest diffuser centre — 9.2 mm of clear stem — so the
// rod lands on web, not on a cap.
frame_sprue = [ [ -37.623,  52.60, +1 ],
                [  57.627,  52.60, +1 ],
                [ -37.623,  -4.55, -1 ],
                [  57.627, -23.60, -1 ],
                [ -62.750, -14.75, +1 ] ];

module _frame_sprue(n)
{
    span = (n - 1) * frame_stack_pitch + frame_h;

    for (s = [0:n - 1])
        for (p = frame_sprue)
            translate([ p[0], p[1] + p[2] * sprue_gap / 2,
                        web_mid + s * frame_stack_pitch ])
                rotate([ 90, 0, 0 ])
                    cylinder(h = sprue_gap + 1.5, r = pin_r, center = true, $fn = 24);

    for (p = frame_sprue)
        translate([ p[0], p[1] + p[2] * sprue_gap, frame_lo + span / 2 ])
            cylinder(h = span, r = post_r, center = true, $fn = 32);
}

module diffuser_frame_left_stacked(n = 4)
{
    for (s = [0:n - 1])
        translate([ 0, 0, s * frame_stack_pitch ]) diffuser_frame_left();
    _frame_sprue(n);
}

// The right frame is the exact x-mirror of the left (see mirror_x() in
// parts/tools/gen_diffuser_frame.py), so mirroring the whole stack gives the
// right half with its sprue already in the matching places.
module diffuser_frame_right_stacked(n = 4)
{
    mirror(v = [ 1, 0, 0 ]) diffuser_frame_left_stacked(n);
}

diffuser_frame_left_stacked(4);
