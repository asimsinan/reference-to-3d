"""photo unwrapped onto (angle, z): unwrap.png  (cols: phi -90..90 deg, 0.25 deg/px; rows: z top->bottom, 0.25 mm/px)"""
import numpy as np, cv2, json
import cam as C
from geom import prof_out, h
im=cv2.imread('../photo.jpg')
zr=np.array(prof_out(1200))
phis=np.radians(np.arange(-90,90,0.25)); zs=np.arange(h,0,-0.00025)
rr=np.interp(zs,zr[:,0],zr[:,1])
PH,ZZ=np.meshgrid(phis,zs); RR=np.meshgrid(phis,rr)[1]
X=np.stack([RR*np.cos(PH),RR*np.sin(PH),ZZ],-1).reshape(-1,3)
uv=C.proj(X).reshape(len(zs),len(phis),2).astype(np.float32)
out=cv2.remap(im,uv[...,0],uv[...,1],cv2.INTER_LINEAR)
cv2.imwrite('unwrap.png',out); print(out.shape)
