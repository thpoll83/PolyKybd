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
# x y w h are read in the SVG's own user units -- for our sheets that is MILLIMETRES
# with the origin at the top-left of the page, so a region is just the numbers you
# would measure on the printed sheet.  ⚠️ `drawing.py` works in SHEET coordinates
# (origin at the page CENTRE, +y UP); convert first:
#       x_file = x_sheet + PAGE_W/2        y_file = PAGE_H/2 - y_sheet
# For the stem sheets that is x + 210 and 148.5 - y.
set -u

die() { echo "svg_view.sh: $*" >&2; exit 2; }

[ $# -ge 2 ] || die "usage: svg_view.sh out.png file.svg [x y w h [px_per_unit]]"
out=$1; src=$2; shift 2
[ -f "$src" ] || die "no such file: $src"
case "$out" in *.png) ;; *) die "output must be a .png: $out";; esac

CHROME=${CHROME:-/opt/pw-browsers/chromium}
[ -x "$CHROME" ] || CHROME=$(command -v chromium || command -v chromium-browser) \
  || die "no chromium; set CHROME=/path/to/chromium"

abs=$(cd "$(dirname "$src")" && pwd)/$(basename "$src")

# A malformed SVG renders as a BLANK PAGE rather than partly, so a bad crop and a
# broken document look identical.  Rule the second one out here instead of staring
# at white pixels.
python3 - "$abs" <<'PY' || die "the SVG is not well-formed XML (a browser would show a blank page)"
import sys, xml.etree.ElementTree as ET
ET.parse(sys.argv[1])
PY

# The viewBox is what maps the file's units onto the rendered image.
read -r vbx vby vbw vbh < <(python3 - "$abs" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read(4096)
m = re.search(r'viewBox="\s*([-\d.eE]+)[\s,]+([-\d.eE]+)[\s,]+([-\d.eE]+)[\s,]+([-\d.eE]+)', s)
if m:
    print(" ".join(m.groups()))
else:                       # no viewBox: fall back to width/height, else 0 0 100 100
    w = re.search(r'\bwidth="([\d.]+)', s)
    h = re.search(r'\bheight="([\d.]+)', s)
    print("0 0 %s %s" % (w.group(1) if w else 100, h.group(1) if h else 100))
PY
)

if [ $# -eq 0 ]; then
    x=$vbx y=$vby w=$vbw h=$vbh
    ppu=$(python3 -c "print(1600.0/float('$vbw'))")
else
    [ $# -ge 4 ] || die "a region needs four numbers: x y w h [px_per_unit]"
    x=$1 y=$2 w=$3 h=$4
    ppu=${5:-12}
fi

read -r imgw left top winw winh < <(python3 - "$vbx" "$vby" "$vbw" "$x" "$y" "$w" "$h" "$ppu" <<'PY'
import sys
vbx, vby, vbw, x, y, w, h, ppu = (float(a) for a in sys.argv[1:9])
print("%.4f %.4f %.4f %d %d" % (vbw * ppu, -(x - vbx) * ppu, -(y - vby) * ppu,
                                max(1, round(w * ppu)), max(1, round(h * ppu))))
PY
)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/v.html" <<EOF
<html><body style="margin:0;background:#fff;overflow:hidden">
<div style="width:${winw}px;height:${winh}px;overflow:hidden;position:relative">
<img src="file://$abs" style="position:absolute;width:${imgw}px;left:${left}px;top:${top}px">
</div></body></html>
EOF

"$CHROME" --headless --no-sandbox --disable-gpu --hide-scrollbars \
          --window-size="$winw,$winh" --screenshot="$out" \
          "file://$tmp/v.html" >/dev/null 2>&1

[ -s "$out" ] || die "chromium wrote no output"
echo "wrote $out  (${winw}x${winh} px, ${ppu} px/unit, region ${x},${y} ${w}x${h})"
