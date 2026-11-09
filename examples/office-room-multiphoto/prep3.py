"""Third texture pass: individual books (with lean), the outdoor view projected from the window photo, printer faces.
  uv run --with numpy --with opencv-python-headless python prep3.py
"""
import json
import cv2
import numpy as np
from camlib import load

cams = load('cams_final.json'); R = json.load(open('room_final.json'))
bk = cv2.imread('tex/bookcase.png'); g = cv2.cvtColor(bk, cv2.COLOR_BGR2GRAY).astype(np.float32)
lab = cv2.cvtColor(bk, cv2.COLOR_BGR2LAB).astype(np.float32)
BC = json.load(open('tex/bookcols.json'))
# book runs per compartment (texture columns); objects that are not books are modelled separately
BOOKS = {'c1': (132, 297), 'c2': (142, 299), 'c3': (146, 299)}
ROWS = {'c1': (45, 143), 'c2': (156, 290), 'c3': (304, 431)}
out = {}
# per shelf, read off the photo: the lean of the leaning books and the column where the upright books start
SHELF = {'c1': (-0.40, 272), 'c2': (0.0, 142), 'c3': (-0.30, 190)}
gx_all = np.abs(cv2.Sobel(cv2.GaussianBlur(g, (3, 3), 0), cv2.CV_32F, 1, 0, ksize=3))
def segment(r0, r1, cA, cB, s):
    """book boundaries (bottom columns) in [cA, cB) for books leaning by shear s (top col = bottom col - s * height)"""
    if cB - cA < 4: return []
    H_ = r1 - r0; acc = np.zeros(cB - cA, np.float32)
    for i_ in range(H_):
        rr = r0 + i_; off = -s * (r1 - rr)
        cols = np.arange(cA, cB) + off; ok = (cols >= 0) & (cols < g.shape[1] - 1)
        acc[ok] += np.interp(cols[ok], np.arange(g.shape[1]), gx_all[rr])
    prof = np.convolve(acc, [0.25, 0.5, 0.25], 'same'); thr = np.median(prof) * 1.15
    pk = [k for k in range(2, len(prof) - 2) if prof[k] >= prof[k - 1] and prof[k] >= prof[k + 1] and prof[k] > thr]
    keep = []
    for q in pk:
        if keep and q - keep[-1] < 4:
            if prof[q] > prof[keep[-1]]: keep[-1] = q
            continue
        keep.append(q)
    return [cA] + [cA + q for q in keep] + [cB]
def book_top(r0, r1, a, b, s):
    bgc = np.median(np.concatenate([lab[rr, int(a - s * (r1 - rr)) + 1:int(b - s * (r1 - rr)) - 1].reshape(-1, 3) for rr in range(r0 + 12, r0 + 18)]), 0)
    for rr in range(r0 + 14, r1 - 8):
        seg = lab[rr:rr + 3, int(a - s * (r1 - rr)) + 1:int(b - s * (r1 - rr)) - 1].reshape(-1, 3)
        if len(seg) and np.linalg.norm(np.median(seg, 0) - bgc) > 20: return rr
    return None
for ck, (cA, cB) in BOOKS.items():
    r0, r1 = ROWS[ck]; s, U = SHELF[ck]
    # typical height of the leaning books, to know where their bottoms end (their tops reach column U)
    hs = [r1 - t for t in [book_top(r0, r1, c_, c_ + 6, s) for c_ in range(cA, max(cA + 7, U - 6), 6)] if t]
    htyp = float(np.median(hs)) if hs else 70.0
    lean_end = int(U + s * htyp) if s < 0 else U
    books = []
    for grp, (a0, a1, sg) in (('lean', (cA, lean_end, s)), ('up', (U, cB, 0.0))):
        bnd = segment(r0, r1, a0, a1, sg)
        for a, b in zip(bnd[:-1], bnd[1:]):
            if b - a < 3: continue
            top = book_top(r0, r1, a, b, sg)
            if top is None or r1 - top < 12: continue
            mid = (top + r1) // 2; off = int(round(-sg * (r1 - mid)))
            colr = np.median(bk[mid - 6:mid + 6, a + off + 1:b + off - 1].reshape(-1, 3), 0)
            books.append(dict(c0=int(a), c1=int(b), top=int(top), bgr=colr.tolist(), shear=float(sg), upright=grp == 'up'))
    med = float(np.median([b['top'] for b in books])) if books else r0
    fixed = []
    for b in books:
        if b['top'] - med > 25: b['top'] = int(med)
        w_ = b['c1'] - b['c0']; n_ = max(1, int(round(w_ / 11.0))) if w_ > 26 else 1
        for k in range(n_):
            nb = dict(b); nb['c0'] = int(b['c0'] + k * w_ / n_); nb['c1'] = int(b['c0'] + (k + 1) * w_ / n_); fixed.append(nb)
    # leaning tops may not pass the first upright book (column U) nor the side panel
    for b in fixed:
        hh = max(r1 - b['top'], 1); lim = (U if not b['upright'] else 296) - b['c1']
        if -b['shear'] * hh > lim: b['shear'] = -max(lim, 0) / hh
    out[ck] = dict(shear=float(s), rows=[r0, r1], books=fixed)
    print(ck, 'lean %.2f, upright from %d, leaning bottoms end at %d' % (s, U, lean_end), len(fixed), 'books')
