"""ek3 camera from the corridor vanishing point + known cross-section, refined on our door frame and notice board."""
import json, numpy as np
from scipy.optimize import least_squares
from camlib import Cam
R = json.load(open('room_final.json')); YC = R['L'] + R['t_wall']; CJ = json.load(open('tex/corridor.json'))
b0, b1, bz0, bz1 = CJ['noticeboard']
VP = np.array([726.0, 823.0])
OBS = [((R['dx0'], YC, 2.12), (1450, 430)), ((R['dx1'], YC, 2.12), (1295, 470)), ((R['dx1'], YC, 0.0), (1300, 1600)),
       ((b1, YC, bz1), (1232, 750)), ((b0, YC, bz1), (1268, 745)), ((b1, YC, bz0), (1232, 865)), ((b0, YC, bz0), (1268, 860)),
       ((6.0, YC, 0.0), None), ]
def make(q):
    xc, yc, zc, f, roll = q
    d = np.array([(VP[0] - 768) / f, (VP[1] - 1024) / f, 1.0]); d /= np.linalg.norm(d)
    up = np.array([np.sin(roll), -np.cos(roll), 0.0]); up -= d * up.dot(d); up /= np.linalg.norm(up)
    col0, col2 = d, up; col1 = np.cross(col2, col0)
    Rm = np.stack([col0, col1, col2], 1)
    return dict(pos=[xc, yc, zc], R=Rm.tolist(), f=f, cx=768, cy=1024, W=1536, H=2048)
# lines on the right wall along x (y = YC): skirting z 0 through (1270,1545), dado z 1.10 through (1280,1050)
LINES = [((YC, 0.0), (1270, 1545)), ((YC, 1.10), (1280, 1050)), ((7.98, 0.0), (530, 1220))]
def res(q):
    c = Cam(make(q)); r = []
    for P, uv in OBS:
        if uv is None: continue
        p, z = c.proj(P); r += list((p - np.array(uv)) / 10.0)
    for (yw, zw), uv in LINES:     # the image point must lie on the projected line: distance via two points on it
        p1, _ = c.proj((3.0, yw, zw)); p2, _ = c.proj((12.0, yw, zw))
        dv = p2 - p1; n = np.array([-dv[1], dv[0]]) / np.linalg.norm(dv); r.append(n.dot(np.array(uv) - p1) / 5.0)
    return np.array(r)
best = None
for xc in (-4.5, -3.6, -2.5):
    for f in (1600, 2300, 3000):
        s = least_squares(res, [xc, 6.98, 1.59, f, 0.0], bounds=([-8, 6.0, 1.2, 900, -0.1], [-0.3, 7.9, 1.9, 4000, 0.1]))
        if best is None or s.cost < best.cost: best = s
q = best.x; c = make(q); print('pos', np.round(q[:3], 2), 'f %.0f roll %.3f' % (q[3], q[4]), 'res', np.round(np.abs(res(q)), 1))
C = json.load(open('cams_final.json')); C['ek3'] = c; json.dump(C, open('cams_final.json', 'w'), indent=1)
cam = Cam(c)
def onwall(u, v, yw): return np.round(cam.hit(u, v, 1, yw), 2)
for nm, uv, yw in (('cab far top', (1123, 700), YC), ('cab near top', (1172, 688), YC), ('cab near bottom', (1173, 995), YC), ('cab far bottom', (1123, 975), YC),
                   ('pipe', (1117, 1300), YC), ('next door near', (1110, 640), YC), ('win start top', (425, 620), 7.98), ('win start sill', (430, 1010), 7.98),
                   ('win far', (615, 800), 7.98), ('end door floor', (760, 960), None)):
    if yw is None: print(nm, np.round(cam.hit(*uv, 2, 0.0), 2)); continue
    print(nm, onwall(*uv, yw))
for nm, uv, zz in (('beam1 top', (700, 350), 3.0), ('beam1 bottom', (700, 540), 2.45), ('beam2 top', (700, 580), 3.0), ('fixture1', (760, 220), 3.0), ('fixture2', (750, 560), 3.0)):
    print(nm, np.round(cam.hit(*uv, 2, zz), 2))
