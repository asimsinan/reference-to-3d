import cv2, numpy as np
from plate import pushpull
im=cv2.imread('ref.png').astype(np.float32)
rng=np.random.default_rng(1); n=cv2.GaussianBlur(rng.normal(0,1,im.shape[:2]).astype(np.float32),(0,0),1.2)*4
for cov,out in [('A','plate_B.png'),('AB','plate_C.png'),('ABC','plate.png')]:
    c=cv2.imread(f'cover_{cov}.png',0); full=(c>=250).astype(np.uint8)
    big=cv2.morphologyEx(full,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))       # thin parts (wires, legs, slat gaps) drop out
    m=(cv2.dilate(big,np.ones((7,7),np.uint8))|cv2.dilate(full,np.ones((5,5) if out!='plate.png' else (1,1),np.uint8)))>0
    p=pushpull(im,~m); p[m]+=n[m][:,None]; cv2.imwrite(out,np.clip(p,0,255).astype(np.uint8)); print(out,m.mean().round(3))
