"""A close-up of a block of the left half's keys, lit from a legend atlas.

    blender -b render/out/hero.blend --python render/closeup_view.py -- \
        out.png samples width atlas fx fy dist elev yaw lens [fstop]

`atlas` names textures/<atlas>.png/.json (export_screens.py, overlay_atlas.py);
fx, fy place the camera target as fractions of the framed half's display decals'
bounding box (x from the left, y from the front); dist is in metres, elev and
yaw in degrees, lens in mm, fstop > 0 turns on depth of field. PK_STRENGTH sets
the legends' emission (6 saturates to white at close range; 3 keeps the
LIT_TINT visible), PK_STATUS the status-panel suffix (_l1), PK_BORDER a crop, PK_SIDE=right
frames the right half, PK_CLEAR_CASE=1 makes the case clear in the studio,
PK_COVE_RGB="r,g,b" colours the studio floor, PK_SPLAY the left
half's turn (default -2; 0 squares its columns to the frame), PK_SPLAY_RIGHT
the right half's (default -9), PK_BLOOM="threshold,mix"
a compositor fog glow around bright pixels, PK_PANEL_FLOOR="r,g,b"
(screens.py) gives every key panel a faint glow of that colour, PK_LIGHT scales
the studio lights (0.15 is a dim room, for the docs' idle close-up).
PK_RGB="h0,h1" is the night shot: the studio off, the case clear, and every
per-key LED lit along a hue gradient from h0 (left) to h1 (right), in degrees;
PK_LED sets each LED's power in W, PK_GLOW the caps' glow and
PK_CASE_GLOW="h0,h1,strength" the clear case's own gradient, and
PK_FALLOFF="mm,strength" adds a glow that fades over that distance from each
cap's own LED (rgb.py). PK_POWER_LED=<W> lights the three indicator LEDs (D1 red, D5 green,
D6 yellow) on the back of both halves; PK_CASE_LEDS=<strength> adds their
light to the clear case's edges.
PK_FOCUS="fx,fy" moves the focus to
another point of the displays' box. PK_PROFILE re-poses the caps to
a stem profile: stepped, stepped-uniform or curved, PK_DENT="depth,rim" (mm) dents
the cap tops into a shallow tray with a soft rim, and PK_DISH=<mm> fakes a
dish in the shading normal only (profile.py).
The docs' overlays close-up: screens_gimp_l1 0.47 0.6 0.15 52 0 55, strength 3.
"""
import bpy, sys, os, math, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import materials, lighting, screens, studio, textured_parts, bridge_cable, rgb, profile
a = sys.argv[sys.argv.index("--") + 1:]
out, samples, width, atlas = os.path.abspath(a[0]), int(a[1]), int(a[2]), a[3]
fx, fy, dist, elev, yaw, lens = map(float, a[4:10])
aperture = float(a[10]) if len(a) > 10 else 0.0


sc = bpy.context.scene
materials.tag(bpy)
SIDE = os.environ.get("PK_SIDE", "left")           # PK_SIDE=right frames the right half
OTHER = "right" if SIDE == "left" else "left"
root = bpy.data.objects[f"split72_{SIDE}.wrl"]
board = os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{SIDE}.kicad_pcb")
textured_parts.add(root, textured_parts.board_keys(board))
materials.apply(bpy)
PROFILE = os.environ.get("PK_PROFILE")
print("lit", screens.keys(root, board, SIDE, strength=float(os.environ.get("PK_STRENGTH", 6.0)), atlas_name=atlas), screens.status(root, SIDE, suffix=os.environ.get("PK_STATUS", "")))
if os.environ.get("PK_DENT"):                     # "depth_mm[,rim_mm]": a real dented top
    _d = [float(v) for v in os.environ["PK_DENT"].split(",")]
    profile.dent(root, board, *_d)
if os.environ.get("PK_DISH"):
    profile.dish(root, board, float(os.environ["PK_DISH"]))
if PROFILE:
    profile.apply(root, board, PROFILE)
materials.scene_settings(sc)
tgt = bpy.data.objects.get("target")
RGB = os.environ.get("PK_RGB")
if RGB:
    rgb.night(sc)
    rgb.clear_case()
else:
    lighting.studio(sc, tgt, float(os.environ.get("PK_LIGHT", 1.0)))
    if os.environ.get("PK_CLEAR_CASE"):             # the clear printed case of the docs' language photos
        rgb.clear_case()
studio.splay(float(os.environ.get("PK_SPLAY", -2)),          # PK_SPLAY=0: columns square to the frame
             right=float(os.environ.get("PK_SPLAY_RIGHT", -9)))  # the same for the right half
other = bpy.data.objects[f"split72_{OTHER}.wrl"]
for o in [other] + list(other.children_recursive):
    o.hide_render = True
