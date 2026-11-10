"""Cameras solved by fit.py (cams.json): rays, plane hits, projection, plane rectification."""
import json

import numpy as np


class Cam:
    def __init__(s, d):
        s.pos = np.array(d['pos'], float); s.R = np.array(d['R'], float); s.f = d['f']
        s.cx, s.cy, s.W, s.H = d['cx'], d['cy'], d['W'], d['H']

    def ray(s, px, py):
        v = s.R.T @ np.array([(px - s.cx) / s.f, (py - s.cy) / s.f, 1.0]); return v / np.linalg.norm(v)

    def hit(s, px, py, axis, value):
        r = s.ray(px, py); t = (value - s.pos[axis]) / r[axis]; return s.pos + t * r

    def proj(s, P):
        c = s.R @ (np.asarray(P, float) - s.pos)
        return np.array([s.f * c[0] / c[2] + s.cx, s.f * c[1] / c[2] + s.cy]), c[2]

    def rectify(s, img, origin, u, v, usize, vsize, ppm, mask_img=None):
        """texture of the plane patch origin + a*u + b*v (a in [0,usize], b in [0,vsize]), bottom-left = origin.
        Returns (bgr image, known-mask). Unseen texels are magenta."""
        import cv2
        w, h = int(round(usize * ppm)), int(round(vsize * ppm))
        U, V = np.meshgrid((np.arange(w) + 0.5) / ppm, (np.arange(h)[::-1] + 0.5) / ppm)
        P = np.asarray(origin, float) + U[..., None] * np.asarray(u, float) + V[..., None] * np.asarray(v, float)
        C = np.einsum('ij,hwj->hwi', s.R, P - s.pos)
        x = s.f * C[..., 0] / C[..., 2] + s.cx; y = s.f * C[..., 1] / C[..., 2] + s.cy
        ok = (C[..., 2] > 0.05) & (x >= 0) & (x < s.W - 1) & (y >= 0) & (y < s.H - 1)
        out = cv2.remap(img, x.astype(np.float32), y.astype(np.float32), cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 0, 255))
        if mask_img is not None:
            m = cv2.remap(mask_img, x.astype(np.float32), y.astype(np.float32), cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            ok &= m > 127
        out[~ok] = (255, 0, 255); return out, ok


def load(path='cams.json'):
    return {k: Cam(v) for k, v in json.load(open(path)).items()}
