#!/usr/bin/env bash
# The assembly video, start to end: the left half built part by part, then both halves
# and the USB cables (render/assembly_video.py).
#
#   render/assembly_build.sh [width] [samples] [out dir]     # defaults: 1920 32 render/out/assembly_<width>
#
# Needs render/out/hero.blend and render/out/split72_left.wrl (the image's "scene" step),
# Blender 4.1 as $BLENDER, Blender 5.1 as $BLENDER51 with pcb2blender at $PCB2BLENDER, and
# KiCad 9 with its Python (pcbnew) for the board export. Each step whose output exists is
# skipped, and so is each frame already rendered: stop it any time and run it again.
# Delete render/out/assembly*.blend, render/out/left.pcb3d and render/out/pcb_left.blend
# to rebuild the scene after a board change.
#
#   PK_JOBS   Blender processes rendering frames side by side (default: one per 8 cores;
#             1 with PK_GPU). Each holds the scene, about 5.2 GB.
#   PK_GPU    OPTIX | CUDA | HIP | ONEAPI to render on a GPU (default: CPU)
#   PK_FRAMES "first last" to render only those frames (default: all 1686)
set -euo pipefail
cd "$(dirname "$0")/.."
WIDTH=${1:-1920}
SAMPLES=${2:-32}
OUT=${3:-render/out/assembly_${WIDTH}}
BLENDER=${BLENDER:-blender}
BLENDER51=${BLENDER51:-blender-5.1}
export PCB2BLENDER=${PCB2BLENDER:-/opt/pcb2blender}
mkdir -p "$OUT"
LOG="$OUT/build.log"
say() { echo "$(date +%T) $*" | tee -a "$LOG"; }
need() { [ -f "$1" ] || { echo "missing $1: $2" >&2; exit 2; }; }
need render/out/hero.blend "build it first (render/docker/README.md, the scene step)"
need render/out/split72_left.wrl "build it first (render/export_boards.sh)"
run() {                                   # run a step, its output into the log, and fail loudly
    local name=$1; shift
    say "$name"
    if ! "$@" >> "$OUT/$name.log" 2>&1 || grep -q Traceback "$OUT/$name.log"; then
        say "$name FAILED, see $OUT/$name.log"; exit 1
    fi
}

# 1. the left half as one object per part (Blender 4.1, ~15 min: it imports the VRML again)
[ -f render/out/assembly.blend ] || run scene "$BLENDER" -b render/out/hero.blend --python render/assembly_scene.py -- \
    render/out/split72_left.wrl render/out/assembly.blend
# 2. the bare board through pcb2blender, as for the PCB shot (render/README.md)
if [ ! -f render/out/left.pcb3d ]; then
    python3 render/pcb_shot/board_copy.py poly_kybd/poly_kybd_split72_left.kicad_pcb poly_kybd/_shot_left.kicad_pcb
    cp poly_kybd/poly_kybd_split72_left.kicad_pro poly_kybd/_shot_left.kicad_pro
    run export xvfb-run -a python3 render/pcb_shot/export.py poly_kybd/_shot_left.kicad_pcb render/out/left.pcb3d
    rm -f poly_kybd/_shot_left.*
fi
[ -f render/out/pcb_left.blend ] || run import "$BLENDER51" -b --python render/pcb_shot/import.py -- \
    render/out/left.pcb3d render/out/pcb_left.blend
# 3. that board and its parts in the assembly scene (Blender 5.1)
[ -f render/out/assembly_pcb.blend ] || run pcb "$BLENDER51" -b --python render/assembly_pcb.py -- \
    render/out/assembly.blend render/out/pcb_left.blend render/out/left.pcb3d render/out/assembly_pcb.blend

# 4. the frames, dealt round-robin to PK_JOBS processes
CORES=$(nproc)
if [ -n "${PK_GPU:-}" ]; then JOBS=${PK_JOBS:-1}; else JOBS=${PK_JOBS:-$(( CORES / 8 > 0 ? CORES / 8 : 1 ))}; fi
THREADS=$(( CORES / JOBS > 0 ? CORES / JOBS : 1 ))
read -r FIRST LAST <<< "${PK_FRAMES:-1 1686}"
say "assembly video: ${WIDTH} px, ${SAMPLES} samples, frames ${FIRST}-${LAST}, ${JOBS} jobs x ${THREADS} threads, GPU=${PK_GPU:-none}, out $OUT"
pids=()
for j in $(seq 0 $(( JOBS - 1 ))); do
    frames=$(seq -s, $(( FIRST + j )) "$JOBS" "$LAST")
    [ -n "$frames" ] || continue
    "$BLENDER51" -b render/out/assembly_pcb.blend -t "$THREADS" --python render/assembly_video.py -- \
        "$OUT/frames" "$WIDTH" "$SAMPLES" stills "$frames" > "$OUT/frames_$j.log" 2>&1 &
    pids+=($!)
done
fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
if [ $fail = 1 ] || grep -l Traceback "$OUT"/frames_*.log >/dev/null 2>&1; then
    say "a frame job FAILED, see $OUT/frames_*.log"; exit 1
fi
n=$(ls "$OUT/frames" | wc -l)
say "rendered $n frames"

# 5. the video (silent for now), from the whole run's frames
if [ "$n" -ge 1686 ]; then
    ffmpeg -loglevel error -y -framerate 25 -i "$OUT/frames/frame_%04d.png" \
        -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -movflags +faststart "$OUT/assembly_${WIDTH}.mp4"
    say "done: $OUT/assembly_${WIDTH}.mp4"
else
    say "$n of 1686 frames: run again to finish, the video is made once all are there"
fi
