# Per-texel albedo calibration: the photo / final-render ratio (linear, low frequency) projected back onto each
# part's UVs and folded into a gain map that albedo.py multiplies in. Clamped so the paint stays paint.
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2, numpy as np, json, types
src = open('texbuild.py').read().split("if __name__ != '__main__'")[0]
T = types.ModuleType('tb'); exec(src, T.__dict__)
def s2l(x): x = np.clip(x / 255.0, 0, 1); return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
ref = s2l(cv2.imread('ref.jpg').astype(np.float32)); ren = s2l(cv2.imread('out_final.png').astype(np.float32))
alpha = cv2.erode((cv2.imread('out_match.png', cv2.IMREAD_UNCHANGED)[..., 3] > 250).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32)
num = cv2.GaussianBlur(ref * alpha[..., None], (0, 0), 5); den = cv2.GaussianBlur(ren * alpha[..., None], (0, 0), 5)
ratio = np.where(alpha[..., None] > 0, num / np.maximum(den, 1e-4), 1.0)
ratio = np.clip(ratio, 0.5, 2.0)
T.ref = (ratio * 100).astype(np.float32)      # sample the ratio image instead of the photo (x100 for precision)
for g, members in T.GROUPS.items():
    if g in ('spinner',): continue
    best = None
    for name, fn, pri in members:
        col, w, A = T.sample_member(name)
        if fn is not None: col = T.remap_v(col, fn); w = T.remap_v(w, fn)
        w = w * pri
        if best is None: best = [col, w]
        else:
            take = w > best[1]; best[0][take] = col[take]; best[1][take] = w[take]
    r, w = best[0] / 100.0, best[1]
    seen = (w > (0.02 if g in ('htail', 'wing') else 0.15)).astype(np.float32)
    hh, ww = seen.shape; sig = max(hh, ww) / 200.0
    sm, dn = T.smooth_valid(np.log(np.maximum(r, 1e-3)), seen, sig)
    lg = np.where(dn[..., None] > 0.05, sm, 0.0) * np.clip(dn * 2, 0, 1)[..., None]
    gp = 'tex/%s_gain.npy' % g
    old = np.load(gp) if os.path.exists(gp) else np.ones((hh, ww, 3), np.float32)
    new = np.clip(old * np.exp(lg), 0.55, 1.8).astype(np.float32)
    np.save(gp, new)
    print(g, 'gain mean %.3f  p5 %.3f p95 %.3f' % (new.mean(), np.percentile(new, 5), np.percentile(new, 95)))
