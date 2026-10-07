"""Material rules shared by blender_scene.py (both halves) and key_scene.py (one key).

Tune materials HERE: key_scene.py renders one key in about a minute, and the
full scene picks up the same table, so a look settled on the key carries over.

The VRML importer gives every shape a Principled BSDF holding the model's
diffuse colour and transparency. Each ROLES entry matches on that source colour
(within TOL per channel) and sets Principled inputs. The first match wins;
unmatched materials keep their colour with roughness DEFAULT_ROUGHNESS.
"""
TOL = 0.001          # the source colours are exact; 0.098 (switch) vs 0.1 (display) differ by 0.002

# (role, source rgb, transparent in the source?, Principled BSDF inputs)
ROLES = [
    # clear outer keycap (outercap1u*.wrl: 0.9 grey, transparency 0.7)
    ("keycap glass", (0.9, 0.9, 0.9), True, {
        "Base Color": (1.0, 1.0, 1.0, 1), "Transmission Weight": 1.0,
        "Roughness": 0.0, "IOR": 1.49, "Alpha": 1.0}),
    # main PCB solder mask (stackup green, transparency 0.17 in the export)
    ("solder mask", (0.078, 0.2, 0.141), True, {
        "Base Color": (0.02, 0.09, 0.05, 1), "Roughness": 0.25, "Alpha": 1.0,
        "Transmission Weight": 0.0}),
    # aluminium switch plate (gen_plates.py writes 0.58 0.59 0.61)
    ("plate aluminium", (0.58, 0.59, 0.61), False, {
        "Base Color": (0.80, 0.81, 0.83, 1), "Metallic": 1.0, "Roughness": 0.28}),
    # printed case, display holder and lids (stl_to_wrl.py default 0.35 0.35 0.37)
    ("case PLA", (0.35, 0.35, 0.37), False, {
        "Base Color": (0.018, 0.018, 0.02, 1), "Roughness": 0.6,
        # matte print: less specular, so on a white floor the case does not
        # mirror the room into a mid grey
        "Specular IOR Level": 0.2}),
    # keycap stem (keycap_stem_r7*.wrl)
    ("stem", (0.3, 0.3, 0.3), False, {
        # the real stem is the case's dark grey-black; seen through the clear
        # cap it sets how dark the whole keycap reads
        "Base Color": (0.018, 0.018, 0.02, 1), "Roughness": 0.45,
        "Specular IOR Level": 0.3}),
    # keycap OLED face (keycap_display.wrl)
    ("display face", (0.1, 0.1, 0.1), False, {
        "Base Color": (0.01, 0.01, 0.012, 1), "Roughness": 0.05, "Coat Weight": 1.0}),
    # display flex cable (keycap_display_cable.wrl): polyimide
    ("flex cable", (0.7, 0.3, 0.1), False, {
        "Base Color": (0.65, 0.33, 0.06, 1), "Roughness": 0.35,
        "Transmission Weight": 0.3}),
    # MX switch and Kailh socket housings
    # Tecsee Medium/Middle tactile: a translucent "banana" yellow bottom
    # housing (HPE / nylon) ...
    ("switch housing", (0.098, 0.098, 0.098), False, {
        "Base Color": (0.95, 0.75, 0.22, 1), "Transmission Weight": 0.35,
        "Roughness": 0.3, "IOR": 1.5}),
    # the MX model's top housing is a separate part, exported pure white. On
    # the Tecsee switch it is a MILKY translucent plastic, whitish with a
    # trace of yellow, not the bottom's banana yellow: transmissive but
    # frosted, so light passes and nothing behind it reads sharp. 0.75 at
    # Fully transmissive but strongly FROSTED is what reads milky: the
    # internals behind it (the yellow stem, the bottom housing's posts that
    # reach up to 9.6 mm inside it) only blur through. Partial transmission
    # (0.75..0.95) read as a solid or a second plastic under it; little frost
    # (0.08..0.28) read as clear glass; subsurface tinted it blue-grey
    ("switch top housing", (1.0, 1.0, 1.0), False, {
        "Base Color": (0.99, 0.97, 0.90, 1), "Transmission Weight": 1.0,
        "Roughness": 0.8, "IOR": 1.5}),
    # ... and an opaque cheese-yellow POM stem
    ("switch stem", (0.533, 0.235, 0.0), False, {
        "Base Color": (0.93, 0.70, 0.17, 1), "Roughness": 0.4}),
    # Kailh socket contacts
    ("socket contacts", (0.957, 0.898, 0.655), False, {
        "Base Color": (0.95, 0.78, 0.40, 1), "Metallic": 1.0, "Roughness": 0.25}),
    # status display module glass (gen_inserts.py): black glass, glossy
    ("oled glass", (0.06, 0.06, 0.07), False, {
        "Base Color": (0.006, 0.006, 0.008, 1), "Roughness": 0.08}),
    # status display active area (gen_inserts.py lcd): unlit OLED, black and glossy
    ("status lcd", (0.01, 0.01, 0.015), False, {
        "Base Color": (0.002, 0.002, 0.003, 1), "Roughness": 0.06}),
    # LED diffuser frame (gen_inserts.py DIFFUSER): frosted clear resin, so
    # each diffuser reads as a milky plug beside its switch
    ("diffuser resin", (0.85, 0.86, 0.88), False, {
        "Base Color": (0.92, 0.93, 0.95, 1), "Transmission Weight": 0.85,
        "Roughness": 0.45, "IOR": 1.5}),
    # M3 case screws (gen_models.py STEEL): dark silver metal
    ("screw steel", (0.62, 0.63, 0.66), False, {
        "Base Color": (0.40, 0.40, 0.42, 1), "Metallic": 1.0, "Roughness": 0.32}),
]
DEFAULT_ROUGHNESS = 0.3

