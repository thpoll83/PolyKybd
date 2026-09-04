"""Pin the exact font file the engraving is cut from.

    python3 font.py            # fetch + instantiate; prints the path it will use

⚠️ **OCCT does not go through fontconfig.** `font="Noto"` -- what `keycap_stem.scad`
asks for, and what fontconfig happily resolves -- makes build123d emit
*"unable to find font 'Noto'; 'FreeSans' is used instead"* and carry on. The stamp then
comes out in a different typeface from the printed plates, silently, and a toolmaker
cuts that. Asking for the family by its real name (`"Noto Sans"`) finds the file but
gets the **variable font's default instance**, i.e. not Bold -- the same trap the
firmware's `fonts/README` records for `fontconvert`.

So: instantiate `wght=700` from the variable file once, and hand build123d the path.
The engraving is then reproducible from the repo rather than from whatever the build
machine happened to have installed.

The variable font is cached where `../build_stems.sh --fetch-font` puts it, so the two
share one download. ⚠️ Do **not** use that flag to get it: it fetches and then goes on
to **re-export all sixteen printed plates** against the new font, which rewrites
committed meshes (it did, here -- three of them, before it was killed). This module
fetches and stops.
"""
import hashlib
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# Same URL and cache path as ../build_stems.sh, which takes them from the firmware's
# fonts/noto-fonts.yaml -- one download serves both.
URL = ("https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/"
       "NotoSans%5Bwdth%2Cwght%5D.ttf")
CACHE = os.path.join(os.environ.get("XDG_DATA_HOME",
                                    os.path.expanduser("~/.local/share")),
                     "fonts", "polykybd", "NotoSans.ttf")
WEIGHT = 700                                        # `Noto:style=Bold` in the .scad

# ⚠️ **THE DIGEST IS THE PIN.**  The URL tracks `main`, so upstream can change these
# bytes under us -- and this font is not decoration: the engraved beta and S are cut
# into a steel cavity from outlines it supplies, and CLAUDE.md already records that a
# variable-vs-static Noto changes those outlines measurably.  Left unpinned, a rebuild
# months from now silently produces a different tool geometry and nothing says so.
#
# So every read is verified against SHA256 and a mismatch is a hard stop with
# instructions, never a shrug.  A commit-pinned URL would be tidier still, but this
# session cannot reach the GitHub API to resolve one (the proxy serves only the
# session's authorised repos); the digest gives the property that actually matters and
# is strictly stronger than a commit pin alone, since it also catches a truncated or
# proxied download -- the exact failure PolyKybdHost's font_downloader was written for.
#
# To adopt a new upstream font DELIBERATELY: check the new digest, put it here, and
# re-export both STEPs -- the engraving geometry changes, so the committed files must.
SHA256 = "bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d"
VERSION = "Noto Sans 2.015 (wght 100-900, wdth 62.5-100)"   # what that digest is

# ⚠️ The instantiated Bold file is NAMED AFTER THE SOURCE DIGEST, and that is what
# carries the pin through to the geometry.  `bold_path` returns this file without
# consulting the cache at all, so under a fixed name a Bold instance generated
# BEFORE the pin existed -- or from a since-superseded digest -- would go on
# engraving silently, with the verified cache sitting unused beside it.  Putting
# the digest in the name makes a SHA256 change a *different file*, so it
# regenerates on its own and needs no staleness bookkeeping.  (CodeRabbit, PR #38.)
BOLD = os.path.join(HERE, f".notosans-bold-{SHA256[:12]}.ttf")   # generated, gitignored


def _digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(force=False):
    """Return a verified NotoSans.ttf, downloading it if the cache is absent or wrong.

    ⚠️ The cache is SHARED with ../build_stems.sh, which fetches the same URL with no
    verification of its own -- so the file sitting there may be whatever `main` served
    whenever that script last ran, which is not necessarily what this digest names.
    Hence a mismatched cache is re-downloaded rather than rejected: that heals the
    shared path in the common case, and both callers end up on the pinned bytes.  Only
    a fresh download that still mismatches is fatal.
    """
    if os.path.exists(CACHE) and not force:
        if _digest(CACHE) == SHA256:
            return CACHE
        print(f"cached font is not {VERSION} -- re-fetching")
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    print(f"fetching {URL}\n     -> {CACHE}")
    urllib.request.urlretrieve(URL, CACHE)
    got = _digest(CACHE)
    if got != SHA256:
        raise RuntimeError(
            f"font digest mismatch -- refusing to engrave with an unknown font.\n"
            f"  expected {SHA256}  ({VERSION})\n"
            f"  got      {got}\n"
            f"  {URL}\n"
            f"Upstream has moved.  Review the new font, then update font.SHA256 and\n"
            f"VERSION and re-export both STEPs -- the engraved outlines change with it.")
    return CACHE


def bold_path(auto_fetch=True):
    """Path to a static Bold instance of Noto Sans, making it if necessary."""
    if os.path.exists(BOLD):
        return BOLD
    if not os.path.exists(CACHE) or _digest(CACHE) != SHA256:
        if not auto_fetch:
            raise FileNotFoundError(
                f"{CACHE} is missing or is not {VERSION} -- run `make font` (NOT "
                f"`build_stems.sh --fetch-font`, which also re-exports the plates)")
        fetch()
    from fontTools import ttLib
    from fontTools.varLib import instancer
    font = ttLib.TTFont(CACHE)
    instancer.instantiateVariableFont(font, {"wght": WEIGHT}, inplace=True)
    font.save(BOLD)
    print(f"instantiated wght={WEIGHT} -> {BOLD}")
    return BOLD


if __name__ == "__main__":
    print(bold_path())
    sys.exit(0)
