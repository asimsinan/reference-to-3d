"""Measure a straight edge of the object in the photo from brightness steps, fit a line, and intersect two edges.
Reading corners by eye on a grid misplaced a rounded lid corner by ~20 px; this does not.

Run: uv run --with numpy --with opencv-python-headless python edge_profile.py ref.jpg EDGE_A EDGE_B
  EDGE = "h:Y0-Y1:X,X,X..:dark|light"  a near-horizontal edge, scanned down columns X within rows Y0..Y1
         "v:X0-X1:Y,Y,Y..:dark|light"  a near-vertical edge, scanned along rows Y within columns X0..X1
  dark|light = what the scan meets after the edge (dark: the object is darker than the background before it).
  Scan only where the background next to the edge is plain (a bright wall), not where it is as dark as the object.
Prints each edge's samples and fitted line, then their intersection (the sharp corner, x y).
Example (the lid's top-left corner): "h:20-130:570,600,615:dark" "v:500-620:280,440,600,760:dark"
"""
import sys
import cv2
import numpy as np


def edge(gray, spec):
    kind, rng, at, sense = spec.split(":")
    a, b = map(int, rng.split("-"))
    pts = []
    for s in map(int, at.split(",")):
        line = gray[a:b, s] if kind == "h" else gray[s, a:b]
        d = np.diff(cv2.GaussianBlur(line.reshape(-1, 1), (1, 5), 0).ravel())
        k = int(np.argmin(d) if sense == "dark" else np.argmax(d)) + a + 0.5
        pts.append((s, k) if kind == "h" else (k, s))
    pts = np.array(pts, float)
    if kind == "h":   # y = m x + c
        m, c = np.polyfit(pts[:, 0], pts[:, 1], 1)
        res = pts[:, 1] - (m * pts[:, 0] + c)
    else:             # x = m y + c
        m, c = np.polyfit(pts[:, 1], pts[:, 0], 1)
        res = pts[:, 0] - (m * pts[:, 1] + c)
    print(f"{spec}: samples {pts.tolist()}  residuals {np.round(res, 1).tolist()}")
    return kind, m, c


def intersect(e1, e2):
    (k1, m1, c1), (k2, m2, c2) = e1, e2
    if k1 == "v":
        (k1, m1, c1), (k2, m2, c2) = (k2, m2, c2), (k1, m1, c1)
    # y = m1 x + c1 ; x = m2 y + c2
    y = (m1 * c2 + c1) / (1 - m1 * m2)
    return m2 * y + c2, y


g = cv2.cvtColor(cv2.imread(sys.argv[1]), cv2.COLOR_BGR2GRAY).astype(np.float32)
e = [edge(g, s) for s in sys.argv[2:4]]
x, y = intersect(*e)
print(f"corner: {x:.1f} {y:.1f}")
