# cmp.py RENDER.png OUT.jpg : composite render over the photo, per-region colour stats, 2x2 sheet
import cv2, numpy as np, sys, json
ref = cv2.imread('ref.jpg').astype(np.float32); rr = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED).astype(np.float32)
a = rr[..., 3:] / 255.0; comp = rr[..., :3] * a + ref * (1 - a)
m = cv2.erode((rr[..., 3] > 250).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
d = np.abs(comp - ref).mean(2)
lab_r = cv2.cvtColor(ref.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(float); lab_c = cv2.cvtColor(comp.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(float)
print('model px %d  mean |diff| %.1f  median %.1f' % (m.sum(), d[m].mean(), np.median(d[m])))
REG = {'nose': (100, 640, 340, 880), 'mid_fus': (430, 560, 760, 760), 'aft_fus': (800, 520, 1100, 680),
       'fin': (1080, 160, 1200, 500), 'near_wing': (1000, 660, 1620, 720), 'far_wing': (100, 470, 300, 640),
       'engine': (790, 750, 980, 870), 'htail_near': (1200, 505, 1510, 560), 'nose_gear': (255, 880, 330, 975)}
res = {}
for k, (x0, y0, x1, y1) in REG.items():
    mm = m[y0:y1, x0:x1]
    if mm.sum() < 50: continue
    L1 = lab_r[y0:y1, x0:x1, 0][mm]; L2 = lab_c[y0:y1, x0:x1, 0][mm]
    c1 = ref[y0:y1, x0:x1][mm].mean(0)[::-1]; c2 = comp[y0:y1, x0:x1][mm].mean(0)[::-1]
    res[k] = dict(diff=float(d[y0:y1, x0:x1][mm].mean()), ref_rgb=c1.round(0).tolist(), mod_rgb=c2.round(0).tolist(),
                  ref_L_p5_p95=[float(np.percentile(L1, 5)), float(np.percentile(L1, 95))],
                  mod_L_p5_p95=[float(np.percentile(L2, 5)), float(np.percentile(L2, 95))], ref_Lsd=float(L1.std()), mod_Lsd=float(L2.std()))
    r = res[k]; print('%-11s diff %5.1f  rgb ref %s mod %s  L p5/p95 ref %.0f/%.0f mod %.0f/%.0f  Lsd %.1f/%.1f' % (k, r['diff'], r['ref_rgb'], r['mod_rgb'], *r['ref_L_p5_p95'], *r['mod_L_p5_p95'], r['ref_Lsd'], r['mod_Lsd']))
json.dump(res, open(sys.argv[2] + '.json', 'w'), indent=1)
top = np.hstack([ref, comp]); dd = np.clip(np.abs(comp - ref) * 3, 0, 255)
ov = ref.copy(); e = cv2.Canny((rr[..., 3] > 127).astype(np.uint8) * 255, 50, 150) > 0; ov[e] = (0, 255, 255)
bot = np.hstack([ov, dd]); sheet = np.vstack([top, bot])
cv2.imwrite(sys.argv[2], cv2.resize(sheet, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
cv2.imwrite(sys.argv[2].replace('.jpg', '_comp.jpg'), comp)
