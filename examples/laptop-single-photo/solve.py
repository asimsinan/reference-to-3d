"""Camera, lid angle and lid length from one photo of a MacBook Pro 14 (mm). -> cam.json
Points: deck front corners, lid outline top/bottom corners (each corner = the intersection of its two straight
edges, measured with edge profiles, not by eye), and the display's four corners (a 302.5 x 196.5 mm rectangle,
centred across the lid, its top t_top below the lid's top). Image left = the laptop's right (-y)."""
import numpy as np, json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R
W,D,HB,HL=312.6,221.2,9.5,6.0
HX=-D/2+6
DW,DH=302.5,196.5
def pts3(phi,LL,ttop):
    d=np.array([np.cos(phi),0,np.sin(phi)])
    h=lambda y: np.array([HX,y,HB])
    return np.array([
      [D/2,-W/2,HB],[D/2,W/2,HB],                       # deck front corners
      h(-W/2)+LL*d, h(W/2)+LL*d,                        # lid top corners
      h(-W/2)+8*d, h(W/2)+8*d,                          # lid bottom visible corners
      h(-DW/2)+(LL-ttop)*d, h(DW/2)+(LL-ttop)*d,        # display top corners
      h(-DW/2)+(LL-ttop-DH)*d, h(DW/2)+(LL-ttop-DH)*d,  # display bottom corners
    ])
img=np.array([[256,1350],[2018,1366],[545.5,81],[1689,48],[563,843],[1689,845],
              [569.5,101],[1669,71],[580,804],[1670,796]],float)
wts=np.array([1,1,1,1,.5,.5,1.5,1.5,1.5,1.5])            # display corners are the sharpest; lid bottom the least sure
def proj(p,P3):
    X=R.from_rotvec(p[0:3]).apply(P3)+p[3:6]
    return np.c_[p[6]*X[:,0]/X[:,2]+1000, p[6]*X[:,1]/X[:,2]+750]
def res(p): return ((proj(p,pts3(p[7],p[8],p[9]))-img)*wts[:,None]).ravel()
best=None
for pitch in [20,35,50]:
  for dist in [400,550,700]:
    Rm=R.from_euler('x',-pitch,degrees=True).as_matrix()@np.array([[0,1,0],[0,0,-1],[-1,0,0]],float)
    p0=np.r_[R.from_matrix(Rm).as_rotvec(),[0,40,dist],1450,np.radians(110),219,4]
    r=least_squares(res,p0,bounds=([-np.inf]*6+[500,np.radians(80),200,1],[np.inf]*6+[5000,np.radians(140),235,12]))
    if best is None or r.cost<best.cost: best=r
p=best.x; e=proj(p,pts3(p[7],p[8],p[9]))-img
print('rms px %.2f  f %.0f  lid %.1f deg  LL %.1f  t_top %.1f'%(np.sqrt((e**2).sum(1).mean()),p[6],np.degrees(p[7]),p[8],p[9]))
print(np.round(e,1))
Rm=R.from_rotvec(p[:3]).as_matrix(); C=-Rm.T@p[3:6]; print('camera mm',np.round(C,1))
json.dump({'rotvec':p[:3].tolist(),'t':p[3:6].tolist(),'f':p[6],'phi':p[7],'cam':C.tolist(),'W':W,'D':D,'HB':HB,'HL':HL,
           'HX':HX,'LL':p[8],'ttop':p[9]},open('cam.json','w'),indent=1)
