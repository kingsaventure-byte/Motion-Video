"""Rendu parallèle image par image -> ffmpeg.

Exemples :
  python render.py puce_atomique                       # master 1080p60
  python render.py puce_atomique --preview             # aperçu 960x540 30 i/s
  python render.py puce_atomique --stills 3.5,12,40    # images fixes PNG
  python render.py puce_atomique --start 30 --end 45   # extrait
"""
import argparse
import importlib
import multiprocessing as mp
import os
import subprocess
import sys
import time

import cv2
import numpy as np

_V = _P = _POST = None
_FPS = 60


def load(name, tts):
    mod = importlib.import_module(f'videos.{name}.video')
    return mod.make().prepare(tts=tts)


def _init(name, scale, fps):
    global _V, _P, _POST, _FPS
    cv2.setNumThreads(1)
    from .painter import Painter
    from .post import Post
    _V = load(name, tts=False)
    _P = Painter(_V.W, _V.H, scale=scale)
    _POST = Post(_P.pw, _P.ph)
    _FPS = fps


def _frame(i):
    t = i / _FPS
    _P.begin()
    _V.draw(_P, t)
    img = _POST.apply(_P.buf, _P.gbuf, i, _P.post)
    return i, img.tobytes()


def render(name, out, scale=1.0, fps=60, start=0.0, end=None, workers=4, crf=16, preset='slow', audio=None):
    v = load(name, tts=True)
    total = v.duration if end is None else min(end, v.duration)
    f0, f1 = int(round(start * fps)), int(round(total * fps))
    from .painter import Painter
    pw, ph = Painter(v.W, v.H, scale=scale).pw, int(round(v.H * scale))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{pw}x{ph}',
           '-r', str(fps), '-i', '-']
    if audio:
        cmd += ['-ss', f'{start:.4f}', '-i', audio]
    cmd += ['-vf', 'scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int',
            '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p',
            '-x264-params', 'aq-mode=3:aq-strength=0.9:deblock=-1,-1',
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
            '-movflags', '+faststart']
    if audio:
        cmd += ['-c:a', 'aac', '-b:a', '320k', '-shortest']
    cmd += [out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = f1 - f0
    print(f'[render] {name}: {n} images {pw}x{ph} @ {fps} i/s ({n / fps:.1f}s) -> {out}')
    t0 = time.time()
    with mp.get_context('fork').Pool(workers, initializer=_init, initargs=(name, scale, fps)) as pool:
        for k, (i, data) in enumerate(pool.imap(_frame, range(f0, f1), chunksize=2)):
            enc.stdin.write(data)
            if k % 120 == 0 or k == n - 1:
                el = time.time() - t0
                fps_r = (k + 1) / el if el > 0 else 0
                eta = (n - k - 1) / fps_r if fps_r > 0 else 0
                print(f'  {k + 1}/{n}  {fps_r:.1f} i/s  reste ~{eta / 60:.1f} min', flush=True)
    enc.stdin.close()
    enc.wait()
    print(f'[render] terminé en {(time.time() - t0) / 60:.1f} min')
    return out


def stills(name, times, out_dir, scale=1.0, fps=60):
    _init(name, scale, fps)
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for t in times:
        i = int(round(t * fps))
        _, data = _frame(i)
        img = np.frombuffer(data, np.uint8).reshape(_P.ph, _P.pw, 3)
        path = os.path.join(out_dir, f't{t:07.2f}.png')
        cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        paths.append(path)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('--out')
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--scale', type=float)
    ap.add_argument('--fps', type=int)
    ap.add_argument('--start', type=float, default=0.0)
    ap.add_argument('--end', type=float)
    ap.add_argument('--workers', type=int, default=os.cpu_count() or 4)
    ap.add_argument('--crf', type=int)
    ap.add_argument('--stills')
    ap.add_argument('--no-audio', action='store_true')
    a = ap.parse_args()
    sys.path.insert(0, os.getcwd())
    scale = a.scale or (0.5 if a.preview else 1.0)
    fps = a.fps or (30 if a.preview else 60)
    if a.stills:
        v = load(a.name, tts=True)
        times = [float(x) for x in a.stills.split(',')]
        for pth in stills(a.name, times, os.path.join('out', a.name, 'stills'), scale, fps):
            print(pth)
        return
    out = a.out or os.path.join('out', a.name, f'{a.name}{"_preview" if a.preview else ""}.mp4')
    audio = None
    if not a.no_audio:
        try:
            from .audio import build_mix
        except ImportError:  # mixage pas encore implémenté : rendu muet
            print('[render] module audio absent : rendu sans son')
        else:
            v = load(a.name, tts=True)
            audio = build_mix(v)
    render(a.name, out, scale=scale, fps=fps, start=a.start, end=a.end, workers=a.workers,
           crf=a.crf or (22 if a.preview else 16), preset='veryfast' if a.preview else 'slow', audio=audio)


if __name__ == '__main__':
    main()
