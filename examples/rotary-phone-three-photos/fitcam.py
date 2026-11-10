"""re-solve one photo's camera from body + handset silhouettes and the dial points together (dolly-zoom starts)"""
import cv2,numpy as np,json,sys
from scipy.optimize import minimize
import geom,camlib,fit
from overlay import sil
V=sys.argv[1];J=json.load(open('cam.json'));G=J['geom'];p=geom.load();P=geom.parts(p)
OBS=dict(dig={2:(818,820),3:(783,838),4:(785,882),5:(837,937),6:(932,1000),7:(1028,1032),8:(1097,1035),9:(1123,1008),0:(1110,962)},
 wheel=[(811,853),(870,824),(1103,973),(1030,1015)],ring=[(739,847),(840,803),(796.7,930),(880,986.7),(963,1026.7),(1063,1053),(1030,870),(1097,913),(1140,957)])
C,n,u,v=geom.dial_frame(p);a=np.linspace(0,2*np.pi,720,endpoint=False)[:,None]
circ=lambda R,h:C+h*n+R*(np.cos(a)*u+np.sin(a)*v);cw=circ(38.1,G['hw']);cr=circ(G['Rn'],0)
dig={k:C+G['Rd']*(np.cos(G['phi%d'%k])*u+np.sin(G['phi%d'%k])*v) for k in range(10)}
def cam_of(x): return (cv2.Rodrigues(np.array(x[:3]))[0],np.array(x[3:6]),x[6],x[7],x[8])
def cost(x,detail=False):
    c=cam_of(x);r=[]
    for k,(X,Y) in OBS['dig'].items(): r.append(np.hypot(*(camlib.proj(c,dig[k])[0]-[X,Y])))
    for pts,cc in ((OBS['wheel'],cw),(OBS['ring'],cr)):
        pc=camlib.proj(c,cc)
        for (X,Y) in pts: r.append(np.sqrt(((pc-[X,Y])**2).sum(1)).min())
    rms=float(np.sqrt(np.mean(np.square(r))))
    tb=np.zeros((2000,1500),np.uint8);th=tb.copy()
    for k,(Vv,F) in P.items():
        if k.startswith('foot'):continue
        m=sil(c,Vv,F);th|=m
        if k!='handset':tb|=m
    io=[]
    for tot,Z in ((tb,fit.ZA[V]),(th,fit.ZB[V])):
        A=(tot>0)&fit.IG[V]&Z;B=fit.PH[V]&fit.IG[V]&Z;io.append((A&B).sum()/(A|B).sum())
    val=(1-io[0])+0.5*(1-io[1])+0.02*rms
    return (val,rms,io) if detail else val
c0=J['cams'][V];R0=cv2.Rodrigues(np.array(c0['rv']))[0];P0=np.array(c0['pos']);best=None
for f in (c0['f'],1500,1300):
    Pn=C+(P0-C)*f/c0['f'];x0=np.r_[c0['rv'],-R0@Pn,f,750,1000]
    r=minimize(cost,x0,method='Powell',options=dict(maxfev=900,xtol=1e-3,ftol=1e-5),bounds=[(a_-b_,a_+b_) for a_,b_ in zip(x0,[.25]*3+[60]*3+[150]+[350,350])])
    d=cost(r.x,True);print('start f',f,'->',round(r.x[6]),'pp',r.x[7:].round(0),'cost',round(d[0],4),'dial rms',round(d[1],1),'IoU A,B',[round(float(i),3) for i in d[2]])
    if best is None or r.fun<best.fun: best=r
R,t,f=cam_of(best.x)[:3];J['cams'][V]=dict(c=[float(best.x[7]),float(best.x[8])],rv=list(map(float,best.x[:3])),t=list(map(float,t)),f=float(f),pos=list(map(float,-R.T@t)))
json.dump(J,open('cam.json','w'),indent=1);print('pos',(-R.T@t).round(1),'f',round(f))
