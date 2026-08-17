#!/usr/bin/env bash
# Regenerate the one-piece LED diffuser frame end to end and verify it.
#
#   parts/diffuser/build_frame.sh            # generate, export everything, check
#   parts/diffuser/build_frame.sh --no-4x    # skip the stacked exports (the slow half)
#   parts/diffuser/build_frame.sh --check    # verify the committed STLs, export nothing
#
# Run this after ANY edit to parts/diffuser/diffuser.scad or
# parts/diffuser/gen_diffuser_frame.py.
# Doing the steps by hand is where they get missed: a diffuser.scad change alters
# every frame STL *and* both stacked ones, and forgetting the stacked pair leaves
# them silently a revision behind (happened twice while this part was developed --
# once also leaving the stack pitch wrong for the new part height).
#
# The 4x exports are minutes each, hence --no-4x for a quick loop; just do not
# commit without a full run.
set -euo pipefail

cd "$(dirname "$0")/../.."          # repo root
GEN=parts/diffuser/gen_diffuser_frame.py
CHECK=parts/diffuser/check_frame.py
do_4x=1; do_build=1

for a in "$@"; do
  case "$a" in
    --no-4x) do_4x=0 ;;
    --check) do_build=0 ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 64 ;;
  esac
done

# openscad exports geometry without a display; only PNG rendering needs xvfb.
command -v openscad >/dev/null || { echo "openscad not on PATH" >&2; exit 69; }


# Keep the committed bytes when only the facet order moved -- see the helper
# for why the comparison is rounded.
settle() {
  python3 parts/settle_mesh.py "$1"
}

export_scad() {   # <out.stl> <scad source line>
  local out=$1 src=$2 tmp
  tmp=$(mktemp parts/diffuser/_build_XXXXXX.scad)   # must sit beside the sources:
  printf '%s\n' "$src" > "$tmp"                    # `use <>` is relative to the .scad file
  trap 'rm -f "$tmp"' RETURN
  printf '  %-38s ' "$out"
  openscad -o "$out" --export-format asciistl "$tmp" >/dev/null 2>&1 \
    || { echo "EXPORT FAILED"; return 1; }
  settle "$out"
}

if [ "$do_build" = 1 ]; then
  echo "generating the frames from the plate PCB"
  python3 "$GEN"

  echo "exporting"
  for s in left right; do
    export_scad "parts/export/diffuser/diffuser_frame_$s.stl" \
      "use <diffuser_frame_$s.scad>
diffuser_frame_$s();"
  done
  if [ "$do_4x" = 1 ]; then
    for s in left right; do
      export_scad "parts/export/diffuser/diffuser_frame_${s}_4x.stl" \
        "use <diffuser_frame_stacked.scad>
diffuser_frame_${s}_stacked(4);"
    done
  else
    echo "  (skipping the 4x stacked exports -- --no-4x)"
  fi
fi

echo "verifying"
python3 "$CHECK"
