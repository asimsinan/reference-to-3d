#!/bin/sh
./py.sh ovpart.py side 200 600 950 1100 1.0 op_side.jpg handset && ./py.sh ovpart.py rear 280 920 1400 1290 1.0 op_rear.jpg handset && ./py.sh ovpart.py front 320 660 1340 1000 1.0 op_front.jpg handset && ./py.sh -c "
import cv2,numpy as np
a,b,c=[cv2.imread('op_%s.jpg'%n) for n in ['side','rear','front']]
h=430;f=lambda x:cv2.resize(x,(int(x.shape[1]*h/x.shape[0]),h))
r=np.hstack([f(b)[:,:1200],f(a)]);r2=f(c)[:,:1200];r2=np.hstack([r2,np.zeros((h,r.shape[1]-r2.shape[1],3),np.uint8)])
cv2.imwrite('op3.jpg',np.vstack([r,r2]))"
