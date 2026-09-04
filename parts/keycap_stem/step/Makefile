# Clean B-Rep STEP + a dimensioned drawing for the moulded keycap stems.
#   keycap_stem.scad + params  ->  build123d / OpenCASCADE  ->  STEP, SVG
#
# Requires: python3, build123d (pip install build123d, pulls in OCP), scipy, fontTools.
# `make verify` additionally wants `openscad` on PATH -- it diffs the solid against
# the .scad it was ported from, which is the check that makes the rest trustworthy.
#
# `make font` fetches the engraving font.  It happens automatically on first build; the
# target exists so you never reach for ../build_stems.sh --fetch-font, which fetches AND
# re-exports all sixteen committed printed plates against the new font.

PY  ?= python3
OUT ?= ../../export/keycap_stem
STEPS = $(OUT)/stem_S_1U.step $(OUT)/stem_S_1U25.step

.PHONY: all step drawing validate verify selftest font clean

all: step drawing validate

step: $(STEPS)

# ⚠️ ONE stamp target, not two output targets sharing a recipe.  `$(STEPS): ; build.py`
# reads as one rule and is two, so `make -j` can start build.py twice -- both writing
# the same pair of STEP files.  The stamp is the single thing make schedules; the STEPs
# just depend on it, and their own recipe is empty.
.build-stamp: stem_model.py hull3d.py font.py build.py
	$(PY) build.py
	@touch $@

$(STEPS): .build-stamp
	@:

drawing: $(STEPS) drawing.py
	$(PY) drawing.py

validate: step
	$(PY) validate_step.py

verify: step
	$(PY) verify.py

selftest:
	$(PY) verify.py --self-test

font:
	$(PY) font.py

clean:
	rm -f $(OUT)/stem_S_1U*.step $(OUT)/stem_S_1U*_drawing.svg *.stl .build-stamp
	rm -rf __pycache__
	# .notosans-bold.ttf is left alone -- it is a cache, not an output
