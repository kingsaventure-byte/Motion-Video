"""01 — L'échelle : zoom continu du boîtier jusqu'aux atomes d'un aileron de transistor."""
import math

import numpy as np
import skia

from engine import ease as E
from engine.anim import clamp, lerp, prog, smoothstep
from engine.camera import Cam3D
from engine.color import alpha as A, mix, hex2
from engine.mesh import Box, render
from engine.noise import noise1, rng
from engine.painter import lin, rad
from engine.timeline import Scene

from .. import script as SC
from .. import style as St
from .. import kit as K

# Largeur de champ (m) à l'échelle de base de chaque niveau ; Lz = log10 du grossissement.
BASE = [0.0, 1.0, 3.7, 4.7, 6.22]
FOV0 = 0.020

C_CORE = hex2('#3FA9FF')
C_CACHE = hex2('#9277FF')
C_GPU = hex2('#3FE0C0')
C_IO = hex2('#FFB547')


def _fmt_len(m):
    for unit, k in (('cm', 1e-2), ('mm', 1e-3), ('µm', 1e-6), ('nm', 1e-9)):
        if m >= k * 0.999:
            v = m / k
            return (f'{v:.0f}' if v >= 1 else f'{v:.1f}') + ' ' + unit
    return f'{m * 1e12:.0f} pm'


