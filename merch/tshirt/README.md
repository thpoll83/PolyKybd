# T-shirt designs

Print-ready vector artwork for PolyKybd T-shirts. The SVGs have physical `mm` sizes and a transparent background. All lettering is converted to outlines, so no fonts are needed to print them. Glyphs come from the Noto Sans families at weight 600; the wordmark uses an Arial Bold Italic metric equivalent.

## Keycap grid

| File | Size | Colours |
|------|------|---------|
| `polykybd-tee-2g-keycap-grid.svg` | 280 × 168 mm | 1 (`#2f7bf6`) |
| `polykybd-tee-2g-wordmark.svg` | 79.6 × 15.8 mm | 1 |

The grid has 160 keycaps in 16 columns, each with a different glyph from 18 scripts. It has 24 Latin glyphs (accents, strokes, ligatures), 11 Arabic, 5 Cherokee, and 8 from each of the other 15 scripts. The glyphs were picked to carry no bad meaning when read alone, and no two look alike across scripts. The glyph is knocked out of the keycap, so the shirt colour shows through. The wordmark "PolyKybd" goes above the grid.

## POLY blocks

A 2 × 2 keycap block spelling POLY. Each file is 33.25 × 32 mm and uses one colour.

| File | Glyphs | Scripts |
|------|--------|---------|
| `polykybd-tee-poly-greek.svg` | ΠΟΛΥ | Greek |
| `polykybd-tee-poly-armenian.svg` | ՊՈԼԻ | Armenian |
| `polykybd-tee-poly-georgian.svg` | პოლი | Georgian |
| `polykybd-tee-poly-mix-2.svg` | पஒلኢ | Devanagari, Tamil, Arabic, Ethiopic |
| `polykybd-tee-poly-mix-3.svg` | ՊওలΥ | Armenian, Bengali, Telugu, Greek |
| `polykybd-tee-poly-mix-5.svg` | பኦลই | Tamil, Ethiopic, Thai, Bengali |

## Blue bursts

The same 160 keycaps, each glyph knocked out, arranged at many sizes. One colour (`#2f7bf6`), so these suit screen printing on a light or a black shirt.

| File | Size | Shape |
|------|------|-------|
| `polykybd-tee-star-explosion.svg` | 300 × 300 mm | keycaps thrown outward from a bright core |
| `polykybd-tee-black-hole.svg` | 300 × 300 mm | keycaps spiralling into an empty centre |
| `polykybd-tee-oval-explosion.svg` | 300 × 300 mm | uneven oval burst |

## Colour bursts (for a black shirt)

The 160 keycaps plus several hundred filler keycaps, with depth shading: front keycaps are bigger and brighter. Tiny coloured sparkles follow the outline of the design, so the print shows no rectangular edge. Glyph tops point toward the centre. These need DTG or DTF printing, since each uses 35–39 fill colours.

| File | Size | Shape |
|------|------|-------|
| `polykybd-tee-black-hole-colour.svg` | 300 × 300 mm | ring around an empty core |
| `polykybd-tee-oval-explosion-colour.svg` | 300 × 300 mm | uneven oval burst |
| `polykybd-tee-star-burst-colour.svg` | 300 × 300 mm | 8 major and 22 minor rays; keycaps start small, peak at 2/3 of each ray, then shrink |
| `polykybd-tee-star-burst-thin-rays-colour-rot30.svg` | 300 × 315 mm | the star burst plus 5 thin rays, turned 30° clockwise and not scaled |

The files have no background. To preview one as printed, open it on a black page.

## Regenerating

The generators are in `tools/`. They need Python 3 with `fonttools`, `skia-pathops` and `uharfbuzz`, plus `curl` and network access to Google Fonts. The wordmark also needs Liberation Sans Bold Italic (`fonts-liberation`), or pass another font path.

```bash
cd tools
python3 fetch_fonts.py                 # Noto Sans subsets for glyphs.txt into fonts/
python3 grid.py                        # polykybd-tee-2g-keycap-grid.svg
python3 wordmark.py                    # polykybd-tee-2g-wordmark.svg
python3 poly_single.py                 # greek, armenian, georgian (pass other names to build them)
python3 poly_mix.py                    # mix-2, mix-3, mix-5
python3 explosion.py; python3 blackhole.py; python3 oval.py        # blue bursts
python3 colour_designs.py black-hole
python3 colour_designs.py oval-explosion
python3 colour_designs.py star-burst
python3 colour_designs.py star-burst-thin-rays radial 30          # 30 = turn in degrees, clockwise
```

- Output goes to this folder. Set `TEE_OUT=<dir>` to write elsewhere.
- Set `TEE_PREVIEW=1` to also write a `-on-black` preview of each colour design.
- `glyphs.txt` holds the 160 grid glyphs, in grid order.
- The POLY scripts download their own font subsets into `tools/fonts_poly/`.
- Every design uses a fixed random seed. Run with the fonts fetched on 2026-09-30, each script reproduces its committed file byte for byte. A later Noto release can move outlines slightly.
- `colour_designs.py random` in place of `radial` gives random per-keycap rotation instead of glyph tops pointing at the centre.
