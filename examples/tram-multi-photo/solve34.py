"""solve34.py -- cameras of #34's photos from front-end features, body priors from the 115 solve -> cams34.json"""
import json, numpy as np, cv2
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
J=json.load(open('cams.json')); M0=dict(J['model']); M0['Xe']=1.85; M0['wp']=0.45; M0['w1']=1.15; M0['w2']=1.15; M0['w3']=1.15; M0['zpt']=2.63; import os
P=json.load(open('pts34.json'))
DROP=os.environ.get('DROP','').split(',')
for k in P: P[k]={a:v for a,v in P[k].items() if a not in DROP}
ONLY=os.environ.get('ONLY'); P={k:v for k,v in P.items() if not ONLY or k in ONLY.split(',')}
FIX=os.environ.get('FIX')
SZ={k:cv2.imread(f'ref2/p{k}.png').shape[1::-1] for k in P}
FREE=['Xe','wp','w1','w2','w3','zpt','zws','zs','xh','zh','xb','yb','zb','xsl','ysl','zsl','xk','zk','zwd','Xf','ac','xo','yo']
SIG={'Xe':0.4,'wp':0.3,'w1':0.5,'w2':0.5,'w3':0.5,'zpt':0.3,'zws':0.15,'zs':0.15,'xh':0.05,'zh':0.06,'xb':0.05,'yb':0.06,'zb':0.08,'xsl':0.1,'ysl':0.08,'zsl':0.1,'xk':0.15,'zk':0.08,'zwd':0.06,'Xf':0.04,'ac':0.04,'xo':0.05,'yo':0.03}
def pts3(m):
    g=lambda k:m.get(k,M0[k])
    return {'HL':(g('xh'),0,g('zh')),'Bm':(g('xb'),-g('yb'),g('zb')),'Bp':(g('xb'),g('yb'),g('zb')),'SLm':(g('xsl'),-g('ysl'),g('zsl')),'SLp':(g('xsl'),g('ysl'),g('zsl')),
            'K':(g('xk'),0,g('zk')),'Dm':(g('Xf'),-g('ac'),g('zwd')),'Dp':(g('Xf'),g('ac'),g('zwd')),'Op':(g('xo'),g('yo'),g('zwd')),'Om':(g('xo'),-g('yo'),g('zwd')),
            }
def side_pts(m,sd):
    g=lambda k:m.get(k,M0[k]); hw=g('hw')*sd; Xe=g('Xe'); wp=g('wp'); w1,w2,w3=g('w1'),g('w2'),g('w3')
    H=os.environ.get('HYP')
    if H=='norear': w1=w2=w3=(2*Xe-wp)/3
    if H=='equal': w2=w3=w1
    if H=='rearpanel': w1=w2=w3=(2*Xe-2*wp)/3
    zw=g('zws'); zb=g('zs')
    return {'PF_s':(Xe,hw,zw),'PR_s':(Xe-wp,hw,zw),'W1_s':(Xe-wp-w1,hw,zw),'W2_s':(Xe-wp-w1-w2,hw,zw),'E_s':(Xe-wp-w1-w2-w3,hw,zw),
            'PF_b':(Xe,hw,zb),'E_b':(Xe-wp-w1-w2-w3,hw,zb),'PT':(Xe-wp/2,hw,g('zpt'))}
SIDE={'9':1,'12':1,'11':-1,'13':1}
def proj(c,X,W,H):
    R=Rot.from_rotvec(c[:3]).as_matrix(); Xc=(np.asarray(X)-c[3:6])@R.T
    return np.stack([c[6]*Xc[:,0]/Xc[:,2]+c[7], c[6]*Xc[:,1]/Xc[:,2]+c[8]],1)
ks=sorted(P,key=int); cams={}
def allp(m,k): d=pts3(m); d.update(side_pts(m,SIDE[k])); return d
for k in ks:
    d0=allp({},k); W,H=SZ[k]; n=list(P[k]); X=np.array([d0[a] for a in n],float); u=np.array([P[k][a] for a in n],float); best=None
    for f in np.linspace(0.4,4,40)*W:
        K=np.array([[f,0,W/2],[0,f,H/2],[0,0,1.]]); ok,rv,tv=cv2.solvePnP(X,u,K,None,flags=cv2.SOLVEPNP_SQPNP)
        pr,_=cv2.projectPoints(X,rv,tv,K,None); e=np.sqrt(((pr.reshape(-1,2)-u)**2).sum(1).mean())
        if best is None or e<best[0]: best=(e,f,rv.ravel(),tv.ravel())
    e,f,rv,tv=best; R=Rot.from_rotvec(rv).as_matrix(); cams[k]=np.r_[rv,-R.T@tv,f,W/2,H/2]; print('init',k,round(e,1),round(f))
def unpack(x): return dict(zip(FREE,x[:len(FREE)])),{k:x[len(FREE)+9*i:len(FREE)+9*i+9] for i,k in enumerate(ks)}
def res(x,det=False):
    m,cs=unpack(x); r=[]; D={}
    for k in ks:
        d=allp(m,k)
        W,H=SZ[k]; n=list(P[k]); e=proj(cs[k],[d[a] for a in n],W,H)-np.array([P[k][a] for a in n]); r.append(e.ravel()/2.0); D[k]=dict(zip(n,np.round(np.hypot(*e.T),1).tolist()))
        r.append([(cs[k][7]-W/2)/(0.15*W),(cs[k][8]-H/2)/(0.15*H),np.log(abs(cs[k][6])/W)/0.25*2])
    r.append([(m[a]-M0[a])/SIG[a] for a in FREE])
    r=np.concatenate([np.ravel(a) for a in r]); return (r,D) if det else r
if FIX:
    MF=json.load(open(FIX))['model']; M0.update(MF); SIG={a:1e-4 for a in SIG}
x0=np.r_[[M0[a] for a in FREE],np.concatenate([cams[k] for k in ks])]
s=least_squares(res,x0,loss='soft_l1',f_scale=2,x_scale='jac'); r,D=res(s.x,True); m,cs=unpack(s.x)
for k in ks: print(k,'f',round(cs[k][6]),'C',np.round(cs[k][3:6],2),D[k])
print('HYP',os.environ.get('HYP'),'total |r|^2',round(float((r**2).sum()),1)); print({a:(round(M0[a],3),round(float(m[a]),3)) for a in FREE})
mm=dict(M0); mm.update({a:float(v) for a,v in m.items()})
OUT=os.environ.get('OUT','cams34.json'); old=json.load(open(OUT)) if os.path.exists(OUT) and FIX else {'cams':{},'sizes':{}}
old['model']=mm; old['cams'].update({k:[float(v) for v in cs[k]] for k in ks}); old['sizes'].update({k:list(SZ[k]) for k in ks})
json.dump(old,open(OUT,'w'),indent=1)
