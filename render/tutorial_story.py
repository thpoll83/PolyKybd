"""The first-run tutorial video's scene list, and the screens of each scene.

    ../PolyKybdHost/.venv/bin/python render/tutorial_story.py <out.npz>

Writes one representative frame per scene: every keycap screen (72x40) and both
status panels (128x64), plus a JSON list of the scenes beside it (<out>.json) with
the camera shot, the caption, the key pressed and the room light. tutorial_video.py
composites them over the shot's layers (a storyboard now, the video later).

The order and the words follow the firmware: base/tutorial_plan.h's phases,
anim/tutorial.c's status lines and poly_keymap.c's tutorial_tour_build() /
tutorial_tour_line() on the default split72 keymap, en-US. The tutorial picks its
three letters and the Intl letter at random; this story uses e, k, b and e.
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
SHIFTED = S.layer("_L0", True)
LETTERS = [mp for mp, t in zip(ts.MATRICES, ts.ld.parse_base_layer_keycodes(ts.KEYMAP, "_L0"))
           if len(t) == 4 and t.startswith("KC_") and t[3].isalpha()]
SCENES = []
# base/tutorial_plan.h timings the story uses
P_LETTER_IN, P_REVEAL, P_WIPE, P_DARK = 500, 2400, 1650, 200
# the language names' keys: display rows 1 and 2 of both halves, as tut_name_keys_build() orders them
NAME_KEYS = [mp for side in ("L", "R") for row in ts._name_keys()[side] for mp in row]
# the wipe's corners, item by item (tut_corner_slot): the outermost key of display row 0,
# left half then right half
_g = ts.FwSim()
_inv = {hi: mp for mp, hi in ts.mp_to_half_idx().items() if hi}
CORNERS = []
for _side, _right in (("L", False), ("R", True)):
    _best = None
    for _c in range(8):
        _gg = _g.GEOM[_side][_c]
        if int(_gg[3]) and (_side, _c) in _inv and (_best is None or (int(_gg[0]) > _best[0] if _right else int(_gg[0]) < _best[0])):
            _best = (int(_gg[0]), _inv[(_side, _c)])
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
          sweep=None, strike=False, named=(), tap=None, cascade=0, hold=False, held=(),
          beat=True, fadein=0, dur=0):
    """One scene. sweep = (origin key, run ms): a board-wide front leaves `origin`, and
    every key it passes shows this scene's legend instead of the previous one's.
    strike: the press sends the chapter-1 ripple. named: keys spelling a language name
    (their LEDs glow faintly). tap: a key pressed in place, without a close-up (a menu
    tab). cascade: how many physical rows of this scene's keys appear key by key
    (anim/menu_cascade.c; 3 for a menu or the Shift reveal, 2 for a name). hold: the
    pressed key stays down (Shift, Intl). held: keys drawn inverted for the whole scene,
    as the firmware inverts a pressed key's display. beat: may the video cut to the
    status panels before this scene. fadein: the keys fade in over this many ms."""
    point = getattr(frame, "point", None)
    fr = frame.copy()
    if status != (None, None):
        fr.status = S.status_line(*status)
    SCENES.append(dict(id=sid, shot=shot, caption=caption, press=press, ambient=ambient,
                       note=note, status=list(status), point=point, sweep=sweep, strike=strike,
                       named=list(named), tap=tap, cascade=cascade, hold=hold, held=list(held),
                       beat=beat, fadein=fadein, dur=dur, frame=fr))


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
# panels say the welcome; the room light comes up over it (0.07 -> 0.35)
scene("E3", "full", "Eden tail: the stars keep falling on the dark board; the room light comes up",
      eden(sim.TOTAL - 1), ("Welcome", "to PolyKybd"), ambient=(NIGHT + ROOM) / 2, dur=1400, beat=False)
scene("E3s", "status", "Status panels: Welcome | to PolyKybd", eden(sim.TOTAL - 1), ("Welcome", "to PolyKybd"),
      ambient=(NIGHT + ROOM) / 2, dur=1800)

# ---- chapter 1: the lit key (the firmware asks for three; the video shows two) --------
e, k = "1,3", "7,4"
lines = [("Press the", "lit key"), ("And now", "the next")]
for i, (mp, shot) in enumerate(((e, "k_e"), (k, "k_k"))):
    lit = only(BASE, {mp})
    scene(f"C1.{i + 1}a", "full", f"Letter {i + 1}: one key fades in, the rest of the board is dark",
          ringed(lit, mp), lines[i], fadein=P_LETTER_IN)
    scene(f"C1.{i + 1}b", shot, "Close-up: pressed (its display inverts), a ripple leaves the key",
          ringed(lit, mp), lines[i], press=mp, strike=True)
scene("C1.3", "full", "Good", only(BASE, set()), (None, "Good"))

# ---- chapter 2: Shift, once per hand, HELD ---------------------------------------------
lit = set(LETTERS) | {"3,0", "8,7"}
for n, (sk, shot, ask, said) in enumerate((("3,0", "k_lsft", ("Press and hold", "SHIFT"), ("All keys", "react...")),
                                           ("8,7", "k_rsft", ("Try again", "SHIFT"), ("Isn't that", "...nice?")))):
    scene(f"C2.{n + 1}a", "full", "The letters and both Shifts; this Shift pulses", ringed(only(BASE, lit), sk), ask,
          cascade=3 if n == 0 else 0)
    scene(f"C2.{n + 1}b", shot, "Close-up: Shift goes down and stays held", ringed(only(BASE, lit), sk), ask,
          press=sk, hold=True)
    scene(f"C2.{n + 1}c", "full", "Held: every letter turns capital", only(SHIFTED, lit), said, held=[sk])

# ---- the board reveal, then languages and scripts (full view and status panels only) ----
scene("C4.1", "full", "Board reveal: a wave from the last Shift lights every key", BASE,
      ("Every key", "is a screen"), sweep=("8,7", P_REVEAL))
scene("C4.2", "full", "The whole board, still", BASE, ("72 screens,", "one keyboard"))
scene("C4.3", "full", "It speaks your language", BASE, ("It speaks", "your language"))
DARK = ts.Frame({})
# two of the firmware's eleven items (s_tut_preview_all entries 0 and 5), each: a dark
# cut, its name on the keys, then a ring wipes the layout in from a corner that takes
# turns item by item (tut_corner_slot: top-left, then top-right)
items = (("el-GR", 0, "Greek", "ELLHNIKA", None, "How about"),
         ("ja-JP", 5, "Japanese", None, "JA", "Or is it"))
for n, (code, entry, latin, native, tiles, lead) in enumerate(items):
    corner = CORNERS[n]
    scene(f"C4.{4 + 3 * n}d", "full", "Every key dark for a moment", DARK, (lead, latin), dur=P_DARK, beat=False)
    scene(f"C4.{5 + 3 * n}", "full", f"The name: {latin.upper()} in Latin, and its native name on the other half",
          S.name_frame(entry, latin, native, code, ts.name_tiles(tiles) if tiles else None), (lead, latin),
          named=NAME_KEYS, cascade=2)
    scene(f"C4.{6 + 3 * n}", "full", f"A ring wipes in from a corner and every key turns {latin}",
          ts.Screens(code).layer(), (lead, latin), sweep=(corner, P_WIPE))
scene("C4.10d", "full", "Dark", DARK, ("...and many", "more layouts"), dur=P_DARK, beat=False)
scene("C4.11", "full", "160 | LAYOUTS in the heavy splash face", S.more_frame(False), ("...and many", "more layouts"),
      cascade=2)
scene("C4.12d", "full", "Dark", DARK, ("...plus", "fun scripts"), dur=P_DARK, beat=False)
scene("C4.13", "full", "10 FUN | SCRIPTS", S.more_frame(True), ("...plus", "fun scripts"), cascade=2)

# ---- the key tour: Lang menu, all on the menu camera (no status cuts) ------------------
M = "menu"
scene("T1a", "full", "Find the Lang key", ringed(BASE, "9,1"), ("Pick yours in", "the Lang menu"))
scene("T1b", "k_lang", "Close-up: the key goes down", ringed(BASE, "9,1"), ("Pick yours in", "the Lang menu"),
      press="9,1")
scene("T1c", M, "The language menu cascades in", S.lang_menu(0), ("Pick yours in", "the Lang menu"),
      cascade=3, beat=False)
regions = [("From Canada", "to Chile"), ("All across", "Europe"), ("The Middle", "East"),
           ("Languages of", "Africa"), ("The whole of", "Asia"), ("And down to", "Oceania")]
REGION = ["America", "Europe", "Middle East", "Africa", "Asia", "Oceania"]
for r in (1, 2, 3, 4, 5):
    scene(f"T2.{r}", M, f"Tab {r}: {REGION[r]}, pressed in place", ringed(S.lang_menu(r - 1), f"0,{r + 1}"),
          regions[r], tap=f"0,{r + 1}", beat=False)
    scene(f"T2.{r}b", M, f"{REGION[r]}: the flags cascade in", S.lang_menu(r), regions[r], cascade=3, beat=False)
scene("T3", M, "Base, pressed in place", ringed(S.lang_menu(5), "4,0"), ("Now back", "home"), tap="4,0", beat=False)
scene("T3b", M, "Home", BASE, ("Now back", "home"), beat=False)

# ---- the key tour: emoji ------------------------------------------------------------------
scene("T4", M, "The emoji key, pressed in place", ringed(BASE, "3,6"), ("Now for", "some emoji"), tap="3,6",
      beat=False)
scene("T4b", M, "The emoji menu cascades in", S.emoji_menu(0), ("Now for", "some emoji"), cascade=3, beat=False)
tabs = [(4, "0,5", ("Animals,", "big and small")), (5, "0,6", ("Plants", "and food")),
        (7, "5,2", ("Travel", "and places")), (8, "5,3", ("Sports", "and games"))]
prev_cat = 0
for cat, mp, words in tabs:
    scene(f"T5.{cat}", M, f"Emoji tab {cat}, pressed in place", ringed(S.emoji_menu(prev_cat), mp), words, tap=mp,
          beat=False)
    scene(f"T5.{cat}b", M, "The category cascades in", S.emoji_menu(cat), words, cascade=3, beat=False)
    prev_cat = cat
scene("T6", M, "Base, pressed in place", ringed(S.emoji_menu(prev_cat), "4,0"), ("And home", "again"), tap="4,0",
      beat=False)
scene("T6b", M, "Home", BASE, ("And home", "again"), beat=False)

# ---- the key tour: Intl, the accents and the picker ----------------------------------------
INTL = S.intl()
I_ = "7,1"
scene("T9a", M, "Hold Intl", ringed(BASE, I_), ("Hold Intl", "for accents"), beat=False)
scene("T9b", "k_intl", "Close-up: Intl goes down and stays held", ringed(BASE, I_), ("Hold Intl", "for accents"),
      press=I_, hold=True, beat=False)
scene("T9c", M, "Every letter switches to its chosen accent", INTL, ("Each letter's", "chosen accent"),
      held=[I_], beat=False)
scene("T10a", M, "Keep holding Intl, tap Ctrl", ringed(INTL, "4,0"), ("Keep holding,", "tap"), held=[I_], beat=False)
scene("T10b", "k_base", "Close-up: tap Ctrl", ringed(INTL, "4,0"), ("Keep holding,", "tap"), press="4,0", beat=False)
scene("T10c", M, "The picker is armed: Ctrl stays inverted", INTL, ("The picker", "is open"),
      held=[I_, "4,0"], beat=False)
scene("T11a", M, "Pick the letter e", ringed(INTL, e), ("Pick the", "letter e"), held=[I_, "4,0"], beat=False)
scene("T11b", "k_e", "Close-up: press e", ringed(INTL, e), ("Pick the", "letter e"), press=e, beat=False)
PICK = S.intl("e", picker=True)
scene("T11c", M, "Its accents appear on the number row", PICK, ("Its accents", "are on top"), held=[I_, "4,0"],
      beat=False)
scene("T12a", M, "Take the lit accent", ringed(PICK, "0,3"), ("Now take", "the lit accent"), held=[I_, "4,0"],
      beat=False)
scene("T12b", "k_lat2", "Close-up: take the accent", ringed(PICK, "0,3"), ("Now take", "the lit accent"), press="0,3", beat=False)
CHOSEN = S.intl(chosen={"e": 2})
scene("T12c", M, "Saved: the e key now shows its new accent", CHOSEN, ("Saved for", "the e"), held=[I_], beat=False)
scene("T13a", M, "Press the e", ringed(CHOSEN, e), ("And press", "the e"), held=[I_], beat=False)
scene("T13b", "k_e", "Close-up: e types its accent", ringed(CHOSEN, e), ("And press", "the e"), press=e, beat=False)
scene("T13c", M, "That's how accents work", CHOSEN, ("That's how", "accents work"), held=[I_], beat=False)

# ---- finale ----------------------------------------------------------------------------------
scene("F", "full", "You're ready!", BASE, ("You're", "ready!"))


def with_status_beats(scenes, ms=1800):
    """A short cut to the status panels whenever their message changes. It goes BEFORE
    the scene that brings the new message, so the instruction is read first, except
    when that scene continues an action (it follows a press or a tap: the board's
    reaction must follow at once), where it goes after."""
    out, shown = [], None
    for i, s in enumerate(scenes):
        words = [w for w in s["status"] if w]
        new = words and s["status"] != shown and s["shot"] != "status" and s.get("beat", True)
        beat = dict(s, id=s["id"] + "s", shot="status", caption="Status panels: " + " | ".join(words),
                    press=None, tap=None, sweep=None, strike=False, cascade=0, hold=False, fadein=0,
                    dur=ms) if new else None
        follows = i > 0 and (scenes[i - 1].get("press") or scenes[i - 1].get("tap"))
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
