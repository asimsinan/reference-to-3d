# Sun direction from the plane's shadow on the ground: project dense surface points (baked P maps) along the sun
# onto z=0, then into the photo; compare with the photo's shadow mask (dark ground).
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2, numpy as np, json, glob
cam = json.load(open('cam.json')); Rm = np.array(cam['R']); C = np.array(cam['C']); f = cam['f']; W, H = cam['W'], cam['H']
pts = []
for p in glob.glob('bake/*_P.exr'):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED); a = im[..., 3] > 0.5
    P = im[..., [2, 1, 0]][a]; pts.append(P[::7])
pts = np.concatenate(pts); pts = pts[pts[:, 2] > 0.05]
print('points', len(pts))
def proj(X):
    pc = (X - C) @ Rm.T; return np.c_[f * pc[:, 0] / pc[:, 2] + W / 2, f * pc[:, 1] / pc[:, 2] + H / 2]
ref = cv2.imread('ref.jpg'); lab = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB)
plane = cv2.imread('out_match.png', cv2.IMREAD_UNCHANGED)[..., 3] > 10
L = cv2.GaussianBlur(lab[..., 0].astype(float), (0, 0), 3)
ground = np.zeros((H, W), bool); ground[640:, :] = True; ground &= ~cv2.dilate(plane.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
sh = (L < 125) & ground
cv2.imwrite('shadow_ref.png', sh.astype(np.uint8) * 255)
print('shadow frac in ground', sh[ground].mean())
best = None
for el in np.arange(4, 30, 1.0):
    for az in np.arange(0, 360, 3.0):
        d = np.array([np.cos(np.radians(el)) * np.cos(np.radians(az)), np.cos(np.radians(el)) * np.sin(np.radians(az)), np.sin(np.radians(el))])
        g = pts - np.outer(pts[:, 2] / d[2], d)
        uv = proj(g); ok = (uv[:, 0] >= 0) & (uv[:, 0] < W) & (uv[:, 1] >= 0) & (uv[:, 1] < H)
        m = np.zeros((H, W), np.uint8); ui = uv[ok].astype(int); m[ui[:, 1], ui[:, 0]] = 1
        m = cv2.morphologyEx(cv2.dilate(m, np.ones((5, 5), np.uint8)), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
        m &= ground
        iou = (m & sh).sum() / max((m | sh).sum(), 1)
        if best is None or iou > best[0]: best = (iou, el, az, m)
print('best IoU %.3f el %.1f az %.1f' % best[:3])
json.dump({'el': best[1], 'az': best[2], 'iou': best[0]}, open('sun.json', 'w'))
ov = ref.copy(); ov[best[3] & ~sh] = (0, 0, 255); ov[sh & ~best[3]] = (255, 0, 0); ov[best[3] & sh] = (0, 255, 0)
cv2.imwrite('sun_ov.jpg', cv2.addWeighted(ref, 0.5, ov, 0.5, 0))
