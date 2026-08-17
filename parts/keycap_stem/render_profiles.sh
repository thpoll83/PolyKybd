#!/usr/bin/env bash
# Render the profile lineup pictures used by the top-level README.
#
#   parts/keycap_stem/render_profiles.sh            # all four, into images/
#   parts/keycap_stem/render_profiles.sh curved     # just that view
#   parts/keycap_stem/render_profiles.sh --out /tmp # somewhere else
#
# These are PICTURES, not print plates -- preview_stems.scad has no exportable
# geometry and build_stems.sh ignores it.  The reason this is a script rather
# than a note about which camera to use: the four images only compare if they
# share a camera, and the previous set was hand-framed in the GUI, so the flat
# one sits at a different elevation from the curved one and the eye reads that
# as a profile difference.
#
# Rendering needs a display even though exporting does not, hence xvfb-run.
set -euo pipefail

cd "$(dirname "$0")/../.."                  # repo root
SRC=parts/keycap_stem/preview_stems.scad
OUT=images

VIEWS="curved stepped stepped_uniform flat"

# One camera for every view.  Gimbal form: transx,y,z, rotx,y,z, dist.
# 70 deg of elevation is the compromise that shows the tops (so the engraved
# revision reads) while still showing enough of the side for the tilt and lift
# to be visible -- straight on and the profile reads but the labels vanish.
CAM=0,0,0,70,0,90,150
SIZE=1300,430

want=()
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 64 ;;
    *)  want+=("$1") ;;
  esac
  shift
done

command -v openscad >/dev/null || { echo "openscad not on PATH" >&2; exit 69; }
command -v xvfb-run >/dev/null || { echo "xvfb-run not on PATH (apt-get install xvfb)" >&2; exit 69; }

# Same trap as the exporters: openscad exits 1 for an empty result and 1 for a
# syntax error alike, so test for the marker before trusting the exit code.  An
# empty result here means `view` matched none of the branches.
mkdir -p "$OUT"
for v in $VIEWS; do
  if [ ${#want[@]} -gt 0 ]; then
    printf '%s\n' "${want[@]}" | grep -qx "$v" || continue
  fi
  png="$OUT/profile_$v.png"
  printf '%-18s %s ' "$v" "$png"
  log=$(xvfb-run -a openscad -o "$png" -D "view=\"$v\"" \
          --imgsize="$SIZE" --render=cgal --autocenter --camera="$CAM" \
          "$SRC" 2>&1) || true
  if printf '%s' "$log" | grep -q 'Current top level object is empty'; then
    echo "EMPTY -- no such view in $SRC"; exit 1
  fi
  [ -s "$png" ] || { echo "RENDER FAILED"; printf '%s\n' "$log" | tail -3 >&2; exit 1; }
  echo "$(wc -c < "$png") bytes"
done
