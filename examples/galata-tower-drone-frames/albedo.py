import os; os.environ['OPENCV_IO_ENABLE_OPENEXR']='1'
import cv2,numpy as np
from scipy.spatial import cKDTree
def lin(c): return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
def srgb(c): return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.maximum(c,1e-9),1/2.4)-0.055)
for n in open('bake/names.txt').read().split():
    pq='tex/%s_q.png'%n; ph=lin(cv2.imread(pq if os.path.exists(pq) else 'tex/%s_photo.png'%n).astype(np.float32)/255.)   # material: the crisp synthesis
    Er=cv2.imread('tex/%s_irr.exr'%n,cv2.IMREAD_UNCHANGED); E=Er[...,:3].astype(np.float32)
    E=cv2.resize(cv2.GaussianBlur(E,(0,0),1.0),(ph.shape[1],ph.shape[0]),interpolation=cv2.INTER_LINEAR)
    A=cv2.resize((Er[...,3]>0.5).astype(np.uint8),(ph.shape[1],ph.shape[0]),interpolation=cv2.INTER_NEAREST)>0
    a=ph/np.maximum(E,0.08); a=np.clip(a,0.002,0.92)
    Pm=cv2.imread('bake/%s_P.exr'%n,cv2.IMREAD_UNCHANGED); Nm=cv2.imread('bake/%s_N.exr'%n,cv2.IMREAD_UNCHANGED)
    X,Y,Z=Pm[...,2],Pm[...,1],Pm[...,0]; nx,ny,nz=Nm[...,2],Nm[...,1],Nm[...,0]; R=np.hypot(X,Y)
    if n=='upper':   # the wall behind the railing and the people: mirror the clean wall above the railing's top down
        zt=9.9; wall=A&(np.abs(R-7.3)<0.04)&(np.abs(nz)<0.3)
        src=wall&(Z>zt)&(Z<zt+2.4); dst=wall&(Z<=zt)
        tr=cKDTree(np.stack([X[src],Y[src],Z[src]],1)); q=np.stack([X[dst],Y[dst],np.minimum(2*zt-Z[dst],zt+2.35)],1)
        _,ii=tr.query(q); a[dst]=a[src][ii]
    if n=='balcony':  # walkway floor: people and railing shadows removed by a large median
        fl=A&(nz>0.9)
        med=cv2.medianBlur((np.clip(srgb(a),0,1)*255).astype(np.uint8),21); a[fl]=lin(med[fl].astype(np.float32)/255.)
    if n in ('arcade','upper'):
        seenw=cv2.resize(cv2.imread('tex/%s_seen.png'%n,0),(ph.shape[1],ph.shape[0]))/255.
        ro=7.3 if n=='upper' else 8.25
        inner=A&(R<ro-0.03)
        st=A&(R>ro-0.01)&(seenw>0.3)                                   # well-seen outer stone
        base=np.median(a[st],0)
        # stone pattern: the shaft's own albedo divided by its blur (photo-derived), at this texture's scale
        sh=lin(cv2.imread('tex/shaft_alb.png').astype(np.float32)/255.); pat=sh/np.maximum(cv2.GaussianBlur(sh,(0,0),12),1e-3)
        pat=cv2.resize(pat,(ph.shape[1],ph.shape[0]))
        if n=='arcade':
            back=inner&(R<ro-0.35-0.2)&(np.abs(nz)<0.5)                     # the windows' back plane: dark glazing
            reveal=inner&~back&(seenw<0.35)
            a[reveal]=np.clip(base*0.85*pat[reveal],0.003,0.9); a[back&(seenw<0.35)]=0.02
        else:
            sill=inner&(nz>0.8); dark=inner&~sill
            a[dark]=np.where(seenw[dark][:,None]>0.5,np.minimum(a[dark],0.05),0.025); a[sill]=np.clip(base*pat[sill],0.003,0.9)
    if n=='shaft':   # light left in the photos across the angle (a soft sun on the west side in r2/r3): flatten it per row
        L=a.mean(2)
        Lb=cv2.GaussianBlur(np.hstack([L,L,L]),(0,0),sigmaX=140,sigmaY=30)[:,L.shape[1]:2*L.shape[1]]
        W_=L.shape[1]; gc=slice(int(720*W_/2048),int(1180*W_/2048)); target=np.median(Lb[:,gc],1,keepdims=True)   # the best-seen angles (the quilting sources)
        fac=np.clip(target/np.maximum(Lb,1e-4),0.75,1.35); a=np.clip(a*fac[...,None],0.002,0.92)
        print('  shaft: angle-wise light flattened, factor p5-p95 %.2f-%.2f'%tuple(np.percentile(fac,[5,95])))
    cv2.imwrite('tex/%s_alb.png'%n,(np.clip(srgb(a),0,1)*255+0.5).astype(np.uint8))
    print(n,'median albedo (rgb)',np.round(np.median(a[A][:,::-1],0),3),'E median',np.round(np.median(E[A]),3))
