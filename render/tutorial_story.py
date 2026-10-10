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


def only(frame, keep):
    """`frame` with every key outside `keep` dark (the lesson hides them)."""
    return ts.Frame({mp: a for mp, a in frame.keys.items() if mp in keep}, frame.status)


def ringed(frame, mp):
    """The pointing ring on key `mp` (the key the lesson waits for)."""
    fr = frame.copy()
    base = fr.keys.get(mp, np.zeros((ts.OH, ts.OW), np.float32))
    fr.keys[mp] = ts.ring(base, ts.OW / 2, ts.OH / 2, 19, 3)
    return fr


def scene(sid, shot, caption, frame, status=(None, None), press=None, ambient=ROOM, note=""):
    fr = frame.copy()
    if status != (None, None):
        fr.status = S.status_line(*status)
    SCENES.append(dict(id=sid, shot=shot, caption=caption, press=press, ambient=ambient,
                       note=note, status=list(status), frame=fr))


def wait_press(sid, shot, key, status, frame, after, after_status, caption, after_caption,
               after_shot="full", note=""):
    """The three beats of every step: the board points at a key, a close-up of the
    press, back to the whole board showing what the press did."""
    scene(sid + "a", "full", caption, ringed(frame, key), status)
    scene(sid + "b", shot, "Close-up: the key goes down", ringed(frame, key), status, press=key)
    scene(sid + "c", after_shot, after_caption, after, after_status, note=note)


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
scene("E3", "full", "Eden tail: welcome over falling stars; the room light comes up",
      eden(sim.INTRO + sim.HOLD + 600), ("Welcome", "to PolyKybd"), ambient=(NIGHT + ROOM) / 2,
      note="room light ramps 0.07 -> 0.35 over ~2 s")

# ---- chapter 1: three letters --------------------------------------------------
e, k, b = "1,3", "7,4", "3,5"
lines = [("Press the", "lit key"), ("And now", "the next"), ("One more", "and done")]
for i, (mp, shot) in enumerate(((e, "k_e"), (k, "k_k"), (b, "k_b"))):
    lit = only(BASE, {mp})
    scene(f"C1.{i + 1}a", "full", f"Letter {i + 1}: one key fades in, the rest of the board is dark",
          lit, lines[i])
    scene(f"C1.{i + 1}b", shot, "Close-up: pressed, a ripple ring leaves the key",
          ringed(lit, mp), lines[i], press=mp)
scene("C1.4", "full", "Good", only(BASE, set()), (None, "Good"))

# ---- chapter 2: Shift, once per hand -------------------------------------------
lit = set(LETTERS) | {"3,0", "8,7"}
wait_press("C2.1", "k_lsft", "3,0", ("Press and hold", "SHIFT"), only(BASE, lit),
           only(SHIFTED, lit), ("All keys", "react..."),
           "The letters reveal; the left Shift pulses", "A wave repaints every letter as a capital")
wait_press("C2.2", "k_rsft", "8,7", ("Try again", "SHIFT"), only(BASE, lit),
           only(SHIFTED, lit), ("Isn't that", "...nice?"),
           "Now the right Shift", "Capitals again, from the other hand")

# ---- chapter 3: a layer, and the notation ------------------------------------
FN = S.layer("_FL")
wait_press("C3.1", "k_fn", "2,0", ("Now hold", "Fn"), only(BASE, lit | {"2,0"}),
           FN, (None, "a whole layer"), "Hold Fn", "The whole Fn layer appears")
scene("C3.2", "full", "Status panels explain the marks on layer keys", only(BASE, lit),
      ("Layer keys:", "no mark = hold"))

# ---- chapter 3: the board reveal, languages and scripts -------------------------
scene("C4.1", "full", "Board reveal: a wave from the last Shift lights every key", BASE,
      ("Every key", "is a screen"))
scene("C4.2", "full", "The whole board, still", BASE, ("72 screens,", "one keyboard"))
scene("C4.3", "full", "It speaks your language", BASE, ("It speaks", "your language"))
mid = ["2,1", "2,2", "2,3", "2,4", "2,5", "7,2", "7,3", "7,4", "7,5", "7,6"]
scene("C4.4", "full", "The name: Latin on the left half, native script on the right",
      ts.Frame(S.spelled("GREEKΕΛΛΗΝ", mid)), ("How about", "Greek"))
greek = ts.Screens("el-GR").layer()
scene("C4.5", "right", "A ring wipes in from a corner and every key turns Greek", greek, ("How about", "Greek"),
      note="then Arabic, Hebrew, Hindi, Thai, Japanese, Korean, Elvish, Runes, Aurebesh, Braille; "
           "the video shows 3-4 of them")
scene("C4.6", "full", "160 LAYOUTS spelled on the keys", ts.Frame(S.spelled("160LAYOUTS", mid)),
      ("...and many", "more layouts"))
