import json, numpy as np, cv2
from pnp import pnp
R = json.load(open('room_final.json')); YC = R['L'] + R['t_wall']
CJ = json.load(open('tex/corridor.json'))
n0, n1, nz0, nz1 = CJ['nameplate']; b0, b1, bz0, bz1 = CJ['noticeboard']
P = [((R['dx1'], YC, 2.12), (157, 628)), ((R['dx0'], YC, 2.12), (318, 700)), ((R['dx0'], YC, 0), (318, 1880)),
     ((n1, YC, nz1), (55, 885)), ((n0, YC, nz1), (150, 905)), ((n1, YC, nz0), (57, 965)), ((n0, YC, nz0), (150, 982)),
     ((b1, YC, bz1), (50, 1015)), ((b0, YC, bz1), (158, 1018)), ((b1, YC, bz0), (55, 1235)), ((b0, YC, bz0), (160, 1205))]
# coplanar points only: add the f prior from the lens (main 1x ~1480) by scanning and reporting
c, e = pnp([p for p, _ in P], [q for _, q in P], 1536, 2048, fr=(700, 2600))
print('f', c['f'], 'pos', np.round(c['pos'], 2), 'err', np.round(e, 1))
from camlib import Cam
cam = Cam(c)
for nm, px in {'glass_bl': (420, 1780), 'glass_br': (1395, 1800), 'end_corner_floor': (395, 1790), 'glass_top_l': (440, 620),
               'soffit_bottom_l': (350, 560), 'ek4_floor_center': (768, 1900)}.items():
    print(nm, np.round(cam.hit(*px, 2, 0.0) if 'floor' in nm or nm.endswith(('bl', 'br')) else cam.ray(*px), 2))
C = json.load(open('cams_final.json')); C['ek4'] = c; json.dump(C, open('cams_final.json', 'w'), indent=1)
