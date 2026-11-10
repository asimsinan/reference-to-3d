import numpy as np, json, cv2
W,H=1500,2000
J=json.load(open(__file__.replace('camlib.py','cam.json')))
def cam(v):
    c=J['cams'][v];R=cv2.Rodrigues(np.array(c['rv']))[0];cc=c.get('c',[W/2,H/2]);return R,np.array(c['t']),c['f'],cc[0],cc[1]
def proj(v,X):
    cm=cam(v) if isinstance(v,str) else v;R,t,f=cm[:3];cx,cy=(cm[3],cm[4]) if len(cm)>3 else (W/2,H/2)
    X=np.atleast_2d(np.asarray(X,float));Xc=X@R.T+t
    return np.stack([cx+f*Xc[:,0]/Xc[:,2],cy+f*Xc[:,1]/Xc[:,2]],1)
def ray(v,u,w):
    R,t,f,cx,cy=cam(v);d=R.T@np.array([(u-cx)/f,(w-cy)/f,1.]);return -R.T@t,d
def hit(v,u,w,axis,val):
    P,d=ray(v,u,w);k=(val-P[axis])/d[axis];return P+k*d
