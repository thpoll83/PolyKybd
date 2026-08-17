// Arrangement renders for photos and for eyeballing a profile set -- NOT print
// plates.  build_stems.sh exports only variants/, so nothing here is committed
// as a mesh; open this file and switch `view` to look at one.
//
// These lived as commented-out blocks at the bottom of keycap_stem.scad.  They
// are kept because they are genuinely useful (a row lineup shows the profile
// progression far better than a plate does), but they do not belong in the
// library: `include` executes top-level geometry, so anything left there would
// appear in all sixteen variants.
include <keycap_stem.scad>

// "alpha_rows"  the shipped revAlpha stepped set, rows 1..5, tilted for a photo
// "r2_rows"     the older r2 curved set (historic; not the revAlpha parameters)
// "cutaway"     one stem with the display and its FFC cable in place
view = "alpha_rows";

ROW = 19.25;

if (view == "alpha_rows") {
    rotate([ 8, 0, 0 ]) {
        translate([ 0, ROW * 3, 0 ])  mx_stem(u_size = 1, angle = 10, extra_len = 2.5, txt = str("S5   ", revision));
        translate([ 0, ROW * 2, 0 ])  mx_stem(u_size = 1, angle = -7, extra_len = 1.5, txt = str("S    ", revision));
        translate([ 0, ROW, 0 ])      mx_stem(u_size = 1, angle = -7, extra_len = 1.5, txt = str("S    ", revision));
                                      mx_stem(u_size = 1, angle = -7, extra_len = 1.5, txt = str("S    ", revision));
        translate([ 0, -ROW, 0 ])     mx_stem(u_size = 1, angle = 5,  extra_len = 0.5, txt = str("S1   ", revision));
    }
}

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
