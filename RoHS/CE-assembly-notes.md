# CE technical file — final assembly notes

To-do list for when all sections are combined into one master PDF. (Left for later on purpose — page
numbers and section order stay in flux until every part exists.)

## 1. Fix the running order and page offsets
Each generated PDF now takes `--start N` and prints where the next section should begin, so page
numbers run continuously across the bundle. Decide the order, then rebuild each with the right offset,
e.g.:

```
python3 appendix-tools/build_schematics.py --start 1     # prints -> next section at page X
python3 appendix-tools/pcb_merge.py        --start X
python3 appendix-tools/build_appendix.py   --start Y
```

## 2. Section names in the header
The header/footer section labels are currently hardcoded per script
("Schematics", "PCB Layer Documentation", "RoHS Compliance Appendix"). If we want
"Annex A / B / C …", change the `SECTION = "..."` line at the top of each build script.
Shared styling (doc name, colours, frame) lives in `appendix-tools/ce_common.py`.

## 3. Declaration of Conformity
`EU-Declaration-of-Conformity.docx` is a standalone Word doc (Arial, matches the PDFs) and does **not**
yet carry the shared PDF header/footer. When bundling: convert it to PDF and stamp it with the same
frame + page offset (reuse `ce_common.stamp` / `draw_frame`). Also fill the `[TO CONFIRM]` fields first.

## 4. PCB silkscreen layers
`PolyKybd-PCB-Layers.pdf` currently omits the silkscreen layers (they were too heavy to rasterise in the
build environment). Re-export all layers — including silkscreen — natively with
`kicad-cli pcb export pdf` from the KiCad boards and refresh the PDF before final assembly. (See
`CE-content-authoring-task.md`.)

## 5. Still-missing content before a complete file
Author the written documents in `CE-content-authoring-task.md` (general description, theory of
operation, standards list, risk assessment, user manual, marking/label), and obtain the **EMC test
report** (EN 55032 / EN 55035) from a lab. Slot these in per `CE-Technical-File-Checklist.md`.

## 6. Merge & finish
Concatenate the section PDFs (pypdf), add a master cover page and a top-level table of contents /
bookmarks, and confirm every page reads A4 with a continuous "Page N" footer. Fonts across all
generated sections are Helvetica (PDFs) / Arial (DoC) — keep it that way for any new sections.
