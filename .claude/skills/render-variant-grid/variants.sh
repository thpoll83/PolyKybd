#!/bin/bash
# Render preview variants of render/closeup_view.py one after another.
#
#   variants.sh <base.sh> <outdir> <name> "<VAR=val;VAR=val>" [<name> "<...>" ...]
#
# <base.sh> is sourced and must set two arrays:
#   BASE_ENV=(PK_RGB=170,280 PK_EMIT=6000 ...)    # the look being tuned
#   VIEW=(screens_layer1 0.45 0.45 0.085 48 -15 22 6.3)   # closeup_view args after samples/width
# A variant's overrides are separated by ";" (values may hold spaces and
# commas, as PK_LOOK and PK_RGB do) and come after BASE_ENV, so they win.
# SAMPLES (default 64) and WIDTH (default 1400) set the preview quality.
# One queue at a time (a lock), and each queue waits for any running Blender
# render first: two at once on 4 CPUs finish later than one after the other.
# Writes <outdir>/<name>.png and <name>.log; a variant counts as ok only when
# Blender exits 0, logs no Traceback and writes a new PNG.
set -u
base=$1; out=$2; shift 2
source "$base"
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
blender=${BLENDER:-/tmp/blender-4.1.1-linux-x64/blender}
mkdir -p "$out" && [ -w "$out" ] || { echo "cannot write to $out"; exit 1; }
out=$(cd "$out" && pwd)
exec 9>"${TMPDIR:-/tmp}/polykybd-render-variant-grid.lock"
flock 9
while pgrep -f "[b]lender -b" >/dev/null; do sleep 20; done
cd "$repo"
while [ $# -ge 2 ]; do
  name=$1; IFS=';' read -ra over <<< "$2"; shift 2
  rm -f "$out/$name.png" "$out/$name.log"
  env "${BASE_ENV[@]}" "${over[@]}" "$blender" -b render/out/hero.blend --python render/closeup_view.py -- \
      "$out/$name.png" "${SAMPLES:-64}" "${WIDTH:-1400}" "${VIEW[@]}" > "$out/$name.log" 2>&1
  status=$?
  if [ $status -ne 0 ] || grep -q Traceback "$out/$name.log" || [ ! -f "$out/$name.png" ]; then
    echo "FAILED $name (exit $status, see $out/$name.log)"
  else
    echo "ok $name"
  fi
done
