"""Photo vs the model from the photo's camera (emission render, out/photo_view.png composited over the photo).
usage: uv run --with opencv-python-headless --with numpy python cmp.py OUTDIR
prints IoU, mean/median colour difference over the model and per region (this photo's boxes); writes compare.jpg"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, sys
out=sys.argv[1]
ph=cv2.imread('photo.jpg').astype(float)
r=cv2.imread(f'{out}/photo_view.png',cv2.IMREAD_UNCHANGED).astype(float)
a=r[...,3:]/255; comp=r[...,:3]*a+ph*(1-a)
sil=cv2.imread('mask_photo.png',0)>0; m=a[...,0]>0.5
print('IoU %.4f'%((sil&m).sum()/(sil|m).sum()))
d=np.abs(comp-ph).mean(2)
print('mean diff over model %.1f  median %.1f'%(d[m].mean(),np.median(d[m])))
REG=dict(body=(420,1050,900,1650),inside=(420,905,940,985),rim_front=(400,975,950,1010),handle=(980,1030,1240,1560),bottom=(480,1700,880,1800))
for nm,(x0,y0,x1,y1) in REG.items():
    mm=m[y0:y1,x0:x1]; print('%-10s %.1f'%(nm,d[y0:y1,x0:x1][mm].mean()))
over=ph.copy(); over[cv2.dilate(cv2.Canny(m.astype(np.uint8)*255,50,150),np.ones((3,3)))>0]=(0,0,255)
dd=np.repeat(np.clip(d*3,0,255)[...,None],3,2)
crop=lambda x: x[860:1840,320:1260]
cv2.imwrite(f'{out}/compare.jpg',cv2.resize(np.vstack([np.hstack([crop(ph),crop(comp)]),np.hstack([crop(over),crop(dd)])]).astype(np.uint8),None,fx=0.5,fy=0.5))
