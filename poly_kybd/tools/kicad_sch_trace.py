#!/usr/bin/env python3
"""Trace top-level connectivity of a PolyKybd KiCad schematic.

Builds a net model from the wires of a top-level .kicad_sch (union-find over
wire segments, including T-junctions where an endpoint lands mid-segment) and
attaches labels (local + global) and hierarchical-sheet pins to those nets.

The main product is the per-key wiring table: for every K_* sheet instance
(one SSD1306_TO_SPI[_NO_LED] key/display cell each) it reports which Row/Col
matrix nets, which SCLK/SDIN display chain and which shift-register output
(CS) the key is wired to. This is the electrical contract the firmware's
MATRIX_*_PINS / key_display[] table must match — diff it between boards, or
against the firmware, instead of eyeballing the schematic.

Usage:
    python3 tools/kicad_sch_trace.py <board.kicad_sch> [more boards ...]

Works on plain text — no KiCad installation required (KiCad 9 files).
"""
import re
import sys
from collections import defaultdict

WIRE_RE = re.compile(
    r'\(wire\s*\(pts\s*\(xy ([\-\d.]+) ([\-\d.]+)\)\s*\(xy ([\-\d.]+) ([\-\d.]+)\)\s*\)')
LABEL_RE = r'\(%s "([^"]+)"[\s\S]{0,220}?\(at ([\-\d.]+) ([\-\d.]+) [\d.]+\)'
SHEET_RE = re.compile(r'\(sheet\n[\s\S]*?\n\t\)')
SHEETNAME_RE = re.compile(r'\(property "Sheetname" "([^"]+)"')
SHEETPIN_RE = re.compile(r'\(pin "([^"]+)" \w+\s*\(at ([\-\d.]+) ([\-\d.]+) [\d.]+\)')


def _on_seg(px, py, x1, y1, x2, y2, eps=0.01):
    if abs((x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)) > eps * max(abs(x2 - x1) + abs(y2 - y1), 1):
        return False
    return min(x1, x2) - eps <= px <= max(x1, x2) + eps and min(y1, y2) - eps <= py <= max(y1, y2) + eps


class SchNets:
    def __init__(self, text):
        self.text = text
        self.wires = [tuple(map(float, m)) for m in WIRE_RE.findall(text)]
        self._parent = {}
        for i, (x1, y1, x2, y2) in enumerate(self.wires):
            self._union(self._key(x1, y1), ('w', i))
            self._union(self._key(x2, y2), ('w', i))
        for i, (x1, y1, x2, y2) in enumerate(self.wires):
            for j, (a1, b1, a2, b2) in enumerate(self.wires):
                if i == j:
                    continue
                for (px, py) in ((x1, y1), (x2, y2)):
                    if _on_seg(px, py, a1, b1, a2, b2):
                        self._union(('w', i), ('w', j))

    @staticmethod
    def _key(x, y):
        return (round(x, 2), round(y, 2))

    def _find(self, a):
        r = a
        while self._parent.get(r, r) != r:
            r = self._parent[r]
        while self._parent.get(a, a) != a:
            self._parent[a], a = r, self._parent[a]
        return r

    def _union(self, a, b):
        ra, rb = self._find(a), self._find(b)
        if ra != rb:
            self._parent[ra] = rb

    def net_of(self, px, py):
        """Net id for a point, or None if no wire touches it."""
        k = self._key(px, py)
        if k in self._parent:
            return self._find(k)
        for i, (x1, y1, x2, y2) in enumerate(self.wires):
            if _on_seg(px, py, x1, y1, x2, y2):
                return self._find(('w', i))
        return None

    def labels(self):
        for kind in ('label', 'global_label'):
            for m in re.finditer(LABEL_RE % kind, self.text):
                yield kind, m.group(1), float(m.group(2)), float(m.group(3))

    def sheets(self):
        for sm in SHEET_RE.finditer(self.text):
            s = sm.group(0)
            nm = SHEETNAME_RE.search(s)
            if not nm:
                continue
            pins = [(p.group(1), float(p.group(2)), float(p.group(3)))
                    for p in SHEETPIN_RE.finditer(s)]
            yield nm.group(1), pins, sm.start()


def trace(path):
    """Return {sheet_name: {pin_name: net description}} for a top-level sch."""
    nets = SchNets(open(path).read())
    netlabels = defaultdict(set)
    netpins = defaultdict(list)
    for _, name, x, y in nets.labels():
        n = nets.net_of(x, y)
        if n is not None:
            netlabels[n].add(name)
    sheet_list = list(nets.sheets())
    for sname, pins, _ in sheet_list:
        for pname, x, y in pins:
            n = nets.net_of(x, y)
            if n is not None:
                netpins[n].append(f'{sname}.{pname}')
    out = {}
    for sname, pins, _ in sheet_list:
        d = {}
        for pname, x, y in pins:
            n = nets.net_of(x, y)
            if n is None:
                d[pname] = '-'
            else:
                labs = sorted(netlabels.get(n, set()))
                others = [p for p in netpins[n] if p != f'{sname}.{pname}']
                d[pname] = labs[0] if labs else (others[0] if others else '?')
        out[sname] = d
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for path in sys.argv[1:]:
        r = trace(path)
        print(f'===== {path}')
        for s in sorted(r):
            if not s.startswith('K_'):
                continue
            d = r[s]
            f = lambda p: d.get(p, '?')
            print(f'  {s:6s} Row={f("KeyRow"):6s} Col={f("KeyCol"):6s} '
                  f'SCLK={f("SCLK"):8s} SDIN={f("SDIN"):8s} CS={f("CS")}')


if __name__ == '__main__':
    main()
