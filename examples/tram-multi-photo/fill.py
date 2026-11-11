"""Unseen texels: synthesised from the same part's own seen pixels (an exemplar cut from the largest fully-seen square,
laid down in feathered blocks at random offsets), never stretched. Parts with no usable exemplar get the class exemplar
from another part (CLASS_SRC) or, failing that, are left to the material version."""
import numpy as np, cv2

def exemplar(img, seen, minsz=24):
    """largest square fully inside the seen mask (distance transform)"""
    m = np.pad(seen.astype(np.uint8), 1)
    if m.sum() < minsz * minsz: return None
    dt = cv2.distanceTransform(m, cv2.DIST_C, 3)[1:-1, 1:-1]
    y, x = np.unravel_index(np.argmax(dt), dt.shape); r = int(dt[y, x])
    if 2 * r < minsz: return None
    r = min(r, 96)
    e = img[max(0, y - r + 1):y + r, max(0, x - r + 1):x + r].copy()
    return e if min(e.shape[:2]) >= minsz else None

def synth(shape, ex, block=None, seed=0):
    """cover `shape` with feathered random blocks of the exemplar"""
    H, W = shape; eh, ew = ex.shape[:2]; b = block or max(8, min(eh, ew) // 2)
    rs = np.random.RandomState(seed); acc = np.zeros((H, W, 3), np.float32); wsum = np.zeros((H, W), np.float32)
    win = np.outer(np.hanning(2 * b + 2)[1:-1], np.hanning(2 * b + 2)[1:-1]).astype(np.float32) + 1e-3
    for y in range(-b, H, b):
        for x in range(-b, W, b):
            sy = rs.randint(0, max(1, eh - 2 * b)); sx = rs.randint(0, max(1, ew - 2 * b))
            p = ex[sy:sy + 2 * b, sx:sx + 2 * b].astype(np.float32)
            if p.shape[0] < 2 * b or p.shape[1] < 2 * b: p = cv2.resize(ex.astype(np.float32), (2 * b, 2 * b))
            y0, x0 = max(y, 0), max(x, 0); y1, x1 = min(y + 2 * b, H), min(x + 2 * b, W)
            if y1 <= y0 or x1 <= x0: continue
            pp = p[y0 - y:y1 - y, x0 - x:x1 - x]; ww = win[y0 - y:y1 - y, x0 - x:x1 - x]
            acc[y0:y1, x0:x1] += pp * ww[..., None]; wsum[y0:y1, x0:x1] += ww
    return acc / np.maximum(wsum, 1e-6)[..., None]

def fill(img, valid, seen, ex=None, seed=0):
    """img float HxWx3 ; valid/seen bool HxW. Returns filled image and the exemplar used."""
    hole = valid & ~seen
    if not hole.any(): return img, None
    ex = ex if ex is not None else exemplar(img, seen)
    if ex is None: return img, None
    syn = synth(hole.shape, ex, seed=seed)
    out = img.copy(); out[hole] = syn[hole]
    # soften the boundary between seen and synthesised texels
    edge = cv2.dilate(hole.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~cv2.erode(hole.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & valid
    bl = cv2.GaussianBlur(out, (0, 0), 1.2); out[edge] = bl[edge]
    return out, ex
