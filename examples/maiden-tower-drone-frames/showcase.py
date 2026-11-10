"""Showcase: top row, the model in real materials from three drone frames' solved cameras (out/final_rN.png, cropped
to the island by the index render id/rN.png); bottom row, viewpoints no frame has (out/nv_*.png). The reference
frames themselves are not included. Writes maiden_tower_showcase.jpg"""
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H, GAP = 610, 460, 6
def crop_frame(v):
    im = cv2.imread('out/final_%s.png' % v); idm = cv2.imread('id/%s.png' % v, cv2.IMREAD_UNCHANGED)
    ys, xs = np.nonzero((idm[..., 3] > 127) & (idm[..., 2] > 0)); cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    h = (ys.max() - ys.min()) * 1.08; w = h * W / H; x0, y0 = int(max(cx - w / 2, 0)), int(max(cy - h / 2, 0))
    return im[y0:int(y0 + h), x0:int(x0 + w)]
def pil(im): return Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB)).resize((W, H), Image.LANCZOS)
def nv(n):
    im = cv2.imread('out/nv_%s.png' % n); h, w = im.shape[:2]; tw = int(h * W / H); x0 = max((w - tw) // 2, 0)
    return im[:, x0:x0 + tw]
panels = [(pil(crop_frame('r1')), 'Model · drone frame 1 camera'), (pil(crop_frame('r5')), 'Model · drone frame 5 camera'),
          (pil(crop_frame('r6')), 'Model · drone frame 6 camera'), (pil(nv('south_east')), 'New view · three-quarter, closer'),
          (pil(nv('west_low')), 'New view · low, at the fort'), (pil(nv('dome_close')), 'New view · the dome')]
out = Image.new('RGB', (3 * W + 2 * GAP, 2 * H + GAP), 'white')
font = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 20)
for i, (im, lab) in enumerate(panels):
    x = (i % 3) * (W + GAP); y = (i // 3) * (H + GAP); out.paste(im, (x, y))
    d = ImageDraw.Draw(out, 'RGBA'); tw = d.textlength(lab, font=font)
    d.rounded_rectangle((x + 12, y + H - 44, x + 12 + tw + 22, y + H - 12), radius=8, fill=(0, 0, 0, 150))
    d.text((x + 23, y + H - 40), lab, font=font, fill=(255, 255, 255, 255))
out.save('maiden_tower_showcase.jpg', quality=88); print(out.size)
