"""03 — Le dopage : phosphore (électron libre, type N) et bore (trou mobile, type P)."""
import math

import numpy as np
import skia

from engine import ease as E
from engine.anim import clamp, lerp, prog
from engine.color import alpha as A, mix
from engine.noise import noise1, rng
from engine.painter import make_path, point_on
from engine.timeline import Scene

from .. import script as SC
from .. import style as St
from .. import kit as K
from ..lattice import Lattice

D = 200.0


class Dopage(Scene):
    id = 'dopage'
    chapter = ("03", "Le dopage")
    lead = 2.4
    tail = 0.9
    trans = 1.0

    def lines(self):
        return SC.DOPAGE

    def setup(self):
        self.lat = Lattice(25, 11, D)
        lat = self.lat
        self.P_idx = lat.atom(0, 0)
        self.B_idx = lat.atom(5, 0)
        lat.names = {self.P_idx: 'P', self.B_idx: 'B'}
        # trajectoire de l'électron libéré : marche dans les interstices
        g = rng(8)
        pts = [(0.0, 0.0), (0.5 * D, -0.5 * D)]
        i, j = 0.5, -0.5
        for _ in range(14):
            di, dj = [(1, 0), (0, 1), (0, -1), (-1, 0), (1, 0)][int(g.integers(0, 5))]
            if abs(j + dj) > 3:
                dj = -dj
            i += di
            j += dj
            pts.append((i * D + g.uniform(-30, 30), j * D + g.uniform(-30, 30)))
        self.walk = make_path(pts, smooth=True)
        # chaîne de liaisons pour le déplacement du trou (vers la gauche)
        b = lat.bond
        self.hchain = [(b((5, 0), (6, 0)), 0), (b((4, 0), (5, 0)), 1), (b((3, 0), (4, 0)), 1),
                       (b((2, 0), (3, 0)), 1), (b((1, 0), (2, 0)), 1)]
        # champ lointain : image pré-calculée de milliers d'atomes
        H, W = 1080, 1920
        img = np.zeros((H, W, 4), np.uint8)
        yy, xx = np.mgrid[0:H, 0:W]
        m = ((xx % 9) < 2) & ((yy % 9) < 2)
        img[m] = (105, 125, 175, 255)
        self.field = skia.Image.fromarray(img, colorType=skia.kRGBA_8888_ColorType)
        self.dopants = [(g.uniform(80, 1840), g.uniform(80, 1000), g.random() < 0.5) for _ in range(9)]

    def draw(self, p, S):
        t = S.t
        lat = self.lat
        K.chapter_card(p, S, '03', 'Le dopage')
        c = dict(etr=S.w('d1', 'étrangers'), dopage=S.w('d1', 'dopage'), phos=S.w('d2', 'phosphore'),
                 cinq=S.w('d2', 'cinq'), cinquieme=S.w('d2', 'cinquième'), libere=S.w('d3', 'libère'),
                 errer=S.w('d3', 'errer'), negative=S.w('d3', 'négative'), typeN=S.w('d3', 'type'),
                 inverse=S.w('d4', "l'inverse"), bore=S.w('d4', 'bore'), trois=S.w('d4', 'trois'),
                 trou=S.w('d4', 'trou'), manque=S.w('d4', 'manque'), combler=S.w('d5', 'combler'), derriere=S.w('d5', 'derrière'),
                 deplace=S.w('d5', 'déplace'), positive=S.w('d5', 'positive'), typeP=S.w('d5', 'type'),
                 suffit=S.w('d6', 'suffit'), millions=S.w('d6', 'millions'))

        # caméra
        pan = prog(t, c['inverse'] - 0.2, 1.4, E.in_out_cubic)
        pan2 = prog(t, c['combler'], 6.0, E.in_out_sine)
        cx = lerp(0, 5 * D, pan) - 2.0 * D * pan2
        zoom = lerp(0.8, 1.0, prog(t, c['phos'] - 0.5, 1.5, E.in_out_cubic))
        zoom = lerp(zoom, 0.85, prog(t, c['libere'] + 0.5, 2.0, E.in_out_cubic))
        out = prog(t, c['suffit'] - 0.2, 2.2, E.in_out_cubic)
        zoom = zoom * lerp(1.0, 0.18, out)
        a_lat = 1 - prog(t, c['suffit'] + 0.6, 1.0)

        # états
        colors, hidden = {}, set()
        kP = prog(t, c['phos'] - 0.1, 0.6)
        if kP > 0:
            colors[self.P_idx] = mix(St.SI, St.PHOS, kP)
        kB = prog(t, c['bore'] - 0.1, 0.6)
        if kB > 0:
            colors[self.B_idx] = mix(St.SI, St.BORON, kB)
        hops = [c['combler'], c['derriere'] - 0.2, c['deplace'], c['deplace'] + 0.75]
        hole_k = 0
        flying = None
        if kB > 0.5:
            for k, th in enumerate(hops):
                if t >= th + 0.7:
                    hole_k = k + 1
                elif t >= th:
                    flying = (k, (t - th) / 0.7)
                    break
            hidden.add(self.hchain[hole_k])
            if flying is not None:
                hidden.add(self.hchain[flying[0] + 1])

        if a_lat > 0.01:
            with p.fade(a_lat), p.camera(cx, 0, zoom):
                P = lat.draw(p, t, amp=2.2, colors=colors, labels=zoom > 0.5, hidden=hidden,
                             e_a=1.0, glow=0.45)
                # ---- phosphore : 5e électron puis libération
                if kP > 0:
                    px, py = P[self.P_idx]
                    a5 = prog(t, c['cinquieme'] - 0.3, 0.5) * (1 - prog(t, c['typeN'] + 2.2, 0.8))
                    if a5 > 0:
                        tf = t - c['libere']
                        if tf < 0:
                            ang = t * 2.6
                            ex, ey = px + math.cos(ang) * 62, py + math.sin(ang) * 62
                        else:
                            u = E.in_out_sine(clamp(tf / 6.5)) * 0.92 + 0.08 * clamp(tf / 6.5)
                            ex, ey = point_on(self.walk, min(1.0, u))
                            ex += noise1(t * 6, 3) * 6
                            ey += noise1(t * 6, 4) * 6
                            # traînée
                            n = 26
                            tr = [point_on(self.walk, max(0.0, min(1.0, E.in_out_sine(clamp((tf - k * 0.03) / 6.5)))))
                                  for k in range(n)]
                            p.poly(tr, stroke=St.CYAN, w=3, a=a5 * 0.6, glow=0.6, smooth=True)
                        K.electron(p, ex, ey, 10, a=a5, k=1.4, sign=True)
                        if tf > 0.6:
                            p.text('P^{+}', px + 40, py - 36, size=24, family='mono', weight=600, color=St.PHOS,
                                   a=prog(tf, 0.6, 0.5) * (1 - out))
                # ---- bore : trou et sauts d'électrons
                if kB > 0.5:
                    q, s_ = self.hchain[hole_k]
                    hx, hy = lat.slot(P, q, s_)
                    pulse = 0.75 + 0.25 * math.sin(t * 5)
                    ah = prog(t, c['manque'] - 0.2, 0.5)
                    K.hole(p, hx, hy, 20 * pulse + 4, a=ah, k=1.0, sign=True)
                    if flying is not None:
                        k, u = flying
                        u = E.in_out_cubic(u)
                        x0, y0 = lat.slot(P, *self.hchain[k + 1])
                        x1, y1 = lat.slot(P, *self.hchain[k])
                        ex = lerp(x0, x1, u)
                        ey = lerp(y0, y1, u) - math.sin(u * math.pi) * 60
                        K.electron(p, ex, ey, 8, k=1.2)

        # ---- étiquettes (repère écran)
        def scr(x, y):
            return 960 + (x - cx) * zoom, 540 + y * zoom
        la = a_lat * (1 - out)
        ax, ay = scr(0, -36)
        K.label(p, 300, 230, 'Phosphore · P', t - c['cinq'] + 0.2, ax=ax, ay=ay, sub='5 électrons externes',
                sub_color=St.PHOS, a=la * (1 - prog(t, c['inverse'], 0.4)))
        K.keyword(p, 'Type N', t - c['typeN'] + 0.2, color=St.CYAN, sub='porteurs : électrons libres (négatifs)',
                  hold=2.0)
        ax, ay = scr(5 * D, -36)
        K.label(p, 1480, 230, 'Bore · B', t - c['trois'] + 0.2, ax=ax, ay=ay, sub='3 électrons externes',
                sub_color=St.BORON, a=la * (1 - prog(t, c['combler'] + 1.0, 0.5)))
        K.keyword(p, 'Trou', t - c['trou'] + 0.1, color=St.AMBER, sub="une place vide, qui se comporte comme une charge +",
                  hold=1.6, size=56)
        K.keyword(p, 'Type P', t - c['typeP'] + 0.2, color=St.AMBER, sub='porteurs : trous (positifs)', hold=1.8)

        # ---- champ lointain : des millions d'atomes, quelques dopants
        af = prog(t, c['suffit'] + 0.2, 1.2)
        if af > 0:
            sc = lerp(3.0, 1.0, E.out_cubic(clamp((t - c['suffit']) / 3.0)))
            with p.fade(af):
                w, h = 1920 * sc, 1080 * sc
                p.blit(self.field, 960 - w / 2, 540 - h / 2, w, h, a=0.9)
                for k, (x, y, isP) in enumerate(self.dopants):
                    x2, y2 = 960 + (x - 960) * sc, 540 + (y - 540) * sc
                    pr = prog(t, c['millions'] - 1.0 + k * 0.12, 0.5, E.out_back)
                    col = St.PHOS if isP else St.BORON
                    p.circle(x2, y2, 5 * pr, fill=col, glow=1.4, gr=3.0)
                    p.circle(x2, y2, 16 * pr, stroke=A(col, 0.6), w=1.5, a=pr)
            p.dots([700], [540], [700], St.BG_OUT, a=0.85 * af, sprite='soft')
            K.readout(p, 960 - 300, 480, 'Dopage typique', '1 / 1 000 000', t - c['millions'] + 0.2, size=64,
                      color=St.TEXT, a=af)
            with p.fade(af * prog(t, c['millions'] + 0.6, 0.5)):
                p.text("un atome étranger pour un million d'atomes de silicium (et parfois bien plus)", 960 - 300,
                       610, size=22, family='sans', weight=400, color=St.TEXT2)
