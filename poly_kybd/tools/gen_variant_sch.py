#!/usr/bin/env python3
"""Generate a PolyKybd top-level schematic (per side) from KLE + variant YAML.

This is the first cut of the "universal" variant generator (see
tools/README.md, "Where this is going"): the KLE layout contributes geometry +
the matrix position of every key; the variant YAML (tools/variants/*.yaml)
contributes the complete electrical parameter set — matrix size, MCU GPIO
contract (col/row pins, LED array, SR control, SPI, split link, encoder,
trackpad), display-chain partition, CS bit rules, LED chain order and the
sub-sheet files to instantiate. The hand-drawn sub-sheets (key cell, buffer,
shift registers, MCU) stay the unit of graphical reuse — this tool only writes
sheet INSTANCES and nets, exactly the roadmap's gen_schematic stage.

Output: tools/out/<name>_<side>.kicad_sch (KiCad 8/9-readable, version
20231120). Sheet refs and every UUID derive deterministically from the variant
name + side + matrix position, so regeneration is byte-stable.

Verification (--verify): traces the GENERATED file and the HAND-MADE reference
from the YAML with kicad_sch_trace and compares canonical per-key contracts
keyed on the matrix position — Row/Col nets, SCLK/SDIN chain, CS output, LED
chain neighbours, fixed nets — plus the MCU pin map, buffer set and SR wiring.
Nets the hand-made file loses inside flat symbols the tracer cannot follow
(series resistors, connectors: value '?') tolerate any generated value; every
other field must match exactly. Non-zero exit on any mismatch.

Usage (from poly_kybd/tools/):
    python3 gen_variant_sch.py variants/split72.yaml --verify
"""
import argparse
import math
import re
import sys
import uuid
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from kicad_sch_trace import trace  # noqa: E402

TOOLS = Path(__file__).resolve().parent
GRID = 1.27
PITCH_X, PITCH_Y = 30.0, 42.0
ORIGIN_X, ORIGIN_Y = 30.0, 30.0
STUB = 3.81


def snap(v):
    return round(round(v / GRID) * GRID, 2)


def det_uuid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'polykybd-gen:' + ':'.join(map(str, parts))))


def parse_kle(path):
    """Minimal KLE reader for layouts whose labels are "row,col" matrix
    positions. Returns [{row, col, cx, cy}] with centers in key units."""
    import json
    data = json.loads(Path(path).read_text())
    keys, y = [], 0.0
    rot = rx = ry = 0.0
    for row in data:
        if isinstance(row, dict):
            continue
        x, w, h = 0.0, 1.0, 1.0
        for item in row:
            if isinstance(item, dict):
                if 'r' in item:
                    rot = float(item['r'])
                if 'rx' in item:
                    rx = float(item['rx'])
                    x = rx
                if 'ry' in item:
                    ry = float(item['ry'])
                    y = ry
                x += float(item.get('x', 0))
                y += float(item.get('y', 0))
                w = float(item.get('w', w))
                h = float(item.get('h', h))
                continue
            r, c = (int(v) for v in str(item).split(','))
            cx, cy = x + w / 2, y + h / 2
            if rot:
                th = math.radians(rot)
                dx, dy = cx - rx, cy - ry
                cx = rx + dx * math.cos(th) - dy * math.sin(th)
                cy = ry + dx * math.sin(th) + dy * math.cos(th)
            keys.append({'row': r, 'col': c, 'cx': cx, 'cy': cy})
            x += w
            w = h = 1.0
        y += 1.0
    return keys


def sheet_pins(sheet_file):
    """Pin interface of a sub-sheet = its hierarchical labels, in file order."""
    t = (TOOLS.parent / sheet_file).read_text()
    seen = []
    for m in re.finditer(r'\(hierarchical_label "([^"]+)"', t):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


