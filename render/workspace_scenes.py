"""The workspace scenes: where the keyboard sits, what is around it, the room behind.

One entry per scene, read by workspace_assets.py (what to fetch) and
workspace_scene.py (how to build it). Ids are Poly Haven's; "@counter" is a
reception counter built in workspace_scene.py.

Props are (asset, part, x, y, turn deg, height m or None, lie flat):
- part names one object of a Poly Haven set (office_notepads is a sheet of ten pads,
  stationery_supplies a display of pens around a cup); None takes the whole asset,
- x, y are metres from the keyboard's centre on the desk top (+y away from the viewer),
- the height scales the part to it; None keeps Poly Haven's real-world size,
- lie flat turns a part that stands in the set's display (the pens) onto the desk,
- an optional last dict: origin=True stands the model on its own origin (the clamp
  lamp: its origin is the desk top, the clamp hangs below), at_back=True measures y
  from the desk's back edge, towards the viewer, z lifts it (a cup onto its saucer),
  on=True leaves it out of the overlap check (it stands on another prop).
"@tablet", "@ruler" (300 mm steel), "@set_square" (45 deg acrylic), "@mug",
"@mug_dark", "@puzzle_cube" and "@clips" are built in workspace_scene.py; tint=(r, g, b)
in the last dict multiplies a prop's colours, scale=k resizes it; desk "@black_desk" is a gaming desk. desk_mat: an extended mat under
keyboard and mouse in color at rough, glow=(r, g, b) lights its edge. wall: the desk
stands against a painted wall (color), with an LED strip (led=(r, g, b)), a poster, and
items: a cork "board" with pinned "sheets", a "sheet" on the wall itself, a "clock"
(workspace_scene.wall_item(); x from the keyboard's centre, z from the desk top).
desk_height, desk_depth and desk_width stretch a desk's height, depth or width only (WoodenTable_01 is a
0.55 m low table, 0.66 m deep). mouse: a built mouse on a pad, x, y from the keyboard; wired=True gives it a cable
over the desk's back edge.
monitor: built screens y m behind the keyboard (workspace_scene.monitors(): style
stand, dual, ultrawide or arm), showing render/textures/workspace/<screen> (or one of
screens each, dual) at glow. legend_glow: the key displays' light, against the
room's. The camera looks at the keyboard's centre plus (0, aim_y, aim_z) and focuses
there.
"""
SCENES = {
    "office": dict(
        hdri="poly_haven_studio", hdri_turn=0, hdri_strength=0.65,
        desk="metal_office_desk", desk_height=None, desk_color=(0.88, 0.88, 0.86, 0.75),
        kb_from_front=0.26,                       # m from the desk's front edge to the keyboard's centre
        props=[("potted_plant_01", None, -0.82, 0.34, 30, 0.42, False),
               ("office_notepads", "office_notepads_a4_stack", 0.68, 0.08, 10, None, False, dict(tint=(1.0, 0.93, 0.78))),
               ("stationery_supplies", "stationery_supplies_pen_fancy", 0.66, 0.06, 70, None, True, dict(z=0.011, on=True)),
               ("stationery_supplies", "stationery_supplies_pencil_new_a", 0.67, -0.11, 12, None, True),
               ("stationery_supplies", "stationery_supplies_pencil_used", 0.69, -0.15, -8, None, True),
               ("stationery_supplies", "stationery_supplies_pen_red", -0.44, -0.14, 20, None, True),
               ("@clips", None, 0.56, -0.03, 0, None, False),
               ("@puzzle_cube", None, -0.58, 0.10, 22, None, False),
               ("@mug_dark", None, -0.42, -0.02, 140, None, False),
               ("vintage_stapler", None, -0.58, -0.05, 20, None, False, dict(scale=0.62)),
               ("stationery_supplies", "stationery_supplies_eraser", 0.79, -0.17, 30, None, False),
               ("@usb_hub", None, -0.20, 0.24, 6, None, False, dict(cable=dict(dx=-0.24))),
               ("rubber_duck_toy", None, 0.56, 0.24, -30, 0.065, False)],
        desk_mat=dict(w=0.76, d=0.34, x=0.06, y=0.0, image="mat_topo.jpg", rough=0.95),
        wall=dict(color=(0.56, 0.54, 0.50), items=[
            dict(kind="board", x=-0.40, z=0.63, w=0.80, h=0.40, sheets=[
                dict(img="paper_sprint.jpg", x=-0.29, z=0.13, w=0.16, rot=-3, pin=(0.85, 0.1, 0.1)),
                dict(img="print_pcb_rev33.jpg", x=-0.08, z=0.14, w=0.20, rot=3, pin=(0.1, 0.3, 0.85)),
                dict(img="print_stems.jpg", x=0.13, z=0.14, w=0.16, rot=-4, pin=(0.95, 0.8, 0.1)),
                dict(img="print_pcb_split42.jpg", x=0.30, z=0.12, w=0.13, rot=5, pin=(0.1, 0.6, 0.2)),
                dict(img="paper_schematic.jpg", x=-0.10, z=-0.03, w=0.19, rot=-2, pin=(0.85, 0.1, 0.1)),
                dict(img="print_rgb.jpg", x=0.10, z=-0.02, w=0.15, rot=2, pin=(0.1, 0.3, 0.85)),
                dict(img="print_emoji.jpg", x=0.27, z=-0.04, w=0.10, rot=-6, pin=(0.85, 0.1, 0.1)),
                dict(img="sticky_yellow.jpg", x=-0.30, z=-0.08, w=0.076, rot=6, pin=(0.95, 0.8, 0.1))]),
            dict(kind="sheet", img="paper_month.jpg", x=0.86, z=0.76, w=0.28, rot=0, pin=(0.2, 0.2, 0.22)),
            dict(kind="sheet", img="print_halves.jpg", x=0.94, z=0.37, w=0.14, rot=-3, bow=0.0, pin=(0.1, 0.3, 0.85)),
            dict(kind="sheet", img="sticky_blue.jpg", x=0.90, z=0.22, w=0.076, rot=3, bow=0.008)]),
        monitor=dict(style="dual", y=0.42, inches=27, finish="black",
                     screens=["screen_code.jpg", "screen_polykybd_org.jpg"], gap=0.003,
                     notes=[(0, -0.36, "sticky_green.jpg", -4), (0, 0.12, "sticky_wide.jpg", 2, 0.076),
                            (1, 0.28, "sticky_pink.jpg", -3, 0.038)], screen_rough=0.12, cables=True),
        mouse=dict(x=0.32, y=0.0, turn=-6, wired=True, color=(0.035, 0.035, 0.037), side=(0.015, 0.015, 0.016), rough=0.7, coat=0.0),
        lights=[dict(at=(0.1, 0.1, 1.5), size=(1.2, 0.6), energy=55, color=(1.0, 0.80, 0.55))],
        camera=dict(distance=2.6, elev=13, azim=-10, lens=52, fstop=11.0, aim_y=0.16, aim_z=0.29)),
    "front_desk": dict(
        hdri="entrance_hall", hdri_turn=90, hdri_strength=1.2,
        desk="@counter", desk_height=None,
        kb_from_front=0.24,
        props=[("potted_plant_04", None, 0.64, 0.30, 20, None, False),
               ("binder_notebook", "binder_notebook_closed", -0.44, 0.04, 8, None, False),
               ("alarm_clock_01", None, 0.56, 0.08, -25, None, False),
               ("stationery_supplies", "stationery_supplies_pen_fancy", -0.30, -0.10, -60, None, True),
               ("ceramic_vase_01", None, -0.62, 0.32, 0, 0.30, False),
               ("tea_set_01", "tea_set_01_saucer_circular_04", 0.62, -0.14, 0, None, False),
               ("tea_set_01", "tea_set_01_cup_small_01", 0.62, -0.136, -20, None, False, dict(z=0.009, on=True))],
        monitor=dict(style="stand", y=0.42, x=-0.04, inches=24, screen="screen_calendar.jpg", turn=-6, glow=1.0),
        mouse=dict(x=0.34, y=0.02, turn=-4, wired=True),
        camera=dict(distance=1.2, elev=15, azim=10, lens=40, fstop=4.0, aim_y=0.16, aim_z=0.17)),
    "planning": dict(
        hdri="studio_country_hall", hdri_turn=60, hdri_strength=1.0,
        desk="WoodenTable_01", desk_height=0.75, desk_depth=0.90,
        kb_from_front=0.22,
        props=[("office_notepads", "office_notepads_a4_stack", 0.66, 0.16, -8, None, False),
               ("office_notepads", "office_notepads_a4_b", 0.62, -0.14, 14, None, False),
               ("binder_notebook", "binder_notebook", -0.52, 0.10, 15, None, False),
               ("stationery_supplies", "stationery_supplies_pencil_new_a", 0.58, -0.08, 30, None, True),
               ("stationery_supplies", "stationery_supplies_pencilcup", 0.56, 0.38, 0, None, False),
               ("potted_plant_02", None, -0.76, 0.34, 0, 0.36, False),
               ("measuring_tape_01", None, -0.30, -0.14, 60, None, False),
               ("round_spectacles", None, 0.40, -0.24, 20, None, False),
               ("@ruler", None, 0.70, 0.02, 84, None, False),
               ("@set_square", None, -0.62, -0.16, 15, None, False),
               ("stationery_supplies", "stationery_supplies_pencil_used", -0.44, -0.20, 40, None, True),
               ("stationery_supplies", "stationery_supplies_eraser", -0.36, -0.24, -10, None, False)],
        desk_mat=dict(w=0.9, d=0.36, x=0.1, y=0.0, color=(0.16, 0.08, 0.035), rough=0.45, coat=0.15),
        monitor=dict(style="ultrawide", y=0.42, x=-0.06, inches=34, screen="screen_plan.jpg", turn=4, glow=1.0),
        mouse=dict(x=0.34, y=0.02, turn=-8, wired=True),
        camera=dict(distance=1.25, elev=14, azim=18, lens=40, fstop=4.0, aim_y=0.14, aim_z=0.17)),
    "designer": dict(
        hdri="artist_workshop", hdri_turn=120, hdri_strength=1.0,
        desk="painted_wooden_table", desk_height=0.75, desk_depth=0.85, desk_width=1.7,
        kb_from_front=0.24,
        props=[("@tablet", None, 0.52, 0.02, -12, None, False),
               ("potted_plant_04", None, -0.66, 0.34, 0, None, False),
               ("tea_set_01", "tea_set_01_saucer_circular_04", -0.44, 0.04, 0, None, False),
               ("tea_set_01", "tea_set_01_cup_small_01", -0.44, 0.044, 50, None, False, dict(z=0.009, on=True)),
               ("croissant", None, -0.52, 0.24, 30, None, False),
               ("office_notepads", "office_notepads_sticky_stack", -0.26, -0.16, -15, None, False),
               ("stationery_supplies", "stationery_supplies_pencil_used", 0.30, -0.22, 50, None, True),
               ("@ruler", None, -0.30, 0.30, 6, None, False),
               ("stationery_supplies", "stationery_supplies_pencil_old", -0.24, -0.22, 20, None, True)],
        desk_mat=dict(w=1.0, d=0.38, x=0.2, y=0.0, color=(0.42, 0.38, 0.32), rough=0.95),
        monitor=dict(style="stand", y=0.42, inches=27, screen="screen_design.jpg", glow=1.4),
        mouse=None,
        camera=dict(distance=1.25, elev=15, azim=-14, lens=40, fstop=4.0, aim_y=0.15, aim_z=0.18)),
    "gamer": dict(
        hdri="neon_photostudio", hdri_turn=210, hdri_strength=0.7,
        desk="@black_desk", desk_height=None,
        kb_from_front=0.25,
        desk_mat=dict(w=0.92, d=0.38, x=0.12, y=0.0, glow=(1.0, 0.15, 0.85), strength=8.0),
        props=[("gamepad", None, -0.58, -0.10, 25, None, False),
               ("digital_wrist_watch", None, 0.70, -0.10, 70, None, False)],
        monitor=dict(style="ultrawide", y=0.42, inches=34, screen="screen_game.jpg", glow=1.8),
        mouse=dict(x=0.36, y=0.0, turn=-6, wired=True),
        legend_glow=14.0,
        camera=dict(distance=1.55, elev=15, azim=12, lens=40, fstop=4.0, aim_y=0.14, aim_z=0.17)),
    "gamer_wall": dict(
        hdri="neon_photostudio", hdri_turn=210, hdri_strength=0.6,
        desk="@black_desk", desk_height=None,
        kb_from_front=0.25,
        wall=dict(color=(0.13, 0.14, 0.18), led=(0.25, 0.35, 1.0), led_strength=300.0, led_z=0.30, led_w=0.9,
                  poster="poster_road.jpg", poster_x=-0.68, poster_z=0.36, poster_w=0.36),
        desk_mat=dict(w=0.92, d=0.38, x=0.12, y=0.0, glow=(1.0, 0.15, 0.85), strength=8.0),
        props=[("gamepad", None, -0.60, -0.08, 25, None, False),
               ("digital_wrist_watch", None, 0.70, -0.12, 70, None, False)],
        monitor=dict(style="ultrawide", y=0.40, inches=34, screen="screen_game.jpg", glow=1.8),
        mouse=dict(x=0.36, y=0.0, turn=-6, wired=True),
        legend_glow=14.0,
        camera=dict(distance=1.6, elev=14, azim=14, lens=40, fstop=4.0, aim_y=0.16, aim_z=0.22)),
}
