import numpy as np, cv2, sys
out=sys.argv[1]
ph=cv2.imread('../photo.jpg').astype(float)
r=cv2.imread(f'{out}/photo_view.png',cv2.IMREAD_UNCHANGED).astype(float)
a=r[...,3:]/255; comp=r[...,:3]*a+ph*(1-a)
sil=cv2.imread('mask_raw.png',0)>0; m=a[...,0]>0.5
print('IoU %.4f'%((sil&m).sum()/(sil|m).sum()))
d=np.abs(comp-ph).mean(2)
print('mean diff over model %.1f  median %.1f'%(d[m].mean(),np.median(d[m])))
REG=dict(rim=(180,195,410,252),inside=(200,200,390,240),neck=(220,260,370,380),belly=(150,400,440,650),foot=(200,700,390,820))
for nm,(x0,y0,x1,y1) in REG.items():
    mm=m[y0:y1,x0:x1]; print('%-8s %.1f'%(nm,d[y0:y1,x0:x1][mm].mean()))
dd=np.repeat(np.clip(d*3,0,255)[...,None],3,2)
crop=lambda x: x[180:840,100:490]
cv2.imwrite(f'{out}/compare.jpg',np.hstack([crop(ph),crop(comp),crop(dd)]).astype(np.uint8))
