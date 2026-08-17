// PolyKybd keycap stem -- curved profile, row 4, 1.25U, 10 pieces per plate.
//
// One variation per file, so this renders on its own: open it in OpenSCAD to
// see exactly what parts/keycap_stem/build_stems.sh exports to
// parts/export/keycap_stem/keycap_stem_revAlpha_1U25_R4_10p.stl (the .stl name matches this filename).
// Shared modules and parameters are in ../keycap_stem.scad; `include` rather
// than `use` because the engraved `revision` is a variable, and `use` imports
// modules only.

include <../keycap_stem.scad>

// angle = tilt of the cap in degrees; extra_len = how far the stem is raised, mm.
ten_connected_pieces_1U25(angle = 5, extra_len = 1.5, txt = str("R4   ", revision));
