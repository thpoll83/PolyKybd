#!/bin/bash
# midi_anim.py's frames -> the video: a missing frame (PK_STEP) repeats the one before,
# the last 2 s fade to black, and the soundtrack is midi_video.py's (PK_SF2 for the
# sampled piano).
#   render/midi_anim_video.sh <frame dir> <out.mp4> [fps]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
D=$(cd "$1" && pwd); OUT=$2; FPS=${3:-25}
BPY=${BPY:-$(dirname "$(readlink -f "$(command -v blender)")")/4.1/python/bin/python3.11}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
N=$("$BPY" -c "import sys; sys.argv=['x']; sys.path.insert(0, '$HERE'); import midi_video as m; print(int(m.TOTAL * $FPS))")
prev=""
for ((i = 0; i < N; i++)); do
  f=$(printf "%s/%05d.png" "$D" $i)
  [ -f "$f" ] && prev=$f
  [ -n "$prev" ] && ln -s "$prev" "$(printf "%s/%05d.png" "$TMP" $i)"
done
"$BPY" "$HERE/midi_video.py" "$TMP/sound.wav"
DUR=$(echo "$N / $FPS" | bc -l)
VF="fade=t=out:st=$(echo "$DUR - 2" | bc -l):d=2"
if [ -n "${PK_CREDIT:-}" ]; then          # the soundfont's attribution along the bottom
    FONT=${PK_CREDIT_FONT:-/usr/share/fonts/truetype/freefont/FreeSans.ttf}
    VF="$VF,drawtext=fontfile=$FONT:text='${PK_CREDIT//:/\\:}':fontsize=h*0.022:fontcolor=white@0.55:x=(w-text_w)/2:y=h-text_h-h*0.03"
fi
ffmpeg -loglevel error -y -framerate "$FPS" -i "$TMP/%05d.png" -i "$TMP/sound.wav" \
  -vf "$VF" -af "afade=t=out:st=$(echo "$DUR - 2" | bc -l):d=2" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
echo "wrote $OUT ($N frames)"
