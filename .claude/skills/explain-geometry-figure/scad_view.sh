#!/usr/bin/env bash
# Headless OpenSCAD -> PNG.  Wraps the two things that silently bite:
# a missing display (writes a 0-byte PNG) and --render needing an argument.
#
#   scad_view.sh out.png model.scad top            # ortho top view
#   scad_view.sh out.png model.scad iso            # 3/4 view
#   scad_view.sh out.png model.scad '0,0.9,0.6,58,0,205,32'   # explicit camera
#
# Camera has TWO forms, both accepted by --camera:
#   7 numbers  translate_x,y,z, rot_x,y,z, dist   <- axis-aligned views, and
#                                                    `dist` is also the ortho scale
#   6 numbers  eye_x,y,z, centre_x,y,z            <- aim at a point
# Env: SIZE=WxH  CENTRE=x,y,z  DIST=n  SCHEME="Tomorrow Night"  PREVIEW=1
set -euo pipefail

if (( $# < 2 || $# > 3 )); then
  echo "usage: $(basename "$0") out.png model.scad [top|front|iso|<camera>]" >&2
  exit 64
fi

out=$1; scad=$2; view=${3:-iso}
size=${SIZE:-1000x760}
centre=${CENTRE:-0,0,0}
dist=${DIST:-}
scheme=${SCHEME:-Tomorrow Night}

case "$view" in
  top)  cam="$centre,0,0,0,${dist:-40}";   proj=o ;;
  front) cam="$centre,90,0,0,${dist:-40}"; proj=o ;;
  iso)  cam="$centre,58,0,205,${dist:-40}"; proj=p ;;
  *)    cam="$view"; proj=${PROJ:-p} ;;
esac

# --render=cgal is a FULL geometry evaluation: one clean solid colour, real facets.
# Omit it (PREVIEW=1) for the fast OpenCSG preview — but note preview tints
# difference() results and can paint an explicit color() over the wrong region.
render=(--render=cgal)
[ -n "${PREVIEW:-}" ] && render=()

xvfb-run -a openscad -o "$out" \
  --imgsize="${size/x/,}" --camera="$cam" --projection="$proj" \
  --colorscheme="$scheme" "${render[@]}" "$scad" 2>&1 | tail -2

[ -s "$out" ] || { echo "EMPTY PNG — no display?  run under xvfb-run" >&2; exit 1; }
echo "wrote $out"
