# Marketing renders of the split72

Two paths, both driven from the KiCad boards in `poly_kybd/`.

## 1. Quick: KiCad's own raytracer

```bash
render/export_boards.sh --png      # also writes render/out/split72_{left,right}_kicad.png
```

`kicad-cli pcb render` takes `--rotate`, `--zoom`, `--perspective`, `--floor`
and `--quality high`. It is good enough for a product shot, but it has no real
glass, no area lights and no camera depth of field.

## 2. Blender (Cycles)

```bash
render/export_boards.sh            # render/out/split72_{left,right}.wrl, ~90 MB each
blender -b --python render/blender_scene.py -- \
    render/out/split72_left.wrl render/out/split72_right.wrl render/out/hero.png 256 1920
```

The arguments after `--` are: left VRML, right VRML, output PNG, Cycles
samples, width in pixels (16:9). The script also saves `hero.blend` next to
the PNG. Open that in the Blender GUI to move the camera, add an HDRI or set up
an animation, for example a turntable on the `piv` empties.

What the script sets up:

- both halves on a dark floor, 5 cm apart and splayed 10°
- three area lights (key, fill, rim) and a 50 mm camera at f/4 with depth of field
- the clear outer keycaps changed to transmissive glass (VRML only carries a
  diffuse colour plus transparency)

### Tuning materials on one key

```bash
blender -b --python render/key_scene.py -- render/out/key.png 64 1000
```

`key_scene.py` builds one 1U key (SW_K_2: switch, socket, stem, display,
flex cable, outer cap) from the model files with the board's own offsets, over
a patch of PCB and of the aluminium plate. It renders in about a minute and
saves `key.blend`. Edit the `ROLES` table in `render/materials.py`; the full
scene uses the same table, so a look settled on the key carries over. Each role
matches the model's source colour exactly (`TOL` 0.001), since the switch
housing (0.098) and the display face (0.1) differ by only 0.002.

```bash
blender -b render/out/key.blend --python render/key_views.py -- render/out/key_views 128 1000
```

⚠️ `photo_view.py` and `topview.py` load the saved `render/out/hero.blend`, and
`textured_parts.add()` keeps the decals and flex cables a saved scene already
has. After changing `poly_kybd/models/flex_cable.py` (or the decal geometry),
rebuild that scene first, from the import checkpoint, in about a minute:

```
blender -b render/out/hero_imported.blend --python render/rebuild_scene.py
```

Otherwise every photo and top view keeps the old flex route; `add()` prints a
WARNING when the scene's flex no longer matches.

`key_views.py` loads `render/out/key.blend`, re-applies the materials, lights the
display with one legend from the layer-0 atlas (KC_A by default) and renders
the key from five directions: front, front_left, side, top and low.

### Display and flex textures

```bash
python render/gen_textures.py      # Blender's python: numpy + Pillow
```

writes `textures/display_front.png`, `display_front_top.png`,
`display_rim.png`, `flex.png`, `flex_traces.png` and `braid.png`.
`display_front_top.png` is the display face with lighter glass, for
`topview.py`: seen from straight above, the photo view's calmer colours read
as one black square. The display face and the flex are a
reconstruction traced from a photo of the real part
(`textures/source/oled_module_photo.jpg`, FPT042000Z05_V2): the glass and its
cut edge, the dark panel, the striped sticker with the lot number, the black
sticker over the flex with the flex fading into its shadow, the traces,
part number and contact fingers. `STYLE = "photo"` uses the photo itself
instead. ⚠️ The photo is not evenly scaled (29.1 px/mm along the display,
24.3 across); `keymatch.A_*`, the active area the lit legends and the host
editor's display quads use, is centred in the photo's dark panel, so a
different photo means re-measuring it. `display_rim.png` drives a glass coat
on the rim and `flex_traces.png` makes the copper traces metallic
(`materials.py`).

### Re-rendering without re-importing

```bash
blender -b render/out/hero.blend --python render/rerender.py -- render/out/hero2.png 64 1600 1.0 0
```

Arguments: output, samples, width, light scale, exposure (stops). It re-applies
`materials.py` and renders: about 2 minutes for the full keyboard instead of
the ~25 the import and merge take. Every material remembers its role
(`pk_role`), so this works on a scene whose colours were already changed.

