#!/usr/bin/env bash
# Export the simple parts -- the ones whose .scad top level already IS the print
# plate, so they need no driver file.
#
#   parts/build_parts.sh                 # every part marked default below
#   parts/build_parts.sh legs            # just that one
#   parts/build_parts.sh --list          # show the manifest, export nothing
#
# The diffuser frame and the keycap stems are NOT here: they are generated or
# parameterised and have their own loops (parts/diffuser/build_frame.sh,
# parts/keycap_stem/build_stems.sh).  Everything else in the tree is still
# exported by hand from the OpenSCAD GUI.
#
# Why this exists: legs.scad had no build step, and its export had been
# committed under an unrelated name (case_ins_r2.stl) in a different folder, so
# nothing tied the two together and the mesh could drift from its source
# unnoticed -- it took a re-export and a mesh compare to work out what the part
# even was.
set -euo pipefail

cd "$(dirname "$0")/.."                       # repo root

#      name      default  source                    output
PARTS="
legs      yes  parts/legs/legs.scad         parts/export/legs/legs_r2_8p.stl
led_caps  no   parts/diffuser/led_caps.scad parts/export/diffuser/led_caps_4x19p.stl
"
# led_caps is the superseded earlier diffuser generation and no mesh for it is
# committed, so it is opt-in: name it explicitly to build it.

want=(); do_list=0
while [ $# -gt 0 ]; do
  case "$1" in
    --list) do_list=1 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 64 ;;
    *)  want+=("$1") ;;
  esac
  shift
done

command -v openscad >/dev/null || { echo "openscad not on PATH" >&2; exit 69; }


# Keep the committed bytes when only the facet order moved -- see the helper
# for why the comparison is rounded.
settle() {
  python3 parts/settle_mesh.py "$1"
}

printf '%-10s %-30s %s\n' NAME SOURCE OUTPUT
echo "$PARTS" | while read -r name def src out; do
  [ -n "${name:-}" ] || continue
  if [ ${#want[@]} -gt 0 ]; then
    printf '%s\n' "${want[@]}" | grep -qx "$name" || continue
  elif [ "$def" != yes ]; then
    continue
  fi
  printf '%-10s %-30s %s ' "$name" "$src" "$out"
  [ "$do_list" = 1 ] && { echo; continue; }

  [ -f "$src" ] || { echo "MISSING SOURCE"; exit 1; }
  mkdir -p "$(dirname "$out")"
  # openscad exits 1 for an empty result and 1 for a syntax error alike, so test
  # for the marker before trusting the exit code.
  log=$(openscad -o "$out" --export-format binstl "$src" 2>&1) || true
  if printf '%s' "$log" | grep -q 'Current top level object is empty'; then
    echo "EMPTY -- nothing at the top level of $src"; exit 1
  fi
  [ -s "$out" ] || { echo "EXPORT FAILED"; printf '%s\n' "$log" | tail -3 >&2; exit 1; }
  settle "$out"
done
