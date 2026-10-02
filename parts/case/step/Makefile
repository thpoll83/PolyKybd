# Clean B-Rep STEP export of the PolyKybd Split72 metal case.
#   SVG outlines + params  ->  build123d / OpenCASCADE  ->  clean STEP
#
# Requires: python3, build123d (PINNED, see BUILD123D_PIN) which pulls in OCP.
# Preview/validation extras: matplotlib (render), OCP (validate, comes with build123d).

PY  ?= python3
OUT ?= ../../export/case

# ⚠️ PINNED, for the same reason as the stem pipeline: the geometry is
# version-sensitive, so an unpinned `pip install` silently rewrites a fabrication
# deliverable.  VERIFIED rather than assumed -- rebuilding the committed STEPs on
# 0.12.0 reproduces metal-case-left byte for byte below the header, and
# metal-case-right to a single DIRECTION vector written `(-0.,-0.,-1.)` instead of
# `(0.,0.,-1.)`, which is the same direction (-0.0 == 0.0).
#
# Checked as an ORDER-ONLY prerequisite, so it runs on every make without making the
# outputs look out of date -- which matters here more than for the stems, because a
# needless rebuild of this model costs ~15 MINUTES (measured: 903.7 s for the right
# side alone).
BUILD123D_PIN ?= 0.12.0

.PHONY: all step validate preview clean toolchain

all: step validate

step: $(OUT)/metal-case-right.step $(OUT)/metal-case-left.step

$(OUT)/metal-case-right.step $(OUT)/metal-case-left.step: case_model.py build.py | toolchain
	$(PY) build.py

toolchain:
	@$(PY) -c "import build123d as b, sys; v = b.__version__; p = '$(BUILD123D_PIN)'; \
	  v == p or sys.exit('build123d %s is installed, but the committed STEP was generated \
with %s.  Rebuilding with another version silently rewrites it -- see \
../../../CLAUDE.md.  Run: pip install build123d==%s   (or override BUILD123D_PIN).' \
% (v, p, p))"

validate: step
	$(PY) validate_step.py $(OUT)/metal-case-right.step $(OUT)/metal-case-left.step

preview: step
	$(PY) render_compare.py   # writes compare.png (mine vs original mesh)

clean:
	rm -f $(OUT)/metal-case-*.step metal-case-*.stl compare.png
	rm -rf __pycache__
