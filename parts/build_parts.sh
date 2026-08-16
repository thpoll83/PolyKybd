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

# OpenSCAD does not emit facets in a stable order between runs, and different
# builds of it disagree in the last few float digits, so a re-export of an
# UNCHANGED part still rewrites the whole mesh.  Compare rounded (a micron is
# far below anything printable) and put the committed bytes back when only that
# noise moved -- otherwise every run shows up as a multi-MB diff.
settle() {
  python3 - "$1" <<'PY'
import struct, subprocess, sys
p = sys.argv[1]
r = subprocess.run(['git', 'show', f'HEAD:{p}'], capture_output=True)
if r.returncode:
    print('new'); sys.exit(0)
def key(b, nd=3):
    n = struct.unpack('<I', b[80:84])[0]
    if len(b) != 84 + 50 * n:
        return None                       # not a binary STL -- never claim equal
    return sorted(tuple(sorted(round(x, nd) for x in
                              struct.unpack('<9f', b[84+50*i+12:84+50*i+48])))
                  for i in range(n))
new = open(p, 'rb').read()
a, b = key(r.stdout), key(new)
if a is not None and a == b:
    open(p, 'wb').write(r.stdout)         # same solid -- keep the committed bytes
    print('unchanged')
else:
    print('CHANGED')
PY
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
