"""Photo vs the model from the photo's camera. usage: python cmp.py OUTDIR -> numbers + OUTDIR/compare.jpg"""
import sys,numpy as np,cv2
out=sys.argv[1]
ph=cv2.imread('photo.jpg').astype(float)
r=cv2.imread(f'{out}/photo_view.png',cv2.IMREAD_UNCHANGED).astype(float)
a=r[...,3:]/255; comp=r[...,:3]*a+ph*(1-a); m=a[...,0]>0.5
sil=cv2.imread('mask_photo.png',0)>0
print('IoU vs GrabCut, rows<1545 (cap, collar, label): %.4f'%(((sil&m)[:1545]).sum()/((sil|m)[:1545]).sum()))
d=np.abs(comp-ph).mean(2)
print('mean colour diff over model %.1f  median %.1f'%(d[m].mean(),np.median(d[m])))
REG=dict(cap=(715,465,900,690),collar=(680,710,905,855),clear_top=(625,880,945,975),label=(615,1000,940,1540),base=(610,1560,940,1690))
for nm,(x0,y0,x1,y1) in REG.items():
    mm=m[y0:y1,x0:x1]; print('%-10s %.1f'%(nm,d[y0:y1,x0:x1][mm].mean()))
over=ph.copy(); over[cv2.dilate(cv2.Canny(m.astype(np.uint8)*255,50,150),np.ones((3,3)))>0]=(0,0,255)
dd=np.repeat(np.clip(d*3,0,255)[...,None],3,2)
crop=lambda x: x[430:1710,560:1020]
cv2.imwrite(f'{out}/compare.jpg',cv2.resize(np.hstack([crop(ph),crop(comp),crop(over),crop(dd)]).astype(np.uint8),None,fx=0.6,fy=0.6))
