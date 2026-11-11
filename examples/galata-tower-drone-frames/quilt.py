# Seamless fill of a cylindrical-UV texture (u = angle, rows = height) from its well-seen part:
#  1) the foot band no frame sees: one copy of the stones just above, joined by a horizontal minimum-error cut
#  2) the unseen angles: full-height strips taken from well-seen angles (same rows, so courses and bands stay level),
#     each joined to the previous by a vertical minimum-error cut, the last one also to the seen texture on its right.
import numpy as np, cv2

rng = np.random.default_rng(7)


def min_cut_vertical(E):
    """E: (H, w) error. Returns for each row the column of a top-to-bottom 8-connected seam of minimum total error."""
    H, w = E.shape; C = E.copy(); B = np.zeros((H, w), np.int8)
    for r in range(1, H):
        prev = C[r - 1]; l = np.r_[np.inf, prev[:-1]]; rr = np.r_[prev[1:], np.inf]
        st = np.stack([l, prev, rr]); k = np.argmin(st, 0); C[r] += st[k, np.arange(w)]; B[r] = k - 1
    seam = np.zeros(H, int); seam[-1] = int(np.argmin(C[-1]))
    for r in range(H - 1, 0, -1): seam[r - 1] = np.clip(seam[r] + B[r, seam[r]], 0, w - 1)
    return seam


def err(a, b):
    d = cv2.GaussianBlur(a, (0, 0), 1.0) - cv2.GaussianBlur(b, (0, 0), 1.0)
    return (d * d).sum(-1)


