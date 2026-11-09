"""Outer profile r(z) of the mug from the silhouette edges, each edge ray tangent to the surface of revolution.
writes profile.json: z (m), r (m) samples, bottom to rim.
usage: uv run --with opencv-python-headless --with numpy --with scipy python profile.py
Each ray's tangent point is searched only near its closest approach to the axis (a spline evaluated outside its data
blew the iteration up), the spline is clipped to its range, outliers are dropped. Rows where the handle's roots join
the body's right edge are left out (this photo: right edges only above v 1030 and below v 1545). The lowest rows are
the base's front, not tangents: fit_bottom.py takes over below Z1."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from cam import ray, P
s=cv2.imread('mask_photo.png',0)>0
U=[];V=[];S=[]
for v in range(958,1772,3):
    xs=np.where(s[v])[0]; runs=np.split(xs,np.where(np.diff(xs)>1)[0]+1)
    U.append(runs[0][0]-0.5); V.append(v); S.append(0)
    if v<1030 or v>1545:
        U.append(runs[0][-1]+0.5); V.append(v); S.append(1)
S=np.array(S)
C,d=ray(np.array(U),np.array(V))
# closest approach to the axis, then search only near it
tc=-(C[0]*d[:,0]+C[1]*d[:,1])/(d[:,0]**2+d[:,1]**2)
t=tc[:,None]+np.linspace(-0.06,0.06,1201)[None]
pts=C[None,None]+t[...,None]*d[:,None,:]
rho=np.hypot(pts[...,0],pts[...,1]); z=pts[...,2]
k=np.arange(len(tc))
zz=z[k,rho.argmin(1)]; rr=rho.min(1)
from scipy.interpolate import UnivariateSpline
def fit(zz,rr):
    keep=np.ones(len(zz),bool)
    for _ in range(3):
        o=np.argsort(zz[keep]); a=zz[keep][o]; b=rr[keep][o]
        sp=UnivariateSpline(a,b,k=3,s=len(a)*0.0003**2)
        e=rr-sp(np.clip(zz,a.min(),a.max())); keep=np.abs(e)<max(3*np.std(e[keep]),0.0004)
    lo,hi=a.min(),a.max(); return lambda q: sp(np.clip(q,lo,hi))
for it in range(10):
    f=fit(zz,rr); g=rho-f(z); j=g.argmin(1); m=g[k,j]
    zz=z[k,j]; rr=f(zz)+m
    print('iter',it,'max |m| %.5f'%np.abs(m).max())
f=fit(zz,rr)
for side in (0,1):
    q=S==side; print('side',side,'mean resid %.5f'%(rr[q]-f(zz[q])).mean())
zs=np.linspace(zz.min(),zz.max(),50)
print('z range %.4f..%.4f, rim h %.4f'%(zz.min(),zz.max(),P['h']))
for a,b in zip(zs[::5],f(zs[::5])): print('  z %.4f r %.4f'%(a,b))
print('residual std %.5f max %.5f'%(np.std(rr-f(zz)),np.abs(rr-f(zz)).max()))
json.dump(dict(z=zs.tolist(),r=f(zs).tolist(),pts=np.stack([zz,rr,S],1).tolist()),open('profile.json','w'))
