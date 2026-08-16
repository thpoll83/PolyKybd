#!/usr/bin/env python3
"""Keep the committed bytes when a re-export produced the same solid.

    python3 parts/settle_mesh.py <path-to-exported-mesh>

Prints one word: `new` (nothing committed to compare against), `unchanged`
(same solid -- the committed bytes have been put back) or `CHANGED`.

Why this exists: OpenSCAD does not emit facets in a stable order between runs,
so re-exporting an UNCHANGED part still rewrites the whole file -- 23k lines of
diff on one diffuser frame, or ~32 MB across the sixteen keycap stem plates --
which buries any real change.  Comparing the facets as an unordered multiset
tells you whether the solid actually moved.

⚠️ The comparison is ROUNDED, and that is load-bearing rather than sloppy.
Different builds of OpenSCAD disagree in the last few float digits, so an exact
compare reports CHANGED for a part nobody touched.  Three decimal places is a
micron -- orders of magnitude below anything printable, and below the tolerance
of every check in check_frame.py -- so a difference that survives rounding is a
real geometry change.  This was learned twice: identifying legs.scad as the
source of an orphan mesh needed rounding to see the match (100% of facets agree
at 3 dp, 0% exactly), and the three build scripts had each grown their own copy
of this logic with a different tolerance before it was extracted here.

Handles both STL flavours this repo ships -- ASCII for the diffuser frames,
binary for everything else (see parts/README.md).  Stdlib only.
"""
import re
import struct
import subprocess
import sys

ROUND_DP = 3          # 1 micron


def facets(blob):
    """Unordered multiset of facets, or None if this is not a parseable STL.

    None is never equal to anything, so an unreadable file can only ever be
    reported as CHANGED -- it must not be able to claim a false match and
    silently restore stale bytes over a real export.
    """
    if blob[:5] == b'solid' and b'facet normal' in blob[:2000]:
        txt = blob.decode('utf-8', 'replace')
        vals = [tuple(map(float, m)) for m in
                re.findall(r'vertex\s+(\S+)\s+(\S+)\s+(\S+)', txt)]
        if not vals or len(vals) % 3:
            return None
        tris = [tuple(x for v in vals[i:i + 3] for x in v)
                for i in range(0, len(vals), 3)]
    else:
        if len(blob) < 84:
            return None
        n = struct.unpack('<I', blob[80:84])[0]
        if len(blob) != 84 + 50 * n:
            return None
        tris = [struct.unpack('<9f', blob[84 + 50 * i + 12:84 + 50 * i + 48])
                for i in range(n)]
    # Sort within a facet as well as across them: a re-export may emit the same
    # triangle starting from a different vertex.
    return sorted(tuple(sorted(round(x, ROUND_DP) for x in t)) for t in tris)


def main(path):
    committed = subprocess.run(['git', 'show', f'HEAD:{path}'],
                               capture_output=True)
    if committed.returncode:
        print('new')                     # not committed yet -- nothing to keep
        return 0
    with open(path, 'rb') as fh:
        fresh = fh.read()
    old, new = facets(committed.stdout), facets(fresh)
    if old is not None and old == new:
        with open(path, 'wb') as fh:     # same solid -- keep committed bytes
            fh.write(committed.stdout)
        print('unchanged')
    else:
        print('CHANGED')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        raise SystemExit(64)
    raise SystemExit(main(sys.argv[1]))
