#!/bin/bash
# Render preview variants of render/closeup_view.py one after another.
#
#   variants.sh <base.sh> <outdir> <name> "<VAR=val ...>" [<name> "<VAR=val ...>" ...]
#
# <base.sh> is sourced and must set two arrays:
#   BASE_ENV=(PK_RGB=170,280 PK_EMIT=6000 ...)    # the look being tuned
#   VIEW=(screens_layer1 0.45 0.45 0.085 48 -15 22 6.3)   # closeup_view args after samples/width
# Each variant's VAR=val pairs come after BASE_ENV, so they override it.
# SAMPLES (default 64) and WIDTH (default 1400) set the preview quality.
# Waits for any running Blender render first: two at once on 4 CPUs is slower
# than one after the other. Writes <outdir>/<name>.png and <name>.log.
set -u
base=$1; out=$2; shift 2
source "$base"
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
blender=${BLENDER:-/tmp/blender-4.1.1-linux-x64/blender}
while pgrep -f "[b]lender -b" >/dev/null; do sleep 20; done
cd "$repo"
while [ $# -ge 2 ]; do
  name=$1; vars=$2; shift 2
  # shellcheck disable=SC2086  # vars is a list of VAR=val words
  env "${BASE_ENV[@]}" $vars "$blender" -b render/out/hero.blend --python render/closeup_view.py -- \
      "$out/$name.png" "${SAMPLES:-64}" "${WIDTH:-1400}" "${VIEW[@]}" > "$out/$name.log" 2>&1
  if grep -q Traceback "$out/$name.log" || [ ! -f "$out/$name.png" ]; then
    echo "FAILED $name (see $out/$name.log)"
  else
    echo "ok $name"
  fi
done
