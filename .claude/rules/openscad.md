---
paths:
  - "parts/**/*.scad"
  - "parts/**/*.py"
  - "parts/**/*.sh"
---
# Working on a printed part

Notes: `parts/OPENSCAD_NOTES.md` · `parts/PRINT_VERIFICATION.md`.

- ⚠️ **`use <x.scad>` resolves relative to the .scad FILE, not the cwd.** A helper in the
  wrong directory finds no modules, the top-level object is empty, and for a collision
  test that is a **false PASS** — indistinguishable from "no collision". Always pair a
  clearance test with a positive control that displaces the part.
- ⚠️ **openscad exits `1` for an EMPTY result and for a syntax error alike.** Test for
  the `Current top level object is empty` marker first.
- **An empty top-level object writes no file**, so a reused output path silently re-reads
  the previous run's mesh.
- **STL export is not byte-reproducible** — compare sorted facet multisets, never `cmp`.
  STL format is **per part group**: ASCII for the diffuser frames, binary for everything
  else. Match the siblings; `check_frame.py` parses ASCII only.
- ⚠️ **The engraved revision silently renders in the wrong face when Noto is absent.**
- **To LOOK at a part use `.claude/skills/explain-geometry-figure/scad_view.sh`** rather
  than hand-building `--camera` flags.
