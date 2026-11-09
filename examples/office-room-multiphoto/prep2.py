"""Second texture pass: blinds, outdoor backdrop, corridor terrazzo tile, bookcase front (handles removed) and
book/item column profile, clock face, laptop keyboard.   uv run --with numpy --with opencv-python-headless --with pillow python prep2.py"""
import json, cv2, numpy as np
from camlib import load
from PIL import Image, ImageDraw, ImageFont
cams = load('cams_final.json'); R = json.load(open('room_final.json')); win = cv2.imread('win.jpg'); out = {}
WINS = {'A': (1.46, 2.50), 'B': (0.20, 1.24)}
# ---- blinds (fabric between the blind bottom bar 1.51 and the roller 2.29), a few cm inside the reveal
for k, (x0, x1) in WINS.items():
    b, _ = cams['win'].rectify(win, (x1, -0.03, 1.49), (-1, 0, 0), (0, 0, 1), x1 - x0, 2.30 - 1.49, 500)
    cv2.imwrite(f'tex/blind_{k}.jpg', b, [cv2.IMWRITE_JPEG_QUALITY, 92])
# ---- outdoor view seen below the blinds: rectify on the glass plane, wipe out the white PVC frames
view = []
for k, (x0, x1) in WINS.items():
    v, _ = cams['win'].rectify(win, (x1, -0.15, 1.06), (-1, 0, 0), (0, 0, 1), x1 - x0, 0.46, 500)
    hsv = cv2.cvtColor(v, cv2.COLOR_BGR2HSV); m = ((hsv[..., 1] < 45) & (hsv[..., 2] > 150)).astype(np.uint8)
    m = cv2.dilate(m, np.ones((7, 7), np.uint8)); v = cv2.inpaint(v, m * 255, 15, cv2.INPAINT_TELEA); view.append(v)
v = np.concatenate(view[::-1], 1)          # B (x small) on the left when seen from outside? keep room-view order: A left, B right
v = np.concatenate([view[0], view[1]], 1)
v = cv2.resize(v, (v.shape[1], int(v.shape[0] * 2.2)))  # the backdrop is taller than the strip under the blinds
sky = np.zeros((int(v.shape[0] * 0.6), v.shape[1], 3), np.uint8); sky[:] = (235, 228, 214)
grad = np.linspace(0, 1, sky.shape[0])[:, None, None]; sky = (sky * (0.85 + 0.15 * grad)).astype(np.uint8)
cv2.imwrite('tex/outdoor.jpg', np.concatenate([sky, v], 0), [cv2.IMWRITE_JPEG_QUALITY, 90])
# (corridor terrazzo is generated separately from the real floor speckle; not overwritten here)
# ---- bookcase front: handles inpainted (3D handles replace them), brightened like the first pass
bk = cv2.imread('tex/bookcase.png')
m = np.zeros(bk.shape[:2], np.uint8)
for (c0, c1) in ((136, 152), (172, 188)): m[452:492, c0:c1] = 1
g = cv2.cvtColor(bk, cv2.COLOR_BGR2GRAY); m = (m & (g < np.median(g[452:492, 120:200]) - 12)).astype(np.uint8)
m = cv2.dilate(m, np.ones((5, 5), np.uint8)); bk = cv2.inpaint(bk, m * 255, 5, cv2.INPAINT_TELEA)
cv2.imwrite('tex/bookcase_front.jpg', np.clip(bk.astype(np.float32) * 1.25, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
# ---- book / item columns per compartment: top row of the contents per texture column
lab = cv2.cvtColor(bk, cv2.COLOR_BGR2LAB).astype(np.float32)
COMP = {'c1': (42, 140), 'c2': (152, 282), 'c3': (300, 420)}   # texture rows (400 px / m, row 0 = z 1.83)
cols = {}
for k, (r0, r1) in COMP.items():
    bg = np.median(lab[r0 + 2:r0 + 10, 20:300], axis=(0,))            # per-column background from the empty top band
    bg = cv2.GaussianBlur(bg.reshape(1, -1, 3), (0, 0), (9, 0)).reshape(-1, 3) if False else bg
    tops = []
    for c in range(20, 300):
        dcol = np.linalg.norm(lab[r0:r1, c] - np.median(lab[r0 + 2:r0 + 10, max(20, c - 30):c + 30].reshape(-1, 3), 0), axis=1)
        on = dcol > 22
        run = np.convolve(on.astype(int), np.ones(4, int), 'valid') >= 4
        idx = np.argmax(run) if run.any() else None
        top = r0 + idx if idx is not None and on[idx:].mean() > 0.55 else None
        tops.append(int(top) if top is not None else None)
    cols[k] = tops
json.dump({'comp': COMP, 'tops': cols, 'col0': 20}, open('tex/bookcols.json', 'w'))
vis = bk.copy()
for k, tops in cols.items():
    for i, t_ in enumerate(tops):
        if t_ is not None: vis[t_:COMP[k][1], 20 + i] = (vis[t_:COMP[k][1], 20 + i] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
cv2.imwrite('g/bookcols.png', cv2.resize(vis, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
# ---- clock face (white dial, black numerals and hands) and laptop keyboard
S = 512; im = Image.new('RGB', (S, S), (238, 236, 230)); dr = ImageDraw.Draw(im)
try: font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman.ttf', 52)
except Exception: font = ImageFont.load_default()
import math
for h in range(1, 13):
    a = math.radians(h * 30 - 90); x, y = S / 2 + 190 * math.cos(a), S / 2 + 190 * math.sin(a)
    dr.text((x, y), str(h), fill=(25, 25, 25), font=font, anchor='mm')
for mnt in range(60):
    a = math.radians(mnt * 6 - 90); r0 = 238 if mnt % 5 else 228
    dr.line([(S / 2 + r0 * math.cos(a), S / 2 + r0 * math.sin(a)), (S / 2 + 248 * math.cos(a), S / 2 + 248 * math.sin(a))], fill=(30, 30, 30), width=3 if mnt % 5 == 0 else 1)
for ang, ln, wd in ((math.radians(10 * 30 + 9 * 0.5 - 90), 120, 10), (math.radians(9 * 6 - 90), 175, 6)):
    dr.line([(S / 2, S / 2), (S / 2 + ln * math.cos(ang), S / 2 + ln * math.sin(ang))], fill=(20, 20, 20), width=wd)
dr.ellipse([S / 2 - 10, S / 2 - 10, S / 2 + 10, S / 2 + 10], fill=(20, 20, 20)); im.save('tex/clockface.png')
K = Image.new('RGB', (1024, 420), (38, 39, 43)); dr = ImageDraw.Draw(K)
rows = [(14, 0.75), (14, 1.0), (13, 1.0), (12, 1.0), (11, 1.0)]
y = 20
for i, (n, hgt) in enumerate(rows):
    kw = (1024 - 40) / n; kh = 62 * hgt
    for j in range(n): dr.rounded_rectangle([20 + j * kw + 3, y, 20 + (j + 1) * kw - 3, y + kh], 6, fill=(18, 18, 20))
    y += kh + 8
dr.rounded_rectangle([20 + 3 * 82, y, 20 + 9 * 82, y + 62], 6, fill=(18, 18, 20)); K.save('tex/keyboard.png')
json.dump(out, open('tex/prep2.json', 'w'))
print('ok')
