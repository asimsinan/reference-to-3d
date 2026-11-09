import cv2, numpy as np, json
ref = cv2.imread('ref.jpg').astype(np.float32); uv = np.load('ground_uv.npy')
top = cv2.remap(ref, uv[..., 0], uv[..., 1], cv2.INTER_CUBIC)
r0, c0 = 1200 + 95, 1250 + 95; Ht, Wt = 300, 262
top = np.clip(top, 0, 255); t = top[r0:r0 + Ht, c0:c0 + Wt].copy()
blk = t.mean(2) < 20
sh = np.roll(top, -132, axis=1)[r0:r0 + Ht, c0:c0 + Wt]
t[blk] = sh[blk]
hsv = cv2.cvtColor(np.clip(t, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
grey = np.zeros(t.shape[:2], bool); grey[0:75, 215:] = True
dn = top[r0 + 150:r0 + 150 + Ht, c0:c0 + Wt]
sm_ = cv2.GaussianBlur(grey.astype(np.float32), (0, 0), 6)[..., None]; sm_ = np.clip(sm_ * 1.6, 0, 1)
t = t * (1 - sm_) + dn * sm_
# seamless: cross-fade a band at each edge with the opposite edge
b = 12
for k in range(b):
    a = 0.5 * (1 - k / b)
    t[k], t[-1 - k] = (1 - a) * t[k] + a * t[-1 - k], (1 - a) * t[-1 - k] + a * t[k]
    t[:, k], t[:, -1 - k] = (1 - a) * t[:, k] + a * t[:, -1 - k], (1 - a) * t[:, -1 - k] + a * t[:, k]
# flatten slow light gradient (keep joints and grain)
lin = (t / 255.0) ** 2.2
sm = cv2.GaussianBlur(lin, (0, 0), 60); lin = lin / sm * sm.reshape(-1, 3).mean(0)
out = np.clip(lin ** (1 / 2.2) * 255, 0, 255).astype(np.uint8)
cv2.imwrite('tex/ground_tile.png', cv2.resize(out, (Wt * 4, Ht * 4), interpolation=cv2.INTER_CUBIC))
json.dump({'x_top': 60 - r0 * 0.05, 'y_left': 80 - c0 * 0.05, 'len_x': Ht * 0.05, 'len_y': Wt * 0.05,
           'mean_srgb': out.reshape(-1, 3).mean(0)[::-1].tolist()}, open('tex/ground_tile.json', 'w'), indent=1)
cv2.imwrite('gtile_prev.jpg', np.tile(out, (2, 2, 1)))
print(json.load(open('tex/ground_tile.json')))
