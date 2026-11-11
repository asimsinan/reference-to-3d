"""solve.py -- joint solve: tram parameters + one camera per photo, from hand-read points (pts.json) -> cams.json"""
import os, json, numpy as np, cv2
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
P=json.load(open('pts.json'))
SIZES={'1':(1056,960),'2':(970,968),'3':(462,660),'4':(840,768),'5':(742,734),'6':(1002,954)}
SIDE={'1':1,'2':1,'3':1,'4':1,'5':-1,'6':1}
MP=(['hw'] if os.environ.get('RAILS') else [])+['zs','Xs','Xf','ac','xo','yo','zwd','zws','zh','xh','xb','yb','zb','xsl','ysl','zsl','xk','zk']
M0=dict(hw=1.0,zs=0.85,Xs=2.2,Xf=4.0,ac=0.55,xo=3.3,yo=0.95,zwd=1.85,zws=1.85,zh=1.3,xh=4.15,xb=4.03,yb=0.3,zb=1.6,xsl=3.9,ysl=0.75,zsl=3.6,xk=3.8,zk=3.8)
G=1.05
import os
RAILS=json.load(open('rails.json')) if os.environ.get('RAILS') else {}
def pts3(m,side):
    g=lambda k:(m[k] if k in m else M0[k])
    d={'HL':(g('xh'),0,g('zh')),'Bm':(g('xb'),-g('yb'),g('zb')),'Bp':(g('xb'),g('yb'),g('zb')),
       'SLm':(g('xsl'),-g('ysl'),g('zsl')),'SLp':(g('xsl'),g('ysl'),g('zsl')),'K':(g('xk'),0,g('zk')),
       'Dm':(g('Xf'),-g('ac'),g('zwd')),'Dp':(g('Xf'),g('ac'),g('zwd')),'Op':(g('xo'),g('yo'),g('zwd')),'Om':(g('xo'),-g('yo'),g('zwd')),
       'SFT':(g('Xs'),side*g('hw'),g('zws')),'SRT':(-g('Xs'),side*g('hw'),g('zws')),'SFB':(g('Xs'),side*g('hw'),g('zs')),'SRB':(-g('Xs'),side*g('hw'),g('zs'))}
    return d
def proj(X,c,size):
    R=Rot.from_rotvec(c[:3]).as_matrix(); t=c[3:6]; f=c[6]
    cx,cy=(c[7],c[8]) if len(c)>7 else (size[0]/2,size[1]/2)
    Xc=(R@(np.asarray(X)-t).T).T
    return np.stack([f*Xc[:,0]/Xc[:,2]+cx, f*Xc[:,1]/Xc[:,2]+cy],1), Xc[:,2]
def look(cam_pos,target):
    z=np.array(target)-cam_pos; z/=np.linalg.norm(z); x=np.cross(z,[0,0,1]); x/=np.linalg.norm(x); y=np.cross(z,x)
    return Rot.from_matrix(np.stack([x,y,z])).as_rotvec()
# init each camera by PnP on the initial model, f scan
cams={}
for k in P:
    d=pts3(M0,SIDE[k]); names=[n for n in P[k] if n in d]
    X=np.array([d[n] for n in names],float); u=np.array([P[k][n] for n in names],float)
    W,H=SIZES[k]; best=None
    for f in np.linspace(0.6,3.0,25)*W:
        K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]])
        ok,rv,tv=cv2.solvePnP(X,u,K,None,flags=cv2.SOLVEPNP_SQPNP)
        if not ok: continue
        pr,_=cv2.projectPoints(X,rv,tv,K,None); e=np.sqrt(((pr.reshape(-1,2)-u)**2).sum(1).mean())
        if best is None or e<best[0]: best=(e,f,rv.ravel(),tv.ravel())
    e,f,rv,tv=best; R=Rot.from_rotvec(rv).as_matrix(); C=-R.T@tv
    cams[k]=np.r_[rv,C,f,W/2,H/2]; print('init',k,round(e,2),'f',round(f),'C',np.round(C,2))
keys=sorted(P)
def unpack(x):
    m=dict(zip(MP,x[:len(MP)])); cs={}
    for i,k in enumerate(keys): cs[k]=x[len(MP)+9*i:len(MP)+9*i+9]
    return m,cs
def resid(x,detail=False):
    m,cs=unpack(x); r=[]; det={}
    for k in keys:
        d=pts3(m,SIDE[k]); names=[n for n in P[k] if n in d]
        X=np.array([d[n] for n in names]); u=np.array([P[k][n] for n in names])
        pr,z=proj(X,cs[k],SIZES[k]); e=(pr-u); r.append(e.ravel()/2.0); det[k]=dict(zip(names,np.round(np.hypot(*e.T),1)))
        for sd,segs in RAILS.get(k,{}).items():
            y=(-G/2 if sd=='m' else G/2)
            q,_=proj(np.array([[0,y,0],[8,y,0.]]),cs[k],SIZES[k]); dvec=q[1]-q[0]; nrm=np.array([-dvec[1],dvec[0]])/np.hypot(*dvec)
            for sg in segs:
                for e in (sg[:2],sg[2:]): r.append([((np.array(e)-q[0])@nrm)/1.5])
    # weak priors: symmetry/ordering sanity
    for k in keys:
        W,H=SIZES[k]; r.append([(cs[k][7]-W/2)/(0.25*W)*3,(cs[k][8]-H/2)/(0.25*H)*3])
    r.append([(m['xh']-m['Xf']-0.15)/0.3,(m['xb']-m['Xf'])/0.3,(m['xk']-m['Xf']+0.3)/1.0])
    r=np.concatenate([np.ravel(a) for a in r])
    return (r,det) if detail else r
x0=np.r_[[M0[k] for k in MP],np.concatenate([cams[k] for k in keys])]
sol=least_squares(resid,x0,loss='soft_l1',f_scale=2.0,x_scale='jac',max_nfev=20000)
r,det=resid(sol.x,True); m,cs=unpack(sol.x)
for k in keys: print(k,'f',round(cs[k][6]),'C',np.round(cs[k][3:6],2),'rms',round(float(np.sqrt(np.mean(np.array(list(det[k].values()))**2))),2),det[k])
print({k:round(float(v),3) for k,v in m.items()})
json.dump({'model':{k:float(v) for k,v in m.items()},'G':G,'cams':{k:[float(v) for v in cs[k]] for k in keys},'sizes':SIZES},open('cams.json','w'),indent=1)
