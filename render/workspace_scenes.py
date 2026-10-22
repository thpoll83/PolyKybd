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
BOOKS = [  # (title, author, cover rgb, ink rgb, height m, thickness m, spine style), the office shelf
    # left to right; workspace_screens.py draws spine_<i>.jpg, cover_<i>.jpg and back_<i>.jpg. Spine
    # styles, after real books: 0 title down the spine, author and a publisher mark below; 1 serif
    # title between two colour bands; 2 short words stacked across a thick spine; 3 condensed
    # capitals with a rule and a series number
    ("Embedded C", "M. Barr", (0.10, 0.18, 0.32), (235, 225, 200), 0.195, 0.030, 0),
    ("PCB Design", "R. Kehl", (0.55, 0.12, 0.08), (240, 235, 220), 0.205, 0.038, 3),
    ("Typography", "E. Ruder", (0.86, 0.82, 0.70), (40, 40, 45), 0.180, 0.022, 1),
    ("The Art of Electronics", "Horowitz & Hill", (0.12, 0.24, 0.16), (220, 200, 140), 0.215, 0.050, 2),
    ("QMK Notes", "", (0.95, 0.62, 0.12), (30, 30, 35), 0.170, 0.018, 0),
    ("Ergonomics", "K. Kroemer", (0.30, 0.30, 0.33), (230, 230, 230), 0.190, 0.028, 1),
    ("Rust", "S. Klabnik", (0.62, 0.28, 0.12), (245, 240, 230), 0.198, 0.032, 3)]

