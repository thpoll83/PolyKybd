"""Fetch the Poly Haven assets the workspace scenes use (render/workspace_scene.py).

    python3 render/workspace_assets.py            # into render/out/assets/polyhaven/

Every asset is CC0 (polyhaven.com/license): no attribution is required, and
render/out/assets/polyhaven/CREDITS.md lists them anyway. Models come as glTF with
their 2k textures, HDRIs as 4k .hdr (the room behind the desk, out of focus). A file
already on disk is not fetched again. Plain Python 3, no packages.
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "assets", "polyhaven")
API = "https://api.polyhaven.com"
sys.path.insert(0, HERE)
from workspace_scenes import SCENES  # noqa: E402


def get(url, path=None):
    req = urllib.request.Request(url, headers={"User-Agent": "polykybd-render"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if path is None:
        return data
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".part", "wb") as f:
        f.write(data)
    os.replace(path + ".part", path)


def fetch_model(aid, res="2k"):
    files = json.loads(get(f"{API}/files/{aid}"))
    g = files["gltf"].get(res) or files["gltf"][sorted(files["gltf"])[0]]
    top = g["gltf"]
    d = os.path.join(OUT, aid)
    path = os.path.join(d, os.path.basename(top["url"]))
    for rel, inc in [(os.path.basename(top["url"]), top)] + list(top.get("include", {}).items()):
        p = os.path.join(d, rel)
        if not os.path.exists(p):
            get(inc["url"], p)
    return path


def fetch_hdri(aid, res="4k"):
    files = json.loads(get(f"{API}/files/{aid}"))
    h = files["hdri"][res]["hdr"]
    path = os.path.join(OUT, aid, os.path.basename(h["url"]))
    if not os.path.exists(path):
        get(h["url"], path)
    return path


def fetch_photo(aid):
    """An HDRI's tonemapped JPG: a CC0 landscape photo (equirectangular, 8k+ wide)."""
    files = json.loads(get(f"{API}/files/{aid}"))
    t = files["tonemapped"]
    path = os.path.join(OUT, aid, os.path.basename(t["url"]).replace("%20", "_"))
    if not os.path.exists(path):
        get(t["url"], path)
    return path


def fetch_texture(aid, res="2k"):
    """A Poly Haven texture's colour, normal (GL) and roughness maps as 2k JPGs;
    returns {"diff": path, "nor": path, "rough": path}."""
    files = json.loads(get(f"{API}/files/{aid}"))
    out = {}
    for key, kind in (("diff", "Diffuse"), ("nor", "nor_gl"), ("rough", "Rough")):
        u = files[kind][res]["jpg"]["url"]
        path = os.path.join(OUT, aid, os.path.basename(u))
        if not os.path.exists(path):
            get(u, path)
        out[key] = path
    return out


FONTS = {"Caveat.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/caveat/Caveat%5Bwght%5D.ttf",
         "Caveat-OFL.txt": "https://raw.githubusercontent.com/google/fonts/main/ofl/caveat/OFL.txt"}


def fetch_font(name):
    """A handwriting font (SIL OFL) for the pen notes in workspace_screens.py."""
    path = os.path.join(HERE, "out", "assets", "fonts", name)
    if not os.path.exists(path):
        get(FONTS[name], path)
    return path


PHOTOS = ["bell_park_pier"]                                   # the office calendar's picture (workspace_screens.py)


def main():
    info = json.loads(get(f"{API}/assets"))
    used = {}
    for name, sc in SCENES.items():
        p = fetch_hdri(sc["hdri"])
        used[sc["hdri"]] = p
        print(f"{name}: room {os.path.relpath(p, HERE)}")
        if sc.get("wall", {}).get("texture"):
            used[sc["wall"]["texture"]["id"]] = fetch_texture(sc["wall"]["texture"]["id"])["diff"]
        for aid in [sc["desk"]] + [pr[0] for pr in sc["props"]] + [t[0] for t in sc.get("room", {}).get("things", [])] + sc.get("fetch", []):
            if aid.startswith("@"):                   # built in the scene script, not fetched
                continue
            if aid not in used:
                used[aid] = fetch_model(aid)
                print(f"  {aid}: {os.path.relpath(used[aid], HERE)}")
    for aid in PHOTOS:
        used[aid] = fetch_photo(aid)
        print(f"photo {aid}: {os.path.relpath(used[aid], HERE)}")
    with open(os.path.join(OUT, "CREDITS.md"), "w", encoding="utf-8") as f:
        f.write("# Poly Haven assets in the workspace scenes\n\nAll CC0 (https://polyhaven.com/license).\n\n")
        for aid in sorted(used):
            a = info.get(aid, {})
            f.write(f"- {a.get('name', aid)} (`{aid}`), by {', '.join(a.get('authors', {})) or 'Poly Haven'}: "
                    f"https://polyhaven.com/a/{aid}\n")
    print("credits:", os.path.relpath(os.path.join(OUT, "CREDITS.md"), HERE))


if __name__ == "__main__":
    main()
