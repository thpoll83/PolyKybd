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
- ("appear", ms, key)      a name key's legend arrives: a very soft high tick

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


# the pad's chord per chapter (semitones from A4): A minor, F, C, G, A minor
CHORDS = [("E", [-24, -17, -12, -9, -5]), ("C1", [-24, -17, -12, -9, -5]), ("C4", [-28, -21, -16, -12, -9]),
          ("T", [-33, -21, -14, -9, -5]), ("I", [-26, -19, -14, -10, -7]), ("F", [-24, -17, -12, -9, -5])]


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
    """The stage turning bright: a slow breath of noise rising through the low band,
    over a soft low tone gliding up an octave."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / n
    s = _band_noise(n, lambda u: 160 + 900 * u ** 1.5, 0.5, int(rng.integers(1 << 30)))
    env = np.sin(np.pi * np.minimum(t / 0.75, 1.0) / 2) ** 2 * np.minimum(1.0, (1 - t) / 0.25)
    f = 55 * 2 ** t
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
    mono = (s * 0.14 + tone * 0.06) * env
    return np.stack([mono * 0.95, mono], 1)


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
    return out / max(np.abs(out).max(), 1e-6) * 0.4


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
    for p, notes in CHORDS:
        at = next((ms for _, ms, sid, _ in scenes if sid.startswith(p)), None)
        if at is not None:
            marks.append((at / 1000, notes))
    marks.sort()
    out = np.zeros((n, 2))
    xf = 2.0
    for k, (start, notes) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else t[-1] + 1
        w = np.clip((t - start + xf / 2) / xf, 0, 1) * np.clip((end - t + xf / 2) / xf, 0, 1)
        if not w.any():
            continue
        for j, st in enumerate(notes):
            f = _note(st)
            lfo = 0.6 + 0.4 * np.sin(2 * np.pi * t / (7 + 2.3 * j) + j)
            amp = w * lfo * (0.05 if j else 0.07)
            for side, det in ((0, 0.9985), (1, 1.0015)):
                ph = 2 * np.pi * f * det * t
                out[:, side] += amp * (np.sin(ph) + 0.15 * np.sin(2 * ph))
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


def write(events, total_ms, path):
    n = int(total_ms * SR / 1000)
    rng = np.random.default_rng(2024)
    scenes = [e for e in events if e[0] == "scene"]
    by_id = {e[2]: (e[1], e[3]) for e in scenes}
    buf = pad(total_ms, scenes)
    for k, e in enumerate(events):
        kind, ms = e[0], e[1]
        if kind == "hit":
            key, shot = e[2], e[3]
            close = shot.startswith("k_")
            p = -0.35 if int(key.split(",")[0]) < 5 else 0.35
            _add(buf, ms, _pan(thock(close, rng), p))
            _add(buf, ms + rng.uniform(260, 340), _pan(thock(close, rng, up=True), p))
        elif kind == "sweep":
            first = e[3] == "C1.2"               # the board reveal: longer, the one to remember
            _add(buf, ms, swoosh(e[2] + 1500 if first else e[2], seed=1000 + k, gain=0.26 if first else 0.22,
                                 longest=6.0 if first else 4.2))
        elif kind == "cascade":
            if not e[3]:                         # a menu; a name has its own ticks instead
                _add(buf, ms, swoosh(700, seed=2000 + k, gain=0.07))
        elif kind == "appear":
            _add(buf, ms, _pan(tick(rng), -0.4 if int(e[2].split(",")[0]) < 5 else 0.4))
        elif kind == "scene":
            sid, dur = e[2], e[3]
            if sid == "E1":                      # the sparks streaming in
                _add(buf, ms + 300, swoosh(3200, seed=99, gain=0.12))
            elif sid == "E2":                    # the name forms
                _add(buf, ms, swoosh(2200, seed=98, gain=0.1))
            elif sid == "E3":                    # the room light comes up: a swell, starting just before
                _add(buf, ms - 800, swell(3.4))
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