# The key displays' glass: the textured decal (textured_parts.py) and the lit
# legends over it (screens.py). Glossy, but a polished coat on top mirrored
# the white studio and read as bright, metallic glass; without the coat, a
# little rougher and with less specular it stays dark like the real panel.
DISPLAY_GLASS = {"Roughness": 0.16, "Coat Weight": 0.0, "Specular IOR Level": 0.25}
RIM_MASK = "display_rim.png"        # gen_textures.display_rim(): a glass coat on the rim
# textured materials whose image stays linked; apply() sets only these inputs
TEXTURED = {"display decal": DISPLAY_GLASS, "flex textured": {}}
FLEX_TRACES = "flex_traces.png"      # gen_textures.flex_drawn(): the copper traces and fingers


def _set(bsdf, name, value):
    aliases = {"Transmission Weight": ("Transmission Weight", "Transmission"),
               "Coat Weight": ("Coat Weight", "Clearcoat")}
    for n in aliases.get(name, (name,)):
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return


def role_of(rgb, alpha=1.0):
    for role, src, _, _ in ROLES:
        if all(abs(a - b) <= TOL for a, b in zip(rgb, src)):
            return role
    return None


def _input(bsdf, *names):
    for n in names:
        if n in bsdf.inputs:
            return bsdf.inputs[n].default_value
    return 0.0


def detect(bsdf):
    """Role from the material's source colour; an older scene had already
    turned the plate metallic (base 0.80), which is the one colour it changed."""
    role = role_of(tuple(bsdf.inputs["Base Color"].default_value[:3]))
    if role is None and bsdf.inputs["Metallic"].default_value > 0.99:
        return "plate aluminium"
    return role


def tag(bpy):
    """Store each material's role ("pk_role") once, from its source colour."""
    for m in bpy.data.materials:
        if m.use_nodes and "pk_role" not in m:
            b = m.node_tree.nodes.get("Principled BSDF")
            if b:
                m["pk_role"] = detect(b) or ""


def scene_settings(sc):
    """Light paths for clear glass: enough transmission and glossy bounces that
    a ray through cap, display glass and back is not cut short (the default 8
    total renders stacked glass milky)."""
    c = sc.cycles
    c.max_bounces, c.transmission_bounces, c.glossy_bounces = 24, 16, 8
    c.transparent_max_bounces, c.diffuse_bounces = 24, 4
    # refractive caustics must stay ON: the displays are lit only through the
    # glass caps, and without them every display renders black
    c.caustics_reflective, c.caustics_refractive = False, True
    c.blur_glossy = 1.0                 # "Filter Glossy": tames the caustic noise
    c.use_denoising = denoiser_available()


def _rim_glass(bpy, m, bsdf):
    """The display glass's rim: clear glass over the substrate's lighter
    underside. The texture carries the underside's colour; the rim mask
    drives Coat Weight, so a glossy glass layer lies over it there and only
    there. (Metallic from the mask made the rim a mirror, not glass.)
    Idempotent."""
    import os
    nt = m.node_tree
    tex = nt.nodes.get("rim mask")
    if tex is None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "rim mask"
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures", RIM_MASK)
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"
    for link in list(nt.links):
        if link.from_node == tex:
            nt.links.remove(link)
    bsdf.inputs["Metallic"].default_value = 0.0
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Coat Weight"])
    _rim_irregular(nt, bsdf, tex)


