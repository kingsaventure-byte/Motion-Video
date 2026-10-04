"""02 — Le silicium : l'atome, ses 4 électrons de valence, les liaisons, le cristal."""
import math

import numpy as np

from engine import ease as E
from engine.anim import clamp, lerp, prog, smoothstep
from engine.camera import Cam3D
from engine.color import alpha as A, mix
from engine.timeline import Scene

from .. import script as SC
from .. import style as St
from .. import kit as K
from ..lattice import Lattice


def _diamond(n=3):
    """Atomes et liaisons d'un cristal de type diamant (n x n x n mailles, a = 1)."""
    basis = [(0, 0, 0), (0, .5, .5), (.5, 0, .5), (.5, .5, 0)]
    pts = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for b in basis:
                    for off in ((0, 0, 0), (.25, .25, .25)):
                        pts.append((i + b[0] + off[0], j + b[1] + off[1], k + b[2] + off[2]))
    P = np.array(pts) - n / 2
    d = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    ii, jj = np.nonzero((d > 0.3) & (d < 0.45))
    bonds = [(a, b) for a, b in zip(ii, jj) if a < b]
    return P, bonds


class Silicium(Scene):
    id = 'silicium'
    chapter = ("02", "Le silicium")
    lead = 2.4
    tail = 0.9
    trans = 1.0

    def lines(self):
        return SC.SILICIUM

    def setup(self):
        self.lat = Lattice(15, 9, 200.0)
        self.dP, self.dB = _diamond(3)

    def draw(self, p, S):
        t = S.t
        K.chapter_card(p, S, '02', 'Le silicium')
        c = dict(si=S.w('s1', 'silicium'), atome=S.w('s2', 'atome'), q14=S.w('s2', 'quatorze'),
                 quatre=S.w('s2', 'quatre'), couche=S.w('s2', 'couche'), partage=S.w('s3', 'partage'),
                 voisins=S.w('s3', 'voisins'), chaque=S.w('s3', 'Chaque'), paire=S.w('s3', 'paire'),
                 repete=S.w('s4', 'Répété'), cristal=S.w('s4', 'cristal'), dans=S.w('s5', 'Dans'),
                 prison=S.w('s5', 'prisonnier'), mal=S.w('s5', 'mal'), decider=S.w('s6', 'décider'),
                 ou=S.w('s6', 'où'))

        # ---------------- tuile du tableau périodique -----------------------
        a_tile = prog(t, 2.5, 0.6) * (1 - prog(t, c['partage'] - 0.3, 0.6))
        if a_tile > 0:
            k = prog(t, c['atome'] - 0.2, 1.0, E.in_out_cubic)
            cx, cy = lerp(960, 420, k), 540
            sc = lerp(1.0, 0.72, k) * (0.9 + 0.1 * E.out_back(clamp((t - 2.5) / 0.7)))
            with p.fade(a_tile), p.push():
                p.translate(cx, cy)
                p.scale_(sc)
                w = 300
                p.rect(-w / 2, -w / 2, w, w, fill=A(St.BG_IN, 0.85), r=22)
                p.rect(-w / 2, -w / 2, w, w, stroke=A(St.CYAN, 0.9), sw=2, r=22, glow=0.7)
                p.text('14', -w / 2 + 26, -w / 2 + 50, size=34, family='mono', weight=500, color=St.CYAN, glow=0.4)
                p.text('Si', 0, 40, size=150, family='display', weight=700, color=St.TEXT, align='center', glow=0.15)
                p.text('Silicium', 0, 100, size=26, family='sans', weight=400, color=St.TEXT2, align='center')
                p.text('28,085', 0, 132, size=18, family='mono', color=St.TEXT3, align='center')

        # ---------------- atome de Bohr ---------------------------------------
        a_bohr = prog(t, c['atome'], 0.8) * (1 - prog(t, c['partage'] - 0.2, 0.7))
        if a_bohr > 0:
            k = prog(t, c['partage'] - 0.4, 1.0, E.in_out_cubic)
            bx = lerp(1180, 960, k)
            K.bohr(p, bx, 540, t * 1.2, a=a_bohr, inner_dim=prog(t, c['quatre'], 0.6),
                   outer_hot=prog(t, c['quatre'], 0.6), scale=lerp(1.0, 0.5, k))
            K.label(p, 1480, 300, '14 électrons', t - c['q14'], ax=1180 + 90, ay=540 - 110, a=a_bohr,
                    sub='2 + 8 + 4')
            K.label(p, 1480, 800, 'Couche externe', t - c['couche'], ax=1180 + 150, ay=540 + 140, a=a_bohr,
                    sub='4 électrons de valence', color=St.CYAN)

        # ---------------- liaisons : l'atome et ses 4 voisins ----------------
        lat = self.lat
        tz = c['repete']
        zoom = lerp(1.0, 0.42, prog(t, tz - 0.2, 2.4, E.in_out_cubic))
        a_3d = prog(t, c['cristal'] - 0.6, 0.8) * (1 - prog(t, c['dans'] - 0.2, 0.8))
        zoom = lerp(zoom, 0.78, prog(t, c['dans'] - 0.3, 1.6, E.in_out_cubic))
        a_lat = prog(t, c['partage'] - 0.2, 0.6) * (1 - a_3d)
        if a_lat > 0.01:
            n = len(lat.ij)
            reveal = np.zeros(n)
            for k, (i, j) in enumerate(lat.ij):
                if (i, j) == (0, 0):
                    reveal[k] = 1.0
                elif abs(i) + abs(j) == 1:
                    reveal[k] = prog(t, c['voisins'] - 0.5 + 0.1 * (k % 4), 0.7, E.snap)
                else:
                    d = math.hypot(i, j)
                    reveal[k] = prog(t, tz + 0.2 + d * 0.18, 0.6)
            with p.fade(a_lat), p.camera(0, 0, zoom):
                # arrivée des voisins : glissement
                P = lat.draw(p, t, amp=2.2, reveal=reveal, labels=zoom > 0.6,
                             e_a=prog(t, c['voisins'] + 0.2, 0.8), bond_a=prog(t, c['voisins'] + 0.1, 0.8),
                             e_jitter=1.5 + 4.0 * prog(t, c['mal'] - 0.6, 0.5) * (1 - prog(t, c['mal'] + 1.6, 0.6)))
                # liaison mise en évidence
                q = lat.bond((0, 0), (1, 0))
                hl = prog(t, c['chaque'], 0.5) * (1 - prog(t, c['repete'] - 0.3, 0.5))
                if hl > 0:
                    x1, y1 = lat.slot(P, q, 0)
                    x2, y2 = lat.slot(P, q, 1)
                    p.rect(x1 - 26, y1 - 30, x2 - x1 + 52, 60, stroke=St.CYAN, sw=2, r=30, a=hl, glow=0.8)
            if hl > 0:
                K.label(p, 1270, 330, 'Liaison covalente', t - c['paire'] + 0.3, ax=960 + 100 * zoom, ay=540 - 32,
                        sub="= 2 électrons partagés", a=hl)

            # les 4 électrons de valence avant la formation des liaisons
            a_v = prog(t, c['partage'], 0.5) * (1 - prog(t, c['voisins'] + 0.2, 0.6))
            if a_v > 0:
                ang = t * 0.8
                xs = [960 + math.cos(ang + k * math.pi / 2) * 62 * zoom for k in range(4)]
                ys = [540 + math.sin(ang + k * math.pi / 2) * 62 * zoom for k in range(4)]
                K.electrons(p, np.array(xs), np.array(ys), r=7, a=a_v * a_lat, k=1.0)

        # ---------------- cristal 3D -----------------------------------------
        if a_3d > 0.01:
            self._crystal(p, t, c, a_3d)

        # ---------------- isolant : le champ ne fait presque rien ------------
        a_e = prog(t, c['mal'] - 0.8, 0.5) * (1 - prog(t, c['decider'] - 0.5, 0.6))
        if a_e > 0:
            for k in range(3):
                y = 260 + k * 280
                K.arrow(p, 200, y, 1720, y, St.VIOLET, w=3.5, head=20, pr=prog(t, c['mal'] - 0.8 + k * 0.1, 0.9,
                        E.snap), a=a_e, glow=0.4)
            p.text('CHAMP ÉLECTRIQUE', 200, 230, size=16, family='grotesk', weight=500, color=St.VIOLET,
                   tracking=0.2, a=a_e)
            K.readout(p, 1720, 880, 'Courant', '≈ 0', t - c['mal'], align='right', a=a_e, color=St.TEXT)
        K.keyword(p, 'Silicium pur = isolant', t - c['prison'] - 0.3, hold=3.2, size=52, color=St.TEXT,
                  sub="(ou presque : un semi-conducteur)")

        # ---------------- « où et quand il conduira » -------------------------
        a_d = prog(t, c['decider'], 0.6)
        if a_d > 0:
            with p.camera(0, 0, zoom):
                P = lat.positions(t, 2.2)
                pts = [lat.atom(i, 0) for i in range(-4, 5)]
                pulse = 0.5 + 0.5 * math.sin((t - c['ou']) * 6) if t > c['ou'] else 0.0
                for k, idx in enumerate(pts):
                    pr = prog(t, c['decider'] + k * 0.08, 0.5, E.snap)
                    p.circle(P[idx, 0], P[idx, 1], 52, stroke=St.CYAN, w=2.2, a=pr * (0.5 + 0.5 * pulse) * a_d,
                             glow=0.9)
                if t > c['ou']:
                    x0, x1 = P[pts[0], 0], P[pts[-1], 0]
                    pr = prog(t, c['ou'], 0.9, E.in_out_cubic)
                    p.line(x0, 0, lerp(x0, x1, pr), 0, St.CYAN, w=6, a=0.8 * a_d, glow=1.2)

    def _crystal(self, p, t, c, a):
        yaw = 20 + (t - c['cristal']) * 14
        cam = Cam3D.orbit(target=(0, 0, 0), dist=8.6, yaw=yaw, pitch=22, fov=38)
        sx, sy, z, s = cam.project(self.dP)
        with p.fade(a):
            for i, j in self.dB:
                dep = (z[i] + z[j]) / 2
                fa = float(np.clip(1.25 - (dep - 4.2) / 3.5, 0.15, 1))
                p.line(sx[i], sy[i], sx[j], sy[j], A(St.SI, 0.5), w=2.2 * fa, a=fa)
            order = np.argsort(-z)
            fa = np.clip(1.25 - (z[order] - 4.2) / 3.5, 0.15, 1)
            p.spheres(sx[order], sy[order], 0.085 * s[order], St.SI, a=fa, glow=0.15)
        K.label(p, 1420, 300, 'Cristal de silicium', t - c['cristal'] + 0.1, a=a, sub='structure de type diamant')
        K.label(p, 1420, 820, 'Maille', t - c['cristal'] - 0.5, a=a, sub='a = 0,543 nm')
