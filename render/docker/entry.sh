#!/bin/bash
# The image's entry point, run from the PolyKybd checkout.
#
#   scene                 export both boards (KiCad) and build render/out/hero.blend
#   [width] [samples] [out dir]   the tutorial video (render/tutorial_build.sh)
set -euo pipefail
if [ "${1:-}" = "scene" ]; then
    render/export_boards.sh
    # the scene is saved before its test render, so a small render is enough
    blender -b --python render/blender_scene.py -- \
        render/out/split72_left.wrl render/out/split72_right.wrl render/out/hero.png 16 640
    ls -la render/out/hero.blend
    exit 0
fi
exec render/tutorial_build.sh "$@"
