"""Acceptance test for the exported STEP -- the case's checker, reused unchanged.

The recipe says to reuse `case/step/validate_step.py`, so this delegates to it rather
than copying it: a second copy is a second thing to keep in step, and the pass criteria
(real solid, curved faces present, tight edge tolerance, sane face count) are identical
for a stem.

    python validate_step.py [file.step ...]      # defaults to both stem variants
"""
import os, sys, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
CASE_STEP = os.path.join(HERE, "..", "..", "case", "step")
OUT = os.path.join(HERE, "..", "..", "export", "keycap_stem")

if not sys.argv[1:]:
    sys.argv += [os.path.join(OUT, "stem_S_1U.step"),
                 os.path.join(OUT, "stem_S_1U25.step")]

sys.path.insert(0, CASE_STEP)
runpy.run_path(os.path.join(CASE_STEP, "validate_step.py"), run_name="__main__")