def quilt(T, G, A, sw=160, ov=56, foot_frac=0.6, log=print, exclude=(), Gsrc=None, win_rows=None, win_gap=0.0):
    """T: HxWx3 float texture, G: good-texel mask, A: texels on the surface. Returns filled texture and filled mask."""
    T = T.copy(); H, W = G.shape
    colgood = (G & A).sum(0) / np.maximum(A.sum(0), 1)
    gcols = colgood > 0.75
    # ---- 1) foot band: rows (from the bottom) whose good fraction over the good columns is low
    rowgood = (G[:, gcols] & A[:, gcols]).mean(1)
    rows_ok = np.nonzero(rowgood > foot_frac)[0]; f0 = rows_ok.max() + 1 if len(rows_ok) else H
    if f0 < H:
        band = H - f0; o = 40; s = band + o                     # copy the stones s rows higher
        src = np.roll(T, s, 0)                                   # src[r] = T[r - s]
        # horizontal seam in the overlap rows [f0-o, f0): transpose to reuse the vertical cut
        E = err(T[f0 - o:f0], src[f0 - o:f0]).T                  # (W, o)
        seam = min_cut_vertical(E)                               # per column: first row (in overlap) taken from src
        for c in range(W):
            r0 = f0 - o + seam[c]; T[r0:, c] = src[r0:, c]
        G = G.copy(); G[f0 - o:, gcols] = True
        log('foot band %d rows (%.1f%% of the height) filled from %d rows higher' % (band, 100 * band / H, s))
    # ---- 2) unseen angles
    good = colgood > 0.75
    if good.all(): return T, G
    srcok = good.copy() if Gsrc is None else ((Gsrc & A).sum(0) / np.maximum(A.sum(0), 1) > 0.75)
    for a0, a1 in exclude: srcok[a0:a1] = False
    # the unknown run (cyclic): start right after the last good column before it
    g = good.astype(int); starts = [c for c in range(W) if g[c] == 0 and g[c - 1] == 1]
    ends = [c for c in range(W) if g[c] == 0 and g[(c + 1) % W] == 1]
    a = starts[0]; b = min(ends, key=lambda e: (e - a) % W); n_unk = (b - a) % W + 1
    # source starts: strips fully inside good columns (cyclic)
    cand = [c for c in range(W) if all(good[(c + k) % W] for k in range(0, sw, 4)) and good[(c + sw - 1) % W]]
    cols = lambda c0, n: (np.arange(n) + c0) % W
    Ts = T[::4]                                                  # rows subsampled for the choice
    pos = (a - ov) % W; covered = 0; used = []
    wins = np.array([], int); placed = []
    if win_rows is not None:
        Lw = T[win_rows[0]:win_rows[1]].mean(2); dark = (Lw < np.percentile(Lw, 3)).mean(0)
        n, lab, st, cen = cv2.connectedComponentsWithStats((dark > 0.25).astype(np.uint8)[None, :].repeat(3, 0))
        wins = np.array([int(cen[i][0]) for i in range(1, n) if st[i][2] >= 4], int)
        placed = [w for w in wins if good[w]]                     # windows of the kept photo
        log('windows found at columns %s, kept %s' % (list(wins), placed))
    gap = int(win_gap * W / 360)
    def win_ok(c, width, at):
        if gap == 0: return True
        for w in wins:
            d = (w - c) % W
            if d < width:
                t = (at + d) % W
                if any(abs(((t - p + W // 2) % W) - W // 2) < gap for p in placed): return False
        return True
    out = T.copy()
    while covered < n_unk + ov:
        remaining = n_unk + ov - covered
        last = remaining <= sw - ov
        width = min(sw, remaining + ov) if not last else remaining + ov
        width = max(width, 2 * ov + 8)
        cs_ok = [c for c in range(W) if all(srcok[(c + k) % W] for k in range(0, width, 2)) and srcok[(c + width - 1) % W]]
        if not cs_ok:            # the remaining gap is wider than any clean source: one more ordinary strip first
            last = False; width = sw
            cs_ok = [c for c in range(W) if all(srcok[(c + k) % W] for k in range(0, width, 2)) and srcok[(c + width - 1) % W]]
        best = []
        def strip(c, fl, a0, n):          # columns a0..a0+n of the (possibly mirrored) source strip
            idx = cols(c, width)
            if fl: idx = idx[::-1]
            return idx[a0:a0 + n]
        for rep, wrel in ((False, False), (True, False), (True, True)):
          for c in cs_ok[::3]:
            for fl in (False,):
              if not rep and any(abs(((c - u + W // 2) % W) - W // 2) < width // 2 and f == fl for u, f in used[-4:]): continue
              if not wrel and not win_ok(c, width, pos): continue
              e = ((Ts[:, cols(pos, ov)] - Ts[:, strip(c, fl, 0, ov)]) ** 2).mean()
              if last:
                  e += ((Ts[:, cols(pos + width - ov, ov)] - Ts[:, strip(c, fl, width - ov, ov)]) ** 2).mean()
              best.append((e, c, fl))
          if best: break
        best.sort(); _, c, fl = best[int(rng.integers(0, min(5, len(best))))]; used.append((c, fl))
        S = T[:, strip(c, fl, 0, width)].copy()
        for w in wins:
            d = (w - c) % W
            if d < width and d >= ov // 2: placed.append((pos + d) % W)
        # gentle tone match on the left overlap
        gain = (out[:, cols(pos, ov)].reshape(-1, 3).mean(0) + 1) / (S[:, :ov].reshape(-1, 3).mean(0) + 1)
        S *= np.clip(gain, 0.85, 1.18)
        seam = min_cut_vertical(err(out[:, cols(pos, ov)], S[:, :ov]))
        for r in range(H):
            k = seam[r]; out[r, cols(pos + k, width - k)] = S[r, k:]
        if last:   # right side: back to the seen texture through a second cut
            seam2 = min_cut_vertical(err(S[:, width - ov:], T[:, cols(pos + width - ov, ov)]))
            for r in range(H):
                k = seam2[r]; out[r, cols(pos + width - ov + k, ov - k)] = T[r, cols(pos + width - ov + k, ov - k)]
            break
        covered += width - ov; pos = (pos + width - ov) % W
    log('unseen angles: %d columns (%.0f deg) filled with %d strips (%d distinct sources, %d mirrored)' % (n_unk, 360 * n_unk / W, len(used), len(set(u for u, f in used)), sum(f for u, f in used)))
    return out, np.ones_like(G)
