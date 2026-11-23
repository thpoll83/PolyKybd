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
keep_backups=0
cleanup() {
    rm -rf "$tmp"
    rm -f "$mask.new" "$svg.new"
    if [ "$keep_backups" = 1 ]; then return; fi
    if [ -e "$mask" ]; then rm -f "$mask.old"; fi
    if [ -e "$svg" ]; then rm -f "$svg.old"; fi
}
trap cleanup EXIT
python3 "$study/make_trace_tool.py" --image "$here/tabletB_verso_photo.jpg" --out "$tmp/tool.html"
node "$here/export_mask.js" "$tmp/tool.html" "$here/trace_settings.json" "$tmp/out"
# scale the SVG with the resolution of the mask itself (the page clamps the setting)
python3 "$here/trace_svg.py" "$tmp/out/mask.png" "$tmp/plate.svg" "$(cat "$tmp/out/res.txt")"

# publish the pair together: stage both next to the targets, keep the old pair, and put it
# back if either rename fails
cp "$tmp/out/mask.png" "$mask.new"
cp "$tmp/plate.svg" "$svg.new"
# back up only the outputs that exist (one may have been deleted to force a rebuild)
had_mask=0; had_svg=0
if [ -e "$mask" ]; then cp -p "$mask" "$mask.old"; had_mask=1; fi
if [ -e "$svg" ]; then cp -p "$svg" "$svg.old"; had_svg=1; fi
if mv -f "$mask.new" "$mask" && mv -f "$svg.new" "$svg"; then
    rm -f "$mask.old" "$svg.old"
else
    # back to the previous state: the old file where there was one, none where there was none.
    # Try both restores; if one fails, keep every backup and say where it is.
    ok=1
    if [ "$had_mask" = 1 ]; then mv -f "$mask.old" "$mask" || ok=0; else rm -f "$mask" || ok=0; fi
    if [ "$had_svg" = 1 ]; then mv -f "$svg.old" "$svg" || ok=0; else rm -f "$svg" || ok=0; fi
    if [ "$ok" = 1 ]; then
        echo "publishing failed; the previous mask and SVG are back in place" >&2
    else
        keep_backups=1
        echo "publishing and restoring failed; backups kept: $mask.old $svg.old" >&2
    fi
    exit 1
fi
