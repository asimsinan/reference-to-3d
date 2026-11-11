import json,numpy as np,cv2
from invert import CC,C
g=json.load(open('solve.json'))['g']
def unwrap(k,z0=-35.4,z1=0,dz=0.05,dth=0.5,rfun=None,az=0.0):
    c=CC(C[k]) if az==0.0 else CC(C[k]); im=cv2.imread('ref/%s.png'%k).astype(np.float32)
    th=np.radians(np.arange(0,360,dth)); zs=np.arange(z1,z0,-dz)
    T,Z=np.meshgrid(th,zs); R=rfun(Z) if rfun else g['r_s0']-g['taper']*Z
    P=np.stack([R*np.cos(T),R*np.sin(T),Z],-1).reshape(-1,3)
    N=np.stack([np.cos(T),np.sin(T),np.zeros_like(T)],-1).reshape(-1,3)
    p=c.proj(P); v=c.pos-P; v/=np.linalg.norm(v,axis=1,keepdims=True); cs=(N*v).sum(1)
    ok=(cs>0.2)&(p[:,0]>=0)&(p[:,0]<C[k]['W']-1)&(p[:,1]>=0)&(p[:,1]<C[k]['H']-1)
    out=cv2.remap(im,p[:,0].reshape(T.shape).astype(np.float32),p[:,1].reshape(T.shape).astype(np.float32),cv2.INTER_LINEAR)
    w=np.where(ok,cs,0).reshape(T.shape); return out,w
if __name__=='__main__':
    rows=[]
    for k in ['r1','r2','r3','r4']:
        o,w=unwrap(k); o[w<=0]=(255,0,255); rows.append(o)
        np.save('out/uw_%s.npy'%k,np.dstack([o,w[...,None]]))
    cv2.imwrite('out/unwrap_shaft.jpg',np.vstack([np.hstack([r,np.zeros((r.shape[0],4,3))]) for r in rows]))
