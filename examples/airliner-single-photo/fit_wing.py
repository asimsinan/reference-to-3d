# Fit wing planform/dihedral/winglet params to the photo's wing edges through the solved camera.
import numpy as np, json, math, cv2, copy
from scipy.optimize import least_squares
import params as PM, secs
cam = json.load(open('cam.json'))
Rm = np.array(cam['R']); C = np.array(cam['C']); f = cam['f']; W, H = cam['W'], cam['H']
def proj(X):
    pc = (Rm @ (np.asarray(X) - C).T).T
    return np.c_[f * pc[:, 0] / pc[:, 2] + W / 2, f * pc[:, 1] / pc[:, 2] + H / 2]
def airfoil(n=16, t=0.12, camber=0.02):
    up, lo = [], []
    for i in range(n + 1):
        b = math.pi * i / n; x = (1 - math.cos(b)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        m, p = camber, 0.4
        yc = m / p ** 2 * (2 * p * x - x * x) if x < p else m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x * x)
        up.append((x, yc + yt)); lo.append((x, yc - yt))
    return list(reversed(up)) + lo[1:-1]
def rings(S):
    out = []
    for s in S:
        foil = airfoil(16, s['t'], s.get('camber', 0)); le = np.array(list(s['le']), float); up = np.array(list(s['up']), float)
        out.append(np.array([le + np.array([-xc * s['chord'], 0, 0]) + up * zc * s['chord'] for xc, zc in foil]))
    return out
def raster(rs):
    m = np.zeros((H, W), np.uint8)
    P2 = [proj(r) for r in rs]; n = len(rs[0])
    for a, b in zip(P2[:-1], P2[1:]):
        for i in range(n):
            j = (i + 1) % n
            q = np.array([a[i], a[j], b[j], b[i]]) * 4
            cv2.fillConvexPoly(m, np.round(q).astype(np.int32), 1, lineType=cv2.LINE_8, shift=2)
    return m
# --- targets
g = cv2.cvtColor(cv2.imread('ref.jpg'), cv2.COLOR_BGR2GRAY).astype(float)
near_top, near_bot = [], []
for x in range(1180, 1601, 20):
    col = g[620:760, x]; b = np.where(col > 150)[0]
    if len(b): near_top.append((x, 620 + b.min())); near_bot.append((x, 620 + b.max() + 3))
far_top = [(160, 583), (200, 600), (240, 610), (280, 617)]
far_bot = [(120, 604), (160, 618), (200, 633), (240, 647)]
pts = {'L': (near_top, near_bot), 'R': (far_top, far_bot)}
tips = {'L': (1712, 518), 'R': (132, 458)}
names = ['z_root', 'dihedral', 's_le_glove', 'sweep_le', 'c_tip', 's_te_kink', 'wl_len', 'wl_cant', 'wl_sweep', 'wl_radius', 'y_tip', 't_root', 't_tip']
P0 = PM.params()
def setp(v):
    P = copy.deepcopy(P0)
    for n, x in zip(names, v): P['wing'][n] = x
    return P
def res(v, verbose=False):
    P = setp(v); r = []
    for side in 'LR':
        S = secs.wing_secs(P, side); rs = rings(S); m = raster(rs)
        top, bot = pts[side]
        for x, y in top:
            c = np.where(m[:, x])[0]; r.append((c.min() - y) if len(c) else 40)
        for x, y in bot:
            c = np.where(m[:, x])[0]; r.append((c.max() - y) if len(c) else 40)
        # winglet tip: top-most projected point of the last ring
        tp = proj(rs[-1]); k = np.argmin(tp[:, 1]); r += list((tp.mean(0) - tips[side]))
    r = np.array(r, float)
    if verbose: print(np.round(r, 1))
    return r
v0 = np.array([P0['wing'][n] for n in names], float)
lo = v0 - np.array([1.5, 4, 2, 6, 0.6, 2, 1.0, 10, 25, 0.6, 1.5, 0.06, 0.05]); hi = v0 + np.array([1.5, 4, 2, 6, 0.6, 2, 1.5, 25, 15, 0.6, 1.5, 0.03, 0.03])
print('start'); res(v0, True)
s = least_squares(res, v0, bounds=(lo, hi), diff_step=0.02, max_nfev=300)
print('end rms', np.sqrt(np.mean(s.fun ** 2))); res(s.x, True)
out = dict(zip(names, map(float, s.x))); print(out)
T = json.load(open('tweaks.json')) if __import__('os').path.exists('tweaks.json') else {}
T.setdefault('wing', {}).update(out); json.dump(T, open('tweaks.json', 'w'), indent=1)