class Emitter:
    def __init__(self, name, side):
        self.name, self.side = name, side
        self.root = det_uuid(name, side, 'root')
        self.body = []
        self.page = 1

    def wire(self, x1, y1, x2, y2, ident):
        self.body.append(
            f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1} {y1}) (xy {x2} {y2})\n\t\t)\n'
            f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(uuid "{det_uuid(self.name, self.side, "wire", ident)}")\n\t)')

    def label(self, name, x, y, ident, glob=False):
        kind = 'global_label' if glob else 'label'
        shape = '\n\t\t(shape input)' if glob else ''
        self.body.append(
            f'\t({kind} "{name}"{shape}\n\t\t(at {x} {y} 0)\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify left)\n\t\t)\n'
            f'\t\t(uuid "{det_uuid(self.name, self.side, "label", ident)}")\n\t)')

    def sheet(self, sname, sfile, x, y, w, h, pins):
        """pins: [(pin_name, px, py)] — must lie on the sheet border."""
        self.page += 1
        p = [f'\t(sheet\n\t\t(at {x} {y})\n\t\t(size {w} {h})\n'
             f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type solid)\n\t\t)\n'
             f'\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n'
             f'\t\t(uuid "{det_uuid(self.name, self.side, "sheet", sname)}")\n'
             f'\t\t(property "Sheetname" "{sname}"\n\t\t\t(at {x} {round(y - 0.7, 2)} 0)\n'
             '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
             '\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
             f'\t\t(property "Sheetfile" "{sfile}"\n\t\t\t(at {x} {round(y + h + 0.7, 2)} 0)\n'
             '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
             '\t\t\t\t(justify left top)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)']
        for pname, px, py in pins:
            p.append(f'\t\t(pin "{pname}" input\n\t\t\t(at {px} {py} 0)\n'
                     '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                     '\t\t\t\t(justify right)\n\t\t\t)\n'
                     f'\t\t\t(uuid "{det_uuid(self.name, self.side, "pin", sname, pname)}")\n\t\t)')
        p.append(f'\t\t(instances\n\t\t\t(project "{self.name}_{self.side}"\n'
                 f'\t\t\t\t(path "/{self.root}"\n\t\t\t\t\t(page "{self.page}")\n'
                 '\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        self.body.append('\n'.join(p))

    def emit(self):
        return (f'(kicad_sch\n\t(version 20231120)\n\t(generator "gen_variant_sch")\n'
                f'\t(generator_version "8.0")\n\t(uuid "{self.root}")\n\t(paper "A1")\n'
                f'\t(title_block\n\t\t(title "{self.name} {self.side} (generated)")\n\t)\n'
                '\t(lib_symbols)\n'
                + '\n'.join(self.body) +
                '\n\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n)\n')


def place_sheet(em, sname, sfile, x, y, pin_names, nets, glob_nets, min_h=0):
    """Place one sheet instance; wire every pin in `nets` to a stub + label."""
    w = 22.86
    h = max(min_h, snap((len(pin_names) + 1) * 2.54))
    x, y = snap(x), snap(y)
    pins = []
    for i, pname in enumerate(pin_names):
        pins.append((pname, round(x + w, 2), round(y + 2.54 + i * 2.54, 2)))
    em.sheet(sname, sfile, x, y, w, h, pins)
    for pname, px, py in pins:
        net = nets.get(pname)
        if net is None:
            continue
        ex = round(px + STUB, 2)
        em.wire(px, py, ex, py, f'{sname}.{pname}')
        em.label(net, ex, py, f'{sname}.{pname}', glob=net in glob_nets)


def side_keys(cfg, kle, side):
    rps = cfg['matrix']['rows_per_side']
    lo, hi = (0, rps) if side == 'left' else (rps, 2 * rps)
    skip = {tuple(p) for p in cfg.get('matrix_only', {}).get(side, [])}
    ks = [k for k in kle if lo <= k['row'] < hi and (k['row'], k['col']) not in skip]
    return sorted(ks, key=lambda k: (k['row'], k['col']))


def cs_out(cfg, side, srow, col, rps):
    rule = cfg['shift_registers']['cs_bit'][side]
    which = rule.get('upper_rows', rule['default']) if srow < rps - 1 else rule['default']
    bit = col + 1 if which == 'col_plus_1' else col
    return f'Out{srow + 1}_{bit}'


def generate(cfg, side, out_dir):
    kle = parse_kle(TOOLS / cfg['kle'])
    rps = cfg['matrix']['rows_per_side']
    keys = side_keys(cfg, kle, side)
    chain_of = {c: int(n) for n, cols in cfg['chains'][side].items() for c in cols}

    # LED chain order from the YAML rule, e.g. [row_asc, col_desc]
    sort_dir = {'row_asc': ('row', 1), 'row_desc': ('row', -1),
                'col_asc': ('col', 1), 'col_desc': ('col', -1)}
    led_rule = [sort_dir[r] for r in cfg['led_chain']['order']]
    order = sorted(keys, key=lambda k: tuple(s * k[f] for f, s in led_rule))
    led_prev = {}
    for i, k in enumerate(order):
        led_prev[(k['row'], k['col'])] = None if i == 0 else order[i - 1]

    em = Emitter(cfg['name'], side)
    glob = {'LED_ARR_START'}
    glob.update(cfg['key_cell']['nets'].values())
    glob.update(cfg['mcu']['pins'].values())
    glob.update(cfg['mcu']['power'].values())
    glob.update(f'Col{i + 1}' for i in range(cfg['matrix']['cols']))
    glob.update(f'Row{i + 1}' for i in range(rps))
    glob -= {'SCLK_RAW', 'SDIN_RAW'}   # chain distribution stays sheet-local

    minx = min(k['cx'] for k in keys)
    miny = min(k['cy'] for k in keys)
    maxy = max(k['cy'] for k in keys)

    cell_pins = sheet_pins(cfg['key_cell']['sheet'])
    cw, ch = cfg['key_cell'].get('size', [22.86, 33.02])
    for k in keys:
        pos = (k['row'], k['col'])
        srow = k['row'] % rps
        sname = f'K_{k["row"]}_{k["col"]}'
        nets = dict(cfg['key_cell']['nets'])
        nets['KeyRow'] = f'Row{srow + 1}'
        nets['KeyCol'] = f'Col{k["col"] + 1}'
        nets['SCLK'] = f'SCLK{chain_of[k["col"]]}'
        nets['SDIN'] = f'SDIN{chain_of[k["col"]]}'
        nets['CS'] = cs_out(cfg, side, srow, k['col'], rps)
        prev = led_prev[pos]
        nets['LED_DIN'] = ('LED_ARR_START' if prev is None
                           else f'LED_{prev["row"]}_{prev["col"]}_TO_{k["row"]}_{k["col"]}')
        nxt = next((n for n in order if led_prev[(n['row'], n['col'])] is k), None)
        if nxt is not None:
            nets['LED_DOUT'] = f'LED_{k["row"]}_{k["col"]}_TO_{nxt["row"]}_{nxt["col"]}'
        x = ORIGIN_X + (k['cx'] - minx) * PITCH_X - cw / 2
        y = ORIGIN_Y + (k['cy'] - miny) * PITCH_Y - ch / 2
        place_sheet(em, sname, cfg['key_cell']['sheet'], x, y, cell_pins, nets, glob)

    infra_y = ORIGIN_Y + (maxy - miny) * PITCH_Y + 60
    mcu = dict(cfg['mcu']['pins'])
    mcu.update({p: f'Col{i + 1}' for i, p in enumerate(cfg['mcu']['col_pins'])})
    mcu.update({p: f'Row{i + 1}' for i, p in enumerate(cfg['mcu']['row_pins'])})
    mcu.update(cfg['mcu']['power'])
    place_sheet(em, 'RpPico', cfg['mcu']['sheet'], ORIGIN_X, infra_y,
                sheet_pins(cfg['mcu']['sheet']), mcu, glob)

    sr = cfg['shift_registers']
    sr_nets = dict(sr['nets'])
    for k in keys:
        srow = k['row'] % rps
        sr_nets[cs_out(cfg, side, srow, k['col'], rps)] = \
            cs_out(cfg, side, srow, k['col'], rps)
    place_sheet(em, 'ShiftRegisters', sr['sheet'], ORIGIN_X + 60, infra_y,
                sheet_pins(sr['sheet']), sr_nets, glob)

    buf_pins = sheet_pins(cfg['buffer']['sheet'])
    for n in sorted(set(chain_of.values())):
        nets = dict(cfg['buffer']['nets'])
        for pin, base in cfg['buffer']['outputs'].items():
            nets[pin] = f'{base}{n}'
        place_sheet(em, f'NonInvertingBuffer{n - 1}', cfg['buffer']['sheet'],
                    ORIGIN_X + 120 + (n - 1) * 32, infra_y, buf_pins, nets, glob)

    out = out_dir / f'{cfg["name"]}_{side}.kicad_sch'
    out.write_text(em.emit())
    return out


# ---------------------------------------------------------------- verification

def key_contract(path):
    """Canonical per-key electrical contract keyed on (side_row, col)."""
    t = Path(path).read_text()
    r = trace(str(path))
    files = dict(re.findall(
        r'\(property "Sheetname" "([^"]+)"[\s\S]{0,400}?\(property "Sheetfile" "([^"]+)"', t))
    keys = [s for s in r if files.get(s, '').startswith('SSD1306_TO_SPI')]
    pos = {}
    for s in keys:
        rm = re.fullmatch(r'Row(\d+)', r[s].get('KeyRow', ''))
        cm = re.fullmatch(r'Col(\d+)', r[s].get('KeyCol', ''))
        if rm and cm:
            pos[s] = (int(rm.group(1)) - 1, int(cm.group(1)) - 1)

    def led_link(s, pin, other_pin):
        v = r[s].get(pin, '-')
        if v == 'LED_ARR_START':
            return 'START'
        m = re.fullmatch(r'(\w+)\.LED_D(?:IN|OUT)', v)
        if m and m.group(1) in pos:
            return pos[m.group(1)]
        if v not in ('-', '?'):     # a labeled net: find its other key endpoint
            for o in keys:
                if o != s and r[o].get(other_pin) == v:
                    return pos[o]
        return 'NONE'

    out = {}
    for s in keys:
        d = r[s]
        cs = re.fullmatch(r'(?:\w+\.)?(Out\d+_\d+)', d.get('CS', ''))
        out[pos[s]] = {
            'sclk': d.get('SCLK'), 'sdin': d.get('SDIN'),
            'cs': cs.group(1) if cs else d.get('CS'),
            'led_in': led_link(s, 'LED_DIN', 'LED_DOUT'),
            'led_out': led_link(s, 'LED_DOUT', 'LED_DIN'),
            'dc': d.get('D-C'), 'reset': d.get('RESET'), 'gnd': d.get('GND'),
            'vdd': d.get('VDD'), 'vsup': d.get('VSUP'),
        }

    mcu_sheet = next((s for s in r if files.get(s, '').startswith('rp_pico')), None)
    buffers = sorted(
        (r[s].get('B_OUT'), r[s].get('A_OUT'), r[s].get('B_IN'), r[s].get('A_IN'),
         r[s].get('VCC'), r[s].get('GND'))
        for s in r if files.get(s, '').startswith('ni_buffer'))
    sr_sheet = next((s for s in r if files.get(s, '').startswith('shift_registers')), None)
    sr = {}
    if sr_sheet:
        for p, v in r[sr_sheet].items():
            if p.startswith('Out'):
                m = re.fullmatch(r'(\w+)\.CS', v)
                sr[p] = pos.get(m.group(1), v) if m else (
                    'NONE' if v in ('-', '?') else next(
                        (pos[s] for s in keys if r[s].get('CS') == v), v))
            else:
                sr[p] = v
    return {'keys': out, 'mcu': r.get(mcu_sheet, {}), 'buffers': buffers, 'sr': sr}


def diff_contract(gen, ref):
    """Compare generated vs hand-made contract. '?' on the reference side (a
    net vanishing into flat symbols the tracer can't follow) tolerates any
    generated value. Returns list of mismatch strings."""
    bad = []

    def cmp(what, g, h):
        if h == '?' or g == h:
            return
        bad.append(f'{what}: generated={g!r} handmade={h!r}')

    for p in sorted(set(gen['keys']) | set(ref['keys'])):
        g, h = gen['keys'].get(p), ref['keys'].get(p)
        if g is None or h is None:
            bad.append(f'key {p}: missing on {"generated" if g is None else "handmade"} side')
            continue
        for f in g:
            cmp(f'key {p} {f}', g[f], h[f])
    for pin in sorted(set(gen['mcu']) | set(ref['mcu'])):
        cmp(f'MCU {pin}', gen['mcu'].get(pin, '-'), ref['mcu'].get(pin, '-'))
    cmp('buffers', gen['buffers'], ref['buffers'])
    for p in sorted(set(gen['sr']) | set(ref['sr'])):
        cmp(f'SR {p}', gen['sr'].get(p, '-'), ref['sr'].get(p, '-'))
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('variant', help='variant YAML (e.g. variants/split72.yaml)')
    ap.add_argument('--out', default=str(TOOLS / 'out'), help='output directory')
    ap.add_argument('--verify', action='store_true',
                    help='compare against the hand-made references from the YAML')
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.variant).read_text())
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    fails = 0
    for side in ('left', 'right'):
        out = generate(cfg, side, out_dir)
        print(f'wrote {out}')
        if not args.verify:
            continue
        ref_file = TOOLS / cfg['reference'][side]
        bad = diff_contract(key_contract(out), key_contract(ref_file))
        print(f'  verify vs {ref_file.name}: '
              f'{len(bad)} mismatches' if bad else
              f'  verify vs {ref_file.name}: contract MATCHES')
        for b in bad:
            print(f'    {b}')
        fails += len(bad)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
