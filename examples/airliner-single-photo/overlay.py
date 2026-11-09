# overlay.py ID.png OUT.jpg : model part outlines over the photo + IoU vs GrabCut mask
import cv2, numpy as np, sys
ref = cv2.imread('ref.jpg'); idp = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)
a = idp[...,3] > 127; rgb = idp[...,:3].astype(int)
key = rgb[...,0]//40*10000 + rgb[...,1]//40*100 + rgb[...,2]//40
key[~a] = -1
edge = np.zeros(a.shape, bool)
edge[:-1] |= key[:-1] != key[1:]; edge[:,:-1] |= key[:,:-1] != key[:,1:]
edge = cv2.dilate(edge.astype(np.uint8), np.ones((2,2),np.uint8)) > 0
ov = ref.copy(); ov[edge] = (0,255,255)
cv2.imwrite(sys.argv[2], ov)
m = cv2.imread('mask_gc.png',0) > 0
print('IoU vs grabcut (upper body only meaningful): %.3f' % ((a&m).sum()/(a|m).sum()))
