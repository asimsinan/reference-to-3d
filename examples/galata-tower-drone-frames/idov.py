import cv2,numpy as np,sys
tiles=[]
for k in ['r1','r2','r3','r4']:
    a=cv2.imread('ref/%s.png'%k); idm=cv2.imread('id/%s.png'%k,cv2.IMREAD_UNCHANGED)
    idx=np.round(idm[...,2]/8.0).astype(int); idx[idm[...,3]<128]=0
    e=(cv2.dilate(idx.astype(np.uint8),np.ones((2,2),np.uint8))!=cv2.erode(idx.astype(np.uint8),np.ones((2,2),np.uint8)))
    o=a.copy(); o[e]=(0,255,255)
    H=900; o=cv2.resize(o,(int(o.shape[1]*H/o.shape[0]),H)); tiles.append(o)
cv2.imwrite('out/idov.jpg',np.hstack(tiles))
