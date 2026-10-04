"""Composants graphiques réutilisables (style « HUD scientifique premium »)."""
import math

import numpy as np

from engine import ease as E
from engine.anim import clamp, lerp, prog
from engine.color import alpha as A, mix
from engine.painter import make_path
from . import style as St


# ------------------------------------------------------------- particules
def electrons(p, xs, ys, r=5.0, a=1.0, k=0.9, halo=0.22):
    if len(xs) == 0:
        return
    p.dots(xs, ys, r * 2.6, St.CYAN, a=(a * halo) if not isinstance(a, np.ndarray) else a * halo, sprite='halo')
    p.dots(xs, ys, r, St.CYAN_HOT, a=a, sprite='disk', glow=k, gr=3.6, gcolors=St.CYAN)


def electron(p, x, y, r=6.0, a=1.0, k=1.0, sign=False):
    electrons(p, [x], [y], r, a, k)
    if sign and r >= 9:
        p.line(x - r * 0.45, y, x + r * 0.45, y, St.BG_OUT, w=max(1.5, r * 0.18), a=a * 0.8)


def holes(p, xs, ys, r=6.0, a=1.0, k=0.7):
    if len(xs) == 0:
        return
    p.dots(xs, ys, r * 2.4, St.AMBER, a=(a * 0.16) if not isinstance(a, np.ndarray) else a * 0.16, sprite='halo')
    p.dots(xs, ys, r, St.AMBER, a=a, sprite='ring', glow=k, gsprite='ring', gr=1.25)


def hole(p, x, y, r=8.0, a=1.0, k=0.8, sign=False):
    holes(p, [x], [y], r, a, k)
    if sign and r >= 10:
        w = max(1.5, r * 0.16)
        p.line(x - r * 0.4, y, x + r * 0.4, y, St.AMBER, w=w, a=a)
        p.line(x, y - r * 0.4, x, y + r * 0.4, St.AMBER, w=w, a=a)


# ------------------------------------------------------------ typographie
def label(p, x, y, text, t, size=19, color=St.TEXT, align='left', ax=None, ay=None, sub=None,
          sub_color=St.CYAN, tracking=0.14, a=1.0, dur=0.5, weight=500, line_color=None, glow=0.0):
    """Étiquette HUD : point d'ancrage + filet + texte en capitales espacées.
    t = temps écoulé depuis l'apparition (peut être négatif)."""
    if t <= 0 or a <= 0.003:
        return
    with p.fade(a):
        lc = line_color or A(St.TEXT2, 0.7)
        if ax is not None:
            pr = prog(t, 0, dur * 0.8, E.snap)
            p.circle(ax, ay, 3.2 * E.out_back(clamp(t / 0.3)), fill=St.TEXT, glow=0.6)
            p.circle(ax, ay, 9 * pr, stroke=A(St.TEXT, 0.35 * (1 - pr * 0.5)), w=1)
            # coude : diagonale puis horizontale
            pts = [(ax, ay), (x, y - size * 0.35)]
            p.poly(pts, stroke=lc, w=1.2, trim=(0, pr))
        tt = t - (dur * 0.45 if ax is not None else 0)
        if tt > 0:
            dx = 10 if (ax is not None and align == 'left') else (-10 if ax is not None and align == 'right' else 0)
            p.text_reveal(text, x + dx, y, tt, size=size, family='grotesk', weight=weight, color=color, align=align,
                          tracking=tracking, upper=True, gap=0.018, dur=0.5, rise=0.3, glow=glow)
            if sub:
                p.text_reveal(sub, x + dx, y + size * 1.45, tt - 0.12, size=size * 0.86, family='mono', weight=400,
                              color=sub_color, align=align, tracking=0.02, gap=0.012, dur=0.45, rise=0.3, glow=0.25)


def readout(p, x, y, name, value, t, align='left', size=34, color=St.CYAN, a=1.0, name_color=St.TEXT2,
            glow=0.35):
    """Mesure : petit intitulé + grande valeur en chasse fixe."""
    if t <= 0 or a <= 0.003:
        return
    with p.fade(a):
        p.text_reveal(name, x, y, t, size=15, family='grotesk', weight=500, color=name_color, align=align,
                      tracking=0.2, upper=True, gap=0.012, dur=0.4)
        p.text_reveal(value, x, y + size * 1.25, t - 0.1, size=size, family='mono', weight=500, color=color,
                      align=align, tracking=-0.01, gap=0.02, dur=0.5, glow=glow)


