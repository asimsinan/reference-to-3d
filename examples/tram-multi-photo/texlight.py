"""texlight.py -- one albedo for the whole tram, each photo's light fitted separately.
Model per photo k (linear RGB):  photo = albedo * E_k(n) * ao^g_k + o_k ,  E_k = 2nd-order spherical harmonics of the normal.
1) sample texels of every part, fit E_k, g_k, o_k and the samples' albedo by alternating least squares -> light.json
2) every texel: albedo from the views that see it best (photo minus o_k, divided by its light), unseen texels from the
   180-deg partner, then the y-mirror, then inpainting -> tex_alb/<obj>.png (sRGB)
3) per photo, albedo relit by that photo's light -> tex_l<k>/<obj>.png (for the photo-camera comparison)"""
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR'] = '1'
import cv2, json, numpy as np, sys
from camlib import cam
J = json.load(open('cams.json')); info = json.load(open('bake/objs.json')); occ = json.load(open('occ.json'))
ks = sorted(J['cams']); POW = float(os.environ.get('POW', '12'))
PRIO = {'6': 3.0, '1': 1.6, '4': 1.2, '2': 0.8, '3': 0.5, '5': 1.0}
def lin(c): c = c / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def srgb(l): l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055) * 255
PH = {k: lin(cv2.imread(f'ref/p{k}.png')[..., ::-1].astype(np.float32)).astype(np.float32) for k in ks}   # RGB linear
DEP = {}; OCC = {}
for k in ks:
    d = cv2.imread(f'bake/depth{k}.exr', cv2.IMREAD_UNCHANGED); z = d[..., 2].copy(); z[d[..., 3] < 0.5] = 1e9; DEP[k] = z
    m = np.zeros(PH[k].shape[:2], np.uint8)
    for poly in occ.get(k, []): cv2.fillPoly(m, [np.array(poly, np.int32)], 1)
    OCC[k] = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
CAMS = {k: cam(k) for k in ks}
AO = {}
def sh(N):
    x, y, z = N[:, 0], N[:, 1], N[:, 2]
    return np.stack([np.ones_like(x), x, y, z, x * y, y * z, 3 * z * z - 1, x * z, x * x - y * y], 1)
def views(P, N):
    cols = []; ws = []
    for k in ks:
        R, C, f, W, H, cx, cy = CAMS[k]
        Xc = (P - C) @ R.T; z = Xc[:, 2]; zs = np.where(z > 0.05, z, 1e9)
        u = f * Xc[:, 0] / zs + cx; v = f * Xc[:, 1] / zs + cy
        ok = (z > 0.05) & (u >= 1) & (v >= 1) & (u < W - 2) & (v < H - 2)
        ui = np.clip(np.round(u).astype(int), 0, W - 1); vi = np.clip(np.round(v).astype(int), 0, H - 1)
        ok &= np.abs(DEP[k][vi, ui] - z) < 0.025 + 0.004 * z
        ok &= ~OCC[k][vi, ui]
        dv = C - P; dv /= np.linalg.norm(dv, axis=1, keepdims=True); cs = (N * dv).sum(1); ok &= cs > 0.08
        w = np.where(ok, (f / np.maximum(z, 0.1)) ** 2 * cs ** 2 * PRIO[k], 0.0)
        uc = np.clip(u, 0, W - 1.001); vc = np.clip(v, 0, H - 1.001); x0 = np.floor(uc).astype(int); y0 = np.floor(vc).astype(int)
        fx = (uc - x0)[:, None]; fy = (vc - y0)[:, None]; I = PH[k]
        col = I[y0, x0] * (1 - fx) * (1 - fy) + I[y0, x0 + 1] * fx * (1 - fy) + I[y0 + 1, x0] * (1 - fx) * fy + I[y0 + 1, x0 + 1] * fx * fy
        cols.append(col); ws.append(w)
    return np.stack(cols), np.stack(ws)
def load(name):
    Pi = cv2.imread(f'bake/{name}_P.exr', cv2.IMREAD_UNCHANGED); Ni = cv2.imread(f'bake/{name}_N.exr', cv2.IMREAD_UNCHANGED)
    valid = (Pi[..., 3] > 0.5) & (np.abs(Pi[..., :3]).sum(-1) > 1e-6)
    P = Pi[..., 2::-1][valid].astype(np.float64); N = Ni[..., 2::-1][valid].astype(np.float64)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    A = cv2.imread(f'bake/{name}_AO.exr', cv2.IMREAD_UNCHANGED) if os.path.exists(f'bake/{name}_AO.exr') else None
    ao = np.clip(A[..., 1][valid], 0.02, 1).astype(np.float64) if A is not None else np.ones(len(P))
    return Pi.shape[0], valid, P, N, ao