SCENES = {
    "office": dict(
        hdri="poly_haven_studio", hdri_turn=0, hdri_strength=0.55, exposure=0.25,
        look="AgX - Punchy", sun=dict(**{"from": (-1.0, -0.3, 0.6)}, strength=4.0, angle=1.5),
        post=dict(vignette=0.35, glare=0.06, glare_threshold=1.5, sat=0.95, sharpen=0.05), filter_width=1.0,
        desk="metal_office_desk", desk_height=None, desk_color=(0.88, 0.88, 0.86, 0.75), desk_spots=0.6,
        kb_from_front=0.26,                       # m from the desk's front edge to the keyboard's centre
        props=[("planter_pot_clay", None, -0.90, 0.30, 0, 0.14, False),
               ("@pot_soil", None, -0.90, 0.30, 0, None, False, dict(z=0.112, on=True)),
               ("calathea_orbifolia_01", "calathea_orbifolia_01_b", -0.90, 0.30, 110, 0.32, False, dict(z=0.10, on=True)),
               ("office_notepads", "office_notepads_a4_stack", 0.78, 0.08, 10, None, False, dict(tint=(1.0, 0.93, 0.78), grime=0.6, page=("notepad_page.jpg", 0.205, 0.285, 0.010))),
               ("stationery_supplies", "stationery_supplies_pen_fancy", 0.76, 0.06, 70, None, True, dict(z=0.011, on=True, grip=("auto", 0.12, 0.40, 0.35))),
               ("stationery_supplies", "stationery_supplies_pencil_new_a", 0.84, 0.28, 12, None, True, dict(grip=("auto", 0.12, 0.40, 0.35))),
               ("stationery_supplies", "stationery_supplies_pencil_used", 0.86, 0.31, -8, None, True, dict(grip=("auto", 0.12, 0.45, 0.45))),
               ("stationery_supplies", "stationery_supplies_pen_red", -0.40, -0.11, 20, None, True, dict(grip=("auto", 0.12, 0.40, 0.35))),
               ("@clips", None, 0.56, -0.03, 0, None, False),
               ("@puzzle_cube", None, -0.58, 0.17, 22, None, False),
               ("@mug_dark", None, -0.52, 0.03, 140, None, False),
               ("vintage_stapler", None, -0.70, 0.02, 20, None, False, dict(scale=0.62, grime=0.55)),
               ("stationery_supplies", "stationery_supplies_eraser", 0.68, 0.30, 30, None, False, dict(grime=0.8)),
               ("@usb_hub", None, -0.39, 0.13, 6, None, False, dict(cable=dict(dx=-0.17))),
               ("rubber_duck_toy", None, 0.56, 0.24, -30, 0.065, False, dict(hsv=(0.545, 1.3, 0.6, 0.3))),
               ("planter_pot_clay", None, -1.18, 0.46, 0, 0.42, False, dict(floor=True)),
               ("pachira_aquatica_01", ("pachira_aquatica_01_bark_d", "pachira_aquatica_01_leaves_d"), -1.18, 0.46, 30, 1.60,
                False, dict(floor=True, z=0.30))],
        desk_mat=dict(w=0.76, d=0.34, x=0.06, y=0.0, image="mat_topo.jpg", rough=0.95),
        wall=dict(color=(0.56, 0.54, 0.50), texture=dict(id="painted_plaster_wall", tile=2.0, tint=(1.15, 1.12, 1.08), bump=0.6),
                  items=[
            dict(kind="board", x=-0.40, z=0.63, w=0.80, h=0.40,
                 loose_pins=[(0.33, 0.165, (0.85, 0.1, 0.1)), (0.345, 0.15, (0.1, 0.3, 0.85)), (-0.36, -0.17, (0.95, 0.8, 0.1)),
                             (0.15, -0.16, (0.1, 0.6, 0.2)), (-0.02, 0.17, (0.85, 0.1, 0.1))], sheets=[
                dict(img="paper_sprint.jpg", x=-0.29, z=0.13, w=0.16, rot=-3, pin=(0.85, 0.1, 0.1)),
                dict(img="print_pcb_rev33.jpg", x=-0.08, z=0.14, w=0.20, rot=3, pin=(0.1, 0.3, 0.85)),
                dict(img="print_stems.jpg", x=0.13, z=0.14, w=0.16, rot=-4, pin=(0.95, 0.8, 0.1)),
                dict(img="print_pcb_split42.jpg", x=0.30, z=0.12, w=0.13, rot=5, pin=(0.1, 0.6, 0.2)),
                dict(img="paper_schematic.jpg", x=-0.10, z=-0.03, w=0.19, rot=-2, pin=(0.85, 0.1, 0.1)),
                dict(img="print_rgb.jpg", x=0.10, z=-0.02, w=0.15, rot=2, pin=(0.1, 0.3, 0.85)),
                dict(img="print_emoji.jpg", x=0.27, z=-0.04, w=0.10, rot=-6, pin=(0.85, 0.1, 0.1)),
                dict(img="sticky_yellow.jpg", x=-0.30, z=-0.08, w=0.076, rot=6, pin=(0.95, 0.8, 0.1))]),
            dict(kind="shelf", x=0.36, z=0.56, w=0.62, d=0.19, books=True, lean=10,
                 pins=[(0.16, -0.06, (0.85, 0.1, 0.1), 30), (0.19, -0.075, (0.1, 0.3, 0.85), 110), (0.05, -0.07, (0.95, 0.8, 0.1), 200)], things=[
                ("standing_picture_frame_01", None, 0.10, 0.16, -8),
                ("potted_plant_04", None, 0.24, 0.15, 0)]),
            dict(kind="sheet", img="paper_month.jpg", x=0.86, z=0.76, w=0.28, rot=0, pin=(0.2, 0.2, 0.22), pages=8, bow=0.006, dents=0.25),
            dict(kind="sheet", img="print_halves.jpg", x=0.94, z=0.37, w=0.14, rot=-3, bow=0.0, pin=(0.1, 0.3, 0.85)),
            dict(kind="sheet", img="sticky_blue.jpg", x=0.90, z=0.22, w=0.076, rot=3, bow=0.008)]),
        monitor=dict(style="dual", y=0.42, inches=30, finish="black",
                     screens=["screen_sheet.jpg", "screen_mail.jpg"], gap=0.022,
                     notes=[(0, -0.36, "sticky_green.jpg", -4), (0, 0.12, "sticky_wide.jpg", 2, 0.076),
                            (1, 0.28, "sticky_pink.jpg", -3, 0.038)], screen_rough=0.06, cables=True),
        mouse=dict(x=0.32, y=0.0, turn=-6, wired=True, color=(0.016, 0.016, 0.017), side=(0.008, 0.008, 0.009), rough=0.85, coat=0.0, specular=0.2),
        lights=[dict(at=(0.1, 0.1, 1.5), size=(1.2, 0.6), energy=40, color=(1.0, 0.80, 0.55)),
                dict(at=(-0.1, -1.5, 1.75), size=(1.2, 0.3), energy=90, color=(1.0, 0.84, 0.62)),
                dict(at=(1.35, -0.1, 0.95), size=(0.9, 0.9), energy=70, color=(1.0, 0.93, 0.84), rot=(0, 60, 0))],
        glints=[dict(at=(0.30, -2.5, 0.78), size=(1.1, 0.07), strength=5.0, color=(1.0, 0.88, 0.70)),
                dict(at=(1.15, -2.4, 0.66), size=(0.6, 0.05), strength=3.0, color=(1.0, 0.92, 0.80))],
        camera=dict(distance=2.6, elev=13, azim=-10, lens=52, fstop=11.0, aim_y=0.16, aim_z=0.33)),
    "front_desk": dict(
        hdri="cyclorama_hard_light", hdri_turn=90, hdri_strength=1.1, exposure=0.35,
        room=dict(wall_y=3.2, wall=(0.92, 0.92, 0.90), floor=(0.85, 0.84, 0.82),
                  window=dict(x=(0.95, 2.9), z=(0.45, 2.55), panes=4, strength=2.5),
                  things=[("planter_pot_clay", None, 0.55, 2.85, 0, 0.45), ("Sofa_01", None, -1.45, 2.78, 180, 0.85),
                          ("pachira_aquatica_01", ("pachira_aquatica_01_bark_d", "pachira_aquatica_01_leaves_d"), 0.55, 2.85, 30, 1.75, 0.32)],
                  items=[dict(kind="frame", img="art_arches.jpg", x=-1.45, z=1.22, w=0.90, border=0.03),
                         dict(kind="clock", x=-0.55, z=1.27, r=0.12)]),
        look="AgX - Punchy", sun=dict(**{"from": (-0.8, 0.6, 0.7)}, strength=3.0, angle=1.5),
        post=dict(vignette=0.32, glare=0.05, glare_threshold=1.5, sat=0.95, sharpen=0.05), filter_width=1.0,
        lights=[dict(at=(0.0, 0.0, 1.5), size=(1.2, 0.6), energy=45, color=(1.0, 0.82, 0.58)),
                dict(at=(-0.1, -1.5, 1.5), size=(1.2, 0.3), energy=70, color=(1.0, 0.86, 0.66))],
        desk="@counter", desk_height=None, desk_spots=0.5,
        counter_wood=dict(id="oak_veneer_01", tile=1.83, tint=(0.80, 0.74, 0.68), bump=0.5),
        counter_glass=dict(t=0.008, density=0.6, tint=(0.975, 1.0, 0.993), edge=(0.66, 0.98, 0.92)),
        counter_dents=0.2,
        kb_from_front=0.26,
        grommet=dict(r=0.03, inset=0.07),
        screen_items=[
            dict(kind="sheet", img="paper_rota.jpg", x=-0.62, z=0.315, w=0.27, rot=-1, bow=0.002, tape=True),
            dict(kind="sheet", img="paper_phone.jpg", x=-0.41, z=0.31, w=0.11, rot=2, bow=0.002, tape=True),
            dict(kind="sheet", img="paper_desk_month.jpg", x=0.42, z=0.31, w=0.15, rot=0, bow=0.003, pages=5, pin=(0.85, 0.85, 0.87)),
            dict(kind="sheet", img="paper_wifi.jpg", x=0.58, z=0.27, w=0.12, rot=-3, bow=0.001, tape=True),
            dict(kind="sheet", img="sticky_courier.jpg", x=-0.40, z=0.13, w=0.07, rot=5, bow=0.006)],
        props=[("@white_pot", None, 0.66, 0.26, 0, None, False, dict(wear=[      # specks, watering tide marks,
                   dict(spots=0.7, scale=70, lo=0.58, tint=(0.55, 0.50, 0.42), detail=4.0),   # a darker foot
                   dict(spots=0.3, scale=8, lo=0.52, tint=(0.86, 0.81, 0.72)), dict(band=("Z", 0.0, 0.12), amount=0.25)])),
               ("anthurium_botany_01", "anthurium_botany_01_b", 0.66, 0.26, 200, 0.30, False, dict(z=0.112, on=True, matte=0.6)),
               ("binder_notebook", "binder_notebook_closed", -0.52, 0.02, 8, None, False, dict(grime=0.6, wear=[dict(spots=0.4, scale=15, lo=0.58)])),
               ("stationery_supplies", "stationery_supplies_pen_fancy", -0.40, 0.14, 80, None, True, dict(grip=("auto", 0.12, 0.40, 0.35), wear=[dict(spots=0.3, scale=60, lo=0.62)])),
               ("office_notepads", "office_notepads_sticky_stack", -0.33, -0.10, -12, None, False, dict(grime=0.4, wear=[dict(spots=0.3, scale=12, lo=0.6, tint=(0.85, 0.80, 0.70))])),
               ("@badges", None, 0.52, -0.04, 10, None, False, dict(wear=[dict(spots=0.3, scale=20, lo=0.6), dict(edges=0.4)])),
               ("@name_card", None, -0.55, 0.655, 4, None, False, dict(z=0.37, on=True)),     # on the ledge top
               ("@nfc_reader", None, 0.42, 0.705, 186, None, False, dict(z=0.37, on=True,   # on the ledge, for visitors
                cable=dict(ledge_hole=0.355, r=0.0017),
                wear=[dict(spots=0.3, scale=90, lo=0.66, tint=(0.25, 0.25, 0.26), mode="MIX", detail=4.0)])),
               ("@mug", None, 0.56, 0.10, 40, None, False, dict(wear=[dict(band=("Z", 0.90, 1.0), amount=0.2),   # a coffee
                   dict(spots=0.6, scale=45, lo=0.60, tint=(0.68, 0.52, 0.38), detail=4.0)]))],                       # ring, drips
        desk_mat=dict(w=0.80, d=0.34, x=0.06, y=0.0, color=(0.10, 0.06, 0.04), rough=0.55, coat=0.1,
                      wear=[dict(spots=0.5, scale=4, lo=0.5, tint=(0.78, 0.74, 0.70)), dict(edges=0.5),
                            dict(spots=0.3, scale=3, lo=0.55, tint=(0.17, 0.12, 0.09), mode="MIX")]),
        monitor=dict(style="stand", y=0.40, x=-0.02, inches=27, finish="black", screen="screen_reception2.jpg", glow=1.4,
                     wear=[dict(spots=0.5, scale=140, lo=0.65, tint=(0.14, 0.14, 0.14), mode="MIX", detail=4.0)],
                     screen_rough=0.06, cables=True,
                     notes=[(0.38, "sticky_yellow.jpg", 3, 0.051), (-0.30, "sticky_blue.jpg", -2, 0.038)]),
        mouse=dict(x=0.34, y=0.0, turn=-4, wired=True, shape="ambi", color=(0.62, 0.63, 0.65), side=(0.05, 0.05, 0.055),
                   rough=0.4, coat=0.3,
                   wear=[dict(band=("Y", 0.0, 0.5), amount=0.15), dict(spots=0.25, scale=110, lo=0.68, tint=(0.70, 0.68, 0.64), detail=4.0)]),
        glints=[dict(at=(0.25, -2.5, 0.75), size=(1.0, 0.07), strength=4.0, color=(1.0, 0.88, 0.70))]
               + [dict(at=(-0.85 + 0.45 * k, -2.2, 0.58), size=(0.40, 0.85), strength=3.5, color=(0.92, 0.96, 1.0), flat=True)
                  for k in range(3)],     # a window behind the camera, three panes, where the screen's reflected rays go
        camera=dict(distance=2.5, elev=13, azim=8, lens=52, fstop=11.0, aim_y=0.16, aim_z=0.22)),
    "planning": dict(                                  # an architect's desk in a planning office
        hdri="studio_country_hall", hdri_turn=60, hdri_strength=0.7, exposure=0.35,
        look="AgX - Punchy", sun=dict(**{"from": (-1.0, -0.3, 0.6)}, strength=3.5, angle=1.5),
        post=dict(vignette=0.35, glare=0.06, glare_threshold=1.5, sat=0.95, sharpen=0.05), filter_width=1.0,
        lights=[dict(at=(0.1, 0.1, 1.5), size=(1.2, 0.6), energy=40, color=(1.0, 0.82, 0.58)),
                dict(at=(-0.1, -1.5, 1.75), size=(1.2, 0.3), energy=80, color=(1.0, 0.86, 0.66))],
        desk="@industrial_desk", desk_wood=dict(id="plywood", tile=1.22, tint=(1.0, 0.97, 0.92), bump=0.4),
        desk_dents=0.10, desk_spots=0.5,
        kb_from_front=0.24,
        wall=dict(color=(0.62, 0.61, 0.58), texture=dict(id="concrete_wall_008", tile=2.4, tint=(1.12, 1.10, 1.06), bump=0.5),
                  items=[
            dict(kind="board", x=-0.46, z=0.54, w=0.86, h=0.44,
                 loose_pins=[(0.36, 0.17, (0.85, 0.1, 0.1)), (-0.38, -0.18, (0.1, 0.3, 0.85)), (0.18, -0.18, (0.95, 0.8, 0.1))], sheets=[
                dict(img="paper_elevation.jpg", x=-0.22, z=0.15, w=0.30, rot=-2, pin=(0.85, 0.1, 0.1)),
                dict(img="paper_section.jpg", x=0.14, z=0.15, w=0.24, rot=3, pin=(0.1, 0.3, 0.85)),
                dict(img="paper_site.jpg", x=0.33, z=0.13, w=0.12, rot=-4, pin=(0.95, 0.8, 0.1)),
                dict(img="print_halves.jpg", x=-0.06, z=-0.05, w=0.14, rot=2, pin=(0.1, 0.6, 0.2)),
                dict(img="sticky_orange.jpg", x=-0.32, z=-0.07, w=0.076, rot=5, pin=(0.85, 0.1, 0.1))]),
            dict(kind="frame", img="photo_building.jpg", x=0.50, z=0.60, w=0.36, border=0.025),
            dict(kind="sheet", img="sticky_blue.jpg", x=0.82, z=0.34, w=0.076, rot=-3, bow=0.008)]),
        props=[("potted_plant_02", None, -0.80, 0.30, 0, 0.38, False, dict(matte=0.6, wear=[
                    dict(spots=0.5, scale=60, lo=0.6, tint=(0.62, 0.52, 0.42), detail=4.0)])),
               ("binder_notebook", "binder_notebook_closed", -0.62, 0.10, 15, None, False, dict(grime=0.6, wear=[dict(spots=0.4, scale=15, lo=0.58)])),
               ("@mug", None, -0.38, 0.27, 30, None, False, dict(wear=[dict(band=("Z", 0.90, 1.0), amount=0.2),
                   dict(spots=0.6, scale=45, lo=0.60, tint=(0.68, 0.52, 0.38), detail=4.0)])),
               ("@set_square", None, -0.60, -0.12, 15, None, False, dict(wear=[dict(spots=0.3, scale=40, lo=0.62)])),
               ("stationery_supplies", "stationery_supplies_pencil_used", -0.38, -0.17, 40, None, True,
                dict(grip=("auto", 0.12, 0.40, 0.35))),
               ("stationery_supplies", "stationery_supplies_eraser", -0.30, -0.08, -10, None, False, dict(grime=0.5)),
               ("measuring_tape_01", None, -0.80, -0.10, 60, None, False, dict(wear=[dict(edges=0.5), dict(spots=0.3, scale=50, lo=0.62)])),
               ("office_notepads", "office_notepads_a4_stack", 0.72, 0.28, -8, None, False, dict(grime=0.4, matte=0.8)),
               ("office_notepads", "office_notepads_a4_b", 0.66, -0.02, 14, None, False, dict(matte=0.8, wear=[dict(spots=0.3, scale=12, lo=0.6)])),
               ("round_spectacles", None, 0.62, -0.04, 20, None, False, dict(on=True, z=0.002)),
               ("stationery_supplies", "stationery_supplies_pencil_new_a", 0.74, 0.04, 30, None, True, dict(on=True, z=0.002)),
               ("@ruler", None, 0.86, 0.12, 84, None, False, dict(wear=[dict(spots=0.3, scale=80, lo=0.64)])),
               ("stationery_supplies", "stationery_supplies_pencilcup", 0.48, 0.38, 0, None, False, dict(grime=0.4))],
        desk_mat=dict(w=0.90, d=0.36, x=0.06, y=0.0, image="mat_blue.jpg", rough=0.75,
                      wear=[dict(spots=0.4, scale=4, lo=0.5, tint=(0.80, 0.78, 0.74)), dict(edges=0.4)]),
        monitor=dict(style="ultrawide", y=0.42, x=-0.06, inches=34, screen="screen_plan2.jpg", turn=4, glow=1.2,
                     screen_rough=0.06, cables=True,
                     wear=[dict(spots=0.5, scale=140, lo=0.65, tint=(0.75, 0.75, 0.76), mode="MIX", detail=4.0)],
                     notes=[(0.36, "sticky_pink.jpg", 3, 0.045)]),
        mouse=dict(x=0.36, y=0.02, turn=-8, wired=True, color=(0.016, 0.016, 0.017), side=(0.008, 0.008, 0.009), rough=0.85,
                   coat=0.0, specular=0.2, wear=[dict(band=("Y", 0.0, 0.5), amount=0.2)]),
        glints=[dict(at=(0.25, -2.5, 0.75), size=(1.0, 0.07), strength=4.0, color=(1.0, 0.88, 0.70))]
               + [dict(at=(-0.85 + 0.45 * k, -2.2, 0.58), size=(0.40, 0.85), strength=3.5, color=(0.92, 0.96, 1.0), flat=True)
                  for k in range(3)],
        camera=dict(distance=2.35, elev=30, azim=-8, lens=45, fstop=11.0, aim_y=0.14, aim_z=0.08)),
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
