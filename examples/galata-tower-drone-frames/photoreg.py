# refine cameras of r2/r3 (and r1 optional) by photometric alignment to the texture (built mostly from r4)
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2,numpy as np,json,sys
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
cams=json.load(open('cams.json')); GAIN=json.load(open('gain.json'))
PARTS=['shaft','cornice','arcade','upper','roof','balcony']
FR=sys.argv[1:] or ['r2','r3']
rng=np.random.default_rng(0)
data={}
for name in PARTS:
    Pm=cv2.imread('bake/%s_P.exr'%name,cv2.IMREAD_UNCHANGED); Nm=cv2.imread('bake/%s_N.exr'%name,cv2.IMREAD_UNCHANGED)
    T=cv2.imread('tex/%s_photo.png'%name).astype(np.float32); S=cv2.imread('tex/%s_seen.png'%name,0)
    gx=cv2.Sobel(cv2.GaussianBlur(T.mean(2),(0,0),1.5),cv2.CV_32F,1,0); gy=cv2.Sobel(cv2.GaussianBlur(T.mean(2),(0,0),1.5),cv2.CV_32F,0,1)
    A=(Pm[...,3]>0.5)&(S>60)
    data[name]=(Pm[...,[2,1,0]][A],Nm[...,[2,1,0]][A],cv2.GaussianBlur(T,(0,0),1.5)[A],np.hypot(gx,gy)[A])
P=np.concatenate([d[0] for d in data.values()]); N=np.concatenate([d[1] for d in data.values()]); T=np.concatenate([d[2] for d in data.values()]); G=np.concatenate([d[3] for d in data.values()])
out=dict(cams)
for k in FR:
    c=cams[k]; R0=np.array(c['R']); C0=np.array(c['pos']); f0=c['f']; im=cv2.GaussianBlur(cv2.imread('ref/%s.png'%k).astype(np.float32),(0,0),0.8)
    d=cv2.imread('bake/depth_%s.exr'%k,cv2.IMREAD_UNCHANGED); dz=d[...,2].copy(); dz[d[...,3]<0.5]=1e4; H,W=dz.shape
    pc=(P-C0)@R0.T; z=pc[:,2]; u=f0*pc[:,0]/z+c['cx']; v=f0*pc[:,1]/z+c['cy']
    ok=(u>2)&(u<W-3)&(v>2)&(v<H-3)
    ui=np.clip(u.astype(int),0,W-1); vi=np.clip(v.astype(int),0,H-1)
    view=C0-P; view/=np.linalg.norm(view,axis=1,keepdims=True); cs=(N*view).sum(1)
    ok&=(np.abs(dz[vi,ui]-z)<0.2)&(cs>0.3)
    idx=np.nonzero(ok)[0]; pr=G[idx]/G[idx].sum(); sel=rng.choice(idx,size=min(40000,len(idx)),replace=False,p=pr)
    Ps=P[sel]; Ts=T[sel]; g=np.array(GAIN[k],np.float32)
    def proj(x):
        R=Rotation.from_rotvec(x[3:6]).as_matrix()@R0; C=C0+x[:3]; f=f0*np.exp(x[6])
        q=(Ps-C)@R.T; return f*q[:,0]/q[:,2]+c['cx']+x[7], f*q[:,1]/q[:,2]+c['cy']+x[8], R, C, f
    def res(x):
        uu,vv,*_=proj(x); n=len(uu); m=200; pad=(-n)%m; U=np.pad(uu,(0,pad)).reshape(-1,m).astype(np.float32); V=np.pad(vv,(0,pad)).reshape(-1,m).astype(np.float32)
        s=cv2.remap(im,U,V,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).reshape(-1,3)[:n]*g
        return np.concatenate([((s-Ts)/20).ravel(),x[:3]/0.5,x[3:6]/0.01,[x[6]/0.05,x[7]/20,x[8]/20]])
    x0=np.zeros(9); r0=res(x0); s=least_squares(res,x0,loss='soft_l1',f_scale=1.5,diff_step=1e-3,max_nfev=200)
    uu0,vv0,*_=proj(x0); uu,vv,R,C,f=proj(s.x)
    print(k,'cost %.0f -> %.0f'%(np.abs(r0[:-9]).mean()*20,np.abs(s.fun[:-9]).mean()*20),'shift px %.2f'%np.hypot(uu-uu0,vv-vv0).mean(),'dpos',np.round(s.x[:3],2),'drot deg',np.round(np.degrees(s.x[3:6]),3),'df %.3f'%s.x[6])
    out[k]=dict(c,pos=C.tolist(),R=R.tolist(),f=float(f),cx=c['cx']+float(s.x[7]),cy=c['cy']+float(s.x[8]))
json.dump(out,open('cams_reg.json','w'),indent=1)
