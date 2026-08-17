// Profile arrangement renders -- NOT print plates.  build_stems.sh exports only
// variants/, so nothing here is committed as a mesh; open this file and switch
// `view` to look at one, or render the whole set with render_profiles.sh, which
// gives them all the same camera -- four pictures framed by hand compare badly,
// because a difference in elevation reads as a difference in profile.
//
// These lived as commented-out blocks at the bottom of keycap_stem.scad.  They
// are kept because they are genuinely useful -- a row lineup shows the profile
// progression far better than a plate does, and the README's profile pictures
// come from here -- but they do not belong in the library: `include` executes
// top-level geometry, so anything left there would appear in all sixteen
// variants.
include <keycap_stem.scad>

// Rows run FRONT to BACK: row 1 is the one closest to you, row 5 the furthest.
// That is why the curved set rises from R1 (flattest, least lifted) to R5.
//
//   "curved"            R1..R5 -- a different stem per row
//   "stepped"           S1 / S / S5 -- sculpted: S1 front, S5 back, S between
//   "stepped_uniform"   S everywhere -- one stem for all five rows
//   "flat"              R3 everywhere -- one stem, no tilt, no lift
//   "r2_rows"           the older r2 curved set (historic, different parameters)
//   "cutaway"           one stem with the display and its FFC cable in place
view = "curved";

ROW = 19.25;

// One stem per row, front (row 1) nearest the viewer, centred on the middle row.
//
// ⚠️ Do NOT rotate the row to "stand it up so the profile reads better".  The
// renders draw the coordinate axes, and the horizontal axis line is what a
// reader measures each cap angle against -- so a view tilt silently adds itself
// to every angle and the picture reports the wrong profile.  A tilt of 8 was
// tried and had exactly that effect: R3, which is flat by definition, came out
// sitting 8 degrees nose-up on the axis.  Tilt the CAMERA instead (the
// elevation in render_profiles.sh), which moves the axes with it.
module profile_row(angles, lens, labels) {
    for (i = [0:4])
        translate([ 0, (i - 2) * ROW, 0 ])
            mx_stem(u_size = 1, angle = angles[i], extra_len = lens[i],
                    txt = str(labels[i], revision));
}

if (view == "curved")
    profile_row([ 5, -5, 0, 5, 10 ], [ 0.5, 1, 0, 1.5, 4 ],
                [ "R1   ", "R2   ", "R3   ", "R4   ", "R5   " ]);

if (view == "stepped")
    profile_row([ 5, -7, -7, -7, 10 ], [ 0.5, 1.5, 1.5, 1.5, 2.5 ],
                [ "S1   ", "S    ", "S    ", "S    ", "S5   " ]);

if (view == "stepped_uniform")
    profile_row([ -7, -7, -7, -7, -7 ], [ 1.5, 1.5, 1.5, 1.5, 1.5 ],
                [ "S    ", "S    ", "S    ", "S    ", "S    " ]);

if (view == "flat")
    profile_row([ 0, 0, 0, 0, 0 ], [ 0, 0, 0, 0, 0 ],
                [ "R3   ", "R3   ", "R3   ", "R3   ", "R3   " ]);

// The r2 revision's curved parameters, which differ from revAlpha's (R5 lifted
// 3 not 4, R4 0.5 not 1.5, R2 0.5 not 1) -- keep them apart when comparing.
if (view == "r2_rows") {
    translate([ 0, ROW * 3, 0 ])  mx_stem(u_size = 1, angle = 10, extra_len = 3,   txt = "R5r2");
    translate([ 0, ROW * 2, 0 ])  mx_stem(u_size = 1, angle = 5,  extra_len = 0.5, txt = "R4r2");
    translate([ 0, ROW, 0 ])      mx_stem(u_size = 1,                              txt = "R3r2");
                                  mx_stem(u_size = 1, angle = -5, extra_len = 0.5, txt = "R2r2");
    translate([ 0, -ROW, 0 ])     mx_stem(u_size = 1, angle = 5,  extra_len = 0.5, txt = "R1r2");
}

if (view == "cutaway") {
    mx_stem(u_size = 1);
    display();
    cable();
}
