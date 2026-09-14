# OpenSCAD here — CLI, cameras and traps

Moved out of `CLAUDE.md` 2026-09-14. Verbatim.

## OpenSCAD

The CLI is **2021.01** (CGAL backend only — there is no Manifold backend here, so
advice that starts "switch to Manifold" does not apply).

```bash
# export geometry -- no display needed
openscad -o out.stl --export-format asciistl part.scad
# render a PNG -- display IS needed
xvfb-run -a openscad -o view.png --imgsize=1000,700 --camera=… --render=cgal part.scad
```

⚠️ **To LOOK at a part, use the existing wrapper — don't hand-roll the flags.**
`.claude/skills/explain-geometry-figure/scad_view.sh` takes `out.png model.scad
[top|front|iso|<camera>]`, handles the missing-display and empty-PNG traps, and
documents both `--camera` forms (7 numbers = gimbal `transx,y,z, rotx,y,z, dist`;
6 = `eye, centre`). It was written for that skill's figures but is a general
viewer. This is worth stating because it did not get used: a session spent ~12
hand-built `--camera`/`--imgsize`/`--render` invocations, and five of those were
wasted purely on camera geometry, while the wrapper sat one directory away in
this repo (2026-08-17). Same lesson as the control-server deadlock in
`PolyKybdHost/CLAUDE.md` — **the remedy was already in the tree and the failure
was search, not design.** Search the skills for a helper before writing one —
recursively, since each skill is its own directory:
`grep -RIn '<what you need>' .claude/skills/`.

Four traps, each of which has cost real time:

- ⚠️ **`use <x.scad>` resolves relative to the .scad FILE, not the cwd.** A helper
  written in the wrong directory silently finds no modules, so the top-level
  object is empty — and for an intersection test that is **indistinguishable from
  "no collision"**. It is a false PASS, not an error. **Always pair a
  clearance/collision test with a positive control** that displaces the part a
  couple of mm and confirms the test still reports an overlap;
  `parts/diffuser/check_frame.py` does exactly this.
- ⚠️ **openscad exits `1` for an EMPTY result and `1` for a syntax error alike**
  (both verified). So the return code cannot classify the outcome: test for the
  `Current top level object is empty` marker **first**, then treat any remaining
  non-zero exit as a failure. Getting this backwards makes every clean
  no-collision result raise.
- **An empty top-level object writes no output file**, so a script that reuses one
  output path across several runs will silently re-read the *previous* run's mesh.
  Give each invocation its own output file.
- **`$fn` set at your top level does NOT override a `$fn=` hard-coded inside a
  module's primitives.** The facets you see are the facets the STL has.
- ⚠️ **Framing a render: `--viewall` is loose, and `rotz` decides which model axis
  runs across the screen.** Two separate camera traps, both of which read as a
  broken model rather than a bad camera:
  - **`--viewall --autocenter` fits the bounding SPHERE**, so a wide, shallow
    subject (a row of parts) comes out small in a sea of margin — ~60% dead space
    on a 5-stem lineup. Give an explicit `dist` instead and tune it; that is also
    the ortho scale in the 7-number form.
  - **The axis you `translate()` the row along must match the camera's `rotz`** —
    the model's own layout, *not* the camera's `transx,y,z`. At `rotz=0` the
    model's X runs horizontally on screen, at `rotz=90` it is Y. Lay a row out
    along the wrong one and the parts stack in DEPTH — they overlap into a single
    blob, which looks like a geometry failure, not a viewpoint. Cost three renders
    before it was obvious.
  - Useful `rotx` values, gimbal form: `0` top, `90` pure side, `180` straight up
    at the underside (what "from the backside" usually means for a keycap),
    `70`–`80` a 3/4 that still shows the top face.
- **STL export is not byte-reproducible.** Facets come out in a different order
  run to run, so re-exporting an *unchanged* design still rewrites the whole file
  (23k lines of diff on one frame), burying any real change. Compare meshes as a
  **sorted facet multiset**, not with `cmp` — and when only the order moved, put
  the committed bytes back. `parts/diffuser/build_frame.sh` does this automatically;
  the same trick is what proves a refactor left the solid alone.

`use <>` imports a file's modules and **ignores its top-level geometry**, which is
how `parts/diffuser/diffuser.scad` can render a whole print plate on its own while
`diffuser_frame_*.scad` pulls just `diffuser()` out of it. ⚠️ `led_caps.scad`
(the superseded earlier generation, kept beside it) defines `diffuser()`,
`diffuser_cluster()` and `torus()` under the SAME names — so a file that
`use <>`s both silently gets one set of definitions.

