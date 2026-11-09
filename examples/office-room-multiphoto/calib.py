"""Material colours vs the photos: mean colour of the same image box in photo and render (same camera), per material.
Writes tex/calib.json: material -> linear RGB ratio photo/render (geometric mean over views)."""
import json, numpy as np
from PIL import Image
BOX = {  # view: {material: (x0, x1, y0, y1) as image fractions}
    'long': {'paint': (0.80, 0.95, 0.30, 0.40), 'ceiling': (0.45, 0.60, 0.05, 0.12), 'floor': (0.40, 0.55, 0.66, 0.72), 'maple': (0.40, 0.52, 0.82, 0.90)},
    'right': {'paint': (0.35, 0.55, 0.10, 0.30), 'floor': (0.15, 0.35, 0.86, 0.95), 'maple': (0.20, 0.24, 0.40, 0.70),
              'chair': (0.66, 0.72, 0.60, 0.66)},
    'left': {'paint': (0.60, 0.80, 0.30, 0.60), 'floor': (0.55, 0.80, 0.86, 0.95)},
    'door': {'paint': (0.45, 0.60, 0.40, 0.55), 'ceiling': (0.40, 0.60, 0.05, 0.10), 'floor': (0.30, 0.60, 0.85, 0.95)},
    'win': {'maple': (0.40, 0.70, 0.84, 0.88), 'ceiling': (0.60, 0.80, 0.05, 0.12)},
    'corridor': {'cblue': (0.02, 0.15, 0.15, 0.25), 'cbeige': (0.02, 0.15, 0.65, 0.80), 'terrazzo': (0.05, 0.35, 0.95, 0.99)},
    'ek4': {'cblue': (0.92, 0.98, 0.15, 0.30), 'cbeige': (0.00, 0.04, 0.75, 0.85)},
}
lin = lambda a: np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def mean_box(img, b):
    w, h = img.size; a = np.asarray(img.convert('RGB'), np.float32) / 255
    x0, x1, y0, y1 = int(b[0] * w), int(b[1] * w), int(b[2] * h), int(b[3] * h)
    return lin(a[y0:y1, x0:x1]).reshape(-1, 3).mean(0)
acc = {}
for v, mats in BOX.items():
    ph = Image.open(f'{v}.jpg'); rd = Image.open(f'renders_cal/{v}.png')
    for m, b in mats.items():
        r = mean_box(ph, b) / np.maximum(mean_box(rd, b), 1e-4)
        acc.setdefault(m, []).append(r); print(f'{v:9s} {m:9s} photo/render', np.round(r, 2))
out = {m: np.exp(np.mean(np.log(np.array(rs)), 0)).tolist() for m, rs in acc.items()}
# the photos' overall exposure varies; keep the scene's exposure and only correct materials relative to the white paint
ref = np.mean(out['paint'])
out = {m: (np.array(r) / ref).tolist() for m, r in out.items()}
json.dump(out, open('tex/calib.json', 'w'), indent=1)
for m, r in out.items(): print(m, np.round(r, 2))
