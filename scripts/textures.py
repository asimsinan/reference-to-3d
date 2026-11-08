"""The views' cut-outs as textures: each panel's transparent margin filled outward from the object's own edge
pixels (so where the model's silhouette is a little larger than the reference's, it takes the colour next to it, not
the background), then upsampled (default 4x, Lanczos) for sharper sampling.

Run: uv run --with pillow --with numpy python textures.py --panels DIR --views front,left,rear,top --out TEXDIR
     [--fill 60] [--scale 4]
"""
import argparse
import os

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--panels", required=True)
ap.add_argument("--views", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--fill", type=int, default=60, help="px rings filled outward")
ap.add_argument("--scale", type=int, default=4)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)


def fill(px, it):
    rgb = px[..., :3].astype(float)
    ok = px[..., 3] > 128
    for _ in range(it):
        acc = np.zeros_like(rgb)
        n = np.zeros(ok.shape)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            sh_ok = np.roll(np.roll(ok, dy, 0), dx, 1)
            acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * sh_ok[..., None]
            n += sh_ok
        new = (~ok) & (n > 0)
        rgb[new] = acc[new] / n[new][:, None]
        ok |= new
    return rgb.clip(0, 255).astype(np.uint8)


for v in [v for v in a.views.split(",") if v]:
    p = np.asarray(Image.open(os.path.join(a.panels, v + ".png")).convert("RGBA"))
    ys, xs = np.where(p[..., 3] > 128)
    p = p[ys.min():ys.max() + 1, xs.min():xs.max() + 1]  # (to the object's box: the projection fits box to box)
    h, w = p.shape[:2]
    Image.fromarray(fill(p, a.fill)).resize((w * a.scale, h * a.scale), Image.LANCZOS).save(os.path.join(a.out, v + ".png"))
    print(f"{v}: {w} x {h} px -> {w * a.scale} x {h * a.scale}")
