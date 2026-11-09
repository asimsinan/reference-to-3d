"""The bottom corner: the lowest rows of the silhouette are the front of the base, not tangent rays, so the profile
from profile.py stops short of it. Fit r(z) = rf + (r(Z1) - rf) (1 - (1 - z/Z1)^p)^(1/p) for z < Z1: the silhouette of
a solid of revolution is the union of its projected discs, so each row's ends are the extremes over the discs.
usage: uv run --with opencv-python-headless --with numpy --with scipy python fit_bottom.py   -> bottom.json"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from scipy.optimize import minimize
import cam as C
from geom import ro
sil=cv2.imread('mask_photo.png',0)>0
rows=list(range(1730,1802,2))
obs=[]
for v in rows:
    a=np.where(sil[v])[0]; obs.append((a.min()-0.5,a.max()+0.5))
obs=np.array(obs); Z1=0.014
ang=np.linspace(0,2*np.pi,360)
def mask_rows(rf,p):
    zs=np.linspace(0,Z1,40); r1=ro(Z1)
    L=np.full(len(rows),np.inf); R=np.full(len(rows),-np.inf)
    for z in zs:
        t=z/Z1; r=rf+(r1-rf)*(1-(1-t)**p)**(1/p)
        uv=C.proj(np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1))
        poly=uv
        for k,v in enumerate(rows):
            # intersection of horizontal line v with the ellipse polygon
            s=np.sign(poly[:,1]-v); idx=np.where(s[:-1]!=s[1:])[0]
            for i in idx:
                f=(v-poly[i,1])/(poly[i+1,1]-poly[i,1]); u=poly[i,0]+f*(poly[i+1,0]-poly[i,0])
                L[k]=min(L[k],u); R[k]=max(R[k],u)
    return L,R,r1
def cost(x):
    L,R,_=mask_rows(*x); e=np.r_[L-obs[:,0],R-obs[:,1]]; e[~np.isfinite(e)]=40; return (e**2).mean()
for x0 in [(0.026,2.0),(0.024,3),(0.022,2.5)]:
    print(x0,cost(x0))
res=minimize(cost,(0.024,2.5),method='Nelder-Mead',options=dict(xatol=1e-5,fatol=0.01))
print(res.x,res.fun)
L,R,r1=mask_rows(*res.x)
for k in range(0,len(rows),4): print(rows[k],obs[k],round(L[k],1),round(R[k],1))
json.dump(dict(rf=res.x[0],p=res.x[1],Z1=Z1),open('bottom.json','w'))
