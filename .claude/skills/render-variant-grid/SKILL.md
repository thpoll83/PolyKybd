---
name: render-variant-grid
description: Tune one look setting of a PolyKybd Blender render (render/closeup_view.py) against a reference photo by rendering low-sample preview variants one after another and sending them as one numbered, labelled comparison grid. Use when asked to "make X brighter / dimmer / more diffuse", "try a few values of PK_…", "compare against the photo", "the rims / glow / reflection is too strong", or whenever a render setting has to be picked by eye. Covers the base-env file, the sequential queue behind a running render, the grid with the photo in cell 1, and the full-quality follow-up. NOT for changing geometry or materials in code (edit render/*.py first, then use this to pick the value), and NOT for KiCad's own raytracer.
---

# Render variant grid

A look setting is picked by eye, and you can't judge a render setting by
reasoning about it. You render 2–3 variants that each change one value, put
them next to the reference photo, and let the user pick. Done six times in one
session for the RGB close-up (rim glow, edge glow, glow strength, flex
material). Every time, the script was rebuilt by hand from the previous one,
which left a stray render running once (see Pitfalls).

## 1. Write the base file

One bash file with two arrays: the look being tuned, and the view arguments
`closeup_view.py` takes after samples and width. `night_base.sh` here is the
docs RGB close-up, which you can copy as a start:

```bash
BASE_ENV=(PK_RGB=170,280 PK_EMIT=6000 PK_GLOW=15 ... "PK_LOOK=AgX - High Contrast")
VIEW=(screens_layer1 0.45 0.45 0.085 48 -15 22 6.3)
```

Quote any entry with a space (`"PK_HIDE_ROLES=diffuser resin"`). Take the
current values from the README command, not from memory.

## 2. Render the variants

```bash
S=<scratchpad>
.claude/skills/render-variant-grid/variants.sh $S/base.sh $S/v \
    ref ""  g10 "PK_GLOW=10"  g20 "PK_GLOW=20;PK_FLEX=1,0.3"
```

Separate a variant's overrides with `;`, because values may hold spaces
(`PK_LOOK=AgX - High Contrast`) and commas (`PK_RGB=170,280`).

Run it with `run_in_background`. Expect about 4 minutes per variant at the
defaults (64 samples, 1400 px wide, 4 CPUs) and about 75 minutes for a final
render at 1024 samples. The script holds a lock, so a second queue waits for
the first, and it waits for any running Blender render before it starts. It
creates the output directory and deletes each variant's old PNG first. It
prints `ok <name>` only when Blender exits 0, logs no Traceback and writes a
new PNG, and `FAILED <name>` otherwise.

- Change **one** value per variant. Two changes in one cell make the
  comparison unreadable.
- Bracket the value: one below, one above, and the current one as reference
  when it isn't already rendered.
- If the variant needs new code (a new `PK_*` option), watch the first log
  until it reaches `Sample 1/` before leaving it running. A crash in the
  material setup otherwise costs the whole queue's wait.

## 3. Build the grid

```bash
/tmp/blender-4.1.1-linux-x64/4.1/python/bin/python3.11 \
  .claude/skills/render-variant-grid/grid.py $S/cmp.jpg --crop 250,200,1050,650 \
  "photo=$S/orig1400.jpg" "glow 10=$S/v/g10.png" "glow 20=$S/v/g20.png"
```

- The **photo goes in cell 1**, resized to the render size, so every crop
  shows the same region.
- Cells are numbered **row by row**, and the number is drawn into each label.
  Say so in the caption as well. "Picture 4" was misread once when the order
  wasn't stated.
- Crop to the area being judged. A full frame at chat size hides a thin rim
  or a reflection.
- **Look at the grid yourself before sending it** (Read the JPEG), and say
  what you see changing between cells, including when it is nothing. Two
  flex variants that looked the same showed the bright patch wasn't the
  flex's colour.

## 4. Send and ask

`SendUserFile` with `display: render`, a caption that lists the cells in
order, and a recommendation. Then wait for the user's pick.

## 5. Finish

After the user picks:

1. Start the full-quality render with the picked values (the README command,
   1024 samples).
2. Put the values into the README command, and document any new `PK_*` option
   with the reason it exists.
3. Remove options that lost: an unused option in a merged PR is code nobody
   will test again.
4. When the render finishes, replace the docs image, run `npm run build` in
   polykybd-docs, and check that both pages reference the new WebP.

## Pitfalls

- ⚠️ **Never `pkill -f` a pattern that appears elsewhere in the same command.**
  The `[x]` bracket protects only the pkill argument. `pkill -f "[r]im_e"`
  next to `ls $S/rim_e*.png` killed its own shell (exit 144). The rest of the
  command never ran, and a render it was meant to stop kept going. To stop a
  queue, `pgrep -af "[b]lender -b"`, then `kill <pid>` of the script and of
  Blender, each as its own command.
- **One render at a time.** Two Blender processes on 4 CPUs finish later than
  the same two run in sequence. `variants.sh` waits for any `blender -b` for
  that reason, a top-view render included, so don't narrow the match. A
  full-quality render you start by hand is not covered by the lock, so start it
  only when no queue is running.
- **A preview at 64 samples is noisy, not wrong.** Judge brightness, colour and
  where light lands. Leave grain and fine caustics to the final render.
- **Blender loads `render/*.py` when it starts.** Editing the code while a
  variant runs changes nothing for that variant, but the next one in the queue
  picks the edit up. Don't edit mid-queue unless that is what you want.
- `grep -rn` over `render/` takes minutes because of the `.blend` and output
  files there. Grep `render/*.py` instead.
