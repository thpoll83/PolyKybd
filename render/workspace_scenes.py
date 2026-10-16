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
  from the desk's back edge, towards the viewer.
desk_height and desk_depth stretch a desk's height or depth only (WoodenTable_01 is a
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
        props=[("desk_lamp_arm_01", None, 0.62, 0.0, 215, None, False, dict(origin=True, at_back=True)),
               ("potted_plant_02", None, -0.56, 0.32, 0, 0.40, False),
               ("office_notepads", "office_notepads_yellow_pad", 0.58, 0.04, 10, None, False),
               ("stationery_supplies", "stationery_supplies_pencilcup", -0.34, 0.10, 0, None, False),
               ("stationery_supplies", "stationery_supplies_pen_blue", 0.56, -0.02, 70, None, True)],
        monitor=dict(style="dual", y=0.38, inches=24, screens=["screen_code.jpg", "screen_polykybd_org.jpg"]),
        mouse=dict(x=0.34, y=0.0, turn=-6, wired=True),
        camera=dict(distance=1.3, elev=15, azim=-12, lens=40, fstop=4.0, aim_y=0.14, aim_z=0.19)),
    "front_desk": dict(
        hdri="entrance_hall", hdri_turn=90, hdri_strength=1.2,
        desk="@counter", desk_height=None,
        kb_from_front=0.24,
        props=[("potted_plant_02", None, 0.66, 0.30, 40, 0.34, False),
               ("binder_notebook", "binder_notebook_closed", -0.40, 0.06, 8, None, False),
               ("alarm_clock_01", None, 0.52, 0.34, -25, None, False),
               ("stationery_supplies", "stationery_supplies_pen_fancy", -0.30, -0.06, -60, None, True)],
        monitor=dict(style="arm", x=-0.04, inches=24, screen="screen_calendar.jpg", turn=-8, glow=1.0,
                     reach=0.30, height=0.30),
        mouse=dict(x=0.34, y=0.02, turn=-4),
        camera=dict(distance=1.2, elev=15, azim=10, lens=40, fstop=4.0, aim_y=0.16, aim_z=0.17)),
    "planning": dict(
        hdri="art_studio", hdri_turn=150, hdri_strength=1.0,
        desk="WoodenTable_01", desk_height=0.75, desk_depth=0.90,
        kb_from_front=0.22,
        props=[("office_notepads", "office_notepads_a4_stack", 0.60, 0.16, -8, None, False),
               ("office_notepads", "office_notepads_a4_b", 0.66, 0.10, 14, None, False),
               ("binder_notebook", "binder_notebook", -0.50, 0.10, 15, None, False),
               ("stationery_supplies", "stationery_supplies_pencil_new_a", 0.56, -0.10, 30, None, True),
               ("stationery_supplies", "stationery_supplies_pencilcup", 0.48, 0.34, 0, None, False),
               ("potted_plant_02", None, -0.74, 0.20, 0, 0.36, False)],
        monitor=dict(style="ultrawide", y=0.40, x=-0.06, inches=34, screen="screen_plan.jpg", turn=4, glow=1.0),
        mouse=dict(x=0.34, y=0.02, turn=-8, wired=True),
        camera=dict(distance=1.25, elev=14, azim=18, lens=40, fstop=4.0, aim_y=0.14, aim_z=0.17)),
}
