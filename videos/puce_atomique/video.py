"""« Au cœur du silicium » — ce qui se passe vraiment dans une puce quand elle calcule."""
import math

import numpy as np
import skia

from engine import ease as E
from engine.anim import clamp, prog
from engine.color import alpha as A, mix
from engine.noise import noise1, rng
from engine.video import Video

from . import style as St
from .scenes.s00_intro import Intro
from .scenes.s01_echelle import Echelle
from .scenes.s02_silicium import Silicium
from .scenes.s03_dopage import Dopage
from .scenes.s04_transistor import Transistor
from .scenes.s05_electrons import Electrons
from .scenes.s06_portes import Portes
from .scenes.s07_horloge import Horloge
from .scenes.s08_chaleur import Chaleur
from .scenes.s09_quantique import Quantique
from .scenes.s10_finale import Finale


class Backdrop:
    """Fond : dégradé profond pré-calculé (tramé), nappes de lumière lentes, poussières en bokeh."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W * 0.5) / (W * 0.66)) ** 2 + ((yy - H * 0.44) / (H * 0.82)) ** 2)
        t = np.clip(d / 1.25, 0, 1)
        t = t * t * (3 - 2 * t)
        c0, c1 = np.array(St.BG_IN[:3]), np.array(St.BG_OUT[:3])
        img = c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]
        img = img * 255 + rng(3).uniform(-0.5, 0.5, (H, W, 1))
        rgba = np.concatenate([np.clip(img + 0.5, 0, 255), np.full((H, W, 1), 255.0)], axis=2).astype(np.uint8)
        self.img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
        g = rng(11)
        n = 80
        self.dx = g.uniform(0, W, n)
        self.dy = g.uniform(0, H, n)
        self.dz = g.uniform(0.25, 1.0, n)
        self.dr = g.uniform(1.2, 3.2, n) * (0.6 + self.dz)
        self.dph = g.uniform(0, 100, n)

    def draw(self, p, t, energy=1.0, tint=None, dust=1.0):
        p.blit(self.img, 0, 0, self.W, self.H)
        # Nappes lumineuses très lentes.
        x1 = self.W * 0.28 + noise1(t * 0.05, 1) * 160
        y1 = self.H * 0.30 + noise1(t * 0.05, 2) * 90
        x2 = self.W * 0.76 + noise1(t * 0.04, 3) * 160
        y2 = self.H * 0.74 + noise1(t * 0.04, 4) * 90
        c1 = tint or St.BLUE
        p.dots([x1], [y1], [820], c1, a=0.075 * energy, sprite='soft')
        p.dots([x2], [y2], [760], St.VIOLET, a=0.05 * energy, sprite='soft')
        # Poussières en suspension (parallaxe selon la profondeur).
        if dust > 0:
            xs = (self.dx + t * 6 * self.dz + noise1(t * 0.1 + self.dph, 5) * 30 * self.dz) % self.W
            ys = (self.dy - t * 3.5 * self.dz + noise1(t * 0.1 + self.dph, 6) * 30 * self.dz) % self.H
            al = (0.10 + 0.20 * self.dz) * (0.6 + 0.4 * np.sin(t * 0.7 + self.dph)) * dust
            p.dots(xs, ys, self.dr * 2.2, A(St.TEXT, 1.0), a=al * 0.55, sprite='soft')


class PuceAtomique(Video):
    name = 'puce_atomique'
    voice = 'fr-FR-RemyMultilingualNeural'
    rate = '+0%'

    def make_scenes(self):
        return [Intro(), Echelle(), Silicium(), Dopage(), Transistor(), Electrons(), Portes(), Horloge(),
                Chaleur(), Quantique(), Finale()]

    def prepare(self, tts=True):
        super().prepare(tts)
        self.backdrop = Backdrop(self.W, self.H)
        return self

    def background(self, p, t, act):
        energy, dust, wsum = 0.0, 0.0, 0.0
        tint = St.BLUE
        for sc, S in act:
            w = max(1e-3, 1 - S.exit) * min(1.0, S.enter + 1e-3)
            energy += getattr(sc, 'bg_energy', 1.0) * w
            dust += getattr(sc, 'bg_dust', 1.0) * w
            wsum += w
        if wsum > 0:
            energy /= wsum
            dust /= wsum
        if act:
            tint = getattr(act[-1][0], 'bg_tint', St.BLUE)
        self.backdrop.draw(p, t, energy, tint, dust)

    def overlay(self, p, t, act):
        # Repères de cadre discrets (viseur).
        m, L = 46, 16
        c = A(St.TEXT2, 0.22)
        for x, y, sx, sy in ((m, m, 1, 1), (self.W - m, m, -1, 1), (m, self.H - m, 1, -1),
                             (self.W - m, self.H - m, -1, -1)):
            p.poly([(x, y + sy * L), (x, y), (x + sx * L, y)], stroke=c, w=1.2, cap='square')
        # Indicateur de chapitre.
        for sc, S in act:
            if not sc.chapter:
                continue
            num, title = sc.chapter
            a = getattr(S, 'alpha', 1.0) * prog(S.t, 2.9, 0.6, E.out_cubic)
            if a <= 0.01:
                continue
            with p.fade(a):
                p.text(num, 84, 92, size=15, family='mono', weight=500, color=St.CYAN, tracking=0.2, glow=0.4)
                p.line(116, 87, 116 + 26 * a, 87, A(St.TEXT2, 0.6), w=1.2)
                p.text(title, 152, 92, size=15, family='grotesk', weight=500, color=St.TEXT2, tracking=0.22,
                       upper=True)


def make():
    return PuceAtomique()
