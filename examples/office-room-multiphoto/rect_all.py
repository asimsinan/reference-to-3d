"""Rectify the surfaces that carry real detail out of the photos (cams_final.json, room_final.json) into tex/.
  uv run --with numpy --with opencv-python-headless python rect_all.py
"""
import json
import os

import cv2
import numpy as np

from camlib import load

cams = load('cams_final.json')
R = json.load(open('room_final.json'))
W, L, H = R['W'], R['L'], R['H']
os.makedirs('tex', exist_ok=True)
img = {n: cv2.imread(f'{n}.jpg') for n in cams}

S = {
    # name: (photo, origin, u, v, usize, vsize, ppm)
    'window_wall': ('win', (W, 0, 0.90), (-1, 0, 0), (0, 0, 1), W, H - 0.90, 400),
    'door': ('door', (0.15, L, 0.0), (1, 0, 0), (0, 0, 1), 1.20, 2.20, 400),
    'switch': ('door', (1.55, L, 1.16), (1, 0, 0), (0, 0, 1), 0.18, 0.18, 400),
    'bookcase': ('right', (W - R['bd'], R['b0'] + R['bw'], 0), (0, -1, 0), (0, 0, 1), R['bw'], R['bh'], 400),
    'tallcab': ('right', (W - R['tcd'], R['tc0'] + R['tcw'], 0), (0, -1, 0), (0, 0, 1), R['tcw'], R['tch'], 400),
    'radiator': ('win', (2.02, 0.12, 0.15), (-1, 0, 0), (0, 0, 1), 0.60, 0.70, 400),
    'floor_r': ('right', (0.70, 4.70, 0.0), (1, 0, 0), (0, -1, 0), 1.40, 1.60, 300),
    'floor_l': ('left', (2.20, 1.20, 0.0), (-1, 0, 0), (0, 1, 0), 1.20, 2.40, 300),
    'floor_d': ('door', (0.40, 3.40, 0.0), (1, 0, 0), (0, 1, 0), 1.40, 1.90, 300),
}
for k, (n, o, u, v, us, vs, ppm) in S.items():
    out, ok = cams[n].rectify(img[n], o, u, v, us, vs, ppm)
    cv2.imwrite(f'tex/{k}.png', out)
    print(k, out.shape[1], 'x', out.shape[0], f'{100 * ok.mean():.0f}% seen')
