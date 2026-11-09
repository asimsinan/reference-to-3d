"""Outer radius of the mesh wall r(z) from the silhouette's side edges (tangent rays), rows between the rings.
-> profile.json"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from cam import ray, P
s=cv2.imread('mask_photo.png',0)>0
U=[];V=[];S=[]
for v in range(990,1470,3):
    xs=np.where(s[v])[0]
    U+=[xs[0]-0.5,xs[-1]+0.5]; V+=[v,v]; S+=[0,1]
S=np.array(S); C,d=ray(np.array(U),np.array(V))
tc=-(C[0]*d[:,0]+C[1]*d[:,1])/(d[:,0]**2+d[:,1]**2)
t=tc[:,None]+np.linspace(-0.03,0.03,601)[None]
pts=C[None,None]+t[...,None]*d[:,None,:]
rho=np.hypot(pts[...,0],pts[...,1]); z=pts[...,2]
k=np.arange(len(tc)); zz=z[k,rho.argmin(1)]; rr=rho.min(1)
# a cylinder: fit r = a + b z, each side
for side in (0,1):
    q=S==side; A=np.polyfit(zz[q],rr[q],1); e=rr[q]-np.polyval(A,zz[q])
    print('side',side,'r = %.4f + %.4f z   resid std %.5f max %.5f  z %.3f..%.3f'%(A[1],A[0],e.std(),np.abs(e).max(),zz[q].min(),zz[q].max()))
A=np.polyfit(zz,rr,1); e=rr-np.polyval(A,zz)
print('both  r = %.4f + %.4f z   resid std %.5f'%(A[1],A[0],e.std()))
for zq in (0.02,0.05,0.08): print('  r(%.2f)=%.4f'%(zq,np.polyval(A,zq)))
json.dump(dict(a=A[1],b=A[0],pts=np.stack([zz,rr,S],1).tolist()),open('profile.json','w'))
