# edgefit.py : refine each photo camera (pos, yaw/pitch/roll, f, principal point) by fitting projected model edges
# to the photo's Canny edges (distance transform, robust loss). Writes cams.json (backup cams_pre_edge.json).
import cv2,numpy as np,json,shutil,os
from scipy.optimize import least_squares
p=json.load(open('params.json')); cams=json.load(open('cams.json')); IGN=json.load(open('ignore.json'))
if not os.path.exists('cams_pre_edge.json'): shutil.copy('cams.json','cams_pre_edge.json')
A=p['A']; segs=[]
def loop(pts,z,closed=True):
    n=len(pts)
    for i in range(n if closed else n-1): segs.append(((*pts[i],z),(*pts[(i+1)%n],z)))
loop(p['terrace'],p['kerb_h']); loop(p['quay'],-0.15)
F=p['fort']; fr=[(F['x0'],F['y0']),(F['x1'],F['y0']),(F['x1'],F['y1']),(F['x0'],F['y1'])]; loop(fr,0)
for sx,sy in ((1,1),(1,-1),(-1,-1),(-1,1)): segs.append(((sx*A,sy*A,0.0),(sx*A,sy*A,p['z_corb1'])))
from math import cos,sin,pi
oc=[(p['r_balc']*cos(k*pi/4),p['r_balc']*sin(k*pi/4)) for k in range(8)]; loop(oc,p['z_balc']); loop(oc,p['z_balc']+p['balc_t'])
a=p['annex']; loop([(a['x0'],a['y0']),(a['x1'],a['y0']),(a['x1'],a['y1']),(a['x0'],a['y1'])],0)
segs.append(((0,0,p['z_pole']),(0,0,p['z_gold'])))
P=[]
for s0,s1 in segs:
    s0,s1=np.array(s0),np.array(s1); n=max(2,int(np.linalg.norm(s1-s0)/0.25))
    for t in np.linspace(0,1,n): P.append(s0+(s1-s0)*t)
P=np.array(P); print(len(P),'edge samples')
def Rm(yaw,pitch,roll):
    cy,sy,cp,sp=np.cos(yaw),np.sin(yaw),np.cos(pitch),np.sin(pitch)
    fwd=np.array([cy*cp,sy*cp,-sp]); right=np.array([sy,-cy,0.0]); down=np.cross(fwd,right); R=np.stack([right,down,fwd])
    cr,sr=np.cos(roll),np.sin(roll); return np.array([[cr,-sr,0],[sr,cr,0],[0,0,1]])@R
def decompose(R):
    fwd=R[2]; yaw=np.arctan2(fwd[1],fwd[0]); pitch=-np.arcsin(fwd[2]); R0=Rm(yaw,pitch,0); M=R@R0.T; roll=np.arctan2(M[1,0],M[0,0]); return yaw,pitch,roll
src=open('solve.py').read(); ns={}
exec(src[src.index('P={'):src.index("names=")],{'A':3.25},ns); g=json.load(open('geo.json'))
WP={'G':(g['px'],g['py'],g['zG']),'PB':(g['px'],g['py'],g['zPB']),'K1t':(g['x1'],-g['L'],g['hw']),'K1b':(g['x1']+g['bat'],-g['L']-g['bat'],g['zb1']),
   'K2t':(A-g['Lx'],-g['L'],g['hw']),'K2b':(A-g['Lx']-g['bat'],-g['L']-g['bat'],0),'K3t':(A-g['Lx'],g['k3y'],g['hw']),'K3b':(A-g['Lx'],g['k3y'],0),
   'BT':(g['bx'],g['by'],g['bz']),'Ar1':(g['a1'],-g['L'],0),'Ar2':(g['a2'],-g['L'],0),'Ar3':(g['a3'],-g['L'],0)}
out={}
for k,c in cams.items():
    im=cv2.imread('ref/%s.png'%k); g=cv2.GaussianBlur(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY),(0,0),1.2)
    e=cv2.Canny(g,40,110); ok=np.ones(e.shape,np.uint8)
    for poly in IGN.get(k,[]): cv2.fillPoly(ok,[np.array(poly,np.int32)],0)
    e[ok==0]=0; dt=cv2.distanceTransform((e==0).astype(np.uint8),cv2.DIST_L2,5).astype(np.float32)
    H,W=e.shape; R=np.array(c['R']); yaw,pitch,roll=decompose(R)
    x0=np.array([*c['pos'],yaw,pitch,roll,np.log(c['f']),c['cx'],c['cy']])
    def proj(x):
        Rr=Rm(*x[3:6]); q=(P-x[:3])@Rr.T; f=np.exp(x[6]); return f*q[:,0]/q[:,2]+x[7], f*q[:,1]/q[:,2]+x[8]
    ii=int(k[1:]); obs=[(np.array(WP[n]),np.array(o[ii],float)) for n,o in ns['P'].items() if ii in o]
    def ptres(x):
        Rr=Rm(*x[3:6]); f=np.exp(x[6]); r=[]
        for X3,uv in obs:
            q=Rr@(X3-x[:3]); r+=list((np.array([f*q[0]/q[2]+x[7],f*q[1]/q[2]+x[8]])-uv)/1.5)
        return np.array(r)
    def res(x):
        u,v=proj(x); inside=(u>1)&(u<W-2)&(v>1)&(v<H-2)
        d=np.where(inside,cv2.remap(dt,u.astype(np.float32).reshape(-1,1),v.astype(np.float32).reshape(-1,1),cv2.INTER_LINEAR).ravel(),15.0)
        prior=np.concatenate([(x[:3]-x0[:3])/3.0,(x[3:6]-x0[3:6])/np.radians(2),[(x[6]-x0[6])/0.05,(x[7]-x0[7])/80,(x[8]-x0[8])/80]])
        return np.concatenate([np.minimum(d,15.0),prior,ptres(x)*np.sqrt(len(P)/max(len(obs),1))*0.5])
    r0=res(x0)[:len(P)]
    s=least_squares(res,x0,loss='soft_l1',f_scale=3.0,diff_step=1e-4,max_nfev=300)
    r1=res(s.x)[:len(P)]
    print(k,'pts rms %.1f'%np.sqrt(np.mean(ptres(s.x)**2*2.25)),'median edge dist %.2f -> %.2f px'%(np.median(r0),np.median(r1)),'dpos',np.round(s.x[:3]-x0[:3],2),'drot deg',np.round(np.degrees(s.x[3:6]-x0[3:6]),2),'f %.0f->%.0f'%(np.exp(x0[6]),np.exp(s.x[6])),'pp',np.round(s.x[7:9]-x0[7:9],1))
    x=s.x; out[k]=dict(c,pos=list(x[:3]),R=Rm(*x[3:6]).tolist(),f=float(np.exp(x[6])),cx=float(x[7]),cy=float(x[8]))
json.dump(out,open('cams_edge2.json','w'),indent=1)