json.dump(out, open('tex/books.json', 'w'), indent=1)
vis = bk.copy()
for ck, d in out.items():
    r0, r1 = d['rows']
    for b in d['books']:
        for c in (b['c0'], b['c1']):
            cv2.line(vis, (c, r1), (int(c - b.get('shear', d['shear']) * (r1 - b['top'])), b['top']), (0, 255, 255), 1)
        cv2.line(vis, (b['c0'] - int(d['shear'] * (r1 - b['top'])), b['top']), (b['c1'] - int(d['shear'] * (r1 - b['top'])), b['top']), (0, 0, 255), 1)
cv2.imwrite('g/books_seg.png', cv2.resize(vis, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))

# ---------------- outdoor view: behind each clear pane, a backdrop quad carrying exactly what that pane shows in the photo
win = cv2.imread('win.jpg'); cw = cams['win']
YB, YG, ZS, FW, PPM = -0.65, -0.17, 1.02, 0.065, 500
panes = []
for (x0, x1) in ((1.46, 2.50), (0.20, 1.24)):
    xm = (x0 + x1) / 2
    for a0, a1 in ((x0 + FW, xm - 0.04), (xm + 0.04, x1 - FW)):
        g0, g1, gz0, gz1 = a0 + 0.075, a1 - 0.075, ZS + FW + 0.085, 1.475      # clear glass under the blind
        # its image on the backdrop plane, seen from the photo camera (planes are parallel: a scaled rectangle)
        def onb(x, z):
            gp = np.array([x, YG, z]); d = gp - cw.pos; t_ = (YB - cw.pos[1]) / d[1]; return cw.pos + t_ * d
        p0, p1 = onb(g0, gz0), onb(g1, gz1)
        bx0, bx1, bz0, bz1 = min(p0[0], p1[0]), max(p0[0], p1[0]), min(p0[2], p1[2]), max(p0[2], p1[2])
        tex, ok = cw.rectify(win, (bx0, YB, bz0), (1, 0, 0), (0, 0, 1), bx1 - bx0, bz1 - bz0, PPM)
        mx, mz = int(0.10 * PPM), int(0.16 * PPM)                                  # margins seen from other places
        tex = cv2.copyMakeBorder(tex, mz, mz, mx, mx, cv2.BORDER_REFLECT)
        k = len(panes); cv2.imwrite(f'tex/outdoor_pane{k}.jpg', tex, [cv2.IMWRITE_JPEG_QUALITY, 92])
        panes.append(dict(file=f'outdoor_pane{k}.jpg', x0=bx0 - 0.10, x1=bx1 + 0.10, z0=bz0 - 0.16, z1=bz1 + 0.16, y=YB - 0.02 * k))
json.dump(panes, open('tex/outdoor_panes.json', 'w'), indent=1)
print('panes', [(round(p['x0'], 2), round(p['x1'], 2), round(p['z0'], 2), round(p['z1'], 2)) for p in panes])

win = cv2.imread('win.jpg'); cw = cams['win']
# ---------------- printer: rectify its side (facing the door, y = 0.50) and its front (facing the room, x = 2.06)
for name, o, u, v, us, vs in (('printer_side', (2.53, 0.50, 0.50), (-1, 0, 0), (0, 0, 1), 0.50, 0.45),
                              ('printer_front', (2.06, 0.55, 0.50), (0, -1, 0), (0, 0, 1), 0.50, 0.45)):
    t_, _ = cw.rectify(win, o, u, v, us, vs, 600)
    cv2.imwrite(f'tex/{name}.jpg', t_, [cv2.IMWRITE_JPEG_QUALITY, 92])
