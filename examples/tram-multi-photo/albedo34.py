"""albedo34.py -- paint / white / maroon albedo maps for tram 34 from the projected photo texels (tex34):
the measured colour of each class times the photo's own pixel pattern (lightness divided by its wide blur, so the
light and the big reflections go, scratches, lining edges and wear stay). Unseen texels: the class colour."""
import os, cv2, json, numpy as np
info = json.load(open('bake34/objs.json')); os.makedirs('tex34alb', exist_ok=True)
L = json.load(open('lev34.json')); CJ = json.load(open('tex34m/colors.json'))['srgb']
def lin(c): c = np.asarray(c, float) / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def enc(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055) * 255
def hue(name, level): l = lin(CJ[name]); return level * l / l.max()
CLS = {'paint_': hue('red', L['red']), 'sign_': hue('red', L['red']), 'white_': hue('white', L['white']), 'frame_': hue('maroon', L['maroon'])}
n = 0
for name in info:
    pre = next((p for p in CLS if name.startswith(p)), None)
    if not name.startswith(('paint_side_lower', 'paint_side_upper', 'white_band_L', 'white_band_R')) or not os.path.exists(f'tex34/{name}.png'): continue
    t = cv2.imread(f'tex34/{name}.png').astype(np.float32); s = cv2.imread(f'tex34/{name}_src.png', 0) > 0
    Y = lin(t).mean(-1); m = s.astype(np.float32)
    sig = max(3.0, t.shape[0] / 40)
    bl = cv2.GaussianBlur(Y * m, (0, 0), sig) / np.maximum(cv2.GaussianBlur(m, (0, 0), sig), 1e-4)
    ratio = np.clip(Y / np.maximum(bl, 1e-4), 0.55, 1.35) ** 0.6
    ratio = np.where(s, ratio, 1.0)
    alb = CLS[pre][::-1][None, None, :] * ratio[..., None]            # BGR
    cv2.imwrite(f'tex34alb/{name}.png', enc(alb).astype(np.uint8)); n += 1
print('albedo maps', n)
