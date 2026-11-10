"""Showcase: all six drone frames (ref/rN.png), each above the model in real materials from the same frame's solved
camera (out/final_rN.png), same crop (around the island, from the index render id/rN.png). Rows: frames 1-3, their
models, frames 4-6, their models. Writes maiden_tower_showcase.jpg"""
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H, GAP = 610, 460, 6
GROUPS = (('r1', 'r2', 'r3'), ('r4', 'r5', 'r6'))
def box(v):
    idm = cv2.imread('id/%s.png' % v, cv2.IMREAD_UNCHANGED); ys, xs = np.nonzero((idm[..., 3] > 127) & (idm[..., 2] > 0))
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2; h = (ys.max() - ys.min()) * 1.08; w = h * W / H
    x0, y0 = int(max(cx - w / 2, 0)), int(max(cy - h / 2, 0)); return x0, y0, int(x0 + w), int(y0 + h)
def pil(im): return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).resize((W, H), Image.LANCZOS)
panels = []
for FR in GROUPS:
    for v in FR:
        x0, y0, x1, y1 = box(v); panels.append((pil(cv2.imread('ref/%s.png' % v)[y0:y1, x0:x1]), 'Reference · drone frame %s' % v[1:]))
    for v in FR:
        x0, y0, x1, y1 = box(v); panels.append((pil(cv2.imread('out/final_%s.png' % v)[y0:y1, x0:x1]), "Model · frame %s's camera" % v[1:]))
out = Image.new('RGB', (3 * W + 2 * GAP, 4 * H + 3 * GAP + 10), 'white')
font = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 20)
for i, (im, lab) in enumerate(panels):
    x = (i % 3) * (W + GAP); y = (i // 3) * (H + GAP) + (i // 6) * 10; out.paste(im, (x, y))
    d = ImageDraw.Draw(out, 'RGBA'); tw = d.textlength(lab, font=font)
    d.rounded_rectangle((x + 12, y + H - 44, x + 12 + tw + 22, y + H - 12), radius=8, fill=(0, 0, 0, 150))
    d.text((x + 23, y + H - 40), lab, font=font, fill=(255, 255, 255, 255))
out.save('maiden_tower_showcase.jpg', quality=88); print(out.size)
