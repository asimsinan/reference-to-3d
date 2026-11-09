# numpy projection / rasterisation of the parametric model through the solved photo camera
import numpy as np, json, math, cv2
import secs
cam = json.load(open('cam.json'))
Rm = np.array(cam['R']); C = np.array(cam['C']); f = cam['f']; W, H = cam['W'], cam['H']

def proj(X):
    pc = (Rm @ (np.asarray(X, float) - C).T).T
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

def foil_rings(S):
    out = []
    for s in S:
        foil = airfoil(16, s['t'], s.get('camber', 0)); le = np.array(list(s['le']), float)
        up = np.array(list(s['up']), float)
        out.append(np.array([le + np.array([-xc * s['chord'], 0, 0]) + up * zc * s['chord'] for xc, zc in foil]))
    return out

def raster(rs, m=None):
    if m is None: m = np.zeros((H, W), np.uint8)
    P2 = [proj(r) for r in rs]; n = len(rs[0])
    for a, b in zip(P2[:-1], P2[1:]):
        q = np.stack([a, np.roll(a, -1, 0), np.roll(b, -1, 0), b], 1) * 4
        for qq in np.round(q).astype(np.int32):
            cv2.fillConvexPoly(m, qq, 1, lineType=cv2.LINE_8, shift=2)
    return m

def model_mask(P, parts=('fus', 'fin', 'wing', 'htail')):
    m = np.zeros((H, W), np.uint8)
    if 'fus' in parts: raster([np.array(r) for r in secs.fuselage_rings(P)], m)
    if 'fin' in parts: raster(foil_rings(secs.fin_secs(P)), m)
    for side in 'LR':
        if 'wing' in parts: raster(foil_rings(secs.wing_secs(P, side)), m)
        if 'htail' in parts: raster(foil_rings(secs.htail_secs(P, side)), m)
    return m

def top_edge(m, x, y0=0, y1=None):
    c = np.where(m[y0:y1, x])[0]; return y0 + c.min() if len(c) else None
def bot_edge(m, x, y0=0, y1=None):
    c = np.where(m[y0:y1, x])[0]; return y0 + c.max() if len(c) else None
def left_edge(m, y, x0=0, x1=None):
    c = np.where(m[y, x0:x1])[0]; return x0 + c.min() if len(c) else None
def right_edge(m, y, x0=0, x1=None):
    c = np.where(m[y, x0:x1])[0]; return x0 + c.max() if len(c) else None
