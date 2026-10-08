"""A board.json for another base layer, for export_screens.py.

    QT_QPA_PLATFORM=offscreen ../PolyKybdHost/.venv/bin/python render/board_layer.py _L1 out.json

PolyKybdHost's scripts/export_preview_data.py writes the shipped board.json from
`[_L0]` of the firmware's split72 default keymap. This runs the same export on
another layer (`_L1`, Qwerty Stag!, is what a fresh board boots on), from the
firmware and host checkouts beside this repo.
"""
import json
import os
import pathlib
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.path.abspath(os.path.join(HERE, "..", "..", "PolyKybdHost"))
PK = pathlib.Path(HERE, "..", "..", "qmk_firmware", "keyboards", "polykybd").resolve()
sys.path[:0] = [os.path.join(HOST, "scripts"), HOST]

import export_preview_data as epd  # noqa: E402

layer, out = sys.argv[1], sys.argv[2]
layout_args = epd._layout_args
epd._layout_args = lambda src, name: layout_args(src, layer if name == "_L0" else name)
board = epd.build(PK)["board.json"]
with open(out, "w", encoding="utf-8") as f:
    json.dump(board, f, indent=1)
print(f"{layer}: {len(board['keys'])} keys, firmware {board['fw_version']}")
