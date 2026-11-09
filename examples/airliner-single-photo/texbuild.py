# Project the photo onto every part's UV texels the camera sees; merge mirrored partners; write
#   tex/<group>_photo.png  (photo colour, unseen filled)       -> "match" build
#   tex/<group>_seen.png   (weight of the best view, 0 unseen)
#   tex/<group>_ratio.png  (photo / its smooth shading: detail with the light divided out, 1.0 = paint)
import os
os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2, numpy as np, json

cam = json.load(open('cam.json'))
Rm = np.array(cam['R']); C = np.array(cam['C']); f = cam['f']; W, H = cam['W'], cam['H']
ref = cv2.imread('ref.jpg').astype(np.float32)
dep = cv2.imread('bake/depth.exr', cv2.IMREAD_UNCHANGED)
dz = dep[..., 2] if dep.ndim == 3 else dep        # BGR(A): R channel holds depth
alpha = dep[..., 3] if dep.shape[-1] == 4 else (dz > 0)
inside = cv2.erode((alpha > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0

def load(name, a):
    im = cv2.imread('bake/%s_%s.exr' % (name, a), cv2.IMREAD_UNCHANGED)
    return im[..., [2, 1, 0]], im[..., 3]

def sample_member(name):
    Pp, A = load(name, 'P'); Nn, _ = load(name, 'N')
    pc = (Pp.reshape(-1, 3) - C) @ Rm.T
    z = pc[:, 2]; u = f * pc[:, 0] / z + W / 2; v = f * pc[:, 1] / z + H / 2
    hh, ww = A.shape
    ok = (A.reshape(-1) > 0.5) & (z > 1) & (u >= 1) & (u < W - 2) & (v >= 1) & (v < H - 2)
    ui = np.clip(np.round(u).astype(int), 0, W - 1); vi = np.clip(np.round(v).astype(int), 0, H - 1)
    zb = dz[vi, ui]
    vis = ok & inside[vi, ui] & (np.abs(zb - z) < 0.25 + 0.002 * z)
    view = C - Pp.reshape(-1, 3); view /= np.linalg.norm(view, axis=1, keepdims=True) + 1e-9
    n = Nn.reshape(-1, 3); n = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    cos = np.sum(n * view, 1)
    if name.startswith('duct'): cos = np.abs(cos)
    w = np.where(vis & (cos > 0.08), cos, 0.0)
    col = cv2.remap(ref, u.reshape(hh, ww).astype(np.float32), v.reshape(hh, ww).astype(np.float32),
                    cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return col, w.reshape(hh, ww), A > 0.5

def remap_v(img, fn):
    """img in member UV space -> canonical UV space with v' = fn(v) (an involution)."""
    hh, ww = img.shape[:2]
    rr, cc = np.mgrid[0:hh, 0:ww].astype(np.float32)
    v = 1 - (rr + 0.5) / hh; v2 = fn(v); r2 = (1 - v2) * hh - 0.5
    return cv2.remap(img.astype(np.float32), cc, r2.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)

ID = None
MIRF = lambda v: np.mod(0.5 - v, 1.0)      # ring theta -> pi - theta (fuselage, nacelle, belly)
MIRW = lambda v: np.mod(1.0 - v, 1.0)      # aerofoil loop upper <-> lower (fin)
GROUPS = {
    'fuselage': [('fuselage', ID, 1.0), ('fuselage', MIRF, 0.92)],
    'wing': [('wing_L', ID, 1.0), ('wing_R', ID, 1.0)],
    'htail': [('htail_L', ID, 1.0), ('htail_R', ID, 1.0)],
    'fin': [('fin', ID, 1.0), ('fin', MIRW, 0.92)],
    'nacelle': [('nacelle_L', ID, 1.0), ('nacelle_L', MIRF, 0.92), ('nacelle_R', MIRF, 1.0)],
    'duct': [('duct_L', ID, 1.0), ('duct_L', MIRF, 0.9)],
    'spinner': [('spinner_L', ID, 1.0)],
    'fan': [('fan_L', ID, 1.0)],
    'belly': [('belly_fairing', ID, 1.0), ('belly_fairing', MIRF, 0.92)],
}
# which member texture each object uses, and the mapping from canonical to it
USE = {'fuselage': ('fuselage', ID), 'wing_L': ('wing', ID), 'wing_R': ('wing', ID), 'htail_L': ('htail', ID),
       'htail_R': ('htail', ID), 'fin': ('fin', ID), 'nacelle_L': ('nacelle', ID), 'nacelle_R': ('nacelle', MIRF),
       'duct_L': ('duct', ID), 'duct_R': ('duct', MIRF), 'spinner_L': ('spinner', ID), 'fan_L': ('fan', ID), 'fan_R': ('fan', ID), 'spinner_R': ('spinner', ID),
       'belly_fairing': ('belly', ID)}

def smooth_valid(img, w, sig):
    m = (w > 0).astype(np.float32)
    num = cv2.GaussianBlur(img * m[..., None], (0, 0), sig); den = cv2.GaussianBlur(m, (0, 0), sig)
    return num / np.maximum(den, 1e-6)[..., None], den

def fill(img, w, iters=12):
    """fill unseen texels by repeated normalised blur (coarse to fine)."""
    out = img.copy(); m = (w > 0)
    for sig in (2, 4, 8, 16, 32, 64, 128):
        sm, den = smooth_valid(out, m.astype(np.float32), sig)
        newm = den > 0.02
        out[~m & newm] = sm[~m & newm]; m = m | newm
    return out

if __name__ != '__main__': raise ImportError('lib')
os.makedirs('tex', exist_ok=True)
info = {}
for g, members in GROUPS.items():
    best = None; own = {}
    for name, fn, pri in members:
        col, w, A = sample_member(name)
        if fn is None or name not in own: own.setdefault(name, (col.copy(), w.copy(), fn))
        if fn is not None:
            col = remap_v(col, fn); w = remap_v(w, fn)
        w = w * pri
        if best is None: best = [col, w]
        else:
            take = w > best[1]
            best[0][take] = col[take]; best[1][take] = w[take]
    col, w = best
    seen = w > 0.0
    photo = fill(col, w)
    # shading estimate: blur of the seen photo over ~0.6 m; ratio = detail with the light divided out
    hh, ww = w.shape
    sig = max(hh, ww) / 120.0
    sm, den = smooth_valid(col, seen.astype(np.float32), sig)
    ratio = np.where(seen[..., None], col / np.maximum(sm, 1), 1.0)
    ratio = np.clip(ratio, 0, 1.6)
    cv2.imwrite('tex/%s_photo.png' % g, np.clip(photo, 0, 255).astype(np.uint8))
    for name, (oc, ow, ofn) in own.items():
        # the member's own photo samples, in its own UV space, unseen texels from the merged texture
        base = photo if ofn is None else remap_v(photo, ofn)
        o = np.where((ow > 0)[..., None], oc, base)
        cv2.imwrite('tex/own_%s.png' % name, np.clip(o, 0, 255).astype(np.uint8))
    cv2.imwrite('tex/%s_seen.png' % g, (np.clip(w, 0, 1) * 255).astype(np.uint8))
    np.save('tex/%s_ratio.npy' % g, ratio.astype(np.float32))
    cv2.imwrite('tex/%s_ratio.png' % g, np.clip(ratio * 160, 0, 255).astype(np.uint8))
    info[g] = dict(seen=float(seen.mean()), size=[ww, hh])
    print(g, 'seen %.2f' % seen.mean())
json.dump({'groups': info, 'use': {k: [v[0], v[1] is not None] for k, v in USE.items()}}, open('tex/info.json', 'w'), indent=1)
