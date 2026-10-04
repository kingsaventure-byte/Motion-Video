"""Caméra 3D perspective (projection vectorisée) + petits outils de maillage."""
import math
import numpy as np


def _norm(v):
    v = np.asarray(v, np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


class Cam3D:
    """Repère monde : x droite, y haut, z vers la caméra. Écran : y vers le bas."""

    def __init__(self, eye, target=(0, 0, 0), up=(0, 1, 0), fov=35.0, W=1920, H=1080, cx=None, cy=None):
        self.eye = np.asarray(eye, np.float64)
        self.target = np.asarray(target, np.float64)
        f = _norm(self.target - self.eye)
        r = _norm(np.cross(f, up))
        u = np.cross(r, f)
        self.R = np.stack([r, u, -f])  # lignes : axes caméra
        self.f = (H / 2) / math.tan(math.radians(fov) / 2)
        self.cx = W / 2 if cx is None else cx
        self.cy = H / 2 if cy is None else cy

    @classmethod
    def orbit(cls, target=(0, 0, 0), dist=10.0, yaw=0.0, pitch=20.0, fov=35.0, **kw):
        y, p = math.radians(yaw), math.radians(pitch)
        t = np.asarray(target, np.float64)
        eye = t + dist * np.array([math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p)])
        return cls(eye, t, fov=fov, **kw)

    def to_cam(self, pts):
        pts = np.asarray(pts, np.float64).reshape(-1, 3)
        return (pts - self.eye) @ self.R.T

    def project(self, pts):
        """-> (sx, sy, profondeur, échelle_px_par_unité)."""
        pc = self.to_cam(pts)
        z = -pc[:, 2]
        z = np.where(z < 1e-3, 1e-3, z)
        s = self.f / z
        return self.cx + pc[:, 0] * s, self.cy - pc[:, 1] * s, z, s

    def light(self, normals, ldir=(-0.4, 0.8, 0.5), amb=0.28):
        n = np.asarray(normals, np.float64).reshape(-1, 3)
        l = _norm(ldir)
        return amb + (1 - amb) * np.clip(n @ l, 0, 1)


def box_faces(x0, y0, z0, x1, y1, z1):
    """6 faces d'un pavé : liste de (4 sommets, normale)."""
    v = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], np.float64)
    F = [((0, 1, 2, 3), (0, 0, -1)), ((5, 4, 7, 6), (0, 0, 1)), ((4, 0, 3, 7), (-1, 0, 0)),
         ((1, 5, 6, 2), (1, 0, 0)), ((3, 2, 6, 7), (0, 1, 0)), ((4, 5, 1, 0), (0, -1, 0))]
    return [(v[list(idx)], np.array(n, np.float64)) for idx, n in F]


def rot_y(pts, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    M = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.asarray(pts) @ M.T


def rot_x(pts, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    M = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return np.asarray(pts) @ M.T
