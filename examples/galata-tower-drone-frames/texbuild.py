# project photos onto every part's texels -> tex/<part>_photo.png, tex/<part>_seen.png ; unseen texels from the same part rotated by its period
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2, numpy as np, json, sys
cams=json.load(open('cams.json')); os.makedirs('tex',exist_ok=True)
USE=['r2','r3','r4']
GAIN=json.load(open('gain.json')) if os.path.exists('gain.json') else {}
IGN=json.load(open('ignore.json')) if os.path.exists('ignore.json') else {}
PER={'roof':90.0,'dormers':90.0}; DEF=360/14
from quilt import quilt
TH0=json.load(open('params.json'))['th0']
QUILT=('shaft','roof')
BAY={'cornice':(360/14,180/14),'balcony':(360/14,180/14),'arcade':(360/14,180/14),'upper':(360/14,180/14),'posts':(360/14,0.0),'dormers':(90.0,45.0)}
ph={}; dp={}
for k in USE:
    im=cv2.imread('ref/%s.png'%k).astype(np.float32); ok=np.ones(im.shape[:2],np.float32)
    for poly in IGN.get(k,[]): cv2.fillPoly(ok,[np.array(poly,np.int32)],0)
    d=cv2.imread('bake/depth_%s.exr'%k,cv2.IMREAD_UNCHANGED); dz=d[...,2].copy(); dz[d[...,3]<0.5]=1e4
    edge=(cv2.dilate(dz,np.ones((3,3),np.uint8))-cv2.erode(dz,np.ones((3,3),np.uint8)))>0.6
    ok[edge]=0; ph[k]=(im,ok); dp[k]=dz
def fill(img,m):
    out=img.copy(); m=m.copy()
    for sig in (1.5,3,6,12,24,48,96,200):
        mm=m.astype(np.float32); num=cv2.GaussianBlur(out*mm[...,None],(0,0),sig); den=cv2.GaussianBlur(mm,(0,0),sig)
        new=(den>0.02)&~m; out[new]=(num/np.maximum(den,1e-6)[...,None])[new]; m|=new
    return out
def project(Pw,Nw,A,hh,ww):
    acc=np.zeros((len(Pw),3),np.float32); wsum=np.zeros(len(Pw),np.float32); best=np.zeros(len(Pw),np.float32); per={}; cmax=np.zeros(len(Pw),np.float32)
    for k in USE:
        c=cams[k]; R=np.array(c['R']); C=np.array(c['pos']); f=c['f']; im,okm=ph[k]; H,W=im.shape[:2]
        pc=(Pw-C)@R.T; z=pc[:,2]; u=f*pc[:,0]/z+c['cx']; v=f*pc[:,1]/z+c['cy']
        ok=A&(z>1)&(u>=1)&(u<W-2)&(v>=1)&(v<H-2)
        ui=np.clip(np.round(u).astype(int),0,W-1); vi=np.clip(np.round(v).astype(int),0,H-1)
        vis=ok&(np.abs(dp[k][vi,ui]-z)<0.25)&(okm[vi,ui]>0.5)
        view=C-Pw; view/=np.linalg.norm(view,axis=1,keepdims=True); cs=np.sum(Nw*view,1)
        res=(f/np.maximum(z,1))**2; w=np.where(vis&(cs>0.1),cs,0.0)**2*res/400.0
        col=cv2.remap(im,u.reshape(hh,ww).astype(np.float32),v.reshape(hh,ww).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).reshape(-1,3)
        col=col*np.array(GAIN.get(k,[1,1,1]),np.float32); per[k]=(col,w)
        w8=(w**6).astype(np.float32); acc+=col*w8[:,None]; wsum+=w8; best=np.maximum(best,np.minimum(w,1)); cmax=np.maximum(cmax,np.where(vis,cs,0))
    return acc,wsum,best,per,cmax
def rot(V,deg):
    t=np.radians(deg); c,s=np.cos(t),np.sin(t); return np.stack([c*V[:,0]-s*V[:,1],s*V[:,0]+c*V[:,1],V[:,2]],1)
