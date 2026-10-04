"""Bruit cohérent déterministe (valeur + interpolation quintique), scalaire et vectorisé."""
import math
import numpy as np

_PERM = np.random.default_rng(1337).permutation(256)
_PERM = np.concatenate([_PERM, _PERM]).astype(np.int64)
_GRAD = np.random.default_rng(4242).uniform(-1, 1, 256)


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def noise1(x, seed=0):
    """Bruit de gradient 1D, sortie ~[-1, 1]. Accepte scalaires et tableaux numpy."""
    x = np.asarray(x, dtype=np.float64) + seed * 17.123
    i0 = np.floor(x).astype(np.int64)
    f = x - i0
    g0 = _GRAD[_PERM[i0 & 255]]
    g1 = _GRAD[_PERM[(i0 + 1) & 255]]
    v = (g0 * f + (g1 * (f - 1) - g0 * f) * _fade(f)) * 2.0
    return float(v) if v.ndim == 0 else v


def noise2(x, y, seed=0):
    x = np.asarray(x, dtype=np.float64) + seed * 31.7
    y = np.asarray(y, dtype=np.float64) + seed * 11.3
    xi = np.floor(x).astype(np.int64)
    yi = np.floor(y).astype(np.int64)
    xf, yf = x - xi, y - yi

    def g(ix, iy, dx, dy):
        h = _PERM[(_PERM[ix & 255] + iy) & 255]
        a = h * (2 * math.pi / 256)
        return np.cos(a) * dx + np.sin(a) * dy

    u, v = _fade(xf), _fade(yf)
    n00 = g(xi, yi, xf, yf)
    n10 = g(xi + 1, yi, xf - 1, yf)
    n01 = g(xi, yi + 1, xf, yf - 1)
    n11 = g(xi + 1, yi + 1, xf - 1, yf - 1)
    nx0 = n00 + u * (n10 - n00)
    nx1 = n01 + u * (n11 - n01)
    r = (nx0 + v * (nx1 - nx0)) * 1.41
    return float(r) if r.ndim == 0 else r


def fbm1(x, seed=0, octaves=3):
    s, a, f = 0.0, 1.0, 1.0
    for o in range(octaves):
        s = s + a * noise1(x * f, seed + o * 7)
        a *= 0.5
        f *= 2.0
    return s / 1.75


def rng(seed):
    return np.random.default_rng(seed)


def hash01(*args):
    """Hash déterministe -> [0, 1)."""
    h = 2166136261
    for a in args:
        for ch in str(a):
            h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h / 4294967296.0
