"""Solve the camera of ONE consistent-perspective picture of a room (a photo or a game/CG render) from its lines.

Not for AI concept pictures: their perspective is not consistent (see references/single-view-interior.md, step 1).

The room's frame (written to the json): +Y the room's depth (away from the camera, the main vanishing point), +Z up,
+X = Y x Z (to the right when looking down the room); the camera at (0, 0, h), metres.

  uv run --with numpy --with opencv-python-headless python solve_camera_vp.py ref.png --out cam.json \
      --overlay lines.png [--vp 805,450] [--scale FX,FY,TX,TY,HEIGHT]

  --vp     the depth vanishing point, if the RANSAC pick is wrong (look at the overlay: magenta circle)
  --scale  a vertical edge of known height: its foot on the floor (FX,FY) and its top (TX,TY), pixels; sets h.
           Without it h = 1 (everything scales with h). A door (2.0 m) whose foot is hidden: use the floor line
           under it.

Method: LSD segments; near-vertical ones (within 6 deg, longer than 150 px) give the vertical vanishing point by
weighted least squares; the others give the depth vanishing point by RANSAC (1.5 deg) and refinement. Principal point
at the image centre; f from the two points' orthogonality: f^2 = -(vd - c).(vv - c). On the laundromat render: f 1254
px (75 deg across), 4.2 deg down, 7 deg right; the room's edges drawn back over the picture fell on its corners.

Also importable: load(cam.json) -> Cam with ray(px,py), hit(px,py,axis,value), proj(P).
"""
import argparse
import json
import sys

import numpy as np


class Cam:
    def __init__(s, d):
        s.d = d; s.f = d['f']; s.cx, s.cy = d['cx'], d['cy']; s.W, s.H = d['W'], d['H']
        s.M = np.array(d['M'])            # cv-camera coords (x right, y down, z forward) of the world axes: c = M @ w
        s.K = np.array([[s.f, 0, s.cx], [0, s.f, s.cy], [0, 0, 1.]]); s.Ki = np.linalg.inv(s.K)
        s.pos = np.array([0, 0, d.get('h', 1.0)])

    def ray(s, px, py):
        w = s.M.T @ (s.Ki @ np.array([px, py, 1.])); return w / np.linalg.norm(w)

    def hit(s, px, py, axis, value):
        """the world point where pixel (px,py)'s ray meets the plane world[axis] == value (0 x, 1 y, 2 z)"""
        r = s.ray(px, py); t = (value - s.pos[axis]) / r[axis]; return s.pos + t * r

    def proj(s, P):
        c = s.M @ (np.asarray(P, float) - s.pos); p = s.K @ c; return p[:2] / p[2]


def load(path):
    return Cam(json.load(open(path)))


def _hom(S):
    P = np.c_[S[:, :2], np.ones(len(S))]; Q = np.c_[S[:, 2:4], np.ones(len(S))]
    H = np.cross(P, Q); return H / np.linalg.norm(H[:, :2], axis=1, keepdims=True)


