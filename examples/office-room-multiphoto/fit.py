"""Bundle adjustment: room parameters + 6 cameras from the hand-read observations in obs.py.

  uv run --with numpy --with scipy --with opencv-python-headless python fit.py
Writes room.json (parameters), cams.json (per photo: pos, R (world->cam, OpenCV axes), f, cx, cy, W, H) and
overlay_<name>.jpg (the solved room's edges over each photo) + residuals per observation.
"""
import json
import sys

import numpy as np
from scipy.optimize import least_squares

from obs import P0, OBS, CAM0, SIZE, points, DH

PN = list(P0.keys())
# focal priors (mean, sigma, bounds): iPhone 1x ~1538 px at 2048 long side, ultrawide ~800
FP = {'win': (1480, 40, (1380, 1600)), 'win2': (1480, 40, (1380, 1600)), 'door': (1480, 40, (1380, 1600)),
      'long': (790, 30, (700, 900)), 'left': (790, 40, (680, 920)), 'right': (790, 40, (680, 920))}
CN = [c for c in CAM0.keys() if c in (sys.argv[1].split(',') if len(sys.argv) > 1 else CAM0.keys())]


def rot(yaw, pitch, roll):
    yw, pt, rl = np.radians([yaw, pitch, roll])
    fwd = np.array([np.cos(yw) * np.cos(pt), np.sin(yw) * np.cos(pt), -np.sin(pt)])
    right = np.cross(fwd, [0, 0, 1.]); right /= np.linalg.norm(right)
    down = np.cross(fwd, right)
    # roll about fwd
    c, s = np.cos(rl), np.sin(rl)
    right, down = c * right + s * down, -s * right + c * down
    return np.stack([right, down, fwd])


def unpack(x):
    P = dict(zip(PN, x[:len(PN)]))
    cams = {}
    for i, n in enumerate(CN):
        v = x[len(PN) + 7 * i: len(PN) + 7 * (i + 1)]
        cams[n] = dict(pos=v[:3], R=rot(v[3], v[4], v[5]), f=v[6], yaw=v[3], pitch=v[4], roll=v[5])
    return P, cams


def proj(cam, Pw, name):
    Wd, Ht = SIZE[name]
    c = cam['R'] @ (Pw - cam['pos'])
    if c[2] <= 0.05: return np.array([np.nan, np.nan])
    return np.array([cam['f'] * c[0] / c[2] + Wd / 2, cam['f'] * c[1] / c[2] + Ht / 2])


def residuals(x):
    P, cams = unpack(x); pts = points(P); r = []
    for n in CN:
        for k, uv in OBS[n].items():
            p = proj(cams[n], pts[k], n)
            if np.isnan(p[0]): r += [1000., 1000.]
            else: r += list(p - np.array(uv))
    # soft priors: f per lens class (weak), keep cameras ~1.3-1.6 m up (weak)
    for n in CN:
        r.append((cams[n]['f'] - FP[n][0]) / FP[n][1])
        r.append((cams[n]['pos'][2] - 1.5) / 0.4)
        r.append(cams[n]['roll'] / 1.0)
        if n in ('door', 'win', 'long'): r.append(cams[n]['pitch'] / 2.0)
    r.append((P['zd'] - 0.74) / 0.02)
    # physical priors: a floor gap between desk front and coffee table (win2 shows one), a standard desk depth
    r.append(min(0.0, P['ty0'] - P['yf'] - 0.25) / 0.005)
    r.append((P['yf'] - P['yb'] - 0.70) / 0.04)
    r.append((P['tz'] - 0.42) / 0.04)
    return np.array(r)


