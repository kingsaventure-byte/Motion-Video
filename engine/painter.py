"""Peintre double tampon.

- `c` : image principale (pleine résolution).
- `g` : tampon d'émission (demi-résolution) : tout ce qui y est dessiné devient
  de la lumière (halo multi-échelle ajouté en post-traitement).

Toutes les coordonnées sont exprimées dans l'espace de conception 1920x1080,
quelle que soit la résolution de sortie.
"""
import math
from contextlib import contextmanager

import numpy as np
import skia

from . import text as T

WHITE = (1.0, 1.0, 1.0, 1.0)
_CAPS = {'round': skia.Paint.kRound_Cap, 'butt': skia.Paint.kButt_Cap, 'square': skia.Paint.kSquare_Cap}
_SPR = 64           # rayon des sprites de l'atlas (px)
_SPR_SIZE = 2 * _SPR + 8


def _ci(c, a=1.0):
    r, g, b, al = c
    al = al * a
    return skia.Color4f(r, g, b, max(0.0, min(1.0, al)))


def _argb(c, a=1.0):
    r, g, b, al = c
    A = max(0, min(255, int(al * a * 255 + 0.5)))
    return (A << 24) | (max(0, min(255, int(r * 255 + .5))) << 16) | \
        (max(0, min(255, int(g * 255 + .5))) << 8) | max(0, min(255, int(b * 255 + .5)))


