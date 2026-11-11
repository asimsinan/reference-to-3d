"""nosefit.py -- choose the nose corner radii from photos 9 and 13: project the dash outline (z 1.05..1.55) through
each solved camera, compare its left/right image extents per row with the photo's red dash mask."""
import json, math, numpy as np, cv2, os
os.environ['CAMS'] = 'cams34.json'
from camlib import proj
M = json.load(open('cams34.json'))['model']; hw = 0.885; Xf, ac, xo = M['Xf'], M['ac'], M['xo']
def fillet(a, c, b, r, n=20):
    a, c, b = map(np.array, (a, c, b)); d1 = (c - a) / np.linalg.norm(c - a); d2 = (b - c) / np.linalg.norm(b - c)
    th = math.acos(np.clip(d1 @ d2, -1, 1)); t = r * math.tan(th / 2); p1 = c - d1 * t; p2 = c + d2 * t
    nr = np.array([-d1[1], d1[0]]); nr = nr if d2 @ nr > 0 else -nr; ctr = p1 + nr * r
    a1 = math.atan2(*(p1 - ctr)[::-1]); a2 = math.atan2(*(p2 - ctr)[::-1])
    if a2 - a1 > math.pi: a2 -= 2 * math.pi
    if a1 - a2 > math.pi: a2 += 2 * math.pi
    return [ctr + r * np.array([math.cos(a1 + (a2 - a1) * k / n), math.sin(a1 + (a2 - a1) * k / n)]) for k in range(n + 1)]
def plan(rs, rf):
    C = [(xo - 1.0, -hw), (xo, -hw), (Xf, -ac), (Xf, ac), (xo, hw), (xo - 1.0, hw)]; out = [np.array(C[0])]
    for i in range(1, 5): out += fillet(C[i - 1], C[i], C[i + 1], rs if i in (1, 4) else rf)
    out.append(np.array(C[-1])); return np.array(out)
def redmask(k):
    im = cv2.imread(f'ref2/p{k}.png'); h = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
    m = (((h[..., 0] < 8) | (h[..., 0] > 170)) & (h[..., 1] > 110) & (h[..., 2] > 60)).astype(np.uint8)
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
R = {k: redmask(k) for k in ('9', '13')}
def score(rs, rf, show=False):
    P = plan(rs, rf); tot = []
    for k in ('9', '13'):
        for z in np.linspace(1.08, 1.52, 9):
            X = np.c_[P, np.full(len(P), z)]; uv = proj(k, X); y = int(np.median(uv[:, 1]))
            row = np.where(R[k][y, :] > 0)[0]
            # photo dash extents: the run of red that contains the projected centre
            cx = int(proj(k, np.array([[Xf, 0, z]]))[0, 0]); 
            if not len(row): continue
            seg = row[(row > cx - 400) & (row < cx + 400)]
            if not len(seg): continue
            # split into runs, take the run containing cx (or nearest)
            br = np.where(np.diff(seg) > 3)[0]; runs = np.split(seg, br + 1)
            run = min(runs, key=lambda r_: 0 if r_[0] <= cx <= r_[-1] else min(abs(r_[0] - cx), abs(r_[-1] - cx)))
            if k == '13': tot += [uv[:, 0].min() - run[0], uv[:, 0].max() - run[-1]]
            else: tot += [uv[:, 0].min() - run[0]]        # photo 9: the far (left) corner silhouette only
    tot = np.array(tot); return float(np.sqrt(np.mean(tot ** 2))), tot
best = []
for rs in (0.08, 0.15, 0.25, 0.35, 0.45, 0.55):
    for rf in (0.06, 0.12, 0.2, 0.3, 0.45, 0.6):
        try: e, _ = score(rs, rf); best.append((e, rs, rf))
        except Exception as ex: pass
best.sort(); print('best (rms px, RS, RF):', [(round(e, 1), a, b) for e, a, b in best[:6]]); print('current 0.55/0.60:', round(score(0.55, 0.60)[0], 1), ' old 0.16/0.10:', round(score(0.16, 0.10)[0], 1))
cols = {(0.16, 0.10): (255, 255, 0), (0.30, 0.20): (0, 255, 0), (0.55, 0.60): (255, 0, 255)}
outs = []
for k, box in (('13', (150, 380, 700, 800)), ('9', (120, 380, 700, 760))):
    im = cv2.imread(f'ref2/p{k}.png')
    for (rs, rf), c in cols.items():
        P = plan(rs, rf)
        for z in (1.05, 1.62, 0.84):
            uv = proj(k, np.c_[P, np.full(len(P), z)]).astype(np.int32); cv2.polylines(im, [uv], False, c, 1, cv2.LINE_AA)
    x0, y0, x1, y1 = box; outs.append(cv2.resize(im[y0:y1, x0:x1], None, fx=1.6, fy=1.6))
H = max(o.shape[0] for o in outs); cv2.imwrite('g/noseov.jpg', np.concatenate([np.pad(o, ((0, H - o.shape[0]), (0, 0), (0, 0))) for o in outs], 1))
