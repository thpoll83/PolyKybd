#!/usr/bin/env bash
# Export both split72 boards, with every 3D model, for an external renderer.
#
#   render/export_boards.sh            -> render/out/split72_{left,right}.wrl  (VRML, for Blender)
#   render/export_boards.sh --png      -> also KiCad's own raytraced PNG of each half
#
# VRML, not GLB/STEP: KiCad's GLB and STEP exporters go through OpenCASCADE,
# which drops every .wrl model. The keycaps, stems, displays and switches are
# all .wrl, so a GLB comes out as a bare populated PCB. The VRML exporter uses
# the 3D viewer's model loader and keeps both .wrl and .step models.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
boards="$here/../poly_kybd"
out="$here/out"; mkdir -p "$out"
: "${KICAD9_3DMODEL_DIR:=/usr/share/kicad/3dmodels}"; export KICAD9_3DMODEL_DIR
run() { if [ -z "${DISPLAY:-}" ] && command -v xvfb-run >/dev/null; then xvfb-run -a "$@"; else "$@"; fi; }
log=$(mktemp); trap 'rm -f "$log"' EXIT
# run kicad-cli, show only the lines matching $1, and fail if it fails:
# filtering through `grep ... || true` used to hide a failed export
filtered() {
    local pattern=$1; shift
    if ! run "$@" >"$log" 2>&1; then cat "$log" >&2; echo "failed: $*" >&2; exit 1; fi
    grep -iE "$pattern" "$log" || true
}
for side in left right; do
    pcb="$boards/poly_kybd_split72_$side.kicad_pcb"
    filtered 'not found|could not' kicad-cli pcb export vrml -f --units mm -o "$out/split72_$side.wrl" "$pcb"
    if [ "${1:-}" = "--png" ]; then
        filtered 'error' kicad-cli pcb render -o "$out/split72_${side}_kicad.png" -w 1600 -h 900 \
            --rotate '-40,0,0' --perspective --quality high --floor "$pcb"
    fi
done
ls -la "$out"
