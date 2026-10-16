"""A display flex's tail, from straight out of its slot to plugged into its socket.

The tail is the part of a key's flex under the board (assembly_video.py splits it off).
bend_keys() samples its bend as STEPS shape keys: t=0 sticks straight out of the slot,
t=1 is the model, plugged into its FH34 socket. In between, the strip's own curvature
is scaled along its length, theta_t(s) = theta(0) + t * (theta(s) - theta(0)): the same
strip bent less, no stretching, and the root in the slot never moves. drive() blends
the keys over a frame range.
"""
import math

import numpy as np

STEPS = 11


def _smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def centre_line(yz):
    """The strip's centre line in y-z (its width runs along x): a walk from its slot
    end (the highest point) in 0.3 mm steps, each the mean of the points just ahead."""
    p = yz[yz[:, 1].argmax()].copy()
    d = np.array([0.0, -1.0])
    line = [p.copy()]
    for _ in range(400):
        rel = yz - p
        ahead = rel @ d
        sel = (ahead > 0.15) & (ahead < 0.6) & (np.linalg.norm(rel, axis=1) < 0.8)
        if not sel.any():
            break
        q = yz[sel].mean(0)
        d = (q - p) / np.linalg.norm(q - p)
        p = p + d * 0.3
        line.append(p.copy())
    line = np.array(line)
    k = np.ones(5) / 5                            # smooth the walk, keep its ends
    return np.c_[np.convolve(np.pad(line[:, 0], 2, mode="edge"), k, "valid"),
                 np.convolve(np.pad(line[:, 1], 2, mode="edge"), k, "valid")]


def bend_keys(tail, steps=STEPS):
    """Shape keys t0..t(steps-1) on tail (its mesh in the root's frame, mm, plus its
    location). Returns (keys, plug end in the root's frame, length mm, turn deg,
    the strip's turn about z in deg)."""
    me = tail.data
    loc = np.array(tail.location)
    world = np.array([v.co[:] for v in me.vertices]) + loc
    # a thumb key turns its strip up to 20 deg about z: bend in the strip's own frame,
    # its width (the main axis of the part in the slot, in plan) along x
    top = world[world[:, 2] > world[:, 2].max() - 1.0, :2]
    w = np.linalg.svd(top - top.mean(0))[2][0]
    a = math.atan2(w[1], w[0])
    a = (a + math.pi / 2) % math.pi - math.pi / 2   # the width axis has no sign
    R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    co = world @ R                                  # rotated by -a: width along x
    yz = co[:, 1:]
    sm = centre_line(yz)
    seg = np.diff(sm, axis=0)
    ds = np.linalg.norm(seg, axis=1)
    theta = np.unwrap(np.arctan2(seg[:, 1], seg[:, 0]))
    theta = np.append(theta, theta[-1])
    idx = ((yz[:, None, :] - sm[None]) ** 2).sum(-1).argmin(1)
    T = np.c_[np.cos(theta), np.sin(theta)]
    rel = yz - sm[idx]
    along = (rel * T[idx]).sum(1)
    across = (rel * np.c_[-T[:, 1], T[:, 0]][idx]).sum(1)

    def shape(t):
        th = theta[0] + t * (theta - theta[0])
        c = np.vstack([sm[0], sm[0] + np.cumsum(np.c_[np.cos(th[:-1]), np.sin(th[:-1])] * ds[:, None], axis=0)])
        tt = np.c_[np.cos(th), np.sin(th)]
        out = co.copy()
        out[:, 1:] = c[idx] + along[:, None] * tt[idx] + across[:, None] * np.c_[-tt[:, 1], tt[:, 0]][idx]
        return out @ R.T - loc

    if not me.shape_keys:
        tail.shape_key_add(name="Basis")
    keys = []
    for i in range(steps):
        kb = tail.shape_key_add(name=f"t{i}")
        kb.data.foreach_set("co", shape(i / (steps - 1)).ravel())
        keys.append(kb)
    end = np.array([co[:, 0].mean(), sm[-1, 0], sm[-1, 1]]) @ R.T
    return keys, end, float(ds.sum()), math.degrees(theta[-1] - theta[0]), math.degrees(a)


def drive(keys, f0, f1, first=1):
    """t=0 (straight) until frame f0, t=1 (plugged) from f1, eased in between."""
    n = len(keys) - 1
    frames = sorted({first} | set(range(f0, f1 + 1)))
    for fr in frames:
        t = _smooth((fr - f0) / max(f1 - f0, 1)) * n
        lo = min(int(t), n - 1)
        w = t - lo
        for i, kb in enumerate(keys):
            kb.value = (1 - w) if i == lo else w if i == lo + 1 else 0.0
            kb.keyframe_insert("value", frame=fr)
