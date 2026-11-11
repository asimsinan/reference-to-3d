"""Showcase: every pair is the same view twice, a present-day drone frame (ref/rN.png) and the model in real
materials rendered through that frame's solved camera (out/final_rN.png), cut with one and the same crop.
Rows: the frames whole, the model whole, the frames' upper tower (finial to cornice) closer, the model the same.
Frame 1 is not shown: it is the tower before its 2020 restoration (another cone), not the state modelled.
Writes galata_tower_showcase.jpg"""
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
FR = ('r2', 'r3', 'r4'); W, GAP = 520, 6; HF, HC = 990, 760
names = open('id/names.txt').read().split()
def ids(v):
    idm = cv2.imread('id/%s.png' % v, cv2.IMREAD_UNCHANGED); idx = np.round(idm[..., 2] / 8.0).astype(int); idx[idm[..., 3] < 128] = 0; return idx
def box(m, H, pad_top=0.03, pad_bot=0.03):
    ys, xs = np.nonzero(m); y0, y1 = ys.min(), ys.max(); h = y1 - y0
    y0 = y0 - pad_top * h; y1 = y1 + pad_bot * h; w = (y1 - y0) * W / H; cx = (xs.min() + xs.max()) / 2
    return int(cx - w / 2), int(max(y0, 0)), int(cx + w / 2), int(y1)
def crop(im, b):
    x0, y0, x1, y1 = b; p = max(0, -x0, x1 - im.shape[1], y1 - im.shape[0])
    if p: im = cv2.copyMakeBorder(im, 0, p, p, p, cv2.BORDER_CONSTANT, value=(255, 255, 255)); x0 += p; x1 += p
    return im[y0:y1, x0:x1]
def pil(im, H): return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).resize((W, H), Image.LANCZOS)
rows = [[], [], [], []]
for v in FR:
    idx = ids(v); ref = cv2.imread('ref/%s.png' % v); mod = cv2.imread('out/final_%s.png' % v)
    bf = box(idx > 0, HF)
    upper = np.isin(idx, [names.index(n) + 1 for n in names if n != 'shaft'])
    bc = box(upper, HC, 0.02, 0.10)
    rows[0].append((pil(crop(ref, bf), HF), 'Drone frame %s' % v[1:]))
    rows[1].append((pil(crop(mod, bf), HF), 'Model · frame %s camera' % v[1:]))
    rows[2].append((pil(crop(ref, bc), HC), 'Drone frame %s · closer' % v[1:]))
    rows[3].append((pil(crop(mod, bc), HC), 'Model · frame %s camera · closer' % v[1:]))
Hs = (HF, HF, HC, HC)
out = Image.new('RGB', (3 * W + 2 * GAP, sum(Hs) + 3 * GAP + 14), 'white')
font = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 22); y = 0
for r, H in zip(rows, Hs):
    for i, (im, lab) in enumerate(r):
        x = i * (W + GAP); out.paste(im, (x, y)); d = ImageDraw.Draw(out, 'RGBA'); tw = d.textlength(lab, font=font)
        d.rounded_rectangle((x + 12, y + H - 46, x + 12 + tw + 22, y + H - 12), radius=8, fill=(0, 0, 0, 150))
        d.text((x + 23, y + H - 42), lab, font=font, fill=(255, 255, 255, 255))
    y += H + GAP + (14 if H == HF and r is rows[1] else 0)
out.save('galata_tower_showcase.jpg', quality=86); print(out.size)
