"""Camera by least squares on the holder's circles: rim outer top (back half), the ring's front lower edge, base front.
R (rim outer radius) fixed as the assumed size. Roll included (a hand-held phone). -> cam.json"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, json
from scipy.optimize import least_squares
from cam import proj
R=float(os.environ.get('RIM_R','0.045'))
E=json.load(open('edges.json')); top=np.array(E['top'],float); rb_=np.array(E['ringbot'],float); base=np.array(E['base'],float)
top=top[top[:,1]<1000]                 # a column whose mask starts at the chair blob, not the rim
rb_=rb_[rb_[:,0]>700]                  # left of 700 the chair is behind the mesh: the ring's lower edge cannot be told from it
import cv2
from cam import ray
# the wall's side silhouettes (rows between the rings' side points): rays tangent to a cylinder of radius rw
_s=cv2.imread('mask_photo.png',0)>0; SU=[];SV=[]
for v in range(990,1470,6):
    xs=np.where(_s[v])[0]; SU+=[xs[0]-0.5,xs[-1]+0.5]; SV+=[v,v]
SU=np.array(SU,float); SV=np.array(SV,float)
def side_res(p,rw):
    C,d=ray(SU,SV,p); dist=np.abs(C[0]*d[:,1]-C[1]*d[:,0])/np.hypot(d[:,0],d[:,1])
    return (dist-rw)*p['F']/p['D']
ang=np.linspace(0,2*np.pi,1440,endpoint=False)
def circ(z,r,p): return proj(np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1),p)
def dist(pts,curve): return np.sqrt(((pts[:,None,:]-curve[None])**2).sum(2)).min(1)
names='D YC HC TH RO F h t zb rb rw'.split()
def unpack(x): 
    D,YC,HC,TH,RO,F,h,t,zb,rb,rw=x; return dict(D=D,YC=YC,HC=HC,TH=TH,RO=RO,F=F),h,t,zb,rb,rw
def res(x,F=None):
    if F is not None: x=np.r_[x[:5],F,x[5:]]
    p,h,t,zb,rb,rw=unpack(x)
    WR=float(os.environ.get('W_RINGBOT','1'))
    return np.concatenate([dist(top,circ(h,R,p)),WR*dist(rb_,circ(h-t,R,p)),dist(base,circ(zb,rb,p)),side_res(p,rw)])
x0=np.array([0.6,0.0,0.15,0.1,0.0,2000,0.10,0.006,0.002,0.044,0.042])
lo=np.array([0.12,-0.1,0.0,-0.2,-0.1,900,0.06,0.003,0.0,0.03,0.035]); hi=np.array([3.0,0.1,0.8,0.8,0.1,4500,0.16,0.015,0.01,0.05,0.048])
xs=np.array([0.1,0.01,0.05,0.1,0.02,500,0.02,0.002,0.002,0.005,0.002])
best=None
for D0 in (0.3,0.6,1.0):
  for F0 in (1200,2000,3000):
    x0[0]=D0; x0[5]=F0; x0[2]=0.12+0.1*D0
    s=least_squares(res,x0,bounds=(lo,hi),x_scale=xs,loss='soft_l1',f_scale=2.0)
    if best is None or s.cost<best.cost: best=s
FIX=os.environ.get('FIX_F')
if FIX:   # the phone's lens is not in the file; F is weakly determined, so it is set here (see the F scan)
    Ff=float(FIX); s2=least_squares(lambda x: res(x,Ff),best.x[np.r_[0:5,6:11]],bounds=(lo[np.r_[0:5,6:11]],hi[np.r_[0:5,6:11]]),x_scale=xs[np.r_[0:5,6:11]],loss='soft_l1',f_scale=2.0)
    best.x=np.r_[s2.x[:5],Ff,s2.x[5:]]
sol=best; r=res(sol.x); p,h,t,zb,rb,rw=unpack(sol.x)
n1,n2,n3=len(top),len(rb_),len(base)
print(' '.join('%s %.4f'%(k,v) for k,v in zip(names,sol.x)),'| TH %.2f RO %.2f deg'%(np.degrees(p['TH']),np.degrees(p['RO'])))
print('rms top %.2f ringbot %.2f base %.2f sides %.2f px'%tuple(np.sqrt((r[s]**2).mean()) for s in (slice(0,n1),slice(n1,n1+n2),slice(n1+n2,n1+n2+n3),slice(n1+n2+n3,None))),'| >3px:',int((np.abs(r)>3).sum()),'of',len(r))
sel=np.r_[0:5,6:11]
for Ff in [1100,1400,1700,2000,2300,2700,3200]:
    s2=least_squares(lambda x: res(x,Ff),sol.x[sel],bounds=(lo[sel],hi[sel]),x_scale=xs[sel],loss='soft_l1',f_scale=2.0)
    rr=res(s2.x,Ff); print(' F=%d rms %.2f  D %.3f HC %.3f TH %.1f RO %.1f h %.4f t %.4f rb %.4f rw %.4f'%(Ff,np.sqrt((rr**2).mean()),s2.x[0],s2.x[2],np.degrees(s2.x[3]),np.degrees(s2.x[4]),s2.x[5],s2.x[6],s2.x[8],s2.x[9]))
# frame: z=0 at the base ring's lowest point (the solved base contour circle sits ~0.1 tube radius above it)
ZOFF=zb-0.00024; p['HC']-=ZOFF; h-=ZOFF; zb-=ZOFF
json.dump(dict(**p,h=h,t=t,zb=zb,rb=rb,rw=rw,R=R),open('cam.json','w'),indent=1)
