"""fit shape params to the three photo silhouettes. usage: fit.py name1,name2,... [iters]"""
import cv2,numpy as np,sys,json,time
from scipy.optimize import minimize
import geom,camlib
from overlay import sil
IGN={'front':[[(200,830),(345,830),(345,975),(480,975),(480,1600),(200,1600)]],
     'side':[[(230,860),(330,860),(345,1140),(520,1130),(900,1230),(920,1340),(230,1340)],[(830,790),(1000,800),(1130,900),(1170,1010),(1100,960),(950,860),(830,830)]],
     'rear':[[(1125,1235),(1350,1235),(1350,1080),(1490,1080),(1490,1500),(1125,1500)]]}
def reg(polys):
    m=np.zeros((2000,1500),np.uint8)
    for poly in polys: cv2.fillPoly(m,[np.array(poly,np.int32)],1)
    return m>0
R=lambda x0,y0,x1,y1:[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
ZA={'front':[[(545,905),(1160,905),(1175,985),(1400,1000),(1400,1750),(300,1750),(300,975),(545,975)]],
    'side':[R(650,770,1400,1400),R(100,1010,1400,1400)],
    'rear':[R(300,1262,1300,1750),R(590,1060,980,1300)]}
ZB={'front':[R(100,500,1500,800),R(100,500,545,975),R(1160,500,1500,985)],
    'side':[R(100,500,900,760),R(100,500,300,860)],
    'rear':[R(100,700,1500,1000),R(100,700,560,1250),R(985,700,1500,1250)]}
ZA={v:reg(z) for v,z in ZA.items()};ZB={v:reg(z) for v,z in ZB.items()}
PH={};IG={};CAM={}
for v in IGN:
    PH[v]=cv2.imread('m_%s.png'%v,0)>0;m=np.zeros((2000,1500),np.uint8)
    for poly in IGN[v]: cv2.fillPoly(m,[np.array(poly,np.int32)],1)
    IG[v]=m==0;CAM[v]=camlib.cam(v)
_P=geom.parts(geom.load())
for v in PH:
    m=sil(CAM[v],*_P['ring'])|sil(CAM[v],*_P['wheel']);IG[v]&=cv2.dilate(m,np.ones((9,9),np.uint8))==0
def cost(p,detail=False):
    P=geom.parts(p);c=0;det={}
    for v in PH:
        tb=np.zeros((2000,1500),np.uint8);th=np.zeros((2000,1500),np.uint8)
        for k,(V,F) in P.items():
            if k.startswith('foot'): continue
            m=sil(CAM[v],V,F);th|=m
            if k!='handset': tb|=m
        if VIEWSEL and v not in VIEWSEL: continue
        for nm,tot,Z in (('A',tb,ZA[v]),('B',th,ZB[v])):
            if MODE and nm not in MODE: continue
            a=(tot>0)&IG[v]&Z;b=PH[v]&IG[v]&Z;iou=(a&b).sum()/(a|b).sum();det[v+nm]=round(float(iou),4);c+=1-iou
    return (c,det) if detail else c
MODE='';VIEWSEL=''
if __name__=='__main__':
    MODE=sys.argv[3] if len(sys.argv)>3 else ''
    B=float(sys.argv[4]) if len(sys.argv)>4 else 10
    VIEWSEL=sys.argv[5] if len(sys.argv)>5 else ''
    names=sys.argv[1].split(',');p=geom.load()
    print('start',cost(p,True))
    import json as _j
    camv=[n[4:] for n in names if n.startswith('cam_')];names=[n for n in names if not n.startswith('cam_')]
    x0=np.array([p[n] for n in names]);bs=[B]*len(names);C0={}
    for v in camv:
        R,t,f_=CAM[v][:3];C0[v]=np.r_[cv2.Rodrigues(R)[0].ravel(),t,f_];x0=np.r_[x0,C0[v]];bs+=[0.06]*3+[25]*3+[200]
    def setcam(x):
        for i,v in enumerate(camv):
            c=x[len(names)+7*i:len(names)+7*i+7];CAM[v]=(cv2.Rodrigues(c[:3])[0],c[3:6],c[6])
    def f(x):
        setcam(x);q=dict(p);q.update(zip(names,x));return cost(q)
    t=time.time()
    r=minimize(f,x0,method='Powell',options=dict(maxfev=int(sys.argv[2]) if len(sys.argv)>2 else 600,xtol=0.05,ftol=1e-4),
               bounds=[(v-b,v+b) for v,b in zip(x0,bs)])
    setcam(r.x)
    if camv:
        J=_j.load(open('cam.json'))
        for v in camv:
            R,tt,f_=CAM[v];J['cams'][v]=dict(rv=list(map(float,cv2.Rodrigues(R)[0].ravel())),t=list(map(float,tt)),f=float(f_),pos=list(map(float,-R.T@tt)))
        _j.dump(J,open('cam.json','w'),indent=1)
    p.update({n:float(v) for n,v in zip(names,r.x)})
    print('end',cost(p,True),round(time.time()-t),'s');print({n:round(p[n],2) for n in names})
    json.dump(p,open('params.json','w'),indent=1)
