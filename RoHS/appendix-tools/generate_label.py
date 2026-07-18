#!/usr/bin/env python3
"""Generate PolyKybd CE product labels with a continuous serial number.

Each unit (keyboard) gets one serial; both halves are labelled with an -L / -R suffix,
so a pair is traceable to the same unit. A persistent counter (labels/last_serial.txt)
keeps the numbering continuous across runs/batches. SVGs import straight into LightBurn
for laser-engraving the case back.

Usage:
  python generate_label.py                       # next unit -> emits -L and -R labels
  python generate_label.py --count 50            # 50 units (100 label files)
  python generate_label.py --side L              # only the left-half label
  python generate_label.py --no-sides            # single label, no L/R suffix
  python generate_label.py --set 100             # set counter to 100 (emit nothing)
  python generate_label.py --png                 # also write a PNG preview
  python generate_label.py --dry-run             # list serials, write nothing
  # field overrides (else CFG defaults are used):
  python generate_label.py --company "PolyTasten GmbH" --rev 3.2 --ma 500 \
                           --designed Austria --origin "" --address "Musterstr. 1, 1010 Wien"

LightBurn: SVG <text> uses Arial; for guaranteed geometry convert text to paths first, e.g.
  inkscape label.svg --actions="select-all;object-to-path;export-filename:label.svg;export-do"
"""
import argparse, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.normpath(os.path.join(HERE, "..", "labels"))
COUNTER = os.path.join(OUTDIR, "last_serial.txt")

CFG = {
    "company":      "PolyTasten GmbH",          # placer on the market (CE 'manufacturer')
    "address":      "[Austrian address - TO CONFIRM]",
    "model":        "PolyKybd Split72",
    "rev":          "3.2",                       # current hardware revision
    "voltage":      "5 V DC",
    "current_ma":   "500",                       # USB 2.0 max = 500 mA
    "designed_in":  "Austria",                   # 'Designed in Austria' (NOT an origin claim)
    "origin":       "",                          # optional true 'Made in ...'; blank = omit
    "support":      "tom.smart.bishop@gmail.com",
    "serial_prefix":"PK/S72",
    "serial_digits": 6,
    "sides":        ["L", "R"],                  # a label per half; overridden by --side/--no-sides
}

def base_serial(n):
    return f"{CFG['serial_prefix']}-{n:0{CFG['serial_digits']}d}"

def unit_serial(n, side):
    return base_serial(n) + (f"-{side}" if side else "")

def safe_name(s):
    return re.sub(r"[^A-Za-z0-9._-]", "-", s)     # '/' etc. are illegal in filenames

TEMPLATE = r'''<svg xmlns="http://www.w3.org/2000/svg" width="70mm" height="40mm" viewBox="0 0 70 40">
  <!-- PolyKybd CE label. 70 x 40 mm. Serial @SERIAL@. Replace [ ... ] placeholders and
       swap the CE mark + WEEE symbol for official artwork (CE mark min. 5 mm height). -->
  <style>
    text{font-family:Arial,Helvetica,sans-serif;fill:#000}
    .t{font-size:3.6px;font-weight:bold}
    .s{font-size:2.0px}
    .f{font-size:2.2px}
    .sm{font-size:1.7px;fill:#222}
  </style>
  <rect x="0.4" y="0.4" width="69.2" height="39.2" rx="2" fill="#fff" stroke="#000" stroke-width="0.4"/>

  <text class="t" x="3" y="6.2">PolyKybd Split72</text>
  <text class="s" x="3" y="9.4">Wired USB mechanical keyboard</text>

  <text class="f" x="3" y="14.2">Mfr: @COMPANY@</text>
  <text class="f" x="3" y="17.6">@ADDR@</text>
  <text class="f" x="3" y="21.0">Model: @MODEL@ - Rev @REV@</text>
  <text class="f" x="3" y="24.4">Rating: @RATING@</text>
@OPT_LINE@
  <text class="f" x="3" y="31.2">S/N: @SERIAL@</text>
  <text class="sm" x="3" y="35.0">CE: EMC 2014/30/EU - RoHS 2011/65/EU - GPSR (EU) 2023/988</text>
  <text class="sm" x="3" y="37.6">Support: @SUPPORT@</text>

  <!-- CE marking (placeholder geometry; replace with official artwork) -->
  <g transform="translate(52.5,4.5)" fill="none" stroke="#000" stroke-width="1.15">
    <path d="M 6.0 0.9 A 4.1 4.1 0 1 0 6.0 8.3"/>
    <path d="M 14.0 0.9 A 4.1 4.1 0 1 0 14.0 8.3"/>
    <path d="M 8.9 4.6 H 12.4"/>
  </g>

  <!-- WEEE crossed-out wheelie bin (simplified; replace with official symbol) -->
  <g transform="translate(55.4,15.6)" fill="none" stroke="#000" stroke-width="0.45" stroke-linejoin="round">
    <line x1="0.4" y1="1.6" x2="8.6" y2="1.6"/>
    <path d="M 3.2 1.6 L 3.5 0.7 H 5.5 L 5.8 1.6"/>
    <path d="M 1.2 1.6 L 1.8 8.6 H 7.2 L 7.8 1.6"/>
    <line x1="3.1" y1="2.4" x2="3.3" y2="7.9"/>
    <line x1="4.5" y1="2.4" x2="4.5" y2="7.9"/>
    <line x1="5.9" y1="2.4" x2="5.7" y2="7.9"/>
    <rect x="0.6" y="9.4" width="7.8" height="0.9" fill="#000" stroke="none"/>
    <line x1="0.2" y1="7.6" x2="8.8" y2="1.0" stroke-width="0.6"/>
  </g>
</svg>
'''

