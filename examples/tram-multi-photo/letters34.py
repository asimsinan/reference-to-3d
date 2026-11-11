"""letters34.py -- the tram's lettering redrawn sharp (the photo cuts were soft and skewed): white serif text on a
transparent background, laid out as on photos 13 and 17. -> tex34m/{sign,signtab,dash_side}_a.png"""
from PIL import Image, ImageDraw, ImageFont
F = '/System/Library/Fonts/Supplemental/SuperClarendon.ttc'
def font(px, idx=5):
    try: return ImageFont.truetype(F, px, index=idx)
    except Exception: return ImageFont.truetype(F, px)
WHITE = (240, 240, 236, 255)
def centred(d, text, cx, cy, f, sx=1.0, img=None, maxw=None):
    # draw text at its own size, then squeeze horizontally by sx (the photo's lettering is condensed)
    l, t, r, b = d.textbbox((0, 0), text, font=f); w, h = r - l, b - t
    tmp = Image.new('L', (w + 8, h + 8), 0); ImageDraw.Draw(tmp).text((4 - l, 4 - t), text, font=f, fill=255)
    nw = int(tmp.width * sx)
    if maxw and nw > maxw: nw = int(maxw)
    tmp = tmp.resize((max(1, nw), tmp.height), Image.LANCZOS)
    img.paste(Image.new('RGBA', tmp.size, WHITE), (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)
# destination board 1.12 x 0.17 m -> 1400 x 212
im = Image.new('RGBA', (1400, 212), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
d.rectangle([14, 14, 1385, 197], outline=WHITE, width=7)
centred(d, 'TAKSİM - TÜNEL', 700, 108, font(128), 0.80, im, maxw=1250); im.save('tex34m/sign_a.png')
# route-number tab 0.17 x 0.165 m -> 340 x 330 (arc above, the number in the middle)
im = Image.new('RGBA', (340, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
centred(d, '34', 170, 205, font(150), 0.80, im); im.save('tex34m/signtab_a.png')
# corner dash panel: "34" high on the panel, two lines of warning at the bottom (photo 13)
W, H = 600, 1000
im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
centred(d, '34', W * 0.5, H * 0.17, font(210), 0.58, im)
centred(d, 'ASILMAK YASAK', W * 0.5, H * 0.77, font(86), 0.62, im, maxw=W * 0.86)
centred(d, 'VE TEHLİKELİDİR', W * 0.5, H * 0.875, font(86), 0.62, im, maxw=W * 0.86)
im.save('tex34m/dash_side_a.png')
print('ok')
