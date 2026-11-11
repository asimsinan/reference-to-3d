"""photoreg.py -- refine all photo cameras jointly so that the same surface point looks the same in every photo
(local-contrast-normalised grey images, robust to the photos' different light), hand points kept as soft residuals."""
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2, json, numpy as np, sys
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
J=json.load(open('cams.json')); ks=sorted(J['cams']); SZ=J['sizes']
objs=['side_lower_L','side_lower_R','side_upper_L','side_upper_R','dash_F','cab_F','fender_F','bumper_F','roof','headlamp_F','bolt_F1','bolt_F0','sign_F','signtab_F','siglamp_F1','siglamp_F0','solebar_L','glass_cab_F','gate_FL','gate_FR','mirror_F','monitor']
SIG=float(sys.argv[1]) if len(sys.argv)>1 else 2.0
def struct(k):
    g=cv2.cvtColor(cv2.imread(f'ref/p{k}.png'),cv2.COLOR_BGR2GRAY).astype(np.float32)
    m=cv2.GaussianBlur(g,(0,0),6); s=np.sqrt(cv2.GaussianBlur((g-m)**2,(0,0),6))+6
    return cv2.GaussianBlur((g-m)/s,(0,0),SIG)
S={k:struct(k) for k in ks}
DEP={}
for k in ks:
    d=cv2.imread(f'bake/depth{k}.exr',cv2.IMREAD_UNCHANGED); z=d[...,2].copy(); z[d[...,3]<0.5]=1e9; DEP[k]=z
occ=json.load(open('occ.json')); OCC={}
for k in ks:
    m=np.zeros(S[k].shape,np.uint8)
    for p in occ.get(k,[]): cv2.fillPoly(m,[np.array(p,np.int32)],1)
    OCC[k]=cv2.dilate(m,np.ones((9,9),np.uint8))>0
Ps=[];Ns=[]
rs=np.random.RandomState(0)
for o in objs:
    Pi=cv2.imread(f'bake/{o}_P.exr',cv2.IMREAD_UNCHANGED); Ni=cv2.imread(f'bake/{o}_N.exr',cv2.IMREAD_UNCHANGED)
    v=(Pi[...,3]>0.5)&(np.abs(Pi[...,:3]).sum(-1)>0); P=Pi[...,2::-1][v]; N=Ni[...,2::-1][v]
    sel=rs.choice(len(P),min(len(P),12000),replace=False); Ps.append(P[sel]); Ns.append(N[sel])
P=np.concatenate(Ps).astype(np.float64); N=np.concatenate(Ns).astype(np.float64); N/=np.linalg.norm(N,axis=1,keepdims=True)
def project(c,k,X):
    R=Rot.from_rotvec(c[:3]).as_matrix(); Xc=(X-c[3:6])@R.T; z=Xc[:,2]
    return np.stack([c[6]*Xc[:,0]/z+c[7], c[6]*Xc[:,1]/z+c[8]],1), z
# visibility with the initial cameras
VIS={}
for k in ks:
    c=np.array(J['cams'][k]); uv,z=project(c,k,P); W,H=SZ[k]
    ok=(z>0.1)&(uv[:,0]>5)&(uv[:,1]>5)&(uv[:,0]<W-6)&(uv[:,1]<H-6)
    ui=np.clip(uv[:,0].astype(int),0,W-1); vi=np.clip(uv[:,1].astype(int),0,H-1)
    ok&=np.abs(DEP[k][vi,ui]-z)<0.02+0.003*z; ok&=~OCC[k][vi,ui]
    cs=(N*((c[3:6]-P)/np.linalg.norm(c[3:6]-P,axis=1,keepdims=True))).sum(1); ok&=cs>0.25
    VIS[k]=ok
cnt=np.sum([VIS[k] for k in ks],0); use=cnt>=2
# keep textured points: structure magnitude in the best view
print('points',use.sum())
def samp(img,uv):
    H,W=img.shape; x=np.clip(uv[:,0],0,W-1.001); y=np.clip(uv[:,1],0,H-1.001); x0=x.astype(int); y0=y.astype(int); fx=x-x0; fy=y-y0
    return img[y0,x0]*(1-fx)*(1-fy)+img[y0,x0+1]*fx*(1-fy)+img[y0+1,x0]*(1-fx)*fy+img[y0+1,x0+1]*fx*fy
PU=P[use]; V={k:VIS[k][use] for k in ks}
pts=json.load(open('pts.json'))
import importlib.util
spec=importlib.util.spec_from_file_location('sv','solve.py')
src=open('solve.py').read().split('# init each camera')[0]
ns={}; exec(src.replace("RAILS=json.load(open('rails.json')) if os.environ.get('RAILS') else {}","RAILS={}"),ns)
m=J['model']
def unpack(x): return {k:x[9*i:9*i+9] for i,k in enumerate(ks)}
x0=np.concatenate([np.array(J['cams'][k],float) for k in ks])
def resid(x):
    cs=unpack(x); vals={}
    for k in ks:
        uv,_=project(cs[k],k,PU); vals[k]=samp(S[k],uv)
    r=[]
    stack=np.stack([np.where(V[k],vals[k],np.nan) for k in ks]); mean=np.nanmean(stack,0)
    for k in ks: r.append(np.where(V[k],vals[k]-mean,0.0))
    # hand points (soft, 2 px sigma)
    for k in ks:
        d=ns['pts3'](m,ns['SIDE'][k]); names=[n for n in pts[k] if n in d]
        X=np.array([d[n] for n in names]); uv,_=project(cs[k],k,X); r.append(((uv-np.array([pts[k][n] for n in names]))/2.0).ravel()*3)
    return np.concatenate(r)
r0=resid(x0); print('start cost',round(float((r0**2).sum()),1))
sol=least_squares(resid,x0,loss='soft_l1',f_scale=0.5,diff_step=1e-4,x_scale='jac',max_nfev=60)
r1=resid(sol.x); print('end cost',round(float((r1**2).sum()),1))
cs=unpack(sol.x)
for k in ks:
    uv0,_=project(np.array(J['cams'][k]),k,PU); uv1,_=project(cs[k],k,PU); print(k,'mean shift px',round(float(np.linalg.norm(uv1-uv0,axis=1).mean()),2),'f',round(J['cams'][k][6]),'->',round(cs[k][6]))
    J['cams'][k]=[float(v) for v in cs[k]]
json.dump(J,open('cams.json','w'),indent=1)
