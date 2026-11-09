import json, numpy as np, cv2
from scipy.optimize import least_squares
R = json.load(open('room_final.json')); L, H = R['L'], R['H']
FR = [((R['dx1'], 2.12), (600, 240)), ((R['dx0'], 2.12), (1444, 250)), ((R['dx1'], 0), (597, 1885)), ((R['dx0'], 0), (1256, 1895))]
FAR = [((1.23, 0.03, 2.29), (744, 690)), ((1.73, 0.03, 2.29), (700, 690)), ((1.48, 0, H), (722, 610)),
       ((0.98, 0.42, 1.10), (755, 887)), ((1.51, 2.50, 0.42), (661, 1049))]
def res(q):
    rv, tv, f, t = q[:3], q[3:6], q[6], q[7]; K = np.array([[f, 0, 768], [0, f, 1024], [0, 0, 1.]])
    P = np.array([[a, L + t, c] for (a, c), _ in FR] + [list(p) for p, _ in FAR], float)
    o = np.array([o for _, o in FR] + [o for _, o in FAR], float)
    pr, _ = cv2.projectPoints(P, rv, tv, K, None); return np.r_[(pr.reshape(-1, 2) - o).ravel(), (t - 0.30) / 0.01]
best = None
for f0 in (650, 770, 900, 1100):
    K0 = np.array([[f0, 0, 768], [0, f0, 1024], [0, 0, 1.]])
    P4 = np.array([[a, L + 0.25, c] for (a, c), _ in FR], float); p4 = np.array([o for _, o in FR], float)
    _, rv0, tv0 = cv2.solvePnP(P4, p4, K0, None, flags=cv2.SOLVEPNP_IPPE)
    s = least_squares(res, np.r_[rv0.ravel(), tv0.ravel(), f0, 0.25], loss='soft_l1', f_scale=8,
                      bounds=([-np.inf] * 6 + [450, 0.1], [np.inf] * 6 + [2000, 0.45]))
    if best is None or s.cost < best.cost: best = s
q = best.x; Rm = cv2.Rodrigues(q[:3])[0]; pos = -Rm.T @ q[3:6]
print('f %.0f t %.3f pos %s' % (q[6], q[7], np.round(pos, 2)), np.round(np.linalg.norm(res(q)[:-1].reshape(-1, 2), axis=1), 1))
C = json.load(open('cams_final.json')); C['corridor'] = dict(pos=pos.tolist(), R=Rm.tolist(), f=float(q[6]), cx=768, cy=1024, W=1536, H=2048)
json.dump(C, open('cams_final.json', 'w'), indent=1)
Rj = json.load(open('room_final.json')); Rj['t_wall'] = float(q[7]); json.dump(Rj, open('room_final.json', 'w'), indent=1)