LIGHTSKIP = ('glass', 'bow', 'volt', 'bench', 'ceiling', 'floor', 'controller', 'gate', 'door_')
def fit_light():
    rs = np.random.RandomState(1); C = []; W = []; Y = []; AOs = []
    for name in info:
        if name.startswith(LIGHTSKIP): continue
        n, valid, P, N, ao = load(name)
        if len(P) == 0: continue
        sel = rs.choice(len(P), min(len(P), 2500), replace=False)
        c, w = views(P[sel], N[sel]); C.append(c.transpose(1, 0, 2)); W.append(w.T); Y.append(sh(N[sel])); AOs.append(ao[sel])
    C = np.concatenate(C); W = np.concatenate(W); Y = np.concatenate(Y); AO_ = np.concatenate(AOs)
    W = np.where(W > 0, 1.0, 0.0) * (W.sum(1, keepdims=True) > 0)
    keep = (W > 0).sum(1) >= 1; C, W, Y, AO_ = C[keep], W[keep], Y[keep], AO_[keep]
    nK = len(ks); S = np.zeros((nK, 9, 3)); S[:, 0, :] = 1.0; O = np.zeros((nK, 3)); G = np.full(nK, 0.5)
    A = (C * W[..., None]).sum(1) / np.maximum(W.sum(1), 1e-9)[:, None]
    for it in range(12):
        E = np.einsum('ij,kjc->ikc', Y, S) * (AO_[:, None, None] ** G[None, :, None])   # (n,K,3)
        for i in range(nK):
            m = W[:, i] > 0
            for c in range(3):
                X = np.concatenate([(A[m, c] * AO_[m] ** G[i])[:, None] * Y[m], np.ones((m.sum(), 1))], 1)
                sol = np.linalg.lstsq(X, C[m, i, c], rcond=None)[0]; S[i, :, c] = sol[:9]; O[i, c] = sol[9]
            # ao exponent by a small search
            best = None
            for g in np.linspace(0, 1.5, 16):
                pred = A[m] * np.einsum('ij,jc->ic', Y[m], S[i]) * AO_[m, None] ** g + O[i]
                e = np.abs(pred - C[m, i]).mean()
                if best is None or e < best[0]: best = (e, g)
            G[i] = best[1]
        E = np.einsum('ij,kjc->ikc', Y, S) * (AO_[:, None, None] ** G[None, :, None])
        A = ((C - O[None]) * E * W[..., None]).sum(1) / np.maximum((E * E * W[..., None]).sum(1), 1e-9)
        A = np.clip(A, 0.002, 1.5)
        sc = np.median(np.einsum('ij,kjc->ikc', Y, S)[W > 0]); S /= sc; A *= sc   # gauge: median light 1
        pred = A[:, None] * E + O[None]
        err = [float(srgb(np.abs(pred[W[:, i] > 0, i]) ).mean() - 0) for i in range(nK)]
    for i, k in enumerate(ks):
        m = W[:, i] > 0; pr = srgb(A[m] * np.einsum('ij,jc->ic', Y[m], S[i]) * AO_[m, None] ** G[i] + O[i]); ph = srgb(C[m, i])
        print('photo', k, 'samples', int(m.sum()), 'fit |diff| %.1f' % np.abs(pr - ph).mean(), 'ao^%.2f' % G[i], 'offset', np.round(O[i], 3))
    json.dump({'S': {k: S[i].tolist() for i, k in enumerate(ks)}, 'O': {k: O[i].tolist() for i, k in enumerate(ks)}, 'G': {k: float(G[i]) for i, k in enumerate(ks)}}, open('light.json', 'w'))

def build():
    L = json.load(open('light.json')); S = {k: np.array(L['S'][k]) for k in ks}; O = {k: np.array(L['O'][k]) for k in ks}; G = L['G']
    only = sys.argv[2:]
    os.makedirs('tex_alb', exist_ok=True)
    for k in ks: os.makedirs(f'tex_l{k}', exist_ok=True)
    def albedo_views(P, N, ao):
        c, w = views(P, N); Yn = sh(N); al = []
        for i, k in enumerate(ks):
            E = np.maximum(Yn @ S[k], 0.03) * ao[:, None] ** G[k]
            al.append((c[i] - O[k]) / E)
        al = np.stack(al); wm = w.max(0); wn = np.where(wm[None] > 0, (w / np.maximum(wm[None], 1e-12)) ** POW, 0)
        a = (al * wn[..., None]).sum(0) / np.maximum(wn.sum(0), 1e-9)[:, None]
        return np.clip(a, 0.002, 1.0), wm > 0, wm
    for name in info:
        if only and name not in only: continue
        n, valid, P, N, ao = load(name)
        A = np.zeros((len(P), 3)); seen = np.zeros(len(P), bool)
        if len(P):
            best = np.zeros(len(P))
            for (sx, sy), fac in (((1, 1), 1.0), ((-1, -1), 0.55), ((1, -1), 0.01)):
                a, s, wm = albedo_views(P * [sx, sy, 1], N * [sx, sy, 1], ao); sc = wm * fac; take = s & (sc > best)
                A[take] = a[take]; seen |= take; best[take] = sc[take]
        img = np.zeros((n, n, 3), np.float32); img[valid] = srgb(A); simg = np.zeros((n, n), bool); simg[valid] = seen
        hole = (valid & ~simg).astype(np.uint8)
        if hole.any() and hole.sum() < valid.sum():
            img = cv2.inpaint(np.clip(img, 0, 255).astype(np.uint8), hole, 5, cv2.INPAINT_TELEA).astype(np.float32)
        elif valid.any() and not seen.any():
            img[valid] = 50
        pad = cv2.inpaint(np.clip(img, 0, 255).astype(np.uint8), (~valid).astype(np.uint8), 3, cv2.INPAINT_TELEA)
        cv2.imwrite(f'tex_alb/{name}.png', pad[..., ::-1]); cv2.imwrite(f'tex_alb/{name}_src.png', (simg * 12).astype(np.uint8))
        Alin = lin(pad[valid].astype(np.float32))
        if os.environ.get('NOLIT'): continue
        for k in ks:
            E = np.maximum(sh(N) @ S[k], 0.0) * ao[:, None] ** G[k]
            out = np.zeros((n, n, 3), np.float32); out[valid] = srgb(Alin * E + O[k])
            pk = cv2.inpaint(np.clip(out, 0, 255).astype(np.uint8), (~valid).astype(np.uint8), 3, cv2.INPAINT_TELEA)
            cv2.imwrite(f'tex_l{k}/{name}.png', pk[..., ::-1])

if __name__ == '__main__':
    if sys.argv[1] == 'fit': fit_light()
    else: build()
