import numpy as np
from obs import SZ
GN=['z_tip','z_ball','z_apex','tana','r_e','z_e','r_b','z_b','r_c','r_s0','taper']
# z = 0 at the bottom of the lower cornice (gauge); r_s0 = shaft radius just under it (scale, fixed)
def Rm(yaw,pitch,roll):
    cy,sy,cp,sp=np.cos(yaw),np.sin(yaw),np.cos(pitch),np.sin(pitch)
    fwd=np.array([cy*cp,sy*cp,-sp]); right=np.array([sy,-cy,0.0]); down=np.cross(fwd,right)
    R=np.stack([right,down,fwd]); cr,sr=np.cos(roll),np.sin(roll)
    return np.array([[cr,-sr,0],[sr,cr,0],[0,0,1]])@R
class Cam:
    def __init__(s,k,c):  # c: d,h,yaw,pitch,roll,logf,dcx,dcy, az(world azimuth of camera)
        s.k=k; d,h,yaw,pitch,roll,lf,dcx,dcy=c[:8]; az=c[8] if len(c)>8 else 0.0
        ca,sa=np.cos(az),np.sin(az)
        s.pos=np.array([d*ca,d*sa,h]); s.R=Rm(az+np.pi+yaw,pitch,roll); s.f=np.exp(lf)
        W,H=SZ[k]; s.cx=W/2+dcx; s.cy=H/2+dcy; s.W,s.H=W,H
    def proj(s,P):
        q=(np.atleast_2d(P)-s.pos)@s.R.T
        return np.stack([s.f*q[:,0]/q[:,2]+s.cx,s.f*q[:,1]/q[:,2]+s.cy],1)
    def dict(s):
        return {'pos':s.pos.tolist(),'R':s.R.tolist(),'f':float(s.f),'cx':float(s.cx),'cy':float(s.cy),'W':s.W,'H':s.H}
TH=np.linspace(0,2*np.pi,1440,endpoint=False)
def ring(r,z): return np.stack([r*np.cos(TH),r*np.sin(TH),np.full_like(TH,z)],1)
def ring_feats(cam,r,z):
    p=cam.proj(ring(r,z)); 
    # front point = the one nearest the camera (azimuth of camera)
    d=np.linalg.norm(ring(r,z)-cam.pos,axis=1); i=np.argmin(d)
    return p[:,0].min(),p[:,0].max(),p[i]
def sil_x(cam,rfun,z0,z1,y,side,n=80):
    zs=np.linspace(z0,z1,n); th=TH
    rs=np.array([rfun(z) for z in zs])
    P=np.stack([rs[:,None]*np.cos(th)[None],rs[:,None]*np.sin(th)[None],np.repeat(zs[:,None],len(th),1)],2).reshape(-1,3)
    p=cam.proj(P).reshape(n,len(th),2)
    j=np.argmin(p[...,0],1) if side=='L' else np.argmax(p[...,0],1)
    xs=p[np.arange(n),j,0]; ys=p[np.arange(n),j,1]; o=np.argsort(ys)
    return np.interp(y,ys[o],xs[o])