def _make_sprites():
    """Atlas de sprites : disque net, disque doux, halo exponentiel, anneau."""
    S = _SPR_SIZE
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.sqrt((xx - S / 2 + 0.5) ** 2 + (yy - S / 2 + 0.5) ** 2) / _SPR  # 1 = bord
    disk = np.clip((1.0 - d) * _SPR * 0.9 + 0.5, 0, 1)
    soft = np.clip(1 - d, 0, 1) ** 2 * (3 - 2 * np.clip(1 - d, 0, 1))
    halo = np.exp(-d * d * 4.5) * (d < 1)
    halo = halo * np.clip((1 - d) * 6, 0, 1)
    ring = np.clip(1 - np.abs(d - 0.82) * _SPR / 5, 0, 1)
    # Sphère éclairée (lambert + liseré) et reflet spéculaire.
    nx = (xx - S / 2 + 0.5) / _SPR
    ny = (yy - S / 2 + 0.5) / _SPR
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    L = np.array([-0.45, -0.6, 0.66])
    L = L / np.linalg.norm(L)
    lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    shade = 0.16 + 0.84 * lam ** 1.1 + 0.30 * (1 - nz) ** 3
    sphere = np.clip(shade, 0, 1) * disk
    sx, sy = nx + 0.36, ny + 0.42
    spec = np.exp(-(sx * sx + sy * sy) / 0.018) * disk
    tiles = [disk, soft, halo, ring, sphere, spec]
    atlas = np.zeros((S, S * len(tiles), 4), np.uint8)
    for i, a in enumerate(tiles):
        v = (a * 255 + 0.5).astype(np.uint8)
        al = (disk * 255 + 0.5).astype(np.uint8) if i == 4 else v
        atlas[:, i * S:(i + 1) * S, 0] = v
        atlas[:, i * S:(i + 1) * S, 1] = v
        atlas[:, i * S:(i + 1) * S, 2] = v
        atlas[:, i * S:(i + 1) * S, 3] = al
    img = skia.Image.fromarray(atlas, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
    rects = {name: skia.Rect.MakeXYWH(i * S, 0, S, S) for i, name in enumerate(['disk', 'soft', 'halo', 'ring', 'sphere', 'spec'])}
    return img, rects


class Painter:
    def __init__(self, W=1920, H=1080, scale=1.0, glow_scale=0.5):
        self.W, self.H, self.scale = W, H, scale
        self.pw, self.ph = int(round(W * scale)), int(round(H * scale))
        self.buf = np.zeros((self.ph, self.pw, 4), np.uint8)
        self.surf = skia.Surface(self.buf, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        self.c = self.surf.getCanvas()
        self.gs = scale * glow_scale
        self.gw, self.gh = int(round(W * self.gs)), int(round(H * self.gs))
        self.gbuf = np.zeros((self.gh, self.gw, 4), np.uint8)
        self.gsurf = skia.Surface(self.gbuf, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        self.g = self.gsurf.getCanvas()
        self.ga = 1.0      # alpha global (pile multiplicative)
        self.gk = 1.0      # gain global du halo
        self.atlas, self.arect = _make_sprites()
        self.sampling = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
        self.post = {}     # paramètres de post-traitement pour cette image

    # ------------------------------------------------------------------ état
    def begin(self):
        self.c.restoreToCount(1)
        self.g.restoreToCount(1)
        self.c.resetMatrix()
        self.g.resetMatrix()
        self.c.clear(skia.ColorBLACK)
        self.g.clear(skia.ColorTRANSPARENT)
        self.c.scale(self.scale, self.scale)
        self.g.scale(self.gs, self.gs)
        self.ga = 1.0
        self.gk = 1.0
        self.post = {}

    def save(self):
        self.c.save()
        self.g.save()

    def restore(self):
        self.c.restore()
        self.g.restore()

    def translate(self, x, y):
        self.c.translate(x, y)
        self.g.translate(x, y)

    def scale_(self, sx, sy=None):
        sy = sx if sy is None else sy
        self.c.scale(sx, sy)
        self.g.scale(sx, sy)

    def rotate(self, deg, cx=None, cy=None):
        if cx is None:
            self.c.rotate(deg)
            self.g.rotate(deg)
        else:
            self.c.rotate(deg, cx, cy)
            self.g.rotate(deg, cx, cy)

    def concat(self, m):
        self.c.concat(m)
        self.g.concat(m)

    def clip_rect(self, x, y, w, h):
        r = skia.Rect.MakeXYWH(x, y, w, h)
        self.c.clipRect(r, doAntiAlias=True)
        self.g.clipRect(r, doAntiAlias=True)

    def clip_path(self, path):
        self.c.clipPath(path, doAntiAlias=True)
        self.g.clipPath(path, doAntiAlias=True)

    @contextmanager
    def push(self):
        self.save()
        try:
            yield self
        finally:
            self.restore()

    @contextmanager
    def fade(self, a, glow=None):
        """Alpha multiplicatif bon marché (pas de calque)."""
        oa, ok = self.ga, self.gk
        self.ga *= max(0.0, a)
        self.gk *= max(0.0, a if glow is None else glow)
        try:
            yield self
        finally:
            self.ga, self.gk = oa, ok

    @contextmanager
    def layer(self, alpha=1.0, blur=0.0, glow_alpha=None, blend=None):
        """Vrai calque : alpha de groupe, flou gaussien, mode de fusion."""
        p = skia.Paint()
        p.setAlphaf(max(0.0, min(1.0, alpha)))
        if blend is not None:
            p.setBlendMode(blend)
        if blur > 0.05:
            p.setImageFilter(skia.ImageFilters.Blur(blur * self.scale, blur * self.scale))
        pg = skia.Paint()
        pg.setAlphaf(max(0.0, min(1.0, alpha if glow_alpha is None else glow_alpha)))
        if blur > 0.05:
            pg.setImageFilter(skia.ImageFilters.Blur(blur * self.gs, blur * self.gs))
        self.c.saveLayer(None, p)
        self.g.saveLayer(None, pg)
        oa, ok = self.ga, self.gk
        self.ga, self.gk = 1.0, 1.0
        try:
            yield self
        finally:
            self.ga, self.gk = oa, ok
            self.c.restore()
            self.g.restore()

    @contextmanager
    def camera(self, cx, cy, zoom=1.0, rot=0.0, ox=None, oy=None):
        """Caméra 2D : (cx, cy) au centre de l'écran (ou en ox, oy)."""
        self.save()
        self.translate(self.W / 2 if ox is None else ox, self.H / 2 if oy is None else oy)
        if rot:
            self.rotate(rot)
        self.scale_(zoom)
        self.translate(-cx, -cy)
        try:
            yield self
        finally:
            self.restore()

    # --------------------------------------------------------------- peinture
    def _paint(self, color, a=1.0, stroke=None, cap='round', shader=None, blend=None, effect=None, mask_blur=0.0):
        p = skia.Paint(AntiAlias=True)
        p.setColor4f(_ci(color, a * self.ga))
        if stroke is not None:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(stroke)
            p.setStrokeCap(_CAPS[cap])
            p.setStrokeJoin(skia.Paint.kRound_Join)
        if shader is not None:
            p.setShader(shader)
        if blend is not None:
            p.setBlendMode(blend)
        if effect is not None:
            p.setPathEffect(effect)
        if mask_blur > 0:
            p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, mask_blur))
        return p

    def _gpaint(self, color, k, stroke=None, cap='round', effect=None):
        p = skia.Paint(AntiAlias=True)
        r, g, b, al = color
        p.setColor4f(_ci((r, g, b, al), min(1.0, k * self.ga * self.gk)))
        p.setBlendMode(skia.BlendMode.kPlus)
        if stroke is not None:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(stroke)
            p.setStrokeCap(_CAPS[cap])
            p.setStrokeJoin(skia.Paint.kRound_Join)
        if effect is not None:
            p.setPathEffect(effect)
        return p

    def bg(self, color):
        self.c.drawColor(_ci(color).toColor())

    def fill_screen(self, shader=None, color=None, a=1.0, blend=None):
        """Remplit tout l'écran (repère écran, indépendant de la caméra)."""
        self.c.save()
        self.c.resetMatrix()
        self.c.scale(self.scale, self.scale)
        p = self._paint(color or WHITE, a, shader=shader, blend=blend)
        self.c.drawRect(skia.Rect.MakeWH(self.W, self.H), p)
        self.c.restore()

    def circle(self, x, y, r, fill=None, stroke=None, w=1.5, a=1.0, glow=0.0, gcol=None, gr=1.6, shader=None):
        if r <= 0:
            return
        if fill is not None or shader is not None:
            self.c.drawCircle(x, y, r, self._paint(fill or WHITE, a, shader=shader))
        if stroke is not None:
            self.c.drawCircle(x, y, r, self._paint(stroke, a, stroke=w))
        if glow > 0:
            col = gcol or fill or stroke
            if fill is not None or gcol is not None:
                self.g.drawCircle(x, y, r * gr, self._gpaint(col, glow * a))
            else:
                self.g.drawCircle(x, y, r, self._gpaint(col, glow * a, stroke=w * gr))

    def rect(self, x, y, w, h, fill=None, stroke=None, sw=1.5, r=0.0, a=1.0, glow=0.0, gcol=None, shader=None):
        rc = skia.Rect.MakeXYWH(x, y, w, h)
        rr = skia.RRect.MakeRectXY(rc, r, r) if r > 0 else None
        def draw(cv, paint):
            if rr is not None:
                cv.drawRRect(rr, paint)
            else:
                cv.drawRect(rc, paint)
        if fill is not None or shader is not None:
            draw(self.c, self._paint(fill or WHITE, a, shader=shader))
        if stroke is not None:
            draw(self.c, self._paint(stroke, a, stroke=sw, cap='butt'))
        if glow > 0:
            col = gcol or fill or stroke
            if fill is not None or gcol is not None:
                draw(self.g, self._gpaint(col, glow * a))
            else:
                draw(self.g, self._gpaint(col, glow * a, stroke=sw * 1.8))

    def line(self, x1, y1, x2, y2, color, w=2.0, a=1.0, glow=0.0, gcol=None, gw=1.8, cap='round', effect=None):
        self.c.drawLine(x1, y1, x2, y2, self._paint(color, a, stroke=w, cap=cap, effect=effect))
        if glow > 0:
            self.g.drawLine(x1, y1, x2, y2, self._gpaint(gcol or color, glow * a, stroke=w * gw, cap=cap, effect=effect))

    def path(self, path, fill=None, stroke=None, w=2.0, a=1.0, glow=0.0, gcol=None, gw=1.8, trim=None,
             cap='round', shader=None, dash=None):
        eff = None
        if trim is not None:
            t0, t1 = trim
            if t1 - t0 <= 0.0005:
                return
            if t0 > 0.0 or t1 < 1.0:
                eff = skia.TrimPathEffect.Make(max(0.0, t0), min(1.0, t1))
        if dash is not None:
            d = skia.DashPathEffect.Make(list(dash[0]), dash[1])
            eff = d if eff is None else skia.PathEffect.MakeCompose(d, eff)
        if fill is not None or (shader is not None and stroke is None):
            self.c.drawPath(path, self._paint(fill or WHITE, a, shader=shader))
        if stroke is not None:
            self.c.drawPath(path, self._paint(stroke, a, stroke=w, cap=cap, effect=eff, shader=shader))
        if glow > 0:
            col = gcol or stroke or fill
            if stroke is not None:
                self.g.drawPath(path, self._gpaint(col, glow * a, stroke=w * gw, cap=cap, effect=eff))
            else:
                self.g.drawPath(path, self._gpaint(col, glow * a))

    def poly(self, pts, stroke=None, fill=None, w=2.0, closed=False, a=1.0, glow=0.0, gcol=None, trim=None,
             smooth=False, cap='round', shader=None, dash=None):
        self.path(make_path(pts, closed, smooth), fill=fill, stroke=stroke, w=w, a=a, glow=glow, gcol=gcol,
                  trim=trim, cap=cap, shader=shader, dash=dash)

    def arc(self, cx, cy, r, a0, a1, color, w=2.0, a=1.0, glow=0.0, cap='round'):
        """Arc en degrés (0 = droite, sens horaire)."""
        if abs(a1 - a0) < 0.01:
            return
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), a0, a1 - a0)
        self.path(p, stroke=color, w=w, a=a, glow=glow, cap=cap)

    # --------------------------------------------------------- sprites en lot
    def dots(self, xs, ys, rs, colors, a=1.0, sprite='disk', glow=0.0, gsprite='halo', gr=2.5, gcolors=None,
             main=True, blend=None):
        """Dessine N sprites en un appel (atlas). colors : couleur unique ou liste de tuples."""
        n = len(xs)
        if n == 0:
            return
        if np.isscalar(rs):
            rs = np.full(n, float(rs))
        single = isinstance(colors, tuple) and len(colors) == 4 and not isinstance(colors[0], tuple)
        xs = np.asarray(xs, np.float64)
        ys = np.asarray(ys, np.float64)
        rs = np.asarray(rs, np.float64)
        alphas = None
        if isinstance(a, np.ndarray):
            alphas = a
            a = 1.0
        if main:
            k = rs / _SPR
            off = _SPR_SIZE / 2
            xf = [skia.RSXform(s, 0, x - s * off, y - s * off) for s, x, y in zip(k, xs, ys)]
            tex = [self.arect[sprite]] * n
            if single:
                cols = [_argb(colors, a * self.ga * (alphas[i] if alphas is not None else 1.0)) for i in range(n)] \
                    if alphas is not None else [_argb(colors, a * self.ga)] * n
            else:
                cols = [_argb(c, a * self.ga * (alphas[i] if alphas is not None else 1.0)) for i, c in enumerate(colors)]
            pnt = skia.Paint(AntiAlias=True)
            if blend is not None:
                pnt.setBlendMode(blend)
            self.c.drawAtlas(self.atlas, xf, tex, cols, skia.BlendMode.kModulate, self.sampling, None, pnt)
        if glow > 0:
            k = rs * gr / _SPR
            off = _SPR_SIZE / 2
            xf = [skia.RSXform(s, 0, x - s * off, y - s * off) for s, x, y in zip(k, xs, ys)]
            tex = [self.arect[gsprite]] * n
            gk = min(1.0, glow * a * self.ga * self.gk)
            src = gcolors if gcolors is not None else colors
            gsingle = isinstance(src, tuple) and len(src) == 4 and not isinstance(src[0], tuple)
            if gsingle:
                cols = [_argb(src, gk * (alphas[i] if alphas is not None else 1.0)) for i in range(n)]
            else:
                cols = [_argb(c, gk * (alphas[i] if alphas is not None else 1.0)) for i, c in enumerate(src)]
            pnt = skia.Paint(AntiAlias=True)
            pnt.setBlendMode(skia.BlendMode.kPlus)
            self.g.drawAtlas(self.atlas, xf, tex, cols, skia.BlendMode.kModulate, self.sampling, None, pnt)

    def spheres(self, xs, ys, rs, colors, a=1.0, spec=0.55, glow=0.0, gr=1.6):
        """Sphères ombrées (atomes) : diffus teinté + reflet blanc."""
        self.dots(xs, ys, rs, colors, a=a, sprite='sphere', glow=glow, gsprite='soft', gr=gr)
        if spec > 0:
            self.dots(xs, ys, rs, (1.0, 1.0, 1.0, 1.0), a=(a * spec) if not isinstance(a, np.ndarray) else a * spec,
                      sprite='spec', blend=skia.BlendMode.kPlus)

    def glow_dot(self, x, y, r, color, k=1.0, core=True, a=1.0):
        """Point lumineux : noyau net + halo dans le tampon d'émission."""
        if core:
            self.dots([x], [y], [r], color, a=a, sprite='disk')
        self.dots([x], [y], [r], color, a=a, main=False, glow=k, gr=3.0)

    def gcircle(self, x, y, r, color, k=1.0, sprite='halo'):
        """Lumière seule (tampon d'émission)."""
        self.dots([x], [y], [r], color, main=False, glow=k, gsprite=sprite, gr=1.0)

    # ----------------------------------------------------------------- texte
    def text(self, s, x, y, size=32, family='sans', weight=400, color=WHITE, align='left', tracking=0.0,
             a=1.0, glow=0.0, gcol=None, valign='baseline', upper=False):
        if upper:
            s = s.upper()
        items, width = T.layout(s, size, family, weight, tracking)
        if align == 'center':
            x -= width / 2
        elif align == 'right':
            x -= width
        if valign == 'middle':
            y += T.cap_height(size, family, weight) / 2
        elif valign == 'top':
            y += T.cap_height(size, family, weight)
        b = T.blob(items, x, y)
        if b is None:
            return width
        self.c.drawTextBlob(b, 0, 0, self._paint(color, a))
        if glow > 0:
            self.g.drawTextBlob(b, 0, 0, self._gpaint(gcol or color, glow * a))
        return width

    def text_reveal(self, s, x, y, t, size=32, family='sans', weight=400, color=WHITE, align='left',
                    tracking=0.0, a=1.0, glow=0.0, gap=0.035, dur=0.7, rise=0.45, blur=True, upper=False,
                    valign='baseline', ease=None, out=None):
        """Apparition lettre par lettre (fondu + montée + netteté). t = temps depuis le début.
        out=(t_sortie, durée) : disparition lettre par lettre."""
        from . import ease as E
        ease = ease or E.snap
        if upper:
            s = s.upper()
        items, width = T.layout(s, size, family, weight, tracking)
        if align == 'center':
            x -= width / 2
        elif align == 'right':
            x -= width
        if valign == 'middle':
            y += T.cap_height(size, family, weight) / 2
        i = 0
        for f, gl, pos in items:
            for gid, (px, py) in zip(gl, pos):
                pr = ease(max(0.0, min(1.0, (t - i * gap) / dur)))
                if out is not None:
                    to, od = out
                    po = E.in_cubic(max(0.0, min(1.0, (t - to - i * gap * 0.5) / od)))
                    pr = pr * (1 - po)
                i += 1
                if pr <= 0.002:
                    continue
                bb = skia.TextBlobBuilder()
                bb.allocRunPos(f, [gid], [skia.Point(x + px, y + py + (1 - pr) * size * rise)])
                blob = bb.make()
                pnt = self._paint(color, a * pr)
                if blur and pr < 0.98:
                    pnt.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, (1 - pr) * size * 0.12 + 0.01))
                self.c.drawTextBlob(blob, 0, 0, pnt)
                if glow > 0:
                    self.g.drawTextBlob(blob, 0, 0, self._gpaint(color, glow * a * pr))
        return width

    def measure(self, s, size=32, family='sans', weight=400, tracking=0.0):
        return T.measure(s, size, family, weight, tracking)

    # ---------------------------------------------------------------- images
    def blit(self, img, x, y, w, h, a=1.0, glow=0.0, blend=None):
        """Dessine une skia.Image déjà construite (fond pré-calculé, textures)."""
        dst = skia.Rect.MakeXYWH(x, y, w, h)
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(max(0.0, min(1.0, a * self.ga)))
        if blend is not None:
            p.setBlendMode(blend)
        self.c.drawImageRect(img, dst, self.sampling, p)
        if glow > 0:
            pg = skia.Paint(AntiAlias=True)
            pg.setAlphaf(max(0.0, min(1.0, glow * a * self.ga * self.gk)))
            pg.setBlendMode(skia.BlendMode.kPlus)
            self.g.drawImageRect(img, dst, self.sampling, pg)

    def image(self, arr, x, y, w, h, a=1.0, glow=0.0, blend=None):
        img = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType,
                                   alphaType=skia.kPremul_AlphaType)
        dst = skia.Rect.MakeXYWH(x, y, w, h)
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(max(0.0, min(1.0, a * self.ga)))
        if blend is not None:
            p.setBlendMode(blend)
        self.c.drawImageRect(img, dst, self.sampling, p)
        if glow > 0:
            pg = skia.Paint(AntiAlias=True)
            pg.setAlphaf(max(0.0, min(1.0, glow * a * self.ga * self.gk)))
            pg.setBlendMode(skia.BlendMode.kPlus)
            self.g.drawImageRect(img, dst, self.sampling, pg)