def chapter_card(p, S, num, title, t0=0.15, hold=2.3, cx=960, cy=520):
    """Carte de chapitre : numéro + titre + filet, puis sortie floutée."""
    t = S.t - t0
    if t < 0 or t > hold + 1.0:
        return
    out = prog(t, hold, 0.7, E.in_cubic)
    a = 1 - out
    if a <= 0:
        return
    with p.layer(alpha=a, blur=out * 14):
        w = 120 * prog(t, 0.1, 0.9, E.snap)
        p.line(cx - w, cy + 52, cx + w, cy + 52, A(St.CYAN, 0.8), w=1.5, glow=0.6)
        p.text_reveal(num, cx, cy - 78, t, size=22, family='mono', weight=500, color=St.CYAN, align='center',
                      tracking=0.3, glow=0.6, gap=0.05)
        p.text_reveal(title, cx, cy + 22, t - 0.15, size=84, family='display', weight=700, color=St.TEXT,
                      align='center', tracking=-0.025, gap=0.03, dur=0.8, glow=0.12, upper=False)


# ---------------------------------------------------------------- formes
def arrow(p, x1, y1, x2, y2, color, w=2.5, head=12.0, pr=1.0, a=1.0, glow=0.5):
    if pr <= 0.001:
        return
    xe, ye = lerp(x1, x2, pr), lerp(y1, y2, pr)
    p.line(x1, y1, xe, ye, color, w=w, a=a, glow=glow)
    ang = math.atan2(ye - y1, xe - x1)
    hs = head * min(1.0, pr * 3)
    pts = [(xe + math.cos(ang) * hs * 0.3, ye + math.sin(ang) * hs * 0.3),
           (xe - math.cos(ang - 0.45) * hs, ye - math.sin(ang - 0.45) * hs),
           (xe - math.cos(ang + 0.45) * hs, ye - math.sin(ang + 0.45) * hs)]
    p.poly(pts, fill=color, closed=True, a=a, glow=glow)


def dimension(p, x1, y1, x2, y2, text, t, color=St.TEXT2, size=18, offset=0.0, a=1.0, text_color=None,
              side=1):
    """Cote technique : deux butées + ligne + valeur."""
    if t <= 0:
        return
    pr = prog(t, 0, 0.7, E.snap)
    with p.fade(a):
        ang = math.atan2(y2 - y1, x2 - x1)
        nx, ny = -math.sin(ang) * 9, math.cos(ang) * 9
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        hx, hy = (x2 - x1) / 2 * pr, (y2 - y1) / 2 * pr
        p.line(mx - hx, my - hy, mx + hx, my + hy, color, w=1.3)
        for sx, sy in ((mx - hx, my - hy), (mx + hx, my + hy)):
            p.line(sx - nx, sy - ny, sx + nx, sy + ny, color, w=1.3)
        ox, oy = -math.sin(ang) * (24 * side), math.cos(ang) * (24 * side)
        p.text_reveal(text, mx + ox, my + oy + (size * 0.35 if side > 0 else 0), t - 0.25, size=size, family='mono',
                      weight=500, color=text_color or St.TEXT, align='center', gap=0.02)


def brackets(p, x, y, w, h, t, color=None, L=22, wid=1.5, a=1.0):
    """Coins de cadrage façon viseur."""
    if t <= 0:
        return
    color = color or A(St.TEXT2, 0.8)
    pr = prog(t, 0, 0.6, E.snap)
    l = L * pr
    with p.fade(a * pr):
        for cx, cy, sx, sy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
            p.poly([(cx, cy + sy * l), (cx, cy), (cx + sx * l, cy)], stroke=color, w=wid, cap='square')


def panel(p, x, y, w, h, t, a=1.0, fill=None, stroke=None, r=14):
    if t <= 0:
        return
    pr = prog(t, 0, 0.6, E.snap)
    with p.fade(a * pr):
        p.rect(x, y + (1 - pr) * 16, w, h, fill=fill or A(St.BG_IN, 0.55), r=r)
        p.rect(x, y + (1 - pr) * 16, w, h, stroke=stroke or A(St.LINE, 0.9), sw=1.2, r=r)


def bit(p, x, y, value, t_change, t, size=120, a=1.0):
    """Gros chiffre binaire avec transition verticale au changement."""
    col = St.CYAN if value == 1 else St.TEXT2
    pr = prog(t, t_change, 0.35, E.snap)
    with p.fade(a):
        p.text(str(value), x, y + (1 - pr) * size * 0.25, size=size, family='mono', weight=600, color=col,
               align='center', a=pr, glow=0.8 if value == 1 else 0.1)


def wobble(t, seed, amp=1.0, speed=1.0):
    from engine.noise import noise1
    return noise1(t * speed, seed) * amp, noise1(t * speed, seed + 97) * amp
