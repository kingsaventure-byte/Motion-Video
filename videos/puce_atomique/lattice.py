"""Réseau cristallin 2D de silicium (représentation « manuel » : 4 liaisons, 2 électrons par liaison)."""
import math

import numpy as np

from engine.color import alpha as A, mix
from engine.noise import noise1
from . import style as St
from . import kit as K


class Lattice:
    def __init__(self, nx=15, ny=9, D=200.0):
        self.D = D
        self.nx, self.ny = nx, ny
        ii, jj = np.meshgrid(np.arange(nx) - nx // 2, np.arange(ny) - ny // 2)
        self.ij = list(zip(ii.ravel().tolist(), jj.ravel().tolist()))
        self.index = {ij: k for k, ij in enumerate(self.ij)}
        self.pos = np.array([(i * D, j * D) for i, j in self.ij], np.float64)
        self.ph = np.arange(len(self.ij)) * 1.618
        bonds = []
        for (i, j), k in self.index.items():
            for di, dj in ((1, 0), (0, 1)):
                n = self.index.get((i + di, j + dj))
                if n is not None:
                    bonds.append((k, n))
        self.bonds = bonds
        self.bindex = {(min(a, b), max(a, b)): q for q, (a, b) in enumerate(bonds)}

    def atom(self, i, j):
        return self.index[(i, j)]

    def bond(self, ij1, ij2):
        a, b = self.index[ij1], self.index[ij2]
        return self.bindex[(min(a, b), max(a, b))]

    def positions(self, t, amp=2.0, speed=1.0):
        if amp <= 0:
            return self.pos.copy()
        dx = noise1(t * 1.7 * speed + self.ph, 31) * amp
        dy = noise1(t * 1.7 * speed + self.ph, 57) * amp
        return self.pos + np.stack([dx, dy], axis=1)

    def slot(self, P, q, s):
        """Position de l'électron s (0/1) de la liaison q."""
        a, b = self.bonds[q]
        f = 0.38 if s == 0 else 0.62
        return P[a] * (1 - f) + P[b] * f

    def draw(self, p, t, a=1.0, amp=2.0, speed=1.0, atom_r=34.0, colors=None, labels=True, bond_a=1.0,
             e_a=1.0, hidden=(), e_jitter=1.5, reveal=None, e_color=None, bond_color=None, glow=0.5):
        """colors : {index atome: couleur}. hidden : {(liaison, slot)} électrons absents.
        reveal : tableau d'alphas par atome (apparition)."""
        P = self.positions(t, amp, speed)
        n = len(P)
        ra = np.ones(n) * a if reveal is None else np.asarray(reveal) * a
        bc = bond_color or A(St.SI, 0.55)
        # liaisons
        if bond_a > 0:
            for q, (i, j) in enumerate(self.bonds):
                al = min(ra[i], ra[j]) * bond_a
                if al <= 0.01:
                    continue
                (x1, y1), (x2, y2) = P[i], P[j]
                ang = math.atan2(y2 - y1, x2 - x1)
                ox, oy = -math.sin(ang) * 4.5, math.cos(ang) * 4.5
                cx1, cy1 = x1 + math.cos(ang) * atom_r, y1 + math.sin(ang) * atom_r
                cx2, cy2 = x2 - math.cos(ang) * atom_r, y2 - math.sin(ang) * atom_r
                p.line(cx1 + ox, cy1 + oy, cx2 + ox, cy2 + oy, bc, w=1.6, a=al)
                p.line(cx1 - ox, cy1 - oy, cx2 - ox, cy2 - oy, bc, w=1.6, a=al)
        # électrons de liaison
        if e_a > 0:
            xs, ys, als = [], [], []
            for q, (i, j) in enumerate(self.bonds):
                al = min(ra[i], ra[j]) * e_a
                if al <= 0.01:
                    continue
                for s in (0, 1):
                    if (q, s) in hidden:
                        continue
                    x, y = self.slot(P, q, s)
                    jx = noise1(t * 3.1 + q * 0.37 + s * 5.1, 71) * e_jitter
                    jy = noise1(t * 3.1 + q * 0.53 + s * 2.3, 73) * e_jitter
                    xs.append(x + jx)
                    ys.append(y + jy)
                    als.append(al)
            if xs:
                K.electrons(p, np.array(xs), np.array(ys), r=6.5, a=np.array(als), k=glow)
        # atomes
        cols = [colors.get(k, St.SI) if colors else St.SI for k in range(n)]
        m = ra > 0.01
        if m.any():
            idx = np.nonzero(m)[0]
            p.spheres(P[idx, 0], P[idx, 1], atom_r, [cols[k] for k in idx], a=ra[idx], glow=0.12)
            if labels:
                for k in idx:
                    lab = 'Si'
                    if colors and k in colors:
                        lab = getattr(self, 'names', {}).get(k, 'Si')
                    p.text(lab, P[k, 0], P[k, 1] + 8, size=22, family='grotesk', weight=600,
                           color=A(St.BG_OUT, 0.75), align='center', a=ra[k])
        return P
