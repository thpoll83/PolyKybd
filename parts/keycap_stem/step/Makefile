# Clean B-Rep STEP + a dimensioned drawing for the moulded keycap stems.
#   keycap_stem.scad + params  ->  build123d / OpenCASCADE  ->  STEP, SVG
#
# Requires: python3, build123d (PINNED, see BUILD123D_PIN), scipy, fontTools, and
# `openscad` on PATH.  openscad is NOT optional for a full `make`: the parity check
# diffs the solid against the .scad it was ported from, and that is the check that
# makes the rest trustworthy.  `make step` / `make drawing` alone do not need it.
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

# ⚠️ PINNED, and it is load-bearing.  build123d 0.13.0 projects this sheet materially
# differently from 0.12.0 (111 of 2087 paths, 8 structurally, a 43 mm coordinate delta)
# and rewrites the STEP below its header, so an unpinned `pip install` silently rewrites
# a fabrication deliverable.  Checked as an ORDER-ONLY prerequisite below, so it runs on
# every make without making the outputs look out of date.
BUILD123D_PIN ?= 0.12.0
SCAD_SRC = ../keycap_stem.scad
OUT ?= ../../export/keycap_stem
STEPS = $(OUT)/stem_S_1U.step $(OUT)/stem_S_1U25.step

.PHONY: all step drawing validate verify selftest font clean toolchain parity

all: step drawing validate parity

step: $(STEPS)

# ⚠️ A GROUPED target (`&:`), because build.py produces BOTH files in one run.
# `$(STEPS): ; build.py` reads as one rule and is two, so `make -j` can start build.py
# twice, both writing the same pair.  A `.build-stamp` fixes that and breaks something
# else: with the stamp up to date and one STEP deleted, the STEPs' own recipe is a
# no-op, so `make step` reports success and leaves the file missing for `validate` to
# trip over (verified -- it does exactly that).  `&:` says "one invocation makes all of
# these", which make schedules once AND re-runs when any output is missing.
$(STEPS) &: stem_model.py hull3d.py font.py build.py | toolchain
	$(PY) build.py

drawing: $(STEPS) drawing.py | toolchain
	$(PY) drawing.py

validate: step
	$(PY) validate_step.py

verify: step
	$(PY) verify.py

toolchain:
	@$(PY) -c "import build123d as b, sys; v = b.__version__; p = '$(BUILD123D_PIN)'; \
	  v == p or sys.exit('build123d %s is installed, but the committed STEP and drawing \
were generated with %s.  Rebuilding with another version silently rewrites them -- see \
../../../CLAUDE.md.  Run: pip install build123d==%s   (or override BUILD123D_PIN).' \
% (v, p, p))"

# ⚠️ A stamp is the RIGHT shape here and the wrong shape for $(STEPS) -- the difference
# is that this target has no file output of its own, so the stamp IS the result.  (The
# note on the grouped target above is about a stamp standing in for real outputs, where
# deleting one output left the recipe a no-op.  Do not "simplify" the two to match.)
#
# It depends on the .scad because that is what divergence means: build.py does not READ
# the .scad, so a change there cannot alter the export -- it can only make the export
# wrong, and only this check notices.
parity: .parity-stamp
.parity-stamp: $(STEPS) $(SCAD_SRC) verify.py stem_model.py
	$(PY) verify.py
	@touch $@

selftest:
	$(PY) verify.py --self-test

font:
	$(PY) font.py

clean:
	rm -f $(OUT)/stem_S_1U*.step $(OUT)/stem_S_1U*_drawing.svg *.stl
	rm -rf __pycache__
	# .notosans-bold-*.ttf is left alone -- it is a cache, not an output
