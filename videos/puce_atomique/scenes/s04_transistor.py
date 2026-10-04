"""04 — Le transistor : coupe d'un MOSFET, barrière d'énergie, canal, bit."""
import math

import numpy as np

from engine import ease as E
from engine.anim import clamp, lerp, prog
from engine.color import alpha as A, mix, hex2
from engine.noise import noise1, rng
from engine.painter import lin
from engine.timeline import Scene

from .. import script as SC
from .. import style as St
from .. import kit as K

# Géométrie (repère écran)
SUB = (250, 560, 1670, 960)          # substrat P
SRC = (290, 560, 650, 735)           # source N+
DRN = (1270, 560, 1630, 735)         # drain N+
OXY = (640, 528, 1280, 560)          # oxyde de grille
GATE = (650, 405, 1270, 528)         # grille
CH_X0, CH_X1 = 650, 1270


class Transistor(Scene):
    id = 'transistor'
    chapter = ("04", "Le transistor")
    lead = 2.4
    tail = 1.0
    trans = 1.0

    def lines(self):
        return SC.TRANSISTOR

    def setup(self):
        g = rng(44)
        # trous dans la zone P (hors puits)
        hx, hy = [], []
        while len(hx) < 150:
            x, y = g.uniform(SUB[0] + 15, SUB[2] - 15), g.uniform(SUB[1] + 12, SUB[3] - 15)
            if (SRC[0] - 10 < x < SRC[2] + 10 or DRN[0] - 10 < x < DRN[2] + 10) and y < SRC[3] + 12:
                continue
            hx.append(x)
            hy.append(y)
        self.hx, self.hy = np.array(hx), np.array(hy)
        self.hph = g.uniform(0, 100, len(hx))
        # électrons dans les puits N+
        ex, ey = [], []
        for R in (SRC, DRN):
            for _ in range(120):
                ex.append(g.uniform(R[0] + 14, R[2] - 14))
                ey.append(g.uniform(R[1] + 12, R[3] - 12))
        self.ex, self.ey = np.array(ex), np.array(ey)
        self.eph = g.uniform(0, 100, len(ex))
        # électrons du canal
        n = 80
        self.cx0 = g.uniform(CH_X0, CH_X1, n)
        self.cy0 = g.uniform(562, 584, n)
        self.cth = g.uniform(0, 1, n)
        self.cph = g.uniform(0, 100, n)
        self._phase = None

    # --------------------------------------------------------------- états
    def _cues(self, S):
        w = S.w
        return dict(construit=w('t1', 'construit'), brique=w('t1', 'brique'), transistor=w('t1', 'transistor'),
                    libres=w('t2', 'électrons'), source=w('t2', 'source'), drain=w('t2', 'drain'),
                    typeP=w('t2', 'type'), grille=w('t3', 'grille'), oxyde=w('t3', "d'oxyde"),
                    atomes=w('t3', 'atomes'), repos=w('t4', 'repos'), barriere=w('t4', 'barrière'),
                    bloque=w('t4', 'bloqué'), zero=w('t4', 'zéro'), tension=w('t5', 'tension'),
                    volt=w('t5', 'volt'), champ=w('t5', 'champ'), repousse=w('t5', 'repousse'),
                    attire=w('t5', 'attire'), canal=w('t6', 'canal'), abaisse=w('t6', "s'abaisse"),
                    engouffrent=w('t6', "s'engouffrent"), passe=w('t6', 'passe'), un=w('t6', 'un', n=1),
                    coupez=w('t7', 'Coupez'), disparait=w('t7', 'disparaît'), z1=w('t7', 'Zéro'),
                    u1=w('t7', 'Un'), z2=w('t7', 'Zéro', n=1), bit=w('t7', 'bit'))

    def _gate(self, t, c):
        """Commande de grille 0..1."""
        v = prog(t, c['tension'], c['volt'] - c['tension'] + 0.2, E.in_out_cubic)
        v *= 1 - prog(t, c['coupez'] + 0.3, 0.4, E.in_out_cubic)
        v += prog(t, c['u1'] - 0.05, 0.15) * (1 - prog(t, c['z2'] - 0.05, 0.15))
        return clamp(v)

    def _channel(self, t, c):
        ch = 0.35 * prog(t, c['attire'], 1.4, E.out_cubic) + 0.65 * prog(t, c['canal'] - 0.3, 0.8, E.out_cubic)
        ch *= 1 - prog(t, c['coupez'] + 0.35, 0.45, E.in_cubic)
        ch += prog(t, c['u1'] - 0.02, 0.18) * (1 - prog(t, c['z2'] - 0.02, 0.18))
        return clamp(ch)

    def _flow(self, t, c):
        f = prog(t, c['engouffrent'] - 0.4, 0.8)
        f *= 1 - prog(t, c['coupez'] + 0.3, 0.4)
        f += prog(t, c['u1'], 0.2) * (1 - prog(t, c['z2'], 0.15))
        return clamp(f)

    def _flow_phase(self, t, c):
        if self._phase is None:
            ts = np.arange(0, 80, 1 / 60)
            fl = np.array([self._flow(x, c) for x in ts])
            self._phase = (ts, np.cumsum(fl) / 60)
        ts, ph = self._phase
        return float(np.interp(t, ts, ph))

    # ----------------------------------------------------------------- rendu
    def draw(self, p, S):
        t = S.t
        c = self._cues(S)
        K.chapter_card(p, S, '04', 'Le transistor')
        gate = self._gate(t, c)
        ch = self._channel(t, c)
        flow = self._flow(t, c)
        push = gate * prog(t, c['repousse'] - 0.3, 1.0)
        field = gate * prog(t, c['champ'] - 0.2, 0.6)

        a_sub = prog(t, c['construit'] - 0.3, 0.8)
        a_wells = prog(t, c['transistor'] - 0.5, 0.6, E.snap)
        a_gate = prog(t, c['transistor'] - 0.2, 0.7, E.snap)

        # ---------------- substrat P ------------------------------------------
        if a_sub > 0:
            x0, y0, x1, y1 = SUB
            dy = (1 - E.snap(a_sub)) * 40
            with p.fade(a_sub):
                p.rect(x0, y0 + dy, x1 - x0, y1 - y0, shader=lin(0, y0, 0, y1, [(0, hex2('#2A1E2E')), (1, hex2('#120E1C'))]),
                       r=8)
                p.rect(x0, y0 + dy, x1 - x0, y1 - y0, stroke=A(St.AMBER, 0.35), sw=1.4, r=8)
                hl = prog(t, c['typeP'] - 0.2, 0.4) * (1 - prog(t, c['typeP'] + 1.6, 0.6))
                if hl > 0:
                    p.rect(x0, y0, x1 - x0, y1 - y0, stroke=St.AMBER, sw=2.5, r=8, a=hl, glow=0.9)
                # trous
                ha = prog(t, c['brique'] - 0.2, 1.0)
                if ha > 0:
                    jx = noise1(t * 1.4 + self.hph, 3) * 9
                    jy = noise1(t * 1.4 + self.hph, 5) * 9
                    hx = self.hx + jx
                    hy = self.hy + jy + dy
                    under = (hx > CH_X0 - 40) & (hx < CH_X1 + 40)
                    depth = hy - SUB[1]
                    shift = np.where(under & (depth < 200), (200 - depth) * 0.85 * push, 0.0)
                    hy = hy + shift
                    K.holes(p, hx, hy, 6.5, a=ha * 0.9, k=0.5)

        # ---------------- puits source / drain --------------------------------
        if a_wells > 0:
            for R, name in ((SRC, 'source'), (DRN, 'drain')):
                x0, y0, x1, y1 = R
                hl = prog(t, c[name] - 0.15, 0.3) * (1 - prog(t, c[name] + 1.5, 0.6))
                with p.fade(a_wells):
                    p.rect(x0, y0, x1 - x0, y1 - y0, fill=A(hex2('#0E2A4A'), 0.95), r=14)
                    p.rect(x0, y0, x1 - x0, y1 - y0, stroke=A(St.CYAN, 0.45 + 0.5 * hl), sw=1.6 + hl, r=14,
                           glow=0.3 + hl)
            jx = noise1(t * 1.6 + self.eph, 7) * 8
            jy = noise1(t * 1.6 + self.eph, 9) * 8
            ex = np.clip(self.ex + jx, 0, 1920)
            ey = self.ey + jy
            # tentative / rebond à la barrière au repos
            bounce = prog(t, c['heurtent'] if 'heurtent' in c else c['barriere'] - 0.6, 0.1) * 0
            hot = 1 + 0.6 * prog(t, c['libres'] - 0.2, 0.3) * (1 - prog(t, c['libres'] + 1.2, 0.5))
            K.electrons(p, ex, ey, 4.3, a=a_wells * 0.85, k=0.35 * hot)
            # quelques électrons de la source viennent buter contre la barrière
            ab = prog(t, c['barriere'] - 0.6, 0.4) * (1 - prog(t, c['tension'], 0.5))
            if ab > 0:
                for k in range(5):
                    ph = ((t - c['barriere']) * 0.9 + k * 0.21) % 1.0
                    d = math.sin(ph * math.pi) * 70
                    y = 590 + k * 26
                    K.electron(p, SRC[2] - 10 + d, y, 6, a=ab, k=1.0)
                    if ph > 0.45 and ph < 0.55:
                        p.circle(SRC[2] + 64, y, 14, stroke=St.RED, w=2, a=ab * 0.8, glow=0.6)

        # ---------------- canal d'inversion -----------------------------------
        if ch > 0.01:
            y0 = 562
            p.rect(CH_X0 - 10, y0, CH_X1 - CH_X0 + 20, 26, fill=A(St.CYAN, 0.10 + 0.25 * ch), r=13,
                   glow=0.6 * ch, gcol=St.CYAN)
            ph = self._flow_phase(t, c) * 420
            xs = CH_X0 + (self.cx0 - CH_X0 + ph) % (CH_X1 - CH_X0)
            ys = self.cy0 + noise1(t * 3 + self.cph, 11) * 3
            al = np.clip((ch - self.cth * 0.9) * 5, 0, 1)
            K.electrons(p, xs, ys, 4.6, a=al, k=0.9)
            if flow > 0.05:
                for k in range(3):
                    ph2 = ((t * 1.3 + k / 3) % 1.0)
                    xx = lerp(CH_X0 - 60, CH_X1 + 40, ph2)
                    p.line(xx, 575, xx + 60, 575, St.CYAN_HOT, w=2.5, a=flow * math.sin(ph2 * math.pi), glow=1.0)

        # ---------------- oxyde + grille + contacts ---------------------------
        if a_gate > 0:
            dy = (1 - E.snap(a_gate)) * -60
            with p.fade(a_gate):
                x0, y0, x1, y1 = OXY
                p.rect(x0, y0 + dy * 0.5, x1 - x0, y1 - y0, fill=A(St.TEXT, 0.22), r=3)
                p.rect(x0, y0 + dy * 0.5, x1 - x0, y1 - y0, stroke=A(St.TEXT, 0.5), sw=1, r=3)
                x0, y0, x1, y1 = GATE
                p.rect(x0, y0 + dy, x1 - x0, y1 - y0, shader=lin(0, y0 + dy, 0, y1 + dy,
                       [(0, hex2('#4B3C9A')), (1, hex2('#2A2160'))]), r=8)
                p.rect(x0, y0 + dy, x1 - x0, y1 - y0, stroke=mix(A(St.VIOLET, 0.6), St.VIOLET, gate), sw=1.6 + gate,
                       r=8, glow=0.3 + 1.0 * gate)
                # contacts métalliques
                for R in (SRC, DRN):
                    cx = (R[0] + R[2]) / 2
                    p.rect(cx - 50, 430, 100, 130, shader=lin(cx - 50, 0, cx + 50, 0,
                           [(0, hex2('#4E5872')), (0.5, hex2('#8B95AE')), (1, hex2('#4E5872'))]), r=6)
                p.line(960, 405 + dy, 960, 300, A(St.TEXT2, 0.7), w=2)
                for R in (SRC, DRN):
                    cx = (R[0] + R[2]) / 2
                    p.line(cx, 430, cx, 300, A(St.TEXT2, 0.7), w=2)
                for x, lab in ((470, 'S'), (960, 'G'), (1450, 'D')):
                    p.circle(x, 288, 16, fill=St.BG_IN, stroke=A(St.TEXT2, 0.9), w=1.6)
                    p.text(lab, x, 295, size=18, family='mono', weight=600, color=St.TEXT, align='center')
            # tension de grille
            va = prog(t, c['repos'] - 0.3, 0.5)
            K.readout(p, 960, 190, 'Tension de grille', f'{0.7 * gate:.1f} V'.replace('.', ','), t - c['repos'] + 0.3,
                      align='center', size=36, color=mix(St.TEXT2, St.VIOLET, gate), a=va)

        # ---------------- champ électrique -------------------------------------
        if field > 0.01:
            for k in range(8):
                x = CH_X0 + 40 + k * (CH_X1 - CH_X0 - 80) / 7
                ph = ((t * 0.8 + k * 0.13) % 1.0)
                K.arrow(p, x, 530, x, 530 + 150 * field, St.VIOLET, w=2.5, head=12, pr=1.0, a=0.75 * field, glow=0.7)
                yy = 530 + ph * 150 * field
                p.circle(x, yy, 3, fill=St.VIOLET, a=field * (1 - ph), glow=1.0)

        # ---------------- étiquettes -----------------------------------------
        a_lab = 1 - prog(t, c['repos'] - 0.5, 0.5)
        K.label(p, 120, 820, 'Source', t - c['source'], ax=380, ay=650, sub='réservoir d\'électrons', a=a_lab)
        K.label(p, 1800, 820, 'Drain', t - c['drain'], ax=1540, ay=650, sub='N+', a=a_lab, align='right')
        K.label(p, 960, 1030, 'Zone de type P', t - c['typeP'], sub='trous majoritaires', sub_color=St.AMBER,
                a=a_lab, align='center')
        K.label(p, 1450, 200, 'Grille', t - c['grille'], ax=1200, ay=440, a=a_lab, sub='électrode de commande',
                sub_color=St.VIOLET)
        K.label(p, 1450, 330, 'Oxyde isolant', t - c['oxyde'], ax=1240, ay=544, a=a_lab,
                sub="≈ 1 nm : quelques atomes")
        K.keyword(p, 'Le transistor', t - c['transistor'] + 0.1, y=150, size=58, hold=2.4, sub='MOSFET')

        # ---------------- diagramme de bande + bit -----------------------------
        a_band = prog(t, c['repos'], 0.6)
        if a_band > 0:
            self._band(p, t, c, ch, flow, a_band)
        if t > c['zero'] - 0.2:
            bit = 1 if ch > 0.5 else 0
            # instant du dernier changement
            K.panel(p, 140, 120, 240, 230, t - c['zero'] + 0.2, a=1.0)
            p.text('ÉTAT', 260, 160, size=15, family='grotesk', weight=500, color=St.TEXT2, align='center',
                   tracking=0.25, a=prog(t, c['zero'] - 0.2, 0.4))
            K.bit(p, 260, 300, bit, c['zero'] - 0.2 if bit == 0 and t < c['canal'] else self._last_change(t, c), t,
                  size=130)
            p.text('bloqué' if bit == 0 else 'passant', 260, 335, size=18, family='sans', weight=500,
                   color=St.CYAN if bit else St.TEXT3, align='center', a=prog(t, c['zero'], 0.4))
        K.keyword(p, 'Un bit', t - c['bit'] + 0.2, size=60, color=St.CYAN, hold=1.4,
                  sub='un transistor bloqué ou passant : 0 ou 1')

    def _last_change(self, t, c):
        events = [c['canal'], c['coupez'] + 0.55, c['u1'], c['z2']]
        last = c['zero'] - 0.2
        for e in events:
            if t >= e:
                last = e
        return last

    def _band(self, p, t, c, ch, flow, a):
        x0, y0, w, h = 1300, 60, 480, 220
        K.panel(p, x0, y0, w, h, t - c['repos'], a=a)
        with p.fade(a):
            p.text("ÉNERGIE DES ÉLECTRONS", x0 + 20, y0 + 32, size=14, family='grotesk', weight=500,
                   color=St.TEXT2, tracking=0.2)
            hump = 95 * (1 - 0.85 * ch)
            base = y0 + h - 50
            pts = []
            for k in range(81):
                u = k / 80
                b = 1 / (1 + math.exp(-(u - 0.33) * 40)) * (1 - 1 / (1 + math.exp(-(u - 0.67) * 40)))
                pts.append((x0 + 20 + u * (w - 40), base - hump * b + (12 * flow * u)))
            p.poly(pts, stroke=St.TEXT, w=2.2, glow=0.4, smooth=False)
            for u, lab in ((0.12, 'S'), (0.5, 'canal'), (0.88, 'D')):
                p.text(lab, x0 + 20 + u * (w - 40), y0 + h - 14, size=14, family='mono', color=St.TEXT3,
                       align='center')
            # électrons dans la vallée de la source / passage
            xs, ys = [], []
            for k in range(9):
                u = (k * 0.031 + noise1(t * 2 + k, 3) * 0.02 + 0.05)
                if flow > 0.05:
                    ph = ((t * 0.5 + k / 9) % 1.0)
                    u = lerp(0.05, 0.95, ph) if k % 2 == 0 else u
                xx = x0 + 20 + u * (w - 40)
                b = 1 / (1 + math.exp(-(u - 0.33) * 40)) * (1 - 1 / (1 + math.exp(-(u - 0.67) * 40)))
                xs.append(xx)
                ys.append(base - hump * b + 12 * flow * u - 9)
            K.electrons(p, np.array(xs), np.array(ys), 4.5, a=1.0, k=0.8)
            la = prog(t, c['barriere'] - 0.1, 0.4) * (1 - prog(t, c['abaisse'] + 1.5, 0.5))
            p.text('barrière', x0 + w / 2, base - hump - 14, size=15, family='grotesk', weight=500,
                   color=St.RED if ch < 0.5 else St.CYAN, align='center', a=la)
