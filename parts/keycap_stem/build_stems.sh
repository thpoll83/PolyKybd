#!/usr/bin/env bash
# Export the keycap stem print plates (10 pieces per plate).
#
#   parts/keycap_stem/build_stems.sh                  # every profile, both widths
#   parts/keycap_stem/build_stems.sh R2 R3            # only those profiles
#   parts/keycap_stem/build_stems.sh --width 1U R5    # one width
#   parts/keycap_stem/build_stems.sh --list           # show the table, export nothing
#   parts/keycap_stem/build_stems.sh --fetch-font     # install Noto per-user first
#
# The profile table below IS the definition of a row.  It used to live only as
# commented-out top-level calls at the bottom of keycap_stem.scad, exported by
# uncommenting one line at a time in the GUI -- which is why the curved R2..R5
# plates were missing from revAlpha for a whole revision while the stepped ones
# were current.  Add a row here, not a comment there.
#
#   angle     tilt of the cap in degrees (rotate about x)
#   extra_len how far the stem is raised, mm
#   label     engraved on the plate, prefixed to the revision glyph
#
# R1..R5 are the CURVED profile (row 1 = closest to the user), S1/S/S5 the
# STEPPED one.  Note R1 and S1 are deliberately the same geometry (angle 5,
# extra_len 0.5) and differ only in the engraving -- that is what the source
# says, not a copy/paste slip.
set -euo pipefail

cd "$(dirname "$0")/../.."                  # repo root
SRC=parts/keycap_stem                       # keycap_stem.scad lives here
OUT=parts/export/keycap_stem
REV="α"                                     # matches `revision` in keycap_stem.scad

#             angle  extra_len  label
PROFILES="
R1            5      0.5        1
R2           -5      1          2
R3            0      0          3
R4            5      1.5        4
R5           10      4          5
S1            5      0.5        S1
S            -7      1.5        S
S5           10      2.5        S5
"

want_profiles=(); want_widths=(1U 1U25); do_list=0; do_fetch=0
while [ $# -gt 0 ]; do
  case "$1" in
    --list)  do_list=1 ;;
    --fetch-font) do_fetch=1 ;;
    --width) shift; want_widths=("$1") ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 64 ;;
    *)  want_profiles+=("$1") ;;
  esac
  shift
done

# Same source and mechanism as the firmware's fonts/dl-fonts.sh (the `Noto Sans`
# entry of its noto-fonts.yaml).  Installed per-user, so no root is needed.  It
# is the variable font: fontconfig exposes its named instances, so
# `Noto:style=Bold` resolves to a real Bold rather than a synthesised one.
NOTO_URL='https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf'
NOTO_DEST="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/polykybd/NotoSans.ttf"

fetch_noto() {
  mkdir -p "$(dirname "$NOTO_DEST")"
  echo "  fetch $NOTO_DEST"
  if command -v curl >/dev/null; then curl -fsSL "$NOTO_URL" -o "$NOTO_DEST"
  else                                wget -q "$NOTO_URL" -O "$NOTO_DEST"; fi
  fc-cache -f >/dev/null 2>&1 || true
}
[ "$do_fetch" = 1 ] && fetch_noto

command -v openscad >/dev/null || { echo "openscad not on PATH" >&2; exit 69; }

# The engraved revision uses `text_font = "Noto:style=Bold"`.  With no Noto
# installed fontconfig silently substitutes DejaVu -- the plate still exports,
# the glyphs are just the wrong shape, and nothing in the output says so.
if ! fc-match "Noto:style=Bold" 2>/dev/null | grep -qi noto; then
  echo "WARNING: no Noto font -- the engraved revision will render in a substitute face." >&2
  echo "         run with --fetch-font (per-user, no root), or apt-get install fonts-noto-core" >&2
fi

# OpenSCAD does not emit facets in a stable order between runs, so re-exporting
# an unchanged part still rewrites the whole binary blob.  Compare the solids
# and put the committed bytes back when only the ordering moved.
settle() {
  python3 - "$1" <<'PY'
import struct, subprocess, sys
p = sys.argv[1]
r = subprocess.run(['git', 'show', f'HEAD:{p}'], capture_output=True)
if r.returncode:
    print('new'); sys.exit(0)
def key(b):
    n = struct.unpack('<I', b[80:84])[0]
    if len(b) != 84 + 50 * n:
        return None                       # not a binary STL -- never claim equal
    return sorted(tuple(sorted(struct.unpack('<9f', b[84+50*i+12:84+50*i+48])))
                  for i in range(n))
new = open(p, 'rb').read()
a, b = key(r.stdout), key(new)
if a is not None and a == b:
    open(p, 'wb').write(r.stdout)         # identical solid -- keep committed bytes
    print('unchanged')
else:
    print('CHANGED')
PY
}

mkdir -p "$OUT"
printf '%-10s %6s %10s  %-6s %s\n' PROFILE ANGLE EXTRA_LEN LABEL OUTPUT
echo "$PROFILES" | while read -r prof ang xlen label; do
  [ -n "${prof:-}" ] || continue
  if [ ${#want_profiles[@]} -gt 0 ] && ! printf '%s\n' "${want_profiles[@]}" | grep -qx "$prof"; then
    continue
  fi
  for w in "${want_widths[@]}"; do
    case "$w" in
      1U)   mod=ten_connected_pieces_1U ;;
      1U25) mod=ten_connected_pieces_1U25 ;;
      *) echo "unknown width: $w (want 1U or 1U25)" >&2; exit 64 ;;
    esac
    out="$OUT/keycap_stem_rev${REV/α/Alpha}_${w}_${prof}_10p.stl"
    printf '%-10s %6s %10s  %-6s %s ' "$prof" "$ang" "$xlen" "$label" "$out"
    [ "$do_list" = 1 ] && { echo; continue; }

    # The driver must sit beside keycap_stem.scad: `use <>` resolves relative to
    # the .scad file, not the cwd.  A driver written elsewhere finds no modules
    # and exports an EMPTY plate -- which openscad reports the same way as a
    # syntax error, so check for the marker rather than trusting the exit code.
    tmp=$(mktemp "$SRC/_build_XXXXXX.scad")
    trap 'rm -f "$tmp"' EXIT
    # Trailing spaces in the label are load-bearing: the text is halign="center",
    # so the padding is what shifts the glyphs clear of the display cut-out.
    printf 'use <keycap_stem.scad>\n%s(angle=%s, extra_len=%s, txt="%-5s%s");\n' \
           "$mod" "$ang" "$xlen" "$label" "$REV" > "$tmp"
    log=$(openscad -o "$out" --export-format binstl "$tmp" 2>&1) || true
    rm -f "$tmp"; trap - EXIT
    if printf '%s' "$log" | grep -q 'Current top level object is empty'; then
      echo "EMPTY -- the driver found no geometry"; exit 1
    fi
    [ -s "$out" ] || { echo "EXPORT FAILED"; printf '%s\n' "$log" | tail -3 >&2; exit 1; }
    settle "$out"
  done
done