def render(serial):
    rating = f'{CFG["voltage"]} - {CFG["current_ma"]} mA (USB)'
    opt = []
    if CFG["designed_in"].strip(): opt.append(f'Designed in {CFG["designed_in"]}')
    if CFG["origin"].strip():      opt.append(f'Origin: {CFG["origin"]}')
    opt_line = f'  <text class="f" x="3" y="27.8">{" - ".join(opt)}</text>' if opt else ""
    s = TEMPLATE
    for k, v in {
        "@SERIAL@": serial, "@COMPANY@": CFG["company"], "@ADDR@": CFG["address"],
        "@MODEL@": CFG["model"], "@REV@": CFG["rev"], "@RATING@": rating,
        "@SUPPORT@": CFG["support"], "@OPT_LINE@": opt_line,
    }.items():
        s = s.replace(k, v)
    return s

def read_counter():
    try: return int(open(COUNTER).read().strip())
    except Exception: return 0

def write_counter(n):
    os.makedirs(OUTDIR, exist_ok=True); open(COUNTER, "w").write(str(n))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--set", type=int)
    ap.add_argument("--side", choices=["L", "R"], help="emit only this half")
    ap.add_argument("--no-sides", action="store_true", help="single label, no L/R suffix")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    for f in ("company", "address", "rev", "designed", "origin"):
        ap.add_argument("--" + f)
    ap.add_argument("--ma")
    a = ap.parse_args()

    # field overrides
    if a.company: CFG["company"] = a.company
    if a.address: CFG["address"] = a.address
    if a.rev:     CFG["rev"] = a.rev
    if a.ma:      CFG["current_ma"] = a.ma
    if a.designed is not None: CFG["designed_in"] = a.designed
    if a.origin  is not None:  CFG["origin"] = a.origin

    if a.set is not None:
        write_counter(a.set); print("counter set to", a.set); return

    sides = [""] if a.no_sides else ([a.side] if a.side else CFG["sides"])
    start = read_counter() + 1
    units = list(range(start, start + a.count))

    if a.dry_run:
        print("would emit:", ", ".join(unit_serial(n, s) for n in units for s in sides)); return

    os.makedirs(OUTDIR, exist_ok=True)
    for n in units:
        for side in sides:
            sn = unit_serial(n, side)
            svg = render(sn)
            path = os.path.join(OUTDIR, safe_name(sn) + ".svg")
            open(path, "w").write(svg)
            print("wrote", path)
            if a.png:
                try:
                    import cairosvg
                    cairosvg.svg2png(bytestring=svg.encode(), write_to=path[:-4] + ".png", output_width=700)
                except Exception as e:
                    print("  (png skipped:", e, ")")
    write_counter(units[-1])
    print("counter now at", units[-1])

if __name__ == "__main__":
    main()