def main():
    x0 = [P0[k] for k in PN]
    for n in CN:
        pos, yaw, pitch, f = CAM0[n]; x0 += [*pos, yaw, pitch, 0.0, f]
    x0 = np.array(x0, float)
    lo = -np.inf * np.ones_like(x0); hi = np.inf * np.ones_like(x0)
    B = dict(tz=(0.38, 0.55), rzt=(0.6, 1.3), rzb=(0.5, 1.2), W=(2.5, 3.8), L=(4.0, 9.0), H=(2.5, 3.2), d=(0.03, 0.4), d2=(0.05, 0.5), r0=(0.5, 4.5), rz=(1.9, 2.8), p=(0.1, 0.6),
             tcd=(0.3, 0.65), tcw=(0.4, 1.0), tch=(1.5, 2.3), bd=(0.25, 0.6), bw=(0.4, 1.0), bh=(1.5, 2.3))
    for i, k in enumerate(PN):
        if k in B: lo[i], hi[i] = B[k]
    for i, n in enumerate(CN):
        j = len(PN) + 7 * i
        lo[j:j + 3] = (0.1, 0.1, 0.6); hi[j:j + 3] = (3.6, 8.5, 2.1)
        if n in ('door', 'win', 'long'): lo[j + 4], hi[j + 4] = (-3, 4); lo[j + 5], hi[j + 5] = (-0.8, 0.8)
        else: lo[j + 5], hi[j + 5] = (-2.5, 2.5)
        pass
        lo[j + 6], hi[j + 6] = FP[n][2]
    res = least_squares(residuals, x0, bounds=(lo, hi), loss='soft_l1', f_scale=15.0, max_nfev=20000, x_scale='jac')
    P, cams = unpack(res.x)
    r = residuals(res.x)
    print('room:', {k: round(float(v), 3) for k, v in P.items()})
    i = 0
    for n in CN:
        c = cams[n]
        print(f"{n}: pos ({c['pos'][0]:.2f},{c['pos'][1]:.2f},{c['pos'][2]:.2f}) yaw {c['yaw']:.1f} pitch {c['pitch']:.1f} roll {c['roll']:.2f} f {c['f']:.0f}")
        for k in OBS[n]:
            e = r[i:i + 2]; i += 2
            flag = ' <<<' if np.hypot(*e) > 12 else ''
            print(f"   {k:6s} err ({e[0]:+6.1f},{e[1]:+6.1f}){flag}")
    json.dump({k: float(v) for k, v in P.items()} | {'DH': DH}, open('room.json', 'w'), indent=1)
    json.dump({n: dict(pos=c['pos'].tolist(), R=c['R'].tolist(), f=float(c['f']), cx=SIZE[n][0] / 2, cy=SIZE[n][1] / 2,
                       W=SIZE[n][0], H=SIZE[n][1], yaw=float(c['yaw']), pitch=float(c['pitch']), roll=float(c['roll']))
               for n, c in cams.items()}, open('cams.json', 'w'), indent=1)
    overlay(P, cams)