# ---------------------------------------------------------------- utilitaires
def make_path(pts, closed=False, smooth=False):
    p = skia.Path()
    if not len(pts):
        return p
    if not smooth or len(pts) < 3:
        p.moveTo(*pts[0])
        for q in pts[1:]:
            p.lineTo(*q)
    else:  # Catmull-Rom -> Bézier
        P = list(pts)
        n = len(P)
        p.moveTo(*P[0])
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            p0 = P[(i - 1) % n] if (closed or i > 0) else P[i]
            p1 = P[i]
            p2 = P[(i + 1) % n]
            p3 = P[(i + 2) % n] if (closed or i + 2 < n) else P[(i + 1) % n]
            c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
            c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
            p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        p.close()
    return p


def lin(x0, y0, x1, y1, stops):
    """Dégradé linéaire. stops = [(pos, couleur), ...]."""
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)],
                                          [_argb(c) for _, c in stops], [s for s, _ in stops])


def rad(cx, cy, r, stops):
    return skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(r, 0.01),
                                          [_argb(c) for _, c in stops], [s for s, _ in stops])


def rot_pt(x, y, deg, cx=0.0, cy=0.0):
    a = math.radians(deg)
    dx, dy = x - cx, y - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)


_PM = {}


def point_on(path, frac):
    """Point situé à la fraction `frac` de la longueur d'un chemin (mesure mise en cache)."""
    key = id(path)
    ent = _PM.get(key)
    if ent is None or ent[0] is not path:
        meas = skia.PathMeasure(path, False)
        ent = _PM[key] = (path, meas, meas.getLength())
    _, meas, L = ent
    pos, tan = meas.getPosTan(L * max(0.0, min(1.0, frac)))
    return pos.x(), pos.y()


def path_length(path):
    return skia.PathMeasure(path, False).getLength()
