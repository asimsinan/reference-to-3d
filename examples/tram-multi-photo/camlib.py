import json, numpy as np
from scipy.spatial.transform import Rotation as Rot
import os
J=json.load(open(os.environ.get('CAMS','cams.json')))
def cam(k):
    c=np.array(J['cams'][k]); W,H=J['sizes'][k]
    cx,cy=(c[7],c[8]) if len(c)>7 else (W/2,H/2)
    return Rot.from_rotvec(c[:3]).as_matrix(), c[3:6], c[6], W, H, cx, cy
def proj(k,X):
    R,C,f,W,H,cx,cy=cam(k); Xc=(R@(np.atleast_2d(X)-C).T).T
    return np.stack([f*Xc[:,0]/Xc[:,2]+cx, f*Xc[:,1]/Xc[:,2]+cy],1)
def ray(k,u):
    R,C,f,W,H,cx,cy=cam(k); u=np.atleast_2d(u)
    d=np.stack([(u[:,0]-cx)/f,(u[:,1]-cy)/f,np.ones(len(u))],1)@R
    return C, d
def to_plane_z(k,u,z0):
    C,d=ray(k,u); t=(z0-C[2])/d[:,2]; return C+t[:,None]*d
