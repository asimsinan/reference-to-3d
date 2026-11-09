"""Shelf objects: GrabCut masks on the 1000 ppm bookcase front, sampled on a 4 mm grid -> tex/items.json
(per item: grid origin (col,row in 1000 ppm px), step, mask grid, distance-to-edge grid)."""
import json, cv2, numpy as np
im = cv2.imread('tex/bookcase_hi.png'); S = 2.5            # 400 ppm boxes -> 1000 ppm
ITEMS = {   # name: (c0, c1, r0, r1) in 400 ppm texture px, kind
    'balloon':   ((26, 52, 88, 144), 'puff'),
    'football':  ((50, 110, 88, 144), 'puff'),
    'cat_apple': ((102, 137, 98, 144), 'puff'),
    'gears':     ((215, 300, 112, 141), 'puff'),
    'trays':     ((6, 126, 210, 291), 'flat'),
    'pen_box':   ((28, 62, 336, 432), 'flat'),
    'green_box': ((55, 84, 312, 432), 'flat'),
    'phone':     ((64, 150, 344, 432), 'puff'),
    'name_set':  ((222, 318, 376, 432), 'puff'),
}
out = {}; STEP = 4   # px at 1000 ppm = 4 mm
vis = im.copy()
for name, ((c0, c1, r0, r1), kind) in ITEMS.items():
    x0, x1, y0, y1 = int(c0 * S), int(c1 * S), int(r0 * S), int(r1 * S)
    pad = 12
    X0, Y0 = max(0, x0 - pad), max(0, y0 - pad); X1, Y1 = min(im.shape[1], x1 + pad), min(im.shape[0], y1)
    sub = im[Y0:Y1, X0:X1].copy()
    m = np.zeros(sub.shape[:2], np.uint8); bg = np.zeros((1, 65), np.float64); fg = np.zeros((1, 65), np.float64)
    rect = (x0 - X0, y0 - Y0, x1 - x0, (Y1 - Y0) - (y0 - Y0))
    if kind == 'flat':
        mask = np.zeros(sub.shape[:2], np.uint8); mask[rect[1]:, rect[0]:rect[0] + rect[2]] = 1
    else:
        cv2.grabCut(sub, m, rect, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
        mask = ((m == 1) | (m == 3)).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(mask)
        if n > 1: mask = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    dt = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    g = mask[::STEP, ::STEP]; d = dt[::STEP, ::STEP]
    out[name] = dict(kind=kind, X0=X0, Y0=Y0, step=STEP, mask=g.tolist(), dist=np.round(d / 1000.0, 4).tolist())
    cnt, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(vis[Y0:Y1, X0:X1], cnt, -1, (0, 255, 0), 3)
json.dump(out, open('tex/items.json', 'w'))
cv2.imwrite('g/items.jpg', cv2.resize(vis[:1100], None, fx=0.6, fy=0.6))
print({k: int(np.sum(v['mask'])) for k, v in out.items()})
