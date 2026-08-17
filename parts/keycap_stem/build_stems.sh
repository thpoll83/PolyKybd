#!/usr/bin/env bash
# Export the keycap stem print plates (10 pieces per plate).
#
#   parts/keycap_stem/build_stems.sh                       # every variant
#   parts/keycap_stem/build_stems.sh 1U_R2 1U25_R3         # matching ones only
#   parts/keycap_stem/build_stems.sh --list                # show them, export nothing
#   parts/keycap_stem/build_stems.sh --fetch-font          # install Noto per-user first
#
# There is no profile table in this script and no generated driver file: each
# plate is its own .scad in variants/, and this walks that directory.  So the
# thing you export is the thing you can open in the GUI, and adding a plate is
# adding a file rather than editing this script.
#
# That layout is the fix for how the curved R2..R5 plates went missing from
# revAlpha for a whole revision: the profile set used to exist only as
# commented-out calls at the bottom of keycap_stem.scad, which you uncommented
# one line at a time to export.
#
# Output name = variant name, so variants/<x>.scad -> parts/export/keycap_stem/<x>.stl.
set -euo pipefail

cd "$(dirname "$0")/../.."                  # repo root
SRC=parts/keycap_stem/variants
OUT=parts/export/keycap_stem

want=(); do_list=0; do_fetch=0
while [ $# -gt 0 ]; do
  case "$1" in
    --list)  do_list=1 ;;
    --fetch-font) do_fetch=1 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 64 ;;
    *)  want+=("$1") ;;
  esac
  shift
done

# Same source and mechanism as the firmware's fonts/dl-fonts.sh (the `Noto Sans`
# entry of its noto-fonts.yaml).  Installed per-user, so no root is needed.  It
# is the variable font: fontconfig exposes its named instances, so
# `Noto:style=Bold` resolves to a real Bold rather than a synthesised one.
# ⚠️ This CHANGES which Noto fontconfig resolves, and the engraved glyphs are
# tessellated from whichever file wins -- so a re-export afterwards differs
# from meshes built against a distro-packaged Noto and settle reports CHANGED
# (measured: the variable font gives 46192 facets where the static Bold gives
# 44912, same volume and bounding box).  That is a real difference in the
# engraving, not noise the rounding can absorb, so use this to GET a Noto when
# there is none -- not on a machine that already has one.
NOTO_URL='https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf'
NOTO_DEST="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/polykybd/NotoSans.ttf"

fetch_noto() {
  mkdir -p "$(dirname "$NOTO_DEST")"
  echo "  fetch $NOTO_DEST"
  if command -v curl >/dev/null; then curl -fsSL "$NOTO_URL" -o "$NOTO_DEST"
  else                                wget -q "$NOTO_URL" -O "$NOTO_DEST"; fi
  fc-cache -f >/dev/null 2>&1 || true
}
[ "$do_fetch" = 1 ] && fetch_noto

command -v openscad >/dev/null || { echo "openscad not on PATH" >&2; exit 69; }

# The engraved revision uses `text_font = "Noto:style=Bold"`.  With no Noto
# installed fontconfig silently substitutes DejaVu -- the plate still exports,
# the glyphs are just the wrong shape, and nothing in the output says so.
if ! fc-match "Noto:style=Bold" 2>/dev/null | grep -qi noto; then
  echo "WARNING: no Noto font -- the engraved revision will render in a substitute face." >&2
  echo "         run with --fetch-font (per-user, no root), or apt-get install fonts-noto-core" >&2
fi

# Keep the committed bytes when only the facet order moved -- see the helper
# for why the comparison is rounded.
settle() {
  python3 parts/settle_mesh.py "$1"
}

shopt -s nullglob
variants=("$SRC"/*.scad)
[ ${#variants[@]} -gt 0 ] || { echo "no variants in $SRC" >&2; exit 1; }

mkdir -p "$OUT"
printf '%-42s %s\n' VARIANT OUTPUT
matched=0
for v in "${variants[@]}"; do
  name=$(basename "$v" .scad)
  if [ ${#want[@]} -gt 0 ]; then
    hit=0
    for w in "${want[@]}"; do case "$name" in *"$w"*) hit=1 ;; esac; done
    [ "$hit" = 1 ] || continue
  fi
  matched=$((matched + 1))
  out="$OUT/$name.stl"
  printf '%-42s %s ' "$name" "$out"
  [ "$do_list" = 1 ] && { echo; continue; }

  # openscad exits 1 for an empty result and 1 for a syntax error alike, so test
  # for the marker before trusting the exit code.  An empty result here would
  # mean the variant's `include <../keycap_stem.scad>` failed to resolve.
  log=$(openscad -o "$out" --export-format binstl "$v" 2>&1) || true
  if printf '%s' "$log" | grep -q 'Current top level object is empty'; then
    echo "EMPTY -- $v produced no geometry"; exit 1
  fi
  [ -s "$out" ] || { echo "EXPORT FAILED"; printf '%s\n' "$log" | tail -3 >&2; exit 1; }
  settle "$out"
done

[ "$matched" -gt 0 ] || { echo "no variant matched: ${want[*]}" >&2; exit 64; }
