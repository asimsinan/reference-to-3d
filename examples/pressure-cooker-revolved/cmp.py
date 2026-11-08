"""Photo vs the model rendered from the photo's camera (emission, Standard).
usage: uv run --with opencv-python-headless --with numpy python cmp.py OUTDIR    (reads OUTDIR/photo_view.png)
prints silhouette IoU (rows above the floor's shadow), mean/median colour difference over the model, per region;
writes OUTDIR/compare.png: photo | render over white / model outline over the photo | difference x3."""
import numpy as np, cv2, sys
out=sys.argv[1]
ph=cv2.imread('photo.jpg').astype(float)
r=cv2.imread(f'{out}/photo_view.png',cv2.IMREAD_UNCHANGED).astype(float)
a=r[...,3:]/255; comp=r[...,:3]*a+255*(1-a)
sil=cv2.imread('mask_photo.png',0)>0; m=a[...,0]>0.5
lim=np.zeros_like(sil); lim[:418]=True
print('IoU %.4f'%(((sil&m&lim).sum())/(((sil|m)&lim).sum())))
d=np.abs(comp-ph).mean(2)
print('mean diff over model %.1f  median %.1f'%(d[m].mean(),np.median(d[m])))
REG=dict(body=(130,240,340,400),lid=(110,165,350,195),handle_main=(380,150,515,240),
         handle_left=(37,195,100,235),tab=(100,148,180,170))   # x0,y0,x1,y1 (this photo)
for nm,(x0,y0,x1,y1) in REG.items():
    mm=m[y0:y1,x0:x1]
    if mm.any(): print('%-12s %.1f'%(nm,d[y0:y1,x0:x1][mm].mean()))
over=ph.copy(); over[cv2.Canny(m.astype(np.uint8)*255,50,150)>0]=(0,0,255)
dd=np.repeat(np.clip(d*3,0,255)[...,None],3,2)
cv2.imwrite(f'{out}/compare.png',np.vstack([np.hstack([ph,comp]),np.hstack([over,dd])]).astype(np.uint8))
