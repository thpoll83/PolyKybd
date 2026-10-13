"""The tutorial video's soundtrack, synthesised from the compositor's events.

    tutorial_audio.write(events, total_ms, out.wav)

Nothing is sampled: every sound is numpy maths, so there is no third-party audio and no
licence to track. The events come from tutorial_video.video_part() at video time:

- ("scene", ms, id, dur)   a scene starts; the pad's chord follows the chapter, Eden gets
                           a rising shimmer, a dark cut a soft thump, the title a low boom
- ("hit", ms, key, shot)   a key lands: a mechanical "thock" (THOCKS, PK_THOCK), fuller
                           in a close-up, and its softer upstroke when the key comes back
- ("sweep", ms, run)       a ring sweeps the board: a band-passed noise "swoosh", never
                           the same twice (band, direction, length and pan vary)
- ("cascade", ms, rows, named)  a menu cascades in: a short, airy swoosh
- ("appear", ms, key)      a name key's legend arrives (silent)

The stage turning bright after Eden gets a slow swell, and the ending (idle, the
screensaver, the fade to black) swells into a low organ chord that dies under the title.

The pad is a slow drone of detuned sines that changes chord with the chapter and fades
out with the picture at the end.
"""
import math
import wave

import numpy as np

SR = 48000
A4 = 440.0


def _note(n):
    """Semitones from A4 -> Hz."""
    return A4 * 2 ** (n / 12)


# the pad per chapter: (first scene prefix, chord in semitones from A4, movement). A minor
# for Eden and the lit key, F for the languages; the Lang menu breathes slowly on D minor 9,
# the emoji menu has a light, quick tremolo on C add 9, the Intl picker drifts across the
# stereo field on G sus 2, the app shortcuts breathe on E minor 11; A minor again at the end
CHORDS = [("E", [-24, -17, -12, -9, -5], None), ("C1", [-24, -17, -12, -9, -5], None),
          ("C4", [-28, -21, -16, -12, -9], None), ("T1", [-43, -31, -24, -19, -14, -10], "breathe"),
          ("T4", [-33, -21, -14, -9, -5, 3, 7], "tremolo"), ("I", [-26, -19, -14, -12, -7], "drift"),
          ("A", [-29, -22, -17, -14, -10, -5], "breathe"),
          ("F", [-24, -17, -12, -9, -5], None)]


def _env(n, attack, decay):
    """An attack ramp then an exponential decay, n samples long."""
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def _pan(mono, p):
    """Equal-power pan, p from -1 (left) to 1 (right) -> (n, 2)."""
    a = (p + 1) * math.pi / 4
    return np.stack([mono * math.cos(a), mono * math.sin(a)], 1)


def _add(buf, at_ms, sig):
    i = int(at_ms * SR / 1000)
    if i < 0:
        sig, i = sig[-i:], 0
    if i >= len(buf):
        return
    sig = sig[:len(buf) - i]
    buf[i:i + len(sig)] += sig


# key-press models: the resonances a bottom-out rings (Hz, decay s, level) and the strike's
# brightness (the noise transient's low-pass, Hz). PK_THOCK picks one; thock_samples()
# writes each to a file to choose by ear.
THOCKS = {
    "A": dict(modes=[(280, 0.030, 1.0), (520, 0.018, 0.55), (1100, 0.008, 0.25), (2400, 0.004, 0.12)], bright=2500),
    "B": dict(modes=[(350, 0.022, 1.0), (700, 0.012, 0.45), (1500, 0.006, 0.2)], bright=1800),
    "C": dict(modes=[(600, 0.015, 0.8), (1400, 0.008, 0.6), (3200, 0.005, 0.35), (5200, 0.003, 0.2)], bright=6000),
    "D": dict(modes=[(220, 0.020, 1.0), (450, 0.010, 0.4), (900, 0.005, 0.15)], bright=1500),
    "E": dict(modes=[(420, 0.028, 1.0), (980, 0.014, 0.5), (2100, 0.007, 0.3), (3900, 0.004, 0.15)], bright=3500),
}


def _lowpass(x, hz):
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(spec / (1 + (f / hz) ** 4), len(x))