### White studio and the bridge cable

```bash
blender -b render/out/hero.blend --python render/rerender.py -- render/out/hero_white.png 128 2560 1.0 0 5 white bridge+host 0 40
```

The last three arguments are the splay of each half in degrees (the import
sets 10), `white` and the cables: `bridge`, `host` or `bridge+host`. An
optional ninth sets the f-stop; the default 0 turns depth of field off, so
the keyboard is sharp front to back. An optional tenth sets the camera's
elevation in degrees (the import sets ~33); the black card moves with it,
since the caps' mirror direction follows the camera.

`host` adds a straight plug on the left half's USB1 (the top-edge port) and
a braided cable that runs back across the desk and out of frame.

`white` (studio.py) replaces the dark floor with a white seamless cove. It
adds a light that reaches only the cove (Cycles light linking), so the floor
goes white at exposure 0 while the dark case stays dark. It also sets AgX's
Medium High Contrast look. Brightening the whole image with exposure instead
turned the case mid grey.

The same option puts a matte black card above and behind the keyboard, out of
frame. The camera looks down at about 33 degrees, so each flat cap top
mirrors whatever sits 33 degrees up behind the keyboard. The rim light used
to sit there (0, 0.8, 0.5), and every cap showed a white patch that hid its
display. With the card there, the caps mirror black and the displays read
through them. This is the "dark field" trick product photographers use for
glass. The rim light now sits higher.

`bridge` (bridge_cable.py) adds the USB-C cable between the inner USB2
ports. The halves sit ~50 mm apart, less than two straight plugs need, so
the plugs are 90 degree ones. The cable leaves each plug towards the back
and lies in a U on the desk behind the keyboard. The overmold (9 x 22.5 x
6.5 mm, inside the USB-IF 12.35 x 6.5 mm envelope across the plug) sits
against the case wall, read from the case mesh. The sleeve carries
`textures/braid.png`. At hero framing the cable is ~10 px wide, so the braid
shows only in close-ups. The receptacles themselves have no 3D model yet:
the KiCad library ships none for the HRO TYPE-C-31-M-12.

### Which Blender

Use **Blender 4.1.1 from blender.org**. It is the last release that bundles
the X3D/VRML importer (4.2 moved it to an online extension), and the official
builds carry OpenImageDenoise. The Ubuntu/Debian package lacks the denoiser,
so its images stay grainy at any sample count you would wait for. The scripts
switch denoising on whenever the build has it.

### Editing an imported mesh (bmesh)

`profile.dent()` and `rgb.clear_case()` rebuild geometry that came in from
VRML. Each of these steps failed silently once, so skipping one gives a wrong
image rather than an error:

- **Weld first.** VRML stores every triangle's corners separately, so the
  mesh has no shared edges and no boundary loop to find. `remove_doubles`
  fixes that.
- **Weld in world millimetres.** The imported objects carry a scale. A 1 µm
  threshold in the object's own frame merged the case's pieces into one, and
  the whole case went opaque. Measure with `matrix_world * 1000`.
- **Map vertices by identity, not `v.index`.** bmesh renumbers vertices when
  faces are removed and added, so an index taken before the edit points at a
  different vertex after it.
- **Call `normal_update()` on new faces.** Without it, the rebuilt cap tops
  rendered as mirrors.
- **Set sharp edges after a weld** (`set_sharp_from_angle`, 30°). Once the
  corners are shared, smooth shading spans them, and the caps looked like a
  kaleidoscope.

⚠️ **`ShaderNodeMix` carries float, vector and colour sockets under the same
names.** Setting `data_type = "RGBA"` does not make `inputs["B"]` the colour
input, and assigning a colour to the float socket raises an error before the
render writes anything. Select the sockets by `type == "RGBA"`, as
`screens.py` and `rgb.clear_flex()` do.

### Why VRML and not GLB or STEP

KiCad 9 can export GLB and STEP, but both go through OpenCASCADE, which drops
every `.wrl` model. The keycaps, stems, displays, cables and switches are all
`.wrl`, so a GLB comes out as a bare populated PCB. The VRML exporter uses the
3D viewer's own loader and keeps everything.