only=[a for a in sys.argv[1:] if a!='gains']; SOLVE='gains' in sys.argv; pairs={}
for name in open('bake/names.txt').read().split():
    if only and name not in only: continue
    Pm=cv2.imread('bake/%s_P.exr'%name,cv2.IMREAD_UNCHANGED); Nm=cv2.imread('bake/%s_N.exr'%name,cv2.IMREAD_UNCHANGED)
    A=(Pm[...,3]>0.5).reshape(-1); Pw=Pm[...,[2,1,0]].reshape(-1,3).astype(np.float64); A&=np.abs(Pw).sum(1)>1e-3; Nw=Nm[...,[2,1,0]].reshape(-1,3).astype(np.float64)
    Nw/=np.linalg.norm(Nw,axis=1,keepdims=True)+1e-9; hh,ww=Pm.shape[:2]
    acc,wsum,best,per,cmax=project(Pw,Nw,A,hh,ww)
    if SOLVE:
        ks=list(per)
        for i in range(len(ks)):
            for j in range(i+1,len(ks)):
                ca,wa=per[ks[i]]; cb,wb=per[ks[j]]; m=(wa>0.25)&(wb>0.25)&(ca.max(1)<240)&(cb.max(1)<240)&(ca.min(1)>12)&(cb.min(1)>12)
                if m.sum()>300: pairs.setdefault((ks[i],ks[j]),[]).append(np.log(ca[m]+1)-np.log(cb[m]+1))
        continue
    seen=wsum>1e-9; out=np.zeros_like(acc); out[seen]=acc[seen]/wsum[seen,None]; src=seen.copy()
    if name in QUILT:
        T0=fill(out.reshape(hh,ww,3).copy(),seen.reshape(hh,ww)); gsrc=seen&(cmax>0.7)
        kw=dict(log=lambda m: print('  ',name,m),exclude=[(1190,1232)] if name=='shaft' else [],Gsrc=gsrc.reshape(hh,ww),
                win_rows=(290,410) if name=='shaft' else None,win_gap=30.0 if name=='shaft' else 0.0)
        # material version: only the crisp core of the photos is kept, the rest is synthesised from it
        qm,_=quilt(T0,(seen&(cmax>0.68)).reshape(hh,ww),A.reshape(hh,ww),**kw)
        cv2.imwrite('tex/%s_q.png'%name,np.clip(fill(qm,np.ones((hh,ww),bool)),0,255).astype(np.uint8))
        # photo version: every texel a frame sees (even at a slant) keeps the photo, only the unseen side is synthesised
        q,G=quilt(T0,(seen&(cmax>0.4)).reshape(hh,ww),A.reshape(hh,ww),**kw)
        out=q.reshape(-1,3); seen=G.reshape(-1)|~A
    elif name in BAY:
        P_,off=BAY[name]; th=np.degrees(np.arctan2(Pw[:,1],Pw[:,0])); b=np.floor((th-TH0+off)/P_).astype(int)%int(round(360/P_))
        nb=int(round(360/P_)); q=np.array([cmax[A&(b==k)].mean() if (A&(b==k)).any() else 0 for k in range(nb)])
        order=np.argsort(-q); bestb=[int(k) for k in order[:3] if q[k]>=0.8*q[order[0]]]
        own=q>=0.3
        need=A&((~own[b])|(wsum<1e-9)|(cmax<0.3))
        need&=~np.isin(b,bestb)|(wsum<1e-9)
        for k in range(nb):
            sel=need&(b==k)
            if not sel.any(): continue
            for sb in sorted(bestb,key=lambda x: abs(((x-k+nb//2)%nb)-nb//2)):
                if sb==k: continue
                d=(sb-k)*P_; a2,w2,_,_,_=project(rot(Pw,d),rot(Nw,d),sel,hh,ww)
                got=sel&(w2>1e-6); out[got]=a2[got]/w2[got,None]; wsum[got]=w2[got]; seen|=got; sel&=~got
                if not sel.any(): break
        print('  ',name,'bays',nb,'quality',np.round(q,2),'sources',bestb)
    p=PER.get(name,DEF)
    for kk in ([] if name in QUILT else [1,-1,2,-2,3,-3,4,-4,5,-5,6,-6,7,-7]):
        need=A&(wsum<1e-4)
        if need.sum()==0: break
        a2,w2,_,_,_=project(rot(Pw,kk*p),rot(Nw,kk*p),need,hh,ww)
        got=need&(w2>1e-6); out[got]=a2[got]/w2[got,None]; wsum[got]=w2[got]; seen|=got
    out=fill(out.reshape(hh,ww,3),seen.reshape(hh,ww))
    cv2.imwrite('tex/%s_photo.png'%name,np.clip(out,0,255).astype(np.uint8)); cv2.imwrite('tex/%s_seen.png'%name,(np.clip(best.reshape(hh,ww),0,1)*255).astype(np.uint8))
    print(name,'direct %.0f%%  filled %.0f%%'%(100*src[A].mean(),100*seen[A].mean()))
if SOLVE:
    ks=USE; idx={k:i for i,k in enumerate(ks)}; rows=[]; rhs=[]; wts=[]
    for (a,b),l in pairs.items():
        d=np.concatenate(l); r=np.zeros(len(ks)); r[idx[a]]=1; r[idx[b]]=-1
        rows.append(-r); rhs.append(np.median(d,0)); wts.append(np.sqrt(len(d))); print(a,b,len(d),np.round(np.exp(np.median(d,0)),3))
    r=np.zeros(len(ks)); r[idx['r3']]=1; rows.append(r*1e3); rhs.append(np.zeros(3)); wts.append(1.0)
    g=np.linalg.lstsq(np.array(rows)*np.array(wts)[:,None],np.array(rhs)*np.array(wts)[:,None],rcond=None)[0]
    out={k:[float(v) for v in np.exp(g[idx[k]])*np.array(GAIN.get(k,[1,1,1]))] for k in ks}; json.dump(out,open('gain.json','w'),indent=1); print(out)
