"""The photo's camera (solve2.py writes cam.json). Object frame: +X towards the camera, +Y image-right, +Z up, metres,
base centre at 0. Camera at (D,YC,HC), looking along -X pitched down by TH, rolled by PSI; focal F px, principal point (CX,CY)."""
import json, os, numpy as np
W,H=1500,2000
_p=os.path.join(os.getcwd(),'cam.json')
P=json.load(open(_p)) if os.path.exists(_p) else {}
def axes(th,psi=0.0):
    f=np.array([-np.cos(th),0,-np.sin(th)]); r0=np.array([0,1.0,0]); up0=np.cross(r0,f)
    r=np.cos(psi)*r0+np.sin(psi)*up0; up=-np.sin(psi)*r0+np.cos(psi)*up0
    return f,r,up
def proj(X,p=None):
    p=p or P; X=np.asarray(X,float); C=np.array([p['D'],p['YC'],p['HC']]); f,r,up=axes(p['TH'],p.get('PSI',0.0))
    q=X-C; d=q@f; return np.stack([p.get('CX',750.0)+p['F']*(q@r)/d, p.get('CY',1000.0)-p['F']*(q@up)/d],-1)
def ray(u,v,p=None):
    p=p or P; C=np.array([p['D'],p['YC'],p['HC']]); f,r,up=axes(p['TH'],p.get('PSI',0.0))
    d=f[None]+((np.asarray(u,float)-p.get('CX',750.0))/p['F'])[:,None]*r[None]-((np.asarray(v,float)-p.get('CY',1000.0))/p['F'])[:,None]*up[None]
    return C,d/np.linalg.norm(d,axis=1,keepdims=True)
def head_rot(phi):
    """rotation of the sprayer head (collar+cap) about +X through the neck point (0,0,h): y,z -> rotated"""
    c,s=np.cos(phi),np.sin(phi); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
