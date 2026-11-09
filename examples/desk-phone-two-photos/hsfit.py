"""Handset alone, cameras and body fixed (cam.json): do the two photos agree on it?"""
import numpy as np, json
from scipy.optimize import least_squares
from geom import *
HS_SIDE_TOP=np.array([(280,592),(400,595),(500,603),(600,615),(700,635),(800,655),(900,672),(1000,705),(1060,725)],float)
HS_SIDE_BACK=np.array([(221,640),(221,690)],float); HS_SIDE_FRONT=np.array([(1138,810),(1138,860)],float)
HS_FRONT=np.array([(455,797),(640,797),(345,1300),(640,1300)],float)
def obs(p,parts=False):
    xb,xf,zb,zf,yc,we=p; zt=lambda x: zb+(zf-zb)*(x-xb)/(xf-xb); r={}
    P=np.array([[x,yc-we/2+5,zt(x)-1.5] for x in np.linspace(xb+12,xf-10,len(HS_SIDE_TOP))]); r['side_top_y']=cam2.proj(P)[:,1]-HS_SIDE_TOP[:,1]
    r['side_back_x']=cam2.proj(np.array([[xb,yc-we/2+3,zb-8],[xb,yc-we/2+3,zb-14]]))[:,0]-HS_SIDE_BACK[:,0]
    r['side_front_x']=cam2.proj(np.array([[xf,yc-we/2+3,zf-5],[xf,yc-we/2+3,zf-10]]))[:,0]-HS_SIDE_FRONT[:,0]
    P=np.array([[xb+6,yc-we/2+4,zb-2],[xb+6,yc+we/2-4,zb-2],[xf-6,yc-we/2+4,zf-2],[xf-6,yc+we/2-4,zf-2]]); r['front_corners']=(cam1.proj(P)-HS_FRONT).ravel()
    return r if parts else np.concatenate(list(r.values()))
for name,w in [('both',(1,1,1,1)),('side only',(1,1,1,0)),('front only',(0,0,0,1))]:
    def res(p):
        r=obs(p,True); return np.concatenate([w[0]*r['side_top_y'],w[1]*r['side_back_x'],w[2]*r['side_front_x'],w[3]*r['front_corners']])
    s=least_squares(res,[-73,83,50,35,-37,50],bounds=([-120,40,20,10,-60,30],[-40,110,90,70,-15,70]))
    p=s.x; r=obs(p,True)
    print(f'{name:10s} xb {p[0]:.1f} xf {p[1]:.1f} zb {p[2]:.1f} zf {p[3]:.1f} (rim there {float(ztop(p[0])):.1f}/{float(ztop(p[1])):.1f}) yc {p[4]:.1f} we {p[5]:.1f}')
    for k,v in r.items(): print('    ',k,np.round(v,1))
    print('    rms',round(float(np.sqrt((np.concatenate(list(r.values()))**2).mean())),1))

# handset.json for build.py: the fit to both photos, plus the top's arc read off the side photo on the handset's
# left flank (y = yc - we/2 + 5) and shifted to the compromise height (the photos disagree on it by ~10 mm).
import json
s=least_squares(lambda p: obs(p),[-73,83,50,35,-37,50],bounds=([-120,40,20,10,-60,30],[-40,110,90,70,-15,70])); p=s.x
H=dict(xb=float(p[0]),xf=float(p[1]),zb=float(p[2]),zf=float(p[3]),yc=float(p[4]),we=float(p[5]))
yf=H['yc']-H['we']/2+5
P=np.array([cam2.hit_plane(u,v,[0,yf,0],[0,1,0]) for u,v in HS_SIDE_TOP]); c=np.polyfit(P[:,0],P[:,2],2)
xs=np.linspace(H['xb'],H['xf'],7); off=(H['zb']+(H['zf']-H['zb'])*(xs-H['xb'])/(H['xf']-H['xb'])).mean()-np.polyval(c,xs).mean()
H['top_quad']=[float(c[0]),float(c[1]),float(c[2]+off)]; json.dump(H,open('handset.json','w'),indent=1); print('handset.json',H)