The Blender 4.0 import of one half takes about 7 minutes and creates about
87k objects. Blender 4.2 and later ship the X3D/VRML importer as an extension
("Web3D X3D/VRML2 format"), so install that first there.

### Known gaps in the board models

- the USB-C receptacles (HRO TYPE-C-31-M-12) have no model: the KiCad 9
  library ships none, and inside the case only the plug shows
- the key displays are unlit in the hero and top views; only the product
  photo's viewpoint (below) turns them on (`screens.py`)

## The product photo's viewpoint

```bash
blender -b render/out/hero.blend --python render/photo_view.py -- render/out/photo_view.png 128 2600
```

The composition of `images/PolyKybdSplit72p.jpg` on the white studio: from
in front, 42 deg above the desk, a 35 mm lens, the halves 35 mm apart with
their inner ends brought forward (the left 2 deg, the right 9 deg, measured
on the photo's top edges), the bridge cable looping in front of them
(`bridge_cable.add(toward=-1, clear=...)`: the 90 deg plugs turn the cable
forwards and it runs straight down the gap before the U) and the host cable
leaving the left half's back edge. The optional arguments after the width
are the gap (m), the turns as "left,right" (deg, negative = inner end
forward), elevation (deg), lens (mm) and the share of the frame's width the
keyboard fills. The log reports the bridge cable's closest approach to a
case.

The displays are on, as in the photo (`screens.py`): every key display shows
its layer-0 legend and both status panels their layer-0 screen, as emissive
quads over the active areas. The pictures are the raw framebuffers in
`textures/screens_layer0.png` (an atlas, cells listed in
`screens_layer0.json`) and `textures/status_{left,right}.png`, drawn by
PolyKybdHost's layout-editor preview code over the firmware's default keymap:

```bash
QT_QPA_PLATFORM=offscreen ../PolyKybdHost/.venv/bin/python render/export_screens.py
```

Re-run it when the keymap or the legends change. Two keys stay dark: (8,0)
has no display, and (6,1) holds `KC_HYPR`, for which the preview draws no
legend.

## Close-ups of the lit keys

`closeup_view.py` frames a block of the left half's keys, for the docs' close-up
photos. Its legends come from a named atlas, so a close-up can show any layer
or an app's overlay:

```bash
# layer 1 (Qwerty Stag!, what a fresh board boots on) instead of the shipped layer 0
QT_QPA_PLATFORM=offscreen ../PolyKybdHost/.venv/bin/python render/board_layer.py _L1 /tmp/board_L1.json
QT_QPA_PLATFORM=offscreen ../PolyKybdHost/.venv/bin/python render/export_screens.py ../PolyKybdHost /tmp/board_L1.json 1
# GIMP's overlay icons over those legends, as update_displays() ORs them
python render/overlay_atlas.py /tmp/board_L1.json ../PolyKybdHost/polyhost/res/overlays/gimp_template.mods.png screens_layer1 screens_gimp_l1
PK_STRENGTH=3 PK_STATUS=_l1 blender -b render/out/hero.blend --python render/closeup_view.py -- \
    out.png 128 2100 screens_gimp_l1 0.47 0.6 0.15 52 0 55
```

The lit pixels sample their texture with `Closest`, so one OLED pixel stays one
square, and carry a faint blue cast (`screens.LIT_TINT`). ⚠️ At the default
emission strength (6) a close-up's legends clip, and AgX bleaches clipped
highlights to white, which hides the tint: strength 3 keeps them near
(228, 233, 237). ⚠️ The camera's near clip is 5 mm; Blender's default 0.1 m
cuts the front keys off at close-up distance.

### The RGB night shot

The docs' RGB close-up (`rgb-keycaps-closeup.jpg`) is the same view at night:
the studio off, the clear case, the stepped stem profile with a dented cap
top, and light only from the per-key LEDs. About 75 minutes on 4 CPUs:

```bash
PK_RGB=170,280 PK_EMIT=6000 PK_GLOW=15 PK_FLEX=1,0.15 PK_LED=0 PK_HIDE_ROLES="diffuser resin" \
PK_PROFILE=stepped PK_DENT=0.3,2.5 PK_CASE_GLOW=300,420,80 \
PK_POWER_LED=0.15 PK_CASE_LEDS=30 PK_INDICATOR_HAZE=200 PK_HAZE_RADIUS=0.02 PK_INDICATOR_RADIUS=0.006 \
PK_FOCUS=0.36,0.42 PK_LOOK="AgX - High Contrast" PK_STRENGTH=5 PK_STATUS=_l1 \
blender -b render/out/hero.blend --python render/closeup_view.py -- \
    out.png 1024 1400 screens_layer1 0.45 0.45 0.085 48 -15 22 6.3
```

- `PK_RGB="h0,h1"` turns the studio off and spreads a hue gradient over the
  LEDs from left to right; `PK_EMIT` puts an emissive 3 mm square over each
  LED. It sits 4.4 mm above the PCB (`PK_EMIT_Z`), in the plate opening where
  the diffuser frame glows on the board. ⚠️ The bare LED lies under the plate,
  and from there almost nothing reaches the caps in Cycles (image mean 5.9
  against 30); the frame itself is hidden, because its frosted resin traps
  the light (4x the LED power changed the image mean by 2%).
- `PK_GLOW=15` adds a faint volume glow in the caps, which puts the bright
  rims of the photo back on the cap edges: a wall seen edge-on holds a longer
  path. ⚠️ Cycles does not find the light that the clear walls guide up from
  the LEDs, so without it the rims are dark, and putting the diffuser frame
  back does not help (the image only gets darker). At 40 the caps look milky.
- `PK_FLEX="dim,roughness"` makes the display flex a clear film with no
  specular and no coat, and its copper traces fully metallic (`clear_flex()`).
  At the studio values its satin film lit up the space under every cap.
- `PK_PROFILE` re-poses every cap, display and legend to the stepped,
  stepped-uniform or curved stem profile (`profile.py`, the angle and lift of
  `keycap_stem.scad`'s variants). `PK_DENT="depth,rim"` presses the cap tops
  into a shallow dent with a soft rim; the model's top is a few large
  triangles, so it is rebuilt by a constrained Delaunay fill first.
- `clear_case()` keeps the lid and the status display holder opaque: they
  come in merged with the case (one source colour), so every piece narrower
  than 100 mm gets an opaque copy of the material.
- The indicator LEDs (D1 red, D5 green, D6 yellow on the back of both halves)
  are hidden point lights; `PK_CASE_LEDS` bakes their light into the clear
  case's edges, and the red one gets a soft glow (`PK_INDICATOR_HAZE`). ⚠️ A
  light inside a clear solid never reaches the camera in Cycles, because
  shadow rays stop at glass; the same is why the key LEDs need `PK_EMIT`.
- `PK_FOCUS="fx,fy"` moves the depth-of-field focus off the target, here onto
  the front three rows.

Two approaches that do not work in Cycles here, so the next attempt can skip
them: a Point Density texture over the LED positions contributed nothing to
the caps, even with its bounding box fixed; and a vertex attribute read inside
a volume shader does not interpolate. `glow_from_leds()` bakes the falloff into
a surface colour attribute instead.

To tune one of these values against the photo, use the `render-variant-grid`
skill (`.claude/skills/render-variant-grid/`).

⚠️ `textured_parts.fit()` is cached per half. A fit taken after `profile.py`
has re-posed the displays drifts by 3.5 mm of height, which once put the LED
emitters inside the plate.

### The Eden intro video

The docs' First run video plays the Eden boot animation on both halves seen
from above, in the night look. Rendering every frame in Cycles would take a
day, but only the keycap screens and the backlight change during Eden, and
light adds. So `eden_view.py` renders a few layers once, and `eden_video.py`
sums them per frame in about a second:

```bash
export PK_EMIT=6000 PK_GLOW=15 PK_FLEX=1,0.15 PK_HIDE_ROLES="diffuser resin" \
  PK_PROFILE=stepped PK_DENT=0.3,2.5 PK_CASE_GLOW=80 PK_POWER_LED=0.15 PK_CASE_LEDS=30 \
  PK_INDICATOR_HAZE=200 PK_HAZE_RADIUS=0.02 PK_INDICATOR_RADIUS=0.006 PK_LOOK="AgX - High Contrast" \
  PK_ELEV=65 PK_SPLAY=0 PK_SPLAY_RIGHT=0 PK_GAP=38.5 PK_FLOOR=0.02,0.45
for p in uv id base ambient w c1 s1; do
  blender -b render/out/hero.blend --python render/eden_view.py -- layers/$p.exr 256 2560 $p
done
BPY="$(dirname "$(readlink -f "$(command -v blender)")")/4.1/python/bin/python3.11"   # Blender's own Python
PK_AMBIENT=0.07 PK_ASPECT=2.35 PK_CROP_CY=0.55 "$BPY" render/eden_video.py layers eden-intro.mp4 25
```

- The backlight is QMK's `CYCLE_LEFT_RIGHT` rainbow, which Eden turns on
  (`tutorial_rgb.c`). Its light is rendered three times in white, weighted 1,
  (1 + cos)/2 and (1 + sin)/2 of the rainbow's phase over x (`w`, `c1`, `s1`);
  any moment of the rainbow is a sum of those, to its first harmonic, so its
  colours come out a little softer than real HSV. `startup_anim_rainbow_level()`
  fades it out as on the board.
- The screens come from PolyKybdHost's `tools/fw_anim_sim.py`, the port of
  `startup_anim.c`. The `uv` and `id` layers say which screen pixel each image
  pixel sees through the glass: the screens emit their own coordinates, the
  glass is pure refraction, so one sample per pixel is exact. They render at
  twice the width and are averaged down.
- `base` holds the indicator LEDs and `ambient` a dim room light, which
  `PK_AMBIENT` scales without a new render. `PK_TIMES=1500,7000` with a `.png`
  output writes only those frames, for comparing settings.
- `PK_SPLAY=0` lines the halves up parallel and `PK_GAP` keeps the 38.5 mm gap
  of the splayed hero shot. `PK_FLOOR` makes the desk a dark satin that
  catches the rainbow's spill.

About 1 hour 50 minutes on 4 CPUs at 2560 wide; the 356 frames take another
20 minutes.

## The bare PCB shot (pcb2blender)

One split72 half as the fab delivers it, socket side up, for the docs' PCB
page: the right half, from the angle of the Rev.2 photo it replaced (the
left half works the same way, with `PK_AZIM=8` for the mirrored view). It does not come from the hero scene: the VRML route flattens the
board's layers into flat-coloured geometry, so the mask, silkscreen and
copper never looked like a board. [pcb2blender](https://github.com/30350n/pcb2blender)
exports the layers as artwork and imports them into its own PCB shaders, so
the traces show under the mask and the pads are real copper.

Setup, once per container (pcb2blender's importer needs Blender 5.1):

```bash
git clone https://github.com/30350n/pcb2blender /tmp/pcb2blender
git -C /tmp/pcb2blender checkout 2a2ac82 && git -C /tmp/pcb2blender submodule update --init --recursive
curl -sSLO https://download.blender.org/release/Blender5.1/blender-5.1.2-linux-x64.tar.xz && tar -xf blender-5.1.2-linux-x64.tar.xz
B51=$PWD/blender-5.1.2-linux-x64
apt-get install -y libegl1 libgl1                       # skia-python needs libEGL
$B51/5.1/python/bin/python3.13 -m pip install error-helper==1.4 pillow==11.3 skia-python==138
curl -sSL -o studio_small_09.hdr https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/2k/studio_small_09_2k.hdr
```

Then, from the repo root:

```bash
python3 render/pcb_shot/board_copy.py poly_kybd/poly_kybd_split72_right.kicad_pcb poly_kybd/_shot_right.kicad_pcb
cp poly_kybd/poly_kybd_split72_right.kicad_pro poly_kybd/_shot_right.kicad_pro
xvfb-run -a python3 render/pcb_shot/export.py poly_kybd/_shot_right.kicad_pcb render/out/right.pcb3d
rm poly_kybd/_shot_right.*
$B51/blender -b --python render/pcb_shot/import.py -- render/out/right.pcb3d render/out/pcb_right.blend
PK_HDRI=$PWD/studio_small_09.hdr $B51/blender -b --python render/pcb_shot/shot.py -- \
    render/out/pcb_right.png 128 2800 render/out/pcb_right.blend render/out/right.pcb3d
```

The export takes about 1.5 minutes and the import 3. A 32-sample, 900 px
preview takes about a minute. Traps:

- **The mask colour is set in shot.py, not in the board.** A custom stackup
  colour (`#RRGGBB`) reaches the importer as 0..255 and the mask renders
  white. The copy therefore says `Purple`, which picks the mask shader, and
  shot.py sets its two colours (over copper, over bare board) to the Rev.2
  boards' redder purple. pcb2blender's own purple is a blue-violet.
- **Register the add-on before opening the .blend.** Its materials are built
  from node types it defines; opened without it, every material renders white.
- **The exporter is a pcbnew GUI plugin.** export.py loads its modules without
  the wx dialog and swaps `pcbnew.GetBoard()` and `pcbnew.ExportVRML()` (which
  writes nothing without the editor frame) for the loaded board and kicad-cli.
- **The board copy needs its own .kicad_pro**, or `${KIPRJMOD}` does not
  resolve and the repo's models drop silently.
- **Khronos PBR Neutral, not AgX.** AgX turned the mask and the parts pastel.
  PBR Neutral keeps base colours, but clips a bright highlight, so exposure
  cannot rescue too much light: the key is 12 W and the HDRI 0.15.
- **The flex slots are cut in shot.py.** KiCad's VRML export cuts round drills
  only, so each key's 9.76 x 1.7 mm plated slot arrives as solid board. The
  .pcb3d's pad records give each slot; their positions map onto the board
  through the solder joints, which are named after their pads (the fit is
  exact on 1846 joints). Passing the .pcb3d as the fifth argument cuts them.
  pcb2blender's drill shapes are one off from KiCad 9's (1 = circle, 2 =
  oblong), so a round drill reads "OVAL" and a slot "UNKNOWN".
  ⚠️ The pad rotation goes in as is, the way the importer places its own
  joints. Negated, it changes nothing at 0 and 90 degrees and crosses every
  rotated thumb-key slot with a second cut at the mirrored angle (an X).
  The cutter's faces are wound outward. With the walls facing the hole, a
  bright mirror-like plating reflects the floor and reads white, so the
  plating is a deeper gold (`PK_SLOT_COLOR`, `PK_SLOT_ROUGH` 0.5).
  ⚠️ Each cutter is 0.03 mm over its drill. The import already opens most slots
  (38 of 46 on the right board), and a cutter whose walls coincide with an
  existing hole leaves the EXACT solver undecided: one encoder slot kept its
  whole capsule, a 20 mm copper rod standing out of the board, with no error.
  After a change here, check the board's z range after the cut (it should stay
  at about +-0.80 mm) before spending an hour on a render.
- **Component colours are matched to the Rev.2 photo** in `COLOR_MATCH`,
  keyed on the colour each material imports with: mat4cad reads near-black
  plastics as mid grey, the Kailh contacts' gold as plastic and their tin as
  a mirror that reads as glass. Compare at full resolution, not downscaled:
  render a crop with `PK_BORDER=x0,y0,x1,y1` (fractions, origin bottom left)
  at the final width and put it beside the matching photo crop.
  ⚠️ The photo is a reference for colour and camera angle only, not for
  features: its board is Rev.2, whose flex slots were unplated. The rev3.3
  slots are plated, so the render shows copper walls the photo lacks. The
  photo shows the right half.
- No depth of field: the board is sharp to the far corner. The camera
  (`PK_ELEV` 50, `PK_AZIM` -8, `PK_LENS` 24, `PK_DIST` 0.15 m) is close and
  wide like the phone photo; it tracks the board's centre.
- **Part markings are added in shot.py** (`MARKINGS`): the stock models carry
  none, and the RP2040, the flash, the inductors, the crystal and the shift
  registers show theirs clearly. export.py writes `<board>.parts.json` (each
  footprint's place) beside the .pcb3d; shot.py finds each part's body there
  and lays the text on its top face, upright to the camera.
- **The hotswap pads' solder is added in shot.py.** The Kailh footprint has
  no paste layer, so the importer's SMART mode skips its 288 SMD pads and they
  render as bare gold. shot.py adds the joints, placed relative to the
  importer's joint on an FH34 socket pad. ⚠️ The reference must come from a
  part on the sockets' face: a joint from the other face puts all 288 under
  the board, and the render looks unchanged. Paint the joints a debug colour
  and look straight down (`PK_ELEV=89.9 PK_AZIM=0`) before believing a
  placement. Each joint is a fillet on the two outer tabs only (the inner
  pads lie under the black body): the tin covers the land and climbs the
  tab's end and sides in a concave arc (`PK_HS_SOLDER_H` 0.2 mm at the tab,
  falling to the land over `PK_HS_SOLDER_REACH` 0.8 mm). It is built in the
  socket's own frame, the socket's rotation read off its two small holes.
  Over the tab's outer end sits a convex bead (`PK_HS_BEAD_H` 0.35 mm,
  `PK_HS_BEAD_R` 0.7 mm) that stands above the tab: the concave fillet
  alone does not show at the full image's scale.
  The importer's joints in the two switch-pin holes are removed: the switch
  plugs into the socket and is never soldered.
- **The FH34 sockets are recoloured per object**: their housing shares its
  imported colour with the 74HC595 bodies, so COLOR_MATCH cannot separate
  them. The
  Kailh model hangs 0.27 mm clear of the board, so shot.py seats it
  (`PK_HS_SEAT`) and the tabs rest on their pads.
- **mat4cad's 0.05 mm edge bevel is cut to 0.015 mm** (`PK_BEVEL`). At the
  default, every 0603 part carries a bright rim along each edge and corner.
- A 2800 px, 128-sample render takes about 60 minutes on 4 CPUs at the
  default close camera (45 with the earlier 70 mm, 0.45 m view), longer than
  a background command's default limit: run it detached and watch its log
  (see `polykybd-claude/docs/web-session.md`).

## Top view for PolyKybdHost's layout editor

```bash
blender -b render/out/hero.blend --python render/topview.py -- render/out/topview.png 4800 96
```

An orthographic render straight down on both halves, unsplayed, without
cables, plus `topview.json`. The matrix labels come from PolyKybdHost's KLE
file: the script reads `../PolyKybdHost/polyhost/res/polykybd-split72.json`
(a checkout next to this repo), or the path given as a 4th argument.

- `keys`: per key display, the KLE matrix label (`"row,col"`, the label
  PolyKybdHost's `polykybd-split72.json` uses), the side, the board
  reference, the rotation and `oled`, the 72x40 active area as four image
  pixels in the OLED's own order (top-left, top-right, bottom-right,
  bottom-left, so the first corner is framebuffer pixel 0,0);
- `status_displays`: each half's 128x64 status display as a pixel bbox;
- `mm_per_px`, and the KLE match residual per half.

The labels come from matching each board key to the nearest KLE key after a
translation fit (19.05 mm per U); the largest residual is ~4.5 mm, well under
half a key, and the script refuses a match that reuses a KLE key.

From straight above every flat cap top mirrors what is directly overhead, so
the black card goes overhead and casts no shadow. The overhead and rim lights
are hidden from reflection AND transmission rays: a display decal's coat
mirrors a light up through the clear cap, and that transmission path laid a
white veil over every display.

## Web viewer

`render/web/index.html` is a `<model-viewer>` page (orbit, zoom, AR on phones)
with a switch between the whole keyboard and one key. Build its two models
from saved scenes:

```bash
blender -b render/out/hero.blend --python render/export_web.py -- render/web/keyboard.glb 80000
blender -b render/out/key.blend  --python render/export_web.py -- render/web/key.glb 60000
for m in keyboard key; do base64 -w0 render/web/$m.glb > render/web/$m.glb.b64.txt; done
```

The page loads `<name>.glb.b64.txt`, not the `.glb`: the artifact host serves
no binary model type, so each model ships as base64 text and the page decodes
it once into a `blob:` URL. The full scene comes out at 131k triangles,
7.9 MB (10.6 MB as base64): the plates and the textured parts are kept out of
the decimation, so the budget is a target rather than a cap. The plate's
Rosetta art is baked into a soft texture (a third of 1536 px, blurred, half
strength; arguments 3 and 4), since the glyphs read as speckle at web size.

`export_web.py` merges the meshes per material, dissolves coplanar faces (the
silkscreen art is most of the triangles) and decimates to the budget. The GLBs
are not compressed: Draco and meshopt need a decoder fetched at runtime, which
an artifact page cannot do, so the triangle budget is the size control
(about 30 bytes per triangle; artifact files are capped at 15 MB).