bridge_cable.remove()
bpy.context.view_layer.update()
dec = next(o for o in root.children_recursive if o.name.endswith("display decals"))
ws = [dec.matrix_world @ v.co for v in dec.data.vertices]
lo = mathutils.Vector([min(w[i] for w in ws) for i in range(3)])
hi = mathutils.Vector([max(w[i] for w in ws) for i in range(3)])
print("decals bbox", lo, hi)
tgt.location = (lo.x + fx * (hi.x - lo.x), lo.y + fy * (hi.y - lo.y), hi.z)
cam = sc.camera
cam.data.lens = lens
cam.data.clip_start = 0.005          # the default 0.1 m cuts the front keys at this distance
e, y = math.radians(elev), math.radians(yaw)
cam.location = tgt.location + mathutils.Vector((dist * math.cos(e) * math.sin(y), -dist * math.cos(e) * math.cos(y), dist * math.sin(e)))
cam.data.dof.use_dof = aperture > 0
if aperture > 0:
    cam.data.dof.focus_object = tgt
    foc = os.environ.get("PK_FOCUS")              # "fx,fy": focus on that display point, not the target
    if foc:
        ffx, ffy = (float(v) for v in foc.split(","))
        fo = bpy.data.objects.new("focus", None)
        sc.collection.objects.link(fo)
        fo.location = (lo.x + ffx * (hi.x - lo.x), lo.y + ffy * (hi.y - lo.y), hi.z)
        cam.data.dof.focus_object = fo
    cam.data.dof.aperture_fstop = aperture
if RGB:
    print("leds", rgb.leds(root, board, [float(h) for h in RGB.split(",")],
                           energy=float(os.environ.get("PK_LED", 0.02))))
    x0, x1 = rgb.led_span(root, board)
    hues = [float(h) for h in RGB.split(",")]
    if float(os.environ.get("PK_GLOW", 300)) > 0:
        rgb.glow("keycap glass", x0, x1, hues, float(os.environ.get("PK_GLOW", 300)))
    fall = os.environ.get("PK_FALLOFF")           # "mm,strength": each cap brighter by its own LED
    if fall:
        r_mm, fs = (float(v) for v in fall.split(","))
        rgb.glow_from_leds(root, board, "keycap glass", hues, r_mm / 1000, fs,
                           z=float(os.environ.get("PK_LED_Z", 8.0)))
    # debugging: PK_HIDE_ROLES="plate aluminium,diffuser resin". ⚠️ Drop the empty
    # names: "".split(",") is [""], which hid every untagged object (the plate's
    # silkscreen, most of the PCB parts) whenever the variable was unset.
    hide = [r for r in os.environ.get("PK_HIDE_ROLES", "").split(",") if r]
    for o in root.children_recursive:
        if o.active_material and o.active_material.get("pk_role") in hide:
            o.hide_render = True
    if os.environ.get("PK_EMIT"):                 # physically lit: emissive LED squares
        print("emitters", rgb.emitters(root, board, hues, float(os.environ["PK_EMIT"]),
                                       z=float(os.environ.get("PK_EMIT_Z", 4.4))))
        rgb.clear_diffuser(float(os.environ.get("PK_DIFFUSER_ROUGH", 0.15)))
    flex = os.environ.get("PK_FLEX")              # "dim,roughness": a clear display flex, copper traces shining
    if flex:
        fd, fr = (float(v) for v in flex.split(","))
        rgb.clear_flex(fd, fr)
    if os.environ.get("PK_POWER_LED"):            # W: the red, green and yellow indicator LEDs of both halves
        for side in ("left", "right"):
            sb = os.path.join(textured_parts.REPO, "poly_kybd", f"poly_kybd_split72_{side}.kicad_pcb")
            print("indicators", side, rgb.indicator_leds(bpy.data.objects[f"split72_{side}.wrl"], sb,
                                                         float(os.environ["PK_POWER_LED"])))
            if os.environ.get("PK_CASE_LEDS"):        # strength of the indicators' light in the clear case
                rgb.case_indicator_glow(bpy.data.objects[f"split72_{side}.wrl"], sb, float(os.environ["PK_CASE_LEDS"]))
    case = os.environ.get("PK_CASE_GLOW")          # "h0,h1,strength": light caught in the clear case
    if case:
        c0, c1, cs = (float(v) for v in case.split(","))
        rgb.glow("case PLA", x0, x1, (c0, c1), cs)
else:
    cove = os.environ.get("PK_COVE_RGB")           # "r,g,b": a coloured floor (the language photos' purple mat)
    studio.cove(sc, colour=tuple(float(v) for v in cove.split(",")) if cove else (0.9, 0.9, 0.9))
    studio.flag(sc)
    studio.white_look(sc)
sc.cycles.filter_width = 1.0
sc.cycles.samples = samples
sc.render.resolution_x, sc.render.resolution_y = width, int(round(width * 9 / 16))
sc.render.resolution_percentage = 100
sc.render.filepath = out
border = os.environ.get("PK_BORDER")
if border:
    x0, y0, x1, y1 = (float(v) for v in border.split(","))
    sc.render.use_border, sc.render.use_crop_to_border = True, True
    sc.render.border_min_x, sc.render.border_max_x = x0, x1
    sc.render.border_min_y, sc.render.border_max_y = 1 - y1, 1 - y0
bloom = os.environ.get("PK_BLOOM")               # "threshold,mix": a soft glow around the lit legends
if bloom:
    th, mix = (float(v) for v in bloom.split(","))
    sc.use_nodes = True
    nt = sc.node_tree
    rl = nt.nodes.get("Render Layers") or nt.nodes.new("CompositorNodeRLayers")
    comp = nt.nodes.get("Composite") or nt.nodes.new("CompositorNodeComposite")
    g = nt.nodes.new("CompositorNodeGlare")
    g.glare_type, g.quality, g.threshold, g.mix, g.size = "FOG_GLOW", "HIGH", th, mix, 8
    nt.links.new(rl.outputs["Image"], g.inputs["Image"])
    nt.links.new(g.outputs["Image"], comp.inputs["Image"])
bpy.ops.render.render(write_still=True)
