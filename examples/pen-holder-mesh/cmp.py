"""Photo vs model from the photo's camera. usage: py scripts/cmp.py OUTDIR -> numbers, OUTDIR/compare.jpg"""
import numpy as np, cv2, sys
out=sys.argv[1]
ph=cv2.imread('photo.jpg').astype(float)
r=cv2.imread(f'{out}/photo_view.png',cv2.IMREAD_UNCHANGED).astype(float)
a=r[...,3:]/255; comp=r[...,:3]*a+ph*(1-a)
sil=cv2.imread('mask_photo.png',0)>0; m=a[...,0]>0.5
hm=cv2.imread(f'{out}/holder_mask.png',cv2.IMREAD_UNCHANGED)[...,3]>127; hm[:888]=False
print('holder IoU %.4f (all rows)  %.4f (below the rim, rows>1000: the photo mask loses the rim behind the pens)'%((sil&hm).sum()/(sil|hm).sum(),(sil&hm)[1000:].sum()/(sil|hm)[1000:].sum()))
d=np.abs(comp-ph).mean(2)
print('mean colour diff over model %.1f  median %.1f'%(d[m].mean(),np.median(d[m])))
REG=dict(rim=(580,890,1120,1000),wall=(600,1010,1100,1540),pens_above=(690,640,990,890),base=(600,1540,1100,1610),
         wall_right=(1000,1100,1080,1400),wall_left=(600,1100,680,1400),wall_mid=(700,1050,1000,1500),glue=(860,1000,930,1100),spoon=(850,1300,950,1500),pen1_body=(640,1050,700,1300),marker_body=(790,1050,850,1400))
pb=cv2.GaussianBlur(ph,(0,0),6); cb=cv2.GaussianBlur(comp,(0,0),6); db=np.abs(cb-pb).mean(2)
print('%-11s %6s %6s   %8s %8s'%('region','diff','blur6','photo','render'))
for nm,(x0,y0,x1,y1) in REG.items():
    mm=m[y0:y1,x0:x1]
    print('%-11s %6.1f %6.1f   %8.1f %8.1f  (coverage %.2f)'%(nm,d[y0:y1,x0:x1][mm].mean() if mm.any() else -1,db[y0:y1,x0:x1].mean(),ph[y0:y1,x0:x1].mean(),comp[y0:y1,x0:x1].mean(),mm.mean()))
over=ph.copy(); over[cv2.dilate(cv2.Canny(m.astype(np.uint8)*255,50,150),np.ones((2,2)))>0]=(0,0,255)
dd=np.repeat(np.clip(d*3,0,255)[...,None],3,2)
crop=lambda x: x[600:1640,520:1180]
cv2.imwrite(f'{out}/compare.jpg',cv2.resize(np.vstack([np.hstack([crop(ph),crop(comp)]),np.hstack([crop(over),crop(dd)])]).astype(np.uint8),None,fx=0.5,fy=0.5))
cv2.imwrite(f'{out}/side_by_side.jpg',np.hstack([crop(ph),crop(comp)]).astype(np.uint8))
