import cv2, numpy as np, sys
ref=cv2.imread('ref.jpg').astype(np.float32)
r=cv2.imread(sys.argv[1],cv2.IMREAD_UNCHANGED).astype(np.float32)
a=r[...,3:]/255; rgb=r[...,:3]
m=a[...,0]>0.99
d=np.abs(rgb-ref).mean(2)
print('mean diff /255 on model pixels: %.1f  median %.1f'%(d[m].mean(),np.median(d[m])))
# regions
for nm,(x0,y0,x1,y1) in {'screen':(600,100,1650,780),'keyboard':(520,880,1750,1080),'palmrest':(350,1120,1900,1320),'front edge':(400,1355,1800,1385)}.items():
    mm=m[y0:y1,x0:x1]; print(f'  {nm:10s} {d[y0:y1,x0:x1][mm].mean():.1f}')
comp=rgb*a+ref*(1-a)
# silhouette: photo laptop region not given; show edges of model over photo
edge=cv2.Canny((a[...,0]*255).astype(np.uint8),50,150)
ov=ref.copy(); ov[edge>0]=(0,255,255)
dimg=np.clip(d*3,0,255).astype(np.uint8); dimg=cv2.cvtColor(dimg,cv2.COLOR_GRAY2BGR)
top=np.hstack([ref,comp]); bot=np.hstack([ov,dimg])
cv2.imwrite(sys.argv[2],cv2.resize(np.vstack([top,bot]),(1600,1200)))
