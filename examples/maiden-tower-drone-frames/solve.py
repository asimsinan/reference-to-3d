import json, numpy as np
from scipy.optimize import least_squares
SZ={1:(1586,1228),2:(1480,1056),3:(1290,1014),4:(1494,1080),5:(1462,1022),6:(1344,1056)}
A=3.25
import sys
PPS=float(sys.argv[1]) if len(sys.argv)>1 else 100
# point observations: name -> {img:(x,y)}
P={
'G':{1:(855,118),2:(716,179),3:(632.5,174),4:(822,179),5:(742.5,110),6:(630,124)},
'PB':{1:(854,325),2:(721,342),3:(635,336),4:(822,336),5:(744,266),6:(627.5,283)},
'K1t':{4:(787,718),5:(810,655),6:(825,647),3:(430,696),1:(642,692)},
'K1b':{4:(787,835),5:(811,762),6:(824,757),3:(421,786),1:(627,805)},
'K2t':{5:(508,655),4:(533,675),6:(619,723),3:(452,585)},
'K2b':{5:(509,762),4:(532,775),6:(615,848)},
'K3t':{6:(423,650),5:(505,562)},'K3b':{6:(417,757)},
'Ar1':{4:(590,773),5:(577,748)},'Ar2':{4:(680,794),5:(687,750),6:(747,775)},'Ar3':{4:(728,807),5:(743,752),6:(787,758)},
'BT':{2:(583,511),3:(322,537),4:(352,685),5:(368,715),6:(664,818)},
}
# shaft vertical edges: (corner sx,sy) -> {img: ((x,y),(x,y))}
E={
(1,1):{1:((840,635),(836.5,810)),4:((892,557),(889,682)),3:((702,580),(703,674)),2:((764,611),(764,705))},
(1,-1):{1:((749,610),(747.5,685)),4:((849,557),(849,670)),5:((800,497),(801,622)),6:((699.5,505),(701,624)),3:((580,580),(579,705)),2:((650,611),(650,705))},
(-1,-1):{4:((744,560),(745,650)),5:((684,497),(685,622))},
(-1,1):{1:((951,635),(951,725)),6:((549,505),(552,655)),2:((805,611),(806,630))},
}
names=['L','Lx','hw','zG','zPB','bx','by','bz','k3y','x1','lf','a1','a2','a3','zb1','bat','px','py']
x0g=[11,16,7,45,32,-18,-18,6,6,3.25,8.0,-9,-3,0,0,0,0,0]
az0={1:45,2:25,3:0,4:-25,5:-85,6:-135}
def world(g):
    d=dict(zip(names,g))
    W={'G':(d['px'],d['py'],d['zG']),'PB':(d['px'],d['py'],d['zPB']),
       'K1t':(d['x1'],-d['L'],d['hw']),'K1b':(d['x1']+d['bat'],-d['L']-d['bat'],d['zb1']),
       'K2t':(A-d['Lx'],-d['L'],d['hw']),'K2b':(A-d['Lx']-d['bat'],-d['L']-d['bat'],0),
       'K3t':(A-d['Lx'],d['k3y'],d['hw']),'K3b':(A-d['Lx'],d['k3y'],0),
       'BT':(d['bx'],d['by'],d['bz']),'Ar1':(d['a1'],-d['L'],0),'Ar2':(d['a2'],-d['L'],0),'Ar3':(d['a3'],-d['L'],0)}
    return {k:np.array(v,float) for k,v in W.items()}
def Rm(yaw,pitch,roll):
    # camera looks along direction f; yaw=azimuth of forward, pitch down
    cy,sy,cp,sp=np.cos(yaw),np.sin(yaw),np.cos(pitch),np.sin(pitch)
    fwd=np.array([cy*cp,sy*cp,-sp]); right=np.array([sy,-cy,0.0]); down=np.cross(fwd,right)
    R=np.stack([right,down,fwd])
    cr,sr=np.cos(roll),np.sin(roll)
    return np.array([[cr,-sr,0],[sr,cr,0],[0,0,1]])@R
def proj(c,i,X,lf=None):
    pos=c[:3]; R=Rm(c[3],c[4],c[5]); f=np.exp(lf)
    q=R@(np.asarray(X,float)-pos); w,h=SZ[i]
    return np.array([f*q[0]/q[2]+w/2+c[7],f*q[1]/q[2]+h/2+c[8]])
def res(x,final=False):
    g=x[:len(names)]; W=world(g); LF=g[names.index('lf')]; r=[]; rep=[]
    for i in range(1,7):
        c=x[len(names)+9*(i-1):len(names)+9*i]
        for n,o in P.items():
            if i in o:
                d=proj(c,i,W[n],LF)-np.array(o[i]); r+=list(d); rep.append((i,n,np.hypot(*d)))
        for (sx,sy),o in E.items():
            if i in o:
                (xa,ya),(xb,yb)=o[i]; nrm=np.array([yb-ya,-(xb-xa)],float); nrm/=np.linalg.norm(nrm)
                for z in (10,22):
                    d=(proj(c,i,(sx*A,sy*A,z),LF)-np.array([xa,ya]))@nrm; r.append(d); rep.append((i,'E%d%d'%(sx,sy),abs(d)))
        r.append(c[7]/PPS); r.append(c[8]/PPS)
        r.append(c[5]*20)                 # weak roll prior
    return rep if final else np.array(r)
x0=list(x0g)
for i in range(1,7):
    a=np.radians(az0[i]); D=220
    x0+=[D*np.cos(a)*.8,D*np.sin(a)*.8,D*.6,a+np.pi,np.radians(35),0,0,0,0]
s=least_squares(res,x0,loss='soft_l1',f_scale=3,max_nfev=4000)
x=s.x; g=dict(zip(names,x[:len(names)])); print({k:round(v,2) for k,v in g.items()})
cams={}
for i in range(1,7):
    c=x[len(names)+9*(i-1):len(names)+9*i]
    print(i,'pos',np.round(c[:3],1),'az',round(np.degrees(np.arctan2(c[1],c[0])),1),'pitch',round(np.degrees(c[4]),1),'roll',round(np.degrees(c[5]),2),'pp',np.round(c[7:9]))
    cams['r%d'%i]={'pos':list(c[:3]),'R':Rm(c[3],c[4],c[5]).tolist(),'f':float(np.exp(g['lf'])),'cx':SZ[i][0]/2+c[7],'cy':SZ[i][1]/2+c[8],'W':SZ[i][0],'H':SZ[i][1]}
for i,n,d in res(x,True):
    if d>4: print('  big',i,n,round(d,1))
print('rms',np.sqrt(np.mean([d*d for _,_,d in res(x,True)])))
json.dump(cams,open('cams.json','w'),indent=1); json.dump(g,open('geo.json','w'),indent=1)
