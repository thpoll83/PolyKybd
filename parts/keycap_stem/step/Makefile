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

# `&:` (grouped targets) is GNU Make 4.3+.  On 4.2 the line parses as an ordinary rule
# with an extra target literally named `&`, which is silently WRONG rather than an
# error -- so fail loudly instead.
ifeq ($(filter grouped-target,$(.FEATURES)),)
$(error GNU Make 4.3+ required for grouped targets; this is $(MAKE_VERSION))
endif

PY  ?= python3
OUT ?= ../../export/keycap_stem
STEPS = $(OUT)/stem_S_1U.step $(OUT)/stem_S_1U25.step

.PHONY: all step drawing validate verify selftest font clean

all: step drawing validate

step: $(STEPS)

# ⚠️ A GROUPED target (`&:`), because build.py produces BOTH files in one run.
# `$(STEPS): ; build.py` reads as one rule and is two, so `make -j` can start build.py
# twice, both writing the same pair.  A `.build-stamp` fixes that and breaks something
# else: with the stamp up to date and one STEP deleted, the STEPs' own recipe is a
# no-op, so `make step` reports success and leaves the file missing for `validate` to
# trip over (verified -- it does exactly that).  `&:` says "one invocation makes all of
# these", which make schedules once AND re-runs when any output is missing.
$(STEPS) &: stem_model.py hull3d.py font.py build.py
	$(PY) build.py

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
	rm -f $(OUT)/stem_S_1U*.step $(OUT)/stem_S_1U*_drawing.svg *.stl
	rm -rf __pycache__
	# .notosans-bold-*.ttf is left alone -- it is a cache, not an output
