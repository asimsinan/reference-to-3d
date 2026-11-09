"""The photo's camera (solved by solve_cam.py) and the holder frame.
Object frame: +X front (towards the camera), +Y the holder's left (= image right), +Z up, metres, base centre at 0.
Camera at C=(D,YC,HC), looking along -X pitched down by TH, rolled by RO about its axis; focal F px, principal point (CX,CY)."""
import json, os, numpy as np
W,H=1500,2000; CX,CY=750.0,1000.0
_p=os.path.join(os.getcwd(),'cam.json')
P=json.load(open(_p)) if os.path.exists(_p) else {}
def axes(th,ro=0.0):
    f=np.array([-np.cos(th),0,-np.sin(th)]); r=np.array([0,1.0,0]); up=np.cross(r,f)
    r2=np.cos(ro)*r+np.sin(ro)*up; up2=-np.sin(ro)*r+np.cos(ro)*up; return f,r2,up2
def proj(X,p=None):
    p=p or P; X=np.asarray(X,float); C=np.array([p['D'],p['YC'],p['HC']]); f,r,up=axes(p['TH'],p.get('RO',0.0))
    q=X-C; d=q@f; return np.stack([CX+p['F']*(q@r)/d, CY-p['F']*(q@up)/d],-1)
def ray(u,v,p=None):
    """camera centre and unit direction of pixel (u,v)"""
    p=p or P; C=np.array([p['D'],p['YC'],p['HC']]); f,r,up=axes(p['TH'],p.get('RO',0.0))
    d=f[None]+((np.asarray(u,float)-CX)/p['F'])[:,None]*r[None]-((np.asarray(v,float)-CY)/p['F'])[:,None]*up[None]
    return C,d/np.linalg.norm(d,axis=1,keepdims=True)
def unproj_plane_x0(u,v,p=None):
    C,d=ray(np.atleast_1d(u),np.atleast_1d(v),p); t=-C[0]/d[:,0]; return C[None]+t[:,None]*d
