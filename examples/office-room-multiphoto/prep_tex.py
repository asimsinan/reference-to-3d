"""Floor tile (seamless, de-lit), wall colour, decal alphas.  uv run --with numpy --with opencv-python-headless python prep_tex.py"""
import json
import cv2
import numpy as np

def delight(im, s=60):
    f = im.astype(np.float32); b = cv2.GaussianBlur(f, (0, 0), s)
    return np.clip(f / np.maximum(b, 1) * b.reshape(-1, 3).mean(0), 0, 255)

def seamless(t):
    h, w = t.shape[:2]
    r = np.roll(np.roll(t, h // 2, 0), w // 2, 1)
    wy = 1 - np.abs(np.linspace(-1, 1, h)); wx = 1 - np.abs(np.linspace(-1, 1, w))
    m = np.clip(np.minimum.outer(wy, wx) * 3, 0, 1)[..., None]
    return t * m + r * (1 - m)

fl = cv2.imread('tex/floor_d.png')[40:480, 130:420]          # 0.97 x 1.47 m at 300 ppm, no chair, no props
fl = seamless(delight(fl))
fl = cv2.resize(fl, (int(fl.shape[1] * 1024 / fl.shape[0]), 1024), interpolation=cv2.INTER_CUBIC)
cv2.imwrite('tex/floor_tile.jpg', fl.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
tile_m = (290 / 300, 440 / 300)

# wall colour: median of plain wall patches in door.jpg rectified door decal border and the window wall below the sill
d = cv2.imread('tex/door.png'); ww = cv2.imread('tex/window_wall.png')
patch = np.concatenate([d[:60, :].reshape(-1, 3), d[:, -40:].reshape(-1, 3)])
wall = np.median(patch, 0)
print('wall colour BGR', wall, 'window wall bottom', np.median(ww[-40:, 100:900].reshape(-1, 3), 0))

def decal(name, feather):
    im = cv2.imread(f'tex/{name}.png').astype(np.float32); h, w = im.shape[:2]
    a = np.ones((h, w), np.float32)
    for k, n in enumerate(feather):  # left, right, bottom, top in px
        if n <= 0: continue
        ramp = np.linspace(0, 1, n)
        if k == 0: a[:, :n] *= ramp
        if k == 1: a[:, -n:] *= ramp[::-1]
        if k == 2: a[-n:, :] *= ramp[::-1, None]
        if k == 3: a[:n, :] *= ramp[:, None]
    out = np.dstack([im, a * 255]).astype(np.uint8); cv2.imwrite(f'tex/{name}_rgba.png', out)

decal('door', (40, 40, 0, 40)); decal('switch', (20, 20, 20, 20))
# window wall: cut at x = d (the chase), full, feather only the bottom
R = json.load(open('room_final.json'))
ww = cv2.imread('tex/window_wall.png'); cut = int((R['W'] - R['d']) * 400); cv2.imwrite('tex/window_wall_c.png', ww[:, :cut])
decal('window_wall_c', (0, 0, 30, 0))
json.dump({'wall_bgr': wall.tolist(), 'floor_tile_m': tile_m}, open('tex/tex.json', 'w'))

# --- colour: floor tile to the mean floor colour of the warmer iPhone photos; decals lifted to white-paint albedo
lg = cv2.imread('long.jpg'); rf = cv2.imread('right.jpg')
fmean = np.concatenate([lg[1250:1500, 560:900].reshape(-1, 3), rf[1300:1500, 300:900].reshape(-1, 3)]).astype(np.float32).mean(0)
ft = cv2.imread('tex/floor_tile.jpg').astype(np.float32)
ft = np.clip(ft * (fmean / ft.reshape(-1, 3).mean(0)), 0, 255)
cv2.imwrite('tex/floor_tile.jpg', ft.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
print('floor mean BGR', fmean)
WALL = np.array([226., 229., 229.])          # BGR albedo of the white paint used for all walls
for n, ref in (('door_rgba', wall), ('window_wall_c_rgba', np.median(ww[-40:, 100:900].reshape(-1, 3), 0)), ('switch_rgba', wall)):
    im = cv2.imread(f'tex/{n}.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
    im[..., :3] = np.clip(im[..., :3] * (WALL / ref), 0, 255); cv2.imwrite(f'tex/{n}.png', im.astype(np.uint8))
# emission mask for the window wall: bright blinds and glass inside the two window frames
w = cv2.imread('tex/window_wall_c.png').astype(np.float32); lum = w.mean(2)
m = np.zeros_like(lum)
for x0, x1 in ((R['xB1'], R['xB0']), (R['xA1'], min(R['xA0'], R['W']))):
    u0, u1 = int((R['W'] - x1) * 400), int((R['W'] - x0) * 400)
    z0, z1 = int((2.81 - R['zb']) * 400) , int((2.81 - 0.95) * 400)
    m[z0:z1, u0:u1] = 1
m = cv2.GaussianBlur(m * np.clip((lum - 120) / 100, 0, 1), (0, 0), 1.5)
cv2.imwrite('tex/window_emit.png', (m * 255).astype(np.uint8))
json.dump({'wall_bgr': WALL.tolist(), 'floor_tile_m': tile_m}, open('tex/tex.json', 'w'))

# --- maple melamine tile from the plain tall-cabinet panel (de-lit, seamless); its colour from the bookcase doors
tc = cv2.imread('tex/tallcab.png')[100:600, 40:170]
mp = seamless(delight(tc, 30))
bk = cv2.imread('tex/bookcase.png'); doors = bk[int(bk.shape[0] * 0.70):int(bk.shape[0] * 0.95), 20:-20].reshape(-1, 3).astype(np.float32)
target = np.array([150., 186., 214.])   # BGR: light maple melamine (photos read ~25 % darker)
mp = np.clip(mp * (target / mp.reshape(-1, 3).mean(0)), 0, 255)
mp = cv2.resize(mp, (256, 1024), interpolation=cv2.INTER_CUBIC)
cv2.imwrite('tex/maple.jpg', mp.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
print('maple BGR', target)
for n in ('bookcase', 'tallcab'):
    im = cv2.imread(f'tex/{n}.png').astype(np.float32) * 1.25
    cv2.imwrite(f'tex/{n}_lit.jpg', np.clip(im, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 92])
