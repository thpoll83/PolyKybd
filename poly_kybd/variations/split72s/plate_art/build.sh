#!/usr/bin/env bash
# Rebuild the plate artwork from the photo and the trace settings:
#   photo + trace_settings.json -> plate_art_tabletB_mask.png -> plate_art_tabletB.svg
# Needs Python 3 with numpy and Pillow, potrace, and Node with Playwright (Chromium).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
study="$here/../layout_study"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
python3 "$study/make_trace_tool.py" --image "$here/tabletB_verso_photo.jpg" --out "$tmp/tool.html"
node "$here/export_mask.js" "$tmp/tool.html" "$here/trace_settings.json" "$tmp"
cp "$tmp/mask.png" "$here/plate_art_tabletB_mask.png"
python3 "$here/trace_svg.py" "$here/plate_art_tabletB_mask.png" "$here/plate_art_tabletB.svg"
