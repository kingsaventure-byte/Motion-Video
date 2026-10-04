"""Classe de base d'une vidéo : orchestration des scènes et des transitions."""
import json
import os

from . import ease as E
from .anim import clamp
from .timeline import SceneTime, Timeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Video:
    name = 'video'
    W, H, fps = 1920, 1080, 60
    voice = 'fr-FR-RemyMultilingualNeural'
    rate = '+0%'
    pitch = '+0Hz'
    post_defaults = {'bloom': 1.0, 'glow': 1.0, 'exposure': 1.0, 'ca': 0.0015, 'vignette': 0.55, 'grain': 0.7}

    def make_scenes(self):
        raise NotImplementedError

    # ------------------------------------------------------------ préparation
    @property
    def build_dir(self):
        return os.path.join(ROOT, 'build', self.name)

    def prepare(self, tts=True):
        self.scenes = self.make_scenes()
        lines = [ln for sc in self.scenes for ln in sc.lines()]
        vdir = os.path.join(self.build_dir, 'voice')
        if tts:
            from .tts import synthesize
            manifest = synthesize(lines, self.voice, self.rate, self.pitch, vdir)
        else:
            with open(os.path.join(vdir, 'manifest.json')) as f:
                manifest = json.load(f)
        self.tl = Timeline(self.scenes, manifest, self.voice, self.rate, self.pitch)
        self.duration = self.tl.duration
        for i, sc in enumerate(self.scenes):
            sc.index = i
            sc.video = self
            sc.prev_trans = self.scenes[i - 1].trans if i > 0 else 0.0
            sc.setup()
        return self

    # --------------------------------------------------------------- rendu
    def background(self, p, t, active):
        p.bg((0, 0, 0, 1))

    def overlay(self, p, t, active):
        pass

    def active(self, t):
        """Scènes visibles à l'instant t avec leurs progressions d'entrée/sortie."""
        out = []
        n = len(self.scenes)
        for i, sc in enumerate(self.scenes):
            tin = sc.prev_trans if i > 0 else 0.0
            tout = sc.trans if i < n - 1 else 0.0
            a, b = sc.start - tin / 2, sc.end + tout / 2
            if not (a <= t < b) and not (i == n - 1 and t >= b - 1e-9 and t <= b + 1):
                continue
            enter = clamp((t - a) / tin) if tin > 0 else 1.0
            exit_ = clamp((t - (sc.end - tout / 2)) / tout) if tout > 0 else 0.0
            out.append((sc, SceneTime(sc, t - sc.start, enter, exit_)))
        return out

    def draw(self, p, t):
        act = self.active(t)
        self.background(p, t, act)
        post_acc, wsum = {}, 0.0
        for sc, S in act:
            mode = sc.transition
            prev_mode = self.scenes[sc.index - 1].transition if sc.index > 0 else 'cut'
            # Entrée : style de transition de la scène précédente ; sortie : le sien.
            ein = E.smooth(S.enter)
            eout = E.smooth(S.exit)
            alpha, scale, blur = 1.0, 1.0, 0.0
            if S.enter < 1 and prev_mode in ('zoom', 'fade'):
                alpha *= ein
                if prev_mode == 'zoom':
                    scale *= 0.94 + 0.06 * E.out_cubic(S.enter)
                    blur += (1 - ein) * 10
            if S.exit > 0 and mode in ('zoom', 'fade'):
                alpha *= 1 - eout
                if mode == 'zoom':
                    scale *= 1 + 0.12 * E.in_cubic(S.exit)
                    blur += eout * 10
            S.alpha = alpha
            if alpha <= 0.002:
                continue
            P = dict(self.post_defaults)
            P.update(sc.post(S) or {})
            for k, v in P.items():
                post_acc[k] = post_acc.get(k, 0.0) + v * alpha
            wsum += alpha
            if alpha >= 0.999 and scale == 1.0 and blur < 0.05:
                sc.draw(p, S)
            else:
                with p.layer(alpha=alpha, blur=blur):
                    if scale != 1.0:
                        p.save()
                        p.translate(self.W / 2, self.H / 2)
                        p.scale_(scale)
                        p.translate(-self.W / 2, -self.H / 2)
                    sc.draw(p, S)
                    if scale != 1.0:
                        p.restore()
        self.overlay(p, t, act)
        if wsum > 0:
            p.post.update({k: v / wsum for k, v in post_acc.items()})
        else:
            p.post.update(self.post_defaults)

    def sfx_events(self):
        ev = []
        for sc in self.scenes:
            S = SceneTime(sc, 0.0)
            for t, name, gain in sc.sfx(S):
                ev.append((sc.start + t, name, gain))
        return sorted(ev)
