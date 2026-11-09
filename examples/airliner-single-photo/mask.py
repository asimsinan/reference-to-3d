import cv2, numpy as np
im = cv2.imread('ref.jpg'); H,W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
# seed: low saturation & bright -> probable plane; strongly saturated -> background
m = np.full((H,W), cv2.GC_PR_BGD, np.uint8)
s, v = hsv[...,1].astype(int), hsv[...,2].astype(int)
m[(s < 40) & (v > 170)] = cv2.GC_PR_FGD
m[(s > 90)] = cv2.GC_BGD
m[:100] = cv2.GC_BGD
bg = np.zeros((1,65),np.float64); fg = np.zeros((1,65),np.float64)
cv2.grabCut(im, m, None, bg, fg, 6, cv2.GC_INIT_WITH_MASK)
out = np.where((m==1)|(m==3),255,0).astype(np.uint8)
cv2.imwrite('mask_gc.png', out)
ov = im.copy(); ov[out>0] = (0.5*ov[out>0] + [0,0,127]).astype(np.uint8)
cv2.imwrite('mask_ov.jpg', ov)
