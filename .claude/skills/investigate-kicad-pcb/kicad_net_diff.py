#!/usr/bin/env python3
"""Per-net PCB inspector / variant-diff for KiCad v9 .kicad_pcb files.

Resolves a net by NAME in each file (net *numbers* are per-file — never reuse a
number across boards), then reports the pads on it, total track length, track
widths, layers used, and via count. Give it one file to inspect a net, or two+
files to diff the same net name across board variants/revisions.

    python3 kicad_net_diff.py SERIAL_COM1 SERIAL_COM2 -- board_a.kicad_pcb board_b.kicad_pcb

Pure stdlib (regex over the S-expr text) — deliberately NOT kiutils/pcbnew:
KiCad 9 / pcbnew is unavailable in this environment (see the skill's Pitfalls),
and text parsing is the most robust way to pull nets/pads/tracks/vias.
"""
import re, sys, math


def net_numbers_by_name(text):
    """Map net NAME -> number for this file (numbers are per-file)."""
    out = {}
    for m in re.finditer(r'\(net (\d+) "([^"]*)"\)', text):
        out.setdefault(m.group(2), int(m.group(1)))
    return out


def refs_index(text):
    return [(m.start(), m.group(1))
            for m in re.finditer(r'\(property "Reference" "([^"]+)"', text)]


def ref_before(refs, idx):
    best = None
    for pos, r in refs:
        if pos < idx:
            best = r
        else:
            break
    return best


def analyze(path, names):
    text = open(path).read()
    name2num = net_numbers_by_name(text)
    nums = {name2num[n]: n for n in names if n in name2num}
    refs = refs_index(text)
    pads = {n: set() for n in nums}
    for m in re.finditer(r'\(pad\s+"([^"]+)"', text):
        seg = text[m.start():m.start() + 800]
        nm = re.search(r'\(net (\d+) "[^"]*"\)', seg)
        if nm and int(nm.group(1)) in nums:
            pads[int(nm.group(1))].add(f"{ref_before(refs, m.start())}.{m.group(1)}")
    segs = {n: [] for n in nums}
    seg_re = re.compile(
        r'\(segment\s+\(start ([\-\d.]+) ([\-\d.]+)\)\s*\(end ([\-\d.]+) ([\-\d.]+)\)'
        r'\s*\(width ([\-\d.]+)\)\s*\(layer "([^"]+)"\)[^)]*\(net (\d+)\)')
    for m in seg_re.finditer(text):
        n = int(m.group(7))
        if n in nums:
            x1, y1, x2, y2, w = map(float, m.group(1, 2, 3, 4, 5))
            segs[n].append((math.hypot(x2 - x1, y2 - y1), w, m.group(6)))
    vias = {n: 0 for n in nums}
    for m in re.finditer(r'\(via\b(.*?)\(net (\d+)\)', text, re.S):
        n = int(m.group(2))
        if n in nums and len(m.group(1)) < 400:
            vias[n] += 1
    missing = [n for n in names if n not in name2num]
    return nums, pads, segs, vias, missing


def report(path, names):
    nums, pads, segs, vias, missing = analyze(path, names)
    print(f"\n### {path}")
    if missing:
        print(f"    (net name(s) not in this file: {missing})")
    for num, name in nums.items():
        tot = sum(L for L, w, ly in segs[num])
        widths = sorted({round(w, 3) for L, w, ly in segs[num]})
        layers = sorted({ly for L, w, ly in segs[num]})
        print(f"    {name} (net {num}): len={tot:.2f}mm  segs={len(segs[num])}  "
              f"vias={vias[num]}  widths={widths}  layers={layers}")
        print(f"        pads={sorted(pads[num])}")


def main(argv):
    if "--" in argv:
        i = argv.index("--")
        names, files = argv[:i], argv[i + 1:]
    else:  # last token that ends in .kicad_pcb splits names from files
        files = [a for a in argv if a.endswith(".kicad_pcb")]
        names = [a for a in argv if not a.endswith(".kicad_pcb")]
    if not names or not files:
        print(__doc__)
        return 2
    for f in files:
        report(f, names)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
