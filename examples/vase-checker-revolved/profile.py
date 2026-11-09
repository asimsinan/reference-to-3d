"""outer profile r(z) from both silhouette edges as tangent rays (mug-revolved/profile.py adapted)"""
import numpy as np, cv2, json
from cam import ray, P
from scipy.interpolate import UnivariateSpline
s=cv2.imread('mask_raw.png',0)>0
U=[];V=[];S=[]
for v in range(224,800,2):
    xs=np.where(s[v])[0]
    U+=[xs[0]-0.5,xs[-1]+0.5]; V+=[v,v]; S+=[0,1]
S=np.array(S); C,d=ray(np.array(U),np.array(V))
tc=-(C[0]*d[:,0]+C[1]*d[:,1])/(d[:,0]**2+d[:,1]**2)
t=tc[:,None]+np.linspace(-0.06,0.06,1201)[None]
pts=C[None,None]+t[...,None]*d[:,None,:]
rho=np.hypot(pts[...,0],pts[...,1]); z=pts[...,2]; k=np.arange(len(tc))
zz=z[k,rho.argmin(1)]; rr=rho.min(1)
from scipy import ndimage as ndi
ZG=np.linspace(0.0,0.30,301)
def fit(zz,rr):
    keep=np.ones(len(zz),bool)
    for _ in range(3):
        idx=np.clip(np.round(zz[keep]/0.001).astype(int),0,300); sm=np.bincount(idx,rr[keep],301); cn=np.bincount(idx,None,301)
        ok=cn>0; g=np.interp(ZG,ZG[ok],sm[ok]/cn[ok]); g=ndi.gaussian_filter1d(g,1.5,mode='nearest')
        lo,hi=ZG[ok].min(),ZG[ok].max()
        f=lambda q,g=g,lo=lo,hi=hi: np.interp(np.clip(q,lo,hi),ZG,g)
        e=rr-f(zz); keep=np.abs(e)<max(3*np.std(e[keep]),0.0006)
    return f,keep
for it in range(12):
    f,keep=fit(zz,rr); g=rho-f(z); j=g.argmin(1); m=g[k,j]; zz=z[k,j]; rr=f(zz)+m
f,keep=fit(zz,rr)
for side in (0,1):
    q=S==side; e=rr[q]-f(zz[q]); print('side',side,'mean %.5f std %.5f'%(e.mean(),e.std()))
print('dropped',(~keep).sum(),'z range %.4f..%.4f h %.4f'%(zz.min(),zz.max(),P['h']))
zs=np.linspace(zz.min(),zz.max(),160)
for a,b in zip(zs[::8],f(zs[::8])): print('  z %.4f r %.4f'%(a,b))
json.dump(dict(z=zs.tolist(),r=f(zs).tolist(),pts=np.stack([zz,rr,S],1).tolist()),open('profile.json','w'))
