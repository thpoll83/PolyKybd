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
    out.png 128 2100 screens_gimp_l1 0.47 0.58 0.145 50 0 55
```

The lit pixels sample their texture with `Closest`, so one OLED pixel stays one
square, and carry a faint blue cast (`screens.LIT_TINT`). ⚠️ At the default
emission strength (6) a close-up's legends clip, and AgX bleaches clipped
highlights to white, which hides the tint: strength 3 keeps them near
(228, 233, 237). ⚠️ The camera's near clip is 5 mm; Blender's default 0.1 m
cuts the front keys off at close-up distance.

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