def edges(P):
    """3D segments of the solved room, for drawing."""
    W, L, H, d, d2, r0, rz, p = (P[k] for k in 'W L H d d2 r0 rz p'.split())
    E = []
    box = lambda x0, x1, y0, y1, z0, z1: [((x0, y0, z0), (x1, y0, z0)), ((x1, y0, z0), (x1, y1, z0)), ((x1, y1, z0), (x0, y1, z0)), ((x0, y1, z0), (x0, y0, z0)),
                                          ((x0, y0, z1), (x1, y0, z1)), ((x1, y0, z1), (x1, y1, z1)), ((x1, y1, z1), (x0, y1, z1)), ((x0, y1, z1), (x0, y0, z1)),
                                          ((x0, y0, z0), (x0, y0, z1)), ((x1, y0, z0), (x1, y0, z1)), ((x1, y1, z0), (x1, y1, z1)), ((x0, y1, z0), (x0, y1, z1))]
    # right wall / door wall / window wall / floor / ceiling (main box, but the left wall is x=0 only between r0 and L-p)
    E += [((W, 0, 0), (W, L, 0)), ((W, 0, H), (W, L, H)), ((W, L, 0), (W, L, H)), ((W, 0, 0), (W, 0, H))]
    E += [((d2, L, 0), (W, L, 0)), ((d2, L, H), (W, L, H)), ((d2, L, 0), (d2, L, H))]
    E += [((d, 0, 0), (W, 0, 0)), ((d, 0, H), (W, 0, H)), ((d, 0, 0), (d, 0, H))]
    # chase, beam, pilaster, recessed wall
    E += [((d, 0, 0), (d, r0, 0)), ((d, r0, 0), (d, r0, rz)), ((d, r0, rz), (0, r0, rz)), ((0, r0, rz), (0, r0, 0)), ((0, r0, 0), (d, r0, 0)),
          ((d, 0, H), (d, L - p, H)), ((d, r0, rz), (d, L - p, rz)), ((0, r0, rz), (0, L - p, rz)), ((0, r0, 0), (0, L - p, 0)),
          ((0, L - p, 0), (0, L - p, rz)), ((0, L - p, rz), (d, L - p, rz)), ((d, L - p, rz), (d, L - p, H)), ((d, L - p, H), (d2, L - p, H)),
          ((d2, L - p, H), (d2, L - p, 0)), ((d2, L - p, 0), (0, L - p, 0)), ((d2, L - p, 0), (d2, L, 0)), ((d2, L - p, H), (d2, L, H))]
    # door frame
    E += [((P['dx0'], L, 0), (P['dx0'], L, DH)), ((P['dx0'], L, DH), (P['dx1'], L, DH)), ((P['dx1'], L, DH), (P['dx1'], L, 0))]
    # windows (sill to blind top) and conduit
    for a, b in (('xA0', 'xA1'), ('xB0', 'xB1')):
        E += [((P[a], 0, P['zs']), (P[b], 0, P['zs'])), ((P[a], 0, P['zb']), (P[b], 0, P['zb'])), ((P[a], 0, P['zs']), (P[a], 0, P['zb'])), ((P[b], 0, P['zs']), (P[b], 0, P['zb']))]
    E += [((d, 0, P['zc']), (W, 0, P['zc']))]
    E += box(W - P['tcd'], W, P['tc0'], P['tc0'] + P['tcw'], 0, P['tch'])
    E += box(W - P['bd'], W, P['b0'], P['b0'] + P['bw'], 0, P['bh'])
    E += [((P['xl'], P['yl0'], H), (P['xl'], P['yl1'], H))]
    E += box(P['tx0'], P['tx1'], P['ty0'], P['ty1'], 0, P['tz'])
    E += box(0.1, P['xa'], P['yb'], P['yf'], P['zd'] - 0.03, P['zd'])
    E += [((W - 0.02, P['ry0'], P['rzt']), (W - 0.02, P['ry1'], P['rzt'])), ((W - 0.02, P['ry0'], P['rzb']), (W - 0.02, P['ry1'], P['rzb']))]
    return E


def overlay(P, cams, names=None):
    import cv2
    E = edges(P); pts = points(P)
    for n in (names or CN):
        im = cv2.imread(f'{n}.jpg'); c = cams[n]
        for a, b in E:
            pa, pb = proj(c, np.array(a, float), n), proj(c, np.array(b, float), n)
            if np.isnan(pa[0]) or np.isnan(pb[0]): continue
            cv2.line(im, tuple(np.round(pa).astype(int)), tuple(np.round(pb).astype(int)), (0, 255, 255), 2, cv2.LINE_AA)
        for k, uv in OBS[n].items():
            cv2.circle(im, tuple(map(int, uv)), 9, (0, 0, 255), 2)
            p = proj(c, pts[k], n)
            if not np.isnan(p[0]): cv2.circle(im, tuple(np.round(p).astype(int)), 5, (255, 0, 0), -1)
        cv2.imwrite(f'overlay_{n}.jpg', im)
        sm = cv2.resize(im, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA); cv2.imwrite(f'g/ov_{n}.jpg', sm)


if __name__ == '__main__':
    main()
