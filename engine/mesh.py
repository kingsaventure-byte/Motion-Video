"""Mini moteur 3D polygonal : pavés ombrés, tri du peintre, arêtes lumineuses."""
import numpy as np

from .camera import box_faces
from .color import mix


class Box:
    __slots__ = ('b', 'color', 'edge', 'a', 'glow', 'edge_w', 'top', 'emit', 'sheen')

    def __init__(self, b, color, edge=None, a=1.0, glow=0.0, edge_w=1.0, top=None, emit=0.0, sheen=None):
        self.b, self.color, self.edge, self.a, self.glow, self.edge_w, self.top, self.emit = \
            b, color, edge, a, glow, edge_w, top, emit
        self.sheen = sheen      # fonction(points écran) -> shader pour la face supérieure


def render(p, cam, boxes, ldir=(-0.45, 0.85, 0.4), amb=0.32, cull=True, fog=None):
    """Dessine des pavés. fog=(z_proche, z_loin, couleur) atténue les faces lointaines."""
    L = np.asarray(ldir, np.float64)
    L = L / np.linalg.norm(L)
    faces = []
    for bx in boxes:
        if bx.a <= 0.003:
            continue
        for verts, n in box_faces(*bx.b):
            c = verts.mean(axis=0)
            if cull and np.dot(n, cam.eye - c) <= 0:
                continue
            sx, sy, z, _ = cam.project(verts)
            if np.any(z <= 1e-2):
                continue
            k = amb + (1 - amb) * max(0.0, float(np.dot(n, L)))
            col = bx.top if (bx.top is not None and n[1] > 0.5) else bx.color
            shaded = (min(1, col[0] * k + bx.emit), min(1, col[1] * k + bx.emit), min(1, col[2] * k + bx.emit), col[3])
            if fog is not None:
                z0, z1, fc = fog
                f = np.clip((z.mean() - z0) / (z1 - z0), 0, 1)
                shaded = mix(shaded, fc, f)
            faces.append((float(z.mean()), list(zip(sx, sy)), shaded, bx, n[1] > 0.5))
    faces.sort(key=lambda f: -f[0])
    for _, pts, col, bx, is_top in faces:
        p.poly(pts, fill=col, closed=True, a=bx.a, glow=bx.glow * 0.5 if bx.glow else 0.0)
        if is_top and bx.sheen is not None:
            p.poly(pts, shader=bx.sheen(pts), closed=True, a=bx.a)
        if bx.edge is not None:
            p.poly(pts, stroke=bx.edge, w=bx.edge_w, closed=True, a=bx.a, glow=bx.glow)
    return faces
