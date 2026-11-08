import numpy as np, json
W,H=1920,1080
f=1253.978; c=np.array([960,540.])
K=np.array([[f,0,c[0]],[0,f,c[1]],[0,0,1]]); Ki=np.linalg.inv(K)
d=np.array([-0.12228594,-0.07097164,0.98995413]); u=np.array([-0.00743268,-0.99734655,-0.07241975])
X=np.cross(d,u); X/=np.linalg.norm(X); Y=d; Z=np.cross(X,Y)
M=np.c_[X,Y,Z]          # cv-cam coords of world axes; c = M @ w
def ray(px,py):
    w=M.T@(Ki@np.array([px,py,1.])); return w/np.linalg.norm(w)
def hit(px,py,axis,val,cam):
    r=ray(px,py); t=(val-cam[axis])/r[axis]; return cam+t*r
def proj(P,cam):
    c_=M@(np.asarray(P)-cam); p=K@c_; return p[:2]/p[2]
