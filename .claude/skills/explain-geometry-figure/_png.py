#!/usr/bin/env python3
"""Two tiny PNG operations `svg_view.sh` needs, with no third-party imports.

    _png.py band <cal.png>        -> prints the viewport shortfall, in rows
    _png.py trim <img.png> <rows> -> rewrites img.png keeping its top <rows> rows

Why this exists: Chromium's `--window-size` is NOT its viewport.  The page gets a
band fewer pixels at the bottom and the screenshot pads it with the page background,
so a crop quietly loses its last rows AS WHITE -- on a drawing, indistinguishable
from "nothing is drawn there".  `band` measures the shortfall on whatever browser
build is present (it is a property of the build, not a constant worth hard-coding)
by finding the last surviving row of a full-bleed black page; `trim` removes it from
the result, so the caller gets exactly the region it asked for.

Everything is re-encoded as filter-0 RGB, which is what makes this ~60 lines: the
images are flat-colour line drawings, so the compression lost against an adaptive
filter is irrelevant next to not carrying a Pillow dependency into a shell helper.
"""
import struct
import sys
import zlib


def _chunks(blob):
    i = 8
    while i < len(blob):
        n = struct.unpack(">I", blob[i:i + 4])[0]
        yield blob[i + 4:i + 8], blob[i + 8:i + 8 + n]
        i += 12 + n


def _decode(path):
    """-> (width, height, bytes-per-pixel, [unfiltered row, ...])."""
    blob = open(path, "rb").read()
    idat, w = b"", None
    for kind, body in _chunks(blob):
        if kind == b"IHDR":
            w, h, depth, colour = struct.unpack(">IIBB", body[:10])
            if depth != 8 or colour not in (0, 2, 4, 6):
                raise SystemExit("_png.py: only 8-bit grey/RGB(A) PNGs are handled")
        elif kind == b"IDAT":
            idat += body
    if w is None:
        raise SystemExit("_png.py: no IHDR")
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[colour]
    raw, stride, rows, prev, pos = zlib.decompress(idat), w * bpp, [], bytearray(w * bpp), 0
    for _ in range(h):
        f, line = raw[pos], bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, bpp, rows


def _write(path, w, rows, bpp):
    body = b"".join(b"\0" + r for r in rows)
    out = [b"\x89PNG\r\n\x1a\n"]
    for kind, data in ((b"IHDR", struct.pack(">IIBBBBB", w, len(rows), 8,
                                             {1: 0, 2: 4, 3: 2, 4: 6}[bpp], 0, 0, 0)),
                       (b"IDAT", zlib.compress(body, 6)),
                       (b"IEND", b"")):
        out.append(struct.pack(">I", len(data)) + kind + data
                   + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))
    open(path, "wb").write(b"".join(out))


def main(argv):
    if len(argv) >= 3 and argv[1] == "band":
        w, h, bpp, rows = _decode(argv[2])
        last = max((y for y, r in enumerate(rows) if r[0] < 128), default=-1)
        # The calibration page is taller than any window, so the last dark row IS the
        # bottom of the viewport; everything under it is the band.
        print(h - 1 - last)
        return 0
    if len(argv) >= 4 and argv[1] == "trim":
        keep = int(argv[3])
        w, h, bpp, rows = _decode(argv[2])
        if keep < h:
            _write(argv[2], w, rows[:keep], bpp)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
