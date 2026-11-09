import numpy as np, json
C_=json.load(open('cam.json')); R=np.array(C_['R']); t=np.array(C_['t']); F=C_['f']; CX=C_['cx']; CY=C_['cy']
L,W,T,H=C_['L'],C_['W'],C_['T'],C_['H']; CAM=np.array(C_['C'])
def proj(X):
    X=np.atleast_2d(np.asarray(X,float)); Xc=X@R.T+t
    return np.c_[F*Xc[:,0]/Xc[:,2]+CX, F*Xc[:,1]/Xc[:,2]+CY]
def ray(u,v):
    d=np.array([(u-CX)/F,(v-CY)/F,1.0]); d=R.T@d; return CAM, d/np.linalg.norm(d)
def hit_z(u,v,z):
    o,d=ray(u,v); s=(z-o[2])/d[2]; return o+s*d
def hit_plane(u,v,n,p0):
    o,d=ray(u,v); n=np.asarray(n,float); s=((np.asarray(p0)-o)@n)/(d@n); return o+s*d
