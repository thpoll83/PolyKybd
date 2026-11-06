#!/bin/bash
# The image's entry point, run from the PolyKybd checkout.
#
#   scene                 export both boards (KiCad) and build render/out/hero.blend
#   [width] [samples] [out dir]   the tutorial video (render/tutorial_build.sh)
set -euo pipefail
# ⚠️ with docker run --user, HOME is / and not writable. kicad-cli then has no config
# directory and exports the bare board with NO 3D models, and still reports success.
# Blender wants a writable HOME too.
if ! { [ -n "${HOME:-}" ] && [ -w "$HOME" ]; }; then
    export HOME=$(mktemp -d /tmp/home.XXXXXX)
fi
if [ "${1:-}" = "scene" ]; then
    render/export_boards.sh
    # the scene is saved before its test render, so a small render is enough
    blender -b --python render/blender_scene.py -- \
        render/out/split72_left.wrl render/out/split72_right.wrl render/out/hero.png 16 640
    [ -f render/out/hero.blend ] || { echo "blender_scene.py failed: no render/out/hero.blend" >&2; exit 1; }
    ls -la render/out/hero.blend
    exit 0
fi
exec render/tutorial_build.sh "$@"
