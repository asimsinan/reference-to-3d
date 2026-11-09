import cv2, numpy as np, sys
ref=cv2.imread('ref.jpg'); r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED)
idimg=r[...,:3].astype(int); a=r[...,3]
dif=lambda A,B: np.abs(A-B).sum(-1)>24
e=np.zeros(a.shape,bool); e[:-1]|=dif(idimg[:-1],idimg[1:])|((a[:-1]>128)!=(a[1:]>128)); e[:,:-1]|=dif(idimg[:,:-1],idimg[:,1:])|((a[:,:-1]>128)!=(a[:,1:]>128))
ov=ref.copy(); ov[e]=(0,255,255)
for nm,(x0,y0,x1,y1),s in [('idA',(330,250,680,420),3),('idB',(580,470,940,970),2),('idC',(60,450,480,820),2),('idD',(220,380,780,960),1.6)]:
    cv2.imwrite(nm+'.png',cv2.resize(ov[y0:y1,x0:x1],None,fx=s,fy=s,interpolation=cv2.INTER_NEAREST))
