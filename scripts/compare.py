"""How close the model's renders are to the reference views: per view the silhouette IoU (overlap / union) and the
mean colour difference (0-255, over the reference object's pixels), both after fitting the render's object box to the
reference's; plus, per view, the two side by side and a difference image, and one sheet of all.

Run: uv run --with pillow --with numpy python compare.py --panels DIR --render DIR --views front,left,rear,top
     [--out DIR] (default: the render folder)
"""
import argparse
import os

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--panels", required=True)
ap.add_argument("--render", required=True)
ap.add_argument("--views", required=True)
ap.add_argument("--out")
a = ap.parse_args()
out = a.out or a.render
os.makedirs(out, exist_ok=True)


def crop(im):
    al = np.asarray(im)[..., 3] > 128
    ys, xs = np.where(al)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def white(im):
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert("RGB")


rows = []
for v in [v for v in a.views.split(",") if v]:
    ref = crop(Image.open(os.path.join(a.panels, v + ".png")).convert("RGBA"))
    ren = crop(Image.open(os.path.join(a.render, v + ".png")).convert("RGBA")).resize(ref.size, Image.LANCZOS)
    rm, mm = np.asarray(ref)[..., 3] > 128, np.asarray(ren)[..., 3] > 128
    iou = (rm & mm).sum() / max((rm | mm).sum(), 1)
    R, M = white(ref), white(ren)
    diff = np.abs(np.asarray(R).astype(float) - np.asarray(M).astype(float)).mean(2)
    cd = diff[rm].mean()
    rows.append((v, iou, cd))
    side = Image.new("RGB", (R.width * 2 + 20, R.height), "white")
    side.paste(R, (0, 0))
    side.paste(M, (R.width + 20, 0))
    side.save(os.path.join(out, f"cmp_{v}.jpg"), quality=90)
    Image.fromarray(np.clip(diff * 2, 0, 255).astype(np.uint8)).save(os.path.join(out, f"diff_{v}.png"))
for v, iou, cd in rows:
    print(f"{v:6s} silhouette IoU {iou:.3f}   mean colour difference {cd:5.1f} / 255")
tiles = [Image.open(os.path.join(out, f"cmp_{v}.jpg")) for v, _, _ in rows]
H = 300
tiles = [t.resize((int(t.width * H / t.height), H)) for t in tiles]
sheet = Image.new("RGB", (max(t.width for t in tiles) + 40, len(tiles) * (H + 20) + 20), "white")
y = 20
for t in tiles:
    sheet.paste(t, (20, y))
    y += H + 20
sheet.save(os.path.join(out, "compare.jpg"), quality=88)
print("sheet:", os.path.join(out, "compare.jpg"))
