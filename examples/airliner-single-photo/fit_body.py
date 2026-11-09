# Fit fuselage nose/tail, fin and stabiliser parameters to the photo silhouette (mask2) through the photo camera.
import numpy as np, json, copy, os, cv2, sys
from scipy.optimize import least_squares
from scipy.signal import medfilt
import params as PM, fitlib as FL

M = cv2.imread('mask2.png', 0) > 0
g = cv2.cvtColor(cv2.imread('ref.jpg'), cv2.COLOR_BGR2GRAY).astype(float)
T = []  # (kind, coord, target, weight)
cols = list(range(110, 1206, 6))
tops = medfilt(np.array([FL.top_edge(M, x, 100, 900) or 0 for x in cols], float), 5)
for x, t in zip(cols, tops):
    if 545 <= x <= 575 or 690 <= x <= 715 or 780 <= x <= 800: continue  # antennas
    T.append(('top', x, t, 1.0))
for y in range(690, 871, 6): T.append(('left', y, FL.left_edge(M, y, 60, 400), 1.0))
for x in range(112, 196, 6): T.append(('bot', x, FL.bot_edge(M, x, 700, 880), 1.0))
for x, y in [(300, 872), (350, 865), (400, 857), (450, 849), (500, 842), (550, 836)]: T.append(('bot', x, y, 1.0))
for y, x in [(512,1196),(520,1199),(528,1199)]: T.append(('right', y, x, 1.5))
for y, x in [(536,1196),(544,1190)]: T.append(('rightf', y, x, 1.5))
for y, x in [(570,1155),(590,1146),(610,1138),(640,1128),(670,1115)]: T.append(('rightf', y, x, 1.2))
for y in range(160, 505, 12): T.append(('right', y, FL.right_edge(M, y, 1100, 1300), 1.0))
for y in range(156, 500, 12): T.append(('leftfin', y, FL.left_edge(M, y, 950, 1250), 1.0))
# near stabiliser: bright band edges
for x in range(1250, 1501, 25):
    col = g[480:600, x]; b = np.where(col > 150)[0]
    if len(b): T.append(('htop', x, 480 + b.min(), 1.0)); T.append(('hbot', x, 480 + b.max() + 2, 1.0))

NAMES = [('nose_len', 1.5), ('nose_pow', 1.0), ('nose_top_pow', 1.0), ('nose_bot_pow', 1.5), ('nose_tip_dz', 0.5),
         ('zc', 0.4), ('fus_b', 0.25), ('L', 1.5), ('tail_top_start', 3), ('tail_top_pow', 0.8), ('tail_bot_start', 3),
         ('tail_bot_pow', 0.6), ('tail_end_z', 1.0), ('tail_end_h', 0.25), ('tail_w_start', 3),
         ('fin.s_le_root', 2), ('fin.sweep_le', 6), ('fin.c_root', 1.5), ('fin.dorsal_s0', 3), ('fin.dorsal_h', 1.0), ('fin.c_top', 0.5),
         ('htail.z_root', 1.0), ('htail.dihedral', 4), ('htail.s_le_root', 2), ('htail.sweep_le', 6),
         ('htail.c_root', 1.2), ('htail.c_tip', 0.5)]
P0 = PM.params()
V0 = None
def get(P, n):
    return P[n.split('.')[0]][n.split('.')[1]] if '.' in n else P[n]
SIG = np.array([s for _, s in NAMES])
def setp(u):
    v = V0 + (u - 10.0) * SIG
    P = copy.deepcopy(P0)
    for (n, _), x in zip(NAMES, v):
        if '.' in n: a, b = n.split('.'); P[a][b] = x
        else: P[n] = x
    P['fin']['z_root'] = P['zc'] + P['fus_b'] - 0.25
    return P
def res(u, verbose=False):
    P = setp(u)
    m = FL.model_mask(P)
    fm = np.zeros_like(m); FL.raster([np.array(r) for r in FL.secs.fuselage_rings(P)], fm)
    hm = np.zeros_like(m); FL.raster(FL.foil_rings(FL.secs.htail_secs(P, 'L')), hm)
    r = []
    for k, c, t, w in T:
        if t is None: continue
        if k == 'top': e = FL.top_edge(m, c, 100, 900)
        elif k == 'bot': e = FL.bot_edge(m, c, 600, 900)
        elif k == 'botr': e = FL.bot_edge(m, c, 520, 700)
        elif k == 'left': e = FL.left_edge(m, c, 40, 400)
        elif k == 'right': e = FL.right_edge(m, c, 1100, 1300 if c < 505 else 1240)
        elif k == 'leftfin': e = FL.left_edge(m, c, 950, 1250)
        elif k == 'rightf': e = FL.right_edge(fm, c, 1000, 1300)
        elif k == 'htop': e = FL.top_edge(hm, c, 470, 620)
        elif k == 'hbot': e = FL.bot_edge(hm, c, 470, 620)
        r.append(w * ((e - t) if e is not None else 30.0))
    r = np.array(r, float)
    pri = (u - 10.0) * 2.0
    if verbose:
        ks = [k for k, c, t, w in T if t is not None]
        for kk in sorted(set(ks)):
            rr = r[[i for i, k in enumerate(ks) if k == kk]]
            print(f'  {kk:6s} n={len(rr):3d} mean {rr.mean():6.1f}  rms {np.sqrt((rr**2).mean()):5.1f}')
    return np.r_[r, pri]
v0 = np.array([get(P0, n) for n, _ in NAMES], float); V0 = v0
print('start'); res(np.full(len(v0), 10.0), True)
s = least_squares(res, np.full(len(v0), 10.0), diff_step=0.02, loss='soft_l1', f_scale=4.0, max_nfev=int(sys.argv[1]) if len(sys.argv) > 1 else 60)
print('end', s.status, s.message, s.nfev, np.abs(s.jac).sum(0).round(1)); res(s.x, True)
P = setp(s.x); s.x = V0 + (s.x - 10.0) * SIG
Tw = json.load(open('tweaks.json')) if os.path.exists('tweaks.json') else {}
for (n, _), x in zip(NAMES, s.x):
    if '.' in n: a, b = n.split('.'); Tw.setdefault(a, {})[b] = float(x)
    else: Tw[n] = float(x)
Tw.setdefault('fin', {})['z_root'] = P['fin']['z_root']
json.dump(Tw, open('tweaks.json', 'w'), indent=1)
for (n, _), x, x0 in zip(NAMES, s.x, v0): print(f'{n:18s} {x0:7.2f} -> {x:7.2f}')
