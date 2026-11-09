# Equirectangular environment from the photo's own sky and horizon. The photo's sky spans only ~1 deg of real
# elevation (a long lens), so its vertical gradient is used as the sky's profile: horizon row -> 0 deg, top row -> 55 deg.
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2, numpy as np
ref = cv2.imread('ref.jpg').astype(np.float32)
plane = cv2.dilate((cv2.imread('out_match.png', cv2.IMREAD_UNCHANGED)[..., 3] > 0).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
rows = []
for r in range(0, 470):
    m = ~plane[r]; rows.append(np.median(ref[r][m], 0))
rows = (np.clip(np.array(rows), 0, 255) / 255) ** 2.2
HZ = 326     # sky meets the distant land
EW, EH = 2048, 1024
E = np.zeros((EH, EW, 3), np.float32)
for i in range(EH):
    e = 90 - (i + 0.5) / EH * 180
    if e >= 0:
        t = min(e / 55, 1) ** 0.8; r = HZ * (1 - t)
        c = rows[int(r)]
        if e > 55: c = rows[0] * (1 - 0.25 * (e - 55) / 35)
    elif e > -4:
        r = HZ + (-e / 4) * (469 - HZ); c = rows[min(int(r), 469)]
    else:
        c = rows[469]
    E[i] = c
cv2.imwrite('tex/env.exr', E)
cv2.imwrite('env_prev.jpg', np.clip(E ** (1 / 2.2) * 255, 0, 255).astype(np.uint8)[::4, ::4])
# camera env: the photo's sky and land at their true elevations through the solved camera
import json
cam = json.load(open('cam.json')); Rm = np.array(cam['R']); f = cam['f']; W, H = cam['W'], cam['H']
vv, uu = np.mgrid[0:H, 0:W]
d = np.stack([(uu - W / 2) / f, (vv - H / 2) / f, np.ones_like(uu, float)], -1) @ Rm
el = np.degrees(np.arcsin(d[..., 2] / np.linalg.norm(d, axis=-1)))
ok = ~plane & (vv < 640)
lin_ref = (ref / 255) ** 2.2
bins = np.arange(-8, 3, 0.05); cen = (bins[:-1] + bins[1:]) / 2; cs = []
for a, b in zip(bins[:-1], bins[1:]):
    mm = ok & (el >= a) & (el < b); cs.append(np.median(lin_ref[mm], 0) if mm.sum() > 20 else [np.nan] * 3)
cs = np.array(cs); g = ~np.isnan(cs[:, 0])
E2 = np.zeros_like(E)
for i in range(EH):
    e = 90 - (i + 0.5) / EH * 180
    E2[i] = [np.interp(e, cen[g], cs[g][:, k]) for k in range(3)]
cv2.imwrite('tex/env_cam.exr', E2.astype(np.float32))
