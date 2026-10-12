"""The tutorial video's soundtrack, synthesised from the compositor's events.

    tutorial_audio.write(events, total_ms, out.wav)

Nothing is sampled: every sound is numpy maths, so there is no third-party audio and no
licence to track. The events come from tutorial_video.video_part() at video time:

- ("scene", ms, id, dur)   a scene starts; the pad's chord follows the chapter, Eden gets
                           a rising shimmer, a dark cut a soft thump, the title a low boom
- ("hit", ms, key, shot)   a key lands: a short "blop", rounder and lower in a close-up
- ("sweep", ms, run)       a ring sweeps the board: a band-passed noise "swoosh"
- ("cascade", ms, rows)    a menu or a name cascades in: a quiet three-note chime

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
    if i >= len(buf):
        return
    sig = sig[:len(buf) - i]
    buf[i:i + len(sig)] += sig


def blop(close):
    """A key landing: a sine gliding down, a little click on top."""
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    f0, f1 = (330, 150) if close else (620, 300)
    f = f1 + (f0 - f1) * np.exp(-t / 0.025)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.07 if close else 0.05)
    click = np.random.default_rng(1).standard_normal(n) * _env(n, 0.0005, 0.003) * 0.3
    return (s + click) * (0.45 if close else 0.3)


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


def swoosh(run_ms, seed=0, gain=0.22):
    """A ring sweeping the board: noise whose band rises and falls, left to right."""
    dur = min(max(run_ms / 1000, 0.6), 2.8)
    n = int(dur * SR)
    s = _band_noise(n, lambda u: 350 + 2600 * math.sin(math.pi * min(u * 1.2, 1.0)) ** 2, 0.35, seed)
    t = np.arange(n) / n
    s *= np.sin(np.pi * np.minimum(t * 1.6, 1.0) ** 0.7) ** 2 * (1 - t) ** 0.5 * gain
    pan = np.linspace(-0.6, 0.6, n)
    a = (pan + 1) * math.pi / 4
    return np.stack([s * np.cos(a), s * np.sin(a)], 1)


def bell(freq, dur=1.2, gain=0.1):
    """A soft bell: three inharmonic partials, the high ones dying first."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / d)
            for r, a, d in ((1.0, 1.0, dur / 2.5), (2.76, 0.4, dur / 6), (5.4, 0.15, dur / 12)))
    return s * np.minimum(1.0, t / 0.004) * gain


def chime(notes=(12, 15, 19), gap=0.11, gain=0.09):
    n = int((gap * len(notes) + 1.4) * SR)
    out = np.zeros((n, 2))
    for k, st in enumerate(notes):
        b = bell(_note(st), 1.2, gain)
        i = int(k * gap * SR)
        out[i:i + len(b)] += _pan(b, -0.4 + 0.4 * k)
    return out


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
    scenes = [e for e in events if e[0] == "scene"]
    buf = pad(total_ms, scenes)
    for k, e in enumerate(events):
        kind, ms = e[0], e[1]
        if kind == "hit":
            key, shot = e[2], e[3]
            close = shot.startswith("k_")
            _add(buf, ms, _pan(blop(close), -0.35 if int(key.split(",")[0]) < 5 else 0.35))
        elif kind == "sweep":
            _add(buf, ms, swoosh(e[2], seed=k))
        elif kind == "cascade":
            _add(buf, ms, chime((12, 15, 19) if e[2] >= 3 else (7, 12)))
        elif kind == "scene":
            sid, dur = e[2], e[3]
            if sid == "E1":                      # the sparks streaming in
                _add(buf, ms + 300, swoosh(4500, seed=99, gain=0.12))
            elif sid == "E2":                    # the name forms
                _add(buf, ms, chime((0, 7, 12, 16), gap=0.18, gain=0.08))
            elif sid == "E3":                    # the welcome
                _add(buf, ms, chime((12, 19), gap=0.25, gain=0.06))
            elif sid.startswith("C4.") and sid.endswith("d"):   # the dark cut before each item
                _add(buf, ms, _pan(thump(), 0.0))
            elif sid == "F":
                _add(buf, ms, chime((12, 16, 19, 24), gap=0.12, gain=0.08))
            elif sid == "Z2":                    # the screensaver comes on
                _add(buf, ms, swoosh(2500, seed=55, gain=0.08))
            elif sid == "Z3":                    # the name on black
                _add(buf, ms + 200, _pan(thump(55, 2.4, 0.18), 0.0))
                _add(buf, ms + 200, chime((-12, -5, 0, 4), gap=0.04, gain=0.07))
    buf = np.tanh(buf * 1.2) / np.tanh(1.2)      # a soft limit, then 1 dB of headroom
    buf *= 0.89 / max(np.abs(buf).max(), 1e-6)
    pcm = (np.clip(buf[:n], -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
