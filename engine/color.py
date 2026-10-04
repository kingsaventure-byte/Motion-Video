"""Couleurs : tuples (r, g, b, a) en flottants 0..1."""


def hex2(c, a=1.0):
    c = c.lstrip('#')
    r, g, b = int(c[0:2], 16) / 255, int(c[2:4], 16) / 255, int(c[4:6], 16) / 255
    return (r, g, b, a)


def alpha(c, a):
    return (c[0], c[1], c[2], c[3] * a)


def mix(c1, c2, t):
    return tuple(x + (y - x) * t for x, y in zip(c1, c2))


def scale(c, k):
    return (min(1.0, c[0] * k), min(1.0, c[1] * k), min(1.0, c[2] * k), c[3])


def ramp(stops, t):
    """Dégradé multi-arrêts : stops = [(pos, couleur), ...]."""
    if t <= stops[0][0]:
        return stops[0][1]
    for i in range(1, len(stops)):
        if t <= stops[i][0]:
            p0, c0 = stops[i - 1]
            p1, c1 = stops[i]
            return mix(c0, c1, (t - p0) / (p1 - p0) if p1 > p0 else 1)
    return stops[-1][1]


def to_int(c):
    r, g, b, a = (max(0, min(255, int(round(v * 255)))) for v in c)
    return (a << 24) | (r << 16) | (g << 8) | b


def premul_int(c):
    """Couleur ARGB pour drawAtlas (modulation)."""
    return to_int(c)
