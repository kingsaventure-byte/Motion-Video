"""Post-traitement « cinéma ».

Chaîne : halo d'émission multi-échelle + bloom à seuil (HDR flottant)
-> tone mapping à épaule douce (LUT) -> aberration chromatique radiale
-> vignette -> grain argentique pondéré par la luminance (sert aussi de dithering).
Les étapes lourdes passent par OpenCV (SIMD) pour tenir ~60 ms / image en 1080p.
"""
import cv2
import numpy as np

HDR_MAX = 4.0          # dynamique maximale avant tone mapping (x blanc)


class Post:
    def __init__(self, pw, ph, seed=7, grain_frames=12):
        self.pw, self.ph = pw, ph
        self.k = pw / 1920.0
        yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
        r = np.sqrt(((xx - pw / 2) / (pw / 2)) ** 2 + ((yy - ph / 2) / (ph / 2)) ** 2 * 0.62)
        self.r = r
        self._vig = {}
        g = np.random.default_rng(seed)
        self.grain = []
        for _ in range(grain_frames):
            n = g.standard_normal((ph, pw)).astype(np.float32)
            n = cv2.GaussianBlur(n, (0, 0), 0.6 * max(self.k, 0.5))
            n /= n.std() + 1e-6
            self.grain.append(np.clip(n * 32, -127, 127).astype(np.int16))   # écart-type 32 = 1/8 de pas
        # LUT de tone mapping sur 0..HDR_MAX (en 1/256 de blanc).
        n = int(256 * HDR_MAX)
        x = np.arange(n, dtype=np.float64) / 255.0
        knee = 0.80
        e = np.maximum(x - knee, 0)
        y = np.minimum(x, knee) + (1 - knee) * (1 - np.exp(-e / (1 - knee)))
        self.tm = np.clip(y * 255 + 0.5, 0, 255).astype(np.uint8)
        # Pondération du grain selon la luminance (plus visible dans les tons moyens).
        L = np.arange(256) / 255.0
        self.gw_lut = None
        self._gw_amt = None
        self._L = L

    def _vignette(self, amt):
        v = self._vig.get(amt)
        if v is None:
            m = 1.0 - amt * np.clip(self.r - 0.30, 0, None) ** 1.7 / 1.25
            m = np.clip(m, 0, 1)
            v = cv2.merge([(m * 255 + 0.5).astype(np.uint8)] * 3)
            self._vig[amt] = v
        return v

    def _grain_w(self, amt):
        if self._gw_amt != amt:
            L = self._L
            w = amt * (0.30 + 1.7 * L * (1 - L) + 0.25 * np.sqrt(L))
            self.gw_lut = np.clip(w * 256 * 8, 0, 255).astype(np.uint8)   # gain en 1/256
            self._gw_amt = amt
        return self.gw_lut

    def apply(self, main, glow, frame, P=None):
        P = P or {}
        bloom_k = P.get('bloom', 1.0)
        glow_k = P.get('glow', 1.0)
        exposure = P.get('exposure', 1.0)
        ca = P.get('ca', 0.0015)
        vig = round(P.get('vignette', 0.55), 3)
        grain = P.get('grain', 0.9)
        pw, ph, k = self.pw, self.ph, self.k

        rgb = cv2.cvtColor(main, cv2.COLOR_RGBA2RGB)
        hdr = None

        # --- halo d'émission ------------------------------------------------
        if glow_k > 0:
            g = cv2.cvtColor(glow, cv2.COLOR_RGBA2RGB)
            if g.max() > 0:
                g = g.astype(np.float32)
                gh, gw = g.shape[:2]
                s = gw / 960.0
                b1 = cv2.GaussianBlur(g, (0, 0), 2.0 * s)
                d2 = cv2.resize(g, (gw // 2, gh // 2), interpolation=cv2.INTER_AREA)
                b2 = cv2.GaussianBlur(d2, (0, 0), 3.5 * s)
                d3 = cv2.resize(d2, (gw // 4, gh // 4), interpolation=cv2.INTER_AREA)
                b3 = cv2.GaussianBlur(d3, (0, 0), 6.0 * s)
                d4 = cv2.resize(d3, (gw // 8, gh // 8), interpolation=cv2.INTER_AREA)
                b4 = cv2.GaussianBlur(d4, (0, 0), 9.0 * s)
                acc = cv2.resize(b4, (gw // 4, gh // 4), interpolation=cv2.INTER_LINEAR)
                acc = cv2.addWeighted(acc, 0.85, b3, 1.0, 0)
                acc = cv2.resize(acc, (gw // 2, gh // 2), interpolation=cv2.INTER_LINEAR)
                acc = cv2.addWeighted(acc, 0.85, b2, 1.0, 0)
                acc = cv2.resize(acc, (gw, gh), interpolation=cv2.INTER_LINEAR)
                acc = cv2.addWeighted(acc, 0.8, b1, 1.0, 0)
                acc = cv2.addWeighted(acc, 1.0, g, 0.3, 0)
                full = cv2.resize(acc, (pw, ph), interpolation=cv2.INTER_LINEAR)
                hdr = rgb.astype(np.float32)
                if exposure != 1.0:
                    hdr *= exposure
                hdr = cv2.scaleAdd(full, 0.55 * glow_k, hdr)

        # --- bloom à seuil sur l'image ---------------------------------------
        if bloom_k > 0:
            small = cv2.resize(rgb if hdr is None else hdr, (pw // 4, ph // 4), interpolation=cv2.INTER_AREA)
            small = small.astype(np.float32) if small.dtype != np.float32 else small
            br = cv2.max(small - 165.0, 0)
            if br.max() > 0.5:
                b = cv2.GaussianBlur(br, (0, 0), 3.0 * k)
                b2 = cv2.GaussianBlur(cv2.resize(br, (pw // 16, ph // 16), interpolation=cv2.INTER_AREA), (0, 0), 2.5 * k)
                b = cv2.addWeighted(b, 1.0, cv2.resize(b2, (pw // 4, ph // 4), interpolation=cv2.INTER_LINEAR), 0.8, 0)
                if hdr is None:
                    hdr = rgb.astype(np.float32)
                    if exposure != 1.0:
                        hdr *= exposure
                hdr = cv2.scaleAdd(cv2.resize(b, (pw, ph), interpolation=cv2.INTER_LINEAR), 0.5 * bloom_k, hdr)

        # --- tone mapping ------------------------------------------------------
        if hdr is not None:
            idx = np.minimum(hdr, len(self.tm) - 1).astype(np.uint16)
            img = self.tm[idx]
        else:
            img = rgb if exposure == 1.0 else cv2.convertScaleAbs(rgb, alpha=exposure)
            img = self.tm[img]

        # --- aberration chromatique radiale --------------------------------
        if ca > 0:
            r, gch, b = cv2.split(img)
            cx, cy = pw / 2, ph / 2
            M1 = np.float32([[1 + ca, 0, -cx * ca], [0, 1 + ca, -cy * ca]])
            M2 = np.float32([[1 - ca, 0, cx * ca], [0, 1 - ca, cy * ca]])
            r = cv2.warpAffine(r, M1, (pw, ph), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            b = cv2.warpAffine(b, M2, (pw, ph), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            img = cv2.merge([r, gch, b])

        # --- vignette ---------------------------------------------------------
        if vig > 0:
            img = cv2.multiply(img, self._vignette(vig), scale=1 / 255.0)

        # --- grain -------------------------------------------------------------
        if grain > 0:
            lum = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            w = cv2.LUT(lum, self._grain_w(grain))
            n = cv2.multiply(self.grain[frame % len(self.grain)], w.astype(np.int16), scale=1 / 256.0,
                             dtype=cv2.CV_16S)
            pos = cv2.convertScaleAbs(cv2.max(n, 0), alpha=1 / 8.0)
            neg = cv2.convertScaleAbs(cv2.min(n, 0), alpha=1 / 8.0)
            pos3 = cv2.merge([pos, pos, pos])
            neg3 = cv2.merge([neg, neg, neg])
            img = cv2.subtract(cv2.add(img, pos3), neg3)
        return img
