"""photo vs render from the photo's camera: mean colour difference on the model's pixels, per region, and a sheet."""
import cv2, numpy as np, sys
ref=cv2.imread('ref.jpg').astype(np.float32)
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED).astype(np.float32)
if r.shape[2]==4: a=r[...,3:]/255; rgb=r[...,:3]
else: a=np.ones_like(r[...,:1]); rgb=r
m=a[...,0]>0.99; d=np.abs(rgb-ref).mean(2)
print('mean diff /255 on model pixels: %.1f  median %.1f  (model covers %d px)'%(d[m].mean(),np.median(d[m]),m.sum()))
REG={'table top':(240,300,760,450),'short apron':(285,460,475,505),'near legs':(250,520,530,940),'stool S1':(600,550,880,960),
     'stool S2':(700,480,930,740),'bench':(75,470,250,800),'cups':(350,335,590,410),'plate+muffins':(490,315,605,360),'sphere+candle':(570,280,662,335)}
for nm,(x0,y0,x1,y1) in REG.items():
    mm=m[y0:y1,x0:x1]
    if mm.sum(): print(f'  {nm:14s} {d[y0:y1,x0:x1][mm].mean():5.1f}   ({mm.sum()} px)')
comp=rgb*a+ref*(1-a)
edge=cv2.Canny((a[...,0]*255).astype(np.uint8),50,150); ov=ref.copy(); ov[edge>0]=(0,255,255)
dimg=cv2.cvtColor(np.clip(d*3*m,0,255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
sheet=np.vstack([np.hstack([ref,comp]),np.hstack([ov,dimg])])
cv2.imwrite(sys.argv[2],cv2.resize(sheet,(1600,1600)))
if len(sys.argv)>3:
    x0,y0,x1,y1=map(int,sys.argv[3].split(',')); cv2.imwrite(sys.argv[4],cv2.resize(ov[y0:y1,x0:x1],None,fx=3,fy=3,interpolation=cv2.INTER_NEAREST))
