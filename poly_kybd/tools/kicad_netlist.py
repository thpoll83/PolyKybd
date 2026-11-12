#!/usr/bin/env python3
"""KiCad's own netlist for a schematic, through `kicad-cli`.

The text-level tracer (kicad_sch_trace.py) reads top-level wires and labels
only. It cannot see inside a sub-sheet and it does not apply KiCad's
connectivity rules. This module asks KiCad itself, which is the authoritative
answer to "which pad is on which net".

One rule this found (2026-11-12): a wire must be BROKEN at every junction.
A hand-written sheet with one long wire and several junction dots on it
connects only the first tap; everything after it reads `unconnected-(...)`.
KiCad's editor always breaks wires at junctions, so only generated files
have this fault, and a check that tests "the pin lies on a wire" passes.

Needs KiCad 9 (`kicad-cli` on PATH). `available()` says whether it is there;
callers skip this check when it is not.

Usage:
    python3 tools/kicad_netlist.py <board.kicad_sch> [REF ...]
prints the pad nets of the given references (all components without any).
"""
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def available():
    return shutil.which('kicad-cli') is not None


def export(sch_path):
    """Run kicad-cli and return (components, nets, pad_nets, messages).

    components: {ref: {'value', 'footprint', 'sheet', 'path', 'fields'}}
    nets:       {net name: [(ref, pin), ...]}
    pad_nets:   {(ref, pin): net name}
    messages:   kicad-cli's own output lines (annotation warnings etc.)
    """
    sch_path = Path(sch_path).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'netlist.xml'
        # nosemgrep: dangerous-subprocess-use-audit -- fixed argv, no shell
        res = subprocess.run(
            ['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml',
             '-o', str(out), sch_path.name],
            cwd=sch_path.parent, capture_output=True, text=True)
        if not out.exists():
            raise RuntimeError(f'kicad-cli wrote no netlist: {res.stdout}{res.stderr}')
        root = ET.parse(out).getroot()
    messages = [ln for ln in (res.stdout + res.stderr).splitlines() if ln.strip()]

    components = {}
    duplicates = []
    for c in root.find('components'):
        ref = c.get('ref')
        sp = c.find('sheetpath')
        if ref in components:
            duplicates.append(ref)
        components[ref] = {
            'value': c.findtext('value'),
            'footprint': c.findtext('footprint'),
            'sheet': sp.get('names') if sp is not None else None,
            'path': ((sp.get('tstamps') if sp is not None else '')
                     + (c.findtext('tstamps') or '')),
            'fields': {f.get('name'): (f.text or '')
                       for f in c.findall('fields/field')},
        }
    if duplicates:
        messages.append('duplicate references: ' + ' '.join(sorted(set(duplicates))))

    nets, pad_nets = {}, {}
    for n in root.find('nets'):
        nodes = [(nd.get('ref'), nd.get('pin')) for nd in n.findall('node')]
        nets[n.get('name')] = nodes
        for node in nodes:
            pad_nets[node] = n.get('name')
    return components, nets, pad_nets, messages


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if not available():
        sys.exit('kicad-cli not found (KiCad 9 is needed for this tool)')
    components, _, pad_nets, messages = export(sys.argv[1])
    for m in messages:
        print('kicad-cli:', m)
    wanted = set(sys.argv[2:]) or set(components)
    for ref, pin in sorted(pad_nets):
        if ref in wanted:
            print(f'{ref}.{pin:4s} {pad_nets[(ref, pin)]}')


if __name__ == '__main__':
    main()
