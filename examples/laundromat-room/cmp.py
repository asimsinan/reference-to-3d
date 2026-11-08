import cv2, numpy as np
a=cv2.imread('ref.png').astype(np.float32); b=cv2.imread('renders2/cam.png')[:,:,:3].astype(np.float32)
d=np.abs(a-b).mean(2); print('mean',d.mean().round(2),'median',np.median(d).round(2),'p95',np.percentile(d,95).round(2))
side=np.hstack([a,b]); side=cv2.resize(side,(1920,540)); cv2.imwrite('cmp_side.jpg',side)
cv2.imwrite('cmp_diff.jpg',cv2.resize(np.clip(d*4,0,255).astype(np.uint8),(960,540)))