class Echelle(Scene):
    id = 'echelle'
    chapter = ("01", "L'échelle")
    lead = 2.4
    tail = 0.8
    trans = 1.1

    def lines(self):
        return SC.ECHELLE

    # ------------------------------------------------------------------ setup
    def setup(self):
        g = rng(21)
        # Plan de la puce (coordonnées : puce 1100 x 740 centrée).
        B = []
        xs = [-510, -373, -236, -99]
        for row, (y0, y1) in enumerate(((-330, -42), (42, 330))):
            for i, x0 in enumerate(xs):
                B.append(('core', (x0, y0, 125, y1 - y0), C_CORE))
        B.append(('cache', (-510, -30, 536, 60), C_CACHE))
        B.append(('gpu', (46, -330, 464, 470), C_GPU))
        B.append(('io', (46, 160, 464, 170), C_IO))
        self.blocks = B
        self.core_target = (-173.5, -186.0)
        self.twinkle = [(g.uniform(-530, 530), g.uniform(-350, 350), g.uniform(0, 10)) for _ in range(160)]
        # Texture « cellules standard » haute résolution pour le niveau cœur.
        self.tex = self._make_cell_texture(g)
        # Rangées de cellules (niveau 2) : largeurs aléatoires.
        self.rows = {}
        self.g2 = rng(77)

    def _make_cell_texture(self, g):
        H, W = 1024, 1024
        img = np.zeros((H, W, 4), np.float32)
        row_h = 12
        for r in range(H // row_h):
            y0 = r * row_h
            x = 0
            while x < W:
                w = int(g.integers(6, 40))
                c = g.uniform(0.45, 1.0)
                img[y0 + 2:y0 + row_h - 2, x + 1:x + w - 1, :3] += c * np.array([0.30, 0.45, 0.80])
                if g.random() < 0.5:
                    img[y0 + 3:y0 + row_h - 3, x + 2:x + w - 2:3, :3] += 0.25
                x += w
            img[y0:y0 + 1, :, :3] += np.array([0.25, 0.35, 0.6])
        for k in range(60):  # routage métal vertical
            x = int(g.integers(0, W))
            img[:, x:x + 2, :3] += np.array([0.55, 0.42, 0.25]) * g.uniform(0.3, 0.8)
        img[..., 3] = 1.0
        img[..., :3] = np.clip(img[..., :3] * 0.55, 0, 1)
        arr = (img * 255).astype(np.uint8)
        im = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
        return im

    # ---------------------------------------------------------------- caméra
    def _cues(self, S):
        return dict(
            proc=S.w('e1', 'processeur'), capot=S.w('e1', 'capot'), plaque=S.w('e1', 'plaque'),
            ongle=S.w('e1', 'ongle'), puce=S.w('e1', 'puce'), ville=S.w('e2', 'ville'),
            coeurs=S.w('e2', 'cœurs'), cache=S.w('e2', 'cache'), gpu=S.w('e2', 'graphique'),
            io=S.w('e2', 'circuits'), z1=S.w('e3', 'Zoomons'), z2=S.w('e3', 'Puis'),
            z3=S.w('e3', 'encore', n=1), forets=S.w('e4', 'forêts'), mil=S.w('e4', 'milliards'),
            fines=S.w('e5', 'fines'), nm=S.w('e5', 'nanomètres'), atomes=S.w('e5', "d'atomes"))

    def _lz(self, t, c):
        lz = 0.0
        lz += 1.0 * prog(t, c['z1'], 1.4, E.in_out_cubic)
        lz += 2.7 * prog(t, c['z2'], 1.2, E.in_out_cubic)
        lz += 1.0 * prog(t, c['z3'] - 0.1, 1.3, E.in_out_cubic)
        lz += 0.12 * prog(t, c['z3'] + 1.2, 5.0, E.in_out_sine)
        lz += 1.40 * prog(t, c['fines'] - 0.5, 1.6, E.in_out_cubic)
        lz += 0.08 * prog(t, c['fines'] + 1.1, 4.0, E.in_out_sine)
        return lz

    # ------------------------------------------------------------------ rendu
    def draw(self, p, S):
        t = S.t
        c = self._cues(S)
        K.chapter_card(p, S, '01', "L'échelle")
        lz = self._lz(t, c)
        speed = (self._lz(t + 1 / 60, c) - self._lz(t - 1 / 60, c)) * 30   # décades / s

        a3d = prog(t, 2.55, 0.7) * (1 - prog(t, c['puce'] + 1.25, 0.55))
        if a3d > 0:
            self._package(p, t, c, a3d)

        a0 = prog(t, c['puce'] + 1.15, 0.55) * (1 - smoothstep(0.55, 0.95, lz))
        if a0 > 0:
            self._die(p, t, c, lz, a0)
        a1 = smoothstep(0.45, 0.85, lz) * (1 - smoothstep(2.5, 3.0, lz))
        if a1 > 0:
            self._core(p, t, c, lz, a1, speed)
        a2 = smoothstep(2.6, 3.1, lz) * (1 - smoothstep(4.25, 4.6, lz))
        if a2 > 0:
            self._cells(p, t, c, lz, a2, speed)
        a3 = smoothstep(4.2, 4.6, lz) * (1 - smoothstep(5.55, 5.95, lz))
        if a3 > 0:
            self._forest(p, t, c, lz, a3)
        a4 = smoothstep(5.4, 5.9, lz)
        if a4 > 0:
            self._fin(p, t, c, lz, a4)
        self._scale_bar(p, t, c, lz)

    # -------------------------------------------------------------- barre d'échelle
    def _scale_bar(self, p, t, c, lz):
        a = prog(t, c['puce'] + 1.0, 0.8) 
        if a <= 0:
            return
        fov = FOV0 / 10 ** lz
        mpp = fov / 1920
        target = fov * 0.16
        e = math.floor(math.log10(target))
        best = None
        for m in (1, 2, 5, 10):
            v = m * 10 ** e
            if v <= target * 1.6:
                best = v
        px = best / mpp
        x0, y0 = 130, 985
        with p.fade(a):
            p.line(x0, y0, x0 + px, y0, St.TEXT, w=2, glow=0.3)
            p.line(x0, y0 - 7, x0, y0 + 7, St.TEXT, w=2)
            p.line(x0 + px, y0 - 7, x0 + px, y0 + 7, St.TEXT, w=2)
            p.text(_fmt_len(best), x0, y0 - 18, size=20, family='mono', weight=500, color=St.TEXT)
            p.text('ÉCHELLE', x0, y0 + 32, size=13, family='grotesk', weight=500, color=St.TEXT3, tracking=0.25)
            p.text(f'x {10 ** lz * 54:,.0f}'.replace(',', ' '), x0 + 110, y0 + 32, size=13, family='mono',
                   color=St.TEXT3)

    # ------------------------------------------------------------- boîtier 3D
    def _package_cam(self, t, c):
        k = prog(t, c['puce'] - 0.1, 1.5, E.in_out_cubic)
        yaw = lerp(-32 + 10 * prog(t, 2.5, 7, E.out_sine), 0.0, k)
        pitch = lerp(36, 88.5, k)
        dist = lerp(98, 24.0, k)
        return Cam3D.orbit(target=(0, 1.6, 0), dist=dist, yaw=yaw, pitch=pitch, fov=30)

    def _package(self, p, t, c, a):
        cam = self._package_cam(t, c)
        rise = (1 - prog(t, 2.55, 1.2, E.snap)) * -6
        lift = prog(t, c['capot'] + 0.2, 1.5, E.in_out_cubic)
        a_lid = 1 - prog(t, c['plaque'] - 0.2, 1.0)
        subs = hex2('#0F2E2C')
        kd = prog(t, c['puce'] - 0.1, 1.5, E.in_out_cubic)
        a_sub = a * (1 - prog(kd, 0.35, 0.45))
        boxes = [Box((-18.75, rise, -18.75, 18.75, 1.2 + rise, 18.75), subs, top=hex2('#123834'),
                     edge=A(hex2('#3E8F7F'), 0.5), a=a_sub, edge_w=1.0)]
        for i in range(14):  # composants CMS autour
            ang = i / 14 * 2 * math.pi
            x, z = math.cos(ang) * 16.5, math.sin(ang) * 16.5
            boxes.append(Box((x - 0.9, 1.2 + rise, z - 0.5, x + 0.9, 1.8 + rise, z + 0.5), hex2('#5E4F3C'), a=a_sub))
        die_col = hex2('#161D3E')
        hl = prog(t, c['puce'], 0.4) * (1 - prog(t, c['puce'] + 0.6, 1.0))
        shimmer = 0.05 + 0.06 * prog(t, c['plaque'], 1.0) + 0.10 * hl

        def die_sheen(pts):
            (x0, y0), (x1, y1) = pts[0], pts[2]
            ph = (t * 0.25) % 1.0
            return lin(x0, y0, x1, y1, [(0, A(St.VIOLET, 0.0)), (max(0.01, ph - 0.15), A(St.CYAN, 0.0)),
                                        (ph, A(St.CYAN, 0.22)), (min(0.99, ph + 0.15), A(St.VIOLET, 0.0)),
                                        (1, A(St.VIOLET, 0.0))])

        boxes.append(Box((-6.5, 1.2 + rise, -4.4, 6.5, 1.95 + rise, 4.4), die_col, top=mix(die_col, St.CYAN, shimmer),
                         edge=A(St.CYAN, 0.8), a=a, glow=0.35 * prog(t, c['plaque'], 0.8), edge_w=1.4,
                         sheen=die_sheen))
        render(p, cam, boxes, amb=0.36)
        boxes = []
        if a_lid > 0.01:
            ly = 1.2 + rise + lift * 20

            def lid_sheen(pts):
                (x0, y0), (x1, y1) = pts[0], pts[2]
                return lin(x0, y0, x1, y1, [(0, A(St.WHITE, 0.0)), (0.42, A(St.WHITE, 0.16)), (0.5, A(St.WHITE, 0.04)),
                                            (0.62, A(St.WHITE, 0.10)), (1, A(St.WHITE, 0.0))])

            boxes.append(Box((-17, ly, -17, 17, ly + 3.0, 17), hex2('#79839A'), top=hex2('#8E98AC'),
                             edge=A(St.TEXT, 0.45), a=a * a_lid, edge_w=1.2, sheen=lid_sheen))
            render(p, cam, boxes, amb=0.36)
        # étiquettes
        sx, sy, _, _ = cam.project([(13, 1.2 + rise + lift * 20 + 3, -10), (5.5, 1.95 + rise, 3.6)])
        K.label(p, sx[0] + 120, sy[0] - 60, 'Capot métallique', t - c['capot'], ax=sx[0], ay=sy[0],
                a=a * (1 - prog(t, c['plaque'], 0.5)))
        K.label(p, sx[1] + 230, sy[1] + 120, 'La puce · silicium', t - c['plaque'] - 0.3, ax=sx[1], ay=sy[1],
                sub='≈ 1 à 2 cm de côté', a=a * (1 - prog(t, c['puce'] + 0.2, 0.5)))

    # ------------------------------------------------------------- plan de la puce
    def _die_cam(self, t, c, lz):
        k = prog(t, c['z1'] - 0.15, 1.1, E.in_out_cubic)
        cx = lerp(0, self.core_target[0], k)
        cy = lerp(0, self.core_target[1], k)
        return cx, cy, 10 ** lz

    def _die(self, p, t, c, lz, a):
        cx, cy, z = self._die_cam(t, c, lz)
        breathe = 1 + 0.015 * prog(t, c['puce'] + 1, 8, E.in_out_sine)
        with p.fade(a), p.camera(cx, cy, z * breathe):
            W, H = 1100, 740
            p.rect(-W / 2 - 14, -H / 2 - 14, W + 28, H + 28, fill=hex2('#081022'), r=10)
            p.rect(-W / 2, -H / 2, W, H, shader=lin(-W / 2, -H / 2, W / 2, H / 2,
                   [(0, hex2('#121B3A')), (0.5, hex2('#0C1430')), (1, hex2('#141A3C'))]), r=6)
            p.rect(-W / 2, -H / 2, W, H, stroke=A(St.CYAN, 0.55), sw=1.4 / z, r=6, glow=0.35)
            # anneau d'E/S : plots
            for i in range(44):
                x = -W / 2 + 14 + i * (W - 28) / 43
                for yy in (-H / 2 + 6, H / 2 - 14):
                    p.rect(x - 5, yy, 10, 8, fill=A(C_IO, 0.45))
            for i in range(30):
                y = -H / 2 + 14 + i * (H - 28) / 29
                for xx in (-W / 2 + 6, W / 2 - 14):
                    p.rect(xx, y - 5, 8, 10, fill=A(C_IO, 0.45))
            cues = {'core': c['coeurs'], 'cache': c['cache'], 'gpu': c['gpu'], 'io': c['io']}
            for i, (kind, (x, y, w, h), col) in enumerate(self.blocks):
                ta = c['ville'] - 0.5 + i * 0.07
                pr = prog(t, ta, 0.8, E.snap)
                if pr <= 0:
                    continue
                hl = prog(t, cues[kind] - 0.1, 0.35, E.out_cubic) * (1 - 0.6 * prog(t, cues[kind] + 1.3, 0.8))
                fa = 0.10 + 0.30 * hl
                p.rect(x, y, w, h, fill=A(col, fa * pr), r=3)
                p.rect(x, y, w, h, stroke=A(col, (0.45 + 0.5 * hl) * pr), sw=1.3, r=3, glow=0.25 + 0.9 * hl)
                self._block_detail(p, kind, x, y, w, h, col, pr * (0.55 + 0.45 * hl))
            # activité : scintillements
            for (x, y, ph) in self.twinkle:
                v = max(0.0, math.sin(t * 2.3 + ph * 3.1)) ** 8
                if v > 0.05:
                    p.dots([x], [y], [1.8], St.CYAN_HOT, a=v * prog(t, c['ville'], 1.0), glow=0.8, gr=4)
        # étiquettes (repère écran)
        if lz < 0.4:
            def scr(x, y):
                return 960 + (x - cx) * z * breathe, 540 + (y - cy) * z * breathe
            la = a * (1 - prog(t, c['z1'] - 0.3, 0.4))
            ax, ay = scr(-449, -186)
            K.label(p, 120, 300, 'Cœurs de calcul', t - c['coeurs'] + 0.1, ax=ax, ay=ay, sub='x 8', a=la)
            ax, ay = scr(-300, 0)
            K.label(p, 120, 640, 'Mémoire cache', t - c['cache'] + 0.1, ax=ax, ay=ay, sub='SRAM', a=la)
            ax, ay = scr(330, -140)
            K.label(p, 1545, 260, 'Graphique', t - c['gpu'] + 0.1, ax=ax, ay=ay, sub='GPU intégré', a=la)
            ax, ay = scr(330, 250)
            K.label(p, 1545, 820, 'Entrées / sorties', t - c['io'] + 0.1, ax=ax, ay=ay, sub='mémoire, PCIe...', a=la)

    def _block_detail(self, p, kind, x, y, w, h, col, a):
        with p.fade(a):
            if kind == 'core':
                p.rect(x + 8, y + 8, w - 16, h * 0.28, fill=A(C_CACHE, 0.25), r=2)
                p.rect(x + 8, y + h * 0.32, w * 0.45, h * 0.3, fill=A(col, 0.18), r=2)
                p.rect(x + w * 0.55, y + h * 0.32, w * 0.38, h * 0.3, fill=A(col, 0.28), r=2)
                p.rect(x + 8, y + h * 0.66, w - 16, h * 0.28, fill=A(col, 0.14), r=2)
                for k in range(6):
                    yy = y + h * 0.69 + k * h * 0.04
                    p.line(x + 12, yy, x + w - 12, yy, A(col, 0.35), w=1)
            elif kind == 'cache':
                for k in range(40):
                    xx = x + 6 + k * (w - 12) / 39
                    p.line(xx, y + 6, xx, y + h - 6, A(col, 0.45), w=1.2)
            elif kind == 'gpu':
                for i in range(6):
                    for j in range(4):
                        bx = x + 12 + i * (w - 24) / 6
                        by = y + 12 + j * (h - 24) / 4
                        bw, bh = (w - 24) / 6 - 8, (h - 24) / 4 - 8
                        p.rect(bx, by, bw, bh, stroke=A(col, 0.5), sw=1, r=2)
                        p.rect(bx + 4, by + 4, bw * 0.4, bh - 8, fill=A(col, 0.18), r=1)
            elif kind == 'io':
                for k in range(8):
                    p.rect(x + 10 + k * (w - 20) / 8, y + 12, (w - 20) / 8 - 10, h - 24, stroke=A(col, 0.45), sw=1, r=2)

    # ---------------------------------------------------------------- niveau cœur
    def _core(self, p, t, c, lz, a, speed):
        z = 10 ** (lz - 1.0)
        # centre caméra : continuité avec le niveau puce puis cible dans l'ALU
        dcx, dcy, _ = self._die_cam(t, c, lz)
        cx = (dcx - self.core_target[0]) * 10
        cy = (dcy - self.core_target[1]) * 10
        k2 = prog(t, c['z2'] - 0.2, 1.0, E.in_out_cubic)
        T1 = (300.0, -40.0)
        cx, cy = lerp(cx, T1[0], k2), lerp(cy, T1[1], k2)
        blur = min(14.0, max(0.0, speed - 0.6) * 5)
        blocks = [('Cache L2', (-600, -1420, 1200, 700), C_CACHE), ('Décodage', (-600, -690, 1200, 420), C_CORE),
                  ('Ordonnanceur', (-600, -240, 540, 400), C_CORE), ('ALU', (-30, -240, 630, 400), C_GPU),
                  ('Vectoriel', (-600, 190, 1200, 600), C_CORE), ('Cache L1', (-600, 820, 1200, 600), C_CACHE)]
        with p.layer(alpha=a, blur=blur):
            with p.camera(cx, cy, z):
                p.rect(-625, -1450, 1250, 2900, fill=hex2('#0A1128'), r=4)
                for name, (x, y, w, h), col in blocks:
                    sh = self.tex.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                                             skia.SamplingOptions(skia.FilterMode.kLinear),
                                             skia.Matrix.Scale(0.5, 0.5))
                    p.rect(x, y, w, h, shader=sh, a=0.9)
                    p.rect(x, y, w, h, fill=A(col, 0.16))
                    p.rect(x, y, w, h, stroke=A(col, 0.7), sw=2.0, glow=0.4)
                    p.text(name, x + 18, y + 34, size=24, family='grotesk', weight=600, color=A(col, 1.0),
                           tracking=0.16, upper=True, glow=0.25)

    # -------------------------------------------------------------- niveau cellules
    def _cells(self, p, t, c, lz, a, speed):
        z = 10 ** (lz - BASE[2])
        blur = min(12.0, max(0.0, speed - 0.6) * 5)
        row_h, pitch = 96.0, 24.0
        view_w, view_h = 1920 / z, 1080 / z
        with p.layer(alpha=a, blur=blur):
            with p.camera(0, 0, z):
                r0 = max(-18, int(math.floor((-view_h / 2) / row_h)) - 1)
                r1 = min(18, int(math.ceil((view_h / 2) / row_h)) + 1)
                x_min, x_max = max(-3000.0, -view_w / 2 - 50), min(3000.0, view_w / 2 + 50)
                for r in range(r0, r1 + 1):
                    y = r * row_h
                    # rails d'alimentation
                    p.rect(x_min, y - 5, x_max - x_min, 10, fill=A(hex2('#5D7BC0'), 0.55))
                    g = np.random.default_rng(1000 + r)
                    x = -3000.0 + g.uniform(0, 200)
                    while x < x_max:
                        w = pitch * int(g.integers(3, 12))
                        if x + w > x_min:
                            p.rect(x + 4, y + 9, w - 8, row_h - 18, fill=A(hex2('#1E6E5A'), 0.55), r=3)
                            n = int(w / pitch)
                            if pitch * z > 3:
                                for k in range(1, n):
                                    gx = x + k * pitch
                                    p.line(gx, y + 4, gx, y + row_h - 4, A(hex2('#FF5F7A'), 0.75), w=3.2)
                            # métal 1
                            if g.random() < 0.6:
                                yy = y + row_h * g.uniform(0.3, 0.7)
                                p.line(x + 6, yy, x + w - 6, yy, A(hex2('#6FB6FF'), 0.7), w=6, cap='butt')
                        x += w
                if 0.01 < a:
                    pass
        K.label(p, 1480, 250, 'Cellules logiques', 0.0 if lz < 3.2 else (lz - 3.2) * 4, a=a * (1 - smoothstep(4.0, 4.3, lz)),
                sub='grilles  |  métal  |  alimentation', align='left')

    # ----------------------------------------------------------- forêt de transistors
    def _forest_cam(self, t, c, lz):
        k = prog(t, c['z3'] + 0.5, 2.6, E.in_out_cubic)
        pitch_deg = lerp(87.0, 30.0, k)
        yaw = lerp(0, -32, k) + 7 * prog(t, c['forets'], 6, E.in_out_sine)
        dz = 10 ** (min(lz, 4.95) - BASE[3])
        dist = lerp(760, 640, k) / dz
        cam = Cam3D.orbit(target=(0, 20, 0), dist=dist, yaw=yaw, pitch=pitch_deg, fov=34)
        # approche finale : face avant de l'aileron central
        k4 = prog(t, c['fines'] - 0.5, 1.6, E.in_out_cubic)
        if k4 > 0:
            eye = cam.eye * (1 - k4) + np.array([0.0, 26.0, 262.0]) * k4
            tgt = cam.target * (1 - k4) + np.array([0.0, 24.0, 250.0]) * k4
            cam = Cam3D(eye, tgt, fov=34)
        return cam

    def _forest(self, p, t, c, lz, a):
        cam = self._forest_cam(t, c, lz)
        fin_col = hex2('#3E62B0')
        gate_col = hex2('#6D55D8')
        sub = hex2('#121B3A')
        nf, ng = 13, 9
        fp, gp = 30.0, 52.0
        fw, fh, gl, gh = 7.0, 48.0, 16.0, 66.0
        X0 = -(nf - 1) * fp / 2
        Z0 = -(ng - 1) * gp / 2
        XE, ZE = -X0 + 22, 250.0
        render(p, cam, [Box((-XE, -14, -ZE, XE, 0, ZE), sub, top=hex2('#16224A'), edge=A(St.LINE, 0.4), a=a)], amb=0.34)
        boxes = []
        fin_x = [X0 + i * fp for i in range(nf)]
        gz = [Z0 + j * gp for j in range(ng)]
        # ailerons découpés entre les grilles (pas d'intersection -> tri du peintre fiable)
        for x in fin_x:
            zs = [-ZE] + [v for zc in gz for v in (zc - gl / 2, zc + gl / 2)] + [ZE]
            for s_ in range(0, len(zs), 2):
                boxes.append(Box((x - fw / 2, 0, zs[s_], x + fw / 2, fh, zs[s_ + 1]), fin_col,
                                 top=mix(fin_col, St.CYAN, 0.45), edge=A(St.CYAN, 0.45), a=a, edge_w=0.9, glow=0.15))
        # grilles découpées en segments (au-dessus et entre les ailerons)
        xs = [-XE] + [v for x in fin_x for v in (x - fw / 2, x + fw / 2)] + [XE]
        for zc in gz:
            for s_ in range(len(xs) - 1):
                x0, x1 = xs[s_], xs[s_ + 1]
                if x1 - x0 < 0.01:
                    continue
                over_fin = (s_ % 2 == 1)
                y0 = fh if over_fin else 0
                boxes.append(Box((x0, y0, zc - gl / 2, x1, gh, zc + gl / 2), gate_col,
                                 top=mix(gate_col, St.TEXT, 0.22), edge=A(St.VIOLET, 0.55), a=a, edge_w=0.7))
        d = float(np.linalg.norm(cam.eye - cam.target))
        render(p, cam, boxes, amb=0.34, fog=(d * 0.7, d * 2.2, A(St.BG_OUT, 1.0)))
        # étiquettes
        k4 = prog(t, c['fines'] - 0.5, 0.6)
        sx, sy, _, _ = cam.project([(fin_x[8], fh, gz[1] + gp / 2), (fin_x[5], gh, gz[4])])
        la = a * prog(t, c['forets'] + 0.4, 0.5) * (1 - k4)
        K.label(p, 1470, 260, 'Grille', t - c['forets'] - 0.6, ax=sx[1], ay=sy[1], a=la)
        K.label(p, 1470, 860, 'Ailerons de silicium', t - c['forets'] - 1.0, ax=sx[0], ay=sy[0], a=la,
                sub='le canal du transistor')
        if t > c['mil'] - 1.2:
            n = 50e9 * E.out_expo(clamp((t - c['mil'] + 1.2) / 2.0))
            ra = a * (1 - k4)
            K.readout(p, 150, 300, 'Transistors sur une puce', f'{n:,.0f}'.replace(',', ' '), t - c['mil'] + 1.2,
                      a=ra, size=40)
            with p.fade(ra * prog(t, c['mil'] + 0.8, 0.5)):
                p.text("ordre de grandeur", 150, 395, size=16, family='sans', weight=400, color=St.TEXT3)

    # ----------------------------------------------------------------- un aileron
    def _fin(self, p, t, c, lz, a):
        """Coupe d'un aileron : réseau d'atomes, oxyde de grille, grille enveloppante."""
        z = 10 ** (lz - BASE[4])
        cx, top = 960.0, 330.0
        sp = 30.0                        # ~0,28 nm entre colonnes d'atomes
        ncol = 18
        fw = ncol * sp                   # ≈ 5 nm
        x0 = cx - fw / 2
        ox = 34.0                        # oxyde ≈ 1 nm
        with p.fade(a), p.camera(cx, 560, z, ox=cx, oy=560):
            gate = skia.Path()
            gate.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0 - ox - 230, top - ox - 170, x0 + fw + ox + 230, 1400),
                                                140, 140))
            p.path(gate, fill=A(St.VIOLET, 0.16))
            p.path(gate, stroke=A(St.VIOLET, 0.6), w=2, glow=0.35)
            oxp = skia.Path()
            oxp.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0 - ox, top - ox, x0 + fw + ox, 1400), 70, 70))
            p.path(oxp, fill=hex2('#0A1024'))
            p.path(oxp, fill=A(St.TEXT, 0.10))
            p.path(oxp, stroke=A(St.TEXT, 0.4), w=1.4)
            finp = skia.Path()
            finp.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, top, x0 + fw, 1400), 46, 46))
            p.path(finp, fill=hex2('#0B1430'))
            # atomes (réseau triangulaire, agitation thermique)
            xs, ys = [], []
            rows = int((1200 - top) / (sp * 0.87))
            for j in range(rows):
                y = top + 22 + j * sp * 0.87
                off = sp / 2 if j % 2 else 0.0
                for i in range(ncol):
                    x = x0 + 15 + i * sp + off
                    if x > x0 + fw - 12:
                        continue
                    # coins arrondis
                    dx = min(x - x0, x0 + fw - x)
                    dy = y - top
                    if dx < 46 and dy < 46 and math.hypot(46 - dx, 46 - dy) > 40:
                        continue
                    xs.append(x)
                    ys.append(y)
            xs, ys = np.array(xs), np.array(ys)
            ph = np.arange(len(xs)) * 1.7
            xs = xs + np.sin(t * 9 + ph) * 1.3
            ys = ys + np.cos(t * 7.3 + ph * 1.3) * 1.3
            # vague de comptage sur « quelques dizaines d'atomes »
            wave = prog(t, c['atomes'] - 0.6, 1.4, E.in_out_sine)
            hot = np.exp(-((xs - (x0 + wave * fw)) / 40.0) ** 2) * (0 < wave < 1)
            cols = [mix(St.SI, St.CYAN_HOT, float(h) * 0.8) for h in hot]
            p.spheres(xs, ys, 11.5, cols, glow=0.18)
        # annotations (repère écran)
        sx = lambda x: cx + (x - cx) * z
        sy = lambda y: 560 + (y - 560) * z
        la = a * prog(lz, 5.9, 0.2)
        K.dimension(p, sx(x0), sy(top - ox - 80), sx(x0 + fw), sy(top - ox - 80), '≈ 5 nm', t - c['nm'] + 0.2, a=a,
                    size=24, side=-1)
        K.label(p, 1500, 330, 'Grille', t - c['nm'] + 0.6, ax=sx(x0 + fw + ox + 120), ay=sy(top + 40), a=la)
        K.label(p, 1500, 520, 'Oxyde · ≈ 1 nm', t - c['nm'] + 0.9, ax=sx(x0 + fw + ox * 0.5), ay=sy(top + 260), a=la)
        K.label(p, 120, 760, 'Aileron de silicium', t - c['atomes'] + 0.6, ax=sx(x0 + 40), ay=sy(top + 420), a=la,
                sub="quelques dizaines d'atomes de large")
