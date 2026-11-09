# Camera solve for the 737-800 photo. Object frame: +X front, +Y aircraft's left, +Z up, metres.
# Station s = metres aft of the nose tip; X = X0 - s with X0 = 19.735 (length 39.47 centred).
import numpy as np, json, cv2
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R

W, H = 1770, 1187
X0 = 19.735
# image points (px), marked on zoomed grids
P = {
 'ng':   (288, 975),   # nose gear ground contact (centre of pair)
 'mg_r': (640, 842),   # right (far) main gear contact
 'mg_l': (948, 862),   # left (near) main gear contact
 'wt_l': (1712, 518),  # left winglet tip (top)
 'wt_r': (132, 458),   # right winglet tip (top)
 'hs_l': (1515, 509),  # left stabiliser tip
 'hs_r': (877, 492),   # right stabiliser tip
 'fin_le': (1157, 150),# fin top, leading corner
 'fin_te': (1208, 148),# fin top, trailing corner
 'eng_l': (842, 820),  # left engine intake ring centre
}
# shape params: name, prior, sigma (m)
SP = [('s_ng',4.9,0.6),('s_mg',20.6,0.8),('s_wt',23.3,1.2),('z_wt',5.8,0.8),('y_wt',17.6,0.4),
      ('s_hs',36.3,1.0),('z_hs',4.3,0.6),('s_fin',35.5,1.0),('c_fin',2.0,0.5),('s_e',12.0,1.0),
      ('z_e',1.55,0.3),('y_e',4.9,0.3),('trk',2.86,0.4),('zc',3.0,0.4)]
def pts3(q):
    d = dict(zip([n for n,_,_ in SP], q))
    X = lambda s: X0 - s
    return {
     'ng': (X(d['s_ng']),0,0), 'mg_r': (X(d['s_mg']),-d['trk'],0), 'mg_l': (X(d['s_mg']),d['trk'],0),
     'wt_l': (X(d['s_wt']),d['y_wt'],d['z_wt']), 'wt_r': (X(d['s_wt']),-d['y_wt'],d['z_wt']),
     'hs_l': (X(d['s_hs']),7.17,d['z_hs']), 'hs_r': (X(d['s_hs']),-7.17,d['z_hs']),
     'fin_le': (X(d['s_fin']),0,12.55), 'fin_te': (X(d['s_fin']+d['c_fin']),0,12.55),
     'eng_l': (X(d['s_e']),d['y_e'],d['z_e'])}
names = list(P)
def proj(cam, Xw):
    rv, t, f = cam[:3], cam[3:6], cam[6]
    Rm = R.from_rotvec(rv).as_matrix()
    pc = (Rm @ np.asarray(Xw).T).T + t
    return np.c_[f*pc[:,0]/pc[:,2] + W/2, f*pc[:,1]/pc[:,2] + H/2]
K = 6.0  # px per sigma of prior
import json as _j
E = _j.load(open('edges.json'))
TOP = np.array([p for p in E['top'] if p[0] <= 870]); BOT = np.array(E['bottom'],float)
TH = np.linspace(0, 2*np.pi, 721)
def sil(cam, q):
    d = dict(zip([n for n,_,_ in SP], q))
    Rm = R.from_rotvec(cam[:3]).as_matrix(); C = -Rm.T @ cam[3:6]
    out = []
    for s in np.arange(7, 27, 2.0):
        X = X0 - s; a, b = 1.88, 2.0
        P3 = np.c_[np.full_like(TH, X), a*np.cos(TH), d['zc'] + b*np.sin(TH)]
        n = np.c_[np.zeros_like(TH), np.cos(TH)/a, np.sin(TH)/b]
        f = np.sum(n*(P3 - C), 1)
        idx = np.where(np.sign(f[:-1]) != np.sign(f[1:]))[0]
        pts = []
        for i in idx:
            w = f[i]/(f[i]-f[i+1]); pts.append(P3[i]*(1-w) + P3[i+1]*w)
        if len(pts) < 2:
            out += [50, 50]; continue
        pts = np.array(pts); uv = proj(cam, pts)
        hi = uv[np.argmin(uv[:,1])]; lo = uv[np.argmax(uv[:,1])]
        out.append(hi[1] - np.interp(hi[0], TOP[:,0], TOP[:,1]) if TOP[0,0] <= hi[0] <= TOP[-1,0] else 0.0)
        out.append(lo[1] - np.interp(lo[0], BOT[:,0], BOT[:,1]) if BOT[0,0] <= lo[0] <= BOT[-1,0] else 0.0)
    return np.array(out)*0.7
def res(v):
    cam, q = v[:7], v[7:]
    p3 = pts3(q); X3 = np.array([p3[n] for n in names])
    r = (proj(cam, X3) - np.array([P[n] for n in names])).ravel()
    pr = [(qi-m)/s*K for qi,(_,m,s) in zip(q,SP)]
    return np.r_[r, pr, sil(cam, q)]
best = None
q0 = [m for _,m,_ in SP]
for yaw in (15, 30, 45, 60):
  for pitch in (5, 10, 18):
    for dist in (40, 70):
      # camera looking toward object centre from direction yaw (deg, from +X towards +Y), elevated by pitch
      a, e = np.radians(yaw), np.radians(pitch)
      C = dist*np.array([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)]) + [0,0,3]
      fwd = (np.array([0,0,3]) - C); fwd /= np.linalg.norm(fwd)
      right = np.cross(fwd, [0,0,1]); right /= np.linalg.norm(right)
      down = np.cross(fwd, right)
      Rm = np.array([right, down, fwd])
      rv = R.from_matrix(Rm).as_rotvec(); t = -Rm @ C
      for f in (1500, 3000):
        v0 = np.r_[rv, t, f, q0]
        try:
          s = least_squares(res, v0, method='lm', max_nfev=4000)
        except Exception: continue
        pass
        if (proj(s.x[:7], np.array([pts3(s.x[7:])[n] for n in names]))[:,0] > -1e9).all():
          pc = (R.from_rotvec(s.x[:3]).as_matrix() @ np.array([pts3(s.x[7:])[n] for n in names]).T).T + s.x[3:6]
          if (pc[:,2] <= 0).any() or s.x[6] <= 0: continue
        c = np.sum(s.fun**2)
        if best is None or c < best[0]: best = (c, s.x)
c, v = best
cam, q = v[:7], v[7:]
p3 = pts3(q); X3 = np.array([p3[n] for n in names]); pp = proj(cam, X3)
for n, a in zip(names, pp): print(f'{n:7s} img {P[n]}  model ({a[0]:.1f},{a[1]:.1f})  err {np.hypot(*(a-P[n])):.1f}')
rms = np.sqrt(np.mean(np.sum((pp-np.array([P[n] for n in names]))**2,1)))
Rm = R.from_rotvec(cam[:3]).as_matrix(); C = -Rm.T @ cam[3:6]
print('rms px', rms, 'f', cam[6], 'cam centre', C, 'dist', np.linalg.norm(C))
for (n,m,s_),qi in zip(SP,q): print(f'  {n} {qi:.2f} (prior {m})')
json.dump({'rvec':cam[:3].tolist(),'t':cam[3:6].tolist(),'f':cam[6],'W':W,'H':H,'C':C.tolist(),
           'R':Rm.tolist(),'shape':dict(zip([n for n,_,_ in SP], q.tolist()))}, open('cam.json','w'), indent=1)
