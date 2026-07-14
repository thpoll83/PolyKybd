#!/usr/bin/env python3
"""Resumable per-layer Gerber->PDF render. Each completed layer is saved atomically,
so calling this repeatedly eventually renders all layers even with a short time limit."""
import io, os, warnings, sys; warnings.filterwarnings("ignore")
import cairosvg
from gerbonara import LayerStack

BASE = "/sessions/bold-festive-carson/mnt/outputs"
OUTDIR = os.path.join(BASE, "pcb_pages"); os.makedirs(OUTDIR, exist_ok=True)
LAYER_KEYS = [
    ("top","copper"), ("inner_2","copper"), ("inner_3","copper"), ("bottom","copper"),
    ("top","mask"), ("bottom","mask"), ("top","paste"), ("bottom","paste"),
    ("mechanical","outline"),
]
stacks = {}
budget = 40.0
import time; t0=time.time()
for sub in ("L","R"):
    for i,key in enumerate(LAYER_KEYS):
        out = os.path.join(OUTDIR, f"{sub}_{i}.pdf")
        if os.path.exists(out): continue
        if time.time()-t0 > budget:
            print("time budget reached; rerun to continue", flush=True); sys.exit(0)
        if sub not in stacks:
            stacks[sub] = LayerStack.open_dir(os.path.join(BASE,"pcb",sub))
        layer = stacks[sub].graphic_layers.get(key)
        tmp = out+".tmp"
        svg = str(layer.to_svg(fg="black", bg="white"))
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=tmp)
        os.rename(tmp, out)
        print("done", sub, i, key, flush=True)
done = sum(os.path.exists(os.path.join(OUTDIR,f"{s}_{i}.pdf")) for s in ("L","R") for i in range(len(LAYER_KEYS)))
print(f"progress {done}/{2*len(LAYER_KEYS)}", flush=True)
print("ALL DONE" if done==2*len(LAYER_KEYS) else "partial", flush=True)
