"""Typographie : mise en forme HarfBuzz (crénage, ligatures) + glyphes Skia.

Texte enrichi : `^{...}` exposant, `_{...}` indice. Exemple : "10^{5} m/s", "e^{-}".
"""
import os
import re
from functools import lru_cache

import skia
import uharfbuzz as hb

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'fonts')

FAMILIES = {
    'display': {300: 'InterDisplay-Light', 500: 'InterDisplay-Medium', 600: 'InterDisplay-SemiBold',
                700: 'InterDisplay-Bold', 800: 'InterDisplay-ExtraBold'},
    'sans': {300: 'Inter-Light', 400: 'Inter-Regular', 500: 'Inter-Medium', 600: 'Inter-SemiBold', 700: 'Inter-Bold'},
    'grotesk': {300: 'SpaceGrotesk-300', 400: 'SpaceGrotesk-400', 500: 'SpaceGrotesk-500',
                600: 'SpaceGrotesk-600', 700: 'SpaceGrotesk-700'},
    'mono': {400: 'JetBrainsMono-Regular', 500: 'JetBrainsMono-Medium', 600: 'JetBrainsMono-SemiBold'},
}


class Face:
    def __init__(self, name):
        path = os.path.join(FONT_DIR, name + '.ttf')
        with open(path, 'rb') as f:
            data = f.read()
        self.hbface = hb.Face(data)
        self.hbfont = hb.Font(self.hbface)
        self.upem = self.hbface.upem
        self.tf = skia.Typeface.MakeFromFile(path)
        self._fonts = {}

    def font(self, size):
        key = round(size * 8) / 8
        f = self._fonts.get(key)
        if f is None:
            f = skia.Font(self.tf, key)
            f.setEdging(skia.Font.Edging.kAntiAlias)
            f.setHinting(skia.FontHinting.kNone)
            f.setSubpixel(True)
            f.setLinearMetrics(True)
            self._fonts[key] = f
        return f


_FACES = {}


def face(family='sans', weight=400):
    fam = FAMILIES[family]
    w = min(fam.keys(), key=lambda k: abs(k - weight))
    name = fam[w]
    fc = _FACES.get(name)
    if fc is None:
        fc = _FACES[name] = Face(name)
    return fc


@lru_cache(maxsize=4096)
def shape(family, weight, text, size, tracking):
    """Renvoie (glyphes, xs, ys, avance totale) ; tracking en fraction de la taille."""
    fc = face(family, weight)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(fc.hbfont, buf, {'kern': True, 'liga': True, 'calt': True})
    k = size / fc.upem
    tr = tracking * size
    gl, xs, ys = [], [], []
    x = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gl.append(info.codepoint)
        xs.append(x + pos.x_offset * k)
        ys.append(-pos.y_offset * k)
        x += pos.x_advance * k + tr
    width = x - tr if gl else 0.0
    return tuple(gl), tuple(xs), tuple(ys), width


_RICH = re.compile(r'(\^\{[^}]*\}|_\{[^}]*\})')


@lru_cache(maxsize=2048)
def runs(text, size):
    """Découpe en segments (texte, taille, décalage vertical)."""
    out = []
    for part in _RICH.split(text):
        if not part:
            continue
        if part.startswith('^{'):
            out.append((part[2:-1], size * 0.62, -size * 0.36))
        elif part.startswith('_{'):
            out.append((part[2:-1], size * 0.62, size * 0.14))
        else:
            out.append((part, size, 0.0))
    return tuple(out)


def layout(text, size, family='sans', weight=400, tracking=0.0):
    """Liste de (font, glyphes, positions[(x,y)]) + largeur totale."""
    x = 0.0
    items = []
    for seg, sz, dy in runs(text, size):
        gl, xs, ys, w = shape(family, weight, seg, sz, tracking)
        f = face(family, weight).font(sz)
        items.append((f, gl, [(x + gx, gy + dy) for gx, gy in zip(xs, ys)]))
        x += w + tracking * size
    return items, x - (tracking * size if items else 0)


def measure(text, size, family='sans', weight=400, tracking=0.0):
    return layout(text, size, family, weight, tracking)[1]


def blob(items, x0=0.0, y0=0.0):
    b = skia.TextBlobBuilder()
    for f, gl, pos in items:
        if gl:
            b.allocRunPos(f, list(gl), [skia.Point(x0 + px, y0 + py) for px, py in pos])
    return b.make()


def cap_height(size, family='sans', weight=400):
    m = face(family, weight).font(size).getMetrics()
    return m.fCapHeight if m.fCapHeight > 0 else size * 0.72