scene("C4.7", "full", "10 FUN SCRIPTS", ts.Frame(S.spelled("10FUNSCRPT", mid)), ("...plus", "fun scripts"))

# ---- the key tour: Lang menu ------------------------------------------------------
wait_press("T1", "k_lang", "9,1", ("Pick yours in", "the Lang menu"), BASE,
           S.lang_menu(0), ("Pick yours in", "the Lang menu"),
           "Find the Lang key", "The language menu: region tabs on top, flags below", after_shot="left")
regions = [("From Canada", "to Chile"), ("All across", "Europe"), ("The Middle", "East"),
           ("Languages of", "Africa"), ("The whole of", "Asia"), ("And down to", "Oceania")]
REGION = ["America", "Europe", "Middle East", "Africa", "Asia", "Oceania"]
for r in (1, 2, 3, 4, 5):
    scene(f"T2.{r}", "tabs_l", f"Tab {r}: {REGION[r]} (press the pulsing tab)", ringed(S.lang_menu(r - 1), f"0,{r + 1}"),
          regions[r], press=f"0,{r + 1}")
    scene(f"T2.{r}b", "left", f"{REGION[r]}: the flags cascade in", S.lang_menu(r), regions[r])
wait_press("T3", "k_base", "4,0", ("Now back", "home"), S.lang_menu(5), BASE, ("Now back", "home"),
           "Base key, back to the letters", "Home")

# ---- the key tour: emoji ----------------------------------------------------------
wait_press("T4", "k_emj", "3,6", ("Now for", "some emoji"), BASE, S.emoji_menu(0), ("Now for", "some emoji"),
           "The emoji key", "The emoji menu", after_shot="left")
tabs = [(4, "0,5", "tabs_l", ("Animals,", "big and small")), (5, "0,6", "tabs_l", ("Plants", "and food")),
        (7, "5,2", "tabs_r", ("Travel", "and places")), (8, "5,3", "tabs_r", ("Sports", "and games"))]
prev = 0
for cat, mp, shot, words in tabs:
    scene(f"T5.{cat}", shot, f"Emoji tab {cat}: {words[0]} {words[1]}", ringed(S.emoji_menu(prev), mp), words, press=mp)
    scene(f"T5.{cat}b", "left" if shot == "tabs_l" else "right", "The category's emoji cascade in", S.emoji_menu(cat), words)
    prev = cat
wait_press("T5.p", "k_enext", "5,7", ("Flip to", "the next page"), S.emoji_menu(8), S.emoji_menu(8, 1),
           ("Flip to", "the next page"), "Page arrow", "The second page", after_shot="right")
wait_press("T6", "k_base", "4,0", ("And home", "again"), S.emoji_menu(8, 1), BASE, ("And home", "again"),
           "Base key", "Home")

# ---- the key tour: Fn and Num -----------------------------------------------------
wait_press("T7", "k_fn", "2,0", ("Hold Fn for", "the F-keys"), BASE, FN, ("F1 to F12,", "and more"),
           "Hold Fn", "The Fn layer, 3 s")
wait_press("T8", "k_num", "4,7", ("Hold Num for", "a number pad"), BASE, S.layer("_NL"),
           ("Digits and", "math keys"), "Hold Num", "The number pad, 3 s")

# ---- the key tour: the Intl chapter -------------------------------------------------
INTL = S.intl()
wait_press("T9", "k_intl", "7,1", ("Hold Intl", "for accents"), BASE, INTL, ("Each letter's", "chosen accent"),
           "Hold Intl", "Each letter shows its chosen accent", after_shot="left")
scene("T10a", "full", "Hold Intl again, keep holding", ringed(INTL, "4,0"), ("Keep holding,", "tap"))
scene("T10b", "k_base", "Close-up: tap Ctrl", ringed(INTL, "4,0"), ("Keep holding,", "tap"), press="4,0")
scene("T10c", "numrow", "The picker is open: the number row waits for a letter", INTL, ("The picker", "is open"))
scene("T11a", "k_e", "Close-up: press e", ringed(INTL, e), ("Pick the", "letter e"), press=e)
PICK = S.intl("e", picker=True)
scene("T11b", "numrow", "Its accents are on top", PICK, ("Its accents", "are on top"))
scene("T12a", "k_lat2", "Close-up: take the lit accent", ringed(PICK, "0,3"), ("Now take", "the lit accent"), press="0,3")
CHOSEN = S.intl("e", picker=True, chosen={"e": 2})
scene("T12b", "numrow", "Saved for the e", CHOSEN, ("Saved for", "the e"))
scene("T13a", "k_e", "Hold Intl one last time and press e", ringed(S.intl(chosen={"e": 2}), e),
      ("And press", "the e"), press=e)
scene("T13b", "full", "That's how accents work", S.intl(chosen={"e": 2}), ("That's how", "accents work"))

# ---- finale -------------------------------------------------------------------------
scene("F", "full", "You're ready!", BASE, ("You're", "ready!"))

if __name__ == "__main__":
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
