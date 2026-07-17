# Clean B-Rep STEP export of the PolyKybd Split72 metal case.
#   SVG outlines + params  ->  build123d / OpenCASCADE  ->  clean STEP
#
# Requires: python3, build123d (pip install build123d) which pulls in OCP.
# Preview/validation extras: matplotlib (render), OCP (validate, comes with build123d).

PY ?= python3

.PHONY: all step validate preview clean

all: step validate

step: metal-case-right.step metal-case-left.step

metal-case-right.step metal-case-left.step: case_model.py build.py
	$(PY) build.py

validate: step
	$(PY) validate_step.py metal-case-right.step metal-case-left.step

preview: step
	$(PY) render_compare.py   # writes compare.png (mine vs original mesh)

clean:
	rm -f metal-case-*.step metal-case-*.stl compare.png
	rm -rf __pycache__