def _rim_irregular(nt, bsdf, mask):
    """Irregularities along the rim: the substrate's underside is not an even
    film, so its colour varies in brightness and a little in hue, in patches
    about a millimetre across. The noise runs in the decal object's own
    coordinates (mm, all keys in one mesh), so no two keys' rims look alike,
    and the rim mask confines it to the rim. Idempotent."""
    base = next((l.from_socket for l in nt.links
                 if l.to_socket == bsdf.inputs["Base Color"] and l.from_node.name != "rim mix"), None)
    mix = nt.nodes.get("rim mix")
    if mix is None:
        if base is None:
            return
        coord = nt.nodes.new("ShaderNodeTexCoord")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.name = "rim noise"
        noise.inputs["Scale"].default_value = 0.9           # per mm
        noise.inputs["Detail"].default_value = 4.0
        nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
        # noise colour 0..1 per channel -> a factor 0.55..1.45 per channel
        span = nt.nodes.new("ShaderNodeVectorMath")
        span.operation = "MULTIPLY_ADD"
        span.inputs[1].default_value = (0.9, 0.9, 0.9)
        span.inputs[2].default_value = (0.1, 0.1, 0.1)
        nt.links.new(noise.outputs["Color"], span.inputs[0])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.name = "rim mix"
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        nt.links.new(base, mix.inputs["A"])
        nt.links.new(span.outputs["Vector"], mix.inputs["B"])
        nt.links.new(mask.outputs["Color"], mix.inputs["Factor"])
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])


def _flex_traces(bpy, m, bsdf):
    """The flex's copper traces under the polyimide catch the light: the trace
    mask makes them partly metallic and a little glossier than the film
    around them. Idempotent; a missing mask (the photo style) leaves the
    material as it is."""
    import os
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures", FLEX_TRACES)
    if not os.path.exists(path):
        return
    nt = m.node_tree
    tex = nt.nodes.get("trace mask")
    if tex is None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.name = "trace mask"
        metal = nt.nodes.new("ShaderNodeMath")
        metal.name = "trace metal"
        metal.operation = "MULTIPLY"
        metal.inputs[1].default_value = 0.7
        rough = nt.nodes.new("ShaderNodeMapRange")
        rough.name = "trace rough"
        rough.inputs["To Min"].default_value = 0.22
        rough.inputs["To Max"].default_value = 0.12
        nt.links.new(tex.outputs["Color"], metal.inputs[0])
        nt.links.new(tex.outputs["Color"], rough.inputs["Value"])
        nt.links.new(metal.outputs["Value"], bsdf.inputs["Metallic"])
        nt.links.new(rough.outputs["Result"], bsdf.inputs["Roughness"])
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.image.colorspace_settings.name = "Non-Color"


def apply(bpy):
    """Rewrite every imported material by its role; returns {role: count}.

    The role is stored on the material ("pk_role") the first time, so
    applying again to a saved scene (rerender.py) still finds it after the
    colours have been changed."""
    counts = {}
    settings = {role: s for role, _, _, s in ROLES}
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        b = m.node_tree.nodes.get("Principled BSDF")
        if not b:
            continue
        if not m.get("pk_role"):        # untagged, or no role last time: a role added since may match
            m["pk_role"] = detect(b) or ""
        role = m["pk_role"] or None
        counts[role] = counts.get(role, 0) + 1
        if role in TEXTURED:
            for k, v in TEXTURED[role].items():
                _set(b, k, v)
            if role == "display decal":
                _rim_glass(bpy, m, b)
            if role == "flex textured":
                _flex_traces(bpy, m, b)
            continue
        if role is not None and role not in settings:     # textured_parts.py's own
            continue
        if role is None:
            b.inputs["Roughness"].default_value = max(DEFAULT_ROUGHNESS,
                                                      b.inputs["Roughness"].default_value)
            continue
        for k, v in settings[role].items():
            _set(b, k, v)
    return counts


def denoiser_available():
    """OpenImageDenoise is missing from the Ubuntu/Debian Blender package;
    the official builds from blender.org have it."""
    try:
        import _cycles
        return bool(_cycles.with_openimagedenoise)
    except Exception:
        return False
