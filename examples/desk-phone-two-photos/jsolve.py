"""Joint solve: the front photo (ref.jpg 1500x2000) and the side photo (side.jpg 1200x1600) of the Tesan phone,
one shared body. Frame: +X front, +Y the phone's left (keypad side; the handset side is -Y), +Z up, table z=0.
Body: rounded-rectangle plan W x D (W fixed), a sloped top from HF (front) to HB (back), a dark band on the walls
whose top runs from ZBK (back) to ZF (front), thickness T. Keypad on the top. Priors: W, f1, f2 (same phone, no EXIF).
-> cam.json"""
import numpy as np, json, sys
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R
W=float(sys.argv[1]) if len(sys.argv)>1 else 140.0
F1=1450.0; F2=float([a for a in sys.argv if a.startswith('f2=')][0][3:]) if any(a.startswith('f2=') for a in sys.argv) else F1*1200/1500; FREE_F2='freef2' in sys.argv; HSW=float([a for a in sys.argv if a.startswith('hs=')][0][3:]) if any(a.startswith('hs=') for a in sys.argv) else 1.0; KH=3.0; RC=10.0
IM1=(1500,2000); IM2=(1200,1600)
KM=np.array(json.load(open('keys_meas.json')))
L1=json.load(open('lines.json')); L1['front_top']={'line':None,'pts':[[400,1468],[1060,1483]]}
L2=json.load(open('slines.json'))
def line_of(e):
    if e.get('line'): return np.array(e['line'])
    p=np.array(e['pts'],float); c=p.mean(0); d=np.linalg.svd(p-c)[2][0]; n=np.array([-d[1],d[0]]); return np.r_[n,-n@c]
LN1={k:line_of(v) for k,v in L1.items()}; LN2={k:line_of(v) for k,v in L2.items()}
NAMES=['D','HF','HB','ZF','ZBK','T','X0','PX','Y0','PY','KD','HXB','HXF','HZB','HZF','HYC','HWE','F2','F1V','KHV','BFX','BFY','BRX','BRY']
FREE_F1='freef1' in sys.argv
HS_CONST=[-73,83,50,35,-37,50,F2,F1,KH, 42.7,50.9,58.3,50.7]
def unpack(p):
    p=np.asarray(p,float)
    if len(p)==27: p=np.r_[p[:23],HS_CONST[:9],p[23:]]
    elif len(p)<12+len(NAMES): p=np.r_[p,HS_CONST[:12+len(NAMES)-len(p)]]
    q=dict(rv1=p[0:3],t1=p[3:6],rv2=p[6:9],t2=p[9:12]); q.update(zip(NAMES,p[12:])); return q
def ztop(q,x): return q['HF']+(q['D']/2-x)*(q['HB']-q['HF'])/q['D']
def zband(q,x): return q['ZBK']+(q['ZF']-q['ZBK'])*(x+q['D']/2)/q['D']
def proj(rv,t,f,im,P):
    X=R.from_rotvec(rv).apply(np.atleast_2d(P))+t
    return np.c_[f*X[:,0]/X[:,2]+im[0]/2, f*X[:,1]/X[:,2]+im[1]/2]
def proj1(q,P): return proj(q['rv1'],q['t1'],q['F1V'],IM1,P)
def proj2(q,P): return proj(q['rv2'],q['t2'],q['F2'],IM2,P)
def key_obs(q):
    r=[]
    for i in range(4):
        for j in range(3):
            x=q['X0']+i*q['PX']; y=q['Y0']+j*q['PY']; kd=q['KD']
            kh=q['KHV']; P=np.array([[x,y,ztop(q,x)+kh],[x-kd/2,y,ztop(q,x-kd/2)+kh],[x+kd/2,y,ztop(q,x+kd/2)+kh],[x+kd/2,y,ztop(q,x+kd/2)]])
            u=proj1(q,P); r.append([u[0,0],u[0,1],u[1,1],u[2,1],u[3,1]])
    return np.array(r)
def seg1(q,name,n=6):
    D,HF=q['D'],q['HF']; s=np.linspace(0,1,n); yy=-W/2+20+s*(W-40)
    if name=='band_top': return np.c_[np.full(n,D/2), yy, np.full(n,q['ZF'])]
    if name=='band_bot': return np.c_[np.full(n,D/2), yy, np.full(n,q['ZF']-q['T'])]
    if name=='floor':    return np.c_[np.full(n,D/2), yy, np.zeros(n)]
    if name=='front_top':return np.c_[np.full(n,D/2), yy, np.full(n,HF)]
    if name=='right_edge': x=-D/2+20+s*(D-40); return np.c_[x, np.full(n,W/2), ztop(q,x)]
    if name=='left_edge':  x=D/2-25+s*20;      return np.c_[x, np.full(n,-W/2), ztop(q,x)]
    if name=='back_edge':  return np.c_[np.full(n,-D/2), -W/2+30+s*(W-50), np.full(n,q['HB'])]
