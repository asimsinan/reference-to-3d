"""The photo's camera by least squares on the silhouette's own circles: the rim's back half and side points (and its
front point read off a zoomed grid: without it the elevation was 8 px off), the base's front half from the lower
contour. Unknowns D, YC, HC, pitch TH, focal F and the mug's height h, base circle zb, rb; the rim radius R is the
assumed size (8.5 cm across). A close phone shot is pitched (rim ~10 deg, base ~30 deg): a level camera does not fit.
F is weakly determined (the refits at fixed F print near-equal rms over 1700-2300 px): check it against the phone's
lens (iPhone 2x at 1500 px wide ~2050 px, 1x ~1130 px). Principal point = image centre (an uncropped phone photo).
usage: uv run --with opencv-python-headless --with numpy --with scipy python solve_cam.py   -> cam.json"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2, json
from scipy.optimize import least_squares
from cam import proj, CX, CY
R=0.0425   # rim outer radius (assumed: rim 8.5 cm across)
s=cv2.imread('mask_photo.png',0)>0
rim=[];base=[]
for v in range(903,951,3):
    xs=np.where(s[v])[0]; rim+= [(xs[0],v),(xs[-1],v)]
for v in range(1745,1798,4):
    xs=np.where(s[v])[0]; base+=[(xs[0],v),(xs[-1],v)]
for u in range(600,740,15):
    ys=np.where(s[:,u])[0]; base.append((u,ys[-1]))
rim+=[(655,989),(665,989)]; rim=np.array(rim,float); base=np.array(base,float)
ang=np.linspace(0,2*np.pi,1440,endpoint=False)
def circ(z,r,p): return proj(np.stack([r*np.cos(ang),r*np.sin(ang),np.full_like(ang,z)],1),p)
def dist(pts,curve): return np.sqrt(((pts[:,None,:]-curve[None])**2).sum(2)).min(1)
def res(x):
    D,YC,HC,TH,F,h,zb,rb=x; p=dict(D=D,YC=YC,HC=HC,TH=TH,F=F)
    return np.concatenate([dist(rim,circ(h,R,p)),dist(base,circ(zb,rb,p))])
x0=[0.30,0.01,0.12,0.2,2000,0.115,0.004,0.03]
lo=[0.12,-0.1,0.0,-0.2,900,0.07,0.0,0.015]; hi=[1.5,0.1,0.6,0.8,4000,0.2,0.02,0.045]
sol=least_squares(res,x0,bounds=(lo,hi),x_scale=[0.1,0.01,0.05,0.1,500,0.02,0.005,0.01])
D,YC,HC,TH,F,h,zb,rb=sol.x; r=res(sol.x)
print('D %.3f YC %.4f HC %.3f TH %.2fdeg F %.0f | h %.4f zb %.4f rb %.4f | rms %.2f max %.2f px'%(D,YC,HC,np.degrees(TH),F,h,zb,rb,np.sqrt((r**2).mean()),r.max()))
# stability: refit with F fixed at several values
for Ff in [1400,1700,2000,2300,2600]:
    f=lambda x: res(np.r_[x[:4],Ff,x[4:]])
    s2=least_squares(f,np.r_[sol.x[:4],sol.x[5:]],bounds=(np.r_[lo[:4],lo[5:]],np.r_[hi[:4],hi[5:]]))
    rr=f(s2.x); print(' F=%d rms %.2f  D %.3f HC %.3f TH %.1f h %.4f'%(Ff,np.sqrt((rr**2).mean()),s2.x[0],s2.x[2],np.degrees(s2.x[3]),s2.x[4]))
json.dump(dict(D=D,YC=YC,HC=HC,TH=TH,F=F,h=h,zb=zb,rb=rb,R=R),open('cam.json','w'),indent=1)
