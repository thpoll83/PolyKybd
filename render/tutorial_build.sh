#!/bin/bash
# The first-run tutorial video, end to end: every render layer, the screens, the encode.
#
#   render/tutorial_build.sh [width] [samples] [out dir]       # defaults: 1024 32 render/out/tutorial_<width>
#
# Run it from the PolyKybd checkout, with PolyKybdHost and qmk_firmware beside it (the
# same layout render/docker/ mounts). It RESUMES: a layer already on disk is not rendered
# again, so a run that was stopped picks up where it ended. Delete the out dir to start over.
#
# Environment:
#   BLENDER   Blender 4.1 executable (default: blender on PATH)
#   HOSTPY    Python with numpy, Pillow, openpyxl and fonttools for tutorial_story.py
#             (default: ../PolyKybdHost/.venv/bin/python, else python3)
#   PK_GPU    OPTIX | CUDA | HIP | ONEAPI to render on a GPU (default: CPU)
#   SCENE     the saved scene (default: render/out/hero.blend)
set -euo pipefail
cd "$(dirname "$0")/.."
WIDTH=${1:-1024}
SAMPLES=${2:-32}
OUT=${3:-render/out/tutorial_${WIDTH}}
BLENDER=${BLENDER:-blender}
BLENDER_BIN=$(readlink -f "$(command -v "$BLENDER")")
BPY=$(ls "$(dirname "$BLENDER_BIN")"/4.1/python/bin/python3.* 2>/dev/null | head -1)
[ -x "$BPY" ] || { echo "Blender 4.1's bundled Python not found beside $BLENDER_BIN" >&2; exit 2; }
if [ -z "${HOSTPY:-}" ]; then
    HOSTPY=../PolyKybdHost/.venv/bin/python
    [ -x "$HOSTPY" ] || HOSTPY=python3
fi
SCENE=${SCENE:-render/out/hero.blend}
[ -f "$SCENE" ] || { echo "no scene at $SCENE (render/README.md: blender_scene.py builds it)" >&2; exit 2; }
SHOTS=render/tutorial_shots.json
mkdir -p "$OUT"
LOG="$OUT/build.log"
say() { echo "$(date +%T) $*" | tee -a "$LOG"; }

# the look of the night renders (render/README.md, "The Eden intro video"), with the
# diffusers as the key LEDs' light and both cables
export PK_EMIT=6000 PK_GLOW=15 PK_FLEX=1,0.15 PK_HIDE_ROLES="" \
    PK_PROFILE=stepped PK_DENT=0.3,2.5 PK_CASE_GLOW=80 PK_POWER_LED=0.15 PK_CASE_LEDS=30 \
    PK_INDICATOR_HAZE=200 PK_HAZE_RADIUS=0.02 PK_INDICATOR_RADIUS=0.006 PK_LOOK="AgX - High Contrast" \
    PK_ELEV=65 PK_SPLAY=0 PK_SPLAY_RIGHT=0 PK_GAP=38.5 PK_FLOOR=0.02,0.45 PK_CABLES=bridge+host \
    PK_DIFFUSER_GLOW=400 PK_SILK=0.55,0.8,0.12

# shot names in the shot list, optionally only those with a press / only "full"
shots() { "$BPY" -c "import json,sys; print(','.join(s['name'] for s in json.load(open('$SHOTS'))))"; }

# render the layer `pass` for the shots in $2 (comma list) into $3 at width $4, skipping
# shots already on disk
layer() {
    local pass=$1 want=$2 dir=$3 width=$4 missing=""
    for s in ${want//,/ }; do
        [ -f "$dir/$s.exr" ] || missing="$missing,$s"
    done
    missing=${missing#,}
    [ -z "$missing" ] && return 0
    say "$pass -> $dir ($(echo "$missing" | tr ',' '\n' | wc -l) shots)"
    local log="$OUT/blender_$(basename "$dir").log"       # one per layer, fresh each attempt
    PK_SHOTS="$SHOTS" PK_ONLY="$missing" "$BLENDER" -b "$SCENE" --python render/eden_view.py -- \
        "$dir" "$SAMPLES" "$width" "$pass" > "$log" 2>&1
    if grep -q Traceback "$log"; then
        say "$pass FAILED, see $log"; exit 1
    fi
}

say "tutorial video: ${WIDTH} px, ${SAMPLES} samples, GPU=${PK_GPU:-none}, out $OUT"
ALL=$(shots)
for p in uv id ambient base; do layer "$p" "$ALL" "$OUT/$p" "$WIDTH"; done
for p in w c1 s1 ambient_m ambient_r; do layer "$p" full "$OUT/$p" "$WIDTH"; done

# the key LEDs' light: three keys per render (one per colour channel), at half width
# (soft light, upscaled by the compositor); each group renders the shots its keys appear in.
# A press variant (it names a "light" shot) borrows that shot's LED renders: a key 3.5 mm
# down moves the light by too little to see
"$BPY" - "$SHOTS" ../PolyKybdHost/polyhost/res/preview/board.json "$OUT/led_jobs.txt" <<'PY'
import json, sys
shots = json.load(open(sys.argv[1]))
keys = sorted({"%d,%d" % tuple(k["matrix"]) for k in json.load(open(sys.argv[2]))["keys"]},
              key=lambda s: tuple(map(int, s.split(","))))
shots = [s for s in shots if "light" not in s]
wide = [s["name"] for s in shots if not s["name"].startswith("k_")]
with open(sys.argv[3], "w") as f:
    n = 0
    for half in ([k for k in keys if int(k.split(",")[0]) < 5], [k for k in keys if int(k.split(",")[0]) >= 5]):
        for i in range(0, len(half), 3):
            g = half[i:i + 3]
            names = wide + [s["name"] for s in shots if s["name"].startswith("k_") and s["focus"][0] in g]
            f.write(f"{n}|{';'.join(g)}|{','.join(names)}\n")
            n += 1
PY
while IFS='|' read -r n keys want; do
    PK_LED_KEYS="$keys" layer led "$want" "$OUT/led_$n" $((WIDTH / 2))
done < "$OUT/led_jobs.txt"

# the screens (always rebuilt: a few seconds, and a stale story would silently win), then
# the frames, straight into ffmpeg, then the soundtrack (render/tutorial_audio.py)
say "story"
PYTHONPATH=../PolyKybdHost "$HOSTPY" render/tutorial_story.py "$OUT/story.npz" >> "$LOG" 2>&1
say "encode"
PK_SHOT_CACHE=${PK_SHOT_CACHE:-4} "$BPY" render/tutorial_video.py video "$OUT" "$OUT/story.npz" \
    "$OUT/tutorial_${WIDTH}.mp4" "$WIDTH" 25 >> "$LOG" 2>&1
say "done: $OUT/tutorial_${WIDTH}.mp4"
