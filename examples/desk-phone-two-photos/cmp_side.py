import cv2, numpy as np, sys
ref=cv2.imread('side.jpg').astype(np.float32)
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED).astype(np.float32)
a=r[...,3:]/255; rgb=r[...,:3]; m=a[...,0]>0.99
d=np.abs(rgb-ref).mean(2)
print('SIDE mean diff /255 on model pixels: %.1f  median %.1f   coverage px %d'%(d[m].mean(),np.median(d[m]),m.sum()))
for nm,(x0,y0,x1,y1) in {'wall upper':(600,830,1000,960),'wall lower':(200,790,450,900),'handset':(250,600,1100,760),'arch/grille':(430,690,800,820)}.items():
    mm_=m[y0:y1,x0:x1]; print(f'  {nm:11s} {d[y0:y1,x0:x1][mm_].mean():.1f}  (coverage {mm_.mean()*100:.0f}%)')
comp=rgb*a+ref*(1-a)
edge=cv2.Canny((a[...,0]*255).astype(np.uint8),50,150); ov=ref.copy(); ov[edge>0]=(0,255,255)
dimg=cv2.cvtColor(np.clip(d*3,0,255).astype(np.uint8),cv2.COLOR_GRAY2BGR)
crop=lambda im: im[540:1120,100:1200]
cv2.imwrite(sys.argv[2],cv2.resize(np.vstack([np.hstack([crop(ref),crop(comp)]),np.hstack([crop(ov),crop(dimg)])]),(1600,844)))
