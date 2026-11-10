# IoU of the model silhouette against the saved GrabCut masks (mask/rN.png), plus per-side error bands
import cv2,numpy as np,json
IGN=json.load(open('ignore.json')); tot=[]
def fillholes(m):
    m=m.astype(np.uint8); h,w=m.shape; ff=m.copy(); mk=np.zeros((h+2,w+2),np.uint8); cv2.floodFill(ff,mk,(0,0),1); return (m|(1-ff))>0
for i in range(1,7):
    ph=cv2.imread('mask/r%d.png'%i,0)>127; idm=cv2.imread('id/r%d.png'%i,cv2.IMREAD_UNCHANGED); mod=fillholes((idm[...,3]>=128)&(idm[...,2]>0))
    ok=np.ones(ph.shape,np.uint8)
    for poly in IGN.get('r%d'%i,[]): cv2.fillPoly(ok,[np.array(poly,np.int32)],0)
    ok=ok>0; iou=(ph&mod&ok).sum()/((ph|mod)&ok).sum(); tot.append(iou)
    print('r%d IoU %.3f  photo-only %5d px  model-only %5d px'%(i,iou,(ph&~mod&ok).sum(),(mod&~ph&ok).sum()))
    v=(cv2.imread('ref/r%d.png'%i)*0.45).astype(np.uint8); v[ph&mod]=(0,170,0); v[ph&~mod]=(0,0,255); v[~ph&mod]=(255,80,0)
    cv2.imwrite('g/gc%d.jpg'%i,cv2.resize(v,None,fx=0.5,fy=0.5))
print('mean IoU %.3f'%np.mean(tot))
