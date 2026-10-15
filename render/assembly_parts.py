"""Which KiCad part every imported shape belongs to, for the assembly video.

Blender's X3D importer flattens the board's VRML: one half arrives as ~95k loose
shapes with no footprint grouping. Each shape still has its place, and every
footprint's place is in the .kicad_pcb, so a shape is given to the smallest
footprint whose pads reach it. Pure numpy, so it can be tested outside Blender.

    fps = footprints(board)                     # parts with a 3D model
    off = fit(cen, roles, fps)                  # board mm -> import frame
    group, kind = classify(cen, lo, hi, roles, fps, off)

`group` names the moving object (a reference such as "C12" or "SW_K_7", or one
of PCB, PLATE, STATUS, CASE, LID0..); `kind` says what it is ("comp", "socket",
"switch", "kstem", "display", "keycap", "pcb", "plate", "diffuser", "status",
"case", "lid", "screw") and decides when it arrives. None means "leave it out"
(the imported flex cables: textured_parts.py replaces them).
"""
import re

import numpy as np

KEY_MODEL = "outercap"                # a footprint with a keycap (outercap1u*.wrl) is a key
BOARD_Z = 0.8                         # the PCB's faces, mm above / below its middle
BIG = 20.0                            # mm: wider than any component, a layer of a board


def footprints(board):
    """The footprints that carry a 3D model: lib, ref, x, y (board mm), rot,
    layer, model file names and r, the reach of its pads (mm, plus 0.8)."""
    t = open(board, encoding="utf-8").read()
    out = []
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"', t):
        s = m.start()
        e = t.find("\n\t(footprint ", s + 5)
        blk = t[s:len(t) if e < 0 else e]
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk)
        mods = [x.split("/")[-1] for x in re.findall(r'\(model "([^"]+)"', blk)]
        if not mods:
            continue
        pads = [(float(a), float(b)) for a, b in re.findall(r'\(pad "[^"]*" \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+)', blk)]
        out.append(dict(lib=m.group(1), ref=ref.group(1) if ref else "?", x=float(at.group(1)),
                        y=float(at.group(2)), rot=float(at.group(3) or 0),
                        layer=re.search(r'\(layer "([^"]+)"\)', blk).group(1), mods=mods,
                        r=max([float(np.hypot(*p)) for p in pads] + [0.5]) + 0.8))
    return out


def is_key(fp):
    return any(m.startswith(KEY_MODEL) for m in fp["mods"])


def fit(cen, roles, fps):
    """(cx, cy): the import frame is (x - cx, -(y - cy)) of the board's mm. Found
    from the keycaps, one per key footprint (left half: 36, residual 0.04 mm)."""
    caps = cen[roles == "keycap glass", :2]
    keys = np.array([(f["x"], f["y"]) for f in fps if is_key(f)])
    if len(caps) != len(keys):
        raise SystemExit(f"{len(caps)} keycaps but {len(keys)} key footprints: cannot fit the board")
    cx = keys[:, 0].mean() - caps[:, 0].mean()
    cy = keys[:, 1].mean() + caps[:, 1].mean()
    k = np.c_[keys[:, 0] - cx, -(keys[:, 1] - cy)]
    resid = np.sqrt(((caps[:, None] - k[None]) ** 2).sum(-1)).min(1).max()
    if resid > 0.5:
        raise SystemExit(f"keycaps do not sit on the key footprints (worst {resid:.2f} mm)")
    return cx, cy


def classify(cen, lo, hi, roles, fps, off):
    """Per shape: (group, kind), or (None, None) to drop it."""
    cx, cy = off
    P = np.array([(f["x"] - cx, -(f["y"] - cy)) for f in fps])
    R = np.array([f["r"] for f in fps])
    key = np.array([is_key(f) for f in fps])
    R[key] = 13.0
    size = (hi - lo)[:, :2].max(1)
    dist = np.sqrt(((cen[:, None, :2] - P[None]) ** 2).sum(-1))
    inside = dist < (R[None] + 0.25 * size[:, None])
    owner = np.where(inside.any(1), np.where(inside, R[None] + 1e-3 * dist, np.inf).argmin(1), dist.argmin(1))
    kd = np.where(key[None], dist, np.inf)
    nearest_key = kd.argmin(1)
    holes = [i for i, f in enumerate(fps) if f["lib"].startswith("MountingHole")]
    out = []
    lids = []
    for i in range(len(cen)):
        r, z, s = roles[i], cen[i, 2], size[i]
        if r == "flex cable":
            out.append((None, None))
        elif r == "solder mask" or (s > BIG and abs(z) < 1.5 and r not in ("case PLA",)):
            out.append(("PCB", "pcb"))
        elif r == "plate aluminium" or (s > BIG and 3.0 < z < 7.0 and r in ("",)):
            out.append(("PLATE", "plate"))
        elif r == "diffuser resin":
            out.append(("PLATE", "diffuser"))
        elif r in ("oled glass", "status lcd"):
            out.append(("STATUS", "status"))
        elif r == "case PLA" and s > 100:
            out.append(("CASE", "case"))
        elif r == "case PLA" and s > 10:
            lids.append(i)
            out.append((f"LID{len(lids) - 1}", "lid"))
        elif r == "screw steel" and holes:
            h = min(holes, key=lambda j: dist[i, j])
            out.append((fps[h]["ref"], "screw"))
        elif r in ("keycap glass", "stem", "display face", "switch top housing", "switch stem", "socket contacts"):
            kind = {"keycap glass": "keycap", "stem": "kstem", "display face": "display",
                    "socket contacts": "socket"}.get(r, "switch")
            out.append((fps[nearest_key[i]]["ref"], kind))
        else:
            f = fps[owner[i]]
            if is_key(f):                   # below the board: the hot-swap socket; above: the switch
                out.append((f["ref"], "socket" if hi[i, 2] < -BOARD_Z else "switch"))
            else:
                out.append((f["ref"], "comp"))
    return out
