import json, numpy as np, sys
from scipy.optimize import least_squares
from obs import SZ, PT, RING, SIL
from model import *
WO=json.load(open('win_obs.json')); WN=list(WO)
AZF=['r3','r4']
import model
model.TH=np.linspace(0,2*np.pi,720,endpoint=False)
FR=['r1','r2','r3','r4']
g0={'z_tip':40,'z_ball':34.5,'z_apex':33,'tana':0.45,'r_e':10.0,'z_e':13.0,'r_b':10.5,'z_b':7.0,'r_c':8.7,'r_s0':8.0,'taper':0.002}
BD={'z_tip':(30,60),'z_ball':(25,55),'z_apex':(22,50),'tana':(0.2,0.8),'r_e':(7,13),'z_e':(9,20),'r_b':(8,14),'z_b':(2,12),'r_c':(7.5,10),'taper':(-0.02,0.03)}
FIX={'r_s0':8.0}
free=[k for k in GN if k not in FIX]
NC=len(free)+8*len(FR)
def unpack(x):
    g=dict(FIX); g.update(dict(zip(free,x[:len(free)]))); cams={}
    az={k:0.0 for k in FR}
    for j,k in enumerate(AZF): az[k]=x[NC+j]
    for i,k in enumerate(FR): cams[k]=Cam(k,list(x[len(free)+8*i:len(free)+8*(i+1)])+[az[k]])
    W={}
    for j,n in enumerate(WN):
        th,z=x[NC+len(AZF)+2*j:NC+len(AZF)+2*j+2]; r=g['r_s0']-g['taper']*z; W[n]=np.array([r*np.cos(th),r*np.sin(th),z])
    g['_W']=W
    return g,cams
def shaft_r(g): return lambda z: g['r_s0']+g['taper']*(-z)
def cone_r(g): return lambda z: (g['z_apex']-z)*g['tana']
def res(x,rep=False):
    g,cams=unpack(x); r=[]; R=[]
    def add(k,n,v,s=1.0):
        r.append(v/s); R.append((k,n,v))
    for k in FR:
        c=cams[k]
        for n,(px,py) in PT.get(k,{}).items():
            p=c.proj(np.array([0,0,g['z_'+n]]))[0]; add(k,n+'x',p[0]-px); add(k,n+'y',p[1]-py)
        for n,(xl,xr,yf) in RING.get(k,{}).items():
            rr,zz={'eave':(g['r_e'],g['z_e']),'bal':(g['r_b'],g['z_b']),'cor':(g['r_c'],0.0)}[n]
            a,b,f=ring_feats(c,rr,zz)
            if n!='cor': add(k,n+'L',a-xl,2.0); add(k,n+'R',b-xr,2.0)
            if yf is not None: add(k,n+'F',f[1]-yf,1.5)
        for part,sides in SIL.get(k,{}).items():
            fn,z0,z1=(shaft_r(g),-45,0) if part=='shaft' else (cone_r(g),g['z_e']+0.5,g['z_apex']-0.3)
            for side,pts in sides.items():
                ys=np.array([p[1] for p in pts]); xs=np.array([p[0] for p in pts]); sx=sil_x(c,fn,z0,z1,ys,side)
                for a,b in zip(sx,xs): add(k,part+side,a-b,1.5)
        for n in WN:
            if k in WO[n]:
                p=c.proj(g['_W'][n])[0]; o=WO[n][k]; add(k,'w'+n+'x',p[0]-o[0],1.0); add(k,'w'+n+'y',p[1]-o[1],1.0)
        cc=x[len(free)+8*FR.index(k):len(free)+8*(FR.index(k)+1)]
        r.append(cc[4]*30); r.append(cc[6]/(0.5*SZ[k][0])); r.append(cc[7]/(0.5*SZ[k][1]))
    r.append((g['taper'])*50)
    return R if rep else np.array(r)
x0=[g0[k] for k in free]
init={'r1':(120,45,0,0.27,0,np.log(2000),0,0),'r2':(150,45,0,0.22,0,np.log(1320),0,0),'r3':(150,45,0,0.22,0,np.log(1650),0,0),'r4':(100,40,0,0.3,0,np.log(1840),0,0)}
for k in FR: x0+=list(init[k])
lo=[BD[k][0] for k in free]; hi=[BD[k][1] for k in free]
for k in FR: lo+=[30,-20,-0.5,-0.2,-0.3,np.log(300),-400,-800]; hi+=[400,150,0.5,1.2,0.3,np.log(6000),400,800]
B=json.load(open('out/blobs.json'))
x0+=[np.radians(13.6),np.radians(11.0)]; lo+=[-1,-1]; hi+=[1,1]
TH0={'Sa':-62.6,'Sb':-34.5,'Sc':-6.7,'Sd':19.6,'Se':46.1,'B1':-33.3,'B2':19.7,'Lc':-6.8}; Z0={'Sa':-2,'Sb':-2,'Sc':-2,'Sd':-2,'Se':-2,'B1':-5.5,'B2':-5.5,'Lc':-10}
for n in WN: x0+=[np.radians(TH0[n]),Z0[n]]; lo+=[-2,-20]; hi+=[2,0]
s=least_squares(res,x0,loss='soft_l1',f_scale=2,max_nfev=3000,x_scale='jac',bounds=(lo,hi))
g,cams=unpack(s.x); W=g.pop('_W')
print({k:round(float(v),3) for k,v in g.items()}); print('az r3 r4',np.degrees(s.x[NC:NC+2]))
for k in FR:
    c=cams[k]; cc=s.x[len(free)+8*FR.index(k):len(free)+8*(FR.index(k)+1)]
    print(k,'d %.1f h %.1f f %.0f pitch %.1f yaw %.2f roll %.2f pp %+.0f %+.0f'%(cc[0],cc[1],np.exp(cc[5]),np.degrees(cc[3]),np.degrees(cc[2]),np.degrees(cc[4]),cc[6],cc[7]))
rep=res(s.x,True); g['_W']=W
for k,n,v in rep:
    if abs(v)>2.5: print('  big',k,n,round(v,1))
print('rms',np.sqrt(np.mean([v*v for _,_,v in rep])))
g.pop('_W'); g['az']={k:float(cams[k].R is not None and 0) for k in FR}
g['az']={'r1':0.0,'r2':0.0,'r3':float(s.x[NC]),'r4':float(s.x[NC+1])}
json.dump({'g':g,'x':list(s.x),'free':free,'W':{n:v.tolist() for n,v in W.items()}},open('solve.json','w'),indent=1)
json.dump({k:c.dict() for k,c in cams.items()},open('cams.json','w'),indent=1)
