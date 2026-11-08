"""Rectify one plane of a room out of its picture, through the camera solve_camera_vp.py wrote.

  uv run --with numpy --with opencv-python-headless python rectify_plane.py --cam cam.json --img plate.png \
      --origin -1.175,2.30,0 --u 0,1,0 --v 0,0,1 --size 1.05,2.398 --ppm 300 --out window.png [--grid]

The texel at the image's bottom-left is --origin; u runs to the right for size[0] m, v upwards for size[1] m.
Texels the picture does not show (outside its frame or behind the camera) come out magenta (255,0,255): fill them
before use (along the structure: row by row under a horizontal beam, column by column along bench slats).
--grid draws ticks every 0.1 m and labels every metre, to read positions off the result.

Seen from inside, a wall rectified with u along +world axis may read mirrored (text backwards); map it back with the
same u in the shader and it comes out the right way.

Importable: rectify(img, cam, origin, u, v, usize, vsize, ppm) -> (image, mask of known texels).
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solve_camera_vp import load  # noqa: E402


def rectify(img, cam, origin, uvec, vvec, usize, vsize, ppm):
    import cv2
    w, h = int(round(usize * ppm)), int(round(vsize * ppm))
    U, V = np.meshgrid((np.arange(w) + 0.5) / ppm, (np.arange(h)[::-1] + 0.5) / ppm)
    P = np.asarray(origin, float) + U[..., None] * np.asarray(uvec, float) + V[..., None] * np.asarray(vvec, float)
    C = np.einsum('ij,hwj->hwi', cam.M, P - cam.pos)
    x = cam.f * C[..., 0] / C[..., 2] + cam.cx; y = cam.f * C[..., 1] / C[..., 2] + cam.cy
    ok = (C[..., 2] > 0.05) & (x >= 0) & (x < cam.W - 1) & (y >= 0) & (y < cam.H - 1)
    out = cv2.remap(img, x.astype(np.float32), y.astype(np.float32), cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 0, 255))
    out[~ok] = (255, 0, 255); return out, ok


def main():
    import cv2
    ap = argparse.ArgumentParser()
    for k in ('cam', 'img', 'origin', 'u', 'v', 'size', 'out'): ap.add_argument('--' + k, required=True)
    ap.add_argument('--ppm', type=float, default=200); ap.add_argument('--grid', action='store_true')
    a = ap.parse_args(); vec = lambda s: [float(t) for t in s.split(',')]
    su, sv = vec(a.size)
    o, ok = rectify(cv2.imread(a.img), load(a.cam), vec(a.origin), vec(a.u), vec(a.v), su, sv, a.ppm)
    if a.grid:
        for i in range(int(su * 10) + 1):
            x = int(i * a.ppm / 10); cv2.line(o, (x, 0), (x, 8 if i % 10 else 22), (0, 255, 255), 1)
            if i % 10 == 0: cv2.putText(o, str(i // 10), (x + 2, 36), 0, 0.5, (0, 255, 255), 1)
        for i in range(int(sv * 10) + 1):
            y = o.shape[0] - int(i * a.ppm / 10); cv2.line(o, (0, y), (8 if i % 10 else 22, y), (0, 255, 255), 1)
            if i % 10 == 0: cv2.putText(o, str(i // 10), (26, y - 2), 0, 0.5, (0, 255, 255), 1)
    cv2.imwrite(a.out, o); print(f'{a.out}: {o.shape[1]}x{o.shape[0]}, {100 * ok.mean():.0f}% seen in the picture')


if __name__ == '__main__':
    main()
