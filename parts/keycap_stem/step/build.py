"""Build the two moulded keycap stem variants and export clean STEP (+ STL for checks).

    python build.py                 # -> ../../export/keycap_stem/stem_S_1U.step, stem_S_1U25.step
    python build.py --no-engrave    # without the profile+revision stamp
"""
import argparse, os, time
from collections import Counter

from build123d import export_step, export_stl
from OCP.BRepAdaptor import BRepAdaptor_Surface

import stem_model as sm

HERE = os.path.dirname(os.path.abspath(__file__))
# The STEP is a committed deliverable, so it joins the repo-wide export tree beside the
# printed plates.  The STL is only for verify.py / render_compare.py and stays here
# (gitignored) -- it is a checking artefact, not something anyone should send a fab.
OUT = os.path.join(HERE, "..", "..", "export", "keycap_stem")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-engrave", action="store_true",
                    help="drop the profile+revision stamp (it is a TOOL feature: changing it "
                         "later is a tool edit -- see stem_model._engraving and font.py)")
    ap.add_argument("--no-click-tabs", action="store_true",
                    help="drop the three cap-click tabs -- for ISOLATING them in a "
                         "comparison only, NOT a shipping option (see outer_hull)")
    ap.add_argument("--only", help="build just this variant")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    for name, cfg in sm.VARIANTS.items():
        if args.only and name != args.only:
            continue
        t = time.time()
        part = sm.build(name, engrave=not args.no_engrave,
                        click_tabs=not args.no_click_tabs)
        bb = part.bounding_box()
        kinds = Counter(str(BRepAdaptor_Surface(f.wrapped).GetType())
                        .rsplit(".", 1)[-1].replace("GeomAbs_", "") for f in part.faces())
        print(f"[{name}] {time.time()-t:.1f}s  faces={len(part.faces())}  "
              f"vol={part.volume:.4f}  valid={part.is_valid}")
        print(f"[{name}] surfaces={dict(kinds)}")
        print(f"[{name}] bbox=({bb.min.X:.4f},{bb.min.Y:.4f},{bb.min.Z:.4f})"
              f"..({bb.max.X:.4f},{bb.max.Y:.4f},{bb.max.Z:.4f})")
        step = os.path.join(OUT, f"stem_{name}.step")
        export_step(part, step)
        export_stl(part, os.path.join(HERE, f"stem_{name}.stl"),
                   tolerance=0.001, angular_tolerance=0.05)
        print(f"[{name}] wrote {step} and ./stem_{name}.stl")


if __name__ == "__main__":
    main()