def thock(close, rng, up=False, style=None):
    """One key press (or, with up, its return): a 2 ms noise strike through the
    model's damped resonances, each press detuned and levelled a little differently.
    The upstroke is shorter, higher and about a third as loud."""
    m = THOCKS[style or __import__("os").environ.get("PK_THOCK", "A")]
    n = int(0.15 * SR)
    t = np.arange(n) / SR
    tune = rng.uniform(0.95, 1.05) * (1.35 if up else 0.9 if close else 1.0)
    out = np.zeros(n)
    for f, d, a in m["modes"]:
        out += a * np.sin(2 * np.pi * f * tune * rng.uniform(0.98, 1.02) * t + rng.uniform(0, 6.3)) \
            * np.exp(-t / (d * (0.6 if up else 1.0)))
    strike = rng.standard_normal(n) * np.exp(-t / 0.0012)
    out += _lowpass(strike, m["bright"] * (1.4 if up else 1.0)) * 0.6
    out *= np.minimum(1.0, t / 0.0004)
    out /= max(np.abs(out).max(), 1e-6)
    return out * (0.42 if close else 0.32) * rng.uniform(0.85, 1.0) * (0.35 if up else 1.0)


KEYS_DIR = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),
                                     "audio", "keys")


def key_strokes(name):
    """The recorded strokes of one set in audio/keys/ (README.md there credits them):
    <name>_<n>.wav are the presses, <name>_up_<n>.wav (if any) the releases."""
    import glob
    out = []
    for f in sorted(glob.glob(__import__("os").path.join(KEYS_DIR, f"{name}_[0-9]*.wav"))):
        with wave.open(f) as w:
            out.append(np.frombuffer(w.readframes(w.getnframes()), "<i2") / 32768)
    if not out:
        raise SystemExit(f"no key strokes '{name}' in {KEYS_DIR}")
    return out


def key_releases(name):
    import glob
    out = []
    for f in sorted(glob.glob(__import__("os").path.join(KEYS_DIR, f"{name}_up_*.wav"))):
        with wave.open(f) as w:
            out.append(np.frombuffer(w.readframes(w.getnframes()), "<i2") / 32768)
    return out


def recorded_key(strokes, close, rng):
    """One press from real recordings, never twice the same: a random stroke, its pitch
    moved up to 8 %, its tone darkened by a random amount (a mix with a low-passed copy),
    its first click softened a little at random, its level up to 30 % down."""
    x = strokes[rng.integers(len(strokes))]
    # about one press in four is a deeper one: played slower, so lower and fuller
    r = rng.uniform(0.80, 0.90) if rng.random() < 0.25 else rng.uniform(0.92, 1.08)
    x = np.interp(np.arange(0, len(x) - 1, r), np.arange(len(x)), x)
    dark = rng.uniform(0.0, 0.6)
    x = x * (1 - dark) + _lowpass(x, rng.uniform(1500, 3500)) * dark
    att = int(0.003 * SR)
    x[:att] *= rng.uniform(0.7, 1.0)
    if r < 0.9:                                   # and a little more body below
        x = x + _lowpass(x, 600) * rng.uniform(0.2, 0.5)
    return x * (0.5 if close else 0.36) * rng.uniform(0.7, 1.0)


def thock_samples(out_dir):
    """thock_<X>.wav per model: eight presses at a typing pace, each with its upstroke."""
    import os
    rng = np.random.default_rng(5)
    for name in THOCKS:
        buf = np.zeros((int(4.0 * SR), 2))
        at = 0.25
        for k in range(8):
            _add(buf, at * 1000, _pan(thock(k == 7, rng, style=name), rng.uniform(-0.3, 0.3)))
            _add(buf, at * 1000 + rng.uniform(90, 140), _pan(thock(k == 7, rng, up=True, style=name), 0.0))
            at += rng.uniform(0.28, 0.45)
        _write_wav(buf / max(np.abs(buf).max(), 1e-6) * 0.8, os.path.join(out_dir, f"thock_{name}.wav"))


def tick(rng):
    """A name key's legend arriving: a very short, soft, high tick (a pixel lighting up)."""
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return _band_noise(n, lambda u: 4200, 0.35, int(rng.integers(1 << 30))) * np.exp(-t / 0.004) * 0.05 * 8


