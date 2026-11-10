# project the six photos onto every part's texels: tex/<part>_photo.png (best-view blend), tex/<part>_seen.png
import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2, numpy as np, json, sys
cams=json.load(open('cams.json')); os.makedirs('tex',exist_ok=True)
GAIN=json.load(open('gain.json')) if os.path.exists('gain.json') else {}
IGN=json.load(open('ignore.json')) if os.path.exists('ignore.json') else {}
ph={}; dp={}
for k,c in cams.items():
    im=cv2.imread('ref/%s.png'%k).astype(np.float32)
    ok=np.ones(im.shape[:2],np.float32)
    for poly in IGN.get(k,[]): cv2.fillPoly(ok,[np.array(poly,np.int32)],0)
    d=cv2.imread('bake/depth_%s.exr'%k,cv2.IMREAD_UNCHANGED); dz=d[...,2].copy(); dz[d[...,3]<0.5]=1e4
    ker=np.ones((7,7),np.uint8); edge=(cv2.dilate(dz,ker)-cv2.erode(dz,ker))>1.2
    ok[edge]=0; ph[k]=(im,ok); dp[k]=d[...,2]
def fill(img,m):
    out=img.copy(); m=m.copy()
    for sig in (1.5,3,6,12,24,48,96,200):
        mm=m.astype(np.float32); num=cv2.GaussianBlur(out*mm[...,None],(0,0),sig); den=cv2.GaussianBlur(mm,(0,0),sig)
        new=(den>0.02)&~m; out[new]=(num/np.maximum(den,1e-6)[...,None])[new]; m|=new
    return out
only=[a for a in sys.argv[1:] if a!='gains']
SOLVE='gains' in sys.argv; pairs={}
for name in open('bake/names.txt').read().split():
    if only and name not in only: continue
    Pm=cv2.imread('bake/%s_P.exr'%name,cv2.IMREAD_UNCHANGED); Nm=cv2.imread('bake/%s_N.exr'%name,cv2.IMREAD_UNCHANGED)
    A=Pm[...,3]>0.5; Pw=Pm[...,[2,1,0]].reshape(-1,3).astype(np.float64); Nw=Nm[...,[2,1,0]].reshape(-1,3).astype(np.float64)
    Nw/=np.linalg.norm(Nw,axis=1,keepdims=True)+1e-9; hh,ww=A.shape
    acc=np.zeros((hh*ww,3),np.float32); wsum=np.zeros(hh*ww,np.float32); best=np.zeros(hh*ww,np.float32); per={}
    for k,c in cams.items():
        R=np.array(c['R']); C=np.array(c['pos']); f=c['f']; im,okm=ph[k]; H,W=im.shape[:2]
        pc=(Pw-C)@R.T; z=pc[:,2]; u=f*pc[:,0]/z+c['cx']; v=f*pc[:,1]/z+c['cy']
        ok=A.reshape(-1)&(z>1)&(u>=1)&(u<W-2)&(v>=1)&(v<H-2)
        ui=np.clip(np.round(u).astype(int),0,W-1); vi=np.clip(np.round(v).astype(int),0,H-1)
        vis=ok&(np.abs(dp[k][vi,ui]-z)<0.35)&(okm[vi,ui]>0.5)
        view=C-Pw; view/=np.linalg.norm(view,axis=1,keepdims=True); cs=np.sum(Nw*view,1)
        w=np.where(vis&(cs>0.12),cs,0.0)**2*GAIN.get(k,{}).get('w',1.0)
        col=cv2.remap(im,u.reshape(hh,ww).astype(np.float32),v.reshape(hh,ww).astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE).reshape(-1,3)
        col=col*np.array(GAIN.get(k,{}).get('g',[1,1,1]),np.float32)
        per[k]=(col,w)
        w8=(w**6).astype(np.float32); acc+=col*w8[:,None]; wsum+=w8; best=np.maximum(best,w)
    if SOLVE:
        ks=list(per)
        for i in range(len(ks)):
            for j in range(i+1,len(ks)):
                ca,wa=per[ks[i]]; cb,wb=per[ks[j]]; m=(wa>0.15)&(wb>0.15)&(ca.max(1)<235)&(cb.max(1)<235)&(ca.min(1)>12)&(cb.min(1)>12)
                if m.sum()>300: pairs.setdefault((ks[i],ks[j]),[]).append((np.log(ca[m]+1)-np.log(cb[m]+1)))
        continue
    seen=wsum>1e-12; out=np.zeros_like(acc); out[seen]=acc[seen]/wsum[seen,None]
    out=out.reshape(hh,ww,3); seen=seen.reshape(hh,ww)
    out=fill(out,seen)
    cv2.imwrite('tex/%s_photo.png'%name,np.clip(out,0,255).astype(np.uint8)); cv2.imwrite('tex/%s_seen.png'%name,(np.clip(best.reshape(hh,ww),0,1)*255).astype(np.uint8))
    print(name,'seen %.0f%%'%(100*seen[A].mean()))

if SOLVE:
    ks=sorted(cams); idx={k:i for i,k in enumerate(ks)}; rows=[]; rhs=[]; wts=[]
    for (a,b),l in pairs.items():
        d=np.concatenate(l); r=np.zeros(len(ks)); r[idx[a]]=1; r[idx[b]]=-1   # log ca - log cb = gb - ga
        rows.append(-r); rhs.append(np.median(d,0)); wts.append(np.sqrt(len(d))); print(a,b,len(d),np.round(np.exp(np.median(d,0)),2))
    r=np.zeros(len(ks)); r[idx['r5']]=1; rows.append(r*1e3); rhs.append(np.zeros(3)); wts.append(1.0)
    Am=np.array(rows)*np.array(wts)[:,None]; B=np.array(rhs)*np.array(wts)[:,None]
    g=np.linalg.lstsq(Am,B,rcond=None)[0]
    old=GAIN; out={k:{'g':[float(v) for v in np.exp(g[idx[k]])*np.array(old.get(k,{}).get('g',[1,1,1]))],'w':old.get(k,{}).get('w',1.0)} for k in ks}
    json.dump(out,open('gain.json','w'),indent=1); print(json.dumps(out))
