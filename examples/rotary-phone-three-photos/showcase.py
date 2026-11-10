"""Showcase: the three reference photos (top) | the model in real materials from each photo's solved camera,
composited over the photo (bottom). Reads front/side/rear.jpg and rF3/{front,side,rear}.png; writes rotary_showcase.jpg"""
import cv2, numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
D = sys.argv[1] if len(sys.argv) > 1 else 'rF3'
CROP = {'front': (150, 600, 1410, 1740), 'side': (130, 560, 1390, 1700), 'rear': (190, 760, 1450, 1900)}
W, H, GAP = 610, 552, 6
def panel(v, model):
    ph = cv2.imread(v + '.jpg')
    if model:
        r = cv2.resize(cv2.imread('%s/%s.png' % (D, v), cv2.IMREAD_UNCHANGED), (1500, 2000))
        a = r[..., 3:].astype(float) / 255; ph = (r[..., :3] * a + ph * (1 - a)).astype(np.uint8)
    x0, y0, x1, y1 = CROP[v]
    return Image.fromarray(cv2.cvtColor(ph[y0:y1, x0:x1], cv2.COLOR_BGR2RGB)).resize((W, H), Image.LANCZOS)
names = {'front': 'front', 'side': 'side', 'rear': 'rear'}
panels = [(panel(v, False), 'Reference · ' + names[v]) for v in CROP] + \
         [(panel(v, True), 'Model · %s photo\'s camera' % names[v]) for v in CROP]
out = Image.new('RGB', (3 * W + 2 * GAP, 2 * H + GAP), 'white')
font = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 20)
for i, (im, lab) in enumerate(panels):
    x = (i % 3) * (W + GAP); y = (i // 3) * (H + GAP); out.paste(im, (x, y))
    d = ImageDraw.Draw(out, 'RGBA'); tw = d.textlength(lab, font=font)
    d.rounded_rectangle((x + 12, y + H - 44, x + 12 + tw + 22, y + H - 12), radius=8, fill=(0, 0, 0, 150))
    d.text((x + 23, y + H - 40), lab, font=font, fill=(255, 255, 255, 255))
out.save('rotary_showcase.jpg', quality=88); print(out.size)
