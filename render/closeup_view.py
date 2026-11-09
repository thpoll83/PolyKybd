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
PK_COVE_RGB="r,g,b" colours the studio floor, PK_MAT_GRID="r,g,b[,lr,lg,lb]" lays a cutting mat
of that colour with a 10 mm grid (lines lr,lg,lb) under the board, PK_STEM_RGB="r,g,b"
recolours the keycap stems and PK_CAP_ROUGH frosts the caps, PK_SPLAY the left
half's turn (default -2; 0 squares its columns to the frame), PK_SPLAY_RIGHT
the right half's (default -9), PK_BLOOM="threshold,mix[,size]"
a compositor fog glow around bright pixels, PK_LIGHT_RGB="r,g,b" tints the studio lights, PK_ROLL=<deg> turns the camera about its view axis, PK_SHEEN="W[,size]" a panel the cap tops mirror, PK_PASSES=<dir> light-group EXRs for a tuning page, PK_PANEL_FLOOR="r,g,b"
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
for _m in bpy.data.materials:                      # PK_STEM_RGB="r,g,b": light stems, so the clear caps read
    _b = _m.node_tree.nodes.get("Principled BSDF") if _m.use_nodes else None   # grey, not black;
    if _b is None:                                 # PK_CAP_ROUGH: a frosted cap surface (0 = clear glass)
        continue
    if _m.get("pk_role") == "stem" and os.environ.get("PK_STEM_RGB"):
        _b.inputs["Base Color"].default_value = (*(float(v) for v in os.environ["PK_STEM_RGB"].split(",")), 1)
    if _m.get("pk_role") == "keycap glass" and os.environ.get("PK_CAP_ROUGH"):
        _b.inputs["Roughness"].default_value = float(os.environ["PK_CAP_ROUGH"])
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
    if os.environ.get("PK_LIGHT_RGB"):             # "r,g,b": tint the studio lights (a warm room light)
        _lc = tuple(float(v) for v in os.environ["PK_LIGHT_RGB"].split(","))
        for _l in [o for o in sc.objects if o.type == "LIGHT"]:
            _l.data.color = _lc
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
if os.environ.get("PK_ROLL"):                       # degrees: turn the camera about its view axis, counter-
    bpy.context.view_layer.update()                # clockwise for positive values (the picture turns the
    _mw = cam.matrix_world.copy()                  # other way); the aim constraint is baked first
    for _c in list(cam.constraints):
        cam.constraints.remove(_c)
    cam.matrix_world = _mw @ mathutils.Matrix.Rotation(math.radians(float(os.environ["PK_ROLL"])), 4, "Z")
sheen = os.environ.get("PK_SHEEN")                 # "strength[,size]": a soft white panel where the flat cap
if sheen:                                          # tops mirror it to the camera (the camera mirrored in the
    _sv = [float(v) for v in sheen.split(",")]     # board plane, 1.6x as far), seen only in reflections: the
    _d = cam.location - tgt.location               # milky sheen of a room light on clear caps
    _p = tgt.location + mathutils.Vector((-_d.x, -_d.y, _d.z)) * 1.6
    _ld = bpy.data.lights.new("cap sheen", "AREA")
    _ld.shape, _ld.size, _ld.size_y = "RECTANGLE", _sv[1] if len(_sv) > 1 else 0.5, _sv[1] if len(_sv) > 1 else 0.5
    _ld.energy = _sv[0]
    _lo = bpy.data.objects.new("cap sheen", _ld)
    sc.collection.objects.link(_lo)
    _lo.location = _p
    _lo.rotation_euler = (tgt.location - _p).to_track_quat("-Z", "Y").to_euler()
    _lo.visible_diffuse = False                    # reflections only: it does not light the scene
    _lo.visible_camera = False
    _caps = bpy.data.collections.new("sheen caps")  # and only the caps see it (light linking): the plate's
    for _o in root.children_recursive:              # aluminium mirrored it as a bright smear
        if _o.type == "MESH" and any(sl.material and sl.material.get("pk_role") == "keycap glass"
                                     for sl in _o.material_slots):
            _caps.objects.link(_o)
    _lo.light_linking.receiver_collection = _caps
    print("sheen caps", len(_caps.objects))
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
    mat_grid = os.environ.get("PK_MAT_GRID")       # "r,g,b": a cutting mat of that colour under the board,
    if mat_grid:                                   # pale lines every 10 mm, wider ones every 50 mm
        _mg = [float(v) for v in mat_grid.split(",")]
        base = tuple(_mg[:3])                      # three more values: the lines' colour
        line_rgb = tuple(_mg[3:6]) if len(_mg) >= 6 else (0.62, 0.68, 0.45)
        bpy.ops.mesh.primitive_plane_add(size=0.8, location=(tgt.location.x, tgt.location.y, 0.0004))
        mat_o = bpy.context.active_object
        mat_o.name = "cutting mat"
        m = bpy.data.materials.new("cutting mat")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = 0.75
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Object"], sep.inputs[0])
        line = None
        for step, half in ((0.010, 0.00025), (0.050, 0.0005)):
            for axis in ("X", "Y"):
                md = nt.nodes.new("ShaderNodeMath"); md.operation = "PINGPONG"; md.inputs[1].default_value = step / 2
                nt.links.new(sep.outputs[axis], md.inputs[0])
                lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = half
                nt.links.new(md.outputs[0], lt.inputs[0])
                if line is None:
                    line = lt
                else:
                    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
                    nt.links.new(line.outputs[0], mx.inputs[0]); nt.links.new(lt.outputs[0], mx.inputs[1])
                    line = mx
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        mix.inputs[6].default_value = (*base, 1); mix.inputs[7].default_value = (*line_rgb, 1)
        nt.links.new(line.outputs[0], mix.inputs["Factor"])
        nt.links.new(mix.outputs[2], b.inputs["Base Color"])
        mat_o.data.materials.append(m)
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
    bv = [float(v) for v in bloom.split(",")]
    th, mix = bv[0], bv[1]
    gsize = int(bv[2]) if len(bv) > 2 else 8      # a third value: the glow's size (6..9, 9 the widest haze)
    sc.use_nodes = True
    nt = sc.node_tree
    rl = nt.nodes.get("Render Layers") or nt.nodes.new("CompositorNodeRLayers")
    comp = nt.nodes.get("Composite") or nt.nodes.new("CompositorNodeComposite")
    g = nt.nodes.new("CompositorNodeGlare")
    g.glare_type, g.quality, g.threshold, g.mix, g.size = "FOG_GLOW", "HIGH", th, mix, gsize
    nt.links.new(rl.outputs["Image"], g.inputs["Image"])
    nt.links.new(g.outputs["Image"], comp.inputs["Image"])
