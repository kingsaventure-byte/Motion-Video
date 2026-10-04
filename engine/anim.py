"""Outils d'animation : interpolation, progression, keyframes, échelonnement."""
import math
from . import ease as E


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


def invlerp(a, b, x):
    if b == a:
        return 0.0
    return (x - a) / (b - a)


def smoothstep(a, b, x):
    t = clamp(invlerp(a, b, x))
    return t * t * (3 - 2 * t)


def prog(t, start, dur, ease=E.smooth):
    """Progression 0->1 entre start et start+dur avec une courbe."""
    if dur <= 0:
        return 1.0 if t >= start else 0.0
    return ease(clamp((t - start) / dur))


def remap(t, t0, t1, v0, v1, ease=E.smooth):
    return lerp(v0, v1, ease(clamp(invlerp(t0, t1, t))))


def window(t, t_in, t_out, fade_in=0.4, fade_out=0.4, ein=E.out_cubic, eout=E.in_cubic):
    """1 entre t_in et t_out, fondu entrée/sortie."""
    a = prog(t, t_in, fade_in, ein)
    b = 1 - prog(t, t_out - fade_out, fade_out, eout) if t_out is not None else 1.0
    return min(a, b)


def stagger(t, start, i, gap, dur, ease=E.snap):
    return prog(t, start + i * gap, dur, ease)


def pulse(t, period=1.0, phase=0.0):
    return 0.5 + 0.5 * math.sin((t / period + phase) * 2 * math.pi)


class Track:
    """Piste de keyframes : [(temps, valeur, ease_vers_cette_clé), ...]."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])

    def __call__(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1]
        for i in range(1, len(ks)):
            t1, v1 = ks[i][0], ks[i][1]
            if t <= t1:
                t0, v0 = ks[i - 1][0], ks[i - 1][1]
                e = ks[i][2] if len(ks[i]) > 2 else E.smooth
                return lerp(v0, v1, e(clamp(invlerp(t0, t1, t))))
        return ks[-1][1]


def typewriter(text, t, start, cps=40.0):
    n = int(max(0.0, (t - start) * cps))
    return text[:n]


def count_up(t, start, dur, v0, v1, ease=E.out_expo):
    return lerp(v0, v1, prog(t, start, dur, ease))
