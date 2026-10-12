"""The first-run tutorial video's scene list, and the screens of each scene.

    ../PolyKybdHost/.venv/bin/python render/tutorial_story.py <out.npz>

Writes one representative frame per scene: every keycap screen (72x40) and both
status panels (128x64), plus a JSON list of the scenes beside it (<out>.json) with
the camera shot, the caption, the key pressed and the room light. tutorial_video.py
composites them over the shot's layers (a storyboard now, the video later).

The order and the words follow the firmware: base/tutorial_plan.h's phases,
anim/tutorial.c's status lines and poly_keymap.c's tutorial_tour_build() /
tutorial_tour_line() on the default split72 keymap, en-US. The tutorial picks its
letters and the Intl letter at random; this story uses e and u.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tutorial_screens as ts  # noqa: E402
from fw_anim_sim import FwSim, mp_to_half_idx  # noqa: E402

NIGHT, ROOM = 0.07, 0.35          # the room light during Eden, and after it (PK_AMBIENT)

S = ts.Screens()
BASE = S.layer()
SCENES = []
# base/tutorial_plan.h timings the story uses
P_LETTER_IN, P_REVEAL, P_WIPE, P_DARK = 500, 2400, 1650, 200
# the language names' keys: display rows 1 and 2 of both halves, as tut_name_keys_build() orders them
NAME_KEYS = [mp for side in ("L", "R") for row in ts._name_keys()[side] for mp in row]
# the wipe's corners, item by item (tut_corner_slot): the outermost key of display rows 0
# and 4, left half then right half
_g = ts.FwSim()
_inv = {hi: mp for mp, hi in ts.mp_to_half_idx().items() if hi}
CORNERS = []
for _side, _right, _dr in (("L", False, 0), ("R", True, 0), ("L", False, 4), ("R", True, 4)):
    _best = None
    for _c in range(8):
        _i = _dr * 8 + _c
        _gg = _g.GEOM[_side][_i]
        if int(_gg[3]) and (_side, _i) in _inv and (_best is None or (int(_gg[0]) > _best[0] if _right else int(_gg[0]) < _best[0])):
            _best = (int(_gg[0]), _inv[(_side, _i)])
    CORNERS.append(_best[1])


def only(frame, keep):
    """`frame` with every key outside `keep` dark (the lesson hides them)."""
    return ts.Frame({mp: a for mp, a in frame.keys.items() if mp in keep}, frame.status)


def ringed(frame, mp):
    """The pointing ring on key `mp` (the key the lesson waits for)."""
    fr = frame.copy()
    fr.point = mp                     # the video draws the firmware ring here and pulses the key
    return fr


def scene(sid, shot, caption, frame, status=(None, None), press=None, ambient=ROOM, note="",
          sweep=None, strike=False, named=(), cascade=0, hold=False, held=(),
          beat=True, fadein=0, dur=0, dim=0, saver=False, glow=(), fadeout=0, title="", pan=None):
    """One scene. sweep = (origin key, run ms): a board-wide front leaves `origin`, and
    every key it passes shows this scene's legend instead of the previous one's.
    strike: the press sends the chapter-1 ripple. named: keys spelling a language name
    (their LEDs glow faintly). A press on a shot that is not a close-up (k_*) is seen in
    place: the video renders that key down from the scene's own camera. cascade: how many physical rows of this scene's keys appear key by key
    (anim/menu_cascade.c; 3 for a menu or the Shift reveal, 2 for a name). hold: the
    pressed key stays down (Shift, Intl). held: keys drawn inverted for the whole scene,
    as the firmware inverts a pressed key's display. beat: may the video cut to the
    status panels before this scene. fadein: the keys fade in over this many ms. dim: idle
    engages, the keys and panels dim over this many ms. saver: the Eden screensaver. glow:
    (key, like) pairs, key's LED pulses as key `like`'s did when it was pointed at.
    fadeout: the whole picture fades to black over the scene's last this many ms. title:
    a black card with this text in the middle. pan: (from, to) along the board, 0 = left
    end, 1 = right end; the shot is cropped to the key rows and tracks across."""
    point = getattr(frame, "point", None)
    fr = frame.copy()
    if status != (None, None):
        fr.status = S.status_line(*status)
    SCENES.append(dict(id=sid, shot=shot, caption=caption, press=press, ambient=ambient,
                       note=note, status=list(status), point=point, sweep=sweep, strike=strike,
                       named=list(named), cascade=cascade, hold=hold, held=list(held),
                       beat=beat, fadein=fadein, dur=dur, dim=dim, saver=saver, glow=[list(g) for g in glow],
                       fadeout=fadeout, title=title, pan=list(pan) if pan else None, frame=fr))


def wait_press(sid, shot, key, status, frame, after, after_status, caption, after_caption,
               after_shot="full", note="", sweep=None, a_cascade=0, after_cascade=0):
    """The three beats of every step: the board points at a key, a close-up of the
    press, back to the whole board showing what the press did."""
    scene(sid + "a", "full", caption, ringed(frame, key), status, cascade=a_cascade)
    scene(sid + "b", shot, "Close-up: the key goes down", ringed(frame, key), status, press=key)
    scene(sid + "c", after_shot, after_caption, after, after_status, note=note, sweep=sweep,
          cascade=after_cascade)


# ---- Eden -------------------------------------------------------------------
sim = FwSim()
half_idx = mp_to_half_idx()


def eden(t):
    keys = {}
    for mp, hi in half_idx.items():
        if hi is None:
            continue
        b = sim.panel(hi[0], hi[1], t)
        if b is not None:
            keys[mp] = np.asarray(b, np.float32)
    return ts.Frame(keys)


scene("E1", "full", "Eden: sparks stream in, the rainbow wakes", eden(2200), ambient=NIGHT)
scene("E2", "full", "Eden: POLY KYBD / SPLIT 72 forms", eden(6500), ambient=NIGHT)
# the welcome tail (SA_TAIL_MS): the stars keep falling on the dark board while the status
# panels say the welcome; the room light comes up over it (0.07 -> 0.35). No status close-up:
# the panels read on the whole board
scene("E3", "full", "Eden tail: the stars keep falling on the dark board; the room light comes up",
      eden(sim.TOTAL - 1), ("Welcome", "to PolyKybd"), ambient=(NIGHT + ROOM) / 2, dur=3200, beat=False)

# ---- chapter 1: the lit key, then the board reveal ---------------------------------------
# The firmware asks for three letters, then Shift, then reveals the board; the video presses
# one letter in place, on the whole-board view, the reveal leaves that key, and Shift is skipped.
e = "1,3"
lit = only(BASE, {e})
scene("C1.1a", "full", "One key fades in, the rest of the board is dark", ringed(lit, e), ("Press the", "lit key"),
      fadein=P_LETTER_IN, beat=False)
scene("C1.1b", "full", "Pressed in place: its display inverts", ringed(lit, e), ("Press the", "lit key"), press=e)
scene("C1.2", "full", "Board reveal: a ring leaves the key and lights every key", BASE,
      ("Every key", "is a screen"), sweep=(e, P_REVEAL), beat=False)

# ---- languages and scripts: the whole board, no status cuts between them -----------------
scene("C4.3", "full", "It speaks your language", BASE, ("It speaks", "your language"))
DARK = ts.Frame({})
# three of the firmware's eleven items (s_tut_preview_all entries 0, 5 and 6), each: a dark
# cut, its name on the keys, then a ring wipes the layout in from a corner; the corner
# takes turns item by item (tut_corner_slot), so entry n starts from corner n % 4
items = (("el-GR", 0, "Greek", "ELLHNIKA", None, "How about"),
         ("ja-JP", 5, "Japanese", None, "JA", "Or is it"),
         ("ko-KR", 6, "Korean", None, "KO", "Maybe"))
for n, (code, entry, latin, native, tiles, lead) in enumerate(items):
    corner = CORNERS[entry % len(CORNERS)]
    scene(f"C4.{4 + 3 * n}d", "full", "Every key dark for a moment", DARK, (lead, latin), dur=P_DARK, beat=False)
    name = S.name_frame(entry, latin, native, code, ts.name_tiles(tiles) if tiles else None)
    # only the keys carrying a letter glow (tutorial_is_name_key), not the whole two rows
    scene(f"C4.{5 + 3 * n}", "full", f"The name: {latin.upper()} in Latin, and its native name on the other half",
          name, (lead, latin), named=sorted(name.keys), cascade=2, beat=False)
    scene(f"C4.{6 + 3 * n}", "full", f"A ring wipes in from a corner and every key turns {latin}",
          ts.Screens(code).layer(), (lead, latin), sweep=(corner, P_WIPE), beat=False)
scene("C4.20d", "full", "Dark", DARK, ("...and many", "more layouts"), dur=P_DARK, beat=False)
MORE = S.more_frame(False)
scene("C4.21", "full", "160 | LAYOUTS in the heavy splash face", MORE, ("...and many", "more layouts"),
      cascade=2, beat=False, named=sorted(MORE.keys))
scene("C4.22d", "full", "Dark", DARK, ("...plus", "fun scripts"), dur=P_DARK, beat=False)
FUN = S.more_frame(True)
scene("C4.23", "full", "10 FUN | SCRIPTS", FUN, ("...plus", "fun scripts"), cascade=2, beat=False,
      named=sorted(FUN.keys))

# ---- the key tour: Lang menu, on the menu camera; close-ups only for Lang and Base ------
M = "menu"
# straight from the status panels to the close-up: no whole-board beat before it
scene("T1b", "k_lang", "Close-up: the key goes down", ringed(BASE, "9,1"), ("Pick yours in", "the Lang menu"),
      press="9,1")
# the first look at each menu: closer, the key rows filling the frame, a slow pan left to right
scene("T1c", M, "The language menu cascades in; the camera tracks slowly across it", S.lang_menu(0),
      ("Pick yours in", "the Lang menu"), cascade=3, beat=False, pan=(0.0, 1.0), dur=7000)
regions = [("From Canada", "to Chile"), ("All across", "Europe"), ("The Middle", "East"),
           ("Languages of", "Africa"), ("The whole of", "Asia"), ("And down to", "Oceania")]
REGION = ["America", "Europe", "Middle East", "Africa", "Asia", "Oceania"]
for r in (1, 2, 3, 4, 5):
    scene(f"T2.{r}", M, f"Tab {r}: {REGION[r]}, pressed in place", ringed(S.lang_menu(r - 1), f"0,{r + 1}"),
          regions[r], press=f"0,{r + 1}", beat=False)
    scene(f"T2.{r}b", M, f"{REGION[r]}: the flags cascade in", S.lang_menu(r), regions[r], cascade=3, beat=False)
scene("T3a", M, "Find Base", ringed(S.lang_menu(5), "4,0"), ("Now back", "home"), beat=False)
scene("T3b", "k_base", "Close-up: Base goes down", ringed(S.lang_menu(5), "4,0"), ("Now back", "home"), press="4,0",
      beat=False)
scene("T3c", M, "Home", BASE, ("Now back", "home"), beat=False)

# ---- the key tour: emoji; close-ups only for the emoji key and Base -----------------------
scene("T4a", M, "Find the emoji key", ringed(BASE, "3,6"), ("Now for", "some emoji"), beat=False)
scene("T4b", "k_emj", "Close-up: the emoji key goes down", ringed(BASE, "3,6"), ("Now for", "some emoji"),
      press="3,6", beat=False)
scene("T4c", M, "The emoji menu cascades in; the camera tracks slowly across it", S.emoji_menu(0),
      ("Now for", "some emoji"), cascade=3, beat=False, pan=(0.0, 1.0), dur=7000)
tabs = [(4, "0,5", ("Animals,", "big and small")), (5, "0,6", ("Plants", "and food")),
        (7, "5,2", ("Travel", "and places")), (8, "5,3", ("Sports", "and games"))]
prev_cat = 0
for cat, mp, words in tabs:
    scene(f"T5.{cat}", M, f"Emoji tab {cat}, pressed in place", ringed(S.emoji_menu(prev_cat), mp), words, press=mp,
          beat=False)
    scene(f"T5.{cat}b", M, "The category cascades in", S.emoji_menu(cat), words, cascade=3, beat=False)
    prev_cat = cat
scene("T6a", M, "Find Base", ringed(S.emoji_menu(prev_cat), "4,0"), ("And home", "again"), beat=False)
scene("T6b", "k_base", "Close-up: Base goes down", ringed(S.emoji_menu(prev_cat), "4,0"), ("And home", "again"),
      press="4,0", beat=False)
scene("T6c", M, "Home", BASE, ("And home", "again"), beat=False)

# ---- the accents: close over the right half's top three rows, every press in place -------
# Hold Intl, press U: the number row shows u's variations; take one from the row on screen
# (KC_LAT7 at 5,2 is u-ring) and the U key takes it over.
I_, U_, ACC = "7,1", "6,3", "5,2"
INTL = S.intl()
PICK = S.intl("u", picker=True)
CHOSEN = S.intl("u", picker=True, chosen={"u": 7})
scene("I1a", "intl", "Hold Intl", ringed(BASE, I_), ("Hold Intl", "for accents"))
scene("I1b", "intl", "Intl goes down and stays held", ringed(BASE, I_), ("Hold Intl", "for accents"),
      press=I_, hold=True, beat=False)
# intl_h: the same camera with Intl down
scene("I1c", "intl_h", "Every letter switches to its chosen accent", INTL, ("Each letter's", "chosen accent"),
      held=[I_], beat=False)
scene("I2a", "intl_h", "Press the U", ringed(INTL, U_), ("Now press", "the U"), held=[I_], beat=False)
scene("I2b", "intl_h", "U pressed in place", ringed(INTL, U_), ("Now press", "the U"), held=[I_], press=U_,
      beat=False)
scene("I2c", "intl_h", "U's accents appear on the number row", PICK, ("Its accents", "are on top"), held=[I_],
      beat=False)
scene("I3a", "intl_h", "Take the lit accent", ringed(PICK, ACC), ("Now take", "the lit accent"), held=[I_],
      beat=False)
scene("I3b", "intl_h", "The accent pressed in place", ringed(PICK, ACC), ("Now take", "the lit accent"), held=[I_],
      press=ACC, beat=False)
# the U key takes the accent's LED light, so the hand-over reads at a glance
scene("I3c", "intl_h", "Saved: the U key now shows its new accent, lit like the accent was", CHOSEN,
      ("Saved for", "the U"), held=[I_], glow=[(U_, ACC)], beat=False)

# ---- finale, then idle: the board dims and the Eden screensaver takes over ----------------
scene("F", "full", "You're ready!", BASE, ("You're", "ready!"))
scene("Z1", "full", "Idle: the keycaps and the status panels dim", BASE, ("You're", "ready!"), dim=700, dur=1000,
      beat=False)
# the screensaver runs, then the picture fades to black and the name comes up
scene("Z2", "full", "The Eden screensaver, then a fade to black", DARK, ambient=(NIGHT + ROOM) / 2, saver=True,
      dur=5500, fadeout=1800, beat=False)
scene("Z3", "full", "Black, and the name in the middle", DARK, title="PolyKybd Split72", dur=4500, beat=False)


def with_status_beats(scenes, ms=1800):
    """A short cut to the status panels whenever their message changes. It goes BEFORE
    the scene that brings the new message, so the instruction is read first, except
    when that scene continues an action (it follows a press: the board's
    reaction must follow at once), where it goes after."""
    out, shown = [], None
    for i, s in enumerate(scenes):
        words = [w for w in s["status"] if w]
        new = words and s["status"] != shown and s["shot"] != "status" and s.get("beat", True)
        beat = dict(s, id=s["id"] + "s", shot="status", caption="Status panels: " + " | ".join(words),
                    press=None, sweep=None, strike=False, cascade=0, hold=False, fadein=0,
                    dur=ms) if new else None
        follows = i > 0 and scenes[i - 1].get("press")
        if beat and not follows:
            out.append(beat)
        out.append(s)
        if beat and follows:
            out.append(beat)
        if s["shot"] == "status" or beat:
            shown = s["status"]
    return out


if __name__ == "__main__":
    SCENES[:] = with_status_beats(SCENES)
    out = os.path.abspath(sys.argv[1])
    arrays, meta = {}, []
    for n, s in enumerate(SCENES):
        fr = s.pop("frame")
        mps = sorted(fr.keys)
        arrays[f"k{n}"] = np.stack([fr.keys[m] for m in mps]).astype(np.uint8) if mps else np.zeros((0, ts.OH, ts.OW), np.uint8)
        arrays[f"s{n}"] = np.stack([s_ if s_ is not None else np.zeros((ts.SH, ts.SW), np.float32)
                                    for s_ in fr.status]).astype(np.uint8)
        meta.append({**s, "keys": mps})
    np.savez_compressed(out, **arrays)
    json.dump(meta, open(out[:-4] + ".json", "w"), indent=1, ensure_ascii=False)
    print(len(SCENES), "scenes")