def main():
    import cv2
    ap = argparse.ArgumentParser(); ap.add_argument('img'); ap.add_argument('--out', default='cam.json')
    ap.add_argument('--overlay'); ap.add_argument('--vp'); ap.add_argument('--scale')
    a = ap.parse_args()
    im = cv2.imread(a.img); H, W = im.shape[:2]; g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    L = cv2.createLineSegmentDetector(0).detect(g)[0].reshape(-1, 4)      # (N,1,4) or (N,4) by version
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1]); ang = np.degrees(np.arctan2(L[:, 3] - L[:, 1], L[:, 2] - L[:, 0])) % 180
    V = L[(np.abs(ang - 90) < 6) & (ln > 150)]
    if len(V) < 4: sys.exit('too few vertical lines')
    Hv = _hom(V); w = np.hypot(V[:, 2] - V[:, 0], V[:, 3] - V[:, 1])
    vv = np.linalg.svd(Hv * np.sqrt(w)[:, None])[2][-1]
    if abs(vv[2]) < 1e-12: sys.exit('verticals are parallel in the picture (no tilt): f cannot come from them')
    vv = vv / vv[2]
    O = L[(ln > 60) & (np.abs(ang - 90) >= 3) & (ang >= 3) & (ang <= 177)]
    if a.vp:
        vd = np.array([*map(float, a.vp.split(',')), 1.])
    else:
        Ho = _hom(O); wo = np.hypot(O[:, 2] - O[:, 0], O[:, 3] - O[:, 1]); mids = (O[:, :2] + O[:, 2:4]) / 2
        d1 = O[:, 2:4] - O[:, :2]; rng = np.random.default_rng(0); best = None
        for _ in range(5000):
            i, j = rng.choice(len(O), 2, replace=False); v = np.cross(Ho[i], Ho[j])
            if abs(v[2]) < 1e-9: continue
            v = v / v[2]
            if not (-W < v[0] < 2 * W and -H < v[1] < 2 * H): continue
            d2 = v[:2] - mids
            cs = np.abs((d1 * d2).sum(1)) / (np.linalg.norm(d1, axis=1) * np.linalg.norm(d2, axis=1) + 1e-9)
            inl = np.degrees(np.arccos(np.clip(cs, 0, 1))) < 1.5; sc = (wo * inl).sum()
            if best is None or sc > best[0]: best = (sc, inl)
        A = Ho[best[1]]; sol = np.linalg.lstsq(A[:, :2], -A[:, 2], rcond=None)[0]; vd = np.array([*sol, 1.])
        print(f'depth vp from {best[1].sum()} of {len(O)} oblique lines')
    c = np.array([W / 2, H / 2]); f2 = -np.dot(vd[:2] - c, vv[:2] - c)
    if f2 <= 0: sys.exit(f'f^2 = {f2:.0f} < 0: the depth vp and the vertical vp are not orthogonal; check --vp')
    f = float(np.sqrt(f2)); K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1]]); Ki = np.linalg.inv(K)
    dd = Ki @ vd; dd /= np.linalg.norm(dd); u = Ki @ vv; u /= np.linalg.norm(u)
    if u[1] > 0: u = -u
    X = np.cross(dd, u); X /= np.linalg.norm(X); Y = dd; Z = np.cross(X, Y); M = np.c_[X, Y, Z]
    out = dict(W=W, H=H, f=f, cx=float(c[0]), cy=float(c[1]), M=M.tolist(), h=1.0, vp_depth=vd[:2].tolist(),
               vp_vertical=vv[:2].tolist(), hfov_deg=float(2 * np.degrees(np.arctan(W / 2 / f))),
               pitch_down_deg=float(np.degrees(np.arcsin(-u[2]))), yaw_right_deg=float(-np.degrees(np.arctan2(dd[0], dd[2]))))
    if a.scale:
        fx, fy, tx, ty, hm = map(float, a.scale.split(',')); cam = Cam(out)
        foot = cam.hit(fx, fy, 2, 0.0); r = cam.ray(tx, ty)
        # the top lies straight above the foot: closest point of its ray to the vertical through the foot
        A = np.c_[r, -np.array([0, 0, 1.])]; t = np.linalg.lstsq(A, foot - cam.pos, rcond=None)[0]
        ztop = (cam.pos + t[0] * r)[2]; out['h'] = float(hm / ztop)
        print(f'scale: that edge is {ztop:.3f} h tall -> camera height {out["h"]:.3f} m')
    json.dump(out, open(a.out, 'w'), indent=1)
    print(f"f {f:.1f} px, hfov {out['hfov_deg']:.1f} deg, pitch down {out['pitch_down_deg']:.2f}, yaw right "
          f"{out['yaw_right_deg']:.2f}, depth vp {vd[0]:.0f},{vd[1]:.0f}, vertical vp {vv[0]:.0f},{vv[1]:.0f}")
    if a.overlay:
        ov = im.copy()
        for x1, y1, x2, y2 in V: cv2.line(ov, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        for x1, y1, x2, y2 in O: cv2.line(ov, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)
        cv2.circle(ov, (int(vd[0]), int(vd[1])), 12, (255, 0, 255), 3); cv2.imwrite(a.overlay, ov)


if __name__ == '__main__':
    main()
