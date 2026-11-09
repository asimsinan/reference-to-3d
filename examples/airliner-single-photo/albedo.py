# Albedo and roughness maps from the photo textures: the light divided out (photo / its smooth shading, linear),
# times the paint albedo; engine inside parts keep the photo's own values scaled like the nacelle paint.
import cv2, numpy as np, json, os, sys
cal = json.load(open('calib.json')) if os.path.exists('calib.json') else {}
PAINT = np.array(cal.get('paint', [0.80, 0.80, 0.80]))[::-1]      # stored RGB -> BGR
def s2l(x): x = np.clip(x / 255.0, 0, 1); return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
def l2s(x): x = np.clip(x, 0, 1); return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055) * 255
def smooth_valid(img, m, sig):
    num = cv2.GaussianBlur(img * m[..., None], (0, 0), sig); den = cv2.GaussianBlur(m, (0, 0), sig)
    return num / np.maximum(den, 1e-6)[..., None], den
info = json.load(open('tex/info.json'))['groups']
nac = s2l(cv2.imread('tex/nacelle_photo.png').astype(np.float32)); nseen = cv2.imread('tex/nacelle_seen.png', 0) > 0
k_eng = PAINT / np.median(nac[nseen], 0) * cal.get('eng_gain', 1.0)
for g in info:
    ph = s2l(cv2.imread('tex/%s_photo.png' % g).astype(np.float32)); seen = (cv2.imread('tex/%s_seen.png' % g, 0) > (0 if g in ('fan', 'spinner', 'duct', 'fin') else 70)).astype(np.float32)
    hh, ww = seen.shape
    if g in ('fan', 'spinner', 'duct'):
        alb = ph * k_eng; rough = np.full((hh, ww), 0.45 if g != 'duct' else 0.3)
    else:
        sig = max(hh, ww) / 90.0
        sm, den = smooth_valid(ph, seen, sig)
        ratio = np.where(seen[..., None] > 0, ph / np.maximum(sm, 1e-4), 1.0)
        # feather the seen/unseen border so no seam shows
        wgt = np.clip(cv2.GaussianBlur(seen, (0, 0), 3) * 1.5, 0, 1)[..., None]
        ratio = 1 + (np.clip(ratio, 0, 1.25) - 1) * wgt
        ratio = np.minimum(ratio, 1.0 + 0.1 * (ratio > 1))   # do not brighten paint beyond its albedo much
        alb = PAINT * ratio
        lum = ratio.mean(2)
        rough = np.where(lum < 0.45, 0.08, 0.28)                 # windows and dark glass glossy, paint satin
        rough = cv2.GaussianBlur(rough.astype(np.float32), (0, 0), 1.0)
    if os.path.exists('tex/%s_gain.npy' % g): alb = alb * np.load('tex/%s_gain.npy' % g)
    alb = np.minimum(alb, 0.92)
    cv2.imwrite('tex/%s_albedo.png' % g, l2s(alb).astype(np.uint8))
    cv2.imwrite('tex/%s_rough.png' % g, np.clip(rough * 255, 0, 255).astype(np.uint8))
    print(g, 'albedo mean', alb.reshape(-1, 3).mean(0)[::-1].round(3))
