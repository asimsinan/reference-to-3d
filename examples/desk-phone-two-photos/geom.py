import numpy as np, json
from scipy.spatial.transform import Rotation as R
C=json.load(open('cam.json'))
W,D,HF,HB,KH,KD=C['W'],C['D'],C['HF'],C['HB'],C['KH'],C['KD']
X0,PX,Y0,PY=C['X0'],C['PX'],C['Y0'],C['PY']
ZF,ZBK,T=C['ZF'],C['ZBK'],C['T']; AL=C['al']
def ztop(x): return HF+(D/2-np.asarray(x,float))*(HB-HF)/D
def zband(x): return ZBK+(ZF-ZBK)*(np.asarray(x,float)+D/2)/D
class Cam:
    def __init__(s,rv,t,f,iw,ih): s.Rm=R.from_rotvec(rv).as_matrix(); s.t=np.array(t); s.f=f; s.iw=iw; s.ih=ih; s.C=-s.Rm.T@s.t
    def proj(s,P):
        P=np.atleast_2d(P); X=P@s.Rm.T+s.t; return np.c_[s.f*X[:,0]/X[:,2]+s.iw/2, s.f*X[:,1]/X[:,2]+s.ih/2]
    def ray(s,u,v):
        d=s.Rm.T@np.array([(u-s.iw/2)/s.f,(v-s.ih/2)/s.f,1.0]); return s.C, d
    def hit_plane(s,u,v,P0,n):
        c,d=s.ray(u,v); return c+((np.array(n)@(np.array(P0)-c))/(np.array(n)@d))*d
cam1=Cam(C['rv'],C['t'],C['f'],C['IW'],C['IH']); cam2=Cam(C['rv2'],C['t2'],C['f2'],C['IW2'],C['IH2'])
proj=cam1.proj
def plan(rc=10,n=6):
    pts=[]
    for (cx,cy,a0) in [(D/2-rc,W/2-rc,0),(-D/2+rc,W/2-rc,90),(-D/2+rc,-W/2+rc,180),(D/2-rc,-W/2+rc,270)]:
        for a in np.linspace(a0,a0+90,n): pts.append((cx+rc*np.cos(np.radians(a)),cy+rc*np.sin(np.radians(a))))
    return pts
