# Fit sun colour and the low/high sky colours (linear in the passes) to the photo's plane pixels and ground.
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2, numpy as np, json, sys
from scipy.optimize import least_squares
PASSES = ['sunpass', 'skylow', 'skyhigh'] + (['fillpass'] if len(sys.argv) > 2 else [])
FILLFILE = sys.argv[2] if len(sys.argv) > 2 else None
I = [cv2.imread(FILLFILE if p == 'fillpass' else 'pass_%s.exr' % p, cv2.IMREAD_UNCHANGED)[..., :3] for p in PASSES]
NP = len(PASSES)
h, w = I[0].shape[:2]
ref = cv2.resize(cv2.imread('ref.jpg'), (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
ref = np.where(ref <= 0.04045, ref / 12.92, ((ref + 0.055) / 1.055) ** 2.4)
alpha = cv2.resize(cv2.imread('out_match.png', cv2.IMREAD_UNCHANGED)[..., 3], (w, h)) > 250
plane = cv2.erode(alpha.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
grd = np.zeros((h, w), bool); grd[int(h * 0.62):, :] = True
grd &= ~(cv2.dilate(alpha.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
def blocks(img, m, b=4):
    hh, ww = (h // b) * b, (w // b) * b
    X = img[:hh, :ww].reshape(hh // b, b, ww // b, b, -1).mean((1, 3)); M = m[:hh, :ww].reshape(hh // b, b, ww // b, b).all((1, 3))
    return X[M]
idi = cv2.resize(cv2.imread('out_id.png', cv2.IMREAD_UNCHANGED), (w, h), interpolation=cv2.INTER_NEAREST)
key = (idi[..., 0] // 64) * 16 + (idi[..., 1] // 64) * 4 + idi[..., 2] // 64
P = [blocks(x, plane) for x in I]; Pr = blocks(ref, plane); ok = Pr.max(1) < 0.95
kb = blocks(key[..., None].astype(np.float32), plane)[:, 0].round().astype(int)
cnt = {k: (kb == k).sum() for k in np.unique(kb)}
pw = np.array([1.0 / np.sqrt(cnt[k]) for k in kb]); pw = pw / pw[ok].mean()
G = [blocks(x, grd) for x in I]; Gr = blocks(ref, grd)
cal = json.load(open('calib.json')) if os.path.exists('calib.json') else {}
wg = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
def res(x):
    c = x.reshape(NP, 3)
    rp = (sum(P[k][ok] * c[k] for k in range(NP)) - Pr[ok]) * pw[ok][:, None] / np.sqrt(ok.sum())
    rg = (sum(G[k] * c[k] for k in range(NP)) - Gr) / np.sqrt(len(Gr)) * wg
    return np.r_[rp.ravel(), rg.ravel()]
FIXSUN = os.environ.get('FIXSUN')
lo_b = np.zeros(NP * 3); hi_b = np.full(NP * 3, np.inf); x0 = np.ones(NP * 3)
if FIXSUN:
    sv = (cal['sun'] * np.array(cal['sun_color']))[::-1]; lo_b[:3] = sv - 1e-6; hi_b[:3] = sv + 1e-6; x0[:3] = sv
sol = least_squares(res, x0, bounds=(lo_b, hi_b)); x = sol.x.reshape(NP, 3)[:, ::-1]
sun, lo, hi = x[:3]
rms = np.sqrt(np.mean(sol.fun ** 2))
print('sun', sun.round(3), 'sky_low', lo.round(3), 'sky_high', hi.round(3), 'fill', x[3].round(3) if NP > 3 else '-', 'rms %.6f' % rms)
if len(sys.argv) > 3 and sys.argv[3] == 'dry': sys.exit(0)
if NP > 3: cal['fill'] = x[3].tolist(); cal['fill_el'], cal['fill_az'] = map(float, os.path.basename(FILLFILE).split('_')[1:3])
cal.update(sun=float(sun.max()), sun_color=(sun / max(sun.max(), 1e-6)).tolist(), sky_low=lo.tolist(), sky_high=hi.tolist())
json.dump(cal, open('calib.json', 'w'), indent=1)
