#!/usr/bin/env bash
# Headless Chromium -> PNG of an SVG, whole or a REGION in the file's own units.
#
# The sibling of scad_view.sh, for the other half of the job: scad_view.sh looks at
# a model, this looks at a drawing that has already been generated.  It exists
# because reading one view out of an A3 sheet otherwise means hand-building an HTML
# wrapper and doing px/mm arithmetic for the crop, every single time -- which is how
# a session came to burn ~8 of them on one drawing, with two of the offsets wrong.
#
#   svg_view.sh out.png sheet.svg                      # whole document, 1600 px wide
#   svg_view.sh out.png sheet.svg 150 60 60 40         # region, in the FILE'S units
#   svg_view.sh out.png sheet.svg 150 60 60 40 24      # ...at 24 px per unit
#
# x y w h give the region's TOP-LEFT corner and its size, in the SVG's own user units
# -- for our sheets that is MILLIMETRES with the origin at the top-left of the page,
# so a region is the numbers you would measure on the printed sheet.
#
# ⚠️ `drawing.py` works in SHEET coordinates (origin at the page CENTRE, +y UP), so a
# BOX needs both of its y bounds converted and they SWAP: the file-space top comes
# from the sheet's HIGHER y.  For a sheet-space box x0..x1, y0..y1:
#       x = x0 + PAGE_W/2        w = x1 - x0
#       y = PAGE_H/2 - y1        h = y1 - y0
# For the stem sheets (420 x 297) that is x + 210 and 148.5 - y_high.  Converting the
# box's LOWER y instead puts the crop one box-height too far down.
set -u

die() { echo "svg_view.sh: $*" >&2; exit 2; }

[ $# -ge 2 ] || die "usage: svg_view.sh out.png file.svg [x y w h [px_per_unit]]"
out=$1; src=$2; shift 2
[ -f "$src" ] || die "no such file: $src"
case "$out" in *.png) ;; *) die "output must be a .png: $out";; esac
# ⚠️ Remove the target NOW, not just before the screenshot.  Anything that fails in
# between -- the parse, the calibration, the browser -- would otherwise leave the
# PREVIOUS run's image in place, and the whole point of the script is inspecting
# successive regions through one out.png, so that hands you a crop of somewhere else.
rm -f "$out"

CHROME=${CHROME:-/opt/pw-browsers/chromium}
[ -x "$CHROME" ] || CHROME=$(command -v chromium || command -v chromium-browser) \
  || die "no chromium; set CHROME=/path/to/chromium"

abs=$(cd "$(dirname "$src")" && pwd)/$(basename "$src")
HERE_PY=$(cd "$(dirname "$0")" && pwd)/_png.py
[ -f "$HERE_PY" ] || die "missing helper: $HERE_PY"

# ONE pass does both jobs, and it has to be the parser rather than a regex over the
# first few KB:
#  - a malformed SVG renders as a BLANK PAGE rather than partly, so a bad crop and a
#    broken document look identical -- rule the second out instead of staring at
#    white pixels;
#  - the viewBox is what maps the file's units onto the image, and a header long
#    enough to push it past a byte cap would otherwise fall through to a GUESSED
#    default and silently misscale every crop.
# `url` comes back percent-encoded, because a '#' in a path turns the rest of a
# file: URL into a fragment and a '"' ends the HTML attribute -- either loads
# nothing while Chromium still writes a perfectly nonempty white screenshot.
read -r vbx vby vbw vbh url < <(python3 - "$abs" <<'PY'
import re, sys, urllib.parse, xml.etree.ElementTree as ET

path = sys.argv[1]
try:
    root = ET.parse(path).getroot()
except ET.ParseError as exc:             # report it; a traceback here is just noise
    sys.exit("  %s" % exc)


def num(s, fallback):
    m = re.match(r"\s*([-+]?[\d.]+(?:[eE][-+]?\d+)?)", s or "")
    return m.group(1) if m else fallback


vb = (root.get("viewBox") or "").replace(",", " ").split()
if len(vb) == 4:
    x, y, w, h = vb
else:                                     # no viewBox: fall back to width/height
    x, y = "0", "0"
    w, h = num(root.get("width"), "100"), num(root.get("height"), "100")
print(x, y, w, h, urllib.parse.quote(path))
PY
) || die "cannot read the SVG: not well-formed XML (a browser would show a blank page)"

if [ $# -eq 0 ]; then
    x=$vbx y=$vby w=$vbw h=$vbh
    ppu=$(python3 -c "print(1600.0/float('$vbw'))")
else
    [ $# -ge 4 ] || die "a region needs four numbers: x y w h [px_per_unit]"
    x=$1 y=$2 w=$3 h=$4
    ppu=${5:-12}
fi

# ⚠️ Both rendered dimensions come from the viewBox, not the width alone.  Given only
# a width the browser derives the height from the file's INTRINSIC ratio, which an SVG
# is free to declare differently from its viewBox -- and then one px/unit holds
# horizontally and another vertically, so every vertical offset below is wrong.
read -r imgw imgh left top winw winh < <(python3 - "$vbx" "$vby" "$vbw" "$vbh" "$x" "$y" "$w" "$h" "$ppu" <<'PY'
import sys
vbx, vby, vbw, vbh, x, y, w, h, ppu = (float(a) for a in sys.argv[1:10])
print("%.4f %.4f %.4f %.4f %d %d" % (vbw * ppu, vbh * ppu,
                                     -(x - vbx) * ppu, -(y - vby) * ppu,
                                     max(1, round(w * ppu)), max(1, round(h * ppu))))
PY
)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/v.html" <<EOF
<html><body style="margin:0;background:#fff;overflow:hidden">
<div style="width:${winw}px;height:${winh}px;overflow:hidden;position:relative">
<img src="file://$url" style="position:absolute;width:${imgw}px;height:${imgh}px;left:${left}px;top:${top}px">
</div></body></html>
EOF

# ⚠️ `--window-size` is NOT the viewport: the page gets a BAND fewer pixels at the
# bottom (87 on this build, constant across sizes and across --headless/--headless=new),
# and the screenshot pads it with the page background.  So a naive crop silently loses
# its last rows AS WHITE -- which on a drawing is indistinguishable from "nothing is
# there", the same class of lie the blank-page check above exists to stop.  It is a
# property of the browser build, so it is MEASURED here rather than hard-coded: render
# a known full-bleed black page and find the last row that survived.
cat > "$tmp/cal.html" <<'CAL'
<html><body style="margin:0;background:#fff"><div style="width:8px;height:4000px;background:#000"></div></body></html>
CAL
"$CHROME" --headless --no-sandbox --disable-gpu --hide-scrollbars \
          --window-size=8,400 --screenshot="$tmp/cal.png" \
          "file://$tmp/cal.html" >/dev/null 2>&1 || die "chromium failed to run at all"
band=$(python3 "$HERE_PY" band "$tmp/cal.png") || die "could not calibrate the viewport"

# CHECK the exit status: testing only that the file is nonempty is what let a stale
# image pass as a fresh one (the removal above is the other half of that fix).
"$CHROME" --headless --no-sandbox --disable-gpu --hide-scrollbars \
          --window-size="$winw,$((winh + band))" --screenshot="$out" \
          "file://$tmp/v.html" >/dev/null 2>&1 || die "chromium failed (exit $?)"

[ -s "$out" ] || die "chromium wrote no output"
python3 "$HERE_PY" trim "$out" "$winh" || die "could not trim the calibration band"
echo "wrote $out  (${winw}x${winh} px, ${ppu} px/unit, region ${x},${y} ${w}x${h})"
