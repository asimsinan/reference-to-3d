"""showcase.py OUT -- top row: photos 9, 13 (cropped to the tram), 8; second row: the model (real materials, Cycles)
rendered through each photo's solved camera with the same crop; third row: views no photo has (rear three-quarter,
the running gear, the cab)."""
import cv2, numpy as np, sys
H = 520
def comp(k):
    p = cv2.imread(f'ref2/p{k}.png'); q = cv2.imread(f'out/real34_{k}.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
    a = q[..., 3:] / 255.0; return p, (q[..., :3] * a + p * (1 - a)).astype(np.uint8)
CROP = {'9': None, '13': (150, 0, 700, 960), '8': None}
top, mid = [], []
for k, c in CROP.items():
    p, m = comp(k)
    if c: x0, y0, x1, y1 = c; p, m = p[y0:y1, x0:x1], m[y0:y1, x0:x1]
    s = H / p.shape[0]; top.append(cv2.resize(p, None, fx=s, fy=s)); mid.append(cv2.resize(m, None, fx=s, fy=s))
gap = lambda h: np.full((h, 8, 3), 255, np.uint8)
row = lambda ims: np.concatenate(sum([[im, gap(im.shape[0])] for im in ims], [])[:-1], 1)
r1, r2 = row(top), row(mid); W = r1.shape[1]
extra = [cv2.imread(f'out/real34_{v}.png') for v in ('arka34', 'altyan', 'kabin')]
hh = int((W - 16) / sum(e.shape[1] / e.shape[0] for e in extra))
r3 = row([cv2.resize(e, (int(e.shape[1] * hh / e.shape[0]), hh)) for e in extra]); r3 = cv2.resize(r3, (W, r3.shape[0]))
band = np.full((8, W, 3), 255, np.uint8)
cv2.imwrite(sys.argv[1], np.concatenate([r1, band, r2, band, r3], 0), [cv2.IMWRITE_JPEG_QUALITY, 86])
