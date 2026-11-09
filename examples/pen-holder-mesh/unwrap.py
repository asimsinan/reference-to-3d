"""Unwrap the photo onto the wall cylinder: columns = angle phi (deg, +Y side at the right as in the image), rows = z.
usage: py scripts/unwrap.py [r_wall]  -> unwrap.png (0.1 mm/px), prints lattice pitch from autocorrelation."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from cam import proj, P
im=cv2.imread('photo.jpg'); H,W=im.shape[:2]
r=float(sys.argv[1]) if len(sys.argv)>1 else 0.0445
S=0.0001
phis=np.radians(np.arange(-85,85,np.degrees(S/r)))      # 0.1 mm steps along the circumference
zs=np.arange(0.012,0.094,S)
PH,Z=np.meshgrid(phis,zs)
X=np.stack([r*np.cos(PH),r*np.sin(PH),Z],-1).reshape(-1,3)
uv=proj(X).reshape(PH.shape+(2,)).astype(np.float32)
out=cv2.remap(im,uv[...,0],uv[...,1],cv2.INTER_LINEAR)
cv2.imwrite('unwrap.png',out)
g=cv2.cvtColor(out,cv2.COLOR_BGR2GRAY).astype(float)
deg=np.degrees(phis)
for (p0,p1) in [(40,65),(-20,20),(-65,-40)]:
    c0,c1=np.searchsorted(deg,p0),np.searchsorted(deg,p1)
    pt=g[200:700,c0:c1].copy(); pt-=pt.mean()
    F=np.fft.fft2(pt); ac=np.fft.fftshift(np.real(np.fft.ifft2(F*np.conj(F)))); ac/=ac.max()
    cy,cx=np.array(ac.shape)//2
    row=ac[cy,cx:cx+80]; col=ac[cy:cy+80,cx]
    px=[i for i in range(3,79) if row[i]>row[i-1] and row[i]>row[i+1] and row[i]>0.05][:3]
    py_=[i for i in range(3,79) if col[i]>col[i-1] and col[i]>col[i+1] and col[i]>0.05][:3]
    print('phi %d..%d: horizontal period(s) %s (0.1mm), vertical %s'%(p0,p1,[(i,round(row[i],2)) for i in px],[(i,round(col[i],2)) for i in py_]))
print('unwrap.png',out.shape)
