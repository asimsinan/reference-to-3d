"""Fit a rounded cushion (plan 2a x 2b, plan corner radius rc, from z_rim up to z_top with a rounded top edge re)
to a cushion's photo outline. Residuals: mask contour points -> predicted hull boundary, and hull boundary -> mask."""
from geom import *
import cv2, json, sys
from scipy.optimize import least_squares
RE=0.03
def outline(cx,cy,th,a,b,rc,z,ins=0.0,n=10):
    a_,b_,r_=a-ins,b-ins,max(rc-ins,0.002); pts=[]
    for (sx,sy,a0) in [(1,1,0),(-1,1,90),(-1,-1,180),(1,-1,270)]:
        for t in np.radians(np.linspace(a0,a0+90,n)):
            pts.append((sx*(a_-r_)+r_*np.cos(t), sy*(b_-r_)+r_*np.sin(t)))
    P=np.array(pts); c,s=np.cos(th),np.sin(th)
    return np.c_[cx+c*P[:,0]-s*P[:,1], cy+s*P[:,0]+c*P[:,1], np.full(len(P),z)]
def hull(p):
    cx,cy,th,a,b,rc,zr,zt=p; P=[outline(cx,cy,th,a,b,rc,zr)]
    for z in np.linspace(zt-RE,zt,5):
        ins=RE-np.sqrt(max(RE**2-(z-(zt-RE))**2,0)); P.append(outline(cx,cy,th,a,b,rc,z,ins))
    q=proj(np.vstack(P)).astype(np.float32); return cv2.convexHull(q)[:,0,:]
def seg_dist(pts,poly):
    A=poly; B=np.roll(poly,-1,0); d=np.full(len(pts),1e9)
    for a,b in zip(A,B):
        ab=b-a; t=np.clip(((pts-a)@ab)/(ab@ab+1e-9),0,1); q=a+t[:,None]*ab; d=np.minimum(d,np.linalg.norm(pts-q,axis=1))
    return d
def fit(name,p0,keep=lambda x,y: np.ones_like(x,bool),fixed={}):
    m=cv2.imread(f'mask_{name}.png',0)>0
    cs,_=cv2.findContours(m.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE); c=max(cs,key=len)[:,0,:].astype(float)
    c=c[keep(c[:,0],c[:,1])][::2]
    dt=cv2.distanceTransform((~cv2.Canny(m.astype(np.uint8)*255,50,150).astype(bool)).astype(np.uint8),cv2.DIST_L2,3)
    names=['cx','cy','th','a','b','rc','zr','zt']; free=[i for i,n in enumerate(names) if n not in fixed]
    def full(x):
        p=np.array(p0,float); p[free]=x
        for k,v in fixed.items(): p[names.index(k)]=v
        return p
    def res(x):
        h=hull(full(x)); r1=seg_dist(c,h)
        # hull boundary samples -> mask edge (only where the kept contour lives)
        B=np.roll(h,-1,0); s=np.vstack([h+(B-h)*t for t in np.linspace(0,1,6)[:-1]])
        s=s[keep(s[:,0],s[:,1])]; s=np.clip(s,0,999)
        r2=dt[s[:,1].astype(int),s[:,0].astype(int)]
        return np.r_[r1,0.5*r2]
    r=least_squares(res,np.array(p0,float)[free],x_scale=0.02)
    p=full(r.x); rr=seg_dist(c,hull(p))
    print(name,'  '.join('%s %.3f'%(n,v) for n,v in zip(names,p)),' th %.1f deg  contour rms %.2f px'%(np.degrees(p[2]),np.sqrt((rr**2).mean())))
    return p
if __name__=='__main__':
    out={}
    out['S1']=fit('S1',[-0.192,-0.459,0.02,0.19,0.16,0.04,0.40,0.46]).tolist()
    json.dump(out,open('cush.json','w'),indent=1)
