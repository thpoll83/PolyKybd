#!/usr/bin/env bash
# Render the profile lineup pictures used by the top-level README.
#
#   parts/keycap_stem/render_profiles.sh            # all four, into images/
#   parts/keycap_stem/render_profiles.sh curved     # just that view
#   parts/keycap_stem/render_profiles.sh --out /tmp # somewhere else
#   parts/keycap_stem/render_profiles.sh --blender /path/to/blender
#                                   # same camera and axes, shaded by Blender
#                                   # (render_profiles_blender.py); the docs'
#                                   # Keycap stems pictures come from this
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
# 78 deg of elevation is the compromise that still shows the tops (so the
# engraved revision reads) while keeping the row close enough to side-on that
# each cap's angle is legible against the axis line.
CAM=0,0,0,78,0,90,150
SIZE=1300,430
# The AXES ARE THE POINT, not chrome: the horizontal axis line is the reference
# a reader measures each profile's cap angle against, and dropping it (as a
# first version of this script did) leaves the pictures pretty and unreadable --
# five tilted caps with nothing to tell you what they are tilted relative to.
VIEWOPTS=axes

want=()
while [ $# -gt 0 ]; do
  case "$1" in
    --out) [ $# -ge 2 ] || { echo "--out needs a directory" >&2; exit 64; }
           OUT="$2"; shift ;;
    --blender) [ $# -ge 2 ] || { echo "--blender needs the blender binary" >&2; exit 64; }
           BLENDER="$2"; shift ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 64 ;;
    *)  want+=("$1") ;;
  esac
  shift
done

# An unknown view name would otherwise match nothing, render nothing, and exit
# 0 -- a script that reports success having produced no image.
for w in ${want[@]+"${want[@]}"}; do
  printf '%s\n' $VIEWS | grep -qx "$w" || {
    echo "unknown view: $w (have: $VIEWS)" >&2; exit 64; }
done

command -v openscad >/dev/null || { echo "openscad not on PATH" >&2; exit 69; }
if [ -z "${BLENDER:-}" ]; then
  command -v xvfb-run >/dev/null || { echo "xvfb-run not on PATH (apt-get install xvfb)" >&2; exit 69; }
fi

# The engraving asks for "Noto:style=Bold". fontconfig has no family "Noto",
# and where only "Noto Sans" is installed (build_stems.sh --fetch-font) it
# substitutes another face (Inter in the cloud container) without a word.
# Alias "Noto" to "Noto Sans" for this run when that is what is installed.
if ! fc-match "Noto:style=Bold" 2>/dev/null | grep -qi noto \
   && fc-match "Noto Sans:style=Bold" 2>/dev/null | grep -qi noto; then
  FONTCONFIG_FILE=$(mktemp --suffix=.conf)
  cat > "$FONTCONFIG_FILE" <<'CONF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <include ignore_missing="yes">/etc/fonts/fonts.conf</include>
  <alias binding="same"><family>Noto</family><prefer><family>Noto Sans</family></prefer></alias>
</fontconfig>
CONF
  export FONTCONFIG_FILE
  trap 'rm -f "$FONTCONFIG_FILE"' EXIT
fi

# Same trap as the exporters: openscad exits 1 for an empty result and 1 for a
# syntax error alike, so test for the marker before trusting the exit code.  An
# empty result here means `view` matched none of the branches.
#
# Render to a temporary file and move it into place only on success.  Writing
# straight to $png would leave the PREVIOUS run's image sitting there after a
# failed render, and `[ -s "$png" ]` would then pass -- reporting success for a
# picture this invocation did not produce, which is the worst outcome for a file
# whose whole job is to be current.
mkdir -p "$OUT"
for v in $VIEWS; do
  if [ ${#want[@]} -gt 0 ]; then
    printf '%s\n' "${want[@]}" | grep -qx "$v" || continue
  fi
  png="$OUT/profile_$v.png"
  tmp="$OUT/.profile_$v.$$.png"
  printf '%-18s %s ' "$v" "$png"
  if [ -n "${BLENDER:-}" ]; then
    stl="$OUT/.profile_$v.$$.stl"
    if log=$(openscad -o "$stl" --export-format binstl -D "view=\"$v\"" "$SRC" 2>&1) \
       && log=$(printf '%s\n' "$log"; "$BLENDER" -b --python parts/keycap_stem/render_profiles_blender.py \
                  -- "$stl" "$tmp" 2>&1); then status=0; else status=$?; fi
    rm -f "$stl"
  elif log=$(xvfb-run -a openscad -o "$tmp" -D "view=\"$v\"" \
             --imgsize="$SIZE" --render=cgal --autocenter --camera="$CAM" \
             --view="$VIEWOPTS" "$SRC" 2>&1); then status=0; else status=$?; fi
  if printf '%s' "$log" | grep -q 'Current top level object is empty'; then
    rm -f "$tmp"; echo "EMPTY -- no such view in $SRC"; exit 1
  fi
  [ "$status" -eq 0 ] && [ -s "$tmp" ] || {
    rm -f "$tmp"; echo "RENDER FAILED"; printf '%s\n' "$log" | tail -3 >&2; exit 1; }
  mv "$tmp" "$png"
  echo "$(wc -c < "$png") bytes"
done
