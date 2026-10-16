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
"@tablet" is a pen tablet built in workspace_scene.py; desk "@black_desk" a gaming
desk. desk_mat: an extended mat under keyboard and mouse, glow=(r, g, b) lights its edge.
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
        hdri="blender_institute", hdri_turn=200, hdri_strength=0.8,
        desk="metal_office_desk", desk_height=None,
        kb_from_front=0.26,                       # m from the desk's front edge to the keyboard's centre
        props=[("desk_lamp_arm_01", None, 0.86, 0.0, 215, None, False, dict(origin=True, at_back=True)),
               ("potted_plant_02", None, -0.84, 0.36, 0, 0.40, False),
               ("office_notepads", "office_notepads_yellow_pad", 0.62, 0.06, 10, None, False),
               ("stationery_supplies", "stationery_supplies_pencilcup", -0.44, 0.14, 0, None, False),
               ("stationery_supplies", "stationery_supplies_pen_blue", 0.44, -0.14, 70, None, True),
               ("tea_set_01", "tea_set_01_saucer_circular_04", -0.36, -0.06, 0, None, False),
               ("tea_set_01", "tea_set_01_cup_small_01", -0.36, -0.056, 35, None, False, dict(z=0.009, on=True)),
               ("round_spectacles", None, 0.50, -0.17, -30, None, False),
               ("vintage_stapler", None, -0.56, 0.02, 20, None, False)],
        monitor=dict(style="dual", y=0.40, inches=24, screens=["screen_code.jpg", "screen_polykybd_org.jpg"], gap=0.16),
        mouse=dict(x=0.34, y=0.0, turn=-6, wired=True),
        camera=dict(distance=1.3, elev=15, azim=-12, lens=40, fstop=4.0, aim_y=0.14, aim_z=0.19)),
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
               ("round_spectacles", None, 0.40, -0.18, 20, None, False)],
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
               ("stationery_supplies", "stationery_supplies_pencil_used", 0.30, -0.18, 50, None, True)],
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
}
