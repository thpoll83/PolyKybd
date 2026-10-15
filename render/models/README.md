# Models made for the renders

| File | What | Made with |
|------|------|-----------|
| `keycap_stem_R3_1U.stl`, `keycap_stem_R3_1U25.stl` | the current keycap stem, flat profile (R3), engraved `R3   α` as the printed plates are | `mx_stem(u_size = 1 or 1.22, txt = str("R3   ", revision))` from `parts/keycap_stem/keycap_stem.scad`, OpenSCAD 2021.01, Noto Sans Bold (`fonts-noto-core`) |

The board's own stem model (`poly_kybd/models/keycap_stem_r7*.wrl`) carries an older
engraving. `assembly_pcb.py` swaps these in on every key of the assembly video. The
1.25U stem uses `u_size = 1.22`, as `ten_connected_pieces_1U25()` does.

Re-export after a change to the stem (from the repo root):

```bash
cd render/models
printf 'include <../../parts/keycap_stem/keycap_stem.scad>\nmx_stem(u_size = 1, txt = str("R3   ", revision));\n' > _s.scad
openscad -o keycap_stem_R3_1U.stl --export-format binstl _s.scad
sed -i 's/u_size = 1,/u_size = 1.22,/' _s.scad && openscad -o keycap_stem_R3_1U25.stl --export-format binstl _s.scad
rm _s.scad
```
