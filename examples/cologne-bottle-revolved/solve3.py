"""Camera + bottle by least squares. Body: straight cylinder R (the size), base radius rb free (taper), shoulder
fillet rs, height h. Head (collar+cap frustums) tilted by PHI about +X at the neck. Camera: level-ish (TH free),
roll PSI, principal row CY free (the photo is a crop), F free (the sags of circles at different heights fix D and HC).
usage: python solve3.py  -> cam.json, prints the fit"""
import sys,json,numpy as np,cv2
from scipy.optimize import least_squares
import cam as C
obs=json.load(open('obs.json')); E=json.load(open('edges.json'))
sil=cv2.imread('mask_photo.png',0)>0
R=0.020
BL=[];BR=[]
for v in range(950,1545,4):
    xs=np.where(sil[v])[0]; BL.append((xs[0]-0.5,v))
    if v<1012: BR.append((xs[-1]+0.5,v))
for v in range(1480,1545,4): BR.append((940.0,v))
body=np.array(BL+BR,float); base=np.array(obs['base'],float)
cap=np.array(obs['cap'],float)[:,:2]; col=np.array(obs['collar'],float)[:,:2]
arc=np.array(E['collar_bot']['pts'],float)
shoulder=np.array([(x,np.where(sil[850:950,x])[0][0]+850-0.5) for x in range(626,690,2)],float)
captop=np.array([(x,np.where(sil[:,x])[0][0]-0.5) for x in range(735,890,5)],float)
col_top=np.array([(682.5,702),(909.5,710)],float)
ANG=np.linspace(0,2*np.pi,720,endpoint=False)
def circ(z,r,p,Rm=None,h=0):
    X=np.stack([r*np.cos(ANG),r*np.sin(ANG),np.full_like(ANG,z)],1)
    if Rm is not None: X=(X-[0,0,h])@Rm.T+[0,0,h]
    return C.proj(X,p)
def tangent_res(pts,p,r_lo,r_hi,z_lo,z_hi,Rm=None,h=0):
    Cc,d=C.ray(pts[:,0],pts[:,1],p)
    if Rm is not None: Cc=Rm.T@(Cc-[0,0,h])+[0,0,h]; d=d@Rm
    tc=-(Cc[0]*d[:,0]+Cc[1]*d[:,1])/(d[:,0]**2+d[:,1]**2)
    t=tc[:,None]+np.linspace(-0.03,0.03,121)[None]
    X=Cc[None,None]+t[...,None]*d[:,None,:]
    rho=np.hypot(X[...,0],X[...,1]); z=X[...,2]
    r=r_lo+(r_hi-r_lo)*(z-z_lo)/(z_hi-z_lo)
    return (rho-r).min(1)*p['F']/p['D']
def outline_res(pts,p,r0,rf,z0,upper,Rm=None,h=0):
    sg=-1 if upper else 1; best=np.full(len(pts),-np.inf)
    for z in np.linspace(0,rf,12):
        r=r0-rf+np.sqrt(max(rf*rf-(rf-z)**2,0)); poly=circ(z0+sg*z,r,p,Rm,h)
        vc=poly[:,1].mean(); low=poly[sg*poly[:,1]>=sg*vc]; o=np.argsort(low[:,0]); low=low[o]
        vv=np.interp(pts[:,0],low[:,0],sg*low[:,1],left=-np.inf,right=-np.inf); best=np.maximum(best,vv)
    bad=~np.isfinite(best); best[bad]=sg*pts[bad,1]-40
    return best-sg*pts[:,1]
def dist(pts,curve): return np.sqrt(((pts[:,None,:]-curve[None])**2).sum(2)).min(1)
NAMES='D YC HC TH PSI CY F rb h rs rc0 rc1 zc0 zc1 rk0 rk1 zk1 PHI rg'.split()
def unpack(x):
    d=dict(zip(NAMES,x)); p=dict(D=d['D'],YC=d['YC'],HC=d['HC'],TH=d['TH'],PSI=d['PSI'],CY=d['CY'],CX=750.0,F=d['F']); return p,d
