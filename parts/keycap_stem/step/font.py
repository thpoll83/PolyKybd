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
BOLD = os.path.join(HERE, ".notosans-bold.ttf")     # generated, gitignored
WEIGHT = 700                                        # `Noto:style=Bold` in the .scad


def fetch(force=False):
    if os.path.exists(CACHE) and not force:
        return CACHE
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    print(f"fetching {URL}\n     -> {CACHE}")
    urllib.request.urlretrieve(URL, CACHE)
    return CACHE


def bold_path(auto_fetch=True):
    """Path to a static Bold instance of Noto Sans, making it if necessary."""
    if os.path.exists(BOLD):
        return BOLD
    if not os.path.exists(CACHE):
        if not auto_fetch:
            raise FileNotFoundError(
                f"{CACHE} is missing -- run `make font` (NOT "
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
