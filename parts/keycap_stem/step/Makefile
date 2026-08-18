# Clean B-Rep STEP + a dimensioned drawing for the moulded keycap stems.
#   keycap_stem.scad + params  ->  build123d / OpenCASCADE  ->  STEP, SVG
#
# Requires: python3, build123d (pip install build123d, pulls in OCP), scipy.
# `make verify` additionally wants `openscad` on PATH -- it diffs the solid against
# the .scad it was ported from, which is the check that makes the rest trustworthy.

PY  ?= python3
OUT ?= ../../export/keycap_stem
STEPS = $(OUT)/stem_S_1U.step $(OUT)/stem_S_1U25.step

.PHONY: all step drawing validate verify selftest clean

all: step drawing validate

step: $(STEPS)

$(STEPS): stem_model.py hull3d.py build.py
	$(PY) build.py

drawing: $(STEPS) drawing.py
	$(PY) drawing.py

validate: step
	$(PY) validate_step.py

verify: step
	$(PY) verify.py

selftest:
	$(PY) verify.py --self-test

clean:
	rm -f $(OUT)/stem_S_1U*.step $(OUT)/stem_S_1U*_drawing.svg *.stl
	rm -rf __pycache__
