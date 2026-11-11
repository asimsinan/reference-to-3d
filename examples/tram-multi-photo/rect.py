"""rect.py K PLANE OUT ppm [u0 u1 z0 z1] -- rectify photo K onto a plane through the solved camera, metric grid.
PLANE: 'y=V' (side; u = x, image left = +x for y>0 ... we draw u increasing to the right as seen from outside) or 'x=V' (front; u = y)."""
import sys, json, os, numpy as np, cv2
from camlib import proj
k,plane,out=sys.argv[1],sys.argv[2],sys.argv[3]; ppm=float(sys.argv[4])
u0,u1,z0,z1=map(float,sys.argv[5:9])
ax,val=plane.split('='); val=float(val)
us=np.arange(u0,u1,1/ppm); zs=np.arange(z1,z0,-1/ppm)
U,Z=np.meshgrid(us,zs)
if ax=='y':   # seen from +y outside: right of image = -x when y>0 ... keep x increasing to the left for y>0 (front at left)
    X=np.stack([U,np.full_like(U,val),Z],-1)
else:
    X=np.stack([np.full_like(U,val),U,Z],-1)
q=proj(k,X.reshape(-1,3)).reshape(U.shape+(2,)).astype(np.float32)
im=cv2.imread(f'ref/p{k}.png') if os.path.exists(f'ref/p{k}.png') and not os.environ.get('REF2') else cv2.imread(f'ref2/p{k}.png')
r=cv2.remap(im,q[...,0],q[...,1],cv2.INTER_LINEAR,borderValue=(60,60,60))
if (ax=='y' and val>0) or (ax=='x' and val<0): r=np.ascontiguousarray(r[:,::-1]); us=us[::-1]   # view from outside
H,W=r.shape[:2]
def col(v): return np.argmin(abs(us-v))
for v in np.arange(np.ceil(u0*10)/10,u1,0.1):
    c=col(v); major=abs(v*2-round(v*2))<1e-6
    if major: cv2.line(r,(c,0),(c,H),(0,255,255),1); cv2.putText(r,'%.1f'%v,(c+2,14),0,0.45,(0,255,255),1)
    else: cv2.line(r,(c,0),(c,6),(0,255,255),1); cv2.line(r,(c,H-6),(c,H),(0,255,255),1)
for v in np.arange(np.ceil(z0*10)/10,z1,0.1):
    rr=int((z1-v)*ppm); major=abs(v*2-round(v*2))<1e-6
    if major: cv2.line(r,(0,rr),(W,rr),(0,255,255),1); cv2.putText(r,'%.1f'%v,(2,rr-2),0,0.45,(0,255,255),1)
    else: cv2.line(r,(0,rr),(6,rr),(0,255,255),1); cv2.line(r,(W-6,rr),(W,rr),(0,255,255),1)
cv2.imwrite(out,r)
