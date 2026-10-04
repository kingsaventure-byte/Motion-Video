"""Courbes d'accélération. Toutes prennent t dans [0, 1] et renvoient ~[0, 1]."""
import math


def clamp01(t):
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def linear(t):
    return t


def in_quad(t):
    return t * t


def out_quad(t):
    return 1 - (1 - t) * (1 - t)


def in_out_quad(t):
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def in_cubic(t):
    return t * t * t


def out_cubic(t):
    return 1 - (1 - t) ** 3


def in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def out_quart(t):
    return 1 - (1 - t) ** 4


def in_out_quart(t):
    return 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2


def out_quint(t):
    return 1 - (1 - t) ** 5


def in_out_quint(t):
    return 16 * t ** 5 if t < 0.5 else 1 - (-2 * t + 2) ** 5 / 2


def in_expo(t):
    return 0.0 if t <= 0 else 2 ** (10 * t - 10)


def out_expo(t):
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def in_out_expo(t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def in_sine(t):
    return 1 - math.cos(t * math.pi / 2)


def out_sine(t):
    return math.sin(t * math.pi / 2)


def in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2


def out_circ(t):
    return math.sqrt(max(0.0, 1 - (t - 1) ** 2))


def in_out_circ(t):
    if t < 0.5:
        return (1 - math.sqrt(max(0.0, 1 - (2 * t) ** 2))) / 2
    return (math.sqrt(max(0.0, 1 - (-2 * t + 2) ** 2)) + 1) / 2


def out_back(t, s=1.70158):
    c3 = s + 1
    return 1 + c3 * (t - 1) ** 3 + s * (t - 1) ** 2


def in_back(t, s=1.70158):
    return (s + 1) * t ** 3 - s * t * t


def in_out_back(t, s=1.70158):
    c2 = s * 1.525
    if t < 0.5:
        return ((2 * t) ** 2 * ((c2 + 1) * 2 * t - c2)) / 2
    return ((2 * t - 2) ** 2 * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2


def out_elastic(t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def bezier(x1, y1, x2, y2):
    """Courbe de Bézier cubique façon CSS cubic-bezier(x1, y1, x2, y2)."""

    def bx(t):
        return 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3

    def by(t):
        return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3

    def dbx(t):
        return 3 * (1 - t) ** 2 * x1 + 6 * (1 - t) * t * (x2 - x1) + 3 * t * t * (1 - x2)

    def f(x):
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        t = x
        for _ in range(8):  # Newton
            d = dbx(t)
            if abs(d) < 1e-6:
                break
            t -= (bx(t) - x) / d
            t = min(1.0, max(0.0, t))
        lo, hi = 0.0, 1.0
        for _ in range(20):  # bissection de sécurité
            if abs(bx(t) - x) < 1e-6:
                break
            if bx(t) < x:
                lo = t
            else:
                hi = t
            t = (lo + hi) / 2
        return by(t)

    return f


# Courbes « signature » du moteur : départ franc, arrivée très douce.
smooth = bezier(0.65, 0.0, 0.35, 1.0)      # in-out élégant
snap = bezier(0.16, 1.0, 0.3, 1.0)         # sortie expo très premium
glide = bezier(0.45, 0.0, 0.1, 1.0)        # mouvement de caméra
anticip = bezier(0.7, -0.35, 0.3, 1.3)     # anticipation + dépassement


def spring(t, stiffness=170.0, damping=18.0, mass=1.0):
    """Ressort amorti analytique (position normalisée 0 -> 1), t en secondes."""
    if t <= 0:
        return 0.0
    w0 = math.sqrt(stiffness / mass)
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    if zeta < 1:
        wd = w0 * math.sqrt(1 - zeta * zeta)
        return 1 - math.exp(-zeta * w0 * t) * (math.cos(wd * t) + zeta * w0 / wd * math.sin(wd * t))
    return 1 - math.exp(-w0 * t) * (1 + w0 * t)
