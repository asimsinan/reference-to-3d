from geom import *
import cv2
lab=cv2.GaussianBlur(cv2.cvtColor(cv2.imread('ref.jpg'),cv2.COLOR_BGR2LAB).astype(np.float32),(3,3),0)
gm=sum(np.hypot(cv2.Sobel(lab[...,i],cv2.CV_32F,1,0),cv2.Sobel(lab[...,i],cv2.CV_32F,0,1)) for i in range(3))
def score(rc,cx,cy,a0,a1,z):
    a=np.linspace(a0,a1,40); P=np.c_[cx+rc*np.cos(a), cy+rc*np.sin(a), np.full_like(a,z)]
    q=proj(P); return np.mean([gm[int(round(v)),int(round(u))] for u,v in q])
for nm,(sx,sy) in {'B':(-1,-1),'C':(1,-1),'A':(-1,1)}.items():
    best=[]
    for rc in np.arange(0.01,0.12,0.005):
        cx=sx*(L/2-rc); cy=sy*(W/2-rc)
        a0=np.arctan2(sy,0) if True else 0
        # arc between the two side directions
        angs=np.arctan2(sy,0), np.arctan2(0,sx)
        s=score(rc,cx,cy,min(angs),max(angs),H) if not (sx==-1 and sy==-1) else score(rc,cx,cy,-np.pi,-np.pi/2,H)
        if sx==-1 and sy==1: s=score(rc,cx,cy,np.pi/2,np.pi,H)
        best.append((s,rc))
    best.sort(reverse=True); print(nm,[('%.3f'%r,'%.0f'%s) for s,r in best[:4]])