passes = os.environ.get("PK_PASSES")              # a directory: the light split into light groups for
if passes:                                         # a tuning page (studio lights and world, the floor's cove
    vl = sc.view_layers[0]                         # light, the cap sheen, the lit legends), each denoised,
    groups = ("studio", "floor", "sheen", "legends")   # as half-float EXRs, beside the combined image
    for g_ in groups:
        if g_ not in vl.lightgroups:
            vl.lightgroups.add(name=g_)
    for o in sc.objects:
        if o.type == "LIGHT":
            o.lightgroup = "sheen" if o.name == "cap sheen" else ("floor" if o.name == "cove light" else "studio")
        elif o.type == "MESH" and ("lit legends" in o.name or "status" in o.name.lower()):
            o.lightgroup = "legends"
    if sc.world:
        sc.world.lightgroup = "studio"
    vl.cycles.denoising_store_passes = True
    if "mat" not in vl.aovs:                       # a mask of the cutting mat (PK_MAT_GRID), filtered like
        vl.aovs.add().name = "mat"                 # the image, so a page can recolour the mat alone
        vl.aovs["mat"].type = "VALUE"
    _mm = bpy.data.materials.get("cutting mat")
    if _mm:
        _aov = _mm.node_tree.nodes.new("ShaderNodeOutputAOV")
        _aov.name = "mat"                         # (in 4.1 the AOV name is the node's `name`)
        _aov.inputs["Value"].default_value = 1.0
    sc.use_nodes = True
    nt = sc.node_tree
    rl = nt.nodes.get("Render Layers") or nt.nodes.new("CompositorNodeRLayers")
    fo = nt.nodes.new("CompositorNodeOutputFile")
    fo.base_path = passes
    fo.format.file_format, fo.format.color_depth = "OPEN_EXR", "16"
    fo.file_slots.clear()
    for name in ("Image", "mat") + tuple("Combined_" + g_ for g_ in groups):
        fo.file_slots.new(name)
        src = rl.outputs[name]
        # the light group passes are not denoised by Cycles; the legends' pass stays raw, since
        # the denoiser smooths the displays' pixel grid (PK_RASTER) away
        if name.startswith("Combined_") and name != "Combined_legends":
            dn = nt.nodes.new("CompositorNodeDenoise")
            nt.links.new(src, dn.inputs["Image"])
            nt.links.new(rl.outputs["Denoising Normal"], dn.inputs["Normal"])
            nt.links.new(rl.outputs["Denoising Albedo"], dn.inputs["Albedo"])
            src = dn.outputs["Image"]
        nt.links.new(src, fo.inputs[name])
bpy.ops.render.render(write_still=True)
