"""Scènes, répliques et synchronisation avec la voix off.

Chaque scène déclare ses répliques ; la durée réelle de chaque réplique vient
de la synthèse vocale (avec l'horodatage de chaque mot). Les animations se
calent ensuite sur `S.L('id').start` ou sur un mot précis : `S.w('id', 'mot')`.
"""
import hashlib
import re
import unicodedata

from . import ease as E
from .anim import clamp


class Line:
    def __init__(self, id, text, pause=0.45):
        self.id, self.text, self.pause = id, text, pause
        self.start = self.end = self.dur = 0.0
        self.words = []          # [(mot, début, fin)] en temps local de scène
        self.file = None

    def key(self, voice, rate, pitch):
        h = hashlib.sha1(f'{voice}|{rate}|{pitch}|{self.text}'.encode()).hexdigest()[:16]
        return h


def _norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = ''.join(ch for ch in w if unicodedata.category(ch) != 'Mn')
    return re.sub(r"[^a-z0-9]", '', w)


class Scene:
    id = 'scene'
    chapter = None           # (numéro, titre) affiché dans l'interface
    lead = 0.7               # silence avant la 1re réplique
    tail = 0.9               # silence après la dernière
    min_dur = 0.0
    trans = 1.0              # durée du fondu enchaîné avec la scène suivante
    transition = 'zoom'      # 'zoom' | 'fade' | 'cut' | 'custom'

    def lines(self):
        return []

    def setup(self):
        pass

    def draw(self, p, S):
        pass

    def sfx(self, S):
        return []

    def post(self, S):
        return {}


class SceneTime:
    """Contexte temporel passé à `Scene.draw`."""

    def __init__(self, scene, t, enter=1.0, exit_=0.0):
        self.scene = scene
        self.t = t
        self.dur = scene.dur
        self.enter = enter       # 0 -> 1 pendant l'entrée
        self.exit = exit_        # 0 -> 1 pendant la sortie
        self._lines = scene._line_map

    def L(self, lid):
        return self._lines[lid]

    def w(self, lid, word, n=0, end=False):
        """Instant où le mot `word` est prononcé dans la réplique `lid` (n-ième occurrence)."""
        ln = self._lines[lid]
        target = _norm(word)
        k = 0
        for wd, s, e in ln.words:
            if _norm(wd).startswith(target):
                if k == n:
                    return e if end else s
                k += 1
        raise KeyError(f'mot "{word}" introuvable dans la réplique {lid}: {[x[0] for x in ln.words]}')

    def since(self, t0):
        return self.t - t0

    def p(self, t0, dur, ease=E.smooth):
        if dur <= 0:
            return 1.0 if self.t >= t0 else 0.0
        return ease(clamp((self.t - t0) / dur))


class Timeline:
    def __init__(self, scenes, manifest, voice, rate, pitch):
        self.scenes = scenes
        t = 0.0
        for sc in scenes:
            sc._lines = sc.lines()
            sc._line_map = {}
            sc.start = t
            lt = sc.lead
            last_pause = 0.0
            for ln in sc._lines:
                m = manifest[ln.key(voice, rate, pitch)]
                ln.file = m['file']
                ln.start = lt
                words = m['words']
                speech_end = words[-1][2] if words else m['dur']
                ln.dur = speech_end + 0.05
                ln.end = lt + ln.dur
                ln.words = [(w, lt + s, lt + e) for w, s, e in words]
                sc._line_map[ln.id] = ln
                lt = ln.end + ln.pause
                last_pause = ln.pause
            sc.dur = max(lt - last_pause + sc.tail, sc.min_dur)
            sc.end = sc.start + sc.dur
            t = sc.end
        self.duration = t

    def narration(self):
        """[(temps global, fichier)] pour le mixage."""
        out = []
        for sc in self.scenes:
            for ln in sc._lines:
                out.append((sc.start + ln.start, ln.file))
        return out

    def subtitles(self):
        """Répliques en temps global pour un fichier .srt."""
        return [(sc.start + ln.start, sc.start + ln.end, ln.text) for sc in self.scenes for ln in sc._lines]
