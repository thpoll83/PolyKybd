# Keycap stems — plates, engraving and re-export

Moved out of `CLAUDE.md` 2026-09-14. Verbatim.

## Keycap stems

**One `.scad` per plate in `parts/keycap_stem/variants/`, over a library that has
NO top-level geometry** — `R1..R5` curved and `S1`/`S`/`S5` stepped, each in both
`1U` and `1U25`, sixteen files. Each `include`s `../keycap_stem.scad` and makes a
single call, so a variant renders on its own: what you open in the GUI is exactly
what gets exported, and `variants/<x>.scad` → `export/keycap_stem/<x>.stl` with no
name munging. `parts/keycap_stem/build_stems.sh` walks the directory and holds no
table of its own, so **adding a plate is adding a file**.

- **`include`, not `use`, in a variant.** `use` imports modules but *not*
  variables, and the engraved `revision` is a variable. That is also why the
  library must stay free of top-level geometry: `include` executes it, so
  anything left there would appear in all sixteen plates. The photo arrangements
  that used to sit at the bottom of the library live in `preview_stems.scad`
  (a `view=` selector), which the build script does not export.
- The profile set previously existed **only** as commented-out calls at the
  bottom of `keycap_stem.scad`, exported by uncommenting one line at a time —
  exactly how revAlpha shipped the stepped plates while the curved `R2..R5` were
  missing for a whole revision.
- ⚠️ **Verify a refactor here by re-exporting all sixteen — but expect only the
  plates YOUR machine last exported to report `unchanged`.** The library/variant
  split was checked this way and came back 8 `unchanged` / 8 `CHANGED`, split
  exactly along who exported what: the eight R2–R5 plates (exported in this
  container) were byte-identical, while R1 and the three S plates (exported by
  the author on their own machine) differed. That is **not** a refactor failure —
  each of the eight was confirmed to have an identical bounding box and a volume
  within 0.04%, i.e. only the engraving is tessellated differently, per the Noto
  note above. **Restore them (`git checkout`) rather than committing the
  rewrite**, or you trade ~16 MB of diff for a re-tessellated `α`. A single plate
  is not a sufficient check either way, since the two widths and the two profile
  families take different code paths.

- ⚠️ **The engraved revision silently renders in the WRONG FACE when Noto is
  absent.** `keycap_stem.scad` asks for `text_font = "Noto:style=Bold"`, and
  fontconfig substitutes (DejaVu Sans Bold in a bare container) rather than
  failing — the plate exports fine and nothing in the output mentions it. In a
  fresh container: `apt-get install fonts-noto-core`, or `build_stems.sh
  --fetch-font` (per-user, no root). `build_stems.sh` warns via `fc-match`,
  which is the only reason this is visible at all.
- ⚠️ **WHICH Noto also matters — `--fetch-font` on a machine that already has one
  will make every later re-export report `CHANGED`.** The engraving is tessellated
  from whatever file fontconfig resolves, and the downloaded *variable* NotoSans
  and a distro *static* NotoSans-Bold do not agree: measured 46192 vs 44912 facets
  on the same plate, at identical volume and bounding box. That is a real
  difference in the glyph outlines, well above what the settle rounding absorbs, so
  it is not a bug in the comparison — it is the comparison working. Use
  `--fetch-font` to acquire a Noto where there is none, not to "refresh" one.
- **`R1` and `S1` are deliberately identical geometry** (angle 5, extra_len 0.5)
  and differ only in the engraving. That is what the source says — don't "fix" it.
- **The engraved label matches the FILENAME's profile token, in a 5-character
  field.** `txt = str("R5   ", revision)` → the keycap reads `R5 α`. The field is
  padded to 5 so the profile sits at one corner of the top face and the revision
  at the other; keep that width when adding a profile (`"S    "`, `"R3   "`,
  `"S1   "` are all 5). It was not always so: the curved plates engraved a **bare
  digit** (`3 α`) while only the stepped ones carried a letter, so a printed stem
  could not be matched to the file that made it and "is the flat one R3?" was a
  question the part itself could not answer (2026-08-17). Note the consequence
  that survives: **flat IS R3** — same parameters, same mesh, same engraving — so
  a flat stem and a curved set's R3 are one interchangeable part, not two.
- ⚠️ **A full `build_stems.sh` run exceeds a two-minute tool timeout** (16 plates,
  CGAL each). Pass name filters (`build_stems.sh R1 R2 R3`) or run it in the
  background. A run killed part-way is not harmless: it leaves the plates it did
  reach re-exported, which then have to be told apart from a real change by bbox
  and volume before being reverted.
- ⚠️ **The README profile pictures draw the coordinate AXES on purpose — the
  horizontal axis line is the REFERENCE the cap angle is read against, and
  without it the images are five tilted caps with nothing to measure against.**
  The originals were GUI screenshots with the axes visible; a first scripted
  version dropped them as chrome and lost the one thing that made the pictures
  informative (field, 2026-08-17). Two rules follow, and they pull in opposite
  directions from the obvious instinct:
  - **Never rotate the row to make the profile read better.** A view tilt adds
    itself to every cap angle *without* moving the axes, so the picture reports
    the wrong profile: a `rotate([8,0,0])` in `profile_row()` made **R3, which is
    flat by definition, sit 8° nose-up on the axis**. Tilt the **camera** instead
    (`CAM` in `render_profiles.sh`) — that moves the axes with it, so the reading
    stays honest.
  - **Render with `--view=axes`** (2021.01 supports `axes`, `scales`,
    `crosshairs`, `edges`, `wireframe`). `scales` adds tick labels that render
    rotated and unreadable at this camera, so `axes` alone is the useful one.
  - The four views must share **one** camera or they cannot be compared —
    a difference in elevation reads as a difference in profile. That is the
    entire reason `render_profiles.sh` exists rather than a note about which
    camera to use.
- **Judge a regenerated plate by bbox + volume, not by facet count.** Text
  tessellation depends on the installed font *version*, so the triangle count
  moves between machines while the part is unchanged: regenerating the committed
  revAlpha R1 here reproduced its bounding box to 0.01 mm and its volume to
  0.01 % while the facet count differed by 2240. That comparison is what proved
  the commented "Curved Profile" parameters really are the alpha R-set.

