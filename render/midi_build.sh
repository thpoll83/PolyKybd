#!/bin/bash
# The MIDI layer video (Für Elise), end to end.
#
#   render/midi_build.sh anim  [width] [samples] [fps] [step]   # moving camera (midi_anim.py)
#   render/midi_build.sh fixed [width] [samples]                # fixed camera (midi_video.py)
#
# Defaults: anim 1280 64 25 1, fixed 2560 256. Run it from the PolyKybd checkout with
# PolyKybdHost beside it (the layout render/docker/ mounts). It RESUMES: a frame or a
# layer already on disk is not rendered again, so a stopped run picks up where it ended.
# Delete the out dir to start over (for example after the camera path changes).
#
#   anim   render/out/midi_anim_<width>/ (one PNG a frame) -> render/out/midi_anim_<width>.mp4
#          step > 1 renders every step-th frame and repeats it (a quick preview)
#   fixed  render/out/midi_layers_<width>/ (eden_view.py layers, keys up and down)
#          -> render/out/midi_fixed_<width>.mp4 and midi_fixed_<width>.gif
#
# Environment:
#   BLENDER   Blender 4.1 executable (default: blender on PATH)
#   PK_GPU    OPTIX | CUDA | HIP | ONEAPI to render on a GPU (default: CPU)
#   PK_SF2    a piano soundfont for the soundtrack (the image sets the Salamander Grand
#             Piano, CC BY 3.0); unset, the soundtrack is the built-in felt piano
#   SCENE     the saved scene (default: render/out/hero.blend)
# ⚠️ Run ONE Blender at a time: each holds about 6 GB, and three at once ran a 15 GB
# machine out of memory, which killed render passes half way.
set -euo pipefail
cd "$(dirname "$0")"
MODE=${1:-anim}
BLENDER=${BLENDER:-blender}
BLENDER_BIN=$(readlink -f "$(command -v "$BLENDER")")
BPY=$(ls "$(dirname "$BLENDER_BIN")"/4.1/python/bin/python3.* 2>/dev/null | head -1)
[ -x "$BPY" ] || { echo "Blender 4.1's bundled Python not found beside $BLENDER_BIN" >&2; exit 2; }
SCENE=${SCENE:-out/hero.blend}
[ -f "$SCENE" ] || { echo "no scene at render/$SCENE (render/README.md: blender_scene.py builds it)" >&2; exit 2; }
say() { echo "$(date +%T) $*"; }

# the night look of the Eden video, with the bridge cable in front and the host cable
export PK_EMIT=6000 PK_GLOW=15 PK_FLEX=1,0.15 PK_HIDE_ROLES="diffuser resin" \
  PK_PROFILE=stepped PK_DENT=0.3,2.5 PK_CASE_GLOW=80 PK_POWER_LED=0.15 PK_CASE_LEDS=30 \
  PK_INDICATOR_HAZE=200 PK_HAZE_RADIUS=0.02 PK_INDICATOR_RADIUS=0.006 PK_LOOK="AgX - High Contrast" \
  PK_ELEV=65 PK_SPLAY=0 PK_SPLAY_RIGHT=0 PK_GAP=38.5 PK_FLOOR=0.02,0.45 \
  PK_CABLES=bridge+host PK_BRIDGE=0.045,-1,0.012,0.022

if [ "$MODE" = anim ]; then
    WIDTH=${2:-1280}; SAMPLES=${3:-64}; FPS=${4:-25}; STEP=${5:-1}
    OUT=out/midi_anim_${WIDTH}
    mkdir -p "$OUT"
    say "frames -> render/$OUT ($WIDTH px, $SAMPLES samples, every $STEP. frame at $FPS fps)"
    PK_STEP=$STEP "$BLENDER" -b "$SCENE" --python midi_anim.py -- "$OUT" "$SAMPLES" "$WIDTH" "$FPS" > "$OUT/blender.log" 2>&1 \
        || { tail -30 "$OUT/blender.log" >&2; exit 1; }
    BPY=$BPY ./midi_anim_video.sh "$OUT" "out/midi_anim_${WIDTH}.mp4" "$FPS"
    exit 0
fi

[ "$MODE" = fixed ] || { echo "mode is anim or fixed" >&2; exit 2; }
WIDTH=${2:-2560}; SAMPLES=${3:-256}
L=out/midi_layers_${WIDTH}
mkdir -p "$L"
export PK_OUTLINES=1 PK_SHOTS=midi_shots.json
for p in uv id base ambient w c1 s1; do
    miss=""
    for n in up down; do [ -f "$L/$p/$n.exr" ] || miss="$miss,$n"; done
    miss=${miss#,}
    [ -z "$miss" ] && continue
    say "layer $p ($miss)"
    PK_ONLY=$miss "$BLENDER" -b "$SCENE" --python eden_view.py -- "$L/$p" "$SAMPLES" "$WIDTH" "$p" > "$L/$p.log" 2>&1 \
        || { tail -30 "$L/$p.log" >&2; exit 1; }
    rm -f "$L/$p"/*.blend "$L/$p"/*.blend1
    for n in up down; do [ -f "$L/$p/$n.exr" ] || { echo "layer $p $n missing: render/$L/$p.log" >&2; exit 1; }; done
done
export PK_ASPECT=2.35 PK_CROP_CY=0.55
say "video"
"$BPY" midi_video.py "$L" "out/midi_fixed_${WIDTH}.mp4" 25
PK_WIDTH=800 PK_START=0.4 PK_END=9.4 "$BPY" midi_video.py "$L" "out/midi_fixed_${WIDTH}.gif" 15
say "done: render/out/midi_fixed_${WIDTH}.mp4 and .gif"
