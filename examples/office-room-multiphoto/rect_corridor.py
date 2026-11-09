"""Corridor/door textures: door leaf (handle removed), corridor wall plates, corridor floor tile, glass-door backdrop,
wall paint colours.  uv run --with numpy --with opencv-python-headless python rect_corridor.py"""
import json, os, cv2, numpy as np
from camlib import load
cams = load('cams_final.json'); R = json.load(open('room_final.json')); L, t = R['L'], R['t_wall']; YC = L + t
img = {n: cv2.imread(f'{n}.jpg') for n in ('door', 'corridor', 'doorout')}
k, d, dr = cams['corridor'], cams['doorout'], cams['door']
os.makedirs('tex', exist_ok=True); out = {}

def bounds(cam, px, plane_axis, val):
    P = np.array([cam.hit(x, y, plane_axis, val) for x, y in px]); return P.min(0), P.max(0)

# ---- door leaf, room side (from door.jpg), leaf clear size
LX0, LX1, LZ0, LZ1 = 0.285, 1.175, 0.01, 2.055
leaf, _ = dr.rectify(img['door'], (LX0, L, LZ0), (1, 0, 0), (0, 0, 1), LX1 - LX0, LZ1 - LZ0, 500)
g = cv2.cvtColor(leaf, cv2.COLOR_BGR2GRAY); h, w = g.shape
# handle + escutcheon: dark pixels in the handle box -> inpaint (a 3D handle replaces them)
box = np.zeros_like(g); hx0, hx1 = int(w * 0.72), w; hz0, hz1 = int(h * (1 - 1.22 / 2.045)), int(h * (1 - 0.88 / 2.045))
box[hz0:hz1, hx0:hx1] = 1
m = ((g < np.median(g[box > 0]) - 18) & (box > 0)).astype(np.uint8)
m = cv2.dilate(m, np.ones((9, 9), np.uint8))
leaf = cv2.inpaint(leaf, m * 255, 9, cv2.INPAINT_TELEA)
cv2.imwrite('tex/door_leaf.jpg', leaf, [cv2.IMWRITE_JPEG_QUALITY, 92])
out['leaf'] = (LX0, LX1, LZ0, LZ1)

# ---- corridor wall plates (name plate, notice board, room sign) on the plane y = YC
plates = {'nameplate': [(286, 620), (544, 620), (286, 710), (544, 710)],
          'noticeboard': [(280, 746), (560, 746), (280, 956), (560, 956)],
          'roomsign': [(994, 150), (1084, 150), (994, 212), (1084, 212)]}
for n, px in plates.items():
    lo, hi = bounds(k, px, 1, YC)
    # seen from the corridor (looking -y) +x is to the left: u = -x so the texture reads the right way
    tex, _ = k.rectify(img['corridor'], (hi[0], YC, lo[2]), (-1, 0, 0), (0, 0, 1), hi[0] - lo[0], hi[2] - lo[2], 1200)
    cv2.imwrite(f'tex/{n}.jpg', tex, [cv2.IMWRITE_JPEG_QUALITY, 94]); out[n] = (float(lo[0]), float(hi[0]), float(lo[2]), float(hi[2]))
    print(n, np.round(lo, 3), np.round(hi, 3))

# ---- corridor floor: doorout sees it through the door (tiles with joints)
fl, ok = d.rectify(img['doorout'], (0.45, YC + 0.15, 0), (1, 0, 0), (0, 1, 0), 0.62, 1.1, 400)
cv2.imwrite('tex/corr_floor_raw.png', fl)
# ---- glass-door backdrop: what the glass shows, rectified on the glass plane
gb, _ = d.rectify(img['doorout'], (-0.01, 7.42, 0.0), (1, 0, 0), (0, 0, 1), 0.85, 2.30, 300)
cv2.imwrite('tex/glassdoor_raw.png', gb)
# ---- paint colours of the corridor wall (photo -> albedo with the room's white-paint ratio)
cw = img['corridor']
blue = np.median(cw[300:560, 20:260].reshape(-1, 3), 0); beige = np.median(cw[1300:1700, 20:260].reshape(-1, 3), 0)
out['blue_bgr'] = blue.tolist(); out['beige_bgr'] = beige.tolist()
print('corridor blue', blue, 'beige', beige)
json.dump(out, open('tex/corridor.json', 'w'), indent=1)