KF=0.0015   # cap top fillet
def res(x):
    p,d=unpack(x); Rm=C.head_rot(d['PHI']); h=d['h']
    return np.concatenate([
        tangent_res(body,p,d['rb'],R,0.0,h),
        tangent_res(col,p,d['rc0'],d['rc1'],d['zc0'],d['zc1'],Rm,h),
        tangent_res(cap,p,d['rk0'],d['rk1'],d['zc1'],d['zk1'],Rm,h),
        dist(arc,circ(d['zc0'],d['rc0'],p,Rm,h)),
        dist(base,circ(0.0005,d['rg'],p)),
        outline_res(shoulder,p,R,d['rs'],h,True),
        outline_res(captop,p,d['rk1'],KF,d['zk1'],True,Rm,h),
        2*dist(col_top,circ(d['zc1'],d['rc1'],p,Rm,h))])
X0=dict(D=0.41,YC=-0.004,HC=0.164,TH=0.0,PSI=0.018,CY=230,F=3400,rb=0.020,h=0.087,rs=0.004,rc0=0.0138,rc1=0.0136,zc0=0.090,zc1=0.108,rk0=0.0106,rk1=0.0100,zk1=0.137,PHI=-0.025,rg=0.017)
LO=dict(D=0.1,YC=-0.05,HC=0.0,TH=-0.3,PSI=-0.1,CY=-3000,F=800,rb=0.016,h=0.07,rs=0.0005,rc0=0.01,rc1=0.01,zc0=0.08,zc1=0.09,rk0=0.007,rk1=0.007,zk1=0.11,PHI=-0.1,rg=0.012)
HI=dict(D=3.0,YC=0.05,HC=0.8,TH=0.3,PSI=0.1,CY=3000,F=12000,rb=0.024,h=0.12,rs=0.007,rc0=0.018,rc1=0.018,zc0=0.11,zc1=0.13,rk0=0.014,rk1=0.014,zk1=0.17,PHI=0.1,rg=0.02)
XS=dict(D=0.1,YC=0.005,HC=0.05,TH=0.05,PSI=0.01,CY=100,F=500,rb=0.002,h=0.01,rs=0.002,rc0=0.001,rc1=0.001,zc0=0.005,zc1=0.005,rk0=0.001,rk1=0.001,zk1=0.005,PHI=0.01,rg=0.002)
sol=None
for F0 in (2000,3400,5000):
    for th0 in (-0.05,0.0,0.05):
        x0=[X0[n] for n in NAMES]; x0[NAMES.index('F')]=F0; x0[NAMES.index('TH')]=th0; x0[NAMES.index('D')]=0.41*F0/3400
        s_=least_squares(res,x0,bounds=([LO[n] for n in NAMES],[HI[n] for n in NAMES]),x_scale=[XS[n] for n in NAMES],max_nfev=400)
        p,d=unpack(s_.x); print('  start F %d TH %.2f -> cost %.1f  F %.0f D %.3f HC %.3f TH %.2f CY %.0f rb %.4f'%(F0,th0,s_.cost,d['F'],d['D'],d['HC'],np.degrees(d['TH']),d['CY'],d['rb']))
        if sol is None or s_.cost<sol.cost: sol=s_
r=res(sol.x); p,d=unpack(sol.x)
ns=np.cumsum([len(body),len(col),len(cap),len(arc),len(base),len(shoulder),len(captop),2]); parts=np.split(r,ns[:-1])
rms=lambda q: np.sqrt((q**2).mean())
print('rms %.2f | body %.2f collar %.2f cap %.2f arc %.2f base %.2f shoulder %.2f captop %.2f coltop %.2f'%(rms(r),*[rms(q) for q in parts]))
print('D %.3f YC %.4f HC %.3f TH %.2f PSI %.2f CY %.0f F %.0f | rb %.4f h %.4f rs %.4f | collar r %.4f/%.4f z %.4f..%.4f | cap r %.4f/%.4f top %.4f | head tilt %.2f deg | rg %.4f'%(
    d['D'],d['YC'],d['HC'],np.degrees(d['TH']),np.degrees(d['PSI']),d['CY'],d['F'],d['rb'],d['h'],d['rs'],d['rc0'],d['rc1'],d['zc0'],d['zc1'],d['rk0'],d['rk1'],d['zk1'],np.degrees(d['PHI']),d['rg']))
d.update(p); d['R']=R; d['rf']=0.003; d['KF']=KF
json.dump(d,open('cam.json','w'),indent=1); print('wrote cam.json')