def seg2(q,name,n=6):
    D=q['D']; s=np.linspace(0,1,n); x=-D/2+15+s*(D-30); yl=np.full(n,-W/2)
    if name=='band_top': return np.c_[x, yl, zband(q,x)]
    if name=='band_bot': return np.c_[x, yl, zband(q,x)-q['T']]
    if name=='floor':    return np.c_[x, yl, np.zeros(n)]
    if name=='rim':      return np.c_[x, yl, ztop(q,x)-2.0]
    if name=='front_corner': z=8+s*(q['HF']-14); return np.c_[np.full(n,D/2-3), np.full(n,-W/2+3), z]
    if name=='back_corner':  z=8+s*(q['HB']-14); return np.c_[np.full(n,-D/2+3), np.full(n,-W/2+3), z]
W1={'band_top':1.0,'band_bot':1.0,'floor':0.8,'front_top':0.4,'right_edge':0.8,'left_edge':0.4,'back_edge':0.3}
W2={'band_top':1.0,'band_bot':1.0,'floor':0.7,'rim':0.5,'front_corner':0.5,'back_corner':0.5}
# handset: its top edge in the side photo (points), its back/front faces there, and its end edges in the front photo
HS_SIDE_TOP=np.array([(280,592),(400,595),(500,603),(600,615),(700,635),(800,655),(900,672),(1000,705),(1060,725)],float)
HS_SIDE_BACK=np.array([(221,640),(221,690)],float); HS_SIDE_FRONT=np.array([(1138,810),(1138,860)],float)
HS_FRONT=np.array([(455,797),(640,797),(345,1300),(640,1300)],float)   # back-left, back-right, front-left, front-right top corners
def hs_obs(q):
    xb,xf,zb,zf,yc,we=q['HXB'],q['HXF'],q['HZB'],q['HZF'],q['HYC'],q['HWE']
    zt=lambda x: zb+(zf-zb)*(x-xb)/(xf-xb)
    r=[]
    # side top edge: the handset's upper-left rounded edge
    P=np.array([[x,yc-we/2+5,zt(x)-1.5] for x in np.linspace(xb+12,xf-10,len(HS_SIDE_TOP))])
    u=proj2(q,P); r.append(((u-HS_SIDE_TOP)*np.array([0.3,1.0])).ravel())   # x along the edge is not an observation: weight it down
    # side back / front faces (vertical-ish lines at x = xb / xf): only the image x matters
    u=proj2(q,np.array([[xb,yc-we/2+3,zb-8],[xb,yc-we/2+3,zb-14]])); r.append(u[:,0]-HS_SIDE_BACK[:,0])
    u=proj2(q,np.array([[xf,yc-we/2+3,zf-5],[xf,yc-we/2+3,zf-10]])); r.append(u[:,0]-HS_SIDE_FRONT[:,0])
    # front photo: the four top corners
    P=np.array([[xb+6,yc-we/2+4,zb-2],[xb+6,yc+we/2-4,zb-2],[xf-6,yc-we/2+4,zf-2],[xf-6,yc+we/2-4,zf-2]])
    u=proj1(q,P); r.append((u-HS_FRONT).ravel()*0.8)
    return np.concatenate(r)
KW=np.array([1,1,1,0.7,1])
BTN_FRONT=np.array([[992,1250],[1005,1318]],float); BTN_SIDE=np.array([[1005,711],[1075,745]],float)   # FLASH, REDIAL centres
def btn_obs(q):
    P=np.array([[q['BFX'],q['BFY'],ztop(q,q['BFX'])+2.6],[q['BRX'],q['BRY'],ztop(q,q['BRX'])+2.6]])
    return np.concatenate([(proj1(q,P)-BTN_FRONT).ravel(),(proj2(q,P)-BTN_SIDE).ravel()])
def res(p):
    q=unpack(p); r=[((key_obs(q)-KM)*KW).ravel(), btn_obs(q)]
    for nm,w in W1.items():
        a,b,c=LN1[nm]; u=proj1(q,seg1(q,nm)); r.append(w*(a*u[:,0]+b*u[:,1]+c))
    for nm,w in W2.items():
        a,b,c=LN2[nm]; u=proj2(q,seg2(q,nm)); r.append(w*(a*u[:,0]+b*u[:,1]+c))
    r.append(HSW*hs_obs(q))
    return np.concatenate(r)
