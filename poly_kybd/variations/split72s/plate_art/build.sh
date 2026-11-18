#!/usr/bin/env bash
# Rebuild the plate artwork from the photo and the trace settings:
#   photo + trace_settings.json -> plate_art_tabletB_mask.png -> plate_art_tabletB.svg
# Needs Python 3 with numpy and Pillow, potrace, and Node with Playwright (Chromium).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
study="$here/../layout_study"
tmp="$(mktemp -d)"
mask="$here/plate_art_tabletB_mask.png"
svg="$here/plate_art_tabletB.svg"
# on any exit: drop the temp folder and staged copies; drop a backup once its file is in place
cleanup() {
    rm -rf "$tmp"
    rm -f "$mask.new" "$svg.new"
    if [ -e "$mask" ]; then rm -f "$mask.old"; fi
    if [ -e "$svg" ]; then rm -f "$svg.old"; fi
}
trap cleanup EXIT
python3 "$study/make_trace_tool.py" --image "$here/tabletB_verso_photo.jpg" --out "$tmp/tool.html"
node "$here/export_mask.js" "$tmp/tool.html" "$here/trace_settings.json" "$tmp"
# scale the SVG with the resolution of the mask itself (the page clamps the setting)
python3 "$here/trace_svg.py" "$tmp/mask.png" "$tmp/plate.svg" "$(cat "$tmp/res.txt")"

# publish the pair together: stage both next to the targets, keep the old pair, and put it
# back if either rename fails
cp "$tmp/mask.png" "$mask.new"
cp "$tmp/plate.svg" "$svg.new"
cp -p "$mask" "$mask.old"
cp -p "$svg" "$svg.old"
if mv -f "$mask.new" "$mask" && mv -f "$svg.new" "$svg"; then
    rm -f "$mask.old" "$svg.old"
else
    mv -f "$mask.old" "$mask"
    mv -f "$svg.old" "$svg"
    echo "publishing failed; the previous mask and SVG are back in place" >&2
    exit 1
fi
