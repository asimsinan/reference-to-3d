import numpy as np, json
from scipy.spatial.transform import Rotation as R
C=json.load(open('cam.json'))
W,D,HB,HL,HX,LL,phi=C['W'],C['D'],C['HB'],C['HL'],C['HX'],C['LL'],C['phi']
Rm=R.from_rotvec(C['rotvec']).as_matrix(); t=np.array(C['t']); f=C['f']
def proj(P):
    P=np.atleast_2d(P); X=P@Rm.T+t
    return np.c_[f*X[:,0]/X[:,2]+1000, f*X[:,1]/X[:,2]+750]
d=np.array([np.cos(phi),0,np.sin(phi)]); n=np.array([np.sin(phi),0,-np.cos(phi)])
def lid(u,v,w=0):  # u along lid from hinge, v = y, w = thickness (0 = screen face, HL = back)
    return np.array([HX,0,HB])+u*d+np.array([0,v,0])-w*n
def quad_deck(): return [np.array(p,float) for p in [(D/2,-W/2,HB),(D/2,W/2,HB),(-D/2,W/2,HB),(-D/2,-W/2,HB)]]
