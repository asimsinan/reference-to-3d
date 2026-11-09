import sys
from PIL import Image
pairs = sys.argv[2:]; out = sys.argv[1]; h = 520; tiles = []
for n in pairs:
    a = Image.open(f'{n}.jpg'); b = Image.open(f'renders/{n}.png').convert('RGB')
    a = a.resize((int(a.width * h / a.height), h)); b = b.resize((int(b.width * h / b.height), h))
    t = Image.new('RGB', (a.width + b.width + 6, h), (255, 255, 255)); t.paste(a, (0, 0)); t.paste(b, (a.width + 6, 0)); tiles.append(t)
W = max(t.width for t in tiles); S = Image.new('RGB', (W, (h + 8) * len(tiles)), (255, 255, 255))
for i, t in enumerate(tiles): S.paste(t, (0, i * (h + 8)))
S.save(out)
