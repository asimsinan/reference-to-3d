"""Any object's shape from its silhouettes: the visual hull (the space every view's silhouette agrees on), carved in
voxels and turned into a smooth mesh (marching cubes on the lightly blurred occupancy).

The object's frame (used by every script of this skill): +X its front, +Y its left, +Z up; x and y centred, the
bottom at z = 0, metres. Each view's mask is fitted to the object's extent in that view (its box to the box), so the
views need not share a scale. View names and what they look along:
  front  from +X (image right = +Y)        rear   from -X (image right = -Y)
  left   from +Y (image right = -X: the front at the image's left)   right  from -Y (the front at the image's right)
  top    from +Z, --top-front left|right|up|down says where the front is in that image
A side view whose front is at the image's left is "left", at its right "right". One side view is enough: the other
is taken as its mirror.

Size: --size L,W,H (length along x, width along y, height), or --height H and the rest from the views' proportions
(the front's or rear's width/height gives W, the side's length/height gives L).

What it cannot do: hollows no view sees (a cup's inside, a car's footwell) come out filled; add them after.

Run: uv run --with pillow --with numpy --with scipy --with scikit-image python hull.py --panels DIR
     --views front,left,top [--top-front left] (--size L,W,H | --height H) [--res 220] [--blur 1.0] --out hull.obj
"""
import argparse
import json

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

ap = argparse.ArgumentParser()
ap.add_argument("--panels", required=True, help="the folder with <view>.png cut-outs (split_sheet.py)")
ap.add_argument("--views", required=True)
ap.add_argument("--top-front", default="left")
ap.add_argument("--size")
ap.add_argument("--height", type=float)
ap.add_argument("--res", type=int, default=220, help="voxels along the longest side")
ap.add_argument("--blur", type=float, default=1., help="voxels: the occupancy's blur before meshing (smoother)")
ap.add_argument("--out", required=True)
a = ap.parse_args()


def mask_of(name):
    m = np.asarray(Image.open(f"{a.panels}/{name}.png").convert("RGBA"))[..., 3] > 128
    ys, xs = np.where(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


views = [v for v in a.views.split(",") if v]
M = {v: mask_of(v) for v in views}
if a.size:
    L, W, H = [float(v) for v in a.size.split(",")]
else:
    if not a.height:
        raise SystemExit("give --size L,W,H or --height H")
    H = a.height
    fr = next((v for v in ("front", "rear") if v in M), None)
    sd = next((v for v in ("left", "right") if v in M), None)
    W = H * M[fr].shape[1] / M[fr].shape[0] if fr else None
    L = H * M[sd].shape[1] / M[sd].shape[0] if sd else None
    if "top" in M:  # the top's proportion fills what is missing
        th, tw = M["top"].shape
        along, across = (tw, th) if a.top_front in ("left", "right") else (th, tw)
        if L is None and W is not None:
            L = W * along / across
        if W is None and L is not None:
            W = L * across / along
    if L is None or W is None:
        raise SystemExit("not enough views for the proportions: give --size L,W,H")
step = max(L, W, H) / a.res
xs = np.arange(-L / 2 + step / 2, L / 2, step)
ys = np.arange(-W / 2 + step / 2, W / 2, step)
zs = np.arange(step / 2, H, step)
X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
occ = np.ones(X.shape, bool)


def sample(m, u, v):
    """The mask at (u right, v down), both 0..1 across its box."""
    h, w = m.shape
    c = np.clip(np.round(u * (w - 1)).astype(int), 0, w - 1)
    r = np.clip(np.round(v * (h - 1)).astype(int), 0, h - 1)
    return m[r, c]


for v, m in M.items():
    if v == "front":
        uu, vv = (Y + W / 2) / W, (H - Z) / H
    elif v == "rear":
        uu, vv = (W / 2 - Y) / W, (H - Z) / H
    elif v == "left":
        uu, vv = (L / 2 - X) / L, (H - Z) / H
    elif v == "right":
        uu, vv = (X + L / 2) / L, (H - Z) / H
    elif v == "top":
        uu, vv = {"left": ((L / 2 - X) / L, (Y + W / 2) / W), "right": ((X + L / 2) / L, (W / 2 - Y) / W),
                  "up": ((W / 2 - Y) / W, (L / 2 - X) / L), "down": ((Y + W / 2) / W, (X + L / 2) / L)}[a.top_front]
    else:
        raise SystemExit(f"unknown view {v} (front, rear, left, right, top)")
    occ &= sample(m, uu, vv)
print(f"size {L:.3f} x {W:.3f} x {H:.3f} m, voxel {step * 1000:.1f} mm, {occ.sum()} of {occ.size} in")
f = ndimage.gaussian_filter(np.pad(occ.astype(np.float32), 2), a.blur) if a.blur > 0 else np.pad(occ.astype(np.float32), 2)
verts, faces, _n, _v = measure.marching_cubes(f, .5)
verts = (verts - 2) * step + np.array([-L / 2 + step / 2, -W / 2 + step / 2, step / 2])
with open(a.out, "w") as o:
    o.write("# visual hull from %s\n" % ",".join(views))
    for p in verts:
        o.write("v %.5f %.5f %.5f\n" % tuple(p))
    for t in faces:
        o.write("f %d %d %d\n" % tuple(t[::-1] + 1))  # (marching cubes' winding reversed: normals out)
json.dump({"L": L, "W": W, "H": H, "views": views, "top_front": a.top_front}, open(a.out + ".json", "w"))
print(f"{len(verts)} vertices, {len(faces)} triangles -> {a.out}")
