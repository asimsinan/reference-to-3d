# GrabCut seeded by the model's ID render: eroded model = probable FG, far outside = BG.
import cv2, numpy as np
im = cv2.imread('ref.jpg'); idp = cv2.imread('out_id.png', cv2.IMREAD_UNCHANGED)
a = (idp[...,3] > 127).astype(np.uint8)
m = np.full(a.shape, cv2.GC_PR_BGD, np.uint8)
m[cv2.dilate(a, np.ones((41,41),np.uint8)) == 0] = cv2.GC_BGD
m[cv2.erode(a, np.ones((9,9),np.uint8)) > 0] = cv2.GC_PR_FGD
m[cv2.erode(a, np.ones((25,25),np.uint8)) > 0] = cv2.GC_FGD
old = cv2.imread('mask_gc.png',0) > 0
m[old & (m != cv2.GC_BGD)] = cv2.GC_FGD
bg = np.zeros((1,65)); fg = np.zeros((1,65))
cv2.grabCut(im, m, None, bg, fg, 8, cv2.GC_INIT_WITH_MASK)
out = np.where((m==1)|(m==3),255,0).astype(np.uint8)
out = cv2.morphologyEx(out, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
cv2.imwrite('mask2.png', out)
ov = im.copy(); e = cv2.Canny(out, 50, 150) > 0; ov[cv2.dilate(e.astype(np.uint8), np.ones((2,2))) > 0] = (0,255,0)
cv2.imwrite('mask2_ov.jpg', ov)
