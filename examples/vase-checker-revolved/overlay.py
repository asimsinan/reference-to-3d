"""union of projected discs of the current profile (+foot) vs the mask; writes ov.png (crop x2) and IoU"""
import numpy as np, cv2, json, sys
import cam as C
from geom import prof_out
im=cv2.imread('../photo.jpg'); sil=cv2.imread('mask_raw.png',0)>0
m=np.zeros(sil.shape,np.uint8); ang=np.linspace(0,2*np.pi,360,endpoint=False)
zr=prof_out()
for z,r in zr:
    uv=C.proj(np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1))
    cv2.fillPoly(m,[np.round(uv*8).astype(np.int32)],1,shift=3)
m=m>0; print('IoU %.4f'%((m&sil).sum()/(m|sil).sum()))
vis=im.copy(); vis[m&~sil]=(0,0,255); vis[sil&~m]=(255,0,0)
cv2.drawContours(vis,cv2.findContours(m.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0],-1,(0,255,0),1)
y0,y1,x0,x1=[int(a) for a in (sys.argv[1:5] if len(sys.argv)>4 else (180,840,100,490))]
cv2.imwrite('ov.png',cv2.resize(vis[y0:y1,x0:x1],None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST))
