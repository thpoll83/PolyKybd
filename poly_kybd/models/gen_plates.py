"""Export the switch plates as VRML models for the split72 boards' 3D view.

    python poly_kybd/models/gen_plates.py          (needs kicad-cli, KiCad 9)

The plate PCBs are not edited. Each is copied to a temp folder, its Edge.Cuts
outline is repaired in the copy, and kicad-cli exports that copy:

- zero-length segments are dropped (36 per plate), and
- endpoints within 0.02 mm are snapped together. The expansion-port cut-out
  misses closing by 0.01 mm on both plates (58.1356 vs 58.1456 on
  plate_left), and on plate_left KiCad then rejects the whole outline and
  exports the plate as its bounding rectangle.

Each plate goes on the half its name says, FLIPPED: the Rosetta artwork is
on the plate PCB's B.SilkS and faces up, and the "< LEFT SIDE >" /
"< RIGHT SIDE >" labels on F.SilkS face the switch PCB. Flipped, plate_left
matches the left board's outline, switch cut-outs and status-display cut-out
with x_board = 259.7096 - x_plate, and plate_right the right board with
x_board = 259.6016 - x_plate (y unchanged). Unflipped, each plate also fits
the OTHER half, because the halves are mirror images; the artwork side is
what decides.

The plate is an aluminium PCB, so every material darker than mid-grey in the
export (KiCad writes the stackup's green mask and a black board body) is
rewritten as brushed aluminium; the white silkscreen art is kept.

The output is gzipped VRML (.wrz, which KiCad reads): 2.2 MB instead of 9.8 MB,
almost all of it the plate's silkscreen art.

The VRML origin is put on the plate point above SW_K_1, in 0.1 inch units,
so each board attaches the plate to SW_K_1 at scale 1, rotate 0 180 0 (the
flip: x mirrored, B side up) and z = 4.2 (plate mid-plane; plate top 5.0 mm
above the PCB top, the MX plate height).
"""
import gzip
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARDS = HERE.parent

# (plate file, model written, plate-frame point that sits above SW_K_1)
PLATES = [
    ("poly_kybd_split72_plate_left.kicad_pcb", "plate_split72_left.wrz", (259.7096 - 48.4915, 50.6615)),
    ("poly_kybd_split72_plate_right.kicad_pcb", "plate_split72_right.wrz", (259.6016 - 73.152, 50.66025)),
]
SNAP = 0.02
ALUMINIUM = ("diffuseColor 0.58 0.59 0.61\n   shininess 0.6\n"
             "   specularColor 0.9 0.9 0.92\n   transparency 0")


def aluminium(wrl):
    """Recolour the mask and board-body materials of a kicad-cli VRML export."""
    def swap(m):
        rgb = [float(v) for v in m.group(1).split()]
        if sum(rgb) / 3 >= 0.5:                 # silkscreen
            return m.group(0)
        return m.group(0)[:m.start(1) - m.start(0) - len("diffuseColor ")] + ALUMINIUM
    pat = r"diffuseColor ([-\d.e ]+?)\s+(?:emissiveColor[^\n]*\s+)?shininess [-\d.e]+\s+specularColor [-\d.e ]+?\s+transparency [-\d.e]+"
    return re.sub(pat, swap, wrl)


def edge_items(text):
    """(start, end) spans of top-level gr_line/gr_arc items on Edge.Cuts."""
    for m in re.finditer(r"\n  \(gr_(?:line|arc) ", text):
        s = m.start() + 3
        depth, i = 0, s
        while True:
            c = text[i]
            depth += c == "("
            depth -= c == ")"
            i += 1
            if depth == 0:
                break
        if '(layer "Edge.Cuts")' in text[s:i]:
            yield s, i


def repair(text):
    spans = list(edge_items(text))
    seen = []                                # snap targets, first come first served
    out, last, dropped, snapped = [], 0, 0, 0
    for s, e in spans:
        item = text[s:e]
        pts = re.findall(r"\((start|end) ([-\d.]+) ([-\d.]+)\)", item)
        if item.startswith("(gr_line") and pts[0][1:] == pts[1][1:]:
            out.append(text[last:s])
            last = e
            dropped += 1
            continue

        def snap(m):
            nonlocal snapped
            x, y = float(m.group(2)), float(m.group(3))
            for sx, sy in seen:
                if abs(sx - x) < SNAP and abs(sy - y) < SNAP:
                    if (sx, sy) != (x, y):
                        snapped += 1
                    return f"({m.group(1)} {sx} {sy})"
            seen.append((x, y))
            return m.group(0)

        out.append(text[last:s])
        out.append(re.sub(r"\((start|end) ([-\d.]+) ([-\d.]+)\)", snap, item))
        last = e
    out.append(text[last:])
    return "".join(out), dropped, snapped


def main():
    with tempfile.TemporaryDirectory() as tmp:
        for plate, model, (ox, oy) in PLATES:
            fixed, dropped, snapped = repair((BOARDS / plate).read_text(encoding="utf-8"))
            copy = Path(tmp) / plate
            copy.write_text(fixed, encoding="utf-8")
            print(f"{plate}: dropped {dropped} zero-length, snapped {snapped} endpoints")
            wrl = Path(tmp) / "plate.wrl"
            cmd = ["kicad-cli", "pcb", "export", "vrml", "-f", "--units", "tenths",
                   "--user-origin", f"{ox:.4f}x{oy:.5f}mm", "-o", str(wrl), str(copy)]
            # Audited: a list argv with no shell; the program is the literal
            # "kicad-cli" and every argument is a fixed string, a number this
            # script formats, or a path under the repo / a mkdtemp() directory.
            # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode:
                sys.exit(r.stdout + r.stderr)
            # mtime=0 keeps the gzip header free of a timestamp
            data = aluminium(wrl.read_text(encoding="utf-8")).encode("utf-8")
            (HERE / model).write_bytes(gzip.compress(data, 9, mtime=0))
            print(f"  wrote {model}")


if __name__ == "__main__":
    main()
