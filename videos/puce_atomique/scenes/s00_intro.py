"""Ouverture : de l'appareil à la puce, des milliards d'interrupteurs, puis le titre."""
import math

import numpy as np

from engine import ease as E
from engine.anim import clamp, lerp, prog
from engine.color import alpha as A, mix
from engine.noise import rng
from engine.painter import make_path, point_on
from engine.timeline import Scene

from .. import script as SC
from .. import style as St
from .. import kit as K

GRID = 24.0


class Intro(Scene):
    id = 'intro'
    lead = 1.2
    tail = 0.9
    trans = 1.2

    def lines(self):
        return SC.INTRO

    def setup(self):
        g = rng(5)
        nx, ny = int(1920 / GRID) + 3, int(1080 / GRID) + 3
        xs, ys = np.meshgrid(np.arange(nx), np.arange(ny))
        self.gx = (xs.ravel() - nx / 2) * GRID
        self.gy = (ys.ravel() - ny / 2) * GRID
        self.gd = np.hypot(self.gx, self.gy * 1.2)
        self.gph = g.uniform(0, 1, self.gx.size)
        self.gseed = g.integers(0, 1 << 30, self.gx.size)
        # Pistes de circuit (Manhattan) pour les flux d'électrons.
        self.paths = []
        for k in range(70):
            x = g.integers(-38, 38) * GRID
            y = g.integers(-21, 21) * GRID
            pts = [(x, y)]
            horiz = bool(g.integers(0, 2))
            for _ in range(g.integers(4, 9)):
                L = g.integers(3, 14) * GRID * (1 if g.random() < 0.5 else -1)
                if horiz:
                    x += L
                else:
                    y += L
                pts.append((x, y))
                horiz = not horiz
            length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            self.paths.append((make_path(pts), length, g.uniform(0, 2.0), g.uniform(700, 1300),
                               g.uniform(0.7, 1.0)))

    def draw(self, p, S):
        t = S.t
        cx, cy = 960, 540
        t_dev = S.w('i1', 'dans')
        t_zoom = S.w('i1', 'dizaines') - 0.5
        t_on = S.w('i1', "s'allument")
        t_fast = S.w('i1', 'milliards', n=1)
        t_freeze = S.w('i2', 'Rien')
        t_move = S.w('i3', 'tout')
        t_title = S.w('i4', 'Plongeons')
        t_sub = S.w('i4', 'comprendre')

        # ---------------- 1. point de lumière initial -------------------------
        Z = lerp(1.0, 34.0, prog(t, t_zoom, 1.9, E.in_out_expo))
        a_point = prog(t, 0.25, 0.9, E.out_cubic) * (1 - prog(t, t_zoom + 0.8, 0.6))
        if a_point > 0:
            pulse = 0.75 + 0.25 * math.sin(t * 3.2)
            r = 4.5 * (1 + 0.6 * prog(t, 1.25, 0.6, E.out_back))
            with p.camera(cx, cy, Z):
                p.glow_dot(cx, cy, r, St.CYAN_HOT, k=1.3 * pulse, a=a_point)
            # onde annulaire sur « En ce moment »
            for k in range(2):
                tr = t - 1.25 - k * 0.35
                if 0 < tr < 1.6:
                    pr = E.out_cubic(tr / 1.6)
                    p.circle(cx, cy, 10 + 220 * pr, stroke=St.CYAN, w=1.5, a=(1 - pr) * 0.6 * a_point, glow=0.4)

        # ---------------- 2. silhouette de l'appareil (dessin au trait) ------
        a_dev = prog(t, t_dev, 0.5) * (1 - prog(t, t_zoom + 0.4, 0.7))
        if a_dev > 0:
            with p.camera(cx, cy, Z):
                w, h = 330, 680
                path = make_path([])
                import skia
                path = skia.Path()
                path.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h), 52, 52))
                tr = prog(t, t_dev, 1.6, E.in_out_cubic)
                p.path(path, stroke=A(St.TEXT2, 0.75), w=2.0 / max(1.0, Z ** 0.5), a=a_dev, trim=(0, tr), glow=0.25)
                p.line(cx - 34, cy - h / 2 + 22, cx + 34, cy - h / 2 + 22, A(St.TEXT2, 0.5), w=4, a=a_dev * tr)
                # la puce au centre
                pc = prog(t, t_dev + 0.9, 0.8, E.snap)
                cs = 64 * pc
                p.rect(cx - cs / 2, cy - cs / 2, cs, cs, fill=A(St.SI_DARK, 0.9), r=5, a=a_dev)
                p.rect(cx - cs / 2, cy - cs / 2, cs, cs, stroke=St.CYAN, sw=1.4, r=5, a=a_dev, glow=0.6)
                for i in range(6):  # broches
                    o = -cs / 2 + (i + 0.5) * cs / 6
                    for sx in (-1, 1):
                        p.line(cx + sx * cs / 2, cy + o, cx + sx * (cs / 2 + 7 * pc), cy + o, A(St.GOLD, 0.8), w=1.5,
                               a=a_dev)
                        p.line(cx + o, cy + sx * cs / 2, cx + o, cy + sx * (cs / 2 + 7 * pc), A(St.GOLD, 0.8), w=1.5,
                               a=a_dev)
                # pastille d'interface « vous »
            K.label(p, cx + 210, cy - 250, "Votre appareil", t - t_dev - 0.6, ax=cx + 165, ay=cy - 300,
                    a=1 - prog(t, t_zoom, 0.4))
            K.label(p, cx + 120, cy + 120, "Le processeur", t - t_dev - 1.4, ax=cx + 34, ay=cy + 30,
                    sub='~ 1 cm²', a=1 - prog(t, t_zoom, 0.4))

        # ---------------- 3. la grille d'interrupteurs ------------------------
        a_grid = prog(t, t_zoom + 0.9, 0.9, E.out_cubic)
        if a_grid > 0:
            self._grid(p, S, a_grid, t_on, t_fast, t_freeze, t_move, t_title)

        # ---------------- 4. compteurs ---------------------------------------
        a_ro = 1 - prog(t, t_freeze, 0.6)
        K.readout(p, 150, 900, 'Transistors', '≈ 10^{10}', t - (S.w('i1', 'milliards') - 0.1), a=a_ro)
        K.readout(p, 1770, 900, 'Basculements', '≈ 10^{9} / s', t - (t_fast - 0.1), align='right', a=a_ro)

        # ---------------- 5. flux d'électrons --------------------------------
        a_flow = prog(t, t_move - 0.25, 0.4, E.out_cubic)
        if a_flow > 0:
            dim = 1 - 0.55 * prog(t, t_title, 1.2)
            self._flows(p, t - (t_move - 0.25), a_flow * dim)

        # ---------------- 6. titre ---------------------------------------------
        tt = t - t_title
        if tt > 0:
            # voile sombre derrière le titre
            p.dots([cx], [cy], [900], St.BG_OUT, a=0.75 * prog(tt, 0, 1.0), sprite='soft')
            p.text_reveal("Au cœur du silicium", cx, cy + 20, tt, size=118, family='display', weight=700,
                          color=St.TEXT, align='center', tracking=-0.02, gap=0.045, dur=0.9, glow=0.18)
            w = 260 * prog(tt, 0.7, 1.2, E.snap)
            p.line(cx - w, cy + 74, cx + w, cy + 74, A(St.CYAN, 0.9), w=1.5, glow=0.8)
            p.text_reveal("UNE PLONGÉE À L'ÉCHELLE DES ATOMES", cx, cy - 110, tt - 0.4, size=18, family='mono',
                          weight=500, color=St.CYAN, align='center', tracking=0.32, gap=0.02, glow=0.5)
        ts = t - t_sub
        if ts > 0:
            p.text_reveal("Ce qui se passe vraiment quand une puce calcule", cx, cy + 136, ts, size=32,
                          family='sans', weight=300, color=St.TEXT2, align='center', tracking=0.0, gap=0.018)

    # -------------------------------------------------------------------------
    def _grid(self, p, S, a, t_on, t_fast, t_freeze, t_move, t_title):
        t = S.t
        cx, cy = 960, 540
        # échelle : la grille « sort » de la puce puis recule légèrement au gel
        zoom_in = lerp(0.35, 1.0, prog(t, t_on - 1.6, 1.6, E.out_cubic))
        recede = lerp(1.0, 0.86, prog(t, t_freeze, 6.0, E.in_out_sine))
        push = lerp(1.0, 1.25, prog(t, t_title + 3.2, 3.5, E.in_cubic))
        z = zoom_in * recede * push
        xs = cx + self.gx * z
        ys = cy + self.gy * z
        # vague d'apparition depuis le centre
        R = 1300 * prog(t, t_on - 1.4, 1.8, E.out_cubic)
        vis = np.clip((R - self.gd * z) / 120.0, 0, 1)
        front = np.exp(-((R - self.gd * z) / 60.0) ** 2) * (R < 1250)
        # clignotement : fréquence croissante, figée au « Rien ne bouge »
        tf = min(t, t_freeze)
        rate = 2.0 + 16.0 * prog(tf, t_on, (t_fast - t_on) + 1.0, E.in_cubic)
        phase = tf * rate + self.gph * 7
        on = ((self.gseed + np.floor(phase).astype(np.int64) * 2654435761) % 1000) < 380
        flick = prog(t, t_on, 0.4)
        frozen = prog(t, t_freeze, 0.5)
        lvl_on = (1 - frozen) * flick
        # figé : le motif reste visible, éteint de toute lumière (immobilité)
        b = 0.42 + 0.8 * on * lvl_on + 0.35 * on * frozen + front * 0.9
        b = b * vis * a
        title_dim = 1 - 0.6 * prog(t, t_title, 1.2)
        b = b * title_dim
        m = b > 0.01
        if not m.any():
            return
        col_on = St.CYAN
        p.dots(xs[m], ys[m], 2.1 * z, mix(St.SI, St.CYAN_HOT, 0.25), a=b[m] * 0.55, sprite='disk')
        hot = m & on & (lvl_on > 0.01)
        if hot.any():
            p.dots(xs[hot], ys[hot], 2.4 * z, col_on, a=(b[hot] * lvl_on), sprite='disk', glow=0.9, gr=4.5)
        fr = m & (front > 0.05)
        if fr.any():
            p.dots(xs[fr], ys[fr], 2.6 * z, St.CYAN_HOT, a=front[fr] * a, main=False, glow=0.8, gr=4)

    def _flows(self, p, tl, a):
        cx, cy = 960, 540
        for path, length, delay, speed, br in self.paths:
            tt = tl - delay * 0.6
            if tt <= 0:
                continue
            period = (length + 600) / speed
            u = (tt % period) * speed  # px parcourus
            head = u / length
            tail_len = 260.0 / length
            with p.push():
                p.translate(cx, cy)
                for k, (f0, al) in enumerate(((1.0, 0.18), (0.6, 0.35), (0.3, 0.7))):
                    t0 = head - tail_len * f0
                    p.path(path, stroke=St.CYAN, w=1.6 + k * 0.4, a=a * al * br, trim=(max(0, t0), min(1, head)),
                           glow=0.7 * br, cap='butt')
                if 0 <= head <= 1:
                    m = point_on(path, head)
                    if m is not None:
                        K.electron(p, m[0], m[1], 3.4, a=a * br, k=1.1)


