"""camera from the vase's circles: rim top (mask back half + sides + front point), gold band at the foot (hand-read
centreline), the foot's bottom (mask lower contour, front half). R (rim outer radius) fixed = assumed size."""
import numpy as np, cv2, json
from scipy.optimize import least_squares
from cam import proj
R=0.052
s=cv2.imread('mask_raw.png',0)>0
rim=[];base=[]
for u in range(200,390,6):
    ys=np.where(s[:,u])[0]; rim.append((u,ys[0]-0.5))
for v in range(214,228,2):
    xs=np.where(s[v])[0]; rim+=[(xs[0]-0.5,v),(xs[-1]+0.5,v)]
rim+=[(285,237),(300,237)]
for u in range(240,350,6):
    ys=np.where(s[:,u])[0]; base.append((u,ys[-1]+0.5))
band=np.array([(240,743),(260,750),(290,755),(320,752),(340,745),(352,737)],float)
rim=np.array(rim,float); base=np.array(base,float)
ang=np.linspace(0,2*np.pi,1440,endpoint=False)
def circ(z,r,p): return proj(np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1),p)
def dist(pts,c): return np.sqrt(((pts[:,None]-c[None])**2).sum(2)).min(1)
def front(z,r,p): # only the near half (x>0) for front-only data
    a=ang[np.cos(ang)>0]; return proj(np.stack([r*np.cos(a),r*np.sin(a),np.full_like(a,z)],1),p)
def res(x):
    D,YC,HC,TH,F,h,rb,zg,rg=x; zb=0.0; p=dict(D=D,YC=YC,HC=HC,TH=TH,F=F)
    return np.concatenate([dist(rim,circ(h,R,p)),dist(base,front(zb,rb,p)),dist(band,front(zg,rg,p))])
x0=[0.66,0.0,0.45,0.38,1300,0.31,0.06,0.03,0.04]
lo=[0.15,-0.1,-0.2,-0.2,300,0.15,0.02,0.0,0.015]; hi=[3,0.1,2,1.2,4000,0.5,0.08,0.08,0.06]
xs=[0.1,0.01,0.1,0.1,300,0.02,0.01,0.01,0.01]
sol=least_squares(res,x0,bounds=(lo,hi),x_scale=xs)
r=res(sol.x); print('sol',np.round(sol.x,4),'deg %.1f rms %.2f max %.2f'%(np.degrees(sol.x[3]),np.sqrt((r**2).mean()),r.max()))
for Ff in [500,700,900,1200,1600,2200]:
    f=lambda x: res(np.r_[x[:4],Ff,x[4:]])
    s2=least_squares(f,np.r_[sol.x[:4],sol.x[5:]],bounds=(np.r_[lo[:4],lo[5:]],np.r_[hi[:4],hi[5:]]),x_scale=np.r_[xs[:4],xs[5:]])
    rr=f(s2.x); print(' F=%d rms %.2f D %.3f HC %.3f TH %.1f h %.4f rb %.4f zg %.4f rg %.4f'%(Ff,np.sqrt((rr**2).mean()),s2.x[0],s2.x[2],np.degrees(s2.x[3]),s2.x[4],s2.x[5],s2.x[6],s2.x[7]))
D,YC,HC,TH,F,h,rb,zg,rg=sol.x; zb=0.0
json.dump(dict(D=D,YC=YC,HC=HC,TH=TH,F=F,h=h,zb=zb,rb=rb,zg=zg,rg=rg,R=R),open('cam.json','w'),indent=1)
