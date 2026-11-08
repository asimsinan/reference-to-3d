"""Split a reference sheet (several views of one object in one image) into one cut-out per view.

The object's pixels come from the alpha channel when the sheet has real transparency, else from their distance to the
background colour (sampled at the corners). Parts of one view that do not touch (a car's mirror, a mug's handle seen
edge-on) are merged by dilating the mask before labelling, so each view is one panel.

Writes, in --out:
  panel_NN.png       the view cut to its box, RGBA (alpha = the object's mask)
  index.jpg          all panels numbered on a grey ground: look at it to tell which panel is which view
  boxes.json         [{"n", "box": [x0, y0, x1, y1] (inclusive, sheet pixels), "name"}]
With --names front,side,... (in panel order: rows top to bottom, left to right) the panels are also saved as
<name>.png; or rename them later with --rename "0=front,2=side".

Run: uv run --with pillow --with numpy --with scipy python split_sheet.py sheet.png --out panels [--names ...]
     [--merge 5] [--min-area 0.01] [--bg-tol 40]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument("sheet")
ap.add_argument("--out", required=True)
ap.add_argument("--names", default="")
ap.add_argument("--rename", default="", help='after a first run: "0=front,2=side" names existing panels')
ap.add_argument("--merge", type=int, default=5, help="px: parts of a view closer than this are one panel (raise it when "
                                                    "a view's separate parts come out as panels of their own; lower it when views merge)")
ap.add_argument("--min-area", type=float, default=.01, help="drop panels smaller than this share of the largest")
ap.add_argument("--bg-tol", type=float, default=40., help="colour distance from the background that counts as object")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

if a.rename:  # only name panels from a previous run
    boxes = json.load(open(os.path.join(a.out, "boxes.json")))
    for pair in a.rename.split(","):
        k, name = pair.split("=")
        src = os.path.join(a.out, "panel_%02d.png" % int(k))
        Image.open(src).save(os.path.join(a.out, name + ".png"))
        boxes[int(k)]["name"] = name
    json.dump(boxes, open(os.path.join(a.out, "boxes.json"), "w"), indent=1)
    print("named:", {b["n"]: b.get("name") for b in boxes})
    raise SystemExit

im = Image.open(a.sheet).convert("RGBA")
px = np.asarray(im).astype(float)
alpha = px[..., 3]
if alpha.min() < 128 and (alpha < 128).mean() > .05:  # real transparency
    mask = alpha > 128
    how = "alpha"
else:  # a flat background: the corners' colour
    h, w = alpha.shape
    corners = np.concatenate([px[:8, :8, :3].reshape(-1, 3), px[:8, -8:, :3].reshape(-1, 3), px[-8:, :8, :3].reshape(-1, 3),
                              px[-8:, -8:, :3].reshape(-1, 3)])
    bg = np.median(corners, 0)
    mask = np.sqrt(((px[..., :3] - bg) ** 2).sum(2)) > a.bg_tol
    mask = ndimage.binary_opening(mask, iterations=1)  # (holes are kept: a handle's opening is real)
    how = "background %s" % bg.astype(int).tolist()
lab, n = ndimage.label(ndimage.binary_dilation(mask, iterations=a.merge))
objs = ndimage.find_objects(lab)
areas = [(mask[s] & (lab[s] == i + 1)).sum() for i, s in enumerate(objs)]
keep = [i for i, ar in enumerate(areas) if ar >= a.min_area * max(areas)]
boxes = []
for i in keep:
    s = objs[i]
    sub = mask[s] & (lab[s] == i + 1)
    ys, xs = np.where(sub)
    y0, x0 = s[0].start + ys.min(), s[1].start + xs.min()
    y1, x1 = s[0].start + ys.max(), s[1].start + xs.max()
    boxes.append({"label": i + 1, "box": [int(x0), int(y0), int(x1), int(y1)]})
# reading order: rows (boxes whose vertical centres are within half a box height share a row), then left to right
boxes.sort(key=lambda b: (b["box"][1] + b["box"][3]) / 2)
rows, cur = [], []
for b in boxes:
    cy = (b["box"][1] + b["box"][3]) / 2
    if cur and abs(cy - np.mean([(c["box"][1] + c["box"][3]) / 2 for c in cur])) > .5 * (b["box"][3] - b["box"][1]):
        rows.append(cur)
        cur = []
    cur.append(b)
if cur:
    rows.append(cur)
ordered = [b for r in rows for b in sorted(r, key=lambda b: b["box"][0])]
names = [s for s in a.names.split(",") if s]
out = []
tiles = []
for k, b in enumerate(ordered):
    x0, y0, x1, y1 = b["box"]
    cut = px[y0:y1 + 1, x0:x1 + 1].copy()
    m = mask[y0:y1 + 1, x0:x1 + 1] & (lab[y0:y1 + 1, x0:x1 + 1] == b["label"])
    cut[..., 3] = np.where(m, px[y0:y1 + 1, x0:x1 + 1, 3] if how == "alpha" else 255, 0)
    pim = Image.fromarray(cut.astype(np.uint8), "RGBA")
    pim.save(os.path.join(a.out, "panel_%02d.png" % k))
    name = names[k] if k < len(names) else None
    if name:
        pim.save(os.path.join(a.out, name + ".png"))
    out.append({"n": k, "box": b["box"], "name": name})
    t = Image.new("RGBA", pim.size, (128, 128, 128, 255))
    t.alpha_composite(pim)
    tiles.append(t.convert("RGB"))
json.dump(out, open(os.path.join(a.out, "boxes.json"), "w"), indent=1)
H = 220
tiles = [t.resize((max(1, int(t.width * H / t.height)), H)) for t in tiles]
sheet = Image.new("RGB", (sum(t.width for t in tiles) + 20 * (len(tiles) + 1), H + 50), (60, 60, 60))
x = 20
d = ImageDraw.Draw(sheet)
for k, t in enumerate(tiles):
    sheet.paste(t, (x, 40))
    d.text((x + 4, 8), "%d %s" % (k, out[k]["name"] or ""), fill=(255, 255, 0))
    x += t.width + 20
sheet.save(os.path.join(a.out, "index.jpg"), quality=88)
for b in out:
    x0, y0, x1, y1 = b["box"]
    if (x1 - x0) > 4 * (y1 - y0) or (y1 - y0) > 4 * (x1 - x0):
        print("WARNING: panel %d is %d x %d px: views may have merged; try a smaller --merge" % (b["n"], x1 - x0 + 1, y1 - y0 + 1))
print("mask from %s; %d panels:" % (how, len(out)))
for b in out:
    x0, y0, x1, y1 = b["box"]
    print("  %d %-6s box %s  %d x %d px" % (b["n"], b["name"] or "", b["box"], x1 - x0 + 1, y1 - y0 + 1))
