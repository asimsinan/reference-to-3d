"""PnP with unknown focal length: scan f, solvePnP, keep the best.  pnp(points3d, points2d, W, H) -> dict like cams.json"""
import numpy as np, cv2, json
def pnp(P3, P2, W, H, fr=(500, 3500), init=None):
    P3 = np.asarray(P3, np.float64); P2 = np.asarray(P2, np.float64); best = None
    for f in np.arange(fr[0], fr[1], 10.0):
        K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]])
        ok, rv, tv = cv2.solvePnP(P3, P2, K, None, flags=cv2.SOLVEPNP_SQPNP)
        if not ok: continue
        ok, rv, tv = cv2.solvePnP(P3, P2, K, None, rv, tv, True, cv2.SOLVEPNP_ITERATIVE)
        pr, _ = cv2.projectPoints(P3, rv, tv, K, None); e = np.linalg.norm(pr.reshape(-1, 2) - P2, axis=1)
        Rm = cv2.Rodrigues(rv)[0]; pos = (-Rm.T @ tv).ravel()
        if (Rm @ (P3 - pos).T)[2].min() <= 0: continue
        if best is None or e.mean() < best[0]: best = (e.mean(), f, Rm, pos, e)
    m, f, Rm, pos, e = best
    return dict(pos=pos.tolist(), R=Rm.tolist(), f=float(f), cx=W / 2, cy=H / 2, W=W, H=H), e
