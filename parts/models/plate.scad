pcb_outline = "poly_kb_wave_right_case-Edge_CutsMod.svg";
disp_cutout = "../poly_kb_atom/models/poly_kb_wave_right_plate-User_Eco1.svg";
silkscreen = "../poly_kb_atom/models/poly_kb_wave_right_plate-F_Silkscreen.svg";

intersection(){
difference() {
linear_extrude(height = 1.2, scale=1) import(file =pcb_outline, dpi = 300);
translate([24,0,-1]) linear_extrude(height = 4, scale=1) import(file =disp_cutout, dpi = 300);
}
translate([24,0,0]) linear_extrude(height = 0.2, scale=1) offset(delta=0.001) import(file =silkscreen, dpi = 600);
}