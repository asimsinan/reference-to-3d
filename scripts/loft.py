"""An elongated object's body (a vehicle, a boat, a bottle on its side, a fuselage, a shoe) lofted along x from its
views: at each station the cross-section is the front view's half-width at every height (eased into the rear view's
towards the back, if given), scaled by the top view's plan there (if given), cut to the side view's top and bottom at
that station, its top crowned and its corners rounded; every section sampled at the same N angles in its own
proportions (so a wide flat section and a tall one match point for point: no creases). Cleaner, lighter topology than
the visual hull for such shapes; the details (wheels, mirrors) are separate parts or come from the texture.

Frame as hull.py: +X front, +Y left, +Z up, bottom z = 0. The side view: "left" (front at the image's left) or "right".

Run: uv run --with pillow --with numpy --with shapely python loft.py --panels DIR --side left [--front front]
     [--rear rear] [--top top --top-front left] --height H [--stations 64] [--ring 72] [--round 0.16] [--crown 0.06]
     [--nose-blunt 0.28] --out body.obj
"""
import argparse
import json
import math

import numpy as np
from PIL import Image
from shapely.geometry import LineString, Point, Polygon

ap = argparse.ArgumentParser()
ap.add_argument("--panels", required=True)
ap.add_argument("--side", required=True, help="the side view's name: left or right")
ap.add_argument("--front")
ap.add_argument("--rear")
ap.add_argument("--top")
ap.add_argument("--top-front", default="left")
ap.add_argument("--height", type=float, required=True)
ap.add_argument("--stations", type=int, default=64)
ap.add_argument("--ring", type=int, default=72)
ap.add_argument("--round", type=float, default=.16, help="m: the sections' corner radius (opening)")
ap.add_argument("--crown", type=float, default=.06, help="share of the section's height its top bulges")
ap.add_argument("--out", required=True)
a = ap.parse_args()


