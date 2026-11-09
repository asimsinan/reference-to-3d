"""Warp the frontal bookcase photo (ek1) onto the metric bookcase front (400 ppm, from right.jpg) by SIFT + homography."""
import cv2, numpy as np
ref = cv2.imread('tex/bookcase_old.png'); src = cv2.imread('ek1.jpg')
sift = cv2.SIFT_create(8000)
g1 = cv2.cvtColor(cv2.resize(ref, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2GRAY)   # 1000 ppm
g2 = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
k1, d1 = sift.detectAndCompute(g1, None); k2, d2 = sift.detectAndCompute(g2, None)
m = cv2.BFMatcher().knnMatch(d2, d1, k=2)
good = [a for a, b in m if a.distance < 0.75 * b.distance]
P2 = np.float32([k2[a.queryIdx].pt for a in good]); P1 = np.float32([k1[a.trainIdx].pt for a in good])
Hm, inl = cv2.findHomography(P2, P1, cv2.RANSAC, 6.0)
print('matches', len(good), 'inliers', int(inl.sum()))
hi = cv2.warpPerspective(src, Hm, (g1.shape[1], g1.shape[0]), flags=cv2.INTER_CUBIC)
cover = cv2.warpPerspective(np.full(src.shape[:2], 255, np.uint8), Hm, (g1.shape[1], g1.shape[0]))
base = cv2.resize(ref, (g1.shape[1], g1.shape[0]), interpolation=cv2.INTER_CUBIC)
# exposure match on the overlap, feathered blend into the old texture where ek1 does not reach
ov = cover > 250
gain = base[ov].reshape(-1, 3).astype(np.float32).mean(0) / np.maximum(hi[ov].reshape(-1, 3).astype(np.float32).mean(0), 1)
hi = np.clip(hi.astype(np.float32) * gain, 0, 255)
a = cv2.GaussianBlur((cover > 250).astype(np.float32), (0, 0), 6)[..., None]
a = np.minimum(a, (cv2.erode((cover > 250).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(np.float32))[..., None] * 0 + a)
out = hi * a + base.astype(np.float32) * (1 - a)
cv2.imwrite('tex/bookcase_hi.png', out.astype(np.uint8))
cv2.imwrite('tex/bookcase.png', cv2.resize(out, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_AREA).astype(np.uint8))
vis = np.concatenate([base, out.astype(np.uint8)], 1); cv2.imwrite('g/bc_new.jpg', cv2.resize(vis, None, fx=0.45, fy=0.45))