def swell(dur, seed=7):
    """The stage turning bright, like a sunrise: a low open fifth fades in, then the notes
    of an A major chord rise into it one after another (A3, E4, A4, C#5, E5), each a soft
    voice with a slow vibrato and no attack, over a breath of air that opens upwards."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    out = np.zeros((n, 2))
    fade_out = np.clip((1 - u) / 0.3, 0, 1)
    for st, start, g in ((-36, 0.0, 0.9), (-29, 0.05, 0.6),                 # A1 + E2: the ground
                         (-12, 0.18, 0.5), (-5, 0.30, 0.45), (0, 0.42, 0.4), (4, 0.54, 0.35), (7, 0.66, 0.3)):
        f = _note(st)
        env = np.clip((u - start) / 0.22, 0, 1) ** 2 * fade_out
        vib = 1 + 0.004 * np.sin(2 * np.pi * (4.5 + rng.uniform(-0.5, 0.5)) * t)
        for side, det in ((0, 0.998), (1, 1.002)):
            ph = 2 * np.pi * f * det * np.cumsum(vib) / SR
            out[:, side] += g * env * (np.sin(ph) + 0.2 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph))
    air = _band_noise(n, lambda v: 250 + 2500 * v ** 2, 0.6, int(rng.integers(1 << 30)))
    out += (air * np.clip(u / 0.6, 0, 1) * fade_out * 1.2)[:, None]
    return out / max(np.abs(out).max(), 1e-6) * 0.15


def organ(total_n, start, peak, end):
    """The ending: a low organ chord (A minor, additive pipes) swelling from `start` to
    `peak` s, then fading out by `end` s, with a slow tremolo and a chorus of detuned
    voices: the slow, dramatic fade of a film score."""
    t = np.arange(total_n) / SR
    rise = np.clip((t - start) / max(peak - start, 0.1), 0, 1) ** 2.2
    tail = np.exp(-np.maximum(t - peak, 0) / max((end - peak) / 2.6, 0.1)) * np.clip((end - t) / 0.8, 0, 1)
    env = np.where(t < peak, rise, tail)
    live = env > 1e-4
    out = np.zeros((total_n, 2))
    tt = t[live]
    trem = 1 + 0.06 * np.sin(2 * np.pi * 4.8 * tt)
    for f in (55.0, 110.0, 164.81, 220.0, 261.63, 329.63):
        for side, det in ((0, 0.997), (1, 1.003), (0, 1.0)):
            ph = 2 * np.pi * f * det * tt
            v = sum(a * np.sin(k * ph) for k, a in ((1, 1.0), (2, 0.5), (3, 0.3), (4, 0.22), (6, 0.1), (8, 0.06)))
            out[live, side] += v * (1.0 if f < 100 else 0.6)
    out[live, 1] += np.sin(2 * np.pi * 27.5 * tt) * 0.8          # the 32-foot pipe, felt more than heard
    out[live] *= (trem * env[live])[:, None]
    return out / max(np.abs(out).max(), 1e-6) * 0.3


def _write_wav(buf, path):
    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _band_noise(n, centre, width, seed):
    """White noise through a moving Gaussian band-pass: centre(t) Hz per STFT frame."""
    rng = np.random.default_rng(seed)
    hop, size = 512, 2048
    win = np.hanning(size)
    x = rng.standard_normal(n + size)
    out = np.zeros(n + size)
    freqs = np.fft.rfftfreq(size, 1 / SR)
    for i in range(0, n, hop):
        c = centre(i / n)
        spec = np.fft.rfft(x[i:i + size] * win) * np.exp(-0.5 * ((freqs - c) / (width * c)) ** 2)
        out[i:i + size] += np.fft.irfft(spec, size) * win
    return out[:n] / 3


def wipe_whoosh(style, run_ms, seed):
    """The language wipes, each its own sound: "rise" (a band climbing, left to right),
    "fall" (high to low, right to left), "whirl" (a band wobbling fast, the stereo
    flickering) and "breath" (a soft, broad, slow breath with a faint whistle in it)."""
    rng = np.random.default_rng(seed)
    dur = min(max(run_ms / 1000 * 1.5, 1.2), 4.0)
    n = int(dur * SR)
    t = np.arange(n) / n
    if style == "rise":
        s = _band_noise(n, lambda u: 300 + 3200 * u ** 1.4, 0.3, seed)
        env, pan = np.sin(np.pi * np.minimum(t / 0.7, 1)) ** 2 * (1 - t) ** 0.3, np.linspace(-0.7, 0.7, n)
    elif style == "fall":
        s = _band_noise(n, lambda u: 3800 - 3300 * u ** 0.7, 0.3, seed)
        env, pan = np.sin(np.pi * np.minimum(t / 0.3, 1) / 2) ** 2 * (1 - t) ** 1.2, np.linspace(0.7, -0.7, n)
    elif style == "whirl":
        s = _band_noise(n, lambda u: 1400 * (1 + 0.6 * math.sin(2 * math.pi * 7 * u * dur)), 0.25, seed)
        env = np.sin(np.pi * t) ** 1.5 * (0.7 + 0.3 * np.sin(2 * np.pi * 11 * t * dur))
        pan = 0.8 * np.sin(2 * np.pi * 1.6 * t * dur)
    else:                                         # breath
        s = _band_noise(n, lambda u: 500 + 900 * u, 0.9, seed)
        f = _note(rng.choice([3, 7, 10]))
        s = s + 0.25 * np.sin(2 * np.pi * f * np.arange(n) / SR) * np.sin(np.pi * t)
        # it peaks early and trails off softly, at the other wipes' level (its broad band
        # carried three times their energy at the same gain)
        env, pan = np.sin(np.pi * t ** 0.6) ** 2 * (1 - t) ** 0.8 * 0.38, np.zeros(n)
    s = s * env * 0.24
    a = (pan + 1) * math.pi / 4
    return np.stack([s * np.cos(a), s * np.sin(a)], 1)


def swoosh(run_ms, seed=0, gain=0.22, longest=4.2):
    """A ring sweeping the board: noise whose band rises and falls. It outlasts the
    sweep a little, and the seed varies the band, its peak, the length, the swell and
    the pan direction, so no two sound alike."""
    rng = np.random.default_rng(seed)
    dur = min(max(run_ms / 1000 * rng.uniform(1.3, 1.7), 0.9), longest)
    n = int(dur * SR)
    lo, top, peak = rng.uniform(200, 450), rng.uniform(1800, 3600), rng.uniform(0.35, 0.65)
    s = _band_noise(n, lambda u: lo + top * math.sin(math.pi * min(u / (2 * peak), 1.0)) ** 2
                    * (1 - 0.5 * max(0.0, u - peak)), rng.uniform(0.25, 0.5), int(rng.integers(1 << 30)))
    t = np.arange(n) / n
    s *= np.sin(np.pi * np.minimum(t / (2 * peak), 1.0)) ** 2 * (1 - t) ** rng.uniform(0.4, 1.0) * gain
    d = rng.choice([-1, 1]) * rng.uniform(0.4, 0.8)
    pan = np.linspace(-d, d, n)
    a = (pan + 1) * math.pi / 4
    return np.stack([s * np.cos(a), s * np.sin(a)], 1)


def thump(freq=70, dur=0.5, gain=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 0.6 * np.exp(-t / 0.04))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.004, dur / 4) * gain


def pad(total_ms, scenes):
    """The drone: each chapter's chord, crossfading over 2 s, the level following the
    story (a slow swell in Eden, down at idle, gone by the end of the fade to black)."""
    n = int(total_ms * SR / 1000)
    t = np.arange(n) / SR
    # which chord when: the first scene of each chapter prefix
    marks = []
    for p, notes, move in CHORDS:
        at = next((ms for _, ms, sid, _ in scenes if sid.startswith(p)), None)
        if at is not None:
            marks.append((at / 1000, notes, move))
    marks.sort()
    out = np.zeros((n, 2))
    xf = 2.0
    for k, (start, notes, move) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else t[-1] + 1
        w = np.clip((t - start + xf / 2) / xf, 0, 1) * np.clip((end - t + xf / 2) / xf, 0, 1)
        if not w.any():
            continue
        for j, st in enumerate(notes):
            f = _note(st)
            if move == "breathe":                # slow, deep swells, voice by voice
                lfo = 0.3 + 0.7 * np.sin(2 * np.pi * t / (16 + 3.1 * j) + j) ** 2
            else:
                lfo = 0.6 + 0.4 * np.sin(2 * np.pi * t / (7 + 2.3 * j) + j)
            if move == "tremolo":                # a light, quick, pulsing shimmer, high voices on top
                lfo = lfo * (1 + 0.45 * np.sin(2 * np.pi * (2.6 + 0.35 * j) * t))
            amp = w * lfo * (0.05 if j else 0.07)
            for side, det in ((0, 0.9985), (1, 1.0015)):
                ph = 2 * np.pi * f * det * t
                g = 1.0
                if move == "drift":              # the voices wander across the stereo field
                    g = 1 + 0.6 * np.sin(2 * np.pi * t / (6 + j) + j) * (1 if side else -1)
                out[:, side] += amp * g * (np.sin(ph) + 0.15 * np.sin(2 * ph))
    # a little air: noise shaped towards the low end
    rng = np.random.default_rng(7)
    spec = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    air = np.fft.irfft(spec / np.maximum(fr, 60) ** 0.9 * (fr < 3000), n)
    out += (air / (np.abs(air).max() + 1e-9) * 0.02)[:, None]
    # the level over the story
    level = np.ones(n)
    by_id = {sid: (ms / 1000, d / 1000) for _, ms, sid, d in scenes}
    if "E1" in by_id:
        level *= np.clip(t / 5.0, 0.15, 1.0)
    if "Z1" in by_id:
        s0, d = by_id["Z1"]
        level *= np.where(t > s0, np.clip(1 - 0.4 * (t - s0) / max(d, 0.1), 0.6, 1), 1)
    if "Z2" in by_id:
        s0, d = by_id["Z2"]
        fade = min(1.8, d)
        level *= np.clip((s0 + d - t) / fade, 0, 1)          # out with the picture, silent after
    return out * level[:, None]


WIPES = {"C4.6": "rise", "C4.9": "fall", "C4.12": "breath"}   # Greek, Japanese, Korean (the whirl did not fit)


def write(events, total_ms, path):
    n = int(total_ms * SR / 1000)
    rng = np.random.default_rng(2024)
    scenes = [e for e in events if e[0] == "scene"]
    by_id = {e[2]: (e[1], e[3]) for e in scenes}
    buf = pad(total_ms, scenes)
    # the key presses: recorded strokes (PK_KEYS, a set in audio/keys/; the default) or,
    # with PK_KEYS=synth, the modal models (PK_THOCK)
    keys = __import__("os").environ.get("PK_KEYS", "largekey")
    strokes = None if keys == "synth" else key_strokes(keys)
    releases = key_releases(keys) if strokes is not None else []
    up_gain = float(__import__("os").environ.get("PK_KEY_UP", 1.6))   # x the recording's own release level
    for k, e in enumerate(events):
        kind, ms = e[0], e[1]
        if kind == "hit":
            key, shot = e[2], e[3]
            hold, up_ms = (e[4], e[5]) if len(e) > 5 else (False, 250)
            close = shot.startswith("k_")
            p = -0.35 if int(key.split(",")[0]) < 5 else 0.35
            if strokes is not None:
                _add(buf, ms, _pan(recorded_key(strokes, close, rng), p))
                if releases and not hold:          # the key comes back up (a held key stays down)
                    _add(buf, ms + up_ms, _pan(recorded_key(releases, close, rng) * up_gain, p))
            else:
                _add(buf, ms, _pan(thock(close, rng), p))
                _add(buf, ms + rng.uniform(260, 340), _pan(thock(close, rng, up=True), p))
        elif kind == "release" and strokes is not None and releases:   # a held key let go
            p = -0.35 if int(e[2].split(",")[0]) < 5 else 0.35
            _add(buf, ms, _pan(recorded_key(releases, e[3].startswith("k_"), rng) * up_gain, p))
        elif kind == "sweep" and e[3] in WIPES:   # a language wipe: each its own kind of sound
            _add(buf, ms, wipe_whoosh(WIPES[e[3]], e[2], seed=3000 + k))
        elif kind == "sweep":
            first = e[3] == "C1.2"               # the board reveal: longer, the one to remember
            _add(buf, ms, swoosh(e[2] + 1500 if first else e[2], seed=1000 + k, gain=0.26 if first else 0.22,
                                 longest=6.0 if first else 4.2))
        elif kind == "cascade":
            pass                                 # a menu has the pad's own movement; a name its ticks
        elif kind == "appear":
            pass                                 # a name's keys arrive silently
        elif kind == "scene":
            sid, dur = e[2], e[3]
            if sid == "E1":                      # the sparks streaming in
                _add(buf, ms + 300, swoosh(3200, seed=99, gain=0.12))
            elif sid == "E2":                    # the name forms
                _add(buf, ms, swoosh(2200, seed=98, gain=0.1))
            elif sid == "E3":                    # the room light comes up: a swell, starting just before
                _add(buf, ms - 1000, swell(6.0))
            elif sid.startswith("C4.") and sid.endswith("d"):   # the dark cut before each item
                _add(buf, ms, _pan(thump(), 0.0))
    if "Z1" in by_id and "Z2" in by_id:
        # idle, the screensaver and the fade to black swell into a low organ chord, which
        # peaks as the picture goes black and dies away under the title
        z1, (z2, z2d) = by_id["Z1"][0] / 1000, by_id["Z2"]
        peak = (z2 + z2d) / 1000
        end = peak + (by_id["Z3"][1] / 1000 if "Z3" in by_id else 4.0)
        buf += organ(len(buf), z1, peak, end)
    buf = np.tanh(buf * 1.2) / np.tanh(1.2)      # a soft limit, then 1 dB of headroom
    buf *= 0.89 / max(np.abs(buf).max(), 1e-6)
    _write_wav(buf[:n], path)
