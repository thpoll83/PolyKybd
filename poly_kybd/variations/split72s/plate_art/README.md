# split72s plate artwork: Rongorongo Tablet B, verso

Silkscreen artwork for the split72s switch plate, traced from a photograph of Rongorongo
Tablet B. Licences and the credit line: [ATTRIBUTION.md](ATTRIBUTION.md).

| File | What |
|---|---|
| `tabletB_verso_photo.jpg` | the source photograph, 2403 x 1128 px |
| `trace_settings.json` | placement and tracing settings from `../layout_study/plate_trace_tool.html` |
| `plate_art_tabletB_mask.png` | the traced mask, white = silkscreen, 8 px/mm, 2557 x 842 px = the whole plate |
| `plate_art_tabletB.svg` | the mask traced to vector paths, 319.62 x 105.25 mm, origin = plate top-left corner |
| `build.sh`, `export_mask.js`, `trace_svg.py` | rebuild the mask and the SVG from the photo and the settings |

## Settings

The plate is turned 4.5 degrees counter-clockwise on the photo, centred at photo pixel
(1170, 610), at 0.164 mm per photo pixel; 99.7 % of the plate lies on the tablet. The trace
uses light strokes on dark, 1.6 mm background blur, threshold 17, +0.05 mm grow, specks
under 0.2 mm² removed and holes under 0.45 mm² filled. 2.9 % of the ink is thinner than
0.21 mm.

## Rebuild

```bash
bash poly_kybd/variations/split72s/plate_art/build.sh
```

Needs Python 3 with numpy and Pillow, `potrace`, and Node with Playwright and Chromium.
The rebuild gives the same mask, byte for byte, and the same SVG paths.

To try other settings, build the tool with the photo embedded, change the values in the
page, export the settings JSON, and replace `trace_settings.json`:

```bash
python3 poly_kybd/variations/split72s/layout_study/make_trace_tool.py \
    --image poly_kybd/variations/split72s/plate_art/tabletB_verso_photo.jpg --out /tmp/tool.html
```

## Before production

- Import `plate_art_tabletB.svg` onto the plate's top silkscreen layer in KiCad and run DRC
  for silkscreen width and clearance (JLC: 0.15 mm minimum line width).
- The plate's switch cut-outs remove the artwork inside them; no extra clearance is drawn.
- Check that the far bottom-right corner (0.3 % of the plate, off the tablet in the photo)
  looks right, or move the plate a few pixels in the tool.
