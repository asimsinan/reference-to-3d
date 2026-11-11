"""Showcase: the three present-day drone frames (ref/r2-r4), each beside the model in real materials from the same
frame's solved camera (out/final_rN.png, same crop round the tower from id/rN.png); below, the side no frame shows
(out/bv_new8_<deg>.png from backviews.py, out/tv_a_<deg>.png from topviews.py). Writes galata_tower_showcase.jpg"""
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H, GAP = 400, 760, 6
def box(v):
    idm = cv2.imread('id/%s.png' % v, cv2.IMREAD_UNCHANGED); ys, xs = np.nonzero((idm[..., 3] > 127) & (idm[..., 2] > 0))
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; h = (ys.max() - ys.min()) * 1.04; w = h * W / H
    x0, y0 = int(cx - w / 2), int(max(cy - h / 2, 0)); return x0, y0, int(x0 + w), int(y0 + h)
def crop(im, b):
    x0, y0, x1, y1 = b; pad = max(0, -x0, x1 - im.shape[1])
    if pad: im = cv2.copyMakeBorder(im, 0, 0, pad, pad, cv2.BORDER_CONSTANT, value=(255, 255, 255)); x0 += pad; x1 += pad
    return im[y0:y1, x0:x1]
def fit(im):   # novel views: centre crop to the panel's aspect
    h, w = im.shape[:2]; tw = int(h * W / H)
    if tw <= w: x0 = (w - tw) // 2; im = im[:, x0:x0 + tw]
    else: th = int(w * H / W); y0 = (h - th) // 2; im = im[max(y0, 0):max(y0, 0) + th]
    return im
def pil(im): return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).resize((W, H), Image.LANCZOS)
top = []
for v in ('r2', 'r3', 'r4'):
    b = box(v)
    top.append((pil(crop(cv2.imread('ref/%s.png' % v), b)), 'Drone frame %s' % v[1:]))
    top.append((pil(crop(cv2.imread('out/final_%s.png' % v), b)), 'Model · its camera'))
bot = [(pil(fit(cv2.imread('out/bv_new8_%d.png' % d))), 'Unseen side %d°' % d) for d in (100, 180, 260)]
bot += [(pil(fit(cv2.imread('out/tv_a_%d.png' % d))), 'Unseen side %d°' % d) for d in (160, 220)]
bot += [(pil(fit(cv2.imread('out/nv_ground.png'))), 'From the plaza')]
out = Image.new('RGB', (6 * W + 5 * GAP, 2 * H + GAP + 10), 'white')
font = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 20)
for i, (im, lab) in enumerate(top + bot):
    x = (i % 6) * (W + GAP); y = (i // 6) * (H + GAP + 10); out.paste(im, (x, y))
    d = ImageDraw.Draw(out, 'RGBA'); tw = d.textlength(lab, font=font)
    d.rounded_rectangle((x + 12, y + H - 44, x + 12 + tw + 22, y + H - 12), radius=8, fill=(0, 0, 0, 150))
    d.text((x + 23, y + H - 40), lab, font=font, fill=(255, 255, 255, 255))
out.save('galata_tower_showcase.jpg', quality=86); print(out.size)