def mask(name):
    m = np.asarray(Image.open(f"{a.panels}/{name}.png").convert("RGBA"))[..., 3] > 128
    ys, xs = np.where(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


H = a.height
S = mask(a.side)
if a.side == "right":
    S = S[:, ::-1]  # (the front to the left, as "left")
hs, ws = S.shape
s = H / (hs - 1)
L = (ws - 1) * s
d = np.arange(ws) * s
top = np.array([(hs - 1 - np.argmax(S[:, c])) * s if S[:, c].any() else np.nan for c in range(ws)])
bot = np.array([(np.argmax(S[::-1, c])) * s if S[:, c].any() else np.nan for c in range(ws)])


def envelope(name):
    """Half-width against height from a front or rear view (scaled to H)."""
    F = mask(name)
    hf, wf = F.shape
    sf = H / (hf - 1)
    cx = (wf - 1) / 2
    z = (hf - 1 - np.arange(hf)) * sf
    hw = np.array([max(cx - np.where(F[r])[0][0], np.where(F[r])[0][-1] - cx) * sf if F[r].any() else np.nan for r in range(hf)])
    k = 9  # (a running median: thin parts such as mirrors smoothed away)
    hw = np.array([np.nanmedian(hw[max(0, i - k):i + k + 1]) for i in range(len(hw))])
    return z[::-1], hw[::-1]


fz, fhw = envelope(a.front) if a.front else (None, None)
rz, rhw = envelope(a.rear) if a.rear else (fz, fhw)
if fz is None:
    fz, fhw = rz, rhw
if fz is None:
    raise SystemExit("give --front or --rear (the cross-section's widths)")
plan_u, plan_p = np.array([0., 1.]), np.array([1., 1.])
if a.top:
    T = mask(a.top)
    if a.top_front in ("up", "down"):
        T = T.T
    if a.top_front in ("right", "down"):
        T = T[:, ::-1]
    th, tw = T.shape
    rows = [np.where(T[:, c])[0] for c in range(tw)]
    mid = np.median([(r[0] + r[-1]) / 2 for r in rows if len(r)])
    half = np.array([max(mid - r[0], r[-1] - mid) if len(r) else 0 for r in rows], float)
    plan_u = np.arange(tw) / (tw - 1)
    plan_p = np.minimum(half / np.median(half[int(tw * .3):int(tw * .7)]), 1.04)  # (a top view's flares and mirrors capped)


def section(dd):
    zt, zb = float(np.interp(dd, d, top)), float(np.interp(dd, d, bot))
    t = min(max((dd / L - .3) / .4, 0.), 1.)  # front widths ahead, rear ones behind, eased between 30 and 70 %
    t = t * t * (3 - 2 * t)
    zs = np.linspace(zb, zt, 60)
    hw = ((1 - t) * np.interp(zs, fz, fhw) + t * np.interp(zs, rz, rhw)) * float(np.interp(dd / L, plan_u, plan_p))
    th_ = float(hw[-1])
    right = [(float(h), float(z)) for h, z in zip(hw, zs, strict=True)]
    crown = [(float(y), zt - a.crown * min(zt - zb, .5 * H) * (y / max(th_, 1e-4)) ** 2) for y in np.linspace(th_, -th_, 25)]
    left = [(-y, z) for y, z in reversed(right)]
    poly = Polygon(right + crown[1:-1] + left).buffer(0)
    r = min(a.round, .45 * (zt - zb), .45 * float(hw.max()))
    rounded = poly.buffer(-r, join_style="round").buffer(r, join_style="round")
    if rounded.geom_type == "Polygon" and not rounded.is_empty:
        poly = rounded
    zc, hwm, hh = (zt + zb) / 2, max(float(hw.max()), 1e-3), max((zt - zb) / 2, 1e-3)
    ring = []
    for k in range(a.ring):
        ang = -math.pi / 2 + 2 * math.pi * k / a.ring
        ray = LineString([(0., zc), (6 * L * math.cos(ang) * hwm, zc + 6 * L * math.sin(ang) * hh)])
        hit = ray.intersection(poly.exterior)
        pts = [hit] if hit.geom_type == "Point" else list(getattr(hit, "geoms", []))
        q = max(pts, key=lambda g: Point(0., zc).distance(g)) if pts else Point(0., zc)
        ring.append((q.x, q.y))
    return zc, ring


tt = np.linspace(0., 1., a.stations)
ds = np.clip(L * (1 - np.cos(np.pi * tt)) / 2, .002 * L, .998 * L)  # (denser at both ends)
V, F = [], []
rings = []
for dd in ds:
    zc, ring = section(float(dd))
    base = len(V)
    V += [(L / 2 - dd, y, z) for y, z in ring]
    rings.append((base, zc, dd))
n = a.ring
for (b0, _, _), (b1, _, _) in zip(rings, rings[1:]):
    for i in range(n):
        F.append((b0 + i, b0 + (i + 1) % n, b1 + (i + 1) % n, b1 + i))
for (b, zc, dd), out_dir in ((rings[0], 1), (rings[-1], -1)):  # the ends: a fan to a middle point
    c = len(V)
    V.append((L / 2 - dd + out_dir * .002 * L, 0., zc))
    for i in range(n):
        F.append((b + i, c, b + (i + 1) % n) if out_dir > 0 else (b + i, b + (i + 1) % n, c))
with open(a.out, "w") as o:
    o.write("# lofted from %s\n" % ",".join(x for x in (a.side, a.front, a.rear, a.top) if x))
    for p in V:
        o.write("v %.5f %.5f %.5f\n" % p)
    for f in F:
        o.write("f " + " ".join(str(i + 1) for i in f) + "\n")
json.dump({"L": L, "H": H}, open(a.out + ".json", "w"))
print(f"length {L:.3f} m, height {H:.3f} m; {len(V)} vertices, {len(F)} faces -> {a.out}")