def lookat(cam,target):
    f=np.array(target,float)-cam; f/=np.linalg.norm(f); up=np.array([0,0,1.]); r=np.cross(f,up); r/=np.linalg.norm(r); d=np.cross(f,r)
    Rm=np.array([r,d,f]); return R.from_matrix(Rm).as_rotvec(), -Rm@cam
C0=json.load(open('cam.json'))
best=None
for cam2 in [(30,-300,110),(60,-250,90),(0,-350,150),(80,-320,60),(120,-170,40)]:
  for tgt in [(0,-70,30),(20,-70,40)]:
    rv2,t2=lookat(np.array(cam2,float),tgt)
    p0=np.r_[C0['rv'],C0['t'],rv2,t2, C0['D'],22,45, 6,22,2.4, C0['X0'],C0['PX'],C0['Y0'],C0['PY'],C0['KD'], -73,83,50,35,-37,50, F2, F1, KH, 42.7,50.9,58.3,50.7]
    lo=[-np.inf]*12+[100,8,15, 1,5,1.0, -100,8,-40,8,4, -110,40,25,15,-60,30, (700 if FREE_F2 else F2-1), (900 if FREE_F1 else F1-1), (1.5 if FREE_F1 else KH-1e-3), 20,30,30,30]
    hi=[ np.inf]*12+[300,60,90, 30,60,5.0, 60,30,70,30,16, -40,110,90,70,-15,70, (2500 if FREE_F2 else F2+1), (4500 if FREE_F1 else F1+1), (7.0 if FREE_F1 else KH+1e-3), 80,70,90,70]
    if HSW==0 and not FREE_F2 and not FREE_F1:
        keep=list(range(23))+list(range(32,36)); p0=p0[keep]; lo=[lo[k] for k in keep]; hi=[hi[k] for k in keep]
    try: r=least_squares(res,p0,bounds=(lo,hi),max_nfev=600)
    except Exception as e: print('fail',e); continue
    if best is None or r.cost<best.cost: best=r
q=unpack(best.x); p=np.r_[q['rv1'],q['t1'],q['rv2'],q['t2'],[q[k] for k in NAMES]]; e=key_obs(q)-KM
print('cost %.1f | keys centre rms %.2f px | D %.1f  HF %.1f  HB %.1f  slope %.1f deg | band top back %.1f front %.1f thick %.1f'%(
  best.cost,np.sqrt((e[:,:2]**2).sum(1).mean()),q['D'],q['HF'],q['HB'],np.degrees(np.arctan((q['HB']-q['HF'])/q['D'])),q['ZBK'],q['ZF'],q['T']))
print('keypad X0 %.1f PX %.2f Y0 %.1f PY %.2f KD %.1f | FLASH (%.1f,%.1f) REDIAL (%.1f,%.1f) btn res %s'%(q['X0'],q['PX'],q['Y0'],q['PY'],q['KD'],q['BFX'],q['BFY'],q['BRX'],q['BRY'],np.round(btn_obs(q),1)))
print('handset x %.1f..%.1f  top z back %.1f front %.1f (body top there %.1f / %.1f)  yc %.1f  end width %.1f   f2 %.0f  f1 %.0f  KH %.1f'%(q['HXB'],q['HXF'],q['HZB'],q['HZF'],ztop(q,q['HXB']),ztop(q,q['HXF']),q['HYC'],q['HWE'],q['F2'],q['F1V'],q['KHV']))
print('  handset residuals', np.round(hs_obs(q),1))
for nm in W1:
    a,b,c=LN1[nm]; u=proj1(q,seg1(q,nm)); print('  front %-12s %s'%(nm,np.round(a*u[:,0]+b*u[:,1]+c,1)))
for nm in W2:
    a,b,c=LN2[nm]; u=proj2(q,seg2(q,nm)); print('  side  %-12s %s'%(nm,np.round(a*u[:,0]+b*u[:,1]+c,1)))
C1=-R.from_rotvec(q['rv1']).as_matrix().T@q['t1']; C2=-R.from_rotvec(q['rv2']).as_matrix().T@q['t2']
print('cam1 mm',np.round(C1,1),' cam2 mm',np.round(C2,1))
out={k:(v.tolist() if hasattr(v,'tolist') else float(v)) for k,v in q.items()}
out.update(W=W,KH=float(q['KHV']),f=float(q['F1V']),f2=float(q['F2']),IW=IM1[0],IH=IM1[1],IW2=IM2[0],IH2=IM2[1],cam=C1.tolist(),cam2=C2.tolist(),
           rv=q['rv1'].tolist(),t=q['t1'].tolist(),al=float(np.arctan((q['HB']-q['HF'])/q['D'])),ZB1=float(q['ZF']),ZB2=float(q['ZF']-q['T']))
json.dump(out,open('cam.json','w'),indent=1)
