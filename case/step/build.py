"""Build the metal case right + left and export clean STEP (+ STL for preview)."""
import time, gc

# Cap the address space: OCCT's allocator over-reserves during the 112-key-hole
# booleans and can trip the container OOM killer even with plenty of RAM free.
# A soft RLIMIT_AS keeps it conservative (see README). Harmless on a big machine.
try:
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = 6_500_000_000
    if soft == resource.RLIM_INFINITY or soft > cap:
        resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
except Exception:
    pass

from build123d import export_step, export_stl
import case_model as cm

def main():
    for name, fn in (("right", cm.build_right), ("left", cm.build_left)):
        t = time.time()
        part = fn()
        bb = part.bounding_box()
        print(f"[{name}] built {time.time()-t:.1f}s  faces={len(part.faces())}  "
              f"vol={part.volume:.0f}  bbox=({bb.min.X:.2f},{bb.min.Y:.2f},{bb.min.Z:.2f})"
              f"..({bb.max.X:.2f},{bb.max.Y:.2f},{bb.max.Z:.2f})")
        export_step(part, f"metal-case-{name}.step")
        export_stl(part, f"metal-case-{name}.stl", tolerance=0.05, angular_tolerance=0.2)
        print(f"[{name}] wrote metal-case-{name}.step / .stl")
        del part; gc.collect()

if __name__ == "__main__":
    main()
